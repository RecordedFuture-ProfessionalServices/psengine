##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

import logging
from typing import Annotated

import stix2
from typing_extensions import Doc

from ..helpers import FormattingHelpers
from .base_stix_entity import BaseStixEntity
from .complex_entity import IndicatorEntity, NoteEntity, Relationship
from .errors import STIX2TransformError, UnsupportedConversionTypeError
from .helpers import convert_entity
from .simple_entity import TTP, ThreatActor

LOG = logging.getLogger(__name__)


class EnrichedIndicator(IndicatorEntity):
    """Class for converting Indicator + risk score + links to OpenCTI bundle."""

    def __init__(
        self,
        name: Annotated[str, Doc('An indicator value.')],
        type_: Annotated[str, Doc('A Recorded Future type of indicator.')],
        evidence_details: Annotated[list, Doc('Risk rules and evidence details.')],
        link_hits: Annotated[list, Doc('A list of lists for link hits.')] = None,
        risk_mapping: Annotated[list, Doc('A risk rule to TTP mapping.')] = None,
        ai_insights: Annotated[dict, Doc('AI insights for IOC in Recorded Future.')] = None,
        author: Annotated[stix2.Identity, Doc('A Recorded Future Identity.')] = None,
        confidence: Annotated[int, Doc('A confidence score of the indicator.')] = None,
        create_indicator: Annotated[
            bool, Doc('A flag that governs if the indicator should be created.')
        ] = True,
        create_obs: Annotated[
            bool, Doc('A flag that governs if the observable should be created.')
        ] = True,
        tlp_marking: Annotated[str, Doc('The TLP level. Defaults to amber.')] = 'amber',
    ):
        """Indicator container. Contains indicator, observable, and relationship between them.

        Raises:
            STIX2TransformError: If transformation fails.
        """
        link_hits = link_hits or []
        risk_mapping = risk_mapping or []
        ai_insights = ai_insights or {}
        evidence_details = [e if isinstance(e, dict) else e.json() for e in evidence_details]
        labels = ['rf:' + (rule.get('Rule') or rule.get('rule')) for rule in evidence_details]

        description = self._format_description(ai_insights)
        super().__init__(
            name=name,
            type_=type_,
            confidence=confidence,
            create_indicator=create_indicator,
            create_obs=create_obs,
            labels=labels,
            description=description,
            tlp_marking=tlp_marking,
            author=author,
        )

        self._add_risk_score_as_note(confidence)

        for ttp in risk_mapping:
            self._add_ttp(ttp)
        for rule in evidence_details:
            self._add_rule(rule)

        for hit in link_hits:
            self._add_link(hit)

    def _format_description(self, ai_insights: dict):
        """If AI insights are available then:
            - use it as a description
            - otherwise use a default string value.

        Returns:
            str: Indicator description
        """
        ai_insights = ai_insights if isinstance(ai_insights, dict) else ai_insights.json()
        description = 'Indicator from Recorded Future'
        if ai_insights.get('text') is not None:
            description = '### Recorded Future AI Insights\n\n{}'.format(
                FormattingHelpers.cleanup_ai_insights(ai_insights.get('text')),
            )

        return description

    def _add_link(self, hit) -> None:
        hit = hit if isinstance(hit, dict) else hit.json()
        for section in hit['sections']:
            for list_ in section['lists']:
                if list_['type']['name'] == 'Threat Actor':
                    for entity in list_['entities']:
                        stix_entity = ThreatActor(entity['name'])
                        self.stix_objects.append(stix_entity.stix_obj)
                        self._relate(stix_entity)
                else:
                    for entity in list_['entities']:
                        try:
                            stix_entity = convert_entity(entity['name'], entity['type'])
                        except UnsupportedConversionTypeError as err:
                            LOG.warning(str(err) + '. Skipping...')
                            continue
                        if isinstance(stix_entity, IndicatorEntity):
                            self.stix_objects.extend(stix_entity.stix_objects)
                            self._relate(stix_entity)
                        else:
                            self.stix_objects.append(stix_entity.stix_obj)
                            self._relate(stix_entity)

    def _relate(self, obj: BaseStixEntity) -> None:
        """Creates relationship between object and indicator/observabe.

        Raises:
            STIX2TransformError: Generic transofmr error
        """
        if isinstance(obj, IndicatorEntity):
            sources = []
            targets = []
            if self.indicator:
                sources.append(self.indicator)
            if self.observable:
                sources.append(self.observable)
            if obj.indicator:
                targets.append(obj.indicator)
            if obj.observable:
                targets.append(obj.observable)
            self._append_indicator_relationships(sources, targets)
        elif isinstance(obj, BaseStixEntity):
            if self.indicator:
                self.stix_objects.append(
                    Relationship(
                        source=self.indicator.id,
                        target=obj.stix_obj.id,
                        type_='indicates',
                        author=self.author,
                    ).stix_obj,
                )
            if self.observable:
                self.stix_objects.append(
                    Relationship(
                        source=self.observable.id,
                        target=obj.stix_obj.id,
                        type_='related-to',
                        author=self.author,
                    ).stix_obj,
                )
        else:
            raise STIX2TransformError('Cannot transform, entity is not of correct type')

    def _append_indicator_relationships(self, sources, targets) -> None:
        for source in sources:
            for target in targets:
                self.stix_objects.append(
                    Relationship(
                        source=source.id,
                        target=target.id,
                        type_='related-to',
                        author=self.author,
                    ).stix_obj,
                )

    def _add_ttp(self, ttp: dict) -> None:
        """Adds a TTP from risk mapping.

        Args:
            ttp (dict): maps a risk rule to one or more T codes
        """
        ttp = ttp if isinstance(ttp, dict) else ttp.json()
        for cat in ttp.get('categories', []):
            if cat['framework'] == 'MITRE':
                obj = TTP(cat['name'])
                self.stix_objects.append(obj.stix_obj)
                self._relate(obj)

    def _add_rule(self, rule: dict) -> None:
        """Convert risk rule + evidence detail to notes.

        Args:
            rule (dict): Risk rule + evidence details json blobs
        """
        rule = rule if isinstance(rule, dict) else rule.json()
        refs = []
        if self.indicator:
            refs.append(self.indicator.id)
        if self.observable:
            refs.append(self.observable.id)

        # in risklists and enrichment 'rule' has different capitalization
        rule_name = rule.get('Rule') or rule.get('rule')

        if not rule_name:
            raise STIX2TransformError('Cannot transform, rule name is missing')

        self.stix_objects.append(
            NoteEntity(
                name=rule_name,
                content=(rule.get('evidenceString') or rule.get('EvidenceString')),
                object_refs=refs,
                author=self.author,
            ).stix_obj,
        )

    def _add_risk_score_as_note(self, risk_score: int) -> None:
        """Add Confidende/Risk Score as a note.

        Args:
            risk_score (int): Confidence score
        """
        if not risk_score:
            raise STIX2TransformError('Cannot transform, confidence is missing')
        object_refs = []
        if self.indicator:
            object_refs.append(self.indicator.id)
        if self.observable:
            object_refs.append(self.observable.id)
        self.stix_objects.append(
            NoteEntity(
                name='Recorded Future Risk Score',
                content=f'{risk_score}/99',
                object_refs=object_refs,
                author=self.author,
            ).stix_obj,
        )

    @property
    def bundle(self) -> stix2.v21.Bundle:
        """Creates STIX2 bundle.

        Returns:
            stix2.v21.Bundle: Bundle
        """
        self.stix_objects.append(self.author)
        return stix2.v21.Bundle(objects=self.stix_objects, allow_custom=True)

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

import json
import logging

from stix2 import Bundle, Identity, Report
from stix2.exceptions import (
    ExtraPropertiesError,
    InvalidValueError,
    MissingPropertiesError,
    STIXError,
)

from ..analyst_notes import AnalystNote
from ..risklists.models import DefaultRiskList
from .complex_entity import DetectionRuleEntity, IndicatorEntity
from .constants import ENTITY_TYPE_MAP, REPORT_TYPE_MAPPER, SUPPORTED_HUNTING_RULES, TLP_MAP
from .enriched_indicator import EnrichedIndicator
from .errors import STIX2TransformError, UnsupportedConversionTypeError
from .helpers import convert_entity
from .util import create_rf_author

LOG = logging.getLogger(__name__)


class RFBundle:
    """Class for creating STIX2 bundles from Recorded Future objects."""

    @classmethod
    def from_default_risklist(
        cls,
        risklist: list[DefaultRiskList],
        entity_type: str,
        identity: Identity = None,
    ) -> Bundle:
        """Creates STIX2 bundle from a Recorded Future default risklist.

        Args:
            risklist (str): Recorded Future default risklist (contains the standard 5 columns)
            entity_type (str): entity type
            identity (_type_, optional): Author identity. Defaults to Recorded Future

        Raises:
            STIX2TransformError: if the risklist is not valid
            STIX2TransformError: if EvidenceDetails is not valid JSON
            STIX2TransformError: if the bundle cannot be created

        Returns:
            Bundle: STIX2 bundle
        """
        if not identity:
            identity = create_rf_author()
        objects = [identity]
        LOG.info(f'Creating STIX2 bundle from {entity_type} risklist')

        try:
            enriched_indicators = []
            for ioc in risklist:
                indicator = EnrichedIndicator(
                    name=ioc.ioc,
                    type_=ENTITY_TYPE_MAP[entity_type],
                    confidence=ioc.risk_score,
                    evidence_details=ioc.evidence_details,
                )
                enriched_indicators.append(indicator)

        except KeyError as ke:
            raise STIX2TransformError(f'Risklist missing header: {ke}') from ke

        except json.JSONDecodeError as jse:
            raise STIX2TransformError(f'EvidenceDetails is not valid JSON: {jse}') from jse

        for i in enriched_indicators:
            objects.extend(i.stix_objects)

        try:
            bundle = Bundle(objects=objects, allow_custom=True)
        except (
            ValueError,
            ExtraPropertiesError,
            InvalidValueError,
            MissingPropertiesError,
            STIXError,
        ) as e:
            raise STIX2TransformError(f'Failed to create STIX2 bundle from risklist. {e}') from e

        return bundle

    @classmethod
    def from_analyst_note(
        cls,
        note: AnalystNote,
        attachment: bytes = None,
        split_snort: bool = False,
        identity: Identity = None,
    ) -> Bundle:
        """Creates a STIX2 bundle from a Recorded Future analyst note.

        Args:
            note (AnalystNote): Recorded Future analyst note
            attachment (bytes, optional): Note attachment. Defaults to None.
            split_snort (bool, optional): Split snort rules into separate DetectionRule objects.
            Defaults to False.
            identity (stix2.Identity, optional): Author. Defaults to Recorded Future.

        Returns:
            Bundle: STIX2 bundle
        """
        LOG.info(f'Creating STIX2 bundle from analyst note {note.id_}')

        if not identity:
            identity = create_rf_author()
        objects = [identity]
        topics = [topic.name for topic in note.attributes.topic]
        report_types = _create_report_types(topics)
        for entity in note.attributes.note_entities:
            try:
                stix_entity = convert_entity(entity.name, entity.type_)
                if isinstance(stix_entity, IndicatorEntity):
                    objects.extend(stix_entity.stix_objects)
                else:
                    objects.append(stix_entity.stix_obj)

            except UnsupportedConversionTypeError as err:  # noqa: PERF203
                LOG.warning(str(err) + '. Skipping...')
                continue

        if attachment and note.detection_rule_type in SUPPORTED_HUNTING_RULES:
            # This is a workaround for OpenCTI
            # OpenCTI does not support multiple Snort rules within a single DetectionRule object
            # so we split them into separate objects (split_snort = True)
            if note.detection_rule_type == 'snort' and split_snort is True:
                objects.extend(_split_snort_rules(note, str(attachment, 'UTF-8')))
            else:
                rule = DetectionRuleEntity(
                    name=note.attributes.title,
                    type_=note.detection_rule_type,
                    content=str(attachment, 'UTF-8'),
                )
                objects.append(rule.stix_obj)

        external_references = _generate_external_references(note.attributes.validation_urls)
        external_references.append(
            {
                'source_name': 'Recorded Future',
                'url': note.portal_url,
            },
        )

        report = Report(
            name=note.attributes.title,
            created_by_ref=identity.id,
            description=note.attributes.text,
            published=note.attributes.published,
            labels=topics,
            report_types=report_types,
            object_refs=[obj.id for obj in objects],
            object_marking_refs=TLP_MAP['amber'],
            external_references=external_references,
        )
        objects.append(report)

        bundle = Bundle(objects=objects, allow_custom=True)

        return bundle


# Helpers for bundle creation


def _split_snort_rules(note: AnalystNote, attachment: str) -> list:
    """Splits snort rules into multiple DetectionRule objects.

    Args:
        note (AnalystNote): AnalystNote object
        attachment (str): snort rule payload
    """
    rules = []
    ctr = 1
    temp_description = []
    for line in attachment.split('\n'):
        line = line.strip()

        # skip comments and empty lines
        if line.startswith('#') or not line:
            temp_description.append(line[1:].strip())
            continue
        rules.append(
            DetectionRuleEntity(
                name=note.attributes.title + f', Rule {ctr}',
                type_=note.detection_rule_type,
                content=line,
                description='\n'.join(temp_description),
            ).stix_obj,
        )
        # reset description for next rule
        temp_description = []
        ctr += 1
    return rules


def _create_report_types(topics: list) -> list:
    """Map topics to STIX2 report types.

    Args:
        topics (list): List of topics to map

    Returns:
        list: List of STIX2 report types
    """
    ret = set()
    for topic in topics:
        if topic not in REPORT_TYPE_MAPPER:
            LOG.warning(f'Could not map a report type for type {topic}')
            continue
        ret.add(REPORT_TYPE_MAPPER[topic])
    return list(ret)


def _generate_external_references(urls: list) -> list:
    """Generate External references from validation urls."""
    refs = []
    if urls is None:
        return refs

    for url in urls:
        source_name = url.name.split('/')[2].split('.')[-2].capitalize()
        refs.append({'source_name': source_name, 'url': url})
    return refs

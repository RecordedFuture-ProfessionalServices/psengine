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
from datetime import datetime
from typing import Annotated, Union

import stix2
from typing_extensions import Doc

from ..constants import INDICATOR_INTEL_CARD_URL
from .base_stix_entity import BaseStixEntity
from .constants import (
    CONVERTED_TYPES,
    INDICATOR_TYPE_TO_RF_PORTAL_MAP,
    INDICATOR_TYPES,
    SUPPORTED_HUNTING_RULES,
    TLP_MAP,
)
from .errors import STIX2TransformError
from .util import generate_uuid


class DetectionRuleEntity(BaseStixEntity):
    """Represents a Yara or SNORT rule."""

    def __init__(
        self,
        name: Annotated[str, Doc('The name of the Detection Rule.')],
        type_: Annotated[str, Doc('The detection rule type (YARA or Sigma).')],
        content: Annotated[str, Doc('The hunting rule itself, typically YARA, Snort, or Sigma.')],
        description: Annotated[str, Doc('A description of the Detection Rule.')] = None,
        author: Annotated[stix2.Identity, Doc('A Recorded Future author.')] = None,
    ) -> None:
        """Detection Rule.

        Raises:
            STIX2TransformError: Description
        """
        self.name = name.split('.')[0]
        self.type = type_
        self.content = content
        self.description = description
        self.stix_obj = None

        if self.type not in SUPPORTED_HUNTING_RULES:
            msg = f'Detection rule of type {self.type} is not supported'
            raise STIX2TransformError(msg)
        super().__init__(name, author)

    def create_stix_object(self) -> None:
        """Creates STIX objects from object attributes."""
        self.stix_obj = stix2.Indicator(
            id=self._generate_id(),
            name=self.name,
            description=self.description,
            pattern_type=self.type,
            pattern=self.content,
            valid_from=datetime.now(),
            created_by_ref=self.author.id,
        )

    def _generate_id(self) -> str:
        """Generates an ID."""
        return 'indicator--' + generate_uuid(name=self.name, content=self.content, type=self.type)


class Grouping(BaseStixEntity):
    """Explicitly asserts that the referenced STIX Objects
    have a shared context, unlike a STIX Bundle (which explicitly
    conveys no context).
    """

    def __init__(
        self,
        name: Annotated[str, Doc('The name of the event. Should be unique.')],
        description: Annotated[str, Doc('A description, usually empty.')] = None,
        is_malware: Annotated[
            bool, Doc('A flag to determine if malware-analysis context should be used.')
        ] = False,
        is_suspicious: Annotated[
            bool, Doc('A flag to determine if suspicious-activity context should be used.')
        ] = False,
        object_refs: Annotated[list, Doc('A list of objects to group together.')] = None,
        author: Annotated[stix2.Identity, Doc('A Recorded Future Identity.')] = None,
    ):
        """Grouping of STIX2 objects. Usually as part of the same event."""
        self.name = name
        self.description = description
        if is_malware:
            self.context = 'malware-analysis'
        elif is_suspicious:
            self.context = 'suspicious-activity'
        else:
            self.context = 'unspecified'
        self.object_refs = object_refs or []
        self.stix_obj = None
        super().__init__(name, author)

    def create_stix_object(self) -> None:
        """Creates STIX objects from object attributes."""
        self.stix_obj = stix2.Grouping(
            id=self._generate_id(),
            name=self.name,
            description=self.description,
            context=self.context,
            object_refs=self.object_refs,
            created_by_ref=self.author.id,
        )

    def _generate_id(self) -> str:
        """Generates an ID."""
        desc = self.description if self.description is not None else ''
        return 'grouping--' + generate_uuid(name=self.name, description=desc)


class Relationship(BaseStixEntity):
    """Represents Relationship SDO."""

    def __init__(
        self,
        source: Annotated[str, Doc('The source of the relationship.')],
        target: Annotated[str, Doc('The target of the relationship.')],
        type_: Annotated[str, Doc('How the source relates to the target.')],
        author: Annotated[stix2.Identity, Doc('A Recorded Future Identity.')] = None,
    ) -> None:
        """Relationship."""
        self.source = source
        self.target = target
        self.type_ = type_
        self.stix_obj = None
        super().__init__(None, author)

    def create_stix_object(self) -> None:
        """Creates the Relationship object."""
        self.stix_obj = stix2.Relationship(
            id=self._generate_id(),
            relationship_type=self.type_,
            source_ref=self.source,
            target_ref=self.target,
            created_by_ref=self.author.id,
        )

    def _generate_id(self) -> str:
        """Generates an ID."""
        return 'relationship--' + generate_uuid(
            source=self.source,
            target=self.target,
            type=self.type_,
        )


class NoteEntity(BaseStixEntity):
    """Note SDO."""

    def __init__(
        self,
        name: Annotated[str, Doc('The title of the note.')],
        content: Annotated[str, Doc('The content or text of the note.')],
        object_refs: Annotated[list, Doc('A list of SDO IDs the note should be attached to.')],
        author: Annotated[stix2.Identity, Doc('A Recorded Future Identity.')] = None,
    ) -> None:
        """Note Entity."""
        self.content = content
        self.object_refs = object_refs
        self.stix_obj = None
        super().__init__(name, author)

    def create_stix_object(self) -> None:
        """Creates the Note object."""
        self.stix_obj = stix2.Note(
            id=self._generate_id(),
            abstract=self.name,
            content=self.content,
            object_refs=self.object_refs,
            created_by_ref=self.author.id,
        )

    def _generate_id(self) -> str:
        """Generates an ID."""
        return 'note--' + generate_uuid(name=self.name, content=self.content)


class IndicatorEntity(BaseStixEntity):
    """Indicator SDO."""

    def __init__(
        self,
        name: Annotated[str, Doc('An indicator value.')],
        type_: Annotated[
            str,
            Doc(
                """
                A Recorded Future type of indicator.
                Options: 'IpAddress', 'InternetDomainName', 'URL', 'FileHash'.
                """
            ),
        ],
        description: Annotated[
            str, Doc('A description of the indicator, usually an AI Insight.')
        ] = None,
        author: Annotated[stix2.Identity, Doc('A Recorded Future Identity.')] = None,
        create_indicator: Annotated[
            bool, Doc('A flag that governs if the indicator should be created.')
        ] = True,
        create_obs: Annotated[
            bool, Doc('A flag that governs if the observable should be created.')
        ] = True,
        confidence: Annotated[int, Doc('A confidence score of the indicator.')] = None,
        labels: Annotated[list, Doc('Labels applied to the indicator, often risk rules.')] = None,
        tlp_marking: Annotated[str, Doc('The TLP level. Defaults to amber.')] = 'amber',
    ):
        """Indicator container. Contains indicator, observable, and relationship between them.

        Raises:
            STIX2TransformError: If indicator type is not supported.
        """
        if not create_indicator and not create_obs:
            raise STIX2TransformError(
                'Inidcator must create at least one of "Observable" or "Indicator"',
            )

        type_ = CONVERTED_TYPES.get(type_, type_)

        if type_ not in INDICATOR_TYPES:
            raise STIX2TransformError(
                f'Indicator {name} of type {type_} not one of: {", ".join(INDICATOR_TYPES)}'
            )

        self.type = type_
        if not author:
            author = self._create_author()
        self.author = author
        self.name = name
        self.confidence = confidence
        self.description = description
        self.labels = labels
        self.tlp = tlp_marking
        self.indicator = None
        self.observable = None
        self.relationship = None
        self.stix_objects = []
        if create_indicator:
            self.indicator = self._generate_indicator()
            self.stix_objects.append(self.indicator)
        if create_obs:
            self.observable = self._generate_observable()
            self.stix_objects.append(self.observable)
        if self.indicator and self.observable:
            self.relationship = self._generate_relationship()
            self.stix_objects.append(self.relationship)

    def _generate_indicator(self) -> stix2.Indicator:
        """Creates STIX2 Indicator Object."""
        return stix2.Indicator(
            id=self._generate_indicator_id(),
            name=self.name,
            confidence=self.confidence,
            pattern_type='stix',
            pattern=self._generate_pattern(),
            created_by_ref=self.author.id,
            labels=self.labels,
            description=self.description,
            object_marking_refs=TLP_MAP.get(self.tlp),
            external_references=self._generate_external_references(),
        )

    def _generate_indicator_id(self) -> str:
        """Creates an indicator ID string."""
        return 'indicator--' + generate_uuid(name=self.name)

    def _generate_pattern(self) -> str:
        """Generates a stix2 pattern for indicators."""
        if self.type == 'IpAddress':
            if ':' in self.name:
                return f"[ipv6-addr:value = '{self.name}']"
            return f"[ipv4-addr:value = '{self.name}']"
        if self.type == 'InternetDomainName':
            return f"[domain-name:value = '{self.name}']"
        if self.type == 'URL':
            ioc = self.name.replace('\\', '\\\\')
            ioc = ioc.replace("'", "\\'")
            return f"[url:value = '{ioc}']"
        if self.type == 'FileHash':
            return f"[file:hashes.'{self._determine_algorithm()}' = '{self.name}']"
        return None

    def _determine_algorithm(self) -> str:
        """Determines Hash Algorithm."""
        if len(self.name) == 64:
            return 'SHA-256'
        if len(self.name) == 40:
            return 'SHA-1'
        if len(self.name) == 32:
            return 'MD5'
        msg = (
            f'Could not determine hash type for {self.name}. Only MD5, SHA1'
            ' and SHA256 hashes are supported'
        )
        raise STIX2TransformError(msg)

    def _generate_external_references(self):
        external_references = []
        intel_card_url = INDICATOR_INTEL_CARD_URL.format(
            INDICATOR_TYPE_TO_RF_PORTAL_MAP[self.type],
            self.name,
        )
        external_references.append(
            {
                'source_name': 'View Intel Card in Recorded Future',
                'url': intel_card_url,
            },
        )

        return external_references

    def _generate_observable(
        self,
    ) -> Union[stix2.IPv6Address, stix2.IPv4Address, stix2.DomainName, stix2.File, stix2.URL]:
        """Creates stix2 observable."""
        uuid = generate_uuid(name=self.name)
        if self.type == 'IpAddress':
            if ':' in self.name:
                return stix2.IPv6Address(id='ipv6-addr--' + uuid, value=self.name)
            return stix2.IPv4Address(id='ipv4-addr--' + uuid, value=self.name)
        if self.type == 'InternetDomainName':
            return stix2.DomainName(id='domain-name--' + uuid, value=self.name)
        if self.type == 'URL':
            return stix2.URL(id='url--' + uuid, value=self.name)
        if self.type == 'FileHash':
            algo = self._determine_algorithm()
            return stix2.File(id='file--' + uuid, hashes={algo: self.name})
        raise STIX2TransformError('')

    def _generate_relationship(self) -> stix2.Relationship:
        return stix2.Relationship(
            id='relationship--'
            + generate_uuid(source=self.indicator.id, target=self.observable.id, type='based-on'),
            relationship_type='based-on',
            source_ref=self.indicator.id,
            target_ref=self.observable.id,
            created_by_ref=self.author.id,
        )

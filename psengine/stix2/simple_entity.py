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

import stix2

from .base_stix_entity import BaseStixEntity
from .constants import IDENTITY_TYPE_TO_CLASS
from .util import generate_uuid


class TTP(BaseStixEntity):
    """Converts MITRE T codes to AttackPattern."""

    def create_stix_object(self) -> None:
        """Creates AttackPattern objects from object attributes."""
        self.stix_obj = stix2.AttackPattern(
            id=self._generate_id(),
            name=self.name,
            created_by_ref=self.author.id,
            custom_properties={'x_mitre_id': self.name},
        )

    def _generate_id(self) -> str:
        """Generates an ID."""
        return 'attack-pattern--' + generate_uuid(name=self.name)


class Identity(BaseStixEntity):
    """Converts various RF entity types to a STIX2 Identity."""

    def __init__(self, name: str, rf_type: str, author: str = None) -> None:
        """Init Identity Class.

        Args:
            name (str): Name of the Identity
            rf_type (str): Recorded Future type of the identity
            author (str, optional): Recorded Future author object
        """
        self.rf_type = rf_type
        super().__init__(name, author)

    def create_stix_object(self) -> None:
        """Creates STIX objects from object attributes."""
        self.stix_obj = stix2.Identity(
            id=self._generate_id(),
            name=self.name,
            identity_class=self.create_id_class(),
            created_by_ref=self.author.id,
        )

    def create_id_class(self):
        """Creates a STIX2 identity class."""
        return IDENTITY_TYPE_TO_CLASS[self.rf_type]

    def _generate_id(self) -> str:
        """Generates an ID."""
        return 'identity--' + generate_uuid(name=self.name, identity_class=self.rf_type)


class ThreatActor(BaseStixEntity):
    """Converts various RF Threat Actor Organization to a STIX2 Threat Actor."""

    def create_stix_object(self) -> None:
        """Creates STIX objects from object attributes."""
        self.stix_obj = stix2.ThreatActor(
            id=self._generate_id(),
            name=self.name,
            created_by_ref=self.author.id,
        )

    def _generate_id(self) -> str:
        """Generates an ID."""
        return 'threat-actor--' + generate_uuid(name=self.name)


class IntrusionSet(BaseStixEntity):
    """Converts Threat Actor to Intrusion Set SDO."""

    def create_stix_object(self) -> None:
        """Creates STIX objects from object attributes."""
        self.stix_obj = stix2.IntrusionSet(
            id=self._generate_id(),
            name=self.name,
            created_by_ref=self.author.id,
        )

    def _generate_id(self) -> str:
        """Generates an ID."""
        return 'intrusion-set--' + generate_uuid(name=self.name)


class Malware(BaseStixEntity):
    """Converts Malware to a Malware SDO."""

    def create_stix_object(self) -> None:
        """Creates STIX objects from object attributes."""
        self.stix_obj = stix2.Malware(
            id=self._generate_id(),
            name=self.name,
            is_family=False,
            created_by_ref=self.author.id,
        )

    def _generate_id(self) -> str:
        """Generates an ID."""
        return 'malware--' + generate_uuid(name=self.name)


class Vulnerability(BaseStixEntity):
    """Converts a CyberVulnerability to a Vulnerability SDO."""

    def __init__(self, name: str, description: str = None, author: str = None) -> None:
        """Init Vulnerability Class.

        Args:
            name (str): Name of the Identity
            description (str, optional): Vulnerability description
            author (str, optional): Recorded Future author object

        """
        self.description = description
        super().__init__(name, author)

    def create_stix_object(self) -> None:
        """Creates STIX objects from object attributes."""
        self.stix_obj = stix2.Vulnerability(
            id=self._generate_id(),
            description=self.description,
            name=self.name,
            created_by_ref=self.author.id,
        )

    def _generate_id(self) -> str:
        """Generates an ID."""
        return 'vulnerability--' + generate_uuid(name=self.name)

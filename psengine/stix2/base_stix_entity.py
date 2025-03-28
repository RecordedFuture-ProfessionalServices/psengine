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

from .util import create_rf_author, generate_uuid


class BaseStixEntity:
    """Base STIX entity class for Recorded Future entities."""

    def __init__(self, name: str, author: stix2.Identity = None) -> None:
        """Initializes base STIX entity.

        Args:
            name (str): Name of entity
            author (stix2.Identity): Recorded Future Identity object

        """
        self.name = name
        if not author:
            author = self._create_author()
        self.author = author
        self.stix_obj = None
        self.create_stix_object()

    def __str__(self) -> str:
        """String representation of entity.

        Returns:
            str: String representation of entity
        """
        return f'Base STIX Entity: {self.name}, Author Name: {self.author.name}'

    def create_stix_object(self) -> None:
        """Creates STIX objects from object attributes."""

    def _create_author(self) -> stix2.Identity:
        """Creates author object if it doesn't already exist."""
        return create_rf_author()

    def __eq__(self, other) -> bool:
        """Verify if two STIX Objects are the same."""
        return self._generate_id() == other._generate_id()

    def __hash__(self) -> int:
        """Hash for set function."""
        return hash(self._generate_id())

    def _generate_id(self) -> str:
        """Generates an ID."""
        return 'invalid-prefix--' + generate_uuid(name=self.name)

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
from functools import total_ordering
from itertools import chain
from typing import Optional

from pydantic import Field, field_validator

from ..common_models import IdName, IdNameTypeDescription, RFBaseModel
from ..constants import TIMESTAMP_STR
from .markdown.markdown import _markdown_alert
from .models import (
    AlertAiInsight,
    AlertDeprecation,
    AlertLog,
    AlertReview,
    AlertURL,
    ClassicAlertHit,
    EnrichedEntity,
    NotificationSettings,
    OwnerOrganisationDetails,
    TriggeredBy,
)


@total_ordering
class ClassicAlert(RFBaseModel):
    """Validate data received from ``/v3/alerts/{id}``.

    Methods:
        __hash__:
            Returns a hash value based on the ``id_``.

        __eq__:
            Checks equality between two ClassicAlert instances based on their ``id_``.

        __gt__:
            Defines a greater-than comparison between two ClassicAlert instances based on their
            log triggered timestamp.

        __str__:
            Returns a string representation of the ClassicAlert instance with:
            ``id_``, triggered timestamp, title, and alerting rule name.

            .. code-block:: python

                >>> print(alert_id_response)
                Classic Alert ID: a123, Triggered: 2024-05-21 10:42:30AM, Title: Example Alert

    Total Ordering:
        The ordering of ClassicAlert instances is determined primarily by the log triggered
        timestamp. If two instances have the same triggered timestamp, their ``id_`` is used as a
        secondary criterion for ordering.
    """

    id_: str = Field(alias='id')
    log: AlertLog
    title: str
    review: Optional[AlertReview] = None
    owner_organisation_details: Optional[OwnerOrganisationDetails] = None
    url: Optional[AlertURL] = None
    rule: Optional[AlertDeprecation] = None
    hits: Optional[list[ClassicAlertHit]] = None
    enriched_entities: Optional[list[EnrichedEntity]] = None
    ai_insights: Optional[AlertAiInsight] = None
    type_: str = Field(alias='type', default=None)
    triggered_by: Optional[list[TriggeredBy]] = None

    _images: Optional[dict] = {}

    @field_validator('triggered_by', mode='before')
    @classmethod
    def parse_trigger_by(cls, data: list[dict]) -> list[dict]:
        """Parses a list of data dictionaries to extract and format entity paths.

        Each entity path is transformed into a formatted string where each entity is represented as
        'EntityName (EntityType)', joined by ' -> '.
        If an entity's type is 'MetaType', it is formatted as 'Any EntityName' instead.

        Args:
            data (List[Dict]): A list of dictionaries, each containing a 'reference_id' and an
                               'entity_paths' list.

        Returns:
            List[Dict]: A list of dictionaries with 'reference_id' and a list of unique formatted
                        'triggered_by_strings' paths.

        Example:
            Input:

            .. code-block::

                [
                    {
                        'reference_id': '123',
                        'entity_paths': [
                            [
                                {'entity': {'name': 'URL1', 'type': 'URL'}},
                                {'entity': {'name': 'Domain1', 'type': 'InternetDomainName'}}
                            ],
                            [
                                {'entity': {'name': 'URL1', 'type': 'URL'}},
                                {'entity': {'name': 'Domain1', 'type': 'InternetDomainName'}}
                            ]
                        ]
                    }
                ]

            Output:

            .. code-block::

                [
                    {
                        'reference_id': '123',
                        'triggered_by_strings': [
                            'URL1 (URL) -> Domain1 (InternetDomainName)'
                        ]
                    }
                ]
        """
        result = []
        for item in data:
            reference_id = item.get('reference_id')
            entity_paths = item.get('entity_paths', [])
            seen_strings = set()
            to_string = []

            for path in entity_paths:
                formatted_entities = [
                    (
                        f'Any {entity["name"]}'
                        if entity.get('type') == 'MetaType'
                        else f'{entity["name"]} ({entity["type"]})'
                    )
                    for obj in path
                    if (entity := obj.get('entity'))
                ]
                parsed_string = ' -> '.join(formatted_entities)
                if parsed_string not in seen_strings:
                    seen_strings.add(parsed_string)
                    to_string.append(parsed_string)

            result.append({'reference_id': reference_id, 'triggered_by_strings': to_string})
        return result

    def __hash__(self):
        return hash(self.id_)

    def __eq__(self, other: 'ClassicAlert'):
        return self.id_ == other.id_

    def __gt__(self, other: 'ClassicAlert'):
        return self.log.triggered > other.log.triggered

    def __str__(self):
        return (
            f'Classic Alert ID: {self.id_}, '
            f'Triggered: {self.log.triggered.strftime(TIMESTAMP_STR)}, '
            f'Title: {self.title}, Alerting Rule: {self.rule.name}'
        )

    def triggered_by_from_hit(self, hit: ClassicAlertHit) -> list[str]:
        """From an Alert Hit block, returns the related Triggered By string representation."""
        return list(
            chain.from_iterable(
                t.triggered_by_strings for t in self.triggered_by if t.reference_id == hit.id_
            )
        )

    def store_image(self, image_id: str, image_bytes: bytes) -> None:
        """Stores the image id and image bytes in ``@images`` dictionary.

        Example:
            .. code-block:: python

                {
                    image_id: image_bytes,
                    image_id: image_bytes
                }


        Args:
            image_id (str): image id
            image_bytes (bytes): image bytes
        """
        self._images[image_id] = image_bytes

    def markdown(
        self,
        owner_org: bool = False,
        ai_insights: bool = True,
        fragment_entities: bool = True,
        triggered_by: bool = True,
        html_tags: bool = False,
        character_limit: int = None,
        defang_iocs: bool = False,
    ):
        """Returns a markdown string representation of the ``ClassicAlert`` instance.

        This function works on ``ClassicAlert`` instances returned by ``ClassicAlertMgr.fetch()``,
        if you are passing the result of ``ClassicAlertMgr.search()`` make sure the ``search``
        method has been called with all the fields. Keep in mind that this will make the
        ``search`` slower.

        Args:
            self (ClassicAlert): ClassicAlert instance to create markdown from.
            owner_org (bool, optional): Include owner org details. Defaults to False.
            ai_insights (bool, optional): Include AI insights. Defaults to True.
            fragment_entities (bool, optional): Include fragment entities. Defaults to True.
            triggered_by (bool, optional): Include triggered by. Defaults to True.
            html_tags (bool, optional): Include HTML tags in the markdown. Defaults to False.
            character_limit (int, optional): Character limit for the markdown. Defaults to None.
            defang_iocs (bool, optional): Defang IOCs in hits. Defaults to False.

        Raises:
            AlertMarkdownError: If fields are not available.

        Returns:
            str: Markdown representation of the alert.
        """
        return _markdown_alert(
            self,
            owner_org=owner_org,
            ai_insights=ai_insights,
            fragment_entities=fragment_entities,
            triggered_by=triggered_by,
            html_tags=html_tags,
            character_limit=character_limit,
            defang_iocs=defang_iocs,
        )

    @property
    def images(self) -> dict:
        """If the alert has images, then return them in a dict.

        Example:
            .. code-block:: python

                {
                    image_id: image_bytes,
                    image_id: image_bytes
                }


        Returns:
            dict: dictionary of image ids and image bytes
        """
        return self._images


class AlertRuleOut(RFBaseModel):
    """Validate data received from ``v2/alert/rule``."""

    intelligence_goals: list[IdName]
    priority: bool = None
    tags: list[IdNameTypeDescription] = None
    id_: str = Field(alias='id')
    owner: IdName
    title: str
    created: datetime
    notification_settings: NotificationSettings
    enabled: bool

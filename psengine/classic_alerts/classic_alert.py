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
from typing import Annotated, Optional

from pydantic import Field, field_validator
from typing_extensions import Doc

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
    """Validate data received from the `/v3/alerts/{id}` endpoint.

    This class supports hashing, equality comparison, string representation, and total
    ordering of `ClassicAlert` instances.

    Hashing:
        Returns a hash value based on the `id_`.

    Equality:
        Checks equality between two `ClassicAlert` instances based on their `id_`.

    Greater-than Comparison:
        Defines a greater-than comparison between two `ClassicAlert` instances based on their
        log triggered timestamp.

    String Representation:
        Returns a string representation of the `ClassicAlert` instance including the `id_`,
        triggered timestamp, title, and alerting rule name.

        ```python
        >>> print(alert_id_response)
        Classic Alert ID: a123, Triggered: 2024-05-21 10:42:30AM, Title: Example Alert
        ```

    Total ordering:
        The ordering of `ClassicAlert` instances is determined primarily by the log triggered
        timestamp. If two instances have the same triggered timestamp, their `id_` is used as a
        secondary criterion.
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
    def parse_trigger_by(
        cls,
        data: Annotated[
            list[dict],
            Doc('List of dicts, each containing a `reference_id` and an `entity_paths` list.'),
        ],
    ) -> Annotated[
        list[dict],
        Doc("""
            List of dicts with `reference_id` and a list of unique formatted
            `triggered_by_strings` paths.
            """),
    ]:
        """Parse a list of data dictionaries to extract and format entity paths.

        Each entity path is transformed into a formatted string where each entity is represented as
        `EntityName (EntityType)`, joined by ` -> `.

        If an entity's type is `MetaType`, it is formatted as `Any EntityName` instead.

        Example:
        ```python
        >>> print(parse_triggered_by([
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
        ])
        [
            {
                'reference_id': '123',
                'triggered_by_strings': [
                    'URL1 (URL) -> Domain1 (InternetDomainName)'
                ]
            }
        ]
        ```
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

    def store_image(
        self,
        image_id: Annotated[str, Doc('The image ID.')],
        image_bytes: Annotated[bytes, Doc('The image bytes.')],
    ) -> None:
        """Store the image ID and image bytes in the `@images` dictionary.

        Example:
        ```python
        {
            image_id: image_bytes,
            image_id: image_bytes
        }
        ```
        """
        self._images[image_id] = image_bytes

    def markdown(
        self,
        owner_org: Annotated[bool, Doc('Include owner org details.')] = False,
        ai_insights: Annotated[bool, Doc('Include AI insights.')] = True,
        fragment_entities: Annotated[bool, Doc('Include fragment entities.')] = True,
        triggered_by: Annotated[bool, Doc('Include triggered by.')] = True,
        html_tags: Annotated[bool, Doc('Include HTML tags in the markdown.')] = False,
        character_limit: Annotated[Optional[int], Doc('Character limit for the markdown.')] = None,
        defang_iocs: Annotated[bool, Doc('Defang IOCs in hits.')] = False,
    ) -> Annotated[str, Doc('Markdown representation of the alert.')]:
        """Return a markdown string representation of the `ClassicAlert` instance.

        Note:
            This function works on `ClassicAlert` instances returned by `ClassicAlertMgr.fetch()`.
            If you are passing the result of `ClassicAlertMgr.search()`, make sure the `search`
            method has been called with all the fields. Keep in mind that this will make the
            `search` slower.

        Raises:
            AlertMarkdownError: If fields are not available.
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
    def images(self) -> Annotated[dict, Doc('A dictionary of image IDs and image bytes.')]:
        """Return a dictionary of images if the alert has any.

        Example:
        ```python
        {
            image_id: image_bytes,
            image_id: image_bytes
        }
        ```
        """
        return self._images


class AlertRuleOut(RFBaseModel):
    """Validate data received from `v2/alert/rule`."""

    intelligence_goals: list[IdName]
    priority: bool = None
    tags: list[IdNameTypeDescription] = None
    id_: str = Field(alias='id')
    owner: IdName
    title: str
    created: datetime
    notification_settings: NotificationSettings
    enabled: bool

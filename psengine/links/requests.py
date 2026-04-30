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

import re
from typing import Literal, Optional

from pydantic import Field, field_validator

from ..common_models import RFBaseModel


###########################################################
# Request Models (for POST /search)
###########################################################
class FilterTechnical(RFBaseModel):
    """Fields in the Technical Object of Filters."""

    timeframe: Optional[str] = Field(
        default=None,
        pattern=r'^-\d{1,2}d$',
        alias='timeframe',
        description=(
            'The time frame filter is used when only technical links newer than '
            'some date are of interest, e.g. -30d for the last 30 days '
            '(maximum timeframe is -90d).'
        ),
        examples=['-30d'],
    )
    events: Optional[list[str]] = Field(
        default=None,
        alias='events',
        description=(
            'The events filter is used to limit the search for links to references '
            'of a certain event type or types. The different types of events '
            'are found in Metadata:Events.'
        ),
        examples=[['InfrastructureAnalysis', 'TTPAnalysis']],
    )
    connected_entities: Optional[list[str]] = Field(
        default=None,
        alias='connected_entities',
        description=(
            'By using the connected entities filter, only technical links '
            'which themselves have links to entities specified in this list '
            'are returned.'
        ),
        examples=[['idn:google.com']],
    )

    @field_validator('timeframe')
    @classmethod
    def validate_time_range(cls, v: Optional[str]) -> Optional[str]:
        """Validate time range between 1 and 90."""
        if v is None:
            return v

        # Extract digits using regex
        match = re.search(r'(\d+)', v)
        if match:
            days = int(match.group(1))
            if not (1 <= days <= 90):
                raise ValueError(f'Timeframe must be between 1 and 90 days. Received {v}')
        return v


class LinksFilterObjects(RFBaseModel):
    """Objects in the fields data parameter of links."""

    sections: Optional[list[str]] = Field(
        default=None,
        alias='sections',
        description=(
            'Filters links only from a specific section (available from '
            'Metadata: Sections), for example only Actors, Tools & TTPs '
            'or only Indicators & Detection Rules.'
        ),
        examples=[['iU_ZsE', 'iU_ZsG', 'iU_ZsI']],
    )
    entity_types: Optional[list[str]] = Field(
        default=None,
        alias='entity_types',
        description=(
            'Filters links only of a specific entity type or types. '
            'The types of entities are returned by Metadata: Entities.'
        ),
        examples=[['AttackVector', 'Company', 'CyberVulnerability', 'Person']],
    )
    sources: Optional[list[str]] = Field(
        default=None,
        alias='sources',
        description=(
            'The API returns technical links and links from Insikt notes. '
            'This filter is used to limit the search to only one of the sources.'
        ),
        examples=[['technical', 'insikt']],
    )
    technical: Optional[FilterTechnical] = Field(
        default=None,
        alias='technical',
        description='Subfilters which applies specifically to technical links.',
        examples=[
            FilterTechnical(
                timeframe='-30d', events=['TTPAnalysis'], connected_entities=['idn:google.com']
            )
        ],
    )


class LinksLimitsObjects(RFBaseModel):
    """Objects in the limits object fields."""

    search_scope: Optional[Literal['small', 'medium', 'large']] = Field(
        default=None,
        alias='search_scope',
        description=(
            'The Links API searches for links in references, which is a '
            'performance intensive search. To ensure a fast response and a '
            'balance between different sources among events, there are some '
            'filters and limits applied. It would be impractical with an '
            'exhaustive search throughout all references from all time. Instead '
            'the API looks through the most recent references. References exist '
            'in different event types (the different types are available in '
            '/metadata/events) and to ensure some balance among sources, a '
            'number of references from each event type are selected. The exact '
            'number of references and Insikt notes fetched is controlled by '
            'the search_scope parameter: small = 10 references of each event '
            'type, 10 Insikt notes; medium = 50 references of each event type, '
            '50 Insikt notes; large = 100 references of each event type plus '
            'an extra 1000 references which can be of any type, 500 Insikt '
            'notes'
        ),
        examples=['small'],
    )
    per_entity_type: Optional[int] = Field(
        default=None,
        alias='per_entity_type',
        description=(
            'Limits how many entities /(IP, hashes, etc) are returned of '
            'each type from technical links and Insikt notes respectively.'
        ),
        examples=[1000],
    )

    @field_validator('per_entity_type')
    @classmethod
    def validate_per_entity_type(cls, v: Optional[int]) -> Optional[int]:
        """Validate per_entity_type."""
        if v is None:
            return v
        if v < 0 or v > 2147483647:
            raise ValueError(
                'per_entity_type must be int (greater than 0 and less than 2147483647)'
            )
        return v


class LinksSearchIn(RFBaseModel):
    """Query parameters for links."""

    entities: list[str] = Field(
        alias='entities',
        description=('Entities for which to search for links. Uses Recorded Future entity IDs.'),
        examples=['QCwdoU'],
    )
    filters: Optional[LinksFilterObjects] = Field(
        default=None,
        alias='filters',
        description='Filters for which links to search for.',
        examples=[
            LinksFilterObjects(
                sections=['iU_ZsE', 'iU_ZsG', 'iU_ZsI'],
                entity_types=['Company', 'Person'],
                sources=['technical', 'insikt'],
                technical=FilterTechnical(
                    timeframe='-30d', events=['TTPAnalysis'], connected_entities=['idn:google.com']
                ),
            )
        ],
    )
    limits: Optional[LinksLimitsObjects] = Field(
        default=None,
        alias='limits',
        description='Limits for the search.',
        examples=[LinksLimitsObjects(search_scope='small', per_entity_type=1000)],
    )

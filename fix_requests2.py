import re

with open("psengine/links/requests.py", "r") as f:
    content = f.read()

content = content.replace(
    "description=('The time frame filter is used when only technical links newer than some '\n                     'date are of interest, e.g. -30d for the last 30 days (maximum timeframe is -90d).'),",
    "description=(\n        'The time frame filter is used when only technical links newer than '\n        'some date are of interest, e.g. -30d for the last 30 days '\n        '(maximum timeframe is -90d).'\n    ),"
)

content = content.replace(
    "description=('The events filter is used to limit the search for links to references of a '\n                     'certain event type or types. The different types of events are found in Metadata:Events.'),",
    "description=(\n        'The events filter is used to limit the search for links to references '\n        'of a certain event type or types. The different types of events '\n        'are found in Metadata:Events.'\n    ),"
)

content = content.replace(
    "description=('By using the connected entities filter, only technical links which '\n                     'themselves have links to entities specified in this list are returned.'),",
    "description=(\n        'By using the connected entities filter, only technical links '\n        'which themselves have links to entities specified in this list '\n        'are returned.'\n    ),"
)

content = content.replace(
    "description=('Filters links only from a specific section (available from Metadata: Sections), '\n                     'for example only Actors, Tools & TTPs or only Indicators & Detection Rules.'),",
    "description=(\n        'Filters links only from a specific section (available from '\n        'Metadata: Sections), for example only Actors, Tools & TTPs '\n        'or only Indicators & Detection Rules.'\n    ),"
)

content = content.replace(
    "description=('Filters links only of a specific entity type or types. '\n                     'The types of entities are returned by Metadata: Entities.'),",
    "description=(\n        'Filters links only of a specific entity type or types. '\n        'The types of entities are returned by Metadata: Entities.'\n    ),"
)

content = content.replace(
    "description=('The API returns technical links and links from Insikt notes. '\n                     'This filter is used to limit the search to only one of the sources.'),",
    "description=(\n        'The API returns technical links and links from Insikt notes. '\n        'This filter is used to limit the search to only one of the sources.'\n    ),"
)

content = content.replace(
    "description=('The Links API searches for links in references, which is a performance intensive search. '\n                     'To ensure a fast response and a balance between different sources among events, '\n                     'there are some filters and limits applied. It would be impractical with an '\n                     'exhaustive search throughout all references from all time. Instead the API '\n                     'looks through the most recent references. References exist in different event '\n                     'types (the different types are available in /metadata/events) and to ensure '\n                     'some balance among sources, a number of references from each event type are selected. '\n                     'The exact number of references and Insikt notes fetched is controlled by '\n                     'the search_scope parameter: small = 10 references of each event type, 10 Insikt notes; '\n                     'medium = 50 references of each event type, 50 Insikt notes; '\n                     'large = 100 references of each event type plus an extra 1000 references '\n                     'which can be of any type, 500 Insikt notes'),",
    "description=(\n        'The Links API searches for links in references, which is a '\n        'performance intensive search. To ensure a fast response and a '\n        'balance between different sources among events, there are some '\n        'filters and limits applied. It would be impractical with an '\n        'exhaustive search throughout all references from all time. Instead '\n        'the API looks through the most recent references. References exist '\n        'in different event types (the different types are available in '\n        '/metadata/events) and to ensure some balance among sources, a '\n        'number of references from each event type are selected. The exact '\n        'number of references and Insikt notes fetched is controlled by '\n        'the search_scope parameter: small = 10 references of each event '\n        'type, 10 Insikt notes; medium = 50 references of each event type, '\n        '50 Insikt notes; large = 100 references of each event type plus '\n        'an extra 1000 references which can be of any type, 500 Insikt '\n        'notes'\n    ),"
)

content = content.replace(
    "description='Limits how many entities /(IP, hashes, etc) are returned of '\n        'each type from technical links and Insikt notes respectively.',",
    "description=(\n        'Limits how many entities /(IP, hashes, etc) are returned of '\n        'each type from technical links and Insikt notes respectively.'\n    ),"
)

content = content.replace(
    "description='Entities for which to search for links. Uses Recorded Future entity IDs.',",
    "description=(\n        'Entities for which to search for links. Uses Recorded Future '\n        'entity IDs.'\n    ),"
)

with open("psengine/links/requests.py", "w") as f:
    f.write(content)

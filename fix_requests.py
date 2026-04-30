import re

with open("psengine/links/requests.py", "r") as f:
    content = f.read()

content = content.replace('"""Fields in the Technical Object of Filters"""', '"""Fields in the Technical Object of Filters."""')
content = content.replace('"""Validate time range between 1 and 90"""', '"""Validate time range between 1 and 90."""')
content = content.replace('"""Objects in the fields data parameter of links"""', '"""Objects in the fields data parameter of links."""')
content = content.replace('"""Objects in the limits object fields"""', '"""Objects in the limits object fields."""')
content = content.replace('"""Validate per_entity_type"""', '"""Validate per_entity_type."""')
content = content.replace('"""Query parameters for links"""', '"""Query parameters for links."""')

content = content.replace(
    "description='The time frame filter is used when only technical links newer than some date are of interest, e.g. -30d for the last 30 days (maximum timeframe is -90d).',",
    "description=('The time frame filter is used when only technical links newer than some '\n                     'date are of interest, e.g. -30d for the last 30 days (maximum timeframe is -90d).'),"
)

content = content.replace(
    "description='The events filter is used to limit the search for links to references of a certain event type or types. The different types of events are found in Metadata:Events.',",
    "description=('The events filter is used to limit the search for links to references of a '\n                     'certain event type or types. The different types of events are found in Metadata:Events.'),"
)

content = content.replace(
    "description='By using the connected entities filter, only technical links which themselves have links to entities specified in this list are returned.',",
    "description=('By using the connected entities filter, only technical links which '\n                     'themselves have links to entities specified in this list are returned.'),"
)

content = content.replace(
    "description='Filters links only from a specific section (available from Metadata: Sections), for example only Actors, Tools & TTPs or only Indicators & Detection Rules.',",
    "description=('Filters links only from a specific section (available from Metadata: Sections), '\n                     'for example only Actors, Tools & TTPs or only Indicators & Detection Rules.'),"
)

content = content.replace(
    "description='Filters links only of a specific entity type or types. The types of entities are returned by Metadata: Entities.',",
    "description=('Filters links only of a specific entity type or types. '\n                     'The types of entities are returned by Metadata: Entities.'),"
)

content = content.replace(
    "description='The API returns technical links and links from Insikt notes. This filter is used to limit the search to only one of the sources.',",
    "description=('The API returns technical links and links from Insikt notes. '\n                     'This filter is used to limit the search to only one of the sources.'),"
)

search_scope_desc_orig = """description='The Links API searches for links in references, which is a performance intensive search. To ensure a fast response and a balance between different sources among events, there are some filters and limits applied.'
        'It would be impractical with an exhaustive search throughout all references from all time. Instead the API looks through the most recent references. References exist in different event types (the different types are available in /metadata/events) and to ensure some balance among sources, a number of references from each event type are selected.'
        'The exact number of references and Insikt notes fetched is controlled by the search_scope parameter:'
        'small = 10 references of each event type, 10 Insikt notes'
        'medium = 50 references of each event type, 50 Insikt notes'
        'large = 100 references of each event type plus an extra 1000 references which can be of any type, 500 Insikt notes',"""

search_scope_desc_new = """description=('The Links API searches for links in references, which is a performance intensive search. '
                     'To ensure a fast response and a balance between different sources among events, '
                     'there are some filters and limits applied. It would be impractical with an '
                     'exhaustive search throughout all references from all time. Instead the API '
                     'looks through the most recent references. References exist in different event '
                     'types (the different types are available in /metadata/events) and to ensure '
                     'some balance among sources, a number of references from each event type are selected. '
                     'The exact number of references and Insikt notes fetched is controlled by '
                     'the search_scope parameter: small = 10 references of each event type, 10 Insikt notes; '
                     'medium = 50 references of each event type, 50 Insikt notes; '
                     'large = 100 references of each event type plus an extra 1000 references '
                     'which can be of any type, 500 Insikt notes'),"""

content = content.replace(search_scope_desc_orig, search_scope_desc_new)

with open("psengine/links/requests.py", "w") as f:
    f.write(content)

import re

with open("psengine/links/response.py", "r") as f:
    content = f.read()

content = content.replace(
    "    missed_links: Annotated[\n        int,\n        Doc(\n            'Used if search was executed over all time, this value is 0. Else, the value is number of missed links outside the requested timeframe.'\n        ),\n    ]\n",
    "    missed_links: Annotated[\n        int,\n        Doc(\n            'Used if search was executed over all time, this value is 0. '\n            'Else, the value is number of missed links outside the requested timeframe.'\n        ),\n    ]\n"
)

content = content.replace(
    "    missed_matches: Annotated[\n        int,\n        Doc(\n            'Used if fewer matches were found than max allowed per query, this value is 0. Else, the value is number of missed matches not returned in the result set due to size limitation.'\n        ),\n    ]\n",
    "    missed_matches: Annotated[\n        int,\n        Doc(\n            'Used if fewer matches were found than max allowed per query, this value is 0. '\n            'Else, the value is number of missed matches not returned in the result set '\n            'due to size limitation.'\n        ),\n    ]\n"
)

content = content.replace(
    "    missed_entities: Annotated[\n        int,\n        Doc(\n            'Used if fewer entities were found than max allowed, this value is 0. Else, the value is number of missed entities not returned in the result set due to size limitation.'\n        ),\n    ]\n",
    "    missed_entities: Annotated[\n        int,\n        Doc(\n            'Used if fewer entities were found than max allowed, this value is 0. '\n            'Else, the value is number of missed entities not returned in the result set '\n            'due to size limitation.'\n        ),\n    ]\n"
)

content = content.replace(
    "    filter_reasons: Annotated[\n        dict,\n        Doc(\n            'This is not currently used, but intended to hold potential reasons some links were not evaluated for return.'\n        ),\n    ]\n",
    "    filter_reasons: Annotated[\n        dict,\n        Doc(\n            'This is not currently used, but intended to hold potential reasons '\n            'some links were not evaluated for return.'\n        ),\n    ]\n"
)

content = content.replace(
    "    attributes: Annotated[\n        list[IdNameType],\n        Doc(\n            'Lists all entities mapped to the source of the links (currently either Insikt Group notes or a specific technical reference).'\n        ),\n    ]\n",
    "    attributes: Annotated[\n        list[IdNameType],\n        Doc(\n            'Lists all entities mapped to the source of the links '\n            '(currently either Insikt Group notes or a specific technical reference).'\n        ),\n    ]\n"
)

with open("psengine/links/response.py", "w") as f:
    f.write(content)

import re

with open("psengine/links/response.py", "r") as f:
    content = f.read()

content = content.replace(
    "description='Used if search was executed over all time, this value is 0. Else, the value is number of missed links outside the requested timeframe.',",
    "description=(\n        'Used if search was executed over all time, this value is 0. '\n        'Else, the value is number of missed links outside the requested timeframe.'\n    ),"
)

content = content.replace(
    "description='Used if fewer matches were found than max allowed per query, this value is 0. Else, the value is number of missed matches not returned in the result set due to size limitation.',",
    "description=(\n        'Used if fewer matches were found than max allowed per query, '\n        'this value is 0. Else, the value is number of missed matches '\n        'not returned in the result set due to size limitation.'\n    ),"
)

content = content.replace(
    "description='Used if fewer entities were found than max allowed, this value is 0. Else, the value is number of missed entities not returned in the result set due to size limitation.',",
    "description=(\n        'Used if fewer entities were found than max allowed, this value is 0. '\n        'Else, the value is number of missed entities not returned '\n        'in the result set due to size limitation.'\n    ),"
)

content = content.replace(
    "description='This is not currently used, but intended to hold potential reasons some links were not evaluated for return.',",
    "description=(\n        'This is not currently used, but intended to hold potential '\n        'reasons some links were not evaluated for return.'\n    ),"
)

content = content.replace(
    "description='Lists all entities mapped to the source of the links (currently either Insikt Group notes or a specific technical reference).',",
    "description=(\n        'Lists all entities mapped to the source of the links '\n        '(currently either Insikt Group notes or a specific technical reference).'\n    ),"
)

with open("psengine/links/response.py", "w") as f:
    f.write(content)

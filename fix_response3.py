import re

with open("psengine/links/response.py", "r") as f:
    content = f.read()

content = content.replace(
    "description=\"Includes an 'id' which is a filter value ID to use in the Links Search requests and a 'name' which is a human-readable name\",",
    "description=(\n        \"Includes an 'id' which is a filter value ID to use in the Links \"\n        \"Search requests and a 'name' which is a human-readable name\"\n    ),"
)

content = content.replace(
    "description='The response contains a small array of section objects, each with an id (used as filter value in Links: Search) and a human-readable name.'",
    "description=(\n        'The response contains a small array of section objects, each with '\n        'an id (used as filter value in Links: Search) and a human-readable name.'\n    )"
)

content = content.replace(
    "description='Returns event type objects. Use the id field as the filter value in Links Search.'",
    "description=(\n        'Returns event type objects. Use the id field as the filter value '\n        'in Links Search.'\n    )"
)

content = content.replace(
    "description='Returns the complete set of supported entity types. Use the id field as the filter value.'",
    "description=(\n        'Returns the complete set of supported entity types. Use the id '\n        'field as the filter value.'\n    )"
)


with open("psengine/links/response.py", "w") as f:
    f.write(content)

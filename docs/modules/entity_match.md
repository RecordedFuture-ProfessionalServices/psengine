## Introduction

The `EntityMatchMgr` class of the `entity_match` module allows you to search for the Recorded Future ID of an entity.

See the [**API Reference**](../api/entity_match/entity_match_mgr.md) for internal details of the module.

## Notes

In this module, the `match` and `resolve_entity_id` methods are very similar. `match` returns a list of all possible matches, while `resolve_entity_id` is more strict and returns a single match.

Specifying the type of the entity leads to better results. For a complete list of entity types, see the support documentation.

## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Find the ID of CVE-2022-0847

In this example, we use the `resolve_entity_id` method to find the ID of the CVE. Since this method always returns a single result, you only need to check whether the `is_found` attribute is `True`. If it is, print the entity `id_`, which is in the `content` attribute.

```python
--8<-- "docs/examples/entity_match/example_1.py"
```

#### 2: Identify the entity with ID b89Juu and print its name

In this example, we use the `lookup` method to retrieve an entity by its ID. If the entity is not found, the method returns `None`, so we check for this condition before attempting to access the `name` attribute.

```python
--8<-- "docs/examples/entity_match/example_2.py"
```

#### 3: Handling entities that are not

If your search criteria is too broad or ambiguous, `resolve_entity_id` may not find the entity. The method does not raise an error, so you should check the `ResolveEntity.is_found` attribute to determine if a match was found, as shown in the example below.

```python
--8<-- "docs/examples/entity_match/example_3.py"
```

This example will print:

```
{   
    'content': "Multiple matches found for 'wannacry' of type 'Malware'",
    'entity': 'wannacry',
    'is_found': False
}
```

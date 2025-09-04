## Introduction

The `EntityMatchMgr` class of the `entity_match` module allows you to search for the Recorded Future ID of an entity.

See the [**API Reference**](../api/entity_match/entity_match_mgr.md) for internal details of the module.

## Notes

In this module, the `match` and `resolve_entity_id` methods are very similar. `match` returns a list of all possible matches, while `resolve_entity_id` is more strict and returns a single match.

Specifying the type of the entity leads to better results.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Find the ID of CVE-2022-0847

In this example, we use the `resolve_entity_id` method to find the ID of the CVE. Since this method always returns a single result, you only need to check whether the `is_found` attribute is `True`. If it is, print the entity `id_`, which is in the `content` attribute.

```python
--8<-- "docs/examples/entity_match/example_1.py"
```

#### Example 2: Find which entity has ID b89Juu and print its name

In this example, we use the `lookup` method to find the entity from the ID. If the entity is not found, the method returns `None`, which is why we use `if` before printing the `name` attribute.

```python
--8<-- "docs/examples/entity_match/example_2.py"
```

#### Example 3: Dealing with entities not found

If you are not specific enough about the entity you are looking for, or there are ambiguities, using `resolve_entity_id` might lead to an entity not found. The method does not raise an error, but you need to check the `ResolveEntity.is_found` attribute, as shown in the example.

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

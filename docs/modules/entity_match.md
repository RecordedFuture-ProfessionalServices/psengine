## Introduction 

The `EntityMatchMgr` class of the `entity_match` module allows to search for the Recorded Future ID of an entity.

See the [**API Reference**](../api/entity_match/entity_match_mgr.md) for internal details of the module.

## Notes

In this module the `match` and `resolve_entity_id` method are very similar. `match` will return a list of all the possible matches, while the `resolve_entity_id` is more strict, it will return a single match. 

Specifying the type of the entity leads to better results.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Find the ID of CVE-2022-0847

In this example we use the `resolve_entity_id` method to find the ID of the CVE. Since this method always return a single result, we only need to check if the `is_found` attribute has been set to `True`. If it is, we print the `id_` of the entity which is in the `content` attribute.

```python 
--8<-- "docs/examples/entity_match/example_1.py"
``` 

#### Example 2: Find which entity has ID b89Juu and print its name

In this example we use the `lookup` method to find the entity from the ID. In case of entity not found, the method will return `None` hence why we use the `if` before printing the attribute `name`.

```python 
--8<-- "docs/examples/entity_match/example_2.py"
``` 


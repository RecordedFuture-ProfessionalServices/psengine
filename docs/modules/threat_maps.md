## Introduction

The `ThreatMapMgr` class in the `threat_maps` module enables you to search for and retrieve enterprise threat maps. Currently this includes:

- Malware
- Actors

See the [**API Reference**](../api/threat_maps/threat_map_mgr.md) for internal details of the module.

## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Fetch all available threat maps

This example uses the `fetch_available_maps` method to fetch all threat maps available to an organization, including any sub-organization threat maps.

```python
--8<-- "docs/examples/threat_maps/example_1.py"
```

#### 2: Search for threat actor by name

In this example, we use the `search_threat_actor` method to find threat actors by name. We set the `name` to the target entity name and limit the results with `max_results`.

```python
--8<-- "docs/examples/threat_maps/example_2.py"
```

#### 3: Fetch malware threat map with categories and filter by scores

This example assumes that you have the malware category IDs from the `fetch_entity_categories` method. We use the `fetch_map` method to fetch the primary organization's malware threat map. By setting `map_type` to `malware`, we fetch the malware threat map only. To further narrow the results to those related to Rootkit and Linux Malware categories, we use the category IDs: `["0fK7b", "RTkDB2"]`. Once the map is returned we then filter for targeted entities based on opportunity and prevalence axis scores.

```python
--8<-- "docs/examples/threat_maps/example_3.py"
```

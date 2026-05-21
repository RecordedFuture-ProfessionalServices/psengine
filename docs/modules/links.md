## Introduction

The `LinksMgr` class of the `links` module allows you to find entities connected to one or more Recorded Future entities.

See the [**API Reference**](../api/links/links_mgr.md) for internal details of the module.

## Notes

The `search` method expects Recorded Future entity IDs (for example, `QCwdoU`), not entity names. If you only have a name, use the `entity_match` module first to resolve the ID.

The response is batched: you get one result per input entity. A specific entity can fail while others succeed, so always check `result.error` before iterating over `result.links`.

For filters such as sections, events, and entity types, use the metadata methods (`list_sections`, `list_events`, and `list_entity_types`) to retrieve valid IDs before calling `search`.

## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Search links for an entity and handle per-entity errors

In this example, we call `search` with a single entity ID. For each result, we first check `result.error`. If there is no error, we print the source entity and the first 5 linked entities returned by the API.

```python
--8<-- "docs/examples/links/example_1.py"
```

The output will be:

```
Entity: Lazarus Group
  -> CVE-2022-47966 source:insikt
  -> 24988feb1b38f400069acec4514aa4deea3f6ca8ceb5296f54926e2b22af1e5a source:insikt
  -> 36db27f5eb3343cfc72d261d78da44957a49cb6731acb50a96ea5694f4d616c5 source:insikt
  -> ffec6e6d4e314f64f5d31c62024252abde7f77acdd63991cb16923ff17828885 source:insikt
  -> 3e5fd9acdab438ffc8b2cce48c91679d3f980d08f9dea47d5e1039d352cd64fb source:insikt
```


#### 2: Filter link results and apply limits

In this example, we pass filter and limit arguments directly to `search` (for example `sources`, `entity_types`, `timeframe`, `search_scope`, and `per_entity_type`) to narrow results to technical malware links seen in the last 30 days and cap result size per entity type.

```python
--8<-- "docs/examples/links/example_2.py"
```

#### 3: Discover available metadata for filters

In this example, we list valid sections, event types, and entity types. These IDs can be reused in the `search` filter arguments when building queries.

```python
--8<-- "docs/examples/links/example_3.py"
```

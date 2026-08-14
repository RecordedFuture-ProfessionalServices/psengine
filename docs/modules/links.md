## Introduction

The `LinksMgr` class of the `links` module allows you to search for technically validated relationships between threat intelligence entities in the Recorded Future Intelligence Cloud — connections established through sandbox analysis, infrastructure analysis, network traffic analysis, and Insikt Group research.

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
--8 < --'docs/examples/links/example_1.py'
```

The output will be:

```
Entity: Lazarus Group
  -> CVE-2022-47966 source: insikt
  -> 24988feb1b38f400069acec4514aa4deea3f6ca8ceb5296f54926e2b22af1e5a source: insikt
  -> 36db27f5eb3343cfc72d261d78da44957a49cb6731acb50a96ea5694f4d616c5 source: insikt
  -> ffec6e6d4e314f64f5d31c62024252abde7f77acdd63991cb16923ff17828885 source: insikt
  -> 3e5fd9acdab438ffc8b2cce48c91679d3f980d08f9dea47d5e1039d352cd64fb source: insikt
```


#### 2: Filter link results and apply limits

In this example, we pass filter and limit arguments directly to `search` (for example `sources`, `entity_types`, `timeframe`, `search_scope`, and `per_entity_type`) to narrow results to technical malware links seen in the last 90 days and cap result size per entity type.

```python
--8 < --'docs/examples/links/example_2.py'
```

#### 3: Extract IOCs, Threat Actors and Malwares from links

Each item returned by `LinksMgr.search()` is an `EntityLinks` object. After checking `result.error`, you can use helper methods to extract common subsets from `result.links`:

- `result.iocs()`: returns linked IOCs grouped by IOC type (`type:InternetDomainName`, `type:CyberVulnerability`, `type:IpAddress`, `type:Hash`, `type:Url`). Each IOC item includes `id`, `type`, `name`, `risk_score`, and `source`.
- `result.ttps()`: returns linked MITRE ATT&CK techniques (`type:MitreAttackIdentifier`). Each item includes `id`, `type`, `name`, `display_name`, and `source`.
- `result.malwares()`: returns linked malware entities (`type:Malware`) with `id`, `type`, `name`, and `source`.
- `result.threat_actors()`: returns linked organizations (`type:Organization`) that are marked as threat actors through the `threat_actor` attribute.

```python
--8 < --'docs/examples/links/example_3.py'
```

This will output:

```
Entity: Lazarus Group

IOCs grouped by type:
  type:CyberVulnerability: 5
    - CVE-2022-47966 score:99
    - CVE-2019-3396 score:89
    - CVE-2022-0609 score:79
  type:Hash: 1273
    - c8706a586afa880fbf23ce662b7fc2925fd0384b8cde0a40f3c00a182c5a3d06 score:89
    - 9ab05d771d6face27502052af8e3a945ad66e3c6726a2dda637fa12641e2bca2 score:89
    - 084f904249f8655e925b4b330426df6b979cd3f630f7765dac405f2144755738 score:89
  type:InternetDomainName: 144
    - calendly.live score:74
    - pypilibrary.com score:72
    - test-wolf.com score:69
  type:IpAddress: 29
    - 172.96.137.224 score:55
    - 103.231.75.101 score:38
    - 23.27.140.49 score:32

TTPs:
  - T1082 (T1082 (System Information Discovery))
  - T1071 (T1071 (Application Layer Protocol))
  - TA0010 (TA0010 (Exfiltration))
  - T1027 (T1027 (Obfuscated Files or Information))
  - T1497.001 (T1497.001 (Virtualization/Sandbox Evasion: System Checks))

Malwares:
  - CIPHERROCKET
  - QuiteRAT
  - PondRAT
  - Trickbot
  - NukeSped
```

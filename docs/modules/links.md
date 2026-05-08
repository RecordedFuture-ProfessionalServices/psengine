## Introduction

The `LinksMgr` class of the `links` module lets you discover entities connected to a given Recorded Future entity. Links are sourced from two places:

- **technical** — automatically extracted relationships across recent references (the API selects the most recent references per event type, controlled by `search_scope`)
- **insikt** — relationships curated by Insikt Group analysts in published notes

Each connected entity comes back annotated with attributes such as risk score, risk level, criticality, and the section it was found under (for example *Actors, Tools & TTPs* or *Indicators & Detection Rules*).

The module also exposes three metadata listings — sections, event types, and entity types — that you can query to discover which filter values the API currently accepts.

See the [**API Reference**](../api/links/links_mgr.md) for internal details of the module.

## Notes

`LinksMgr.search` accepts a list of Recorded Future entity IDs (not free-text names). If you only have a name, look the entity up first via `EntityMatchMgr` or `LookupMgr` to obtain its ID.

The `filters` parameter is optional. If omitted, the API returns links from both sources across all sections and entity types within its default lookback. Static values (such as `sources`) are validated by the request models before the call is made; section, event, and entity-type IDs are validated server-side.

## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Discover entities connected to a given entity

This example uses `LinksMgr.search` with a single Recorded Future entity ID. The response is a `LinksSearchResponse` with one `SearchResultSet` per queried entity. Each result either contains a list of `LinkedEntity` objects under `links` or, if the API failed for that specific entity, an `error` payload — so the example checks `result.error` before iterating.

```python
--8<-- "docs/examples/links/example_1.py"
```

A typical line of the output looks like:

```
Entity: APT28 (Threat Actor)
  -> X-Agent (Malware) source=insikt
  -> Sofacy (Malware) source=insikt
  -> 185.86.148.5 (IpAddress) source=technical
```

#### 2: Narrow the search with filters and limits

This example restricts the search to technical links from the last 30 days, returning only `Malware` entities, and caps the result set with `LinksLimitsObjects`.

The `search_scope` value (`small`, `medium`, or `large`) controls how many references the API scans before returning links — `small` is the fastest, `large` the most thorough. `per_entity_type` caps the number of entities returned of each type.

`FilterTechnical.timeframe` accepts a relative string like `-30d`. The exact lookback bound is enforced by the API.

```python
--8<-- "docs/examples/links/example_2.py"
```

#### 3: Discover the available filter values

Section IDs, event types, and entity types are not stable strings you should hard-code — the API exposes them through three metadata endpoints. Use this example to print the current values before constructing a `LinksFilterObjects`.

```python
--8<-- "docs/examples/links/example_3.py"
```

The output is similar to:

```
Sections:
  iU_ZsE: Actors, Tools & TTPs
  iU_ZsG: Indicators & Detection Rules
  iU_ZsI: Targets & Vulnerabilities
  ...

Event types:
  TTPAnalysis: TTP Analysis
  InfrastructureAnalysis: Infrastructure Analysis
  ...

Entity types:
  Company: Company
  CyberVulnerability: Cyber Vulnerability
  Malware: Malware
  ...
```

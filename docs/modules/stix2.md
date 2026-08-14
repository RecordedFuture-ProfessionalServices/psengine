## Introduction

The `stix2` module allows you to use the `RisklistMgr`, `LookupMgr`, and `AnalystNoteMgr` and transform their output into a STIX2-compatible format.

See the [**API Reference**](../api/stix2/base_stix_entity.md) for internal details of the module.

## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Transform an analyst note into a STIX RFBundle

In this example, we take an analyst note with ID `o6_lui` using the `AnalystNoteMgr.lookup` method, fetch the attachment with the `AnalystNoteMgr.fetch_attachment` method, and create the bundle with the `RFBundle.from_analyst_note` method.

This creates an object that can be serialized with the `serialize` method and written to a file.

```python
--8 < --'docs/examples/stix2/example_1.py'
```

#### 2: Transform a risklist into a STIX RFBundle

Similar to the example above, here we use the `RisklistMgr.fetch_risklist` method to fetch the IP risklist `recentLinkedToAPT`. We validate the entries returned with the `validate` argument, and the risklist returned generates the bundle with `RFBundle.from_default_risklist`.

The bundle is then saved to a file after being serialized.

```python
--8 < --'docs/examples/stix2/example_2.py'
```

#### 3: Transform enriched IOCs into STIX RFBundles

In this example, we use the `LookupMgr` to enrich 4 IOCs using the `links`, `riskMapping`, and `aiInsights` fields. For each IOC, if it has been enriched, an `EnrichedIndicator` object is created, and the related bundle is saved to a file.

```python
--8 < --'docs/examples/stix2/example_2.py'
```

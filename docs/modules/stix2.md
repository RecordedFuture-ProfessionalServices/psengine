## Introduction 

The `stix2` module allows to use the `RisklistMgr`, `LookupMgr` and `AnalystNoteMgr` and transform their output into STIX2 compatible format.

See the [**API Reference**](../../api/stix2/base_stix_entity) for internal details of the module.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Transform an analyst note as STIX RFBundle.

In this example we are taking an analyst note with ID `o6_lui` using the `AnalystNoteMgr.lookup` method, fetching the attachment with the `AnalystNoteMgr.fetch_attachment` method and we create the bundle with the `RFBundle.from_analyst_note` method.

This create an object that can be serialized with the `serialize` method and written to file.

```python 
--8<-- "docs/examples/stix2/example_1.py"
``` 

#### Example 2: Transform a risklist as STIX RFBundle.

Similar to example 1, in this example we are using the `RisklistMgr.fetch_risklist` method to fetch the IP risklist `recentLinkedToAPT`. We validate the entries returned with the `validate` argument and the risklist returned is generates the bundle with `RFBundle.from_default_risklist`.

The bundle is then saved to file after being serialized.

```python 
--8<-- "docs/examples/stix2/example_2.py"
```

#### Example 3: Transform enriched IOCs as STIX RFBundles.

In this example we use the `LookupMgr` to enrich 4 IOCs using the `links`, `riskMapping` and `aiInsights` fields. For each IOC, if it has been eneriched, an `EnrichedIndicator` object is created, and the related bundle is saved to file.

```python 
--8<-- "docs/examples/stix2/example_2.py"
```

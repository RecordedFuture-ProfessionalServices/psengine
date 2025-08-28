## Introduction 

The `RisklistMgr` class of the `risklists` module allows to fetch risklists. A risklist is a file that contains a list of indicators with different levels of maliciousness. These risklists are often used as correlation files in SIEM tools. 

In Recorded Future the concept of "default" risklist means a risklist with usually up to 100.000 indicators with a score from 65 and above.

See the [**API Reference**](../api/risklists/risklist_mgr.md) for internal details of the module.

## Notes

1. The `fetch_risklist` method return a generator object. If it needs to be saved to file you should transform it to list first.
2. Even though there are CSV based risklists, PSEngine converts them to JSON.
3. With this module, fetching custom risklists is possible if any has been built for you.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Fetch and save the default domain risklist as JSON

In this example we are fetching the risklist with the `fetch_risklist` method, giving the arguments of `default` for the type of risklist and `domain` for the type of indicator. Since the file is converted by PSEngine into a JSON like structure we can convert the generator to list and then save it to file with `json.dumps`.

```python 
--8<-- "docs/examples/risklists/example_1a.py"
``` 

After executing the script you should have a file called `default_domain_rsiklist.json` in the `risklists` directory. However, you will see the content of the `EvidenceDetails` block is a JSON like string.

To have a complete JSON we can use the `validate` argument of the `fetch_risklist` method to:
1. Validate that each entry of the risklist respect a model
2. Dump the validated model with the fields we need

In the code below we are performing the same operations but passing the `DefaultRiskList` object (a `pydantic` model) to the `fetch_risklist`, and save the results to file.

What will happen is that while the risklist is converted to JSON it also gets validated. 
The `DefaultRiskList` model is already present in PSEngine, but a custom model can be used as well, see example 2

```python 
--8<-- "docs/examples/risklists/example_1b.py"
```

#### Example 2: Fetch and save a custom risklist as JSON and perform validation

In this example we are assuming that we want to build an script that ingest the Threat Actor related indicators from the Recorded Future risklist `ta_ip_risklist_v2.csv`.

The risklist has the following headers:
- Name,
- Risk,
- RiskString,
- EvidenceDetails,
- Sources,
- ThreatActorIDs,
- ThreatActorNames,
- ThreatActorAliases,
- ThreatActorCategories,
- ThreatActorNotes,
- IndicatorNotes

We want to validate and save the risklist without the `EvidenceDetails`, `Sources`and the related notes fields. These fields has been excluded only for the sake of making the example shorter.

This example is a bit longer but what we are doing is defining the `TARisklist` model which inherits from `RFBaseModel`. In the `TARiskist` model we define how the fields should be organized based on the needs of our tool. We could have left the fields untouched but it is often required to slightly manipulate some of the data for an easier ingestion.

The whole data manipulation is done using only `pydantic` constructs, like `BeforeValidator`  and `@field_validator`, they are just transforming the data from one shape to another, specifically from a dictionary to a list of dictionaries and from a JSON-like string to a JSON object respectively.

Once the model is defined we can fetch the risklist, validate the content and save it to file same as the previous examples.

```python 
--8<-- "docs/examples/risklists/example_2.py"
```

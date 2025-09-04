## Introduction

The `DetectionMgr` class of the `detection` module allows you to search and fetch detections. Detections means Yara, Sigma, and Snort detection rules.

See the [**API Reference**](../api/detection/detection_mgr.md) for internal details of the module.

## Notes

In this module, the `fetch` and `search` are exactly the same method. In fact, under the hood the `fetch` method calls the `search` method with the specified `doc_id`.
The reason why `fetch` exists is for a more understandable and easier interface when you want to retrieve a detection by its ID.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Fetch a detection rule and save it to a file

This example assumes that you have a detection rule ID either from a previously collected analyst note written by the Recorded Future Insikt Group or from an integration/security tool. We will use only two alert IDs for demonstration.
Here we have a detection rule with ID `doc:aqofps`, which is a Recorded Future–specific ID. After fetching it, you can save it with the `save_rule` helper function, which takes the whole `DetectionRule` object created by the `fetch` method and saves the content of the rule as a file.

```python
--8<-- "docs/examples/detection/example_1.py"
```

#### Example 2: Search for the last 10 Yara rules that are related to Command and Control

In this example, we use the `search` method, which allows you to search detection rules based on certain parameters. In this case, we use the `detection_rule` set to `yara` to filter for Yara rules only. To select only rules that are specific to Command and Control activities, we use the MITRE code entity `mitre:T1071`.
We then save each of the notes to a file.

```python
--8<-- "docs/examples/detection/example_2.py"
```

#### Example 3: Search for the last 10 detections related to the LogShell CVE-2021-44228 vulnerability

This example involves using a different module in combination with the `detection` module. It is very similar to Example 2, but in this case we cannot pass the entity `CVE-2021-44228` directly into the list of entities, since this parameter requires the Recorded Future ID of the entity.
To find it, we need to use the `entity_match` module. Please look at that module’s documentation for more information.

We first search for the CVE ID using the `entity_mgr.match` method. This always returns a list of entities of length less than or equal to `limit`, even if entities are not found. You can safely extract the first element and check its `is_found` attribute to see if the lookup was successful. If yes, you can use the `.content.id_` to filter the detection `search`.

```python
--8<-- "docs/examples/detection/example_3.py"
```

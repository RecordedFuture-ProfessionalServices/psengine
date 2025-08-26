## Introduction 

The `DetectionMgr` class of the `detection` module allows to search and fetch detections. Detections means Yara, Sigma and Snort detection rules.

See the [**API Reference**](../../api/detection/detection_mgr) for internal details of the module.

## Note

In this module the `fetch` and `search` are exactly the same method. In fact under the hood the `fetch` method is calling the `search` method with the specified `doc_id`.

## Examples

!!! warning

    Below are some examples of usage of the `detection` module. Consider adding error handling as necessary. All the errors that can be raised by each method or function are specified in the API Reference page.

#### Example 1: Fetch a detection rule and save it to file.

This example starts with the assumption that you have detection rule ID either from a previously collected analyst note written by the Recorded Future Insikt Group, or from an integration/security tool. e will use only two alert IDs for demonstration.
Here we have a detection rule with id `doc:aqofps`, which is a Recorded Future specific ID. After fetching it, we can save it with the `save_rule` helper function, which takes the whole `DetectionRule` object created by the `fetch` method and save the content of the rule as file. 

```python 
--8<-- "docs/examples/detection/example_1.py"
```

#### Example 2: Search for the last 10 Yara rules that are related to Command and Control.

In this example we use the `search` method which allows you to search detection rules based on certain parameters. In this case we use the `detection_rule` set to `yara` to filter for Yara rules only. To select only rules that are specific to Command and Control activies we use the MITRE code entity `mitre:T1071`.
We then save each of the notes to file.

```python 
--8<-- "docs/examples/detection/example_2.py"
```

#### Example 3: Search for last 10 detections related to LogShell CVE-2021-44228 vulnerability.

This example involves the usage of a different module in combination with the `detection` module. It is very similar to Example 2, but in this case we cannot pass the entity `CVE-2021-44228` directly into the list of entites, since this parameter requires the Recorded Future ID of the entity. 
To find it we need to use the `entity_match` module. Please look at the documentation of that module for more information.


We first search for the CVE id using the `entity_mgr.match` method. This always return a list of entities of length less than or equals to `limit`, even if entities are not found. We can safely extrac the first element and check its `is_found` attribute to see if the lookup was succesful. If yes we can use the `.content.id_` to filter the detection `search`. 

```python 
--8<-- "docs/examples/detection/example_3.py"
``` 

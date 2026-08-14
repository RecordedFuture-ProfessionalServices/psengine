## Introduction

The `DetectionMgr` class in the `detection` module enables you to search for and retrieve detection rules. Currently this includes:

- Yara
- Sigma
- Snort

See the [**API Reference**](../api/detection/detection_mgr.md) for internal details of the module.

## Notes

- In this module, the `fetch` and `search` methods are functionally identical. Internally, `fetch` simply calls `search` with the given `doc_id`. The `fetch` method is provided for convenience, making it easier to retrieve a detection rule by its ID.

## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Fetch a detection rule and save it to a file

This example assumes that you have a detection rule ID either from a previously collected analyst note written by the Recorded Future Insikt Group or from an integration/security tool. We will use only two alert IDs for demonstration.
Here we have a detection rule with ID `doc:aqofps`, which is a Recorded Future specific ID. After fetching it, you can save it with the `save_rule` helper function, which takes the whole `DetectionRule` object created by the `fetch` method and saves the content of the rule as a file.

```python
--8 < --'docs/examples/detection/example_1.py'
```

#### 2: Find the 10 detection rules published yesterday

In this example, we use the `search` method to find detection rules based on specific criteria. We set the `created_after` to a relative date, like `-1d` to fetch the rules that have been released yesterday.

```python
--8 < --'docs/examples/detection/example_2.py'
```

#### 3: Find 10 Yara rules related to Command and Control activities

In this example, we use the `search` method to find detection rules based on specific criteria. By setting `detection_rule` to `yara`, we filter for Yara rules only. To further narrow the results to those related to Command and Control activities, we use the MITRE code entity `mitre:T1071`. Each matching rule is then saved to a file.

```python
--8 < --'docs/examples/detection/example_3.py'
```

#### 4: Find 10 detection rules related to the LogShell CVE-2021-44228 vulnerability

This example involves using a different module in combination with the `detection` module. It is very similar to the example above, but in this case we cannot pass the entity `CVE-2021-44228` directly into the list of entities, since this parameter requires the Recorded Future ID of the entity.
To find it, we need to use the `entity_match` module. Please look at that module’s documentation for more information.

We first search for the CVE ID using the `entity_mgr.match` method. This always returns a list of entities of length less than or equal to `limit`, even if entities are not found. You can safely extract the first element and check its `is_found` attribute to see if the lookup was successful. If yes, you can use the `.content.id_` to filter the detection `search`.

```python
--8 < --'docs/examples/detection/example_4.py'
```

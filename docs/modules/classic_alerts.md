## Introduction

The `ClassicAlertMgr` class of the `classic_alerts` module allows you to fetch, search, and update alerts coming from your Recorded Future enterprise.

With classic alerts we mean:

- alerts related to the Recorded Future intelligence goal library
- custom alerts created by you from the advanced query builder

See the [**API Reference**](../api/classic_alerts/classic_alert_mgr.md) for internal details of the module.

## Notes

- The `search`, `fetch`, and `fetch_bulk` methods all return a `ClassicAlert` object, or a list of them. If you want to look for new alerts you can use the `search` endpoint, while if you have alert IDs and you need to look up the alerts related to them, you will need to use `fetch` (for a very small number of IDs to look up) or `fetch_bulk` (for bigger lookups).
- All the methods mentioned in point 1 accept a `fields` parameter to increase or reduce the information retrieved for each alert. The following fields are always requested: `id`, `log`, `title`, `rule`, no matter which `fields` you specify.
    - `search` uses only the required fields by default if the `fields` parameter is not specified.
    - `fetch` and `fetch_bulk` use all the fields if the `fields` parameter is not specified.
- The more fields are requested the slower the action will be; make sure to balance the number of fields and the amount of alerts to search or fetch. A full list of fields can be found in `ALL_CA_FIELDS` in the constants file for this module. [**Link**](../api/classic_alerts/constants.md#psengine.classic_alerts.constants.ALL_CA_FIELDS)

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Search the latest new alerts and save them as markdown

In order to search for newer alerts you can use the `search` method, with a `-1d` trigger time lookback. To further filter them out you can use the value `New` for the `status`.

To build the markdown for alerts we need all the fields, so you can use the `ALL_CA_FIELDS` list to get them all. In the `markdown` method we can specify some options to define a

```python
--8<-- "docs/examples/classic_alerts/example_1.py"
```

#### Example 2: From a list of alert IDs fetch the data and related images, save the images to file

!!! tip

    To replicate this example you will need to change the `ALERT_IDS` list with one or more IDs of alerts that triggered in your enterprise.
    Either hardcode them, or use the `search` method shown above. For each alert found, the `id_` attribute can be used to return the ID of that alert.

This example starts with the assumption that you have a list of alert IDs retrieved by a search, or a colleague, or another integration/security tool. We will use only two alert IDs for demonstration.

In this example we use the `fetch_bulk` method to download the alerts. We use `max_workers=2` to split the task into two threads for better performance.

The alerts might have an image ID in their payload, which will be collected by the `fetch_all_images` method. This method does not return the images but saves them in an `images` property of the alert. If you need to access these images programmatically you can do that with `alert.images`.

`save_images` will save in `OUTPUT_DIR` a `.png` file for each image called `img:<image_id>.png`.

```python
--8<-- "docs/examples/classic_alerts/example_2.py"
```

#### Example 3: Fetch all the hits of an alert, and save the result as a JSON file

!!! tip

    To replicate this example you will need to change the `ALERT_IDS` list with one or more IDs of alerts that triggered in your enterprise.
    Either hardcode them, or use the `search` method shown above. For each alert found, the `id_` attribute can be used to return the ID of that alert.

This example starts with the assumption that you have an alert ID retrieved by a search, or a colleague, or another integration/security tool. We will use only two alert IDs for demonstration.

The `fetch_hits` method allows you to download all the "Hits" of an alert, meaning the entities that triggered the alert to fire. The list of `ClassicAlertHit` objects returned by `fetch_hits` is based on how many hits have triggered the alert. If more than one, you will see more than one object that has the same `alert_id` field.
For this reason we first create a dictionary `data` where we group all the hits by `alert_id`. The use of `defaultdict` is mainly to avoid `if`/`else` statements in the `for` loop.

Note that for each `hit` object we use the `json` method. This method is available on any PSEngine-created object and allows you to dump it as a JSON-compatible dictionary.

Once the new `data` dictionary is populated we can save the content to a file after transforming it to a string with `json.dumps`.

```python
--8<-- "docs/examples/classic_alerts/example_3.py"
```

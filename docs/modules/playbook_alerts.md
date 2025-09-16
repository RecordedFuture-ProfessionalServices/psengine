## Introduction

The `PlaybookAlertMgr` class of the `playbook_alerts` module allows you to search, fetch and update playbook alerts coming from your Recorded Future enterprise.

See the [**API Reference**](../api/playbook_alerts/playbook_alert_mgr.md) for internal details of the module.

## Notes

- The `search` method is used to find alerts based on various parameters and returns only the `status` panel, which provides a brief summary of each alert. If you need the full alert details, including all panels, you must fetch each alert by its ID.

- The `fetch_bulk` method simplifies this process by performing both the search and fetch steps in one function call (multiple API calls under the covers). It returns the complete payload for each alert found, including all available panels.

- Playbook alert data is organized into panels, each containing specific information. The `status` panel is common to all playbook alert types and provides a brief summary. For example: when you use the `search` method, only the `status` panel is returned.

## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Fetch alert data and images by ID, then save images to file

!!! tip
    To run this example you need to provide a playbook alert ID in the `alert_id` argument at line 11. This can be retrieved by using `search` or `fetch_bulk` functions.
    If you are using a playbook alert that is not a Domain Abuse type, change the category to match the alert's.

In this example, we assume that we have an alert ID from either another integration, a colleague, or the portal; however, the steps in this example can be replicated using `fetch_bulk` as well.

We use the `fetch` method to collect the alert, with the `fetch_images` argument set to `True`, so that we get all the images associated with that alert, if any.
We then use the `save_pba_images` helper function to save the file as PNG. Once the script is executed, it writes the PNG file in the `alerts` directory.

To run this sample, change `alert_id` to an alert ID from your organization.

```python
--8<-- "docs/examples/playbook_alerts/example_1.py"
```

#### 2: Find the latest high-priority third-party risk alerts and save them as Markdown

In this example, we show two ways of using the `markdown` method of a playbook alert. The first method uses only the alerts data returned by the `PlaybookAlertMgr` class, and the second combines other modules of `psengine` to enrich the returned data.

We search for the newest alerts using the `fetch_bulk` method. The search is filtered by `category`, `priority`, `statuses`, and `created_from`. Once the alerts have been retrieved, we save each of them to a file as Markdown using the `markdown` method.

```python
--8<-- "docs/examples/playbook_alerts/example_2a.py"
```

In this example, we use a couple of other managers available in PSEngine to show how to get the most possible data out of a Third Party Risk alert. Using `LookupMgr` and `SoarMgr` is not strictly needed for `markdown` to work, but they can be used as an addition.

We retrieve the alerts the same as in the previous example. Once the Third Party Risk alerts have been retrieved, we can get all the IP addresses mentioned in the alert using the `all_ip_addresses` property and enrich them.

The company related to this alert can also be enriched with the `lookup` method; in this case we collect the `aiInsights`, `timestamps`, and `intelCard` data.

This enriched information is passed to the `markdown` method of the alert to create a more comprehensive file.
```python
--8<-- "docs/examples/playbook_alerts/example_2b.py"
```

As mentioned above, `extra_context` is not mandatory; you can remove it from the example and the Markdown will still be generated.

After the sample code executes, in the `alerts` directory you should have a file for each alert that has been retrieved.

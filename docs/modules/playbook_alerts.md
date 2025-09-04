## Introduction

The `PlaybookAlertMgr` class of the `playbook_alerts` module allows you to fetch and search for playbook alerts that triggered for your organization.

See the [**API Reference**](../api/playbook_alerts/playbook_alert_mgr.md) for internal details of the module.

## Notes

The methods `search` and `fetch_bulk` are similar, but they return different results. In the playbook alert data, there is a concept of panels that contain specific information. The `status` panel is the generic one that all the playbook alert types have in common. When you perform a `search`, only the `status` panel is returned.

If you want to get all the other panels of each alert, you will have to get the alert ID of each alert and do a fetch. The `fetch_bulk` method hides these steps by implementing an internal `search` and `fetch` for each alert that has been found.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: From an alert ID, fetch the data and related images, and save the images to file

!!! tip
    To run this example you need to provide a playbook alert ID in the `alert_id` argument at line 11. This can be retrieved by using `search` or `fetch_bulk` shown in the previous example.
    If you are using a playbook alert that is not a Domain Abuse type, change the category to match the alert's.

In this example, we assume that we have an alert ID from either another integration, a colleague, or the portal; however, the steps in this example can be replicated using `fetch_bulk` as well.

We use the `fetch` method to collect the alert, with the `fetch_images` argument set to `True`, so that we get all the images associated with that alert, if any.
We then use the `save_pba_images` helper function to save the file as PNG. Once the script is executed, it writes the PNG file in the `alerts` directory.

To run this sample, change `alert_id` to an alert ID from your organization.

```python
--8<-- "docs/examples/playbook_alerts/example_1.py"
```

#### Example 2: Search the latest new high-priority third-party risk alerts and save them as Markdown

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

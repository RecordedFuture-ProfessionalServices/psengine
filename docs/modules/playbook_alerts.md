## Introduction 

The `PlaybookAlertMgr` class of the `playbook_alerts` module allows to fetch and search for playbook alerts that triggered for your organization.

See the [**API Reference**](../api/playbook_alerts/playbook_alert_mgr.md) for internal details of the module.

## Notes

The methods `search` and `fetch_bulk` are similar but they return different results. In the playbook alert data, there is a concept of panels which contains some specific information. The `status` panel is the generic one that all the plabybook alert types have in common. When you perform a `search` only the `status` panel is returned. 

If you want to get all the other panels of each alert, you will have to get the alert ID of each alert, and do a fetch. The `fetch_bulk` is hiding these steps by implementing a hidden `search` and `fetch` of each alert that has been found. 

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: From an alert ID fetch the data and related images, save the images to file.

!!! tip
    To run this example you need to provide a playbook alert ID in the `alert_id` argument at line 11. This can be retrieved by using the `search` or `fetch_bulk` shown in the previous example.
    If you are using a playbook alert that is not a Domain Abuse type, change the category to match the alert's one.

In this example we assume that we have an alert ID from either another integration, colleague or from the portal, however the steps on this example can be replicated using `fetch_bulk` as well.

We use the `fetch` method to collect the alert, with the `fetch_images` argument set to `True`, so that we will get all the images associated to that alert, if any. 
We then use the `save_pba_images` helper function to save the file as PNG. Once the script is executed it will write the PNG file in the `alerts` directory.

In order to run this sample you need to change the `alert_id` with an alert ID from your organization.

```python 
--8<-- "docs/examples/playbook_alerts/example_1.py"
``` 

#### Example 2: Search the latest new high priority third party risk alerts and save them as markdown.

In this example we are showing two ways of using the `markdown` method of a playbook alert. The first method is with only the alerts data returned by the `PlaybookAlertMgr` class, and the second combining other modules of psengine to enrich the data returned.

What we are doing here is searching for the newest alerts using the `fetch_bulk` method. The search is filtered by the `category`, `priority`, `statuses` and `created_from`. Once the alerts have been retrieved, we save each of them to file as markdown, using the `markdown` method.

```python
--8<-- "docs/examples/playbook_alerts/example_2a.py"
``` 

In this example we are using a couple other managers that are available in PSEngine to show how to get the most possible data out of a Third Party Risk alert. The usage of the `LookupMgr` and `SoarMgr` are not strictly needed for the whole `markdown` to work but they can be used as an addition.

We retrieve the alerts the same as the previous example, once the Third Party Risk alerts have been retrieved, we can get all the IP addresses that have been mentioned in the alert, using the `all_ip_addresses` property, and enrich them. 

The company of which this alert is related to can be enriched as well with the `lookup` method and in this case we collect the `aiInsights`, `timestamps` and `intelCard` data. 

These enriched information will be passed to the `markdown` method of the alert to create a more comprehensive file. 
```python 
--8<-- "docs/examples/playbook_alerts/example_2b.py"
``` 

As mentioned above, the `extra_context` is not mandatory, it can be removed from the example and the markdown will still be generated. 

After the sample codes are executed, in the `alerts` directory you should have a file for each alert that has been retrieved. 

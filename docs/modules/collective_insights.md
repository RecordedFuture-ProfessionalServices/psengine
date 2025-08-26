## Introduction 

The `CollectiveInsights` class of the `collective_insights` module allows you to submit indicators from a detection coming from any of your internal tools to your Recorded Future enterprise. Collective Insights enriches submissions with Recorded Future intelligence to provide your organisation's enterprise with enhanced and actionable intelligence.    

When using the `collective_insights` module, you have to create an `Insight` object and then submit it. The `CollectiveInsights` class provide access to the modules needed to perform these actions. The examples below will show how to use them. 

See the [**API Reference**](../../api/collective_insights/collective_insightsd) for internal details of the module.

## Notes

1. There are some limitations around the number of submissions allowed per day, see the [Collective Insight API](https://support.recordedfuture.com/hc/en-us/articles/15847735339923-Collective-Insights-API) documentation.

2. The insights submitted requires some fields to be filled with specific values. For example the `detection_type` can be either `sigma`, `yara` or `snort`. To help you there are some constants values defined in `collective_insights.constants`. See a usage example below.

## Examples

!!! warning

    Below are some examples of usage of the `collective_insights` module. Consider adding error handling as necessary. All the errors that can be raised by each method or function are specified in the API Reference page.


#### Example 1: Submitting a detection of an hash linked to a Wiper malware speciment.

The `create` method only requires the following arguments to be specified:

- `ioc_value`
- `ioc_type`
- `detection_type`
- `timestamp`

Every other value can optionally be provided and add more context to the detection.
In the example we have a detection coming from Symantec. The hash is coming from a Recorded Future Insikt note defined by the id `doc:o6_lui`. The other informations are retrieved by both the note (example the malware type and MITRE codes) or the incident itself. 

In our case the timestamp has been mocked to "now", but in a real scenario it would be taken from the incident.

```python 
--8<-- "docs/examples/collective_insights/example_1.py"
```

The `create` method return a `Insight` object, which can be passed to the `submit` method.

The `submit` method take a single `Insight` or a list of `Insight` objects.

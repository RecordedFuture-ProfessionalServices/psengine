## Introduction

The `CollectiveInsights` class of the `collective_insights` module allows you to submit indicators from a detection coming from any of your internal tools to your Recorded Future enterprise. Collective Insights enriches submissions with Recorded Future intelligence to provide your organization's enterprise with enhanced and actionable intelligence.

When using the `collective_insights` module, you have to create an `Insight` object and then submit it. The `CollectiveInsights` class provides access to the modules needed to perform these actions. The examples below show how to use them.

See the [**API Reference**](../api/collective_insights/collective_insights.md) for internal details of the module.

## Notes

- There are some limitations around the number of submissions allowed per day; see the Collective Insight API documentation.
- The insights submitted require some fields to be filled with specific values. For example, the `detection_type` can be either `sigma`, `yara`, or `snort`. To help you, there are constant values defined in `collective_insights.constants`. See a usage example below.
- The `CollectiveInsights.create` method has a default value of `debug=True`; this is used to make sure the whole workflow works, but the indicators are not submitted to Recorded Future. In production code, set `debug=False` when you are ready to share the detections with Recorded Future.

## Examples

{! modules/_includes/examples_warning.md !}

### 1: Submit a detection for a Wiper malware hash

The `create` method only requires the following arguments to be specified:

- `ioc_value`
- `ioc_type`
- `detection_type`
- `timestamp`

Every other value can optionally be provided and adds more context to the detection. In the example below, we have a detection coming from Symantec. The hash is coming from a Recorded Future Insikt note defined by the id `doc:o6_lui`. The other information is retrieved by both the note (for example, the malware type and MITRE codes) and the incident itself.

In our case, the timestamp has been mocked to "now", but in a real scenario it would be taken from the incident.

```python
--8<-- "docs/examples/collective_insights/example_1.py"
```

The `create` method returns an `Insight` object, which can be passed to the `submit` method.

The `submit` method takes a single `Insight` or a list of `Insight` objects.

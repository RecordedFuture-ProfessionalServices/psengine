## Introduction

The `risk_history` module allows you to interact with the Recorded Future Risk API to retrieve the historical changes of an entity. 
The changes are determined by the risk score and risk rules mutations over time.


See the [**API Reference**](../api/risk_history/risk_history_mgr.md) for internal details of the module.


## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Display the risk score changes of two entities over time

In this example you search for a query that is matching all the reports having a `sha256` as defined in the `sha256` argument. 
The start and end date are relative to the day in which you run the example. 

```python
--8<-- "docs/examples/risk_history/example_1.py"
```

The output of the example is:


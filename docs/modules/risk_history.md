## Introduction

The `risk_history` module allows you to interact with the Recorded Future Risk API to retrieve the historical changes of an entity. 
The changes are determined by the risk score and risk rules mutations over time.


See the [**API Reference**](../api/risk_history/risk_history_mgr.md) for internal details of the module.


## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Display the risk score changes of two entities over time

In this example you start by fetching all the history for the last 20 days of two entities represented by their ID. To find the entity ID, if not known, you can use the Entity Match module, more information [here](./entity_match.md). 
You then create a table of 4 columns, and a row for each risk change. 

Before adding the data to the table, you convert the datetime values to string. You can use the `TIMESTAMP_STR` constant defined in `psengine.constants`.

To run this example, first add the `rich` package to your virtual environment:

```bash
pip install rich
```

Once installed the example can be executed. 

```python
--8<-- "docs/examples/risk_history/example_1.py"
```

The output of the example will be similar to:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃                   Entity ┃ Score ┃               Added ┃             Removed ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Red Hat Enterprise Linux │    10 │ 2025-09-16 16:30:56 │ 2025-09-27 16:14:20 │
│ Red Hat Enterprise Linux │    81 │ 2025-09-27 16:14:20 │         Not removed │
│                     Sudo │    72 │ 2025-09-19 16:08:43 │ 2025-09-30 02:18:45 │
│                     Sudo │    77 │ 2025-09-30 02:18:45 │ 2025-09-30 16:28:08 │
│                     Sudo │    82 │ 2025-09-30 16:28:08 │         Not removed │
└──────────────────────────┴───────┴─────────────────────┴─────────────────────┘
```


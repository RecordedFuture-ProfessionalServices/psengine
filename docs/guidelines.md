This page focus on all the guidelines to follow or be aware of while using PSEngine to build your integration.

## PSEngine Version

We follow [SemVer](semver.org) standard and while we try to avoid breaking changes with new minor or patch releases, it is always advised to pin a specific version of PSEngine in your `pyproject.toml`. For example:

```toml
dependencies = [
    "psengine==2.1.0",
]
```
And keep the version regularly up to date.

## Feature Deprecation

When a field, feature or endpoint is deprecated, we will add a deprecation warning with a alternative if available. Three minor releases after, it will be removed.
For example a field marked as deprecated in 2.10.x, will effectively be removed in 2.13.0.

## Python Version

We support the minimum supported Python version that is not already end of life. Every time a Python version is marked as end of life, we will upgrade the minimum required version, usually within 1/3 months.

## Features

### Multithreading

Some modules of PSEngine provide built-in concurrent API calls to speed up the fetching of data, for example the enrichment of multiple IOCs can be done both sequentially or concurrently, by setting the `max_workers` argument:

```python
from psengine.enrich import LookupMgr

mgr = LookupMgr()
domains = mgr.lookup_bulk(['google.com', 'facebook.com'], 'domain', max_workers=10)

```
By default `max_workers` is set to `0`. 

Since different APIs behave differently and can handle different workload based on the type of request (ie the number of fields or the size of the payload requested), below is a table to guide you on the suggested number of workers to use:

| Method                                       | Suggested Max Workers | Minimum Calls                                                                                                      |
|----------------------------------------------|------------------------|-------------------------------------------------------------------------------------------------------------------|
| `enrich.lookup_mgr.lookup_bulk`                | 5 to 50                | 10+ IOCs to enrich, when SOAR is not possible. Consider that the more fields requested the lower the numbers of workers to use.|
| `enrich.soar_mgr.soar`                         | 10 to 30               | 1000+ IOCs to enrich, the soar method is batching already up to 1k values per request, so use `max_workers` only when more than 1k of IOCs need to be enriched.|
| `classic_alerts.classic_alerts_mgr.fetch_bulk` | 3 to 10                | 10+ alerts to fetch.                                                                                                             |
| `classic_alerts.classic_alerts_mgr.search`     | 3 to 10                | 10+ alert rules to search, multithreading only works when more than one `rule_id` is requested and `max_workers > 0`.                                    |
| `entity_match.entity_match_mgr.resolve_entity_ids` | 5 to 15             | 10+ entities to fetch.                                                                                                            |

The Minimum Calls column is indicating the minimum amount of entities (IOCs, alerts, etc) after which you should start getting a decent time gain with multithreading.

### Model Validation

By default PSEngine uses a custom Pydantic `BaseModel`, which is configured to use `extra=ignore` to discard any new field returned by the Recorded Future API that has not been added to the related model yet. This is a design choice to make sure we always allow the usage of fields where the behaviour is known.
You can still change this behaviour by setting the `RF_MODEL_EXTRA` environment variable to `allow` or `forbid`. 

In case where the `RF_MODEL_EXTRA` is set to `allow`, no validation will be performed on the new fields, you will be responsible for that.

### Logging

You can either use `psengine.logger.RFLogger` or use the standard python `logging` module based on the other libraries/SDK that you are using:

- If the integration SDK that you are using is already setting up the log handlers, then you can use the `logging` module:
```python
import logging
from psengine.classic_alerts import ClassicAlertMgr
log = logging.getLogger(__name__)
mgr = ClassicAlertMgr()
```

- If the integration SDK that you are using is already setting up the log handlers and is not propagating logs to other modules, then you **must** be using the SDK logger, otherwise your log messages will be lost.
- If the integration SDK that you are using is not setting up any handlers, you can use `RFLogger`, which will set up a `FileHandler` and `ConsoleHandler`:
```python 
from psengine.classic_alerts import ClassicAlertMgr
from psengine.logger import RFLogger
log = RFLogger().get_logger()
mgr = ClassicAlertMgr()
```

## Project Layout

The code structure below is how we are structuring the code for integrations, this is more an internal preference that we have been using, you are free to follow it if you like.

```
myintegration
├── README.md
├── config
│   └── config.toml
├── libmyintegration
│   ├── __init__.py
│   ├── _version.py
│   ├── constants.py
│   ├── exceptions.py
│   └── myintegration.py
├── pytest.ini
├── pyproject.toml
├── ruff.toml
├── run_myintegration.py
├── tests
│   ├── conftest.py
│   └── test_myintegration.py
└── tools
```
File explanation:

- `README.md` → (Mandatory) link to confluence for documentation on this integration, useful for people that find your integration on Git and wants to know more.
- `config` → (Optional) folder to save your config file if needed. There is a `config.toml` sample already created for you to use.
- `libmyintegration` → (Mandatory) the integration code. Rename it with lib<name of the integration>.
- `pytest.ini` → (Optional) contains the config of pytest
- `pyproject.toml` → (Mandatory) list of packages to install and package information.
- `ruff.toml` → (Mandatory) configuration for ruff linting and formatting.
- `run_my_integration.py` → (Mandatory) entry point of your integration code.
- `tests` → (Mandatory) folder for unit testing.
- `tools` → (Optional) any custom code used as utilities. Example exporting the PDF from Confluence.

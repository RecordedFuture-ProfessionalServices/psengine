This page focuses on all the guidelines to follow or be aware of while using PSEngine to build your integration.

## Versioning

### PSEngine Version

We use [semantic versioning](https://semver.org). It is recommended to use [compatible release](https://peps.python.org/pep-0440/#version-specifiers) notation to get the latest patch releases, and avoid breaking changes from major releases:

```toml
dependencies = [
    "psengine~=2.1",
]
```

You can also pin the dependency to a specific version:

```toml
dependencies = [
    "psengine==2.1.0",
]
```

In this case, you should check for new releases, test your code against them, and regularly update the pinned version.

Note that only the latest version is actively supported and maintained. If a new major version is released, older versions are no longer supported.

#### Feature Deprecation

When a field, feature, or endpoint is deprecated, we will add a deprecation warning with an alternative if available. Three minor releases later (or the next major release, whichever comes first), it will be removed.

For example, a field marked as deprecated in 2.10.x will effectively be removed in 2.13.0 or 3.0.

### Python Version

We support the minimum supported Python version that is not already end of life. Every time a Python version is marked as end of life, we will upgrade the minimum required version, usually within 1 to 3 months.

## PSEngine Features

### Multithreading

Some modules of PSEngine provide built-in concurrent API calls to speed up the fetching of data. For example, the enrichment of multiple IOCs can be done both sequentially or concurrently by setting the `max_workers` argument:

```python
from psengine.enrich import LookupMgr

mgr = LookupMgr()
domains = mgr.lookup_bulk(['google.com', 'facebook.com'], 'domain', max_workers=10)

```

By default `max_workers` is set to `0`, in which case, requests are made sequentially.

Since different APIs behave differently and can handle different workloads based on the type of request (i.e., the number of fields or the size of the payload requested), the table below shows the suggested number of workers to use:

| Method                                             | Suggested Max Workers | Minimum Calls                                                                                                                                                |
| -------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `enrich.lookup_mgr.lookup_bulk`                    | 5 to 50               | 10+ IOCs to enrich, when SOAR is not possible. Consider that the more fields requested the lower the number of workers to use.                               |
| `enrich.soar_mgr.soar`                             | 10 to 30              | 1000+ IOCs to enrich. The soar method is already batching up to 1k values per request, so use `max_workers` only when more than 1k IOCs need to be enriched. |
| `classic_alerts.classic_alerts_mgr.fetch_bulk`     | 3 to 10               | 10+ alerts to fetch.                                                                                                                                         |
| `classic_alerts.classic_alerts_mgr.search`         | 3 to 10               | 10+ alert rules to search. Multithreading only works when more than one `rule_id` is requested and `max_workers > 0`.                                        |
| `entity_match.entity_match_mgr.resolve_entity_ids` | 5 to 15               | 10+ entities to fetch.                                                                                                                                       |

The Minimum Calls column indicates the minimum number of entities (IOCs, alerts, etc.) after which you should start getting a decent performance gain with multithreading.

### Model Validation

By default PSEngine uses a custom Pydantic `BaseModel`, which is configured to use `extra=ignore` to discard any new field returned by the Recorded Future API that has not been added to the related model yet. This is a design choice to make sure we always allow the usage of fields where the behaviour is known.
You can still change this behaviour by setting the `RF_MODEL_EXTRA` environment variable to `allow` or `forbid`.

In the case where `RF_MODEL_EXTRA` is set to `allow`, no validation will be performed on the new fields. You will be responsible for that.

### Logging

You can either use `psengine.logger.RFLogger` or use the standard Python `logging` module based on the other libraries/SDKs that you are using:

* If the integration SDK that you are using is already setting up the log handlers, then just use the `logging` module normally:

```python
import logging
from psengine.classic_alerts import ClassicAlertMgr
log = logging.getLogger(__name__)
mgr = ClassicAlertMgr()
```

* If the integration SDK that you are using has already set up log handlers where [propagate=False](https://docs.python.org/3/library/logging.html#logging.Logger.propagate), then you **must** use the SDK logger. Code that is imported and run by the SDK will not pass log messages to the root logger, which is where `RFLogger` adds its handlers.
* If the integration SDK that you are using is not setting up any handlers, you can use `RFLogger`, which will set up a `FileHandler` and `ConsoleHandler`:

```python
from psengine.classic_alerts import ClassicAlertMgr
from psengine.logger import RFLogger
log = RFLogger().get_logger()
mgr = ClassicAlertMgr()
```

## Project Layout

Below is how we typically structure code for integrations. This is more of a convention; you are free to follow it if you like.

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

* `README.md` → (**Mandatory**) link to Confluence for documentation on this integration, useful for people who find your integration on Git and want to know more.
* `config` → (Optional) folder to save your config file if needed. There is a `config.toml` sample already created for you to use.
* `libmyintegration` → (**Mandatory**) the integration code. Rename it to `lib<name of the integration>`.
* `pytest.ini` → (Optional) contains the pytest configuration.
* `pyproject.toml` → (**Mandatory**) list of packages to install and package information.
* `ruff.toml` → (**Mandatory**) configuration for ruff linting and formatting.
* `run_my_integration.py` → (**Mandatory**) entry point of your integration code.
* `tests` → (**Mandatory**) folder for unit testing.
* `tools` → (Optional) any custom code used as utilities. For example, exporting a PDF from Confluence.


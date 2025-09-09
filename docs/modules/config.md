## Introduction

The `config` module does not communicate with any Recorded Future dataset; it is used to configure PSEngine and the integration behavior. Its usage is not mandatory in integration development; it is more a convenience if a configuration file is needed.

The `Config` is a class of PSEngine that you can use to retrieve static information from a file or the system's environment variables. The allowed file extensions are:

- `.toml`
- `.json`
- `.env` file

If the system cannot use any of those, you can still use environment variables or the parameters of the `init` method (see the example below).

The config has a strict priority for reading values:

1. Values passed via the `init` method are the most important.
2. Values gathered from environment variables.
3. Values from any config file.

If you have an environment variable configured, it will overwrite the value set in the config file.

The `Config` class is a singleton, which means that once initialized its values are immutable, and every module will read them. You create the `Config` object via the `init` method. To get the data of the config, use the `get_config` method.

The `Config` class manages a `ConfigModel` class by default, which is a `pydantic.BaseSettings` class that contains attributes of general needs, like proxy settings and HTTP timeout.
The variables defined in the `ConfigModel` are:

- `platform_id` -> str
- `app_id` -> str
- `rf_token` -> `RFToken`
- `http_proxy` -> str
- `https_proxy` -> str
- `client_ssl_verify` -> bool
- `client_basic_auth` -> (str, str)
- `client_cert` -> str or (str, str)
- `client_timeout` -> int
- `client_retries` -> int
- `client_backoff_factor` -> int
- `client_status_forcelist` -> list of int
- `client_pool_max_size` -> int

!!! warning
    Define the `Config` before initializing the manager in your integration entry point. Once that is done, you can reference the `Config` from anywhere. See the example below.

See the [**API Reference**](../api/config/config.md) for internal details of the module.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Read a `Config` from `config.toml`

To run this example, create a `config.toml` file with the following content:

```toml
--8<-- "docs/examples/config/config.toml"
```

Initialize the `Config` object with `init`, passing the path (absolute or relative) of the config file you intend to use. This creates an object but does not return it.

Since you want to print the value of `my_value`, use the `get_config` method to return the `ConfigModel` instance.

```python
--8<-- "docs/examples/config/example_1.py"
```

This will print `5`.

#### Example 2: Configure a `Config` from environment variables

You can read only environment variables that are statically defined in the `ConfigModel`. They need to be prefixed with `RF_` and must be of the type specified in the model as described in the Introduction section. 
For example, to set the `app_id` and `platform_id` variables:

```bash
export RF_APP_ID=example/1.0.0
export RF_PLATFORM_ID=Splunk/10.0.0
```

Then read the config:

```python
--8<-- "docs/examples/config/example_2.py"
```

The sample code will print the values defined above.

#### Example 3: Configure a `Config` from Python

You can initialize your config from the `init` method directly:

```python
--8<-- "docs/examples/config/example_3.py"
```

This will print `5`.

#### Example 4: Define your own config

If you want to define your own config in an integration, you can. The steps are:

1. Define your model (`IntegrationModel` in the example). It has to inherit from `psengine.ConfigModel`.
2. Change `Config.init` to use the `config_class` and assign it to the `IntegrationConfig` model you just created.
3. Use the `config_class` with `IntegrationConfig` in the `get_config` function as well.
4. Keep doing everything else as usual.

To replicate this example, first create a `custom_config.toml` file with the following content:

```toml
--8<-- "docs/examples/config/custom_config.toml"
```

Place this in the same directory as the example Python code. Once the file configuration is created, the sample code will create the custom config in the `IntegrationConfig` class. Then call the `init` method, passing the custom configuration model as `config_class` and the usual TOML path.

```python
--8<-- "docs/examples/config/example_4.py"
```

Each property can be accessed using dot notation, for example, `config.complex_value.data`.

#### Example 5: Real example

Assume you are developing an integration that needs to fetch playbook alerts. The current requirements for the alerts to be ingested are:

- Domain Abuse
- `New` status
- `High` priority
- No older than yesterday

Each domain that triggered this alert has to be enriched with the `links` field.

You can opt for a quick script using free variables around the code or use the config.

**Code 1** without the config:

In this example, you hardcode the values that you need for fetching the alert and enriching the IOCs. This is perfectly fine; however, in larger applications, it might be challenging to maintain if the requirements change.

```python
--8<-- "docs/examples/config/example_5_1.py"
```

An alternative is to save the requirements to a config file and use them instead of the hardcoded values.

**Code 2** with the config:

With the `int_config.toml` file:

```toml
--8<-- "docs/examples/config/int_config.toml"
```

The script can be rewritten as below.

```python
--8<-- "docs/examples/config/example_5_2.py"
```

The code itself is longer; however, you gain maintainability since a person without development experience or inner understanding of the application can change the config to meet new requirements.

#### Example 6: Using a proxy

In this example, you configure a proxy that the `LookupMgr` will use to communicate with the internet. The usage of `client_ssl_verify` is not mandatory, but needed in the example to work with a proxy without certificate.

Similarly to previous examples, you configure the `Config` first, and then initialize the manager. The `https_proxy` argument is used to specify the URL to use as proxy. The manager will automatically pick up this configuration during initialization.

```python
--8<-- "docs/examples/config/example_6.py"
```




## Introduction

The `config` module is used to configure PSEngine and control integration behavior. It does not interact with any Recorded Future datasets, and its use is optional, primarily serving as a convenience when a configuration file is needed.

Configuration values can be provided in several ways:

- Supported file formats: `.toml`, `.json`, or `.env`
- Environment variables
- Directly via parameters to the `init` method

When loading configuration, PSEngine follows a strict priority:

1. Values passed directly to the `init` method
2. Values from environment variables
3. Values from configuration files

If an environment variable is set, it will override the corresponding value in the config file.

The `Config` class is a singleton, meaning its values are immutable once initialized and accessible from any module. You initialize the configuration using the `init` method, and retrieve its data with the `get_config` method.

By default, the `Config` class manages a `ConfigModel`, which is a `pydantic.BaseSettings` class containing common attributes such as proxy settings and HTTP timeout.

The variables pre-defined by the `ConfigModel` are:

- `platform_id` -> str
- `app_id` -> str
- `rf_token` -> `RFToken`
- `asi_token` -> `RFToken`
- `sandbox_token` -> `RFToken`
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

#### 1: Read a `Config` from `config.toml`

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

#### 2: Configure a `Config` from environment variables

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

#### 3: Configure a `Config` from Python

You can initialize your config from the `init` method directly:

```python
--8<-- "docs/examples/config/example_3.py"
```

This will print `5`.

#### 4: Define your own config

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

#### 5: Real example

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

#### 6: Using a proxy

In this example, a proxy is configured for the `LookupMgr` to use when connecting to the Internet. While `client_ssl_verify` is optional, it is included here to allow the example to work with a proxy that does not have a certificate.

As with previous examples, you first set up the `Config`, then initialize the manager. The `https_proxy` argument specifies the proxy URL, and the manager automatically uses this configuration during initialization.

```python
--8<-- "docs/examples/config/example_6.py"
```




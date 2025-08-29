## Introduction 

The `config` module does not communicate with any Recorded Future dataset, it is used to configure PSEngine and the integration behaviour. Its usage is not mandatory in an integration development, it more a conveninece if a configuration file is needed.

The `Config` is a class of PSEngine that can be used to retrieve static information from a file or the environment variables of the system. The file extensions allowed are: 

- `.toml`
- `.json`
- `.env` file

If the system cannot use any of those you can still use the environment variables or the parameters of the `init` method. (See example below)

The config has a very strict priority of reading values:

1. values passed via `init` method are the most important
2. values gathered in the environment variables
2. values from any config file

If you have a environment variable configured it will overwrite the value set in the config file.

The `Config` class is a singleton, which means that once initialized its values are immutable and every module will read them. The creation of the `Config` object is done via the `init` method. If you need to get the data of the config you need to use the `get_config` method.

The `Config` class manages a `ConfigModel` class by default, which is a `pydantic.BaseSetting` class which contains attributes of general needs, like proxy settings, HTTP timeout etc.

!!! warning

    The `Config.init` creates the a global config that is unique at any point of your code execution. You need to define the `Config` before initialising the manager on your integration entrypoint. Once that is done you can reference the `Config` from anywhere. See example below.


See the [**API Reference**](../api/config/config.md) for internal details of the module.

## Examples

{! modules/_includes/examples_warning.md !}


#### Example 1: Read a `Config` from `config.toml`.

To run this example create a `config.toml` file with content:

```toml
--8<-- "docs/examples/config/config.toml"
```

We initialize the `Config` object with `init` passing the path (absolute or relative) of the config file we intend to use. This create an object but it does not return it.

Since we want to print the value of `my_value` we use `get_config` method to return the `ConfigModel` instance. 
```python
--8<-- "docs/examples/config/example_1.py"
```

This will print `5`.

#### Example 2: Configure a `Config` from environment variables.

You can read only variables that are statically defined in the `ConfigModel`. They need to be prefixed with `RF_` and need to be of the type specified in the model. The variables are:

- `platform_id` ->  str 
- `app_id` ->  str 
- `rf_token` ->  RFToken 
- `http_proxy` ->  str 
- `https_proxy` ->  str 
- `client_ssl_verify` ->  bool 
- `client_basic_auth` -> (str, str)
- `client_cert` ->  str or (str, str)
- `client_timeout` ->  int 
- `client_retries` ->  int 
- `client_backoff_factor` ->  int 
- `client_status_forcelist` ->  List of int 
- `client_pool_max_size` ->  int 

So for example if we need to set the `app_id` and `platform_id` variables we can do the following:

```bash
export RF_APP_ID=example/1.0.0
export RF_PLATFORM_ID=Splunk/10.0.0
```

And read the config:

```python
--8<-- "docs/examples/config/example_2.py"
```

The sample code will print the values defined above.

#### Example 3: Configure a `Config` from python.

You can initialise your config from the `init` method directly:

```python
--8<-- "docs/examples/config/example_3.py"
```

This will print `5`. 


#### Example 4: Define your own config.

If you want to define your own config in an integration, you can. The steps are:

1. Define your model (`IntegrationModel` in the example), it has to inherit from `psengine.ConfigModel`
2. Change the `Config.init` to use the `config_class` and assign it to the `IntegrationConfig` model we just created

3. Use the `config_class` with `IntegrationConfig` in the `get_config` function as well
4. Keep doing everything else as usual.

To replicate this example, first create a `custom_config.toml` file with content:

```toml
--8<-- "docs/examples/config/custom_config.toml"
```

This should be placed in the same directory of the example python code. 
Once the file configuration is created the sample code will create the custom config in the `IntegrationConfig` class. We then call the `init` method passing as `config_class` the custom configuration model and the usual TOML path.

```python
--8<-- "docs/examples/config/example_4.py"
```

Each property can be access using the dot notation, for example `config.complex_value.data`.


#### Example 5: Real example.

Let's assume that we are developing an integration that needs to fetch playbook alerts. The current requirements are that the alerts to be ingested to be:

- Domain Abuse
- with `New` status
- `High` priority
- No older than yesterday

Each domain that triggered this alert has to be enriched with the `links` field.

We can opt for a quick script using "free" variables around the code, or using the config. 

**Code 1** without the config:

In this example we are hardcoding the values that we need for fetching the alert and enriching the IOCs. This is a perfectly fine code, however in larger applications it might be challanging to maintain if the requirements change.

```python
--8<-- "docs/examples/config/example_5_1.py"
```

An alternative is to save the requirements to a config file and use them instead of the hardcoded values.

**Code 2** with the config:
With the `int_config.toml` file being:

```toml
--8<-- "docs/examples/config/int_config.toml"
```

The script can be rewritten as below.
```python
--8<-- "docs/examples/config/example_5_2.py"
```

The code itself is defintely longer, however we gain on maintainability, since now a person without development experince or inner understanding of the application can change the config to meet the new requirements. 



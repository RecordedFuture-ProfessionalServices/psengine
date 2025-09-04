## Introduction

The `RFLogger` class of the `rf_logger` module sets up a logger for your integration.

The logger is built into all the manager classes in PSEngine, which means it is used by default as soon as any form of logging is enabled in your code.

This could be in three ways:

- If the SDK you are using already has logging enabled
- If you have already enabled logging
- Neither point 1 nor 2, and you want to use the PSEngine logger

Note that it is not required to use either the `RFLogger` or any type of logging for PSEngine to work.

See the [**API Reference**](../api/logger/rf_logger.md) for internal details of the module.

## Examples

{! modules/_includes/examples_warning.md !}

#### Example 1: Use a PSEngine module when another SDK has logging enabled

In this example, we create a `Logger` instance from the `logging` standard library to emulate the fact that you might have configured your own logging. In this case, there is nothing else that needs to be done before using PSEngine.

```python
--8<-- "docs/examples/logger/example_1.py"
```

If you set the logging level to `DEBUG`, you will see all the internal PSEngine debug logging.

```
DEBUG:psengine.base_http_client:Creating an HTTP client session
DEBUG:psengine.enrich.lookup_mgr:Called LookupMgr.lookup(8.8.8.8, ip, fields='None')
DEBUG:psengine.enrich.lookup_mgr:Called LookupMgr._fetch_data(entity='8.8.8.8', entity_type='ip', fields="['timestamps', 'entity', 'risk']")
DEBUG:psengine.rf_client:Called RFClient.request(get, https://api.recordedfuture.com/v2/ip/8.8.8.8, params="{'fields': 'timestamps,entity,risk'}")
DEBUG:psengine.base_http_client:Called BaseHTTPClient.call(method='get', url='https://api.recordedfuture.com/v2/ip/8.8.8.8', data='None', params="{'fields': 'timestamps,entity,risk'}")
DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): api.recordedfuture.com:443
DEBUG:urllib3.connectionpool:https://api.recordedfuture.com:443 "GET /v2/ip/8.8.8.8?fields=timestamps%2Centity%2Crisk HTTP/1.1" 200 None
DEBUG:psengine.base_http_client:HTTP Status Code: 200
DEBUG:psengine.base_http_client:BaseHTTPClient.call ended with return value '<Response [200]>'
DEBUG:psengine.rf_client:RFClient.request ended with return value '<Response [200]>'
DEBUG:psengine.enrich.lookup_mgr:LookupMgr._fetch_data ended with return value 'EnrichedIP: 8.8.8.8, Risk Score: 0, Last Seen: 202'
DEBUG:psengine.enrich.lookup_mgr:LookupMgr.lookup ended with return value 'EnrichedIP: 8.8.8.8, Risk Score: 0, Last Seen: 202'
INFO:__main__:EnrichedIP: 8.8.8.8, Risk Score: 0, Last Seen: 2025-09-01 09:44:16
```

Any log entries of higher level, like `ERROR` or `CRITICAL`, will be shown as well.

#### Example 2: Use `RFLogger` in combination with another PSEngine module

In this example, we have the same code, except for the logger definition, which is via `RFLogger`. The default `RFLogger` behaviors are:

- to log to the console and to a file under the `logs/` directory in the same location where your script is running
- to log everything from `INFO` and above
- formatted log entries:
    ```
    2025-09-01 13:27:21,297 [MainThread] INFO [example_2] <module>:9 - EnrichedIP: 8.8.8.8, Risk Score: 0, Last Seen: 2025-09-01 11:58:39

    ```
- maintain log propagation for other loggers

All of these parameters can be configured during `RFLogger` initialization.

```python
--8<-- "docs/examples/logger/example_2.py"
```

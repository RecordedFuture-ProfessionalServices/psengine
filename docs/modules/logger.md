## Introduction

The `RFLogger` class of the `rf_logger` module provides optional log handling for your integration. This should only be used if your integration client does not already have some log handling capability configured.

If log handling is already configured for your integration, simply log the normal way in each of your python files:

```
import logging

LOG = logging.getLogger(__name__)
LOG.info('this is a log message')
```

All modules in PSEngine log messages this way, so logging from PSEngine is available in whichever handler you use. 

Importing and using `RFLogger` is only necessary when you do not already have any other code to output log messages to file or terminal.

See the [**API Reference**](../api/logger/rf_logger.md) for internal details of the module.

## Logging Tree Example

The following shows the [logging tree](https://pypi.org/project/logging-tree/) after importing and initializing `RFLogger`. Note the file handlers at the `psengine` module and root levels, and the console handler at the root level. The handlers are what actually output messages to file and the terminal.

```
>>> from logging_tree import printout
>>> from psengine.logger import RFLogger
>>> log = RFLogger().get_logger()
>>> printout()
<--""
   Level WARNING
   Handler RotatingFile '/Users/pkinsella/git/hub/psengine/docs/logs/root_recfut.log' maxBytes=20971520 backupCount=5
     Formatter fmt='%(asctime)s,%(msecs)03d [%(threadName)s] %(levelname)s [%(module)s] %(funcName)s:%(lineno)d - %(message)s' datefmt='%Y-%m-%d %H:%M:%S'
   Handler Stream <_io.TextIOWrapper name='<stderr>' mode='w' encoding='utf-8'>
     Formatter fmt='%(asctime)s,%(msecs)03d %(levelname)s [%(module)s] - %(message)s' datefmt='%Y-%m-%d %H:%M:%S'
   |
   o<--"asyncio"
   |   Level NOTSET so inherits level WARNING
   |
   o<--"charset_normalizer"
   |   Level NOTSET so inherits level WARNING
   |   Handler <NullHandler (NOTSET)>
   |
   o<--[concurrent]
   |   |
   |   o<--"concurrent.futures"
   |       Level NOTSET so inherits level WARNING
   |
   o<--[dotenv]
   |   |
   |   o<--"dotenv.main"
   |       Level NOTSET so inherits level WARNING
   |
   o<--[jsonpath_ng]
   |   |
   |   o<--"jsonpath_ng.jsonpath"
   |   |   Level NOTSET so inherits level WARNING
   |   |
   |   o<--"jsonpath_ng.lexer"
   |   |   Level NOTSET so inherits level WARNING
   |   |
   |   o<--"jsonpath_ng.parser"
   |       Level NOTSET so inherits level WARNING
   |
   o<--"psengine"
   |   Level INFO
   |   Handler <NullHandler (NOTSET)>
   |   Handler RotatingFile '/Users/pkinsella/git/hub/psengine/docs/logs/psengine_recfut.log' maxBytes=20971520 backupCount=5
   |     Formatter fmt='%(asctime)s,%(msecs)03d [%(threadName)s] %(levelname)s [%(module)s] %(funcName)s:%(lineno)d - %(message)s' datefmt='%Y-%m-%d %H:%M:%S'
   |   |
   |   o<--"psengine.helpers"
   |       Level NOTSET so inherits level INFO
   |
   o<--"requests"
   |   Level NOTSET so inherits level WARNING
   |   Handler <NullHandler (NOTSET)>
   |
   o<--"urllib3"
       Level NOTSET so inherits level WARNING
       Handler <NullHandler (NOTSET)>
       |
       o<--"urllib3.connection"
       |   Level NOTSET so inherits level WARNING
       |
       o<--"urllib3.connectionpool"
       |   Level NOTSET so inherits level WARNING
       |
       o<--"urllib3.poolmanager"
       |   Level NOTSET so inherits level WARNING
       |
       o<--"urllib3.response"
       |   Level NOTSET so inherits level WARNING
       |
       o<--[urllib3.util]
           |
           o<--"urllib3.util.retry"
               Level NOTSET so inherits level WARNING
```



## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Use a PSEngine module when another SDK has logging enabled

In this example, we create a `Logger` instance from the `logging` standard library to emulate the fact that you might have configured your own logging handler. In this case, there is nothing else that needs to be done before using PSEngine.

!!! tip

    In this example, the call to `logging.basicConfig` creates the necessary handler for you to see output on the terminal. If a handler is not set up, nothing in this example will actually be logged to file or the terminal. Learn more about python log handlers [here](https://docs.python.org/3/howto/logging.html#advanced-logging-tutorial).


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

Any log entries of a higher level, like `ERROR` or `CRITICAL`, will be shown as well.

#### 2: Use `RFLogger` in combination with another PSEngine module

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

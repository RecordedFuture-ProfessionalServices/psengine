==================================================
PSEngine
==================================================
**PSEngine** is a simple, yet elegant, library for rapid development of integrations with Recorded Future.


.. code-block:: python

    >>> from psengine.enrich import LookupMgr
    >>> lookup_mgr = LookupMgr(rf_token='token')
    >>> domain = lookup_mgr.lookup('cpejcogzznpudbsmaxxm.com', 'domain')
    >>> domain
    'EnrichedDomain: cpejcogzznpudbsmaxxm.com, Risk Score: 20, Last Seen: 2024-07-22 02:50:59PM'
    >>> domain.entity
    'cpejcogzznpudbsmaxxm.com'
    >>> domain.content.risk
    EntityRisk(criticality_label='Unusual', risk_string='4/52', score=20, rules=4...)
    >>> domain.content.risk.score
    20
    >>> 
    domain.content.risk.risk_summary
    '4 of 52 Risk Rules currently observed.'


PSEngine allows you to interact with the Recorded Future API extremely easily. There’s no need to manually build the URLs and query parameters - but nowadays, just use the modules dedicated to individual API endpoints!

PSEngine is a Python package solely built and maintained by the Cyber Security Engineering team powering a number of high profile integrations, such as: Elasticsearch, QRadar, Anomali, Jira, TheHive, etc..


Installation
==================================================
PSEngine is a Python package that can be installed using pip. To install PSengine, run the following command:

.. code-block:: bash

    $ pip install psengine git+https://github.com/RecordedFuture-ProfessionalServices/psengine.git@main


PSEngine officially supports Python >= 3.9, < 3.14


Supported Features & Best–Practices
==================================================

PSEngine is ready for the demands of building robust and reliable integrations.

* Collective Insights
* Analyst Notes
* Classic & Playbook Alerts
* Risklists
* On demand IOC enrichment
* List management
* Detection Rules
* Built in logging
* Easy configuration management
* Proxy support


Quick Start
==================================================
Excited, to get started? 

The section below will give you the basic building blocks to start building integrations with PSEngine.

But first ensure that:

- PSEngine is installed
- PSEngine is up-to-date

Let’s get started with some core concepts and practices.

Config Management
--------------------------------------------------
The key requirement when building integrations with PSEngine is initializing `Config` as early as possible in your program,
before initializing any PSEngine managers. This way `rf_token` `app_id` and `platform_id` you set will be used by every manager
initialized after the Config.

.. code-block:: python

    >>> from psengine.config import Config, get_config
    # Name & version of the integration itself
    >>> APP_ID = 'example-app/1.0.0'
    # Name & version of the tool this integrates with (Optional)
    >>> PLATFORM_ID = 'PSE/1.0.0'
    >>> Config.init(rf_token='your_token', app_id=APP_ID, platform_id=PLATFORM_ID)
    >>> config = get_config()
    >>> config.app_id
    'example-app/1.0.0'

The above will result in API calls made by the managers having the following headers set:

- 'X-RFToken' Header will contain the Recorded Future API Token
- 'User-Agent' Header will contain APP ID and Platform ID (if supplied) which is a Recorded Future requirement, which might look like this:

    example-app/1.0.0 (macOS-14.1-arm64-arm-64bit) psengine-py/2.0.1 PSE/1.0.0
    
Authorization
--------------------------------------------------
In the example above we saw a token passed to the Config by the caller, but you can also omit the token during initialization and let
Config retrieve it from the environment variable `RF_TOKEN`. Just ensure that the environment variable is set before running your program:

    export RF_TOKEN=your_token

Alternatively, if you want to set an rf_token separately for a single manager, you may pass it in the constructor:

.. code-block:: python

    >>> note_mgr = AnalystNoteMgr(rf_token='your_token')

Logging
--------------------------------------------------
PSEngine also provides the capability for logging to console and files. If your program needs to show log output on the terminal and keep a .log file, just import and use psengine’s logger:

.. code-block:: python

    >>> from psengine.logger import RFLogger
    >>> LOG = RFLogger().get_logger()
    >>> LOG.info('Hello, world!')

On the other hand, if your program’s log statements already have handlers setup, just log the normal way:

.. code-block:: python

    >>> import logging
    >>> LOG = logging.getLogger(__name__)
    >>> LOG.info('Hello, world!')

In the second example, nothing is printed to terminal or file unless a handler is setup by another program running your code.

Proxies
--------------------------------------------------
If your environment requires a proxy to access the internet, you can set the proxy in the Config:

.. code-block:: python

    >>> Config.init(
            app_id=APP_ID,
            platform_id=PLATFORM_ID,
            http_proxy='http://proxy:8080',
            https_proxy='http://proxy:8080',
            client_ssl_verify=False,
        )

Examples
--------------------------------------------------
Please refer to `examples <examples>`_ for usage example of each module.

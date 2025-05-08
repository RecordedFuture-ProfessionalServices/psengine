PSEngine Changelog
==================

[2.0.4] - 2025-05-07
--------------------

Fixed
~~~~~

- ``ClassicAlert.markdown()`` no longer fails when hits[].fragment field is None
- ``Domain Abuse`` playbook alert fetching with a missing ``panel_log_v2.[].added.[].entity`` no longer fails with a ValidationError.
- ``EntityListMgr`` initializes ``EntityMatchMgr`` using supplied API token

[2.0.3] - 2025-03-21
--------------------

Added
~~~~~

- ``PBA_Generic`` now has ``markdown`` method. The current PBA supporting markdown are: Domain Abuse, Identity, Code Repo and Unsupported playbook alerts.

Changed
~~~~~~~

- ``ClassicAlert`` now has ``markdown`` method. It has been removed from ``classic_alerts.markdown``.
- ``AnalystNotes`` now skips the validation of not supported ``Events``. Validation will not fail but log a warning.


[2.0.2] - 2025-02-25
--------------------

Changed
~~~~~~~

- ``MarkdownMaker`` now supports ``character_limit``
- ``MarkdownMaker`` now supports ``defang_iocs`` to optionally defang the iocs given via ``iocs_to_defang`` before returning the markdown string


[2.0.1] - 2025-01-29
--------------------

Fixed
~~~~~

- ``AnalystNote.portal_url`` ADT now returns the correct URL
- ``RisklistMgr`` raise the correct module specific exception

Changed
~~~~~~~

- ``@connection_exceptions`` decorator now applies the exception message from the causing exception to the exception that is raised


[2.0.0] - 2024-12-18
--------------------

Added
~~~~~

- New and simplified interface for all Managers
- New ADT for all API responses
- ``pydantic`` validation of API requests and responses
- Classic Alerts V3 support
- ``BaseHTTPClient`` for generic HTTP requests
- ``base_http_client`` and ``rf_client`` example apps
- ``psengine`` CLI for creating project templates


Changed
~~~~~~~

- ``Config`` does not support ``.ini`` files anymore. It supports ``.json``, ``.toml`` and ``.env`` files.
- ``RFClient`` does not have ``<method>_request`` methods anymore, but a single ``call`` method
- Cleaned up example apps
- Moved from deprecated Analyst Notes endpoint to the new one.

Removed
~~~~~~~

- Support for ``.ini`` file settings.
- ``update_lists`` example app


[1.12.1] - 2024-04-19
---------------------

Changed
~~~~~~~

- ``RFLogger`` creates root file and console handlers (set ``psengine`` only console output with ``console_is_root=False``)
- ``RFLogger`` sets ``propagate=True`` by default


[1.12.0] - 2024-02-09
---------------------

Added
~~~~~

-  Ability to switch the base API url via an env variable ``RF_BASE_URL``
-  New parameters for the ``playbook_alerts`` stanza to control alert updates ``update_status`` and ``new_status``
-  ``RFPlaybookAlertMgr.update()`` now supports ``reopen`` parameter
-  Token and connection validation functions ``RFClient.is_token_valid()`` and ``RFClient.is_connectivity_valid()``
-  Ability to rollup a standard/flattened alert via ``RFAlert.rollup()`` function
-  ``RFPlaybookAlertIdentityNovelExposures`` new property ``exposed_secret_clear_text_value``
-  ``RFClient.post_request()`` now supports pagination 
-  ``RFClient`` supports custom certificate path and basic auth

Fixed
~~~~~

-  Enrichment sample app now correctly loads input file specified in ``settings.ini``
-  Enrichment fix for RF ID with 6 chars
-  ``FileHelpers.read_csv`` no longer closes the file prematurely causing an exception

Changed
~~~~~~~

- Python 3.6 is no longer supported. Minimum Python version is now 3.8


[1.11.0] - 2023-12-22
---------------------

Added
~~~~~

-  Support for ``Analyst Notes``
-  ``STIX2`` support
-  Support for ``Identity Exposure`` Playbook Alert
-  ``RFEnrichMgr`` refactor. ``RFEnrichMgr`` contains a list of ``RFEnrich`` objects.
-  ``RFEnrichMgr`` can enrich companies via RF Company ID or domain associated to the company.
-  ``RFEnrichMgr`` can return a json representation via ``RFEnrichMgr.json()``.


[1.10.2] - 2023-09-27
---------------------

Fixed
~~~~~

-  ``RFPlaybookAlertCodeRepoLeakage`` typo in repo properties

[1.10.1] - 2023-09-18
---------------------

Fixed
~~~~~

-  ``TestRFBasePlaybookAlert.entity_risk_score`` fixed getter

[1.10.0] - 2023-09-14
---------------------

Added
~~~~~

-  Support for ``Third-Party Risk`` Playbook Alert
-  Support for ``Cyber Vulnerability`` Playbook Alert
-  Support for ``Data Leakage on code repository`` Playbook Alert
-  Public ``RFPlaybookAlertMgr.search()`` function returns the full
   search results
-  New ``RFPlaybookAlertMgr.prepare_query()`` function for easy search
   query creation
-  New ``RFPlaybookAlertDomainAbuse.store_image()`` function to store
   the fetched raw bytes of the screenshots
-  New ``RFPlaybookAlertMgr.save_images()`` and
   ``RFPlaybookAlertMgr.save_image()`` functions to write Domain Abuse
   screenshots to disk

Changed
~~~~~~~

-  ``RFPlaybookAlertMgr._update()`` is now
   ``RFPlaybookAlertMgr.update()`` and the interface is more
   straightforward
-  ``RFPlaybookAlertMgr.fetch()`` now performs a query or individual
   alert lookup, and no longer accepts a zip of alerts to fetch
-  ``RFPlaybookAlertMgr.fetch()`` no longer writes fetched images to
   disk
-  ``RFPlaybookAlert`` replaced with ``RFBasePlaybookAlert``. Please use
   subclasses instead
-  ``RFMatchMgr.resolve_entity_id`` previously treated a string entity
   as an entity ID. The function is no longer polymorphic, and now
   accepts an entity name and optionally an entity type. It now always
   resolves entity names to an entity ID.

[1.9.0] - 2023-08-11
--------------------

Added
~~~~~

-  ``Collective Insights`` support
-  New sample app for ``Collective Insights``

[1.8.1] - 2023-07-13
--------------------

Added
~~~~~

-  New ``RFAlertMgr.fetch_rules()`` function to fetch all available
   alerting rules

Fixed
~~~~~

-  ``RFClient.make_paged_request()`` no longer fails with ``TypeError``
   when no params where specified
-  ``RFClient.make_paged_request()`` correctly adjusts ``limit``
   parameter to not ``Exceed Max Depth Allowed of 1000 Results``

Changed
~~~~~~~

-  Redused ``DEBUG`` logging verbosity when parsing Legacy Alerts
-  ``RFAlertMgr.lookup_alert()`` now utilises ``RFClient.get_request()``
   for alert lookups

[1.8.0] - 2023-06-29
--------------------

Added
~~~~~

-  New ``detection`` submodule with ``RFDetectionMgr`` and
   ``RFDetectionRule`` classes for Detection API support
-  New ``detection`` example app
-  New ``helpers.FileHelpers`` class for file read and write operations
-  New ``RFMatchMgr.resolve_entity_ids()`` function for bulk entity ID
   resolution

[1.7.0] - 2023-06-12
--------------------

Added
~~~~~

-  ``RFLogger`` now takes a ``loglevel`` argument in its constructor

Changed
~~~~~~~

-  ``psengine`` broken down into submodules
-  ``RFAlertMgr`` now also accepts a time range value for ``triggered``,
   for example: ``[2023-06-11,)``, ``[,2022-12-10]``

Fixed
~~~~~

-  ``RFClient`` issues a warning for a request with a missing API key,
   instead of uncaught ``AttributeError``
-  ``RFClient`` no longer raises ``ValueError`` if initialized without a
   valid RF API Token
-  ``RFLogger`` no longer causes REPL to exit from an uncaught exception
-  ``Config.save()`` correctly resolves the relative path of the
   ``settings.ini`` file

[1.6.0] - 2023-04-25
--------------------

Changed
~~~~~~~

-  ``Config`` rf_token, app_id, platform_id attributes are now set
   directly, not through setter functions
-  Constructors no longer require ``Config`` objects
-  Setting parsing tries as much as possible to use default values
-  Constructors allow keyword arguments for settings that could
   previously only be set by a ``Config`` object
-  Constructors raise ``ValueError`` and ``TypeError`` for invalid
   settings
-  Constructors only raise ``ConfigError`` when the settings file is
   unavailable or when there is an invalid settings configuration from
   the library programmer
-  Manager and enrichment classes have getters and setters for all
   settings. The only exception is RFRiskListMgr, which only allows
   risklist settings to be set on initialization
-  Some functions have additional keyword arguments that override
   settings
-  ``[output]`` stanza only used for risklists. Other outputs are now
   ``output`` setting in relevant stanzas
-  Manager and enrichment classes allow rf_token keyword on
   initialization

Fixed
~~~~~

-  ``RFAlertMgr.fetch_alerts`` filter ID now works correctly when the
   filter alert status has changed

[1.5.1] - 2023-02-06
--------------------

Changed
~~~~~~~

-  ``RFLogger`` takes in a set of parameters in its constructor to
   initialize logging without the ``logging.ini`` file

Changed
~~~~~~~

-  logging.ini is no longer needed when using ``RFLogger``

[1.5.0] - 2023-1-30
-------------------

Added
~~~~~

-  New class ``RFEnrichment`` added to allow IOC Enrichment

Changed
~~~~~~~

-  ``Config.parse_stanza`` now handles ``dict`` values
-  Changelog now shows dates and change categories

[1.4.1] - 2022-11-30
--------------------

Added
~~~~~

-  ``Config.set_platform_id`` to set the platform identifier
-  Full HTTP User-Agent field is now set by ``RFClient``
-  Support for new ``review``, ``rule``, ``fragment`` fields in parsed
   alerts

Removed
~~~~~~~

-  Remove Python 2.7 code
-  Remove malware sandbox playbook alert type, because API support has
   been removed

Fixed
~~~~~

-  Fix an issue causing output directories to be created whenever an
   ``output`` stanza was supplied, even if files were not written

[1.4.0] - 2022-11-08
--------------------

Added
~~~~~

-  List API support
-  List API sample application

[1.3.0] - 2022-09-27
--------------------

Added
~~~~~

-  Playbook alert support
-  Playbook alert sample application
-  ``Config.parse_stanza`` to simplify stanza parsing
-  ``output`` stanza in settings for alerts, risklist output
   destinations
-  ``RFClient.put_request`` to perform **PUT** requests
-  More helper functions within ``helpers.py``

Changed
~~~~~~~

-  Requests module requirement increased from version 2.26 to 2.27.1
-  Endpoints removed from ``settings.ini`` and moved to an internal
   ``endpoints.py`` file

Removed
~~~~~~~

-  Remove ``RFAlertMgr.remove_stale_alert_files`` and moved file
   management to ``get_alerts`` sample app

[1.2.1] - 2022-07-12
--------------------

Changed
~~~~~~~

-  Refactor ``RFAlertMgr.fetch_alerts`` ``filter_id`` kwarg usage,
   reducing payload lookups by a factor of 2
-  ``RFAlertMgr.fetch_alerts`` now always returns alerts in ascending
   order

[1.2.0] - 2022-05-27
--------------------

Added
~~~~~

-  ``Config.set_app_id`` to specify the integration identifier. This is
   picked up by ``RFClient`` which sets the ``User-Agent`` header
-  ``Config.update_stanza`` to update self.settings
-  ``Config.save`` to save updated settings to file

[1.1.0] - 2022-04-26
--------------------

Added
~~~~~

-  Add ``triggered`` param to ``RFAlertMgr.ingest_alerts``

Changed
~~~~~~~

-  Drop Python 3.7 minimum requirement to Python 3.6

Removed
~~~~~~~

-  Remove `jsonschema <https://pypi.org/project/jsonschema/>`__
   dependency

[1.0.1] - 2022-04-26
--------------------

Fixed
~~~~~

-  Fix a bug causing some alert fields to populate null when parsed

[1.0.0] - 2022-03-17
--------------------

Added
~~~~~

-  Official Python package release

[0.1.0] - 2022-02-18
--------------------

Added
~~~~~

-  Beta Python package release

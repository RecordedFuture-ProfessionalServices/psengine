# Changelog

## v2.1.0 - 2025-07-02

### Added

-   `IdentityMgr` added to support interaction with the identity API.

## v2.0.7 - 2025-07-02

### Added

-   `PBA_MalwareReport` playbook alert is now supported, including its
    markdown rendering.
-   `RFClient.request_paged()`supports multiple paths when used on a
    POST request where the pagination field is `next_offset`.

### Changed

-   `PlaybookAlertMgr.update()` now accepts either a playbook alert ADT
    instance or an alert ID string as the `alert` parameter, instead of
    only a playbook alert ADT.
-   `PlaybookAlertMgr.search()` and `PlaybookAlertMgr.fetch_bulk()` now
    fully support pagination. The `alerts_per_page` and `max_results`
    parameters accurately control the number of alerts returned,
    ensuring users receive the requested number of results even when the
    API response is paginated.
-   `PlaybookAlertMgr.search()` and `PlaybookAlertMgr.fetch_bulk()` now
    restrict searches and fetches to supported playbook alert categories
    only. Providing an unsupported alert category will raise a
    `ValueError`.

### Fixed

-   `RFClient.request_paged()` now correctly updates the `limit`
    parameter when using the `post` method, ensuring the correct number
    of results are returned.
-   `PlaybookAlertMgr` bulk operations now count the correct amount of
    errors from ingestion.

### Removed

-   Ability for searching and fetching unsupported playbook alert
    categories and returning a `PBA_Generic` ADT instance.

## v2.0.6 - 2025-06-06

### Added

-   Analyst Note now supports markdown.
-   Third Party Risk Plyabook Alert now supports markdown.
-   Cyber Vulnerability Playbook Alert now supports markdown.
-   Geopol Playbook Alert is now supported, along with its markdown.

### Changed

-   `MarkdownMaker.validate_section` now supports the `content`
    parameter as a string.

### Fixed

-   `PlaybookAlertMgr` applies `panels` correctly when `fetch` or bulk
    operations are called.

## v2.0.5 - 2025-05-12

### Fixed

-   `LookupMgr` does not fail while enrichment entities that have
    unexpected characters.

## v2.0.4 - 2025-05-07

### Fixed

-   `ClassicAlert.markdown()` no longer fails when hits.fragment
    field is None
-   `Domain Abuse` playbook alert fetching with a missing
    `panel_log_v2.[].added.[].entity` no longer fails with a
    ValidationError.
-   `EntityListMgr` initializes `EntityMatchMgr` using supplied API
    token

### Fixed

-   `PlaybookAlertMgr` applies `panels` correctly when `fetch` or bulk
    operations are called.

## v2.0.3 - 2025-03-21

### Added

-   `PBA_Generic` now has `markdown` method. The current PBA supporting
    markdown are: Domain Abuse, Identity, Code Repo and Unsupported
    playbook alerts.

### Changed

-   `ClassicAlert` now has `markdown` method. It has been removed from
    `classic_alerts.markdown`.
-   `AnalystNotes` now skips the validation of not supported `Events`.
    Validation will not fail but log a warning.

## v2.0.2 - 2025-02-25

### Changed

-   `MarkdownMaker` now supports `character_limit`
-   `MarkdownMaker` now supports `defang_iocs` to optionally defang the
    iocs given via `iocs_to_defang` before returning the markdown string

## v2.0.1 - 2025-01-29

### Fixed

-   `AnalystNote.portal_url` ADT now returns the correct URL
-   `RisklistMgr` raise the correct module specific exception

### Changed

-   `@connection_exceptions` decorator now applies the exception message
    from the causing exception to the exception that is raised

## v2.0.0 - 2024-12-18

### Added

-   New and simplified interface for all Managers
-   New ADT for all API responses
-   `pydantic` validation of API requests and responses
-   Classic Alerts V3 support
-   `BaseHTTPClient` for generic HTTP requests
-   `base_http_client` and `rf_client` example apps

### Changed

-   `Config` does not support `.ini` files anymore. It supports `.json`,
    `.toml` and `.env` files.
-   `RFClient` does not have `<method>_request` methods anymore, but a
    single `call` method
-   Cleaned up example apps
-   Moved from deprecated Analyst Notes endpoint to the new one.

### Removed

-   Support for `.ini` file settings.
-   `update_lists` example app


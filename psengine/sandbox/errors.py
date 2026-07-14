##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

from ..errors import RecordedFutureError


class SampleFetchError(RecordedFutureError):
    """Raised when a sample lookup against `/samples/{id}` fails."""


class SampleFileFetchError(RecordedFutureError):
    """Raised when a sample file lookup against `/samples/{id}/sample` fails."""


class SampleDeleteError(RecordedFutureError):
    """Raised when a sample delete against `/samples/{id}` fails."""


class SampleSubmitError(RecordedFutureError):
    """Raised when a sample submission against `/samples` fails."""


class SampleSummaryError(RecordedFutureError):
    """Raised when a sample summary lookup against `/samples/{id}/summary` fails."""


class SampleStaticReportError(RecordedFutureError):
    """Raised when a static report lookup against `/samples/{id}/reports/static` fails."""


class SampleOverviewError(RecordedFutureError):
    """Raised when an overview report lookup against `/samples/{id}/overview.json` fails."""


class SampleBehavioralReportError(RecordedFutureError):
    """Raised when a behavioral report lookup fails.

    Covers the initial sample fetch and connection-level failures of the per-task
    `/samples/{id}/{task_id}/report_triage.json` requests made by
    `SandboxMgr.fetch_behavioral_reports`. Per-task HTTP failures do not raise --
    they are reported in the `not_ready`/`failed` buckets of the returned
    `BehavioralReportsResult`.
    """


class SampleReportNotAvailableError(SampleOverviewError, SampleStaticReportError):
    """Raised when the sample exists but the requested report is not (yet) available.

    The Sandbox API returns a discriminated 404 -- `REPORT_NOT_AVAILABLE` (overview) or
    `NOT_AVAILABLE` (static reports) -- when the sample exists but its analysis has not
    produced the requested report yet (e.g. it is still in `static_analysis`).

    `SandboxMgr.fetch_behavioral_reports` does not raise this: per-task not-ready
    outcomes are reported in the `not_ready` bucket of its `BehavioralReportsResult`.
    """


class SampleReportNotFoundError(
    SampleOverviewError, SampleStaticReportError, SampleBehavioralReportError
):
    """Raised when the sample itself does not exist for a report lookup (404 `NOT_FOUND`)."""


class SampleProfileError(RecordedFutureError):
    """Raised when setting a sample profile against `/samples/{id}/profile` (POST) fails."""


class SampleSearchError(RecordedFutureError):
    """Raised when a sample search against `/search` fails."""


class SamplesFetchError(RecordedFutureError):
    """Raised when a sample listing against `/samples` fails."""


class ProfileFetchError(RecordedFutureError):
    """Raised when a profile lookup against `/profiles` fails."""


class ProfileNotFoundError(RecordedFutureError):
    """Raised when a single-profile lookup against `/profiles/{id}` (GET) fails."""


class ProfileCreateError(RecordedFutureError):
    """Raised when a profile create against `/profiles` (POST) fails."""


class ProfileUpdateError(RecordedFutureError):
    """Raised when a profile update against `/profiles/{id}` (PUT) fails."""


class ProfileDeleteError(RecordedFutureError):
    """Raised when a profile delete against `/profiles/{id}` (DELETE) fails."""

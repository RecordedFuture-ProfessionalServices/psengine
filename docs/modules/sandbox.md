## Introduction

The `SandboxMgr` class of the `sandbox` module wraps the Recorded Future Sandbox (Triage) API so you can detonate samples, retrieve analysis reports, and manage company-wide analysis profiles. 

It covers:

- Submitting samples for analysis — local files, URLs, sandbox-fetched URLs, and imports from public Triage
- Searching and listing submitted samples
- Fetching per-sample status, full records, summary reports, and full analysis reports (overview, static, behavioral)
- Creating, listing, updating, and deleting analysis profiles
- Deleting samples (Enterprise tier, `org_admin` only)

See the [**API Reference**](../api/sandbox/sandbox_mgr.md) for internal details of the module.

## Notes

- The Sandbox uses a **separate token** from the rest of the platform — set `RF_SANDBOX_TOKEN` (not `RF_TOKEN`) in your environment, or pass it explicitly: `SandboxMgr(api_token=...)`. Tokens are issued at [`/account`](https://sandbox.recordedfuture.com/account) under "API Access".
- Pick the right region with `sandbox_choice`. The default is `'eu'` (`https://sandbox.recordedfuture.com/api/v0`); other choices are `'usa'`, `'apj'`, `'public'` (the community Triage at `tria.ge` — all submissions are visible to everyone), and `'private'` (self-hosted deployments).
- `submit_sample` takes one of four `kind`s, each with its own required parameter:
    - `kind='file'` requires `file_path` (a `Path` to a local file).
    - `kind='url'` requires `url` — the URL is opened in a browser inside the analysis VM.
    - `kind='fetch'` requires `url` — the sandbox downloads the file at that URL first, then detonates it.
    - `kind='import'` requires `source_id` — a public Triage sample id to copy in.
- Submissions are asynchronous. The sample status transitions through `pending` → `static_analysis` → `scheduled` → `running` → `processing` → `reported` (terminal, success) or `failed` (terminal, error). To wait for results, poll `fetch_sample(id).status` until it reaches a terminal state (see example 4 below). Typical wall-clock for a URL submission is 1–3 minutes.
- `delete_sample`, `update_profile`, and `delete_profile` are designed for best-effort cleanup:
    - `update_profile` and `delete_profile` are **idempotent on 404** — a missing target returns `updated=False` / `deleted=False` instead of raising, so you can call them without first checking existence.
    - `delete_sample` is not idempotent: any non-2xx response (including "already deleted") raises `SampleDeleteError`. The Triage API maps all delete failures to `401`, so the raw error message on the exception is your only signal for *why*.
- `update_profile` is a **full replace**: name, tags and timeout are required; any optional field you omit is cleared on the server.
- Three methods return full analysis reports — all require the sample to have reached `reported` status:
    - `fetch_sample_overview_report` — the richest result: combined verdict, extracted malware configs, per-target IOC lists (domains, IPs, URLs), and a per-task breakdown. Raises `SampleReportNotAvailableError` if the sample exists but hasn't finished analysis yet, or `SampleReportNotFoundError` if the sample id is unknown — both are subclasses of `SampleOverviewError`.
    - `fetch_sample_static_report` — the pre-detonation pass: file identification, static signatures, the `files` table (the submitted file plus any archive members), and malware configs recoverable without execution.
    - `fetch_behavioral_reports` — fetches every behavioral task's detonation report in one call: process tree, network flows, DNS/HTTP requests, and dumped artifacts. Returns a `BehavioralReportsResult` envelope: finished reports in `reports`, still-running task ids in `not_ready` (check `result.complete` and poll again later), and per-task fetch failures in `failed` — so one unfinished task doesn't hide the reports that are ready. Pass `max_workers` to fetch them concurrently when a sample has multiple behavioral tasks (e.g. multi-architecture Linux submissions).
- Each endpoint family raises its own subclass of `RecordedFutureError` — `SampleSubmitError`, `SampleFetchError`, `SampleFileFetchError`, `SampleDeleteError`, `SampleSearchError`, `SamplesFetchError`, `SampleSummaryError`, `SampleStaticReportError`, `SampleOverviewError`, `SampleReportNotAvailableError`, `SampleReportNotFoundError`, `SampleBehavioralReportError`, `SampleProfileError`, `ProfileFetchError`, `ProfileNotFoundError`, `ProfileCreateError`, `ProfileUpdateError`, `ProfileDeleteError`. See the [**errors API reference**](../api/sandbox/errors.md) for the full list.
- The SaaS sandbox is capped at 1,000 submissions per enterprise per day. Examples below all submit a benign URL — they count against that quota.

## Examples

{! modules/_includes/examples_sb_warning.md !}

#### 1: Submit a URL for analysis

`submit_sample` returns immediately with a `SearchResult` carrying the new sample's `id_` and initial `status`. The example below uses `kind='url'`, which detonates the URL inside a browser VM. `user_tags` are free-form labels you can use later to find the submission.

```python
--8<-- "docs/examples/sandbox/example_1.py"
```

A typical run prints something like:

```
Submitted: id=260501-h4p7laawme, kind=url, status=pending
```

#### 2: Search for samples by malware family

`search_samples` accepts the same field-prefixed query syntax as the Sandbox web UI (`family:`, `tag:`, `sha256:`, `ip:`, `domain:`, ...). Each filter `kwarg` (`family`, `tag`, `botnet`, ...) is composed with `AND` into the final query string. The example searches for up to five samples matching any of three malware families.

!!! tip

    Pass any combination of filter `kwargs` — they're joined with `AND`. For free-form composition (`OR`/`NOT`), pass a raw query via the `query=` argument instead.

```python
--8<-- "docs/examples/sandbox/example_2.py"
```

#### 3: List your own samples and inspect one in detail

`fetch_samples` lists the samples your account can see; `subset='owned'` (the default) is just your own submissions, `'org'` is everything your company has access to, and `'public'` only works on the public Triage cloud. After listing, pass an `id_` to `fetch_sample` to retrieve the richer `SampleOut` record (the same shape but with the per-task analysis breakdown attached).

```python
--8<-- "docs/examples/sandbox/example_3.py"
```

#### 4: Submit, wait for the report, and read the summary

Submissions are asynchronous, so a fresh `id_` will return `status='pending'` for a while. The example polls `fetch_sample` every 10 seconds until the status reaches a terminal state (`reported` or `failed`), then calls `fetch_sample_summary` to retrieve the score and per-task breakdown.

!!! tip

    A URL submission usually reaches `reported` within 1–3 minutes. The script caps the wait at 10 minutes via `TIMEOUT_SEC` — tune both to your needs.

```python
--8<-- "docs/examples/sandbox/example_4.py"
```

The summary's `score` is a 1–10 verdict (10 = known bad, 1 = no malicious behaviour observed); the `tasks` dict carries per-task results keyed by `static1`, `behavioral1`, and so on.

#### 5: Submit and immediately delete a sample

`delete_sample` removes the sample and all its analyses. This example submits a throwaway URL and deletes it in the same run, useful for housekeeping flows where the submission is only needed to drive a downstream action.

!!! note

    `delete_sample` requires the `org_admin` role on Enterprise Sandbox. On the public Triage cloud, samples can't be deleted at all and the call will raise `SampleDeleteError`.

```python
--8<-- "docs/examples/sandbox/example_5.py"
```

#### 6: Manage analysis profiles end-to-end

Profiles are company-wide analysis configurations (OS tags, network mode, timeout, browser, optional VPN region). This example walks the full CRUD cycle on a single profile: `create_profile` → `fetch_profiles` (list) → `fetch_profile` (round-trip) → `update_profile` (full replace — every non-`id` field is required) → `delete_profile`.

!!! tip

    `update_profile` and `delete_profile` are idempotent on 404, they return `updated=False` / `deleted=False` if the target is already gone. Check the returned `.updated` / `.deleted` flag rather than wrapping the call in `try/except`.

```python
--8<-- "docs/examples/sandbox/example_6.py"
```

#### 7: Fetch the overview report for a completed sample

`fetch_sample_overview_report` returns the richest single-call result: the overall verdict `score`, malware `family` tags, all recovered `extracted` configs (C2s, crypto keys, credentials), per-`target` IOC lists (domains, IPs, URLs), and a `tasks` map keyed by task id. It is only available once the sample has reached `reported` status.

!!! note

    Two distinct 404 subclasses are raised: `SampleReportNotAvailableError` means the sample exists but analysis isn't finished yet (retry later); `SampleReportNotFoundError` means the sample id is unknown. Both are subclasses of `SampleOverviewError`.

!!! tip

    Pass `wait_until_ready=True` to poll internally until the overview is available, instead of catching `SampleReportNotAvailableError` yourself. It retries every `OVERVIEW_REPORT_WAIT_INTERVAL_SECONDS` (20s) and raises `SampleReportNotAvailableError` once `timeout` seconds (default 1800) elapse without success. `SampleReportNotFoundError` (unknown sample id) is never retried.

```python
--8<-- "docs/examples/sandbox/example_7.py"
```

#### 8: Inspect the static analysis report

`fetch_sample_static_report` returns the pre-detonation pass: the analysis `score`, any static `signatures`, the `files` table (the submitted file plus every member unpacked from it — useful for archives), and any malware configs extractable without execution.

!!! tip

    Pass `wait_until_ready=True` to poll internally until the report is available, instead of catching `SampleReportNotAvailableError` yourself. It retries every `STATIC_REPORT_WAIT_INTERVAL_SECONDS` (20s) and raises `SampleReportNotAvailableError` once `timeout` seconds (default 600) elapse without success. `SampleReportNotFoundError` (unknown sample id) is never retried.

```python
--8<-- "docs/examples/sandbox/example_8.py"
```

#### 9: Walk the behavioral detonation reports

`fetch_behavioral_reports` discovers the sample's behavioral tasks and fetches each task's full detonation report in one call, returning a `BehavioralReportsResult`: finished reports in `reports`, task ids still awaiting analysis in `not_ready`, and per-task fetch failures in `failed` (each with its status code and message). `result.complete` is `True` once nothing is pending — including when the sample has no behavioral tasks at all — so a poll loop can simply retry until it's set. Each `BehavioralReport` carries the run `analysis` verdict, the `processes` tree, `network` flows and DNS/HTTP requests, `dumped` artifacts, and any `extracted` configs. Non-behavioral tasks (`static*`, `urlscan*`) are skipped.

!!! tip

    Pass `max_workers` to fetch per-task reports concurrently when a sample has several behavioral tasks (e.g. multi-architecture Linux submissions). For samples with a single behavioral task the default sequential mode is sufficient.

```python
--8<-- "docs/examples/sandbox/example_9.py"
```

#### 10: Wait for every behavioral task to finish

Pass `wait_until_ready=True` to `fetch_behavioral_reports` to poll every `BEHAVIORAL_REPORT_WAIT_INTERVAL_SECONDS` (20s) until `result.complete` is `True` or `timeout` seconds (default 1800) elapse.

!!! note

    A timeout here never raises — check `result.complete`; `not_ready` still lists whatever hadn't resolved.

```python
--8<-- "docs/examples/sandbox/example_10.py"
```

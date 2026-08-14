#!/usr/bin/env bash
#
# Run every docs example against the live Recorded Future API in parallel,
# retrying failures that look like transient API flakes and reporting real
# code failures with full logs.
#
# Usage:
#   scripts/run_doc_examples.sh
#
# Environment overrides:
#   EXAMPLES_DIR   Directory to scan for *.py (default: ./docs/examples)
#   JOBS           Parallelism for the first pass (default: 30)
#   MAX_ATTEMPTS   Attempts per file before giving up (default: 3)
#   RETRY_DELAY    Seconds between retries; doubles each attempt (default: 2)
#   LOG_DIR        Where per-attempt logs land (default: a fresh mktemp dir)
#
# Requires: bash 4+, uv, GNU parallel.
# Exits 0 if everything passed (including expected-fail examples that failed as expected).
# Exits 1 if any example hard-failed or exhausted its flaky retries.

set -uo pipefail

EXAMPLES_DIR="${EXAMPLES_DIR:-./docs/examples}"
JOBS="${JOBS:-30}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"
RETRY_DELAY="${RETRY_DELAY:-2}"
LOG_DIR="${LOG_DIR:-$(mktemp -d -t doc-examples-XXXXXX)}"

mkdir -p "$LOG_DIR"

# Examples that are documented as failing (expected exit code 1).
KNOWN_FAILS=(
  "./docs/examples/error_handling/example_1a.py"
  "./docs/examples/error_handling/example_1b.py"
  "./docs/examples/error_handling/example_3.py"
  "./docs/examples/config/example_6.py"
)

# Stderr/stdout signatures that mean "the API misbehaved, worth retrying".
# Anything not matching this is treated as a real code failure and fails fast.
FLAKY_REGEX='HTTP/[0-9.]+ 5[0-9]{2}|status[^0-9]*5[0-9]{2}| 5[0-9]{2} (Server|Bad Gateway|Service Unavailable|Gateway Timeout)|timeout|timed out|Read timed out|ReadTimeout|ConnectTimeout|ConnectionError|ConnectionResetError|RemoteDisconnected|ServerDisconnected|Connection aborted|Temporary failure in name resolution|rate.?limit(ed)?| 429 |Too Many Requests'

KNOWN_FAILS_FILE="$(mktemp)"
FAIL_LIST_FILE="$(mktemp)"
trap 'rm -f "$KNOWN_FAILS_FILE" "$FAIL_LIST_FILE"' EXIT

printf '%s\n' "${KNOWN_FAILS[@]}" > "$KNOWN_FAILS_FILE"

in_ci() { [[ -n "${GITHUB_ACTIONS:-}" ]]; }
group_start() { if in_ci; then echo "::group::$*"; else echo; echo "===== $* ====="; fi; }
group_end()   { if in_ci; then echo "::endgroup::";  else echo "===== end ====="; fi; }
ts() { date -u +%H:%M:%S; }
say() { printf '[%s] %s\n' "$(ts)" "$*"; }

safe_name() { echo "$1" | tr '/' '_' | sed 's/^_*//'; }
expected_rc() { if grep -Fxq -- "$1" "$KNOWN_FAILS_FILE"; then echo 1; else echo 0; fi; }

# Run one file once. Combined output goes to $2.
run_once() {
  local file="$1" log="$2"
  uv run "$file" >"$log" 2>&1
  echo $?
}

# Retry-aware runner. Prints per-attempt status. Returns 0 on success, 1 on failure.
run_with_retry() {
  local file="$1"
  local exp_rc; exp_rc="$(expected_rc "$file")"
  local delay="$RETRY_DELAY"
  local attempt=1
  local rc log name
  name="$(safe_name "$file")"

  while (( attempt <= MAX_ATTEMPTS )); do
    log="$LOG_DIR/${name}.attempt-${attempt}.log"
    rc="$(run_once "$file" "$log")"

    if [[ "$rc" == "$exp_rc" ]]; then
      if (( attempt > 1 )); then
        say "PASS after $attempt attempt(s): $file"
      fi
      return 0
    fi

    if grep -Eq "$FLAKY_REGEX" "$log"; then
      say "FLAKY attempt $attempt/$MAX_ATTEMPTS rc=$rc expected=$exp_rc — $file — sleeping ${delay}s"
      sleep "$delay"
      delay=$(( delay * 2 ))
      (( attempt++ ))
      continue
    fi

    say "HARD FAIL rc=$rc expected=$exp_rc — $file (no flaky signature detected, not retrying)"
    return 1
  done

  say "FLAKY EXHAUSTED after $MAX_ATTEMPTS attempts — $file"
  return 1
}

# parallel worker: run one file and append to the shared fail list on failure.
capture() {
  local file="$1"
  if ! run_with_retry "$file"; then
    echo "$file" >> "$FAIL_LIST_FILE"
    return 1
  fi
}

# Dump the last-attempt log for a failed file with a CI-friendly grouped section.
report_failure() {
  local file="$1"
  local name; name="$(safe_name "$file")"
  local last_log
  last_log="$(ls -1 "$LOG_DIR"/"${name}".attempt-*.log 2>/dev/null | tail -n1)"

  group_start "FAIL: $file"
  echo "expected exit code: $(expected_rc "$file")"
  if [[ -n "$last_log" && -f "$last_log" ]]; then
    echo "log: $last_log"
    echo "---"
    cat "$last_log"
  else
    echo "(no log captured)"
  fi
  group_end
}

# GNU parallel spawns children via $SHELL — force bash so exported functions work everywhere.
export SHELL; SHELL="$(command -v bash)"
export EXAMPLES_DIR JOBS MAX_ATTEMPTS RETRY_DELAY LOG_DIR FLAKY_REGEX
export KNOWN_FAILS_FILE FAIL_LIST_FILE
export -f in_ci group_start group_end ts say safe_name expected_rc
export -f run_once run_with_retry capture

say "Scanning $EXAMPLES_DIR — jobs=$JOBS attempts=$MAX_ATTEMPTS retry_delay=${RETRY_DELAY}s"
say "Per-attempt logs: $LOG_DIR"

find "$EXAMPLES_DIR" -type f -name "*.py" -print0 \
  | parallel -0 -j "$JOBS" capture {} || true

if [[ -s "$FAIL_LIST_FILE" ]]; then
  sort -u "$FAIL_LIST_FILE" -o "$FAIL_LIST_FILE"
  fail_count=$(wc -l < "$FAIL_LIST_FILE" | tr -d ' ')

  say "$fail_count example(s) failed after retries — dumping logs"
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    report_failure "$file"
  done < "$FAIL_LIST_FILE"

  say "Failed files:"
  sed 's/^/  - /' "$FAIL_LIST_FILE"

  # Persist the failure list for downstream steps (e.g., GH issue body).
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    {
      echo "failed_count=$fail_count"
      echo "failed_files<<EOF"
      cat "$FAIL_LIST_FILE"
      echo "EOF"
    } >> "$GITHUB_OUTPUT"
  fi

  exit 1
fi

say "All examples passed ✅"

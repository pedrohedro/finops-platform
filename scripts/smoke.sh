#!/usr/bin/env bash
set -euo pipefail

DOCKER_BIN=${DOCKER_BIN:-docker}
PYTHON_BIN=${PYTHON:-python3}
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
project_name="finops-smoke-$$"
compose_up_timeout_seconds=${SMOKE_COMPOSE_UP_TIMEOUT_SECONDS:-480}
compose_job_timeout_seconds=${SMOKE_COMPOSE_JOB_TIMEOUT_SECONDS:-150}
job_timeout_seconds=${SMOKE_JOB_TIMEOUT_SECONDS:-120}
probe_timeout_seconds=${SMOKE_PROBE_TIMEOUT_SECONDS:-30}
cleanup_timeout_seconds=${SMOKE_CLEANUP_TIMEOUT_SECONDS:-60}

for timeout_seconds in \
  "$compose_up_timeout_seconds" \
  "$compose_job_timeout_seconds" \
  "$job_timeout_seconds" \
  "$probe_timeout_seconds" \
  "$cleanup_timeout_seconds"
do
  [[ "$timeout_seconds" =~ ^[1-9][0-9]*$ ]] || exit 64
done

env_file=$(mktemp "${TMPDIR:-/tmp}/finops-smoke.XXXXXX")
printf '%s\n' \
  'CLICKHOUSE_HOST=clickhouse' \
  'CLICKHOUSE_PORT=9000' \
  'CLICKHOUSE_USER=default' \
  'CLICKHOUSE_PASSWORD=finops' \
  'CLICKHOUSE_DB=finops' \
  'CLICKHOUSE_CONNECT_TIMEOUT=2' \
  'CLICKHOUSE_SEND_RECEIVE_TIMEOUT=5' \
  'CORS_ORIGINS=http://localhost:3000' \
  >"$env_file"

compose_command=(
  env
  -u AWS_ACCESS_KEY_ID
  -u AWS_SECRET_ACCESS_KEY
  -u AWS_SESSION_TOKEN
  -u AWS_PROFILE
  -u AWS_DEFAULT_PROFILE
  -u AWS_DEFAULT_REGION
  -u AWS_REGION
  -u AWS_WEB_IDENTITY_TOKEN_FILE
  -u AWS_ROLE_ARN
  -u AWS_CONTAINER_CREDENTIALS_RELATIVE_URI
  -u AWS_CONTAINER_CREDENTIALS_FULL_URI
  "FINOPS_ENV_FILE=$env_file"
  API_PORT=0
  DASHBOARD_PORT=0
  CLICKHOUSE_HTTP_PORT=0
  CLICKHOUSE_NATIVE_PORT=0
  "$DOCKER_BIN"
  compose
  --env-file "$env_file"
  --project-name "$project_name"
)

compose() {
  "${compose_command[@]}" "$@"
}

bounded_compose() {
  local timeout_seconds=$1
  shift
  "$PYTHON_BIN" "$repo_root/scripts/run_with_timeout.py" \
    "$timeout_seconds" "${compose_command[@]}" "$@"
}

cleanup() {
  original_status=$?
  trap - EXIT INT TERM

  if ((original_status != 0)); then
    bounded_compose "$probe_timeout_seconds" logs --no-color || true
  fi

  teardown_status=0
  bounded_compose "$cleanup_timeout_seconds" \
    down -v --remove-orphans --rmi local >/dev/null \
    || teardown_status=$?

  env_cleanup_status=0
  rm -f "$env_file" || env_cleanup_status=$?

  if ((original_status != 0)); then
    exit "$original_status"
  fi
  if ((teardown_status != 0)); then
    exit "$teardown_status"
  fi
  exit "$env_cleanup_status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

bounded_compose "$compose_up_timeout_seconds" \
  up -d --build --wait --wait-timeout 180 clickhouse api dashboard
bounded_compose "$compose_job_timeout_seconds" \
  run --rm --no-deps collector timeout "$job_timeout_seconds" python collector.py
bounded_compose "$compose_job_timeout_seconds" \
  run --rm --no-deps normalizer timeout "$job_timeout_seconds" python normalizer.py
bounded_compose "$compose_job_timeout_seconds" \
  run --rm --no-deps forecast timeout "$job_timeout_seconds" python forecast.py

bounded_compose "$probe_timeout_seconds" exec -T api python -c \
  "import urllib.request; urllib.request.urlopen('http://localhost:8000/readyz', timeout=5)"
bounded_compose "$probe_timeout_seconds" exec -T dashboard node -e \
  "fetch('http://localhost:3000/', { signal: AbortSignal.timeout(10000) }).then(r => { if (!r.ok) process.exit(1) }).catch(() => process.exit(1))"

counts=$(
  bounded_compose "$probe_timeout_seconds" exec -T clickhouse clickhouse-client \
    --database finops \
    --connect_timeout 5 \
    --send_timeout 10 \
    --receive_timeout 10 \
    --max_execution_time 10 \
    --format TSV \
    --query \
    "SELECT toUInt8(countIf(record_type = 'actual') > 0), toUInt8(countIf(record_type = 'forecast') > 0) FROM costs"
)
test "$counts" = $'1\t1'

printf 'compose smoke: ok\n'

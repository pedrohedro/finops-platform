#!/usr/bin/env bash
set -euo pipefail

DOCKER_BIN=${DOCKER_BIN:-docker}
project_name="finops-smoke-$$"
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

compose() {
  env \
    -u AWS_ACCESS_KEY_ID \
    -u AWS_SECRET_ACCESS_KEY \
    -u AWS_SESSION_TOKEN \
    -u AWS_PROFILE \
    -u AWS_DEFAULT_PROFILE \
    -u AWS_DEFAULT_REGION \
    -u AWS_REGION \
    -u AWS_WEB_IDENTITY_TOKEN_FILE \
    -u AWS_ROLE_ARN \
    -u AWS_CONTAINER_CREDENTIALS_RELATIVE_URI \
    -u AWS_CONTAINER_CREDENTIALS_FULL_URI \
    FINOPS_ENV_FILE="$env_file" \
    API_PORT=0 \
    DASHBOARD_PORT=0 \
    CLICKHOUSE_HTTP_PORT=0 \
    CLICKHOUSE_NATIVE_PORT=0 \
    "$DOCKER_BIN" compose --env-file "$env_file" --project-name "$project_name" "$@"
}

cleanup() {
  cleanup_status=$?
  trap - EXIT INT TERM

  if ((cleanup_status != 0)); then
    compose logs --no-color || true
  fi

  compose down -v --remove-orphans >/dev/null 2>&1 || true
  rm -f "$env_file"
  exit "$cleanup_status"
}
trap cleanup EXIT INT TERM

compose up -d --build --wait --wait-timeout 180 clickhouse api dashboard
compose run --rm --no-deps collector timeout 120 python collector.py
compose run --rm --no-deps normalizer timeout 120 python normalizer.py
compose run --rm --no-deps forecast timeout 120 python forecast.py

compose exec -T api python -c \
  "import urllib.request; urllib.request.urlopen('http://localhost:8000/readyz', timeout=5)"
compose exec -T dashboard node -e \
  "fetch('http://localhost:3000/').then(r => { if (!r.ok) process.exit(1) }).catch(() => process.exit(1))"

counts=$(
  compose exec -T clickhouse clickhouse-client \
    --database finops \
    --format TSV \
    --query \
    "SELECT toUInt8(countIf(record_type = 'actual') > 0), toUInt8(countIf(record_type = 'forecast') > 0) FROM costs"
)
test "$counts" = $'1\t1'

printf 'compose smoke: ok\n'

#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

fake_docker="$tmp_dir/docker"
fake_log="$tmp_dir/docker.log"

cat >"$fake_docker" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail

: "${FAKE_DOCKER_LOG:?}"

printf 'args=%s\n' "$*" >>"$FAKE_DOCKER_LOG"
printf 'envfile=%s\n' "${FINOPS_ENV_FILE:-}" >>"$FAKE_DOCKER_LOG"
if [[ -f "${FINOPS_ENV_FILE:-}" ]]; then
  grep '^NEXT_PUBLIC_API_URL=' "$FINOPS_ENV_FILE" >>"$FAKE_DOCKER_LOG" || true
fi

for variable in \
  AWS_ACCESS_KEY_ID \
  AWS_SECRET_ACCESS_KEY \
  AWS_SESSION_TOKEN \
  AWS_PROFILE \
  AWS_DEFAULT_PROFILE \
  AWS_DEFAULT_REGION \
  AWS_REGION \
  AWS_WEB_IDENTITY_TOKEN_FILE \
  AWS_ROLE_ARN \
  AWS_CONTAINER_CREDENTIALS_RELATIVE_URI \
  AWS_CONTAINER_CREDENTIALS_FULL_URI
do
  if printenv "$variable" >/dev/null 2>&1; then
    printf 'unexpected_aws_env=%s\n' "$variable" >>"$FAKE_DOCKER_LOG"
    exit 90
  fi
done

if [[ -n "${FAKE_FAIL_ON:-}" && "$*" == *"$FAKE_FAIL_ON"* ]]; then
  exit "${FAKE_FAIL_STATUS:-23}"
fi

if [[ -n "${FAKE_FAIL_ON_SECOND:-}" && "$*" == *"$FAKE_FAIL_ON_SECOND"* ]]; then
  exit "${FAKE_FAIL_STATUS_SECOND:-47}"
fi

if [[ -n "${FAKE_SLEEP_ON:-}" && "$*" == *"$FAKE_SLEEP_ON"* ]]; then
  sleep "${FAKE_SLEEP_SECONDS:-2}"
fi

if [[ "$*" == *"exec -T clickhouse clickhouse-client"* ]]; then
  printf '1\t1\n'
fi
FAKE
chmod +x "$fake_docker"

assert_log_contains() {
  grep -F -- "$1" "$fake_log" >/dev/null
}

run_smoke() {
  env \
    AWS_ACCESS_KEY_ID=should-not-leak \
    AWS_SECRET_ACCESS_KEY=should-not-leak \
    AWS_SESSION_TOKEN=should-not-leak \
    AWS_PROFILE=should-not-leak \
    AWS_DEFAULT_REGION=should-not-leak \
    DOCKER_BIN="$fake_docker" \
    FAKE_DOCKER_LOG="$fake_log" \
    "$repo_root/scripts/smoke.sh"
}

run_smoke

assert_log_contains "up -d --build --wait --wait-timeout 180 clickhouse api dashboard"
assert_log_contains "run --rm --no-deps collector timeout 120 python collector.py"
assert_log_contains "run --rm --no-deps normalizer timeout 120 python normalizer.py"
assert_log_contains "run --rm --no-deps forecast timeout 120 python forecast.py"
assert_log_contains "exec -T api python -c"
assert_log_contains "exec -T dashboard node -e"
assert_log_contains "exec -T clickhouse clickhouse-client"
assert_log_contains "down -v --remove-orphans --rmi local"
assert_log_contains "AbortSignal.timeout(10000)"
assert_log_contains "NEXT_PUBLIC_API_URL=http://localhost:8000"
assert_log_contains "content-security-policy"
assert_log_contains "new URL(process.env.NEXT_PUBLIC_API_URL).origin"
assert_log_contains "--connect_timeout 5"
assert_log_contains "--send_timeout 10"
assert_log_contains "--receive_timeout 10"
assert_log_contains "--max_execution_time 10"

if grep -F "unexpected_aws_env=" "$fake_log" >/dev/null; then
  exit 1
fi

env_file=$(awk -F= '/^envfile=/{print $2; exit}' "$fake_log")
test -n "$env_file"
assert_log_contains "compose --env-file $env_file --project-name"
test ! -e "$env_file"

: >"$fake_log"
set +e
FAKE_FAIL_ON="run --rm --no-deps normalizer" run_smoke
smoke_status=$?
set -e

test "$smoke_status" -eq 23
assert_log_contains "logs --no-color"
assert_log_contains "down -v --remove-orphans --rmi local"

: >"$fake_log"
set +e
FAKE_FAIL_ON="down -v --remove-orphans --rmi local" run_smoke
cleanup_status=$?
set -e

test "$cleanup_status" -eq 23

: >"$fake_log"
set +e
FAKE_FAIL_ON="run --rm --no-deps normalizer" \
  FAKE_FAIL_ON_SECOND="down -v --remove-orphans --rmi local" \
  run_smoke
smoke_and_cleanup_status=$?
set -e

test "$smoke_and_cleanup_status" -eq 23

: >"$fake_log"
set +e
FAKE_SLEEP_ON="up -d --build" \
  FAKE_SLEEP_SECONDS=2 \
  SMOKE_COMPOSE_UP_TIMEOUT_SECONDS=1 \
  run_smoke
bounded_status=$?
set -e

test "$bounded_status" -eq 124
assert_log_contains "down -v --remove-orphans --rmi local"
bounded_env_file=$(awk -F= '/^envfile=/{print $2; exit}' "$fake_log")
test -n "$bounded_env_file"
test ! -e "$bounded_env_file"

printf 'smoke script contract: ok\n'

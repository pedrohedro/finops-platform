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
  exit 23
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
assert_log_contains "down -v --remove-orphans"

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
assert_log_contains "down -v --remove-orphans"

printf 'smoke script contract: ok\n'

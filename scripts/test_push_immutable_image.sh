#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tmp_dir=$(mktemp -d)

cleanup() {
  find "$tmp_dir" -type f -delete 2>/dev/null || true
  find "$tmp_dir" -depth -type d -empty -delete 2>/dev/null || true
}
trap cleanup EXIT

fake_docker="$tmp_dir/docker"
fake_log="$tmp_dir/docker.log"
github_output="$tmp_dir/github-output"

cat >"$fake_docker" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail

: "${FAKE_DOCKER_LOG:?}"
printf '%s\n' "$*" >>"$FAKE_DOCKER_LOG"

case "$*" in
  "manifest inspect "*)
    case "${FAKE_MANIFEST_STATE:?}" in
      present)
        exit 0
        ;;
      absent)
        printf 'manifest unknown\n' >&2
        exit 1
        ;;
      absent-404)
        printf 'unexpected status code 404 Not Found\n' >&2
        exit 1
        ;;
      auth-error)
        printf 'unauthorized: authentication required\n' >&2
        exit 1
        ;;
      network-error)
        printf 'dial tcp: network is unreachable\n' >&2
        exit 1
        ;;
      rate-limit)
        printf 'toomanyrequests: rate limit exceeded\n' >&2
        exit 1
        ;;
    esac
    ;;
  "push "*)
    exit 0
    ;;
  "pull "*)
    case "${FAKE_PULL_STATE:-ok}" in
      ok)
        exit 0
        ;;
      auth-error)
        printf 'unauthorized: authentication required\n' >&2
        exit 1
        ;;
    esac
    ;;
  "buildx imagetools inspect "*)
    printf '%s\n' "${FAKE_REMOTE_DIGEST:?}"
    ;;
  "image inspect "*)
    printf '%s\n' "${FAKE_REMOTE_REVISION:?}"
    ;;
  *)
    printf 'unexpected docker invocation: %s\n' "$*" >&2
    exit 99
    ;;
esac
FAKE
chmod +x "$fake_docker"

image_name="ghcr.io/pedrohedro/finops-platform-api"
source_revision="0123456789abcdef0123456789abcdef01234567"
image_ref="${image_name}:${source_revision}"
expected_digest="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

run_publish() {
  : >"$fake_log"
  : >"$github_output"
  env \
    PATH="$tmp_dir:$PATH" \
    FAKE_DOCKER_LOG="$fake_log" \
    FAKE_MANIFEST_STATE="${FAKE_MANIFEST_STATE:?}" \
    FAKE_PULL_STATE="${FAKE_PULL_STATE:-ok}" \
    FAKE_REMOTE_DIGEST="${FAKE_REMOTE_DIGEST:?}" \
    FAKE_REMOTE_REVISION="${FAKE_REMOTE_REVISION:-$source_revision}" \
    GITHUB_OUTPUT="$github_output" \
    IMAGE_NAME="$image_name" \
    IMAGE_REF="$image_ref" \
    SOURCE_REVISION="$source_revision" \
    "$repo_root/scripts/push_immutable_image.sh"
}

FAKE_MANIFEST_STATE=absent \
  FAKE_REMOTE_DIGEST="$expected_digest" \
  run_publish
grep -Fx "digest_ref=${image_name}@${expected_digest}" "$github_output" >/dev/null
grep -F "manifest inspect $image_ref" "$fake_log" >/dev/null
grep -F "push $image_ref" "$fake_log" >/dev/null
grep -F "buildx imagetools inspect $image_ref" "$fake_log" >/dev/null
if grep -F "pull $image_ref" "$fake_log" >/dev/null; then
  exit 1
fi

FAKE_MANIFEST_STATE=absent-404 \
  FAKE_REMOTE_DIGEST="$expected_digest" \
  run_publish

for manifest_state in auth-error network-error rate-limit; do
  set +e
  FAKE_MANIFEST_STATE="$manifest_state" \
    FAKE_REMOTE_DIGEST="$expected_digest" \
    run_publish
  publish_status=$?
  set -e

  test "$publish_status" -ne 0
  if grep -F "push $image_ref" "$fake_log" >/dev/null; then
    exit 1
  fi
done

FAKE_MANIFEST_STATE=present \
  FAKE_REMOTE_DIGEST="$expected_digest" \
  run_publish
grep -Fx "digest_ref=${image_name}@${expected_digest}" "$github_output" >/dev/null
grep -F "pull $image_ref" "$fake_log" >/dev/null
grep -F "image inspect --format" "$fake_log" >/dev/null
if grep -F "push $image_ref" "$fake_log" >/dev/null; then
  exit 1
fi

set +e
FAKE_MANIFEST_STATE=present \
  FAKE_REMOTE_REVISION="ffffffffffffffffffffffffffffffffffffffff" \
  FAKE_REMOTE_DIGEST="$expected_digest" \
  run_publish
wrong_revision_status=$?
set -e

test "$wrong_revision_status" -ne 0
test ! -s "$github_output"
if grep -F "push $image_ref" "$fake_log" >/dev/null; then
  exit 1
fi

set +e
FAKE_MANIFEST_STATE=present \
  FAKE_PULL_STATE=auth-error \
  FAKE_REMOTE_DIGEST="$expected_digest" \
  run_publish
pull_error_status=$?
set -e

test "$pull_error_status" -ne 0
grep -F "pull $image_ref" "$fake_log" >/dev/null
test ! -s "$github_output"

set +e
FAKE_MANIFEST_STATE=absent \
  FAKE_REMOTE_DIGEST="sha256:not-a-digest" \
  run_publish
invalid_digest_status=$?
set -e

test "$invalid_digest_status" -ne 0
test ! -s "$github_output"

# A failed post-push digest step leaves the tag behind; a retry resumes safely.
FAKE_MANIFEST_STATE=present \
  FAKE_REMOTE_DIGEST="$expected_digest" \
  run_publish
grep -Fx "digest_ref=${image_name}@${expected_digest}" "$github_output" >/dev/null
if grep -F "push $image_ref" "$fake_log" >/dev/null; then
  exit 1
fi

printf 'immutable image publish contract: ok\n'

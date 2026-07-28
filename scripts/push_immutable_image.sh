#!/usr/bin/env bash
set -euo pipefail

: "${IMAGE_NAME:?}"
: "${IMAGE_REF:?}"
: "${GITHUB_OUTPUT:?}"

manifest_error=$(mktemp "${TMPDIR:-/tmp}/finops-manifest.XXXXXX")
cleanup() {
  rm -f "$manifest_error"
}
trap cleanup EXIT

inspect_status=0
if docker manifest inspect "$IMAGE_REF" >/dev/null 2>"$manifest_error"; then
  printf 'Refusing to overwrite existing image tag: %s\n' "$IMAGE_REF" >&2
  exit 1
else
  inspect_status=$?
fi

if ! grep -Eiq 'manifest unknown|(^|[^0-9])404([^0-9]|$)' "$manifest_error"; then
  cat "$manifest_error" >&2
  exit "$inspect_status"
fi

docker push "$IMAGE_REF"
remote_digest=$(
  docker buildx imagetools inspect "$IMAGE_REF" \
    --format '{{printf "%s" .Manifest.Digest}}'
)

if [[ ! "$remote_digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  printf 'Registry returned an invalid digest for %s\n' "$IMAGE_REF" >&2
  exit 1
fi

printf 'digest_ref=%s@%s\n' "$IMAGE_NAME" "$remote_digest" >>"$GITHUB_OUTPUT"

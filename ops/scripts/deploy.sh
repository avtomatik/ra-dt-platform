#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"
enter_project
validate_compose
# Images can be provisioned by the offline bundle; do not pull unconditionally.
mkdir -p data/exports logs
"$SCRIPT_DIR/verify-identity.sh"
compose run --rm --no-deps -T --entrypoint /bin/sh platform -ec '
  test -w /app/data && test -w /app/data/exports && test -w /app/logs
  test -r /app/config/certificate-folders.toml
' || die 'Check bind-mount ownership and certificate folder configuration.'
compose up -d --no-build
compose ps

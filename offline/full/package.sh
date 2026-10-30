#!/usr/bin/env bash
###############################################################################
# Create the full RADP offline ZIP from release/radp-offline-full.
###############################################################################
set -Eeuo pipefail
umask 077
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"
# shellcheck source=../lib/package-common.sh
source "$SCRIPT_DIR/../lib/package-common.sh"
radp_package_bundle "full" "$ROOT"

#!/usr/bin/env bash
###############################################################################
# Build a RADP offline runtime bundle without collecting or shipping OS DEBs.
###############################################################################
set -Eeuo pipefail
umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
LIB_DIR="$SCRIPT_DIR/../lib"
STAGE="$ROOT/release/radp-offline-partial"

###############################################################################
# These are the expected host-tool versions. The target administrator may
# supply different verified packages; install.sh then requires an explicit
# compatibility override rather than silently accepting version drift.
###############################################################################
EXPECTED_DOCKER_VERSION="${RADP_EXPECTED_DOCKER_VERSION:-25.0.5}"
EXPECTED_COMPOSE_VERSION="${RADP_EXPECTED_COMPOSE_VERSION:-1.29.2}"

# shellcheck source=../lib/common.sh
source "$LIB_DIR/common.sh"
# shellcheck source=../lib/prepare-runtime.sh
source "$LIB_DIR/prepare-runtime.sh"

fail_trap() {
  local rc=$?
  if ((rc != 0)); then
    printf '\nPARTIAL PREPARATION FAILED (exit %s, line %s).\n' "$rc" "${BASH_LINENO[0]:-unknown}" >&2
  fi
}
trap fail_trap EXIT

radp_require_root "$0"
radp_require_command docker
radp_require_command openssl
radp_require_command python3

mkdir -p "$ROOT/release"
[[ "$STAGE" == "$ROOT/release/radp-offline-partial" ]] || radp_die "Unexpected staging path; refusing to clean it."
rm -rf -- "$STAGE"
mkdir -p "$STAGE/data" "$STAGE/html"
radp_check_target_platform "$STAGE/build-os-release"
radp_verify_project_layout "$ROOT"

###############################################################################
# Deliberately no apt-get update, apt-get download, dpkg-scanpackages or .deb
# collection in this mode. Host Docker/Compose packages are supplied separately
# by the target administrator from their verified repository.
###############################################################################
radp_log "Preparing application images, runtime assets and encrypted environment (no DEBs)."
RADP_EXPECTED_DOCKER_VERSION="$EXPECTED_DOCKER_VERSION" \
RADP_EXPECTED_COMPOSE_VERSION="$EXPECTED_COMPOSE_VERSION" \
  radp_prepare_runtime_assets "$ROOT" "$STAGE" partial \
    "$SCRIPT_DIR/install.sh" "$LIB_DIR/install-common.sh"

###############################################################################
# Keep the requirement sheet in the bundle (runtime prep does not overwrite it).
###############################################################################
cat > "$STAGE/HOST-REQUIREMENTS.txt" <<EOF_HOST
Target OS: Astra Linux SE 1.7.8
Target architecture: amd64
Required executable: docker
Expected Docker CLI version: $EXPECTED_DOCKER_VERSION
Required Compose command: docker-compose (or docker compose plugin)
Expected Compose version: $EXPECTED_COMPOSE_VERSION
Required additional executable: openssl
Package versions previously used by the full bundle:
  docker.io=25.0.5.astra3+ci24
  docker-compose=1.29.2-1astra.se1+ci1+b2
The target administrator may provide other verified packages. If the resulting
CLI versions differ, first establish compatibility, then explicitly run:
  sudo env RADP_ALLOW_HOST_VERSION_VARIANCE=1 ./install.sh
EOF_HOST

printf '\nPARTIAL PREPARATION SUCCESS\n'
printf 'Staging: %s\n.deb packages: 0 (intentionally omitted)\nCompose images: %s\n' \
  "$STAGE" "$(wc -l < "$STAGE/compose-images.txt")"
printf 'Next: sudo %s/package.sh\n' "$SCRIPT_DIR"

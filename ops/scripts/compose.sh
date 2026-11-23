#!/usr/bin/env bash
# Single entrypoint for Compose v1/v2 using .env + .env.compose.
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"
[[ $# -gt 0 ]] || die 'Usage: ops/scripts/compose.sh COMPOSE_ARGS...'
[[ -d "$PROJECT_DIR" ]] || die "Project directory not found: $PROJECT_DIR"
cd "$PROJECT_DIR" || die "Cannot enter $PROJECT_DIR"
radp_config_activate "$PROJECT_DIR" || die 'Invalid deployment environment.'
resolve_compose
compose "$@"

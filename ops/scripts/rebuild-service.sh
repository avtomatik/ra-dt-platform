#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/../lib/common.sh"
usage() {
    cat <<EOF
Usage: $(basename "$0") SERVICE
Build and recreate one Docker Compose service.
Example:
  $(basename "$0") platform
  $(basename "$0") scheduler
EOF
}
[[ $# -eq 1 ]] || {
    usage
    exit 1
}
SERVICE="$1"
enter_project
validate_compose
log "Building service: $SERVICE"
compose build "$SERVICE"
log "Recreating service: $SERVICE"
compose up -d --no-deps --force-recreate "$SERVICE"
if [[ "$SERVICE" == "$APP_SERVICE" ]]; then
    wait_for_health
fi
log "Service status"
compose ps "$SERVICE"
log "Recent service logs"
compose logs --tail=50 "$SERVICE"

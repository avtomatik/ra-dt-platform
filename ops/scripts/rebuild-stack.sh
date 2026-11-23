#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/../lib/common.sh"
NO_CACHE=false
FOLLOW_LOGS=false
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]
Rebuild and redeploy the complete RADP stack.
Options:
  --no-cache   Rebuild images without Docker build cache
  --follow     Follow application logs after deployment
  -h, --help   Show this help
EOF
}
while (($#)); do
    case "$1" in
    --no-cache)
        NO_CACHE=true
        ;;
    --follow)
        FOLLOW_LOGS=true
        ;;
    -h | --help)
        usage
        exit 0
        ;;
    *)
        die "Unknown option: $1"
        ;;
    esac
    shift
done
enter_project
validate_compose
log "Stopping is not required; existing volumes will be preserved."
log "Building RADP images..."
if [[ "$NO_CACHE" == true ]]; then
    compose build --no-cache
else
    compose build
fi
log "Redeploying complete stack..."
compose up -d --force-recreate
wait_for_health
show_services
if [[ "$FOLLOW_LOGS" == true ]]; then
    compose logs -f
else
    log "Recent application logs:"
    compose logs --tail=50
fi

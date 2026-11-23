#!/usr/bin/env bash
set -Eeuo pipefail
###############################################################################
# Resolve operational and application directories.
###############################################################################
OPS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
PROJECT_DIR="${RADP_PROJECT_DIR:-$(cd -- "$OPS_DIR/.." && pwd -P)}"
# shellcheck source=deployment-env.sh
source "$OPS_DIR/lib/deployment-env.sh"
###############################################################################
# Project configuration.
###############################################################################
APP_SERVICE="${RADP_APP_SERVICE:-platform}"
APP_URL="${RADP_APP_URL:-http://127.0.0.1:9000}"
APP_URL="${APP_URL%/}"
HEALTH_URL="${RADP_HEALTH_URL:-${APP_URL}/health}"
###############################################################################
# Docker Compose compatibility (resolved only when an operation needs Docker).
# In particular, --help must work without Docker being installed.
###############################################################################
COMPOSE=()
resolve_compose() {
    if docker compose version >/dev/null 2>&1; then
        COMPOSE=(docker compose)
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE=(docker-compose)
    else
        die "Docker Compose is not installed."
    fi
}
log() {
    printf '\n>>> %s\n' "$*"
}
die() {
    printf '\nERROR: %s\n' "$*" >&2
    exit 1
}
pause() {
    [[ -t 0 ]] || return 0
    read -r -p ">>> Press Enter to continue..."
}
require_command() {
    command -v "$1" >/dev/null 2>&1 ||
        die "Required command not found: $1"
}
enter_project() {
    [[ -d "$PROJECT_DIR" ]] ||
        die "Project directory does not exist: $PROJECT_DIR"
    cd "$PROJECT_DIR"
    [[ -f docker-compose.yml || -f compose.yml || -f compose.yaml ]] ||
        die "Docker Compose configuration not found in $PROJECT_DIR"
    radp_config_activate "$PROJECT_DIR" || die "Cannot load deployment configuration."
    resolve_compose
    docker info >/dev/null 2>&1 ||
        die "Docker daemon is unavailable."
}
compose() {
    if ((${#COMPOSE[@]} == 0)); then
        resolve_compose
    fi
    "${COMPOSE[@]}" "${RADP_COMPOSE_FILES[@]}" "$@"
}
validate_compose() {
    log "Validating Docker Compose configuration..."
    compose config -q
}
show_services() {
    log "Docker services:"
    compose ps
}
wait_for_health() {
    local attempts="${1:-30}"
    local interval="${2:-2}"
    require_command curl
    log "Waiting for application health check..."
    for ((i = 1; i <= attempts; i++)); do
        if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
            log "Application is healthy."
            return 0
        fi
        sleep "$interval"
    done
    compose ps
    compose logs --tail=50 "$APP_SERVICE" || true
    die "Application did not become healthy."
}
open_url() {
    local url="$1"
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$url" >/dev/null 2>&1 &
    else
        log "Open this URL manually: $url"
    fi
}

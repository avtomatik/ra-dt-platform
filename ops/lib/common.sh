#!/usr/bin/env bash
set -Eeuo pipefail
###############################################################################
# Resolve operational and application directories.
###############################################################################
OPS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="${RADP_PROJECT_DIR:-$(cd -- "$OPS_DIR/.." && pwd)}"
###############################################################################
# Project configuration.
###############################################################################
APP_SERVICE="${RADP_APP_SERVICE:-platform}"
HEALTH_URL="${RADP_HEALTH_URL:-http://127.0.0.1:8000/health}"
###############################################################################
# Resolve the directory containing the calling script.
###############################################################################
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[1]}")/.." && pwd)"
###############################################################################
# Docker Compose compatibility.
###############################################################################
if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose)
else
    echo "ERROR: Docker Compose is not installed." >&2
    exit 1
fi
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
    docker info >/dev/null 2>&1 ||
        die "Docker daemon is unavailable."
}
compose() {
    "${COMPOSE[@]}" "$@"
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

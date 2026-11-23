#!/usr/bin/env bash
set -Eeuo pipefail
###############################################################################
# Resolve operational and application directories.
###############################################################################
OPS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
PROJECT_DIR="${RADP_PROJECT_DIR:-$(cd -- "$OPS_DIR/.." && pwd -P)}"
###############################################################################
# Project configuration.
###############################################################################
APP_SERVICE="${RADP_APP_SERVICE:-platform}"
APP_URL="${RADP_APP_URL:-http://127.0.0.1:9000}"
APP_URL="${APP_URL%/}"
HEALTH_URL="${RADP_HEALTH_URL:-${APP_URL}/health}"
SHOW_LOGS=false
LOG_TAIL=30
FAILURES=0
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]
Read-only operational diagnostics for RADP.
Options:
  --logs       Display recent application logs
  -h, --help   Show this help
Environment overrides:
  RADP_PROJECT_DIR
  RADP_APP_SERVICE
  RADP_HEALTH_URL
  RADP_APP_URL
EOF
}
ok() {
    printf '[ OK ] %s\n' "$*"
}
fail() {
    printf '[FAIL] %s\n' "$*" >&2
    FAILURES=$((FAILURES + 1))
}
info() {
    printf '[INFO] %s\n' "$*"
}
while (($#)); do
    case "$1" in
    --logs)
        SHOW_LOGS=true
        ;;
    -h | --help)
        usage
        exit 0
        ;;
    *)
        printf 'Unknown option: %s\n' "$1" >&2
        usage
        exit 2
        ;;
    esac
    shift
done
echo "##############################################"
echo "       RADP Operational Status"
echo "##############################################"
###############################################################################
# 1. Host information
###############################################################################
echo
echo "HOST"
printf 'Hostname: %s\n' "$(hostname)"
printf 'Date:     %s\n' "$(date)"
if command -v hostname >/dev/null 2>&1; then
    printf 'IP:       %s\n' "$(hostname -I 2>/dev/null | awk '{print $1}')"
fi
###############################################################################
# 2. Project installation
###############################################################################
echo
echo "INSTALLATION"
if [[ ! -d "$PROJECT_DIR" ]]; then
    fail "Project directory not found: $PROJECT_DIR"
    exit 2
fi
cd "$PROJECT_DIR" || exit 2
ok "Project directory: $PROJECT_DIR"
# shellcheck source=../lib/deployment-env.sh
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../lib" && pwd -P)/deployment-env.sh"
if radp_config_activate "$PROJECT_DIR"; then
    ok "Loaded .env and .env.compose for ${DEPLOY_ENVIRONMENT:-test}."
else
    fail "Could not load .env and .env.compose."
    exit 2
fi
COMPOSE_FILE=""
for candidate in docker-compose.yml compose.yml compose.yaml; do
    if [[ -f "$candidate" ]]; then
        COMPOSE_FILE="$candidate"
        break
    fi
done
if [[ -z "$COMPOSE_FILE" ]]; then
    fail "Docker Compose configuration not found."
    exit 2
fi
ok "Compose configuration: $COMPOSE_FILE"
if [[ -f .env ]]; then
    ok "Environment file exists."
else
    info "No .env file found. Compose may use externally supplied environment variables."
fi
###############################################################################
# 3. Docker and Docker Compose
###############################################################################
echo
echo "DOCKER"
if ! command -v docker >/dev/null 2>&1; then
    fail "Docker CLI is not installed."
    exit 2
fi
docker --version
if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose)
    ok "Docker Compose v2 is available."
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose)
    ok "Legacy docker-compose is available."
else
    fail "Docker Compose is not available."
    exit 2
fi
###############################################################################
# 4. Docker daemon
###############################################################################
echo
echo "DOCKER DAEMON"
DAEMON_AVAILABLE=false
if docker info >/dev/null 2>&1; then
    ok "Docker daemon is accessible."
    DAEMON_AVAILABLE=true
else
    fail "Docker daemon unavailable or insufficient permissions."
fi
###############################################################################
# 5. Compose configuration validation
###############################################################################
echo
echo "COMPOSE CONFIGURATION"
if "${COMPOSE[@]}" "${RADP_COMPOSE_FILES[@]}" config -q; then
    ok "Compose configuration is valid."
else
    fail "Compose configuration validation failed."
fi
###############################################################################
# 6. Container status
###############################################################################
echo
echo "CONTAINER STATUS"
if [[ "$DAEMON_AVAILABLE" == true ]]; then
    if "${COMPOSE[@]}" "${RADP_COMPOSE_FILES[@]}" ps -a; then
        ok "Container status retrieved."
    else
        fail "Unable to retrieve container status."
    fi
else
    info "Skipped: Docker daemon is unavailable."
fi
###############################################################################
# 7. Application health
###############################################################################
echo
echo "APPLICATION HEALTH"
if ! command -v curl >/dev/null 2>&1; then
    fail "curl is not installed; health check skipped."
else
    HTTP_CODE=""
    if HTTP_CODE="$(
        curl \
            --silent \
            --show-error \
            --output /dev/null \
            --write-out '%{http_code}' \
            --connect-timeout 3 \
            --max-time 8 \
            "$HEALTH_URL" 2>/dev/null
    )" && [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
        ok "Application responded with HTTP $HTTP_CODE."
        info "Health endpoint: $HEALTH_URL"
    else
        fail "Application health check failed (HTTP ${HTTP_CODE:-no response})."
        info "Health endpoint: $HEALTH_URL"
    fi
fi
###############################################################################
# 8. Optional application logs
###############################################################################
if [[ "$SHOW_LOGS" == true ]]; then
    echo
    echo "APPLICATION LOGS"
    if [[ "$DAEMON_AVAILABLE" == true ]]; then
        "${COMPOSE[@]}" "${RADP_COMPOSE_FILES[@]}" logs --tail="$LOG_TAIL" "$APP_SERVICE" ||
            fail "Unable to retrieve application logs."
    else
        info "Skipped: Docker daemon is unavailable."
    fi
fi
###############################################################################
# 9. Final summary
###############################################################################
echo
echo "##############################################"
echo "             STATUS SUMMARY"
echo "##############################################"
if ((FAILURES == 0)); then
    ok "All critical checks passed."
    echo
    echo "RADP appears operational."
    exit 0
else
    fail "$FAILURES check(s) failed."
    echo
    echo "RADP requires investigation."
    echo
    echo "Suggested next command:"
    echo "  ./ops/scripts/status.sh --logs"
    exit 1
fi

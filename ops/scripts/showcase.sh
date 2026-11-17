#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
SYNC=false
OPEN_BROWSER=true
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]
Ensure RADP is running and ready for demonstration.
Options:
  --sync       Synchronize certificates after health check
  --no-open    Do not open browser interfaces
  -h, --help   Show this help
EOF
}
while (($#)); do
    case "$1" in
        --sync)
            SYNC=true
            ;;
        --no-open)
            OPEN_BROWSER=false
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
    shift
done
echo "##############################################"
echo "       Registry Authority Data Platform"
echo "                 RADP Showcase"
echo "##############################################"
log "Host information"
printf "Hostname: "
hostname
printf "IP: "
hostname -I 2>/dev/null | awk '{print $1}' || true
printf "Project: %s\n" "$PROJECT_DIR"
pause
enter_project
validate_compose
show_services
pause
log "Ensuring RADP is built and running..."
###############################################################################
# Docker Compose builds missing or changed images and starts
# missing containers without unnecessarily recreating healthy ones.
###############################################################################
compose up -d --build
wait_for_health
pause
log "Recent application logs"
compose logs --tail=20
pause
if [[ "$SYNC" == true ]]; then
    log "Synchronizing certificates..."
    curl -fsS \
        -X POST \
        http://127.0.0.1:8000/admin/certificates/sync
    echo
    log "Certificate synchronization completed."
else
    log "Certificate synchronization skipped."
    echo "Use --sync to request synchronization."
fi
pause
if [[ "$OPEN_BROWSER" == true ]]; then
    log "Opening RADP interfaces..."
    open_url "http://127.0.0.1:8000/web"
    pause
    open_url "http://127.0.0.1:8000/export/preview"
    pause
    open_url "http://127.0.0.1:8000/export/certificates"
    pause
fi
echo
echo "##############################################"
echo "             RADP Showcase Ready"
echo "##############################################"
echo
echo "Application: http://127.0.0.1:8000"
echo "Web UI:      http://127.0.0.1:8000/web"
echo "Preview:     http://127.0.0.1:8000/export/preview"
echo "Inventory:   http://127.0.0.1:8000/export/certificates"
echo
echo "Expected download:"
echo "  certificates_inventory_YYYY-MM-DD-HH-MM.xlsx"
echo
echo "Check:"
echo "  ~/Downloads"
echo "##############################################"

#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/../lib/common.sh"
ENV_FILE=".env"
CONFIG_KEY="RADP_TRANSPORT__CERT_THUMBPRINT"
usage() {
    cat <<EOF
Usage: $(basename "$0") THUMBPRINT [SERVICE]
Update the RADP client certificate thumbprint and redeploy
the affected Docker Compose service.
Arguments:
  THUMBPRINT   Hexadecimal certificate thumbprint
  SERVICE      Docker Compose service (default: platform)
Example:
  $(basename "$0") 00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff
  $(basename "$0") 00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff platform
EOF
}
[[ $# -ge 1 && $# -le 2 ]] || {
    usage
    exit 1
}
THUMBPRINT="$1"
SERVICE="${2:-$APP_SERVICE}"
[[ "$THUMBPRINT" =~ ^[[:xdigit:]]+$ ]] ||
    die "Thumbprint must contain hexadecimal characters only."
enter_project
[[ -f "$ENV_FILE" ]] ||
    die "Environment file not found: $ENV_FILE"
log "Updating certificate thumbprint..."
###############################################################################
# Update the existing key, preserving the rest of .env.
# If the key does not exist, append it.
###############################################################################
python3 - "$ENV_FILE" "$CONFIG_KEY" "$THUMBPRINT" <<'PY'
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

env_file = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
content = env_file.read_text(encoding="utf-8")
pattern = re.compile(
    rf"^{re.escape(key)}=.*$",
    re.MULTILINE,
)
replacement = f"{key}={value}"
if pattern.search(content):
    content = pattern.sub(replacement, content)
else:
    if content and not content.endswith("\n"):
        content += "\n"
    content += replacement + "\n"
original_mode = stat.S_IMODE(env_file.stat().st_mode)
fd, temporary_path = tempfile.mkstemp(
    dir=env_file.parent,
    prefix=".env.",
    suffix=".tmp",
    text=True,
)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(content)
    os.chmod(temporary_path, original_mode)
    os.replace(temporary_path, env_file)
except BaseException:
    try:
        os.unlink(temporary_path)
    except FileNotFoundError:
        pass
    raise
PY
log "Thumbprint updated successfully."
validate_compose
log "Building service: $SERVICE"
compose build "$SERVICE"
log "Recreating service: $SERVICE"
compose up -d --no-deps --force-recreate "$SERVICE"
if [[ "$SERVICE" == "$APP_SERVICE" ]]; then
    wait_for_health
fi
log "Deployment complete."
compose ps "$SERVICE"

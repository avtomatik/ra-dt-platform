#!/usr/bin/env bash
# Run on the connected Astra builder after prepare.sh succeeds.
set -Eeuo pipefail
umask 077
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
BUNDLE="$ROOT/release/radp-offline"
ZIP="$ROOT/release/radp-offline.zip"
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
trap 'rc=$?; if ((rc != 0)); then printf "PACKAGE FAILED (exit %s, line %s).\n" "$rc" "$LINENO" >&2; fi' EXIT

[[ -d "$BUNDLE" ]] || fail "Missing $BUNDLE; run ./offline/prepare.sh first."
for f in images.tar docker-compose.yml .env.enc build-os-release base-packages.tsv install.sh target-platform.txt; do
  [[ -f "$BUNDLE/$f" ]] || fail "Bundle component missing: $f"
done
[[ -d "$BUNDLE/docker-install/debs" ]] || fail "Missing local OS package directory."
shopt -s nullglob
packages=("$BUNDLE/docker-install/debs"/*.deb)
((${#packages[@]} > 0)) || fail "No .deb packages were collected."
[[ ! -e "$BUNDLE/.env" ]] || fail "Plaintext .env exists in bundle staging; remove it and rerun preparation."
command -v sha256sum >/dev/null || fail "sha256sum is required."
command -v python3 >/dev/null || fail "python3 is required."

cd "$BUNDLE"
rm -f SHA256SUMS
find . -type f ! -name SHA256SUMS ! -name .env -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
sha256sum -c SHA256SUMS >/dev/null

mkdir -p "$ROOT/release"
rm -f "$ZIP"
python3 - "$BUNDLE" "$ZIP" <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile
import sys
root = Path(sys.argv[1]).resolve()
archive = Path(sys.argv[2]).resolve()
with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root.parent)
        # TAR and .deb files are already compressed; storing them avoids wasteful CPU.
        method = ZIP_STORED if p.suffix in {".tar", ".deb"} else ZIP_DEFLATED
        zf.write(p, rel.as_posix(), compress_type=method)
with ZipFile(archive, "r") as zf:
    names = zf.namelist()
    if any(Path(n).name == ".env" for n in names):
        raise SystemExit("ERROR: ZIP contains a plaintext .env entry")
    if not any(Path(n).name == ".env.enc" for n in names):
        raise SystemExit("ERROR: ZIP lacks encrypted .env.enc")
    bad = zf.testzip()
    if bad:
        raise SystemExit(f"ERROR: ZIP CRC check failed for {bad}")
PY
chmod 0600 "$ZIP"
# When invoked through sudo, make only the ZIP readable by the invoking user.
# The staging directory and encrypted config remain root-restricted.
if [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != root ]]; then
  user_group="$(id -gn "$SUDO_USER")"
  chown "$SUDO_USER:$user_group" "$ZIP"
fi
printf '\nPACKAGE SUCCESS\n'
printf 'ZIP: %s\n' "$ZIP"
printf 'Size: %s bytes\n' "$(stat -c '%s' "$ZIP")"
printf 'ZIP SHA-256: '
sha256sum "$ZIP"
printf 'Checksums inside ZIP: verified\n'
printf 'Plaintext .env inside ZIP: NO\n'
printf 'OFFLINE TEST REQUIRED: extract and install on a clean matching Astra VM with its virtual NIC disconnected.\n'

#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
STAGE="$ROOT/release/radp-offline"
ZIP="$ROOT/release/radp-offline.zip"
fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
trap 'rc=$?; if ((rc != 0)); then printf "\nPACKAGE FAILED (exit %s, line %s).\n" "$rc" "$LINENO" >&2; fi' EXIT
[[ -d "$STAGE" ]] || fail "Missing $STAGE; run prepare.sh first."
for f in images.tar docker-compose.yml .env.enc install.sh target-platform.txt compose-images.txt; do
  [[ -s "$STAGE/$f" ]] || fail "Missing/empty required file: $f"
done
[[ "$(cat "$STAGE/target-platform.txt")" == linux/amd64 ]] || fail "Wrong target platform."
[[ ! -e "$STAGE/.env" ]] || fail "Plaintext .env exists in staging; refusing to package."
[[ -d "$STAGE/docker-install/debs" ]] || fail "Missing .deb directory."
compgen -G "$STAGE/docker-install/debs/*.deb" >/dev/null || fail "No .deb packages collected."
command -v python3 >/dev/null || fail "python3 is required for ZIP creation."
cd "$STAGE"
rm -f SHA256SUMS
find . -type f ! -name SHA256SUMS ! -name .env -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
sha256sum -c SHA256SUMS
mkdir -p "$ROOT/release"
rm -f "$ZIP"
python3 - "$STAGE" "$ZIP" <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile
import sys
root, archive = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=5, allowZip64=True) as z:
    for p in sorted(root.rglob("*")):
        if p.is_file():
            z.write(p, p.relative_to(root.parent).as_posix(),
                    compress_type=ZIP_STORED if p.suffix in {".tar", ".deb"} else ZIP_DEFLATED)
with ZipFile(archive) as z:
    names = z.namelist()
    if any(Path(n).name == ".env" for n in names):
        raise SystemExit("ERROR: plaintext .env found in ZIP")
    if not any(Path(n).name == ".env.enc" for n in names):
        raise SystemExit("ERROR: .env.enc missing")
    bad = z.testzip()
    if bad:
        raise SystemExit(f"ERROR: ZIP CRC failure: {bad}")
PY
chmod 0600 "$ZIP"
if [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != root ]]; then
  chown "$SUDO_USER:$(id -gn "$SUDO_USER")" "$ZIP"
fi
printf '\nPACKAGE SUCCESS\nZIP: %s\nSize: %s bytes\nSHA-256: ' "$ZIP" "$(stat -c '%s' "$ZIP")"
sha256sum "$ZIP"
printf 'Plaintext .env in ZIP: NO\n'
printf 'Now test this ZIP on a clean Astra Linux SE 1.7.8 amd64 VM with its network adapter disconnected.\n'

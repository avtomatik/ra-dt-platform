#!/usr/bin/env bash
###############################################################################
# Shared archive builder. Called by full/package.sh or partial/package.sh.
###############################################################################

radp_package_bundle() {
  local mode="$1" root="$2" stage zip_file
  local -a required=()
  stage="$root/release/radp-offline-$mode"
  zip_file="$root/release/radp-offline-$mode.zip"

  [[ -d "$stage" ]] || radp_die "Missing staging directory: $stage. Run $mode/prepare.sh first."
  required=(images.tar docker-compose.yml .env.enc .env.sha256 install.sh install-common.sh \
    target-platform.txt compose-images.txt image-manifest.tsv runtime-requirements.txt bundle-mode.txt)
  if [[ "$mode" == "full" ]]; then
    required+=(os-packages.txt docker-install/package-inventory.tsv docker-install/frozen-sources.list)
    [[ -s "$stage/docker-install/debs/Packages" ]] || radp_die "Full bundle is missing docker-install/debs/Packages."
    [[ -s "$stage/docker-install/debs/Packages.gz" ]] || radp_die "Full bundle is missing docker-install/debs/Packages.gz."
    [[ -s "$stage/docker-install/debs/Release" ]] || radp_die "Full bundle is missing docker-install/debs/Release."
    compgen -G "$stage/docker-install/debs/*.deb" >/dev/null || radp_die "Full bundle contains no .deb archives."
  else
    required+=(HOST-REQUIREMENTS.txt)
    [[ ! -d "$stage/docker-install" ]] || radp_die "Partial bundle must not contain docker-install/."
    if find "$stage" -type f -name '*.deb' -print -quit | grep -q .; then
      radp_die "Partial bundle unexpectedly contains .deb files."
    fi
  fi

  local file
  for file in "${required[@]}"; do
    [[ -s "$stage/$file" ]] || radp_die "Required bundle file missing or empty: $file"
  done

  [[ "$(head -n 1 "$stage/bundle-mode.txt")" == "mode=$mode" ]] || radp_die "Bundle mode manifest does not match $mode."
  grep -q '^linux/amd64$' "$stage/target-platform.txt" || radp_die "Wrong target platform."
  [[ ! -e "$stage/.env" ]] || radp_die "Plaintext .env exists in staging; refusing to package."
  if find "$stage" -type l -print -quit | grep -q .; then
    radp_die "Staging contains symbolic links. Resolve them before packaging."
  fi

  radp_require_command sha256sum
  radp_require_command python3
  mkdir -p "$root/release"
  radp_log "Generating SHA-256 checksums for the $mode bundle."
  (
    cd "$stage"
    rm -f SHA256SUMS
    LC_ALL=C find . -type f ! -name SHA256SUMS -print0 \
      | LC_ALL=C sort -z \
      | xargs -0 sha256sum > SHA256SUMS
    sha256sum -c SHA256SUMS
  )

  rm -f -- "$zip_file"
  python3 - "$stage" "$zip_file" "$mode" <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo
import sys

stage = Path(sys.argv[1]).resolve()
archive = Path(sys.argv[2]).resolve()
mode = sys.argv[3]
prefix = f"radp-offline-{mode}"

with ZipFile(archive, "w", allowZip64=True) as zf:
    for path in sorted((p for p in stage.rglob("*") if p.is_file()), key=lambda p: p.relative_to(stage).as_posix()):
        relative = path.relative_to(stage).as_posix()
        name = f"{prefix}/{relative}"
        info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.create_system = 3
        if path.name in {".env.enc", ".env.sha256"}:
            permissions = 0o100600
        elif path.suffix == ".sh":
            permissions = 0o100755
        else:
            permissions = 0o100644
        info.external_attr = permissions << 16
        info.compress_type = ZIP_STORED if path.suffix in {".tar", ".deb"} else ZIP_DEFLATED
        info.flag_bits |= 0x800
        zf.writestr(info, path.read_bytes(), compress_type=info.compress_type, compresslevel=6)

with ZipFile(archive, "r") as zf:
    names = zf.namelist()
    if any(Path(name).name == ".env" for name in names):
        raise SystemExit("ERROR: plaintext .env found in ZIP")
    if f"{prefix}/.env.enc" not in names:
        raise SystemExit("ERROR: encrypted .env is missing")
    corrupt = zf.testzip()
    if corrupt:
        raise SystemExit(f"ERROR: ZIP CRC failure: {corrupt}")
PY
  chmod 0600 "$zip_file"
  if [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]]; then
    chown "$SUDO_USER:$(id -gn "$SUDO_USER")" "$zip_file"
  fi

  printf '\n%s PACKAGE SUCCESS\nZIP: %s\nSize: %s bytes\nSHA-256: ' \
    "${mode^^}" "$zip_file" "$(stat -c '%s' "$zip_file")"
  sha256sum "$zip_file"
  printf 'Plaintext .env in ZIP: NO\n'
  if [[ "$mode" == "partial" ]]; then
    printf 'DEB archives in bundle: 0 (intentionally omitted)\n'
  else
    printf 'DEB archives in bundle: %s\n' "$(find "$stage/docker-install/debs" -maxdepth 1 -name '*.deb' -type f | wc -l)"
  fi
}

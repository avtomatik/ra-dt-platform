#!/usr/bin/env bash
###############################################################################
# Shared archive builder. Called by full/package.sh or partial/package.sh.
###############################################################################

radp_package_bundle() {
  local mode="$1" root="$2" stage zip_file checksum_file
  local -a required=()
  stage="$root/release/radp-offline-$mode"
  zip_file="$root/release/radp-offline-$mode.zip"
  checksum_file="$zip_file.sha256"

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

  python3 "$root/offline/lib/verify-image-archive.py" \
    "$stage/images.tar" "$stage/compose-images.txt" "$stage/image-manifest.tsv" \
    || radp_die "Compose image references do not match the exported images.tar manifest."

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

  rm -f -- "$zip_file" "$checksum_file"
  python3 - "$stage" "$zip_file" "$mode" <<'PY'
from hashlib import sha256
from pathlib import Path, PurePosixPath
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

required_common = {
    "images.tar", "docker-compose.yml", ".env.enc", ".env.sha256", "install.sh",
    "install-common.sh", "target-platform.txt", "compose-images.txt", "image-manifest.tsv",
    "runtime-requirements.txt", "bundle-mode.txt", "SHA256SUMS",
}
required_by_mode = {
    "full": {
        "os-packages.txt", "docker-install/package-inventory.tsv",
        "docker-install/frozen-sources.list", "docker-install/debs/Packages",
        "docker-install/debs/Packages.gz", "docker-install/debs/Release",
    },
    "partial": {"HOST-REQUIREMENTS.txt"},
}
if mode not in required_by_mode:
    raise SystemExit(f"ERROR: unsupported bundle mode: {mode}")

with ZipFile(archive, "r") as zf:
    infos = zf.infolist()
    names = [info.filename for info in infos]
    if len(names) != len(set(names)):
        raise SystemExit("ERROR: ZIP contains duplicate file names")
    if any(not name.startswith(prefix + "/") for name in names):
        raise SystemExit("ERROR: ZIP contains a path outside its bundle root")
    if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names):
        raise SystemExit("ERROR: ZIP contains an unsafe path")
    if any(PurePosixPath(name).name == ".env" for name in names):
        raise SystemExit("ERROR: plaintext .env found in ZIP")

    relative_names = {name[len(prefix) + 1:] for name in names}
    missing = sorted((required_common | required_by_mode[mode]) - relative_names)
    if missing:
        raise SystemExit("ERROR: ZIP is missing required content: " + ", ".join(missing))
    if mode == "full":
        if not any(name.startswith(prefix + "/docker-install/debs/") and name.endswith(".deb") for name in names):
            raise SystemExit("ERROR: FULL ZIP contains no DEB archives")
    else:
        if any(name.endswith(".deb") for name in names):
            raise SystemExit("ERROR: PARTIAL ZIP contains a DEB archive")
        if any(name.startswith(prefix + "/docker-install/") for name in names):
            raise SystemExit("ERROR: PARTIAL ZIP contains docker-install package assets")
        if prefix + "/os-packages.txt" in names:
            raise SystemExit("ERROR: PARTIAL ZIP contains os-packages.txt")

    for required_executable in (f"{prefix}/install.sh", f"{prefix}/install-common.sh"):
        info = zf.getinfo(required_executable)
        permissions = (info.external_attr >> 16) & 0o777
        if not permissions & 0o111:
            raise SystemExit(f"ERROR: executable permission missing from {required_executable}")
    for secret_file in (f"{prefix}/.env.enc", f"{prefix}/.env.sha256"):
        info = zf.getinfo(secret_file)
        permissions = (info.external_attr >> 16) & 0o777
        if permissions & 0o077:
            raise SystemExit(f"ERROR: {secret_file} permissions are broader than 0600")

    checksum_member = f"{prefix}/SHA256SUMS"
    try:
        checksum_lines = zf.read(checksum_member).decode("utf-8").splitlines()
    except (KeyError, UnicodeDecodeError) as exc:
        raise SystemExit(f"ERROR: cannot read bundled SHA256SUMS: {exc}")

    checked = set()
    for line in checksum_lines:
        if len(line) < 67 or line[64:66] != "  ":
            raise SystemExit(f"ERROR: malformed SHA256SUMS line: {line!r}")
        digest, relative = line[:64], line[66:]
        if relative.startswith("./"):
            relative = relative[2:]
        member = f"{prefix}/{relative}"
        if member not in names:
            raise SystemExit(f"ERROR: SHA256SUMS references a missing file: {relative}")
        if relative in checked:
            raise SystemExit(f"ERROR: duplicate SHA256SUMS entry: {relative}")
        actual = sha256(zf.read(member)).hexdigest()
        if actual != digest:
            raise SystemExit(f"ERROR: checksum mismatch inside ZIP: {relative}")
        checked.add(relative)

    expected_checked = relative_names - {"SHA256SUMS"}
    if checked != expected_checked:
        missing_checksums = sorted(expected_checked - checked)
        extra_checksums = sorted(checked - expected_checked)
        raise SystemExit(
            "ERROR: SHA256SUMS does not cover every packaged file "
            f"(missing={missing_checksums}, extra={extra_checksums})"
        )

    corrupt = zf.testzip()
    if corrupt:
        raise SystemExit(f"ERROR: ZIP CRC failure: {corrupt}")

print(f"Verified {len(names)} ZIP entries, required contents, permissions and SHA-256 manifest")
PY
  chmod 0600 "$zip_file"
  (
    cd "$root/release"
    sha256sum "$(basename "$zip_file")" > "$(basename "$checksum_file")"
    sha256sum -c "$(basename "$checksum_file")"
  )
  chmod 0600 "$checksum_file"
  if [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]]; then
    chown "$SUDO_USER:$(id -gn "$SUDO_USER")" "$zip_file" "$checksum_file"
  fi

  printf '\n%s PACKAGE SUCCESS\nZIP: %s\nZIP checksum: %s\nSize: %s bytes\nSHA-256: ' \
    "${mode^^}" "$zip_file" "$checksum_file" "$(stat -c '%s' "$zip_file")"
  sha256sum "$zip_file"
  printf 'Plaintext .env in ZIP: NO\n'
  if [[ "$mode" == "partial" ]]; then
    printf 'DEB archives in bundle: 0 (intentionally omitted)\n'
  else
    printf 'DEB archives in bundle: %s\n' "$(find "$stage/docker-install/debs" -maxdepth 1 -name '*.deb' -type f | wc -l)"
  fi
}

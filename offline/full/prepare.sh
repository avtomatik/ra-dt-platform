#!/usr/bin/env bash
###############################################################################
# Build a self-contained RADP offline bundle, including Docker/Compose DEBs.
###############################################################################
set -Eeuo pipefail
umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
LIB_DIR="$SCRIPT_DIR/../lib"
STAGE="$ROOT/release/radp-offline-full"
DEBS="$STAGE/docker-install/debs"

###############################################################################
# Frozen Astra Linux SE 1.7.8 package versions previously selected for RADP.
###############################################################################
ENGINE_PKG="docker.io"
ENGINE_VER="${RADP_DOCKER_PACKAGE_VERSION:-25.0.5.astra3+ci24}"
COMPOSE_PKG="docker-compose"
COMPOSE_VER="${RADP_COMPOSE_PACKAGE_VERSION:-1.29.2-1astra.se1+ci1+b2}"
FROZEN_LIST="${RADP_FROZEN_LIST:-/tmp/radp-astra-frozen-1.7.8.list}"
APT_LISTS="${RADP_APT_LISTS:-/tmp/radp-astra-frozen-lists}"

# shellcheck source=../lib/common.sh
source "$LIB_DIR/common.sh"
# shellcheck source=../lib/prepare-runtime.sh
source "$LIB_DIR/prepare-runtime.sh"

fail_trap() {
  local rc=$?
  if ((rc != 0)); then
    printf '\nFULL PREPARATION FAILED (exit %s, line %s).\n' "$rc" "${BASH_LINENO[0]:-unknown}" >&2
  fi
}
trap fail_trap EXIT

radp_require_root "$0"
radp_require_command apt-get
radp_require_command apt-cache
radp_require_command dpkg-deb
radp_require_command sed
radp_require_command python3
radp_require_command docker
radp_require_command openssl

mkdir -p "$ROOT/release"
[[ "$STAGE" == "$ROOT/release/radp-offline-full" ]] || radp_die "Unexpected staging path; refusing to clean it."
rm -rf -- "$STAGE"
mkdir -p "$DEBS" "$STAGE/data" "$STAGE/html"
radp_check_target_platform "$STAGE/build-os-release"

radp_verify_project_layout "$ROOT"

if [[ ! -s "$FROZEN_LIST" ]]; then
  cat > "$FROZEN_LIST" <<'REPOS'
deb https://dl.astralinux.ru/astra/frozen/1.7_x86-64/1.7.8/repository-base/ 1.7_x86-64 main contrib non-free
deb https://dl.astralinux.ru/astra/frozen/1.7_x86-64/1.7.8/repository-update/ 1.7_x86-64 main contrib non-free
REPOS
fi

mapfile -t active_sources < <(sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$FROZEN_LIST" | grep -v '^#' | grep -v '^$' || true)
((${#active_sources[@]} == 2)) || radp_die "The frozen APT list must contain exactly the Astra 1.7.8 base and update repositories."
base_source_count=0
update_source_count=0
for source_line in "${active_sources[@]}"; do
  [[ "$source_line" =~ ^deb[[:space:]]+https://dl\.astralinux\.ru/astra/frozen/1\.7_x86-64/1\.7\.8/repository-(base|update)/[[:space:]]+1\.7_x86-64[[:space:]]+main[[:space:]]+contrib[[:space:]]+non-free$ ]] \
    || radp_die "Unexpected repository in frozen APT list: $source_line"
  [[ "$source_line" == *repository-base/* ]] && ((base_source_count+=1))
  [[ "$source_line" == *repository-update/* ]] && ((update_source_count+=1))
done
[[ "$base_source_count" -eq 1 && "$update_source_count" -eq 1 ]] || radp_die "Frozen APT list must include base and update exactly once."

###############################################################################
# Use only the explicitly frozen Astra list. A blank dpkg status database makes
# APT resolve a complete dependency closure instead of omitting packages merely
# because they happen to be installed on this preparation host.
###############################################################################
rm -rf -- "$APT_LISTS"
mkdir -p "$APT_LISTS/partial" "$DEBS/partial"
APT_OPTS=(
  -o "Dir::Etc::sourcelist=$FROZEN_LIST"
  -o "Dir::Etc::sourceparts=/dev/null"
  -o "Dir::State::lists=$APT_LISTS"
  -o "Dir::State::status=/dev/null"
  -o "Dir::Cache::archives=$DEBS"
  -o "Dir::Cache::archives::partial=$DEBS/partial"
  -o "APT::Sandbox::User=root"
  -o "Acquire::Retries=2"
  -o "Acquire::Languages=none"
)

radp_log "Updating package metadata from the frozen Astra 1.7.8 repositories."
apt-get "${APT_OPTS[@]}" update

engine_candidate="$(apt-cache "${APT_OPTS[@]}" policy "$ENGINE_PKG" | awk '/Candidate:/ {print $2}')"
compose_candidate="$(apt-cache "${APT_OPTS[@]}" policy "$COMPOSE_PKG" | awk '/Candidate:/ {print $2}')"
[[ "$engine_candidate" == "$ENGINE_VER" ]] || radp_die \
  "$ENGINE_PKG candidate is '$engine_candidate'; expected pinned version $ENGINE_VER."
[[ "$compose_candidate" == "$COMPOSE_VER" ]] || radp_die \
  "$COMPOSE_PKG candidate is '$compose_candidate'; expected pinned version $COMPOSE_VER."

radp_log "Downloading the complete dependency closure from frozen repositories."
DEBIAN_FRONTEND=noninteractive apt-get "${APT_OPTS[@]}" \
  --download-only --reinstall --yes --no-install-recommends install \
  "$ENGINE_PKG=$ENGINE_VER" "$COMPOSE_PKG=$COMPOSE_VER" openssl ca-certificates

shopt -s nullglob
mapfile -t deb_archives < <(find "$DEBS" -maxdepth 1 -type f -name '*.deb' -print | LC_ALL=C sort)
((${#deb_archives[@]} > 0)) || radp_die "APT downloaded no .deb files."

radp_log "Building the local APT repository index and exact package inventory."
python3 - "$DEBS" "$STAGE/docker-install/package-inventory.tsv" <<'PY_INDEX'
from hashlib import md5, sha256
from pathlib import Path
import gzip
import subprocess
import sys

repo = Path(sys.argv[1])
inventory_path = Path(sys.argv[2])
archives = sorted(repo.glob("*.deb"), key=lambda p: p.name)
if not archives:
    raise SystemExit("ERROR: no DEB files found for local repository indexing")

records = []
inventory = ["package\tversion\tarchitecture\tfilename"]
seen = set()
for archive in archives:
    control = subprocess.check_output(["dpkg-deb", "-f", str(archive)], text=True)
    fields = {}
    for line in control.splitlines():
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            fields[key.lower()] = value.strip()
    package = fields.get("package", "")
    version = fields.get("version", "")
    architecture = fields.get("architecture", "")
    if not package or not version or not architecture:
        raise SystemExit(f"ERROR: missing Package/Version/Architecture metadata: {archive.name}")
    key = (package, architecture)
    if key in seen:
        raise SystemExit(f"ERROR: more than one archive for package/architecture {package}:{architecture}")
    seen.add(key)

    payload = archive.read_bytes()
    index_record = control.rstrip("\n") + "\n"
    index_record += f"Filename: ./{archive.name}\n"
    index_record += f"Size: {len(payload)}\n"
    index_record += f"MD5sum: {md5(payload).hexdigest()}\n"
    index_record += f"SHA256: {sha256(payload).hexdigest()}\n"
    records.append(index_record)
    inventory.append(f"{package}\t{version}\t{architecture}\t{archive.name}")

packages = "\n".join(records) + "\n"
(repo / "Packages").write_text(packages, encoding="utf-8")
with (repo / "Packages.gz").open("wb") as output:
    with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0, compresslevel=9) as zipped:
        zipped.write(packages.encode("utf-8"))
inventory_path.write_text("\n".join(inventory) + "\n", encoding="utf-8")
PY_INDEX
[[ -s "$DEBS/Packages" && -s "$DEBS/Packages.gz" ]] || radp_die "Could not generate local APT package indexes."

python3 - "$DEBS" <<'PY_RELEASE'
from hashlib import md5, sha256
from pathlib import Path
import sys

repo = Path(sys.argv[1])
files = ("Packages", "Packages.gz")
lines = [
    "Origin: RADP Offline",
    "Label: RADP Offline",
    "Suite: offline",
    "Codename: offline",
    "Architectures: amd64",
    "Components: main",
    "Description: Local package repository for RADP offline installation",
    "MD5Sum:",
]
for name in files:
    payload = (repo / name).read_bytes()
    lines.append(f" {md5(payload).hexdigest()} {len(payload):16d} {name}")
lines.append("SHA256:")
for name in files:
    payload = (repo / name).read_bytes()
    lines.append(f" {sha256(payload).hexdigest()} {len(payload):16d} {name}")
(repo / "Release").write_text("\n".join(lines) + "\n", encoding="utf-8")
PY_RELEASE

###############################################################################
# Prove that APT can resolve every required package from this directory alone.
# The empty status database forces this check to account for the full closure.
###############################################################################
VERIFY_STATE="$(mktemp -d /tmp/radp-offline-apt-verify.XXXXXX)"
trap 'rc=$?; rm -rf -- "$VERIFY_STATE"; if ((rc != 0)); then printf "\nFULL PREPARATION FAILED (exit %s, line %s).\n" "$rc" "$LINENO" >&2; fi' EXIT
mkdir -p "$VERIFY_STATE/lists/partial"
DEBS_URI="$(printf '%s' "$DEBS" | sed 's/ /%20/g')"
printf 'deb [trusted=yes] file:%s ./\n' "$DEBS_URI" > "$VERIFY_STATE/sources.list"
LOCAL_APT_OPTS=(
  -o "Dir::Etc::sourcelist=$VERIFY_STATE/sources.list"
  -o "Dir::Etc::sourceparts=/dev/null"
  -o "Dir::State::lists=$VERIFY_STATE/lists"
  -o "Dir::State::status=/dev/null"
  -o "APT::Sandbox::User=root"
  -o "Acquire::Languages=none"
)
apt-get "${LOCAL_APT_OPTS[@]}" update
apt-get "${LOCAL_APT_OPTS[@]}" --simulate --no-install-recommends install \
  "$ENGINE_PKG=$ENGINE_VER" "$COMPOSE_PKG=$COMPOSE_VER" openssl ca-certificates
rm -rf -- "$VERIFY_STATE"
trap fail_trap EXIT

cp "$FROZEN_LIST" "$STAGE/docker-install/frozen-sources.list"

cat > "$STAGE/os-packages.txt" <<EOF_PACKAGES
docker_package=$ENGINE_PKG
docker_version=$ENGINE_VER
compose_package=$COMPOSE_PKG
compose_version=$COMPOSE_VER
EOF_PACKAGES

radp_log "Preparing application images, runtime assets and encrypted environment."
radp_prepare_runtime_assets "$ROOT" "$STAGE" full \
  "$SCRIPT_DIR/install.sh" "$LIB_DIR/install-common.sh"

printf '\nFULL PREPARATION SUCCESS\n'
printf 'Staging: %s\n.deb packages: %s\nCompose images: %s\n' \
  "$STAGE" "${#deb_archives[@]}" "$(wc -l < "$STAGE/compose-images.txt")"
printf 'Package index: %s/Packages\nNext: sudo %s/package.sh\n' "$DEBS" "$SCRIPT_DIR"

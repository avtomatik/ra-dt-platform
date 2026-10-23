#!/usr/bin/env bash
# Run as root on a CONNECTED, clean Astra Linux 1.7 amd64 VM.
# The VM must not already have Docker/Compose installed: APT must resolve the
# Docker dependency set against the same base package state as the clean target.
set -Eeuo pipefail
umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
BUNDLE="${BUNDLE_DIR:-$ROOT/release/radp-offline}"
DEBS="$BUNDLE/docker-install/debs"
ENGINE_PACKAGE="${ENGINE_PACKAGE:-docker.io}"
COMPOSE_PACKAGE="${COMPOSE_PACKAGE:-docker-compose-v2}"

fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
trap 'rc=$?; printf "\nPREPARATION FAILED (exit %s, line %s).\n" "$rc" "$LINENO" >&2; exit "$rc"' ERR

[[ "$(id -u)" -eq 0 ]] || fail "Run inside the Astra VM with sudo: sudo ./offline/prepare.sh"
for f in pyproject.toml uv.lock docker/Dockerfile docker-compose.yml .env; do
  [[ -e "$ROOT/$f" ]] || fail "Required project path missing: $ROOT/$f"
done
[[ -d "$ROOT/radp" && -d "$ROOT/html" && -d "$ROOT/data" ]] || fail "Expected radp/, html/, and data/ directories at the project root."
[[ -f /etc/os-release ]] || fail "Cannot identify the builder operating system."
# shellcheck disable=SC1091
. /etc/os-release
[[ "${ID:-}" == "astra" ]] || fail "Builder must run Astra Linux (ID=astra); detected ID=${ID:-unknown}."
[[ "$(dpkg --print-architecture)" == "amd64" ]] || fail "Expected dpkg architecture amd64."
[[ "$(uname -m)" == "x86_64" ]] || fail "Expected native x86_64 VM; cross-architecture builds are not supported by this script."

# Critical: APT only downloads dependencies not already installed. Use a clean
# matching Astra VM so the .deb set is complete for a clean target baseline.
if command -v docker >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1; then
  fail "Docker/Compose is already installed on this VM. Use a clean clone/snapshot of the exact target Astra update level, then run this script there. Otherwise APT may omit dependencies already installed on this builder."
fi
for p in docker.io docker-ce docker-ce-cli docker-compose docker-compose-v2; do
  status="$(dpkg-query -W -f='${db:Status-Status}' "$p" 2>/dev/null || true)"
  [[ "$status" != "installed" ]] || fail "Package $p is already installed; use a clean matching Astra VM for complete dependency collection."
done

command -v apt-get >/dev/null || fail "apt-get is unavailable."
command -v docker >/dev/null 2>&1 && fail "Docker unexpectedly appeared before package collection."
command -v python3 >/dev/null || fail "python3 is needed for packaging."

# Start fresh; never reuse a partial previous bundle.
case "$BUNDLE" in
  "$ROOT/release/radp-offline") ;;
  *) fail "For safety, BUNDLE_DIR must be unset; output is fixed at $ROOT/release/radp-offline." ;;
esac
rm -rf -- "$BUNDLE"
mkdir -p "$DEBS/partial" "$BUNDLE/data" "$BUNDLE/html" "$BUNDLE/scripts"

# Stamp the base system BEFORE Docker packages are installed. The target
# installer checks this fingerprint before changing the target OS.
cp /etc/os-release "$BUNDLE/build-os-release"
{
  printf 'package\tversion\n'
  for p in base-files libc6 libstdc++6 systemd systemd-sysv dpkg apt libseccomp2 libapparmor1 iptables nftables containerd runc openssl ca-certificates; do
    version="$(dpkg-query -W -f='${Version}' "$p" 2>/dev/null || true)"
    [[ -n "$version" ]] && printf '%s\t%s\n' "$p" "$version"
  done
} > "$BUNDLE/base-packages.tsv"

printf '%s\n' "Checking Astra APT candidates..."
apt-get update
apt-cache policy "$ENGINE_PACKAGE" "$COMPOSE_PACKAGE" docker.io docker-compose-v2 docker-compose || true
candidate_of() { apt-cache policy "$1" 2>/dev/null | awk '/Candidate:/ {print $2; exit}'; }
engine_candidate="$(candidate_of "$ENGINE_PACKAGE")"
compose_candidate="$(candidate_of "$COMPOSE_PACKAGE")"
[[ -n "$engine_candidate" && "$engine_candidate" != "(none)" ]] || fail "No APT candidate for ENGINE_PACKAGE=$ENGINE_PACKAGE in the configured Astra repositories. See apt-cache policy output above."
[[ -n "$compose_candidate" && "$compose_candidate" != "(none)" ]] || fail "No APT candidate for COMPOSE_PACKAGE=$COMPOSE_PACKAGE. Verify docker-compose-v2 availability; if Astra provides a different package, set COMPOSE_PACKAGE explicitly only if it installs a Compose v2-compatible docker-compose command."

printf '\nCollecting the OS dependency closure into %s ...\n' "$DEBS"
# On a clean matching Astra base, APT downloads all packages needed but not
# already installed. Those already installed must match the target baseline,
# enforced via base-packages.tsv at install time.
DEBIAN_FRONTEND=noninteractive apt-get --download-only --yes \
  -o "Dir::Cache::archives=$DEBS/" \
  -o Acquire::Retries=2 \
  install "$ENGINE_PACKAGE" "$COMPOSE_PACKAGE" openssl ca-certificates
shopt -s nullglob
apt_debs=("$DEBS"/*.deb)
((${#apt_debs[@]} >= 2)) || fail "APT did not download a usable .deb package set."
# Verify top-level package archives were included.
for required in "$ENGINE_PACKAGE" "$COMPOSE_PACKAGE"; do
  found=0
  for deb in "${apt_debs[@]}"; do
    pkg="$(dpkg-deb -f "$deb" Package 2>/dev/null || true)"
    [[ "$pkg" == "$required" ]] && found=1
  done
  ((found == 1)) || fail "Downloaded package archive for $required is missing."
done

printf '\nInstalling Docker/Compose on the connected builder for image preparation...\n'
DEBIAN_FRONTEND=noninteractive apt-get install --yes "$ENGINE_PACKAGE" "$COMPOSE_PACKAGE" openssl ca-certificates
command -v systemctl >/dev/null || fail "systemctl is not available."
systemctl enable --now docker
docker info >/dev/null
docker --version
command -v docker-compose >/dev/null || fail "Package $COMPOSE_PACKAGE did not provide the required docker-compose command."
compose_version="$(docker-compose version 2>&1)"
printf '%s\n' "$compose_version"
grep -Eiq '(^|[^0-9])v?2\.[0-9]+\.[0-9]+' <<<"$compose_version" || fail "docker-compose is not Compose v2. The required --pull never / --no-build flow is unsupported."
up_help="$(docker-compose up --help 2>&1)"
grep -q -- '--pull' <<<"$up_help" || fail "docker-compose up does not support --pull."
grep -q -- '--no-build' <<<"$up_help" || fail "docker-compose up does not support --no-build."
if grep -Eq '^[[:space:]]*build[[:space:]]*:' "$ROOT/docker-compose.yml"; then
  fail "docker-compose.yml contains build:; offline deployment must use prebuilt images only."
fi
policy_count="$(grep -Ec '^[[:space:]]*pull_policy:[[:space:]]*never[[:space:]]*$' "$ROOT/docker-compose.yml" || true)"
((policy_count >= 4)) || fail "Expected pull_policy: never on all four Compose services; found $policy_count entries."
(cd "$ROOT" && docker-compose config -q) || fail "Project docker-compose.yml/.env validation failed on the builder."

# Build in a temporary staging context that explicitly excludes .env and any
# prior offline bundle. This avoids baking project secrets into the image even
# if the repository's .dockerignore is incomplete.
BUILD_CONTEXT="$(mktemp -d /tmp/radp-build-context.XXXXXX)"
cleanup() { rm -rf -- "$BUILD_CONTEXT"; }
trap 'rc=$?; cleanup; if ((rc != 0)); then printf "\nPREPARATION FAILED (exit %s, line %s).\n" "$rc" "$LINENO" >&2; fi; exit "$rc"' EXIT
# Exclude hidden secrets and local build output. Preserve required source/data.
tar -C "$ROOT" \
  --exclude='./.git' --exclude='./.env' --exclude='./.env.*' \
  --exclude='./offline' --exclude='./release' --exclude='./.venv' \
  --exclude='*/__pycache__' --exclude='*.pyc' \
  -cf - . | tar -C "$BUILD_CONTEXT" -xf -
[[ ! -e "$BUILD_CONTEXT/.env" ]] || fail ".env unexpectedly leaked into the staged Docker build context."
docker build --pull --tag radp:latest --file "$BUILD_CONTEXT/docker/Dockerfile" "$BUILD_CONTEXT"
# Native x86_64 Astra VM: image pulls naturally select linux/amd64.
docker pull postgres:17
docker pull mcuadros/ofelia:latest

for img in radp:latest postgres:17 mcuadros/ofelia:latest; do
  docker image inspect "$img" >/dev/null || fail "Required image missing after build/pull: $img"
  os="$(docker image inspect --format '{{.Os}}' "$img")"
  arch="$(docker image inspect --format '{{.Architecture}}' "$img")"
  [[ "$os/$arch" == "linux/amd64" ]] || fail "$img has platform $os/$arch, expected linux/amd64."
done

# Include the actual project Compose file and any relative runtime assets.
cp "$ROOT/docker-compose.yml" "$BUNDLE/docker-compose.yml"
cp -a "$ROOT/data/." "$BUNDLE/data/"
cp -a "$ROOT/html/." "$BUNDLE/html/"
printf 'linux/amd64\n' > "$BUNDLE/target-platform.txt"
printf 'engine_package=%s\ncompose_package=%s\n' "$ENGINE_PACKAGE" "$COMPOSE_PACKAGE" > "$BUNDLE/os-packages.txt"
printf '%s\n' "$compose_version" > "$BUNDLE/compose-version-on-builder.txt"
docker image inspect radp:latest postgres:17 mcuadros/ofelia:latest > "$BUNDLE/image-metadata.json"
docker image save --output "$BUNDLE/images.tar" radp:latest postgres:17 mcuadros/ofelia:latest
cp "$SCRIPT_DIR/install.sh" "$BUNDLE/install.sh"
chmod 0755 "$BUNDLE/install.sh"

# Encrypt, never copy, the plaintext environment file into the bundle.
[[ -s "$ROOT/.env" ]] || fail "Project .env is empty; refusing to produce a bundle with ambiguous runtime configuration."
read -r -s -p 'Enter passphrase to encrypt .env for the ZIP: ' pass1; printf '\n'
read -r -s -p 'Repeat passphrase: ' pass2; printf '\n'
[[ -n "$pass1" && "$pass1" == "$pass2" ]] || fail "Passphrases are empty or do not match."
printf '%s' "$pass1" | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 250000 -pass stdin \
  -in "$ROOT/.env" -out "$BUNDLE/.env.enc"
# Verify we can recover the exact source .env, without retaining plaintext.
tmp_env="$(mktemp /tmp/radp-env-check.XXXXXX)"
if ! printf '%s' "$pass1" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 250000 -pass stdin \
    -in "$BUNDLE/.env.enc" -out "$tmp_env"; then
  rm -f "$tmp_env"; unset pass1 pass2; fail "Could not verify encrypted .env."
fi
cmp -s "$ROOT/.env" "$tmp_env" || { rm -f "$tmp_env"; unset pass1 pass2; fail "Encrypted .env verification mismatch."; }
rm -f "$tmp_env"
unset pass1 pass2
[[ ! -e "$BUNDLE/.env" ]] || fail "Plaintext .env must never be included in the bundle."

# Metadata helps diagnostics; it is not a substitute for clean offline testing.
printf '\nPREPARATION SUCCESS\n'
printf 'Bundle staging directory: %s\n' "$BUNDLE"
printf 'OS packages collected: %s .deb files\n' "${#apt_debs[@]}"
printf 'Images saved: radp:latest, postgres:17, mcuadros/ofelia:latest\n'
printf 'Environment file: encrypted as .env.enc (plaintext excluded)\n'
printf 'IMPORTANT: this is not yet a portability claim; package and ZIP, then test on a clean matching Astra VM with its virtual NIC disconnected.\n'

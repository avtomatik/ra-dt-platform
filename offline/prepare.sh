#!/usr/bin/env bash
# Run as root on the connected Astra Linux SE 1.7.8 amd64 preparation VM.
# This script intentionally uses frozen Astra 1.7.8 repositories and pins the
# Docker/Compose versions already established on the Test host.
set -Eeuo pipefail
umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
STAGE="$ROOT/release/radp-offline"
DEBS="$STAGE/docker-install/debs"
FROZEN_LIST="${FROZEN_LIST:-/tmp/astra-frozen-1.7.8.list}"
APT_LISTS="${APT_LISTS:-/tmp/astra-frozen-lists}"
ENGINE_PKG="docker.io"
ENGINE_VER="25.0.5.astra3+ci24"
COMPOSE_PKG="docker-compose"
COMPOSE_VER="1.29.2-1astra.se1+ci1+b2"
fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
trap 'rc=$?; if ((rc != 0)); then printf "\nPREPARATION FAILED (exit %s, line %s).\n" "$rc" "$LINENO" >&2; fi' EXIT

[[ $EUID -eq 0 ]] || fail "Run on the Astra preparation VM with sudo: sudo ./offline/prepare.sh"
[[ -f /etc/os-release ]] || fail "Missing /etc/os-release"
# shellcheck disable=SC1091
. /etc/os-release
[[ "${ID:-}" == astra ]] || fail "Preparation must run on Astra Linux; detected ID=${ID:-unknown}."
[[ "$(dpkg --print-architecture)" == amd64 && "$(uname -m)" == x86_64 ]] || fail "Expected native x86_64 / amd64."
[[ -f /etc/astra_version ]] || fail "Cannot verify Astra release: /etc/astra_version missing."
grep -q '1\.7\.8' /etc/astra_version || fail "This workflow is pinned to Astra Linux SE 1.7.8; /etc/astra_version does not say 1.7.8."
for f in pyproject.toml uv.lock docker/Dockerfile docker-compose.yml .env; do
  [[ -f "$ROOT/$f" ]] || fail "Required project file missing: $ROOT/$f"
done
for d in radp html data; do [[ -d "$ROOT/$d" ]] || fail "Required project directory missing: $ROOT/$d"; done
command -v apt-get >/dev/null || fail "apt-get not found"
command -v docker-compose >/dev/null || true

# Use the frozen repo list already verified on this VM, or create the exact
# Astra 1.7.8 base/update list. Do not use the host's live repo configuration.
if [[ ! -s "$FROZEN_LIST" ]]; then
  cat > "$FROZEN_LIST" <<'EOF'
deb https://dl.astralinux.ru/astra/frozen/1.7_x86-64/1.7.8/repository-base/ 1.7_x86-64 main contrib non-free
deb https://dl.astralinux.ru/astra/frozen/1.7_x86-64/1.7.8/repository-update/ 1.7_x86-64 main contrib non-free
EOF
fi
mkdir -p "$APT_LISTS/partial"
APT_OPTS=(
  -o "Dir::Etc::sourcelist=$FROZEN_LIST"
  -o "Dir::Etc::sourceparts=/dev/null"
  -o "Dir::State::lists=$APT_LISTS"
  -o "Acquire::Retries=2"
)
# Resolve candidates strictly from the frozen repository metadata, not from
# packages installed on the preparation VM. Otherwise an installed newer
# Debian package (e.g. libcurl4 from bookworm) can be selected and cannot be
# downloaded from the Astra 1.7.8 frozen repositories.
CACHE_OPTS=("${APT_OPTS[@]}" -o "Dir::State::status=/dev/null")
apt-get "${APT_OPTS[@]}" update

engine_candidate="$(apt-cache "${CACHE_OPTS[@]}" policy "$ENGINE_PKG" | awk '/Candidate:/ {print $2}')"
compose_candidate="$(apt-cache "${CACHE_OPTS[@]}" policy "$COMPOSE_PKG" | awk '/Candidate:/ {print $2}')"
[[ "$engine_candidate" == "$ENGINE_VER" ]] || fail "$ENGINE_PKG candidate is '$engine_candidate', expected pinned $ENGINE_VER from frozen Astra 1.7.8."
[[ "$compose_candidate" == "$COMPOSE_VER" ]] || fail "$COMPOSE_PKG candidate is '$compose_candidate', expected pinned $COMPOSE_VER from frozen Astra 1.7.8."

# Use apt-cache's built-in recursive dependency traversal below; no helper
# package such as apt-rdepends is required or assumed to exist in frozen repos.

# Rebuild staging so stale files from a prior attempt cannot silently ship.
rm -rf -- "$STAGE"
mkdir -p "$DEBS" "$STAGE/data" "$STAGE/html"
cp /etc/os-release "$STAGE/build-os-release"
printf 'linux/amd64\n' > "$STAGE/target-platform.txt"
printf 'engine_package=%s\nengine_version=%s\ncompose_package=%s\ncompose_version=%s\n' \
  "$ENGINE_PKG" "$ENGINE_VER" "$COMPOSE_PKG" "$COMPOSE_VER" > "$STAGE/os-packages.txt"

# Capture a conservative transitive dependency closure, including alternatives
# and concrete providers that apt-cache lists beneath virtual dependencies.
# Only packages with a real candidate are downloaded; this may include extras.
printf '\nResolving dependency package names from frozen Astra repositories...\n'
apt-cache "${CACHE_OPTS[@]}" --recurse --important depends "$ENGINE_PKG" "$COMPOSE_PKG" openssl ca-certificates \
  | awk '
      /^[[:alnum:]][[:alnum:]+.-]*(:[[:alnum:]-]+)?$/ {
        pkg = $0
        sub(/:.*/, "", pkg)
        print pkg
        next
      }
      /^[[:space:]]*(PreDepends|Depends):/ {
        line = $0
        sub(/^[[:space:]]*(PreDepends|Depends):[[:space:]]*/, "", line)
        n = split(line, alternatives, /\|/)
        for (i = 1; i <= n; i++) {
          dep = alternatives[i]
          sub(/^[[:space:]<]+/, "", dep)
          sub(/[[:space:]>(].*$/, "", dep)
          sub(/:.*/, "", dep)
          if (dep ~ /^[[:alnum:]][[:alnum:]+.-]*$/) print dep
        }
      }
    ' | sort -u > "$STAGE/dependency-package-names.txt"
printf '%s\n' "$ENGINE_PKG" "$COMPOSE_PKG" openssl ca-certificates >> "$STAGE/dependency-package-names.txt"
sort -u -o "$STAGE/dependency-package-names.txt" "$STAGE/dependency-package-names.txt"

while IFS= read -r pkg; do
  [[ -n "$pkg" ]] || continue
  candidate="$(apt-cache "${CACHE_OPTS[@]}" policy "$pkg" 2>/dev/null | awk '/Candidate:/ {print $2}')"
  [[ -n "$candidate" && "$candidate" != "(none)" ]] || continue
  # Download every candidate even if already installed on the builder.
  (cd "$DEBS" && apt-get "${APT_OPTS[@]}" download "$pkg=$candidate") \
    || fail "Could not download dependency package $pkg=$candidate from the frozen repositories."
done < "$STAGE/dependency-package-names.txt"

# Ensure the exact pinned top-level packages are present (not just candidates).
(cd "$DEBS" && apt-get "${APT_OPTS[@]}" download "$ENGINE_PKG=$ENGINE_VER" "$COMPOSE_PKG=$COMPOSE_VER") \
  || fail "Could not download pinned Docker/Compose packages."

# Remove duplicate package versions, retaining the exact candidate package per name.
# apt-get download names files package_version_arch.deb. Keep every version for now;
# APT will choose the compatible version when installing the local archive set.

# Install the pinned Docker/Compose packages on this connected preparation VM.
DEBIAN_FRONTEND=noninteractive apt-get "${APT_OPTS[@]}" install -y \
  "$ENGINE_PKG=$ENGINE_VER" "$COMPOSE_PKG=$COMPOSE_VER" openssl ca-certificates
systemctl enable --now docker
docker info >/dev/null
[[ "$(docker --version)" == *"25.0.5"* ]] || fail "Unexpected Docker version: $(docker --version)"
compose_version="$(docker-compose version 2>&1)"
grep -q '1\.29\.2' <<<"$compose_version" || fail "Expected docker-compose 1.29.2, got: $compose_version"
printf '%s\n' "$compose_version" > "$STAGE/compose-version.txt"

# Compose v1 does not support --pull never. Validate config and export every
# image named by the real Compose file, rather than assuming service/container names.
(cd "$ROOT" && docker-compose config -q) || fail "docker-compose config failed. Fix the project's Compose/.env first."
# Compose v1.29.2 has no `config --images` option. Read the normalized
# Compose YAML instead (one image: field per service).
mapfile -t compose_images < <(
  cd "$ROOT"
  docker-compose config | awk '$1 == "image:" {print $2}' | sort -u
)
((${#compose_images[@]} > 0)) || fail "Compose config returned no images."
printf '%s\n' "${compose_images[@]}" > "$STAGE/compose-images.txt"

# Build the RADP application image without putting .env into the build context.
BUILD_CONTEXT="$(mktemp -d /tmp/radp-build-context.XXXXXX)"
cleanup() { rm -rf -- "$BUILD_CONTEXT"; }
trap 'rc=$?; cleanup; if ((rc != 0)); then printf "\nPREPARATION FAILED (exit %s, line %s).\n" "$rc" "$LINENO" >&2; fi; exit "$rc"' EXIT
tar -C "$ROOT" \
  --exclude='./.git' --exclude='./.env' --exclude='./.env.*' \
  --exclude='./offline' --exclude='./release' --exclude='./.venv' \
  --exclude='*/__pycache__' --exclude='*.pyc' \
  -cf - . | tar -C "$BUILD_CONTEXT" -xf -
[[ ! -e "$BUILD_CONTEXT/.env" ]] || fail ".env leaked into Docker build context."
docker build --pull -t radp:latest -f "$BUILD_CONTEXT/docker/Dockerfile" "$BUILD_CONTEXT"

# Pull public upstream images, then alias them to the exact names referenced by
# Compose. Existing custom/internal image names are preserved as Compose tags.
docker pull postgres:17
docker pull mcuadros/ofelia:latest
for ref in "${compose_images[@]}"; do
  case "$ref" in
    */postgres:17|postgres:17) docker image tag postgres:17 "$ref" ;;
    */mcuadros/ofelia:latest|mcuadros/ofelia:latest) docker image tag mcuadros/ofelia:latest "$ref" ;;
    *radp*) docker image tag radp:latest "$ref" ;;
    *)
      docker image inspect "$ref" >/dev/null 2>&1 || fail "Compose references '$ref', but it is not present locally and this script has no safe source mapping for it."
      ;;
  esac
  docker image inspect "$ref" >/dev/null || fail "Required Compose image is missing: $ref"
  platform="$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$ref")"
  [[ "$platform" == linux/amd64 ]] || fail "Image $ref has platform $platform, expected linux/amd64."
done

# Copy runtime assets referenced by the known project layout.
cp "$ROOT/docker-compose.yml" "$STAGE/docker-compose.yml"
cp -a "$ROOT/data/." "$STAGE/data/"
cp -a "$ROOT/html/." "$STAGE/html/"
cp "$SCRIPT_DIR/install.sh" "$STAGE/install.sh"
chmod 0755 "$STAGE/install.sh"
docker image inspect "${compose_images[@]}" > "$STAGE/image-metadata.json"
docker image save --output "$STAGE/images.tar" "${compose_images[@]}"

# Record the package inventory. The clean disconnected target test remains the
# final authority on dependency closure.
: > "$STAGE/docker-install/package-inventory.tsv"
for deb in "$DEBS"/*.deb; do
  [[ -f "$deb" ]] || continue
  printf '%s\t%s\t%s\t%s\n' \
    "$(dpkg-deb -f "$deb" Package)" \
    "$(dpkg-deb -f "$deb" Version)" \
    "$(dpkg-deb -f "$deb" Architecture)" \
    "$(basename "$deb")" >> "$STAGE/docker-install/package-inventory.tsv"
done
sort -u -o "$STAGE/docker-install/package-inventory.tsv" "$STAGE/docker-install/package-inventory.tsv"

[[ -s "$ROOT/.env" ]] || fail "Project .env is missing or empty."
read -r -s -p 'Passphrase to encrypt .env for the offline ZIP: ' pass1; printf '\n'
read -r -s -p 'Repeat passphrase: ' pass2; printf '\n'
[[ -n "$pass1" && "$pass1" == "$pass2" ]] || fail "Passphrases are empty or do not match."
printf '%s' "$pass1" | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 250000 -pass stdin \
  -in "$ROOT/.env" -out "$STAGE/.env.enc"
tmp_env="$(mktemp /tmp/radp-env-check.XXXXXX)"
printf '%s' "$pass1" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 250000 -pass stdin \
  -in "$STAGE/.env.enc" -out "$tmp_env" || fail "Could not verify encrypted .env."
cmp -s "$ROOT/.env" "$tmp_env" || fail "Encrypted .env verification mismatch."
rm -f "$tmp_env"
unset pass1 pass2
[[ ! -e "$STAGE/.env" ]] || fail "Plaintext .env must not be in staging."
printf '\nPREPARATION SUCCESS\n'
printf 'Staging: %s\n.deb files: %s\nCompose images: %s\n' "$STAGE" "$(find "$DEBS" -maxdepth 1 -name '*.deb' | wc -l)" "${#compose_images[@]}"
printf 'Next: sudo ./offline/package.sh\n'
printf 'Note: complete dependency closure is accepted only after install succeeds on a clean, disconnected Astra 1.7.8 VM.\n'

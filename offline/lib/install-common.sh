#!/usr/bin/env bash
###############################################################################
# This file is copied into each deployment bundle beside install.sh.
###############################################################################
set -Eeuo pipefail
umask 077

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
APT_STATE=""
APT_LISTS=""
APT_ARCHIVES=""
APT_SOURCE_LIST=""
TEMP_ENV=""

radp_install_log() { printf '\n[radp-install] %s\n' "$*"; }
radp_install_die() { printf '\n[radp-install][ERROR] %s\n' "$*" >&2; exit 1; }
radp_install_cleanup() {
  [[ -z "$TEMP_ENV" || ! -e "$TEMP_ENV" ]] || rm -f -- "$TEMP_ENV"
  [[ -z "$APT_STATE" || ! -d "$APT_STATE" ]] || rm -rf -- "$APT_STATE"
}
trap radp_install_cleanup EXIT

radp_install_read_kv() {
  local file="$1" key="$2"
  awk -F= -v wanted="$key" '$1 == wanted {sub(/^[^=]*=/, ""); print; exit}' "$file"
}

radp_install_compose() {
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  elif docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    radp_install_die "Docker Compose is not installed."
  fi
}

radp_install_preflight() {
  local expected_mode="${1:?bundle mode is required}"
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || radp_install_die "Run with sudo: sudo ./install.sh"
  for command_name in sha256sum awk grep sed; do
    command -v "$command_name" >/dev/null 2>&1 || radp_install_die "Required command is missing: $command_name"
  done
  [[ -s "$ROOT/SHA256SUMS" ]] || radp_install_die "SHA256SUMS is missing."
  [[ ! -e "$ROOT/.env" ]] || radp_install_die "An existing .env is present. Use a fresh, empty extraction directory; it will not be overwritten."
  for required_file in images.tar docker-compose.yml .env.enc .env.sha256 target-platform.txt \
      compose-images.txt image-manifest.tsv runtime-requirements.txt bundle-mode.txt install-common.sh; do
    [[ -s "$ROOT/$required_file" ]] || radp_install_die "Required bundle file is missing or empty: $required_file"
  done
  [[ ! -e "$ROOT/.env" ]] || radp_install_die "Plaintext .env must not be included in the bundle."
  [[ "$(cat "$ROOT/bundle-mode.txt")" == "mode=$expected_mode" ]] || radp_install_die "Bundle mode does not match this installer ($expected_mode)."
  if [[ "$expected_mode" == "partial" ]]; then
    [[ -s "$ROOT/HOST-REQUIREMENTS.txt" ]] || radp_install_die "Partial bundle is missing HOST-REQUIREMENTS.txt."
  fi

  radp_install_log "Verifying bundle checksums."
  (cd "$ROOT" && sha256sum -c SHA256SUMS)

  [[ -f /etc/os-release ]] || radp_install_die "Cannot identify target OS."
  # shellcheck disable=SC1091
  . /etc/os-release
  [[ "${ID:-}" == "astra" ]] || radp_install_die "Target must be Astra Linux; detected ID=${ID:-unknown}."
  [[ -f /etc/astra_version ]] && grep -q '1\.7\.8' /etc/astra_version \
    || radp_install_die "Target must be Astra Linux SE 1.7.8."
  [[ "$(dpkg --print-architecture 2>/dev/null || true)" == "amd64" ]] \
    || radp_install_die "Target architecture must be amd64."
  [[ "$(uname -m)" == "x86_64" ]] || radp_install_die "Target machine architecture must be x86_64."
  grep -q '^linux/amd64$' "$ROOT/target-platform.txt" \
    || radp_install_die "Bundle platform is not linux/amd64."
}

radp_install_full_os_packages() {
  local expected_docker expected_compose debs_dir docker_installed_version compose_installed_version
  debs_dir="$ROOT/docker-install/debs"
  [[ -s "$ROOT/os-packages.txt" ]] || radp_install_die "Full bundle is missing os-packages.txt."
  [[ -s "$debs_dir/Packages" ]] || radp_install_die "Full bundle is missing its local APT Packages index."
  [[ -d "$debs_dir" ]] || radp_install_die "Full bundle is missing docker-install/debs."

  expected_docker="$(radp_install_read_kv "$ROOT/os-packages.txt" docker_version)"
  expected_compose="$(radp_install_read_kv "$ROOT/os-packages.txt" compose_version)"
  [[ -n "$expected_docker" && -n "$expected_compose" ]] || radp_install_die "Invalid os-packages.txt manifest."

  # Refuse to replace a different pre-existing Docker installation. This path
  # is intended for a fresh target; it must not silently downgrade host tools.
  local installed
  docker_installed_version="$(dpkg-query -W -f='${Version}' docker.io 2>/dev/null || true)"
  if [[ -n "$docker_installed_version" && "$docker_installed_version" != "$expected_docker" ]]; then
    radp_install_die "docker.io is already installed at $docker_installed_version, but this bundle pins $expected_docker. Refusing to replace it."
  fi
  compose_installed_version="$(dpkg-query -W -f='${Version}' docker-compose 2>/dev/null || true)"
  if [[ -n "$compose_installed_version" && "$compose_installed_version" != "$expected_compose" ]]; then
    radp_install_die "docker-compose is already installed at $compose_installed_version, but this bundle pins $expected_compose. Refusing to replace it."
  fi
  local conflicting_package status
  for conflicting_package in docker-ce docker-ce-cli docker-compose-plugin containerd.io; do
    status="$(dpkg-query -W -f='${db:Status-Status}' "$conflicting_package" 2>/dev/null || true)"
    [[ "$status" != "installed" ]] || radp_install_die \
      "Conflicting package '$conflicting_package' is already installed. Full mode is intended for a clean target; refusing to replace host-managed Docker packages."
  done
  if command -v docker >/dev/null 2>&1 && [[ -z "$docker_installed_version" ]]; then
    radp_install_die "A Docker CLI already exists but is not accounted for by the expected docker.io package. Use partial mode for host-managed Docker."
  fi
  if command -v docker-compose >/dev/null 2>&1 && [[ -z "$compose_installed_version" ]]; then
    radp_install_die "A docker-compose executable already exists but is not accounted for by the expected package. Use partial mode for host-managed Compose."
  fi
  if docker compose version >/dev/null 2>&1 && [[ -z "$compose_installed_version" ]]; then
    radp_install_die "A Docker Compose plugin already exists but is not accounted for by the expected package. Use partial mode for host-managed Compose."
  fi

  radp_install_log "Installing Docker/Compose exclusively from the bundled local APT repository."
  APT_STATE="$(mktemp -d /var/tmp/radp-offline-apt.XXXXXX)"
  APT_LISTS="$APT_STATE/lists"
  APT_ARCHIVES="$APT_STATE/archives"
  APT_SOURCE_LIST="$APT_STATE/sources.list"
  mkdir -p "$APT_LISTS/partial" "$APT_ARCHIVES/partial"
  : > "$APT_SOURCE_LIST"
  # A file: source is the only configured source for this APT transaction.
  # Existing /etc/apt/sources.list and sources.list.d entries are excluded.
  local debs_uri
  debs_uri="$(printf '%s' "$debs_dir" | sed 's/ /%20/g')"
  printf 'deb [trusted=yes] file:%s ./\n' "$debs_uri" > "$APT_SOURCE_LIST"

  local -a apt_options
  apt_options=(
    -o "Dir::Etc::sourcelist=$APT_SOURCE_LIST"
    -o "Dir::Etc::sourceparts=/dev/null"
    -o "Dir::State::lists=$APT_LISTS"
    -o "Dir::Cache::archives=$APT_ARCHIVES"
    -o "Dir::Cache::archives::partial=$APT_ARCHIVES/partial"
    -o "Acquire::Languages=none"
    -o "APT::Sandbox::User=root"
    -o "APT::Get::AllowUnauthenticated=true"
  )

  apt-get "${apt_options[@]}" update
  DEBIAN_FRONTEND=noninteractive apt-get "${apt_options[@]}" install --yes --no-install-recommends \
    "docker.io=$expected_docker" "docker-compose=$expected_compose" openssl ca-certificates

  installed="$(dpkg-query -W -f='${Version}' docker.io 2>/dev/null || true)"
  [[ "$installed" == "$expected_docker" ]] || radp_install_die "Installed docker.io version '$installed' does not match '$expected_docker'."
  installed="$(dpkg-query -W -f='${Version}' docker-compose 2>/dev/null || true)"
  [[ "$installed" == "$expected_compose" ]] || radp_install_die "Installed docker-compose version '$installed' does not match '$expected_compose'."
}

radp_install_check_host_packages() {
  local expected_docker expected_compose docker_output compose_output
  expected_docker="$(radp_install_read_kv "$ROOT/runtime-requirements.txt" docker_cli_version)"
  expected_compose="$(radp_install_read_kv "$ROOT/runtime-requirements.txt" compose_version)"
  command -v docker >/dev/null 2>&1 || radp_install_die "Docker is not installed. Install it from the host administrator's verified package collection first."
  docker_output="$(docker --version 2>&1)" || radp_install_die "Docker CLI is not functioning."

  if command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then
    compose_output="$(radp_install_compose version 2>&1)" || radp_install_die "Docker Compose is not functioning."
  else
    radp_install_die "Docker Compose is missing. Install the version listed in HOST-REQUIREMENTS.txt or an approved compatible version."
  fi

  if [[ "${RADP_ALLOW_HOST_VERSION_VARIANCE:-0}" == "1" ]]; then
    printf 'Host Docker: %s\nHost Compose: %s\n' "$docker_output" "$compose_output" > "$ROOT/host-runtime-versions.txt"
    printf '[radp-install][WARNING] Host version variance was explicitly allowed.\n' >&2
  else
    [[ "$docker_output" == *"$expected_docker"* ]] || radp_install_die \
      "Host Docker version differs from expected $expected_docker: $docker_output. Confirm compatibility, then explicitly set RADP_ALLOW_HOST_VERSION_VARIANCE=1 if approved."
    [[ "$compose_output" == *"$expected_compose"* ]] || radp_install_die \
      "Host Compose version differs from expected $expected_compose: $compose_output. Confirm compatibility, then explicitly set RADP_ALLOW_HOST_VERSION_VARIANCE=1 if approved."
    printf 'Host Docker: %s\nHost Compose: %s\n' "$docker_output" "$compose_output" > "$ROOT/host-runtime-versions.txt"
  fi

  command -v openssl >/dev/null 2>&1 || radp_install_die "OpenSSL is missing; it is required to decrypt .env."
}

radp_install_decrypt_env() {
  local supplied_pass expected_hash actual_hash
  radp_install_log "Decrypting the environment file."
  read -r -s -p 'Passphrase used to encrypt .env: ' supplied_pass; printf '\n'
  [[ -n "$supplied_pass" ]] || radp_install_die "Empty passphrase is not allowed."
  TEMP_ENV="$ROOT/.env.tmp.$$"
  printf '%s' "$supplied_pass" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 250000 -pass stdin \
    -in "$ROOT/.env.enc" -out "$TEMP_ENV" || radp_install_die "Decryption failed; check the passphrase."
  unset supplied_pass
  [[ -s "$TEMP_ENV" ]] || radp_install_die "Decrypted .env is empty."
  expected_hash="$(tr -d '[:space:]' < "$ROOT/.env.sha256")"
  actual_hash="$(sha256sum "$TEMP_ENV" | awk '{print $1}')"
  [[ -n "$expected_hash" && "$actual_hash" == "$expected_hash" ]] || radp_install_die "Decrypted .env checksum mismatch; the passphrase or bundle is invalid."
  chmod 0600 "$TEMP_ENV"
  mv -- "$TEMP_ENV" "$ROOT/.env"
  TEMP_ENV=""
}

radp_install_deploy_runtime() {
  local -a expected_images configured_images services ids
  local ref platform service id state exit_code api_ready api_port

  radp_install_log "Validating the packaged Compose configuration."
  if grep -Eq '^[[:space:]]*build[[:space:]]*:' "$ROOT/docker-compose.yml"; then
    radp_install_die "Packaged Compose file contains build:. Offline deployment may not build images."
  fi
  (cd "$ROOT" && radp_install_compose config -q) || radp_install_die "Compose configuration validation failed."
  mapfile -t expected_images < "$ROOT/compose-images.txt"
  mapfile -t configured_images < <(
    cd "$ROOT"
    radp_install_compose config | awk '$1 == "image:" {gsub(/"/, "", $2); print $2}' | sort -u
  )
  ((${#configured_images[@]} > 0)) || radp_install_die "Compose reports no images."
  printf '%s\n' "${configured_images[@]}" | sort -u > "$ROOT/.configured-images.tmp"
  printf '%s\n' "${expected_images[@]}" | sort -u > "$ROOT/.expected-images.tmp"
  if ! cmp -s "$ROOT/.configured-images.tmp" "$ROOT/.expected-images.tmp"; then
    rm -f "$ROOT/.configured-images.tmp" "$ROOT/.expected-images.tmp"
    radp_install_die "Configured Compose images do not match compose-images.txt."
  fi
  rm -f "$ROOT/.configured-images.tmp" "$ROOT/.expected-images.tmp"

  radp_install_log "Loading packaged Docker images."
  docker image load --input "$ROOT/images.tar"
  for ref in "${expected_images[@]}"; do
    [[ -n "$ref" ]] || continue
    docker image inspect "$ref" >/dev/null 2>&1 || radp_install_die "Image missing after load: $ref"
    platform="$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$ref")"
    [[ "$platform" == "linux/amd64" ]] || radp_install_die "Image $ref has platform $platform."
  done

  radp_install_log "Starting services without building images."
  (cd "$ROOT" && radp_install_compose up -d --no-build)
  sleep 5
  (cd "$ROOT" && radp_install_compose ps)

  mapfile -t services < <(cd "$ROOT" && radp_install_compose config --services)
  for service in "${services[@]}"; do
    mapfile -t ids < <(cd "$ROOT" && radp_install_compose ps -q -a "$service")
    ((${#ids[@]} > 0)) || radp_install_die "No container was created for Compose service '$service'."
    for id in "${ids[@]}"; do
      state="$(docker inspect --format '{{.State.Status}}' "$id")"
      exit_code="$(docker inspect --format '{{.State.ExitCode}}' "$id")"
      if [[ "$state" == "exited" && "$exit_code" == "0" ]]; then
        continue
      fi
      [[ "$state" == "running" ]] || {
        docker logs --tail=80 "$id" >&2 || true
        radp_install_die "Service '$service' container state is $state (exit=$exit_code)."
      }
    done
  done

  api_port="$(radp_install_read_kv "$ROOT/runtime-requirements.txt" api_tcp_port)"
  [[ "$api_port" =~ ^[0-9]{1,5}$ ]] && ((api_port > 0 && api_port < 65536)) \
    || radp_install_die "Invalid api_tcp_port in runtime-requirements.txt."
  radp_install_log "Waiting for the configured API TCP port ($api_port)."
  api_ready=0
  for _ in $(seq 1 30); do
    if (exec 3<>/dev/tcp/127.0.0.1/"$api_port") >/dev/null 2>&1; then
      api_ready=1
      break
    fi
    sleep 2
  done
  ((api_ready == 1)) || radp_install_die "No TCP listener detected on 127.0.0.1:$api_port. Inspect Compose logs."

  printf '\nDEPLOYMENT SUCCESS\n'
  printf 'All services are running or exited successfully, and TCP port %s accepts connections.\n' "$api_port"
  printf 'This confirms offline installation only when the target network adapter was disconnected throughout installation.\n'
  printf 'Logs: cd %q && docker-compose logs --tail=100 (or use: docker compose logs --tail=100)\n' "$ROOT"
}

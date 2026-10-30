#!/usr/bin/env bash
###############################################################################
# Shared helpers for RADP offline preparation, packaging and installation.
###############################################################################

set -Eeuo pipefail
umask 077

radp_log() { printf '\n[radp-offline] %s\n' "$*"; }
radp_warn() { printf '\n[radp-offline][WARNING] %s\n' "$*" >&2; }
radp_die() { printf '\n[radp-offline][ERROR] %s\n' "$*" >&2; exit 1; }
radp_require_command() {
  command -v "$1" >/dev/null 2>&1 || radp_die "Required command not found: $1"
}
radp_require_file() {
  [[ -f "$1" ]] || radp_die "Required file not found: $1"
}
radp_require_dir() {
  [[ -d "$1" ]] || radp_die "Required directory not found: $1"
}
radp_require_root() {
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || radp_die "Run this script as root, for example: sudo $*"
}

radp_project_root_from_script() {
  local script_dir
  script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[1]}")" && pwd -P)"
  cd -- "$script_dir/../.." && pwd -P
}

radp_check_target_platform() {
  local root_os_release="$1"
  [[ -f /etc/os-release ]] || radp_die "Cannot identify the preparation host: /etc/os-release is missing."
  # shellcheck disable=SC1091
  . /etc/os-release
  [[ "${ID:-}" == "astra" ]] || radp_die "Expected Astra Linux; detected ID=${ID:-unknown}."
  [[ -f /etc/astra_version ]] || radp_die "Cannot verify Astra release: /etc/astra_version is missing."
  grep -q '1\.7\.8' /etc/astra_version || radp_die "This bundle is pinned to Astra Linux SE 1.7.8."
  [[ "$(dpkg --print-architecture)" == "amd64" ]] || radp_die "Expected dpkg architecture amd64."
  [[ "$(uname -m)" == "x86_64" ]] || radp_die "Expected machine architecture x86_64."
  cp /etc/os-release "$root_os_release"
}

radp_compose() {
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  elif docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    radp_die "Neither docker-compose nor the 'docker compose' plugin is available."
  fi
}

radp_compose_version() {
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose version 2>&1
  else
    docker compose version 2>&1
  fi
}

radp_verify_project_layout() {
  local root="$1"
  local required
  for required in pyproject.toml uv.lock docker/Dockerfile docker-compose.yml .env; do
    [[ -f "$root/$required" ]] || radp_die "Project file missing: $root/$required"
  done
  for required in radp html data; do
    [[ -d "$root/$required" ]] || radp_die "Project directory missing: $root/$required"
  done
  [[ -s "$root/.env" ]] || radp_die "Project .env is missing or empty."
  [[ ! -L "$root/.env" ]] || radp_die "Refusing to package a symlinked .env file."
}

radp_read_kv() {
  # Read a simple key=value manifest without evaluating it as shell code.
  local file="$1" key="$2"
  awk -F= -v wanted="$key" '$1 == wanted {sub(/^[^=]*=/, ""); print; exit}' "$file"
}

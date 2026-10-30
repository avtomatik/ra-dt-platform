#!/usr/bin/env bash
###############################################################################
# Install the RADP runtime bundle using Docker/Compose already provisioned by the host administrator.
###############################################################################
set -Eeuo pipefail
umask 077
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=./install-common.sh
source "$ROOT/install-common.sh"

radp_install_preflight partial
radp_install_check_host_packages
command -v systemctl >/dev/null 2>&1 || radp_install_die "systemctl is missing."
systemctl enable --now docker
docker info >/dev/null 2>&1 || radp_install_die "Docker daemon is not responding."
radp_install_decrypt_env
radp_install_deploy_runtime

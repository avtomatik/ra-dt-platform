#!/usr/bin/env bash
###############################################################################
# Install the self-contained RADP bundle, including Docker/Compose from local DEBs.
###############################################################################
set -Eeuo pipefail
umask 077
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=./install-common.sh
source "$ROOT/install-common.sh"

radp_install_preflight full
radp_install_full_os_packages
command -v systemctl >/dev/null 2>&1 || radp_install_die "systemctl is missing after OS package installation."
systemctl enable --now docker
docker info >/dev/null 2>&1 || radp_install_die "Docker daemon is not responding after installation."
radp_install_decrypt_env
radp_install_deploy_runtime

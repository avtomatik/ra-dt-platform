#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"
enter_project
###############################################################################
# Read the expected identity from our safely parsed configuration, never from
# verbose Compose config (which can include secrets).
###############################################################################
[[ "${DEPLOY_CONTAINER_UID:-}" =~ ^[1-9][0-9]*$ && "${DEPLOY_CONTAINER_GID:-}" =~ ^[1-9][0-9]*$ ]] || die 'Invalid DEPLOY_CONTAINER_UID / DEPLOY_CONTAINER_GID'
[[ -n "${DEPLOY_CONTAINER_USER:-}" ]] || die 'Missing DEPLOY_CONTAINER_USER'
expected="$DEPLOY_CONTAINER_USER:$DEPLOY_CONTAINER_UID:$DEPLOY_CONTAINER_GID"
actual="$(compose run --rm --no-deps -T --entrypoint /bin/sh platform -ec '
  u=$(id -un); i=$(id -u); g=$(id -g)
  home=$(getent passwd "$i" | cut -d: -f6)
  test "$HOME" = "$home" && test -d "$home" && test -w "$home"
  printf "%s:%s:%s\n" "$u" "$i" "$g"
')"
[[ "$actual" == "$expected" ]] || die "Identity mismatch: expected $expected, got $actual"
printf 'Verified identity: %s\n' "$actual"

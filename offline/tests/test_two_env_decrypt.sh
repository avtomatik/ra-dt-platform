#!/usr/bin/env bash
# Exercise real OpenSSL encryption / two-file installer decryption offline.
set -Eeuo pipefail
umask 077
TEST_ROOT="$(mktemp -d /tmp/radp-two-env-test.XXXXXX)"
trap 'rm -rf -- "$TEST_ROOT"' EXIT
OFFLINE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cp "$OFFLINE_DIR/lib/install-common.sh" "$TEST_ROOT/install-common.sh"
cp "$OFFLINE_DIR/../ops/lib/deployment-env.sh" "$TEST_ROOT/deployment-env.sh"
printf 'RADP_REMOTE_RA__BASE_URL=http://ra-server-name/api/ra/\n' >"$TEST_ROOT/.env"
printf 'DEPLOY_ENVIRONMENT=production\nDEPLOY_RA_HOST_IP=127.1.1.1\n' >"$TEST_ROOT/.env.compose"
printf 'services: {}\n' >"$TEST_ROOT/docker-compose.yml"
printf 'services: {}\n' >"$TEST_ROOT/docker-compose.production.yml"
for env_name in .env .env.compose; do
    printf 'secret-passphrase' | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 250000 -pass stdin \
        -in "$TEST_ROOT/$env_name" -out "$TEST_ROOT/$env_name.enc"
    sha256sum "$TEST_ROOT/$env_name" | awk '{print $1}' >"$TEST_ROOT/$env_name.sha256"
done
rm -f "$TEST_ROOT/.env" "$TEST_ROOT/.env.compose"
printf 'secret-passphrase\n' | bash -c '
  set -Eeuo pipefail
  source "$1/install-common.sh"
  radp_install_decrypt_env
  [[ "$DEPLOY_RA_HOSTNAME" == ra-server-name ]]
  [[ "${#RADP_COMPOSE_FILES[@]}" -eq 4 ]]
  [[ "$(stat -c %a "$ROOT/.env")" == 600 ]]
  [[ "$(stat -c %a "$ROOT/.env.compose")" == 600 ]]
' _ "$TEST_ROOT"
grep -q '^RADP_REMOTE_RA__BASE_URL=http://ra-server-name/api/ra/$' "$TEST_ROOT/.env"
grep -q '^DEPLOY_RA_HOST_IP=127.1.1.1$' "$TEST_ROOT/.env.compose"
printf 'PASS: decrypted and validated both environment files with 0600 permissions\n'

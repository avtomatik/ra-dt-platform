#!/usr/bin/env bash
# Run as root from the extracted ZIP directory: sudo ./install.sh
set -Eeuo pipefail
umask 077
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$ROOT"
fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
trap 'rc=$?; if ((rc != 0)); then printf "\nINSTALLATION FAILED (exit %s, line %s).\n" "$rc" "$LINENO" >&2; fi' EXIT
[[ $EUID -eq 0 ]] || fail "Run with sudo: sudo ./install.sh"
[[ -f SHA256SUMS ]] || fail "Missing SHA256SUMS."
sha256sum -c SHA256SUMS
for f in images.tar docker-compose.yml .env.enc install.sh target-platform.txt compose-images.txt; do
  [[ -s "$ROOT/$f" ]] || fail "Missing/empty bundle file: $f"
done
[[ "$(cat "$ROOT/target-platform.txt")" == linux/amd64 ]] || fail "Bundle is not linux/amd64."
[[ ! -e "$ROOT/.env" ]] || fail "Plaintext .env is unexpectedly present in bundle."
[[ -f /etc/astra_version ]] && grep -q '1\.7\.8' /etc/astra_version || fail "Target must be Astra Linux SE 1.7.8."
[[ "$(dpkg --print-architecture)" == amd64 && "$(uname -m)" == x86_64 ]] || fail "Target architecture must be amd64/x86_64."
command -v apt-get >/dev/null || fail "apt-get not found."
shopt -s nullglob
debs=("$ROOT"/docker-install/debs/*.deb)
((${#debs[@]} > 0)) || fail "No bundled .deb files."
printf '\nInstalling bundled packages with downloads disabled...\n'
DEBIAN_FRONTEND=noninteractive apt-get --no-download --yes install "${debs[@]}" \
  || fail "Local package installation failed. Missing dependencies or target baseline mismatch; network downloads were disabled."
command -v docker >/dev/null || fail "Docker package did not install docker."
command -v docker-compose >/dev/null || fail "Docker package did not install docker-compose."
[[ "$(docker --version)" == *"25.0.5"* ]] || fail "Unexpected Docker version: $(docker --version)"
grep -q '1\.29\.2' <<<"$(docker-compose version 2>&1)" || fail "Expected docker-compose 1.29.2."
systemctl enable --now docker
docker info >/dev/null || fail "Docker daemon is not responding."

# Decrypt .env only after package and checksum checks. Existing .env is never
# overwritten; this installer is for a fresh deployment.
if [[ -e "$ROOT/.env" ]]; then
  fail "A .env already exists in this directory. Move to a fresh extracted directory; installer will not overwrite it."
fi
read -r -s -p 'Passphrase used to encrypt .env: ' env_pass; printf '\n'
[[ -n "$env_pass" ]] || fail "Empty passphrase is not allowed."
tmp_env="$ROOT/.env.tmp.$$"
printf '%s' "$env_pass" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 250000 -pass stdin \
  -in "$ROOT/.env.enc" -out "$tmp_env" || { rm -f "$tmp_env"; unset env_pass; fail "Decryption failed; check passphrase."; }
unset env_pass
[[ -s "$tmp_env" ]] || { rm -f "$tmp_env"; fail "Decrypted .env is empty."; }
chmod 0600 "$tmp_env"
mv "$tmp_env" "$ROOT/.env"

# Ensure Compose cannot trigger builds; Compose v1.29.2 has no --pull never.
if grep -Eq '^[[:space:]]*build[[:space:]]*:' "$ROOT/docker-compose.yml"; then
  fail "Compose file contains build:. Offline deployment must use prebuilt images."
fi
(cd "$ROOT" && docker-compose config -q) || fail "Compose config validation failed."
mapfile -t expected_images < "$ROOT/compose-images.txt"
mapfile -t configured_images < <(cd "$ROOT" && docker-compose config --images | sort -u)
((${#configured_images[@]} > 0)) || fail "Compose reports no images."
# Require the image references to match those captured at preparation time.
printf '%s\n' "${configured_images[@]}" | sort -u > "$ROOT/.configured-images.tmp"
printf '%s\n' "${expected_images[@]}" | sort -u > "$ROOT/.expected-images.tmp"
cmp -s "$ROOT/.configured-images.tmp" "$ROOT/.expected-images.tmp" || fail "Compose image list differs from the packaged image manifest."
rm -f "$ROOT/.configured-images.tmp" "$ROOT/.expected-images.tmp"

printf '\nLoading bundled images...\n'
docker image load --input "$ROOT/images.tar"
while IFS= read -r img; do
  [[ -n "$img" ]] || continue
  docker image inspect "$img" >/dev/null || fail "Image missing after load: $img"
  platform="$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$img")"
  [[ "$platform" == linux/amd64 ]] || fail "Image $img platform is $platform."
done < "$ROOT/compose-images.txt"

printf '\nStarting Compose services using already-loaded images...\n'
# No pull flag is used: it is unsupported by Compose v1.29.2. Every configured
# image is verified locally first, and --no-build prevents local builds.
(cd "$ROOT" && docker-compose up -d --no-build)
sleep 5
(cd "$ROOT" && docker-compose ps)
# Verify every service container is running or has exited successfully as a
# one-shot init job. Use actual Compose service names rather than guessed names.
mapfile -t services < <(cd "$ROOT" && docker-compose config --services)
for service in "${services[@]}"; do
  mapfile -t ids < <(cd "$ROOT" && docker-compose ps -q -a "$service")
  ((${#ids[@]} > 0)) || fail "No container was created for Compose service '$service'."
  for id in "${ids[@]}"; do
    state="$(docker inspect --format '{{.State.Status}}' "$id")"
    exit_code="$(docker inspect --format '{{.State.ExitCode}}' "$id")"
    if [[ "$state" == exited && "$exit_code" == 0 ]]; then
      continue
    fi
    [[ "$state" == running ]] || { docker logs --tail=80 "$id" >&2 || true; fail "Service '$service' container state is $state (exit=$exit_code)."; }
  done
done
# The known host API port is 8000. Check TCP only; no health endpoint is assumed.
api_ready=0
for _ in $(seq 1 30); do
  if (exec 3<>/dev/tcp/127.0.0.1/8000) >/dev/null 2>&1; then api_ready=1; break; fi
  sleep 2
done
((api_ready == 1)) || fail "No TCP listener detected on 127.0.0.1:8000. Check docker-compose logs."
printf '\nDEPLOYMENT SUCCESS\n'
printf 'Compose services were created; all service containers are running or exited successfully; TCP port 8000 accepts connections.\n'
printf 'OFFLINE TEST SUCCESS may be recorded only if this installation was performed with the target VM network adapter disconnected.\n'
printf 'Diagnostics: cd %q && docker-compose logs --tail=100\n' "$ROOT"

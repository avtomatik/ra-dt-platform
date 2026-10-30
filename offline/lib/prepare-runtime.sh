#!/usr/bin/env bash
###############################################################################
# Shared application/image preparation used by both full and partial modes.
###############################################################################

radp_prepare_runtime_assets() {
  local root="$1" stage="$2" mode="$3" installer="$4" install_common="$5"
  local build_context compose_output image ref platform image_id repo_digests
  local postgres_source ofelia_source env_pass_1 env_pass_2 env_tmp
  local -a compose_images=()

  radp_verify_project_layout "$root"
  radp_require_command docker
  radp_require_command openssl
  radp_require_command tar
  radp_require_command python3
  radp_require_command sha256sum
  radp_compose version >/dev/null 2>&1 || radp_die "Docker Compose is not usable."
  docker info >/dev/null 2>&1 || radp_die "Docker daemon is not responding on the preparation host."

  radp_log "Validating the project's Compose configuration."
  (cd "$root" && radp_compose config -q) || radp_die "Compose configuration is invalid."
  compose_output="$(cd "$root" && radp_compose config)"
  mapfile -t compose_images < <(printf '%s\n' "$compose_output" | awk '$1 == "image:" {gsub(/"/, "", $2); print $2}' | sort -u)
  ((${#compose_images[@]} > 0)) || radp_die "No image references were found in normalized Compose configuration."
  if grep -Eq '^[[:space:]]*build[[:space:]]*:' "$root/docker-compose.yml"; then
    radp_die "docker-compose.yml contains build:. The offline deployment must refer only to prebuilt images."
  fi
  printf '%s\n' "${compose_images[@]}" > "$stage/compose-images.txt"

  # Build in a clean context that deliberately excludes secrets and the offline
  # packaging workspace. The image itself is then exported into images.tar.
  build_context="$(mktemp -d /tmp/radp-offline-build.XXXXXX)"
  env_tmp=""
  cleanup_prepare_runtime() {
    [[ -z "$build_context" || ! -d "$build_context" ]] || rm -rf -- "$build_context"
    [[ -z "$env_tmp" || ! -e "$env_tmp" ]] || rm -f -- "$env_tmp"
  }
  trap cleanup_prepare_runtime RETURN

  radp_log "Creating a secret-free Docker build context."
  tar -C "$root" \
    --exclude='./.git' \
    --exclude='./.env' --exclude='./.env.*' \
    --exclude='./offline' --exclude='./release' \
    --exclude='./.venv' --exclude='./__pycache__' \
    --exclude='*/__pycache__' --exclude='*.pyc' \
    -cf - . | tar -C "$build_context" -xf -
  [[ ! -e "$build_context/.env" ]] || radp_die ".env leaked into the Docker build context."

  radp_log "Building the RADP application image for linux/amd64."
  mutable_bases="$(awk 'toupper($1) == "FROM" { for (i = 2; i <= NF; i++) { if ($i == "AS") break; if ($i ~ /^--platform=/) continue; if ($i !~ /@sha256:/) print $i } }' "$root/docker/Dockerfile")"
  if [[ -n "$mutable_bases" ]]; then
    radp_warn "Dockerfile FROM references are not all digest-pinned: $(tr '\n' ' ' <<<"$mutable_bases"). Pin base images by digest for repeatable future builds."
  fi
  docker build --pull --platform linux/amd64 -t radp:offline-build \
    -f "$build_context/docker/Dockerfile" "$build_context"

  postgres_source="${RADP_POSTGRES_IMAGE_SOURCE:-postgres:17}"
  ofelia_source="${RADP_OFELIA_IMAGE_SOURCE:-mcuadros/ofelia:latest}"
  [[ "$postgres_source" == *@sha256:* ]] || radp_warn \
    "PostgreSQL source '$postgres_source' is tag-based. For repeatable future builds, set RADP_POSTGRES_IMAGE_SOURCE to the recorded repository digest."
  [[ "$ofelia_source" == *@sha256:* ]] || radp_warn \
    "Ofelia source '$ofelia_source' is tag-based. For repeatable future builds, set RADP_OFELIA_IMAGE_SOURCE to the recorded repository digest."
  radp_log "Pulling the configured PostgreSQL image: $postgres_source"
  docker pull --platform linux/amd64 "$postgres_source"
  radp_log "Pulling the configured Ofelia image: $ofelia_source"
  docker pull --platform linux/amd64 "$ofelia_source"

  : > "$stage/image-manifest.tsv"
  printf 'compose_reference\timage_id\tplatform\trepository_digests\n' >> "$stage/image-manifest.tsv"

  for ref in "${compose_images[@]}"; do
    case "$ref" in
      postgres:17|*/postgres:17)
        docker image tag "$postgres_source" "$ref"
        ;;
      mcuadros/ofelia:latest|*/mcuadros/ofelia:latest)
        docker image tag "$ofelia_source" "$ref"
        ;;
      *radp*)
        docker image tag radp:offline-build "$ref"
        ;;
      *)
        docker image inspect "$ref" >/dev/null 2>&1 || radp_die \
          "Compose references '$ref', but it is neither a mapped image nor already present locally. Supply it on the preparation host and retry."
        ;;
    esac

    docker image inspect "$ref" >/dev/null 2>&1 || radp_die "Required image is unavailable: $ref"
    platform="$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$ref")"
    [[ "$platform" == "linux/amd64" ]] || radp_die "Image $ref has platform $platform; expected linux/amd64."
    image_id="$(docker image inspect --format '{{.Id}}' "$ref")"
    repo_digests="$(docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$ref" | paste -sd ';' -)"
    printf '%s\t%s\t%s\t%s\n' "$ref" "$image_id" "$platform" "$repo_digests" >> "$stage/image-manifest.tsv"
  done

  radp_log "Exporting all Compose images."
  docker image save --output "$stage/images.tar" "${compose_images[@]}"
  docker image inspect "${compose_images[@]}" > "$stage/image-metadata.json"

  radp_log "Copying runtime configuration and application data."
  cp "$root/docker-compose.yml" "$stage/docker-compose.yml"
  mkdir -p "$stage/data" "$stage/html"
  cp -a "$root/data/." "$stage/data/"
  cp -a "$root/html/." "$stage/html/"
  cp "$installer" "$stage/install.sh"
  cp "$install_common" "$stage/install-common.sh"
  chmod 0755 "$stage/install.sh" "$stage/install-common.sh"

  radp_log "Encrypting .env for transport."
  read -r -s -p 'Passphrase to encrypt .env for the offline bundle: ' env_pass_1; printf '\n'
  read -r -s -p 'Repeat passphrase: ' env_pass_2; printf '\n'
  [[ -n "$env_pass_1" && "$env_pass_1" == "$env_pass_2" ]] || radp_die "Passphrases are empty or do not match."
  printf '%s' "$env_pass_1" | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 250000 -pass stdin \
    -in "$root/.env" -out "$stage/.env.enc"
  sha256sum "$root/.env" | awk '{print $1}' > "$stage/.env.sha256"

  env_tmp="$(mktemp /tmp/radp-offline-env-check.XXXXXX)"
  printf '%s' "$env_pass_1" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 250000 -pass stdin \
    -in "$stage/.env.enc" -out "$env_tmp"
  cmp -s "$root/.env" "$env_tmp" || radp_die "Encrypted .env verification failed."
  rm -f -- "$env_tmp"
  env_tmp=""
  unset env_pass_1 env_pass_2
  [[ ! -e "$stage/.env" ]] || radp_die "Plaintext .env must not be present in staging."

  cat > "$stage/target-platform.txt" <<'PLATFORM'
Astra Linux SE 1.7.8
linux/amd64
PLATFORM
  cat > "$stage/runtime-requirements.txt" <<REQUIREMENTS
astra_release=1.7.8
architecture=amd64
platform=linux/amd64
docker_cli_version=${RADP_EXPECTED_DOCKER_VERSION:-25.0.5}
compose_version=${RADP_EXPECTED_COMPOSE_VERSION:-1.29.2}
api_tcp_port=8000
REQUIREMENTS
  printf 'mode=%s\n' "$mode" > "$stage/bundle-mode.txt"

  cleanup_prepare_runtime
  trap - RETURN
}

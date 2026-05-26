#!/usr/bin/env bash
set -euo pipefail

export DOCKER_BUILDKIT=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

VERSION="latest"
IMAGE="ra-ds-explorer:${VERSION}"

echo "[BUILD] version: $VERSION"

echo "[BUILD] building image: $IMAGE"

docker build \
  --pull \
  -t "$IMAGE" \
  -f "$ROOT_DIR/docker/Dockerfile" \
  "$ROOT_DIR"

echo "[DONE] built $IMAGE"

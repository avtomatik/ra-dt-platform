#!/usr/bin/env bash
###############################################################################
# End-to-end fixture test for FULL/PARTIAL ZIP assembly and checksum manifests.
###############################################################################
set -Eeuo pipefail
umask 077

SCRIPT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
TEST_ROOT="$(mktemp -d /tmp/radp-package-builder-test.XXXXXX)"
cleanup() { rm -rf -- "$TEST_ROOT"; }
trap cleanup EXIT

mkdir -p "$TEST_ROOT/offline/lib" "$TEST_ROOT/release/radp-offline-partial"
cp "$SCRIPT_ROOT/lib/verify-image-archive.py" "$TEST_ROOT/offline/lib/"
cp "$SCRIPT_ROOT/lib/common.sh" "$TEST_ROOT/offline/lib/"
cp "$SCRIPT_ROOT/lib/package-common.sh" "$TEST_ROOT/offline/lib/"

create_stage() {
  local mode="$1" stage="$2"
  mkdir -p "$stage"
  printf 'version: "3.8"\nservices:\n  fixture:\n    image: radp-test:offline\n' > "$stage/docker-compose.yml"
  printf 'opaque-encrypted-fixture\n' > "$stage/.env.enc"
  printf '%s\n' "$(printf 'TEST_SECRET=fixture\n' | sha256sum | awk '{print $1}')" > "$stage/.env.sha256"
  cp "$SCRIPT_ROOT/$mode/install.sh" "$stage/install.sh"
  cp "$SCRIPT_ROOT/lib/install-common.sh" "$stage/install-common.sh"
  chmod 0755 "$stage/install.sh" "$stage/install-common.sh"
  printf 'Astra Linux SE 1.7.8\nlinux/amd64\n' > "$stage/target-platform.txt"
  printf 'radp-test:offline\n' > "$stage/compose-images.txt"
  printf 'compose_reference\timage_id\tplatform\trepository_digests\n' > "$stage/image-manifest.tsv"
  printf 'runtime-requirements=fixture\n' > "$stage/runtime-requirements.txt"
  printf 'mode=%s\n' "$mode" > "$stage/bundle-mode.txt"
  if [[ "$mode" == "partial" ]]; then
    printf 'Required Docker/Compose host packages are provisioned externally.\n' > "$stage/HOST-REQUIREMENTS.txt"
  else
    printf 'docker_package=docker.io\ndocker_version=25.0.5.astra3+ci24\ncompose_package=docker-compose\ncompose_version=1.29.2-1astra.se1+ci1+b2\n' > "$stage/os-packages.txt"
  fi

  python3 - "$stage" <<'PY'
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path

stage = Path(sys.argv[1])
config = b'{"architecture":"amd64","os":"linux","config":{"Labels":{"fixture":"true"}}}'
image_id = "sha256:" + hashlib.sha256(config).hexdigest()
(stage / "image-manifest.tsv").write_text(
    "compose_reference\timage_id\tplatform\trepository_digests\n"
    + f"radp-test:offline\t{image_id}\tlinux/amd64\t\n",
    encoding="utf-8",
)
with tarfile.open(stage / "images.tar", "w") as archive:
    manifest = json.dumps([{"Config": "fixture-config.json", "RepoTags": ["radp-test:offline"], "Layers": []}]).encode()
    item = tarfile.TarInfo("manifest.json")
    item.size = len(manifest)
    archive.addfile(item, io.BytesIO(manifest))
    item = tarfile.TarInfo("fixture-config.json")
    item.size = len(config)
    archive.addfile(item, io.BytesIO(config))
PY
}

PARTIAL_STAGE="$TEST_ROOT/release/radp-offline-partial"
create_stage partial "$PARTIAL_STAGE"

bash -c '
  set -Eeuo pipefail
  source "$1/offline/lib/common.sh"
  source "$1/offline/lib/package-common.sh"
  radp_package_bundle partial "$1"
' _ "$TEST_ROOT"

mkdir -p "$TEST_ROOT/release/radp-offline-full/docker-install/debs"
FULL_STAGE="$TEST_ROOT/release/radp-offline-full"
create_stage full "$FULL_STAGE"
mkdir -p "$FULL_STAGE/docker-install/debs"
printf 'Package: docker.io\nVersion: 25.0.5.astra3+ci24\nArchitecture: amd64\n' > "$FULL_STAGE/docker-install/debs/Packages"
gzip -c "$FULL_STAGE/docker-install/debs/Packages" > "$FULL_STAGE/docker-install/debs/Packages.gz"
printf 'Origin: RADP fixture\n' > "$FULL_STAGE/docker-install/debs/Release"
printf 'package\tversion\tarchitecture\tfilename\ndocker.io\t25.0.5.astra3+ci24\tamd64\tdocker.io.deb\n' > "$FULL_STAGE/docker-install/package-inventory.tsv"
printf 'deb https://example.invalid/astra frozen main\n' > "$FULL_STAGE/docker-install/frozen-sources.list"
printf 'fixture deb archive\n' > "$FULL_STAGE/docker-install/debs/docker.io.deb"

bash -c '
  set -Eeuo pipefail
  source "$1/offline/lib/common.sh"
  source "$1/offline/lib/package-common.sh"
  radp_package_bundle full "$1"
' _ "$TEST_ROOT"

for mode in full partial; do
  archive="$TEST_ROOT/release/radp-offline-$mode.zip"
  checksum="$archive.sha256"
  [[ -s "$archive" && -s "$checksum" ]]
  (cd "$TEST_ROOT/release" && sha256sum -c "radp-offline-$mode.zip.sha256")
  python3 - "$archive" "$mode" <<'PY'
from pathlib import PurePosixPath
from zipfile import ZipFile
import sys
archive, mode = sys.argv[1:]
prefix = f"radp-offline-{mode}/"
with ZipFile(archive) as zf:
    names = zf.namelist()
    assert all(name.startswith(prefix) for name in names)
    assert not any(PurePosixPath(name).name == ".env" for name in names)
    assert zf.testzip() is None
    for name in (prefix + "install.sh", prefix + "install-common.sh"):
        assert ((zf.getinfo(name).external_attr >> 16) & 0o111) != 0
    if mode == "partial":
        assert not any(name.endswith(".deb") or "/docker-install/" in name for name in names)
    else:
        assert any(name.endswith(".deb") for name in names)
PY
done

printf 'PASS: FULL/PARTIAL ZIP contents, modes, embedded checksums and external SHA-256 sidecars\n'

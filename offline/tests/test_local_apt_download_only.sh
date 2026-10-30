#!/usr/bin/env bash
###############################################################################
# Regression test: prove local-only APT download resolution and missing-DEB detection.
###############################################################################
set -Eeuo pipefail
umask 022

for command_name in apt-get dpkg-deb python3; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'SKIP: required command is missing: %s\n' "$command_name"
    exit 0
  }
done
if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  printf 'SKIP: run this APT fixture test as root.\n'
  exit 0
fi

TEST_ROOT="$(mktemp -d /tmp/radp-apt-download-test.XXXXXX)"
cleanup() { rm -rf -- "$TEST_ROOT"; }
trap cleanup EXIT
REPO="$TEST_ROOT/repo"
mkdir -p "$REPO" "$TEST_ROOT/build-dep/DEBIAN" "$TEST_ROOT/build-root/DEBIAN"
chmod 0755 "$TEST_ROOT/build-dep" "$TEST_ROOT/build-dep/DEBIAN" \
  "$TEST_ROOT/build-root" "$TEST_ROOT/build-root/DEBIAN"

cat > "$TEST_ROOT/build-dep/DEBIAN/control" <<'CONTROL'
Package: radp-apt-fixture-dep
Version: 1.0
Architecture: amd64
Maintainer: RADP Test <radp-test@example.invalid>
Description: fixture dependency for offline APT verification
CONTROL
cat > "$TEST_ROOT/build-root/DEBIAN/control" <<'CONTROL'
Package: radp-apt-fixture-root
Version: 1.0
Architecture: amd64
Maintainer: RADP Test <radp-test@example.invalid>
Depends: radp-apt-fixture-dep (>= 1.0)
Description: fixture root package for offline APT verification
CONTROL

dpkg-deb --build "$TEST_ROOT/build-dep" "$REPO/radp-apt-fixture-dep_1.0_amd64.deb" >/dev/null
dpkg-deb --build "$TEST_ROOT/build-root" "$REPO/radp-apt-fixture-root_1.0_amd64.deb" >/dev/null

python3 - "$REPO" <<'PY'
from datetime import datetime, timezone
from email.utils import format_datetime
from hashlib import md5, sha256
from pathlib import Path
import gzip
import subprocess
import sys

repo = Path(sys.argv[1])
records = []
for archive in sorted(repo.glob("*.deb")):
    control = subprocess.check_output(["dpkg-deb", "-f", str(archive)], text=True).rstrip()
    payload = archive.read_bytes()
    records.append(
        control + "\n"
        + f"Filename: ./{archive.name}\n"
        + f"Size: {len(payload)}\n"
        + f"MD5sum: {md5(payload).hexdigest()}\n"
        + f"SHA256: {sha256(payload).hexdigest()}\n"
    )
packages = "\n".join(records) + "\n"
(repo / "Packages").write_text(packages, encoding="utf-8")
with (repo / "Packages.gz").open("wb") as output:
    with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0, compresslevel=9) as zipped:
        zipped.write(packages.encode())
release_date = format_datetime(datetime.now(timezone.utc), usegmt=True)
lines = [
    f"Date: {release_date}", "Origin: RADP test", "Label: RADP test",
    "Suite: test", "Codename: test", "Architectures: amd64", "Components: main",
    "Description: RADP local APT fixture", "MD5Sum:",
]
for name in ("Packages", "Packages.gz"):
    data = (repo / name).read_bytes()
    lines.append(f" {md5(data).hexdigest()} {len(data):16d} {name}")
lines.append("SHA256:")
for name in ("Packages", "Packages.gz"):
    data = (repo / name).read_bytes()
    lines.append(f" {sha256(data).hexdigest()} {len(data):16d} {name}")
(repo / "Release").write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

verify_local_only() {
  local tag="$1"
  local state="$TEST_ROOT/state-$tag"
  mkdir -p "$state/lists/partial" "$state/archives/partial"
  printf 'deb [trusted=yes] file:%s ./\n' "$REPO" > "$state/sources.list"
  local -a opts=(
    -o "Dir::Etc::sourcelist=$state/sources.list"
    -o "Dir::Etc::sourceparts=/dev/null"
    -o "Dir::State::lists=$state/lists"
    -o "Dir::State::status=/dev/null"
    -o "Dir::Cache::pkgcache=$state/pkgcache.bin"
    -o "Dir::Cache::srcpkgcache=$state/srcpkgcache.bin"
    -o "Dir::Cache::archives=$state/archives"
    -o "Dir::Cache::archives::partial=$state/archives/partial"
    -o "Acquire::Languages=none"
    -o "APT::Architecture=amd64"
    -o "APT::Sandbox::User=root"
  )
  apt-get "${opts[@]}" update >"$state/update.log" 2>&1
  DEBIAN_FRONTEND=noninteractive apt-get "${opts[@]}" \
    --download-only --reinstall --yes --no-install-recommends install \
    radp-apt-fixture-root=1.0 >"$state/resolve.log" 2>&1
}

if ! verify_local_only good; then
  cat "$TEST_ROOT/state-good/update.log" "$TEST_ROOT/state-good/resolve.log" >&2
  exit 1
fi

###############################################################################
# Keep the package index intact but remove one referenced DEB. A local-only
# download-only resolve must fail rather than silently treating it as installed.
###############################################################################
rm -f "$REPO/radp-apt-fixture-dep_1.0_amd64.deb"
if verify_local_only missing-deb; then
  printf 'FAIL: APT accepted an index entry whose DEB file is missing.\n' >&2
  cat "$TEST_ROOT/state-missing-deb/resolve.log" >&2
  exit 1
fi

printf 'PASS: local APT download-only resolution succeeds and detects a missing dependency DEB\n'

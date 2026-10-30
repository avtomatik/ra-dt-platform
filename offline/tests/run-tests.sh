#!/usr/bin/env bash
###############################################################################
# Run offline tooling checks that do not require Astra repositories or Docker.
###############################################################################
set -Eeuo pipefail

OFFLINE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
TEST_DIR="$OFFLINE_DIR/tests"

printf '[tests] Checking Bash syntax...\n'
while IFS= read -r -d '' script; do
  bash -n "$script"
done < <(find "$OFFLINE_DIR" -type f -name '*.sh' -print0 | LC_ALL=C sort -z)

printf '[tests] Checking Python syntax...\n'
python3 - "$OFFLINE_DIR" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
for path in sorted(root.rglob("*.py")):
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
print("Python syntax OK")
PY

printf '[tests] Checking exported Docker image manifest validation...\n'
python3 "$TEST_DIR/test_verify_image_archive.py"

printf '[tests] Checking FULL/PARTIAL package creation...\n'
"$TEST_DIR/test_package_builder.sh"

printf '[tests] Checking isolated local APT download-only resolution...\n'
"$TEST_DIR/test_local_apt_download_only.sh"

printf '\nALL OFFLINE TOOLING TESTS PASSED (Astra target installation not exercised).\n'

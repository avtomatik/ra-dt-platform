#!/usr/bin/env python3
"""Regression tests for Compose-reference validation against docker save output."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HELPER = (
    Path(__file__).resolve().parents[1] / "lib" / "verify-image-archive.py"
)


def build_fixture(root: Path) -> tuple[Path, Path, Path, dict[str, bytes]]:
    archive_path = root / "images.tar"
    compose_path = root / "compose-images.txt"
    manifest_path = root / "image-manifest.tsv"

    configs = {
        "radp-api:offline": b'{"architecture":"amd64","os":"linux","config":{"Labels":{"test":"api"}}}',
        "postgres:17": b'{"architecture":"amd64","os":"linux","config":{"Labels":{"test":"postgres"}}}',
    }
    archive_manifest = []
    rows = ["compose_reference\timage_id\tplatform\trepository_digests"]
    for index, (reference, config) in enumerate(configs.items(), start=1):
        config_name = f"config-{index}.json"
        image_id = "sha256:" + hashlib.sha256(config).hexdigest()
        archive_manifest.append(
            {"Config": config_name, "RepoTags": [reference], "Layers": []}
        )
        rows.append(f"{reference}\t{image_id}\tlinux/amd64\t")

    compose_path.write_text("\n".join(configs) + "\n", encoding="utf-8")
    manifest_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    with tarfile.open(archive_path, "w") as tar:
        payload = json.dumps(archive_manifest).encode()
        member = tarfile.TarInfo("manifest.json")
        member.size = len(payload)
        import io

        tar.addfile(member, io.BytesIO(payload))
        for index, config in enumerate(configs.values(), start=1):
            member = tarfile.TarInfo(f"config-{index}.json")
            member.size = len(config)
            tar.addfile(member, io.BytesIO(config))
    return archive_path, compose_path, manifest_path, configs


def invoke(
    archive: Path, compose: Path, manifest: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(HELPER),
            str(archive),
            str(compose),
            str(manifest),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(
        prefix="radp-image-manifest-test."
    ) as tmp:
        root = Path(tmp)
        archive, compose, manifest, _ = build_fixture(root)

        result = invoke(archive, compose, manifest)
        if result.returncode != 0:
            raise AssertionError(
                f"valid image archive was rejected:\n{result.stdout}\n{result.stderr}"
            )

        # A tag missing from the exported Docker manifest must be rejected.
        entries = [
            {
                "Config": "config-1.json",
                "RepoTags": ["radp-api:offline"],
                "Layers": [],
            },
            {"Config": "config-2.json", "RepoTags": [], "Layers": []},
        ]
        import io

        with tarfile.open(archive, "w") as tar:
            payload = json.dumps(entries).encode()
            member = tarfile.TarInfo("manifest.json")
            member.size = len(payload)
            tar.addfile(member, io.BytesIO(payload))
            for index, config in enumerate(
                [
                    b'{"architecture":"amd64","os":"linux","config":{"Labels":{"test":"api"}}}',
                    b'{"architecture":"amd64","os":"linux","config":{"Labels":{"test":"postgres"}}}',
                ],
                start=1,
            ):
                member = tarfile.TarInfo(f"config-{index}.json")
                member.size = len(config)
                tar.addfile(member, io.BytesIO(config))
        result = invoke(archive, compose, manifest)
        if result.returncode == 0 or "does not appear" not in result.stderr:
            raise AssertionError("missing Compose image tag was not rejected")

        # A tampered config must fail even if its tag still appears.
        with tarfile.open(archive, "w") as tar:
            entries[1]["RepoTags"] = ["postgres:17"]
            payload = json.dumps(entries).encode()
            member = tarfile.TarInfo("manifest.json")
            member.size = len(payload)
            tar.addfile(member, io.BytesIO(payload))
            configs = [
                b'{"tampered":true}',
                b'{"architecture":"amd64","os":"linux","config":{"Labels":{"test":"postgres"}}}',
            ]
            for index, config in enumerate(configs, start=1):
                member = tarfile.TarInfo(f"config-{index}.json")
                member.size = len(config)
                tar.addfile(member, io.BytesIO(config))
        result = invoke(archive, compose, manifest)
        if (
            result.returncode == 0
            or "is not present in images.tar" not in result.stderr
        ):
            raise AssertionError("tampered image config was not rejected")

    print(
        "PASS: exported image manifest checks references and archived image IDs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

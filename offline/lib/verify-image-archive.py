#!/usr/bin/env python3
"""Verify that Compose image references are present in a Docker image archive."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import tarfile
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def read_lines(path: Path) -> list[str]:
    try:
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
        ]
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")
    return [line for line in lines if line]


def load_expected(
    compose_file: Path, manifest_file: Path
) -> dict[str, dict[str, str]]:
    references = read_lines(compose_file)
    if not references:
        fail("compose-images.txt is empty")
    if len(references) != len(set(references)):
        fail("compose-images.txt contains duplicate references")

    expected: dict[str, dict[str, str]] = {}
    try:
        with manifest_file.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            required = {
                "compose_reference",
                "image_id",
                "platform",
                "repository_digests",
            }
            if set(reader.fieldnames or ()) != required:
                fail("image-manifest.tsv has an unexpected header")
            for row in reader:
                reference = (row.get("compose_reference") or "").strip()
                image_id = (row.get("image_id") or "").strip()
                platform = (row.get("platform") or "").strip()
                digests = (row.get("repository_digests") or "").strip()
                if (
                    not reference
                    or not image_id.startswith("sha256:")
                    or platform != "linux/amd64"
                ):
                    fail(
                        f"invalid image-manifest.tsv row for {reference or '<empty reference>'}"
                    )
                if reference in expected:
                    fail(
                        f"duplicate image-manifest.tsv reference: {reference}"
                    )
                expected[reference] = {
                    "image_id": image_id,
                    "repository_digests": digests,
                }
    except OSError as exc:
        fail(f"cannot read {manifest_file}: {exc}")

    if set(expected) != set(references):
        missing = sorted(set(references) - set(expected))
        extra = sorted(set(expected) - set(references))
        details = []
        if missing:
            details.append("missing manifest rows: " + ", ".join(missing))
        if extra:
            details.append("unexpected manifest rows: " + ", ".join(extra))
        fail(
            "Compose references and image-manifest.tsv differ ("
            + "; ".join(details)
            + ")"
        )
    return expected


def verify_archive(
    archive_path: Path,
    expected: dict[str, dict[str, str]],
) -> None:
    try:
        with tarfile.open(archive_path, mode="r:*") as archive:
            try:
                manifest_member = archive.getmember("manifest.json")
            except KeyError:
                fail("images.tar does not contain manifest.json")
            manifest_stream = archive.extractfile(manifest_member)
            if manifest_stream is None:
                fail("cannot read manifest.json from images.tar")
            try:
                manifest = json.load(manifest_stream)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                fail(f"images.tar manifest.json is invalid: {exc}")

            if not isinstance(manifest, list) or not manifest:
                fail("images.tar manifest.json is not a non-empty image list")

            exported: dict[str, set[str]] = {}
            for index, item in enumerate(manifest):
                if not isinstance(item, dict):
                    fail(f"invalid image entry at manifest index {index}")
                config_path = item.get("Config")
                if not isinstance(config_path, str) or not config_path:
                    fail(f"image entry {index} has no Config path")
                try:
                    config_member = archive.getmember(config_path)
                except KeyError:
                    fail(
                        f"image config is missing from images.tar: {config_path}"
                    )
                config_stream = archive.extractfile(config_member)
                if config_stream is None:
                    fail(
                        f"cannot read image config from images.tar: {config_path}"
                    )
                image_id = (
                    "sha256:"
                    + hashlib.sha256(config_stream.read()).hexdigest()
                )
                tags = item.get("RepoTags") or []
                if not isinstance(tags, list) or any(
                    not isinstance(tag, str) for tag in tags
                ):
                    fail(f"invalid RepoTags value at manifest index {index}")
                exported[image_id] = set(tags) | exported.get(image_id, set())

    except (OSError, tarfile.TarError) as exc:
        fail(f"cannot inspect Docker image archive {archive_path}: {exc}")

    exported_ids = set(exported)
    for reference, row in expected.items():
        image_id = row["image_id"]
        if image_id not in exported_ids:
            fail(
                f"Compose image {reference} ({image_id}) is not present in images.tar"
            )

        if reference in exported[image_id]:
            continue

        recorded_digests = set(
            filter(None, row["repository_digests"].split(";"))
        )
        # Digest references do not necessarily appear under RepoTags in the
        # docker-archive manifest. Their inspected repository digest is tied to
        # the exact image ID, which was just verified from the archived config.
        if reference.startswith("sha256:") and reference == image_id:
            continue
        if reference in recorded_digests:
            continue
        fail(
            f"Compose reference {reference} does not appear in images.tar RepoTags "
            "or in its recorded repository digests"
        )


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: verify-image-archive.py IMAGES_TAR COMPOSE_IMAGES IMAGE_MANIFEST_TSV",
            file=sys.stderr,
        )
        return 2

    archive_path, compose_path, manifest_path = map(Path, sys.argv[1:])
    expected = load_expected(compose_path, manifest_path)
    verify_archive(archive_path, expected)
    print(
        f"Verified {len(expected)} Compose image reference(s) against images.tar manifest.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

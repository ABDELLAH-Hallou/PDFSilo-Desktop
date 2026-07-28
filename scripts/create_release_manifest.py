"""Create checksum and signature metadata for release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest for *path*."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def create_manifest(
    *,
    version: str,
    tag: str,
    commit: str,
    assets: list[Path],
    signature_metadata: Path,
) -> dict[str, Any]:
    """Build a release manifest from final, already-signed artifacts."""
    signatures = json.loads(signature_metadata.read_text(encoding="utf-8"))
    if not isinstance(signatures, dict):
        raise ValueError("Signature metadata must be a JSON object.")
    records = []
    for asset in sorted(assets, key=lambda item: item.name.lower()):
        if not asset.is_file():
            raise ValueError(f"Release asset does not exist: {asset}")
        records.append(
            {
                "name": asset.name,
                "size": asset.stat().st_size,
                "sha256": sha256(asset),
            }
        )
    return {
        "schema_version": 1,
        "project": "PDFSilo",
        "version": version,
        "tag": tag,
        "commit": commit,
        "artifacts": records,
        "signatures": signatures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--signature-metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("assets", nargs="+", type=Path)
    arguments = parser.parse_args(argv)

    manifest = create_manifest(
        version=arguments.version,
        tag=arguments.tag,
        commit=arguments.commit,
        assets=arguments.assets,
        signature_metadata=arguments.signature_metadata,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

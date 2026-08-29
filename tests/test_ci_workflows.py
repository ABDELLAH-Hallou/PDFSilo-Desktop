"""Contracts for continuous integration and tag-gated releases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.create_release_manifest import create_manifest, sha256
from scripts.validate_release import validate_release

ROOT = Path(__file__).resolve().parents[1]


def _copy_release_inputs(destination: Path) -> None:
    for relative in (
        "pyproject.toml",
        "pysidedeploy.spec",
        "pdfsilo/__init__.py",
        "pdfsilo/updater/service.py",
        "packaging/windows/PDFSilo.iss",
    ):
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def test_ci_installs_project_runs_quality_and_separates_test_layers() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert 'python -m pip install -e ".[dev]"' in workflow
    assert "python -m ruff check pdfsilo tests scripts" in workflow
    assert "python -m ruff format --check pdfsilo tests scripts" in workflow
    assert "Run Qt-free core and CLI tests" in workflow
    assert "-p no:pytest-qt" in workflow
    assert "Run headless-compatible UI tests" in workflow
    assert "ubuntu-24.04" in workflow
    assert "windows-2022" in workflow
    assert "macos-15-intel" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "pull_request_target" not in workflow


def test_release_supports_non_publishing_candidates_and_tag_publication() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )

    assert '      - "v*.*.*"' in workflow
    assert "workflow_dispatch" in workflow
    assert "Version to build without publishing" in workflow
    assert "contents: write" in workflow
    assert "scripts/validate_release.py" in workflow
    assert "scripts\\build_windows.ps1" in workflow
    assert "scripts\\test_windows_package.ps1" in workflow
    assert "scripts\\build_windows_installer.ps1" in workflow
    assert "scripts\\sign_windows_artifacts.ps1" in workflow
    assert "Get-AuthenticodeSignature" in workflow
    assert "release-manifest.json" in workflow
    assert "gh release upload" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "actions/download-artifact@v4" in workflow
    assert "Install, test, and uninstall on a fresh Windows runner" in workflow
    assert "Get-AuthenticodeSignature" in workflow
    assert "if: github.event_name == 'push'" in workflow
    assert "pull_request_target" not in workflow


def test_release_tag_must_match_every_version_source() -> None:
    assert validate_release(ROOT, "v0.1.0") == "0.1.0"

    with pytest.raises(ValueError, match="stable form"):
        validate_release(ROOT, "release-0.1.0")
    with pytest.raises(ValueError, match="does not match"):
        validate_release(ROOT, "v0.1.1")


def test_release_rejects_a_machine_specific_deployment_python(
    tmp_path: Path,
) -> None:
    release_root = tmp_path / "release-source"
    _copy_release_inputs(release_root)
    spec = release_root / "pysidedeploy.spec"
    content = spec.read_text(encoding="utf-8").replace(
        r"python_path = venv\Scripts\python.exe",
        r"python_path = C:\Users\developer\venv\Scripts\python.exe",
    )
    spec.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="portable python_path"):
        validate_release(release_root, "v0.1.0")


def test_release_manifest_hashes_final_assets(tmp_path: Path) -> None:
    archive = tmp_path / "PDFSilo-0.1.0-windows-x64.zip"
    installer = tmp_path / "PDFSilo-Setup-0.1.0-x64.exe"
    archive.write_bytes(b"standalone")
    installer.write_bytes(b"installer")
    signatures = tmp_path / "windows-authenticode.json"
    signatures.write_text(
        json.dumps(
            {
                "scheme": "Authenticode",
                "artifacts": [{"name": installer.name, "status": "Valid"}],
            }
        ),
        encoding="utf-8",
    )

    manifest = create_manifest(
        version="0.1.0",
        tag="v0.1.0",
        commit="a" * 40,
        assets=[installer, archive],
        signature_metadata=signatures,
    )

    assert manifest["version"] == "0.1.0"
    assert manifest["signatures"]["scheme"] == "Authenticode"
    records = {record["name"]: record for record in manifest["artifacts"]}
    assert records[archive.name]["sha256"] == sha256(archive)
    assert records[installer.name]["size"] == len(b"installer")

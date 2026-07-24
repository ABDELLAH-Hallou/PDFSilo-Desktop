"""Regression tests for project-level legal metadata."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_license_file_and_readme_agree():
    license_text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert license_text.startswith("BSD 2-Clause License")
    assert "BSD 2-Clause License" in readme


def test_license_contains_required_bsd_terms():
    license_text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")

    assert "Redistribution and use in source and binary forms" in license_text
    assert 'THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"' in license_text

"""Regression tests for project-level legal metadata."""

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib

from pathlib import Path

from safepdf import __version__
from safepdf.ui.main import main as gui_main


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


def test_pyproject_contains_required_packaging_metadata():
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as file:
        metadata = tomllib.load(file)

    project = metadata["project"]
    assert project["name"] == "safepdf"
    assert project["version"] == __version__ == "0.1.0"
    assert project["requires-python"] == ">=3.10"
    assert "PyMuPDF>=1.27.2.2" in project["dependencies"]
    assert "PySide6>=6.10,<7" in project["dependencies"]
    assert "pytest>=9,<10" in project["optional-dependencies"]["dev"]
    assert "pytest-qt>=4.5,<5" in project["optional-dependencies"]["dev"]


def test_pyproject_defines_cli_and_gui_entry_points():
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as file:
        scripts = tomllib.load(file)["project"]["scripts"]

    assert scripts["safepdf"] == "safepdf.cli:main"
    assert scripts["safepdf-gui"] == "safepdf.ui.main:main"
    assert callable(gui_main)


def test_pyproject_defines_setuptools_build_backend():
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as file:
        build_system = tomllib.load(file)["build-system"]

    assert build_system["build-backend"] == "setuptools.build_meta"
    assert "setuptools>=77" in build_system["requires"]


def test_pyproject_packages_desktop_resources():
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as file:
        setuptools = tomllib.load(file)["tool"]["setuptools"]

    assert "*.svg" in setuptools["package-data"]["safepdf.ui.resources"]

"""Regression tests for project-level legal metadata."""

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib

from pathlib import Path

from pdfsilo import __version__
from pdfsilo.ui.main import main as gui_main

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRODUCT_HOMEPAGE_URL = "https://pdfsilo.com/"
PRODUCT_DOCUMENTATION_URL = "https://pdfsilo.com/faq/"
PUBLIC_RELEASE_URL = "https://github.com/ABDELLAH-Hallou/PDFSilo/releases"
PRIVATE_SOURCE_URL = "https://github.com/ABDELLAH-Hallou/PDFSilo-Desktop"


def test_license_file_and_readme_agree():
    license_text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert license_text.startswith("BSD 2-Clause License")
    assert "BSD 2-Clause License" in readme


def test_license_contains_required_bsd_terms():
    license_text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")

    assert "Redistribution and use in source and binary forms" in license_text
    assert (
        'THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"'
        in license_text
    )


def test_pyproject_contains_required_packaging_metadata():
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as file:
        metadata = tomllib.load(file)

    project = metadata["project"]
    assert project["name"] == "pdfsilo"
    assert project["version"] == __version__ == "0.1.0"
    assert project["requires-python"] == ">=3.10"
    assert "PyMuPDF>=1.27.2.2" in project["dependencies"]
    assert "PySide6>=6.10,<7" in project["dependencies"]
    assert "pytest>=9,<10" in project["optional-dependencies"]["dev"]
    assert "pytest-qt>=4.5,<5" in project["optional-dependencies"]["dev"]
    assert "ruff==0.15.22" in project["optional-dependencies"]["dev"]


def test_pyproject_defines_cli_and_gui_entry_points():
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as file:
        scripts = tomllib.load(file)["project"]["scripts"]

    assert scripts["pdfsilo"] == "pdfsilo.cli:main"
    assert scripts["pdfsilo-gui"] == "pdfsilo.ui.main:main"
    assert callable(gui_main)


def test_pyproject_defines_setuptools_build_backend():
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as file:
        build_system = tomllib.load(file)["build-system"]

    assert build_system["build-backend"] == "setuptools.build_meta"
    assert "setuptools>=77" in build_system["requires"]


def test_public_project_urls_do_not_expose_the_private_source_repository():
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as file:
        urls = tomllib.load(file)["project"]["urls"]

    assert urls == {
        "Homepage": PRODUCT_HOMEPAGE_URL,
        "Documentation": PRODUCT_DOCUMENTATION_URL,
        "Download": PUBLIC_RELEASE_URL,
    }

    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    about = PROJECT_ROOT / "pdfsilo" / "ui" / "dialogs" / "about_dialog.py"
    about_content = about.read_text(encoding="utf-8")
    assert PUBLIC_RELEASE_URL in readme
    assert PRODUCT_HOMEPAGE_URL in about_content
    assert PRODUCT_DOCUMENTATION_URL in about_content
    assert PRIVATE_SOURCE_URL not in about_content


def test_pyproject_packages_desktop_resources():
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as file:
        setuptools = tomllib.load(file)["tool"]["setuptools"]

    assert "*.svg" in setuptools["package-data"]["pdfsilo.ui.resources"]
    assert "*.png" in setuptools["package-data"]["pdfsilo.ui.resources"]
    assert "*.qm" in setuptools["package-data"]["pdfsilo.ui.resources"]


def test_legacy_project_name_is_absent_from_public_source_and_docs():
    legacy_lower = "safe" + "pdf"
    legacy_display = "Safe" + "PDF"
    legacy_upper = "SAFE" + "PDF"
    public_files = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "CODEBASE_ANALYSIS.md",
        PROJECT_ROOT / "PYSIDE6_MIGRATION_PLAN.md",
        PROJECT_ROOT / "requirements.txt",
        PROJECT_ROOT / "tree.txt",
        *[
            path
            for path in (PROJECT_ROOT / "pdfsilo").rglob("*.py")
            if "deployment" not in path.parts
        ],
    ]

    assert (PROJECT_ROOT / "pdfsilo").is_dir()
    assert not (PROJECT_ROOT / legacy_lower).exists()
    for path in public_files:
        content = path.read_text(encoding="utf-8")
        assert legacy_lower not in content
        assert legacy_display not in content
        assert legacy_upper not in content

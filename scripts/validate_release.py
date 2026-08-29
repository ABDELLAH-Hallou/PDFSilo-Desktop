"""Validate that a release tag matches every checked-in version source."""

from __future__ import annotations

import argparse
import configparser
import os
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib

STABLE_TAG_PATTERN = re.compile(
    r"^v(?P<version>(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))$"
)
PACKAGE_VERSION_PATTERN = re.compile(
    r'^__version__\s*=\s*"(?P<version>[^"]+)"\s*$',
    re.MULTILINE,
)
CANONICAL_REPOSITORY_URL = "https://github.com/ABDELLAH-Hallou/PDFSilo-Desktop"
PORTABLE_WINDOWS_PYTHON_PATH = "venv/Scripts/python.exe"


def validate_release(root: Path, tag: str) -> str:
    """Return the validated version or raise ``ValueError``."""
    match = STABLE_TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ValueError("Release tags must use the stable form vMAJOR.MINOR.PATCH.")
    version = match.group("version")

    with (root / "pyproject.toml").open("rb") as file:
        project = tomllib.load(file)["project"]
    project_version = project["version"]
    package_source = (root / "pdfsilo" / "__init__.py").read_text(encoding="utf-8")
    package_match = PACKAGE_VERSION_PATTERN.search(package_source)
    if package_match is None:
        raise ValueError("pdfsilo.__version__ could not be read.")
    package_version = package_match.group("version")

    deployment = configparser.ConfigParser()
    deployment.read(root / "pysidedeploy.spec", encoding="utf-8")
    deployment_arguments = deployment["nuitka"]["extra_args"]
    deployment_python = deployment["python"]["python_path"].replace("\\", "/")
    windows_version = f"{version}.0"
    updater_source = (root / "pdfsilo" / "updater" / "service.py").read_text(
        encoding="utf-8"
    )
    installer_source = (root / "packaging" / "windows" / "PDFSilo.iss").read_text(
        encoding="utf-8"
    )

    mismatches: list[str] = []
    if project_version != version:
        mismatches.append(f"pyproject.toml={project_version}")
    if package_version != version:
        mismatches.append(f"pdfsilo.__version__={package_version}")
    if f"--file-version={windows_version}" not in deployment_arguments:
        mismatches.append("pysidedeploy.spec file version")
    if f"--product-version={windows_version}" not in deployment_arguments:
        mismatches.append("pysidedeploy.spec product version")
    if deployment_python != PORTABLE_WINDOWS_PYTHON_PATH:
        mismatches.append("pysidedeploy.spec portable python_path")
    if project["urls"].get("Repository") != CANONICAL_REPOSITORY_URL:
        mismatches.append("pyproject.toml repository URL")
    expected_api = (
        "https://api.github.com/repos/ABDELLAH-Hallou/PDFSilo-Desktop/releases/latest"
    )
    if expected_api not in updater_source:
        mismatches.append("updater release API URL")
    if f'#define MyAppURL "{CANONICAL_REPOSITORY_URL}"' not in installer_source:
        mismatches.append("installer project URL")
    if mismatches:
        details = ", ".join(mismatches)
        raise ValueError(f"Tag {tag} does not match: {details}.")
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tag",
        nargs="?",
        default=os.environ.get("GITHUB_REF_NAME", ""),
        help="Release tag; defaults to GITHUB_REF_NAME.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root.",
    )
    arguments = parser.parse_args(argv)
    try:
        version = validate_release(arguments.root.resolve(), arguments.tag)
    except (KeyError, OSError, ValueError) as error:
        print(f"Release validation failed: {error}", file=sys.stderr)
        return 1
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Cross-platform contracts for the checked-in Windows packaging inputs."""

from configparser import ConfigParser
from pathlib import Path

from PySide6.QtGui import QImage

from scripts.generate_windows_icon import ICON_SIZE, generate_windows_icon

ROOT = Path(__file__).resolve().parents[1]


def test_deployment_spec_describes_standalone_versioned_application() -> None:
    config = ConfigParser()
    config.read(ROOT / "pysidedeploy.spec", encoding="utf-8")

    assert config["app"]["title"] == "PDFSilo"
    assert config["app"]["input_file"].replace("\\", "/") == ("pdfsilo/ui/main.py")
    assert config["nuitka"]["mode"] == "standalone"
    assert config["python"]["python_path"].replace("\\", "/") == (
        "venv/Scripts/python.exe"
    )

    arguments = config["nuitka"]["extra_args"]
    assert "--low-memory" in arguments
    assert "--lto=no" in arguments
    assert "--output-filename=PDFSilo.exe" in arguments
    assert "--include-package-data=pdfsilo.ui.resources" in arguments
    assert "--company-name=" in arguments
    assert "--file-version=0.1.0.0" in arguments
    assert "--product-version=0.1.0.0" in arguments


def test_windows_icon_is_generated_from_active_png_identity(
    tmp_path: Path,
) -> None:
    source = ROOT / "pdfsilo" / "ui" / "resources" / "icon.png"
    destination = tmp_path / "pdfsilo.ico"

    generate_windows_icon(source, destination)

    image = QImage(str(destination))
    assert not image.isNull()
    assert image.width() == ICON_SIZE
    assert image.height() == ICON_SIZE


def test_inno_installer_uses_standalone_directory_and_product_metadata() -> None:
    definition = (ROOT / "packaging" / "windows" / "PDFSilo.iss").read_text(
        encoding="utf-8"
    )

    assert 'Source: "..\\..\\dist\\windows\\PDFSilo.dist\\*"' in definition
    assert "PrivilegesRequired=lowest" in definition
    assert "DefaultDirName={localappdata}\\Programs\\PDFSilo" in definition
    assert "VersionInfoProductName={#MyAppName}" in definition
    assert "SetupIconFile=pdfsilo.ico" in definition
    assert "MinVersion=10.0.17763" in definition


def test_build_script_preserves_the_complete_standalone_directory() -> None:
    script = (ROOT / "scripts" / "build_windows.ps1").read_text(encoding="utf-8")

    assert '$candidateDirectory.Extension -ne ".dist"' in script
    assert "-LiteralPath $candidateDirectory.FullName" in script
    assert "-Destination $outputDirectory" in script
    assert "-LiteralPath $candidate.FullName -Destination" not in script
    assert '".pysidedeploy.build.spec"' in script
    assert "-LiteralPath $configPath -Destination $buildConfigPath" in script
    assert "-LiteralPath $buildConfigPath" in script

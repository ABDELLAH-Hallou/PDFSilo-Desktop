"""Generate the Windows deployment icon from the approved PDFSilo PNG."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QImage

ICON_ARTWORK_RECT = QRect(500, 220, 540, 540)
ICON_SIZE = 256


def generate_windows_icon(source: Path, destination: Path) -> None:
    """Crop the transparent promo canvas and write a Windows ICO image."""
    image = QImage(str(source))
    if image.isNull():
        raise RuntimeError(f"Could not read source icon: {source}")
    artwork = image.copy(ICON_ARTWORK_RECT.intersected(image.rect()))
    if artwork.isNull():
        raise RuntimeError("The configured icon artwork rectangle is empty.")
    artwork = artwork.scaled(
        ICON_SIZE,
        ICON_SIZE,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not artwork.save(str(destination), "ICO"):
        raise RuntimeError(f"Could not write Windows icon: {destination}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source = root / "pdfsilo" / "ui" / "resources" / "icon.png"
    destination = root / "packaging" / "windows" / "pdfsilo.ico"
    generate_windows_icon(source, destination)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Packaged visual resources for the PDFSilo desktop interface."""

from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap

RESOURCE_DIRECTORY = Path(__file__).resolve().parent
ICON_PATH = RESOURCE_DIRECTORY / "icon.png"
LOGO_PATH = RESOURCE_DIRECTORY / "logo.png"
APPLICATION_ICON_PATH = ICON_PATH
SIDEBAR_HIDE_ICON_PATH = RESOURCE_DIRECTORY / "sidebar_hide.svg"
SIDEBAR_SHOW_ICON_PATH = RESOURCE_DIRECTORY / "sidebar_show.svg"

# The uploaded PNG artwork sits on a large transparent promotional canvas.
# Crop only that empty canvas at runtime; do not recolour or reshape the logo.
_ICON_ARTWORK_RECT = QRect(500, 220, 540, 540)
_LOGO_ARTWORK_RECT = QRect(190, 300, 1100, 360)


def _artwork_pixmap(path: Path, rect: QRect) -> QPixmap:
    pixmap = QPixmap(str(path))
    return pixmap.copy(rect.intersected(pixmap.rect()))


def application_icon(*, dark: bool = False) -> QIcon:
    """Return the uploaded PDFSilo raster application icon."""
    del dark  # One official PNG identity is shared by all theme modes.
    return QIcon(_artwork_pixmap(ICON_PATH, _ICON_ARTWORK_RECT))


def brand_logo_pixmap(
    *,
    dark: bool = False,
    size: QSize = QSize(184, 58),
) -> QPixmap:
    """Render the uploaded transparent raster wordmark at UI scale."""
    del dark  # One official PNG identity is shared by all theme modes.
    return _artwork_pixmap(LOGO_PATH, _LOGO_ARTWORK_RECT).scaled(
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def sidebar_toggle_icon(sidebar_visible: bool) -> QIcon:
    """Return the action icon for hiding or showing the sidebar."""
    path = SIDEBAR_HIDE_ICON_PATH if sidebar_visible else SIDEBAR_SHOW_ICON_PATH
    return QIcon(str(path))


__all__ = [
    "APPLICATION_ICON_PATH",
    "ICON_PATH",
    "LOGO_PATH",
    "RESOURCE_DIRECTORY",
    "SIDEBAR_HIDE_ICON_PATH",
    "SIDEBAR_SHOW_ICON_PATH",
    "application_icon",
    "brand_logo_pixmap",
    "sidebar_toggle_icon",
]

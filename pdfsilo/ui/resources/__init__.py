"""Packaged visual resources for the PDFSilo desktop interface."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap

RESOURCE_DIRECTORY = Path(__file__).resolve().parent
ICON_LIGHT_PATH = RESOURCE_DIRECTORY / "icon-light.svg"
ICON_DARK_PATH = RESOURCE_DIRECTORY / "icon-dark.svg"
ICON_INDIGO_PATH = RESOURCE_DIRECTORY / "icon-indigo.svg"
LOGO_LIGHT_PATH = RESOURCE_DIRECTORY / "logo-light.svg"
LOGO_DARK_PATH = RESOURCE_DIRECTORY / "logo-dark.svg"
LOGO_INDIGO_PATH = RESOURCE_DIRECTORY / "logo-indigo.svg"
APPLICATION_ICON_PATH = ICON_LIGHT_PATH
SIDEBAR_HIDE_ICON_PATH = RESOURCE_DIRECTORY / "sidebar_hide.svg"
SIDEBAR_SHOW_ICON_PATH = RESOURCE_DIRECTORY / "sidebar_show.svg"


def application_icon(*, dark: bool = False) -> QIcon:
    """Return the contrast-correct packaged PDFSilo application icon."""
    return QIcon(str(ICON_DARK_PATH if dark else ICON_LIGHT_PATH))


def brand_logo_pixmap(
    *,
    dark: bool = False,
    size: QSize = QSize(184, 58),
) -> QPixmap:
    """Render the appropriate transparent wordmark for a UI surface."""
    path = LOGO_DARK_PATH if dark else LOGO_LIGHT_PATH
    return QPixmap(str(path)).scaled(
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def sidebar_toggle_icon(sidebar_visible: bool) -> QIcon:
    """Return the action icon for hiding or showing the sidebar."""
    path = (
        SIDEBAR_HIDE_ICON_PATH
        if sidebar_visible
        else SIDEBAR_SHOW_ICON_PATH
    )
    return QIcon(str(path))


__all__ = [
    "APPLICATION_ICON_PATH",
    "ICON_DARK_PATH",
    "ICON_INDIGO_PATH",
    "ICON_LIGHT_PATH",
    "LOGO_DARK_PATH",
    "LOGO_INDIGO_PATH",
    "LOGO_LIGHT_PATH",
    "RESOURCE_DIRECTORY",
    "SIDEBAR_HIDE_ICON_PATH",
    "SIDEBAR_SHOW_ICON_PATH",
    "application_icon",
    "brand_logo_pixmap",
    "sidebar_toggle_icon",
]

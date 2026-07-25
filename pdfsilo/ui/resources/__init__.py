"""Packaged visual resources for the PDFSilo desktop interface."""

from pathlib import Path

from PySide6.QtGui import QIcon

RESOURCE_DIRECTORY = Path(__file__).resolve().parent
APPLICATION_ICON_PATH = RESOURCE_DIRECTORY / "app_icon.svg"
SIDEBAR_HIDE_ICON_PATH = RESOURCE_DIRECTORY / "sidebar_hide.svg"
SIDEBAR_SHOW_ICON_PATH = RESOURCE_DIRECTORY / "sidebar_show.svg"


def application_icon() -> QIcon:
    """Return the packaged PDFSilo application icon."""
    return QIcon(str(APPLICATION_ICON_PATH))


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
    "RESOURCE_DIRECTORY",
    "SIDEBAR_HIDE_ICON_PATH",
    "SIDEBAR_SHOW_ICON_PATH",
    "application_icon",
    "sidebar_toggle_icon",
]

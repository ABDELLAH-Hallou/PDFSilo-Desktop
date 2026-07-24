"""Packaged visual resources for the SafePDF desktop interface."""

from pathlib import Path

from PySide6.QtGui import QIcon

RESOURCE_DIRECTORY = Path(__file__).resolve().parent
APPLICATION_ICON_PATH = RESOURCE_DIRECTORY / "app_icon.svg"


def application_icon() -> QIcon:
    """Return the packaged SafePDF application icon."""
    return QIcon(str(APPLICATION_ICON_PATH))


__all__ = [
    "APPLICATION_ICON_PATH",
    "RESOURCE_DIRECTORY",
    "application_icon",
]


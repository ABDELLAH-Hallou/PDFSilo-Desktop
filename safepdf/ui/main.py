"""SafePDF desktop application entry point."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from safepdf.ui.main_window import MainWindow
from safepdf.ui.metadata import (
    APPLICATION_DISPLAY_NAME,
    APPLICATION_ID,
    APPLICATION_NAME,
    APPLICATION_VERSION,
    ORGANIZATION_DOMAIN,
    ORGANIZATION_NAME,
)
from safepdf.ui.resources import application_icon
from safepdf.ui.theme import apply_theme


def create_application(arguments: Sequence[str] | None = None) -> QApplication:
    """Create or configure the process-wide Qt application."""
    existing = QApplication.instance()
    if existing is None:
        application = QApplication(
            list(arguments) if arguments is not None else sys.argv
        )
    else:
        application = existing

    application.setApplicationName(APPLICATION_NAME)
    application.setApplicationDisplayName(APPLICATION_DISPLAY_NAME)
    application.setApplicationVersion(APPLICATION_VERSION)
    application.setOrganizationName(ORGANIZATION_NAME)
    application.setOrganizationDomain(ORGANIZATION_DOMAIN)
    application.setDesktopFileName(APPLICATION_ID)
    application.setWindowIcon(application_icon())
    apply_theme(application)
    return application


def create_main_window() -> MainWindow:
    """Create the SafePDF application window."""
    return MainWindow()


def main() -> int:
    """Start the SafePDF PySide6 desktop application."""
    app = create_application()
    window = create_main_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

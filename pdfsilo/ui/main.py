"""PDFSilo desktop application entry point."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication

from pdfsilo.ui.main_window import MainWindow
from pdfsilo.ui.metadata import (
    APPLICATION_DISPLAY_NAME,
    APPLICATION_ID,
    APPLICATION_NAME,
    APPLICATION_VERSION,
    ORGANIZATION_DOMAIN,
    ORGANIZATION_NAME,
)
from pdfsilo.ui.package_self_test import run_package_self_test
from pdfsilo.ui.resources import application_icon
from pdfsilo.ui.theme import ThemeMode, apply_theme


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
    manager = apply_theme(application)
    application.setWindowIcon(
        application_icon(
            dark=manager.effective_mode is ThemeMode.DARK,
        )
    )
    return application


def create_main_window(settings: QSettings | None = None) -> MainWindow:
    """Create the PDFSilo application window."""
    return MainWindow(settings=settings)


def main() -> int:
    """Start the PDFSilo PySide6 desktop application."""
    if "--package-self-test" in sys.argv:
        index = sys.argv.index("--package-self-test")
        if index + 1 >= len(sys.argv):
            return 2
        return run_package_self_test(Path(sys.argv[index + 1]))

    app = create_application()
    window = create_main_window()
    window.show()
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(250, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

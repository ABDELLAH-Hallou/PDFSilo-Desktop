"""SafePDF desktop application entry point.

This initial bootstrap makes the packaged ``safepdf-gui`` command usable.
Feature pages and the final main-window implementation are introduced in later
PySide6 migration phases.
"""

from __future__ import annotations

import sys


def _load_qt():
    """Import and return the Qt classes used by the bootstrap window."""
    # Keep Qt imports local so package metadata and the CLI remain importable in
    # minimal environments that have not installed the UI dependency yet.
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
    except ImportError as exc:
        raise SystemExit(
            "PySide6 is required for the SafePDF desktop interface. "
            "Install the project with: pip install ."
        ) from exc
    return Qt, QApplication, QLabel, QMainWindow


def create_main_window():
    """Create the temporary Phase 2 application window."""
    Qt, _, QLabel, QMainWindow = _load_qt()

    window = QMainWindow()
    window.setWindowTitle("SafePDF")
    window.resize(900, 600)

    message = QLabel(
        "SafePDF desktop foundation is ready.\n"
        "Operation screens will be added in the next migration phases."
    )
    message.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(message)
    return window


def main() -> int:
    """Start the SafePDF PySide6 desktop application."""
    _, QApplication, _, _ = _load_qt()

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("SafePDF")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("SafePDF")

    window = create_main_window()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

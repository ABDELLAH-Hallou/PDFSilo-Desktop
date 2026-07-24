"""Smoke tests for the Phase 5 PySide6 application structure."""

import xml.etree.ElementTree as ElementTree

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QTimer, QSize
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from safepdf.ui import main as ui_main
from safepdf.ui.main import create_application, create_main_window
from safepdf.ui.main_window import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MainWindow,
)
from safepdf.ui.metadata import (
    APPLICATION_DISPLAY_NAME,
    APPLICATION_ID,
    APPLICATION_NAME,
    APPLICATION_VERSION,
    ORGANIZATION_DOMAIN,
    ORGANIZATION_NAME,
)
from safepdf.ui.resources import APPLICATION_ICON_PATH, application_icon
from safepdf.ui.theme import (
    APPLICATION_STYLESHEET,
    FONT_SIZE_BODY,
    SPACE_LG,
    SPACE_MD,
    SPACE_SM,
    SPACE_XL,
    apply_theme,
)


def test_create_main_window(qtbot):
    window = create_main_window()
    qtbot.addWidget(window)

    assert isinstance(window, MainWindow)
    assert window.windowTitle() == "SafePDF"
    assert window.size() == QSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    assert isinstance(window.centralWidget(), QWidget)
    assert window.findChild(QLabel, "titleLabel").text() == "SafePDF"
    assert "structure is ready" in (
        window.findChild(QLabel, "subtitleLabel").text()
    )
    assert not window.windowIcon().isNull()


def test_create_application_sets_metadata_and_theme(qapp):
    application = create_application([])

    assert application is qapp
    assert QApplication.applicationName() == APPLICATION_NAME
    assert QApplication.applicationDisplayName() == APPLICATION_DISPLAY_NAME
    assert QApplication.applicationVersion() == APPLICATION_VERSION
    assert QApplication.organizationName() == ORGANIZATION_NAME
    assert QApplication.organizationDomain() == ORGANIZATION_DOMAIN
    assert QApplication.desktopFileName() == APPLICATION_ID
    assert application.styleSheet() == APPLICATION_STYLESHEET
    assert application.font().pointSize() == FONT_SIZE_BODY
    assert not application.windowIcon().isNull()


def test_packaged_application_icon_is_valid_svg():
    assert APPLICATION_ICON_PATH.is_file()
    assert ElementTree.parse(APPLICATION_ICON_PATH).getroot().tag.endswith("svg")
    assert not application_icon().isNull()
    assert not application_icon().pixmap(QSize(64, 64)).isNull()


def test_spacing_scale_is_ordered():
    assert SPACE_SM < SPACE_MD < SPACE_LG < SPACE_XL


def test_apply_theme_is_idempotent(qapp):
    apply_theme(qapp)
    first_stylesheet = qapp.styleSheet()

    apply_theme(qapp)

    assert qapp.styleSheet() == first_stylesheet


def test_gui_entry_point_starts_and_stops_event_loop(qapp, monkeypatch):
    windows: list[MainWindow] = []
    visible_while_running: list[bool] = []

    def create_window() -> MainWindow:
        window = MainWindow()
        windows.append(window)
        return window

    monkeypatch.setattr(ui_main, "create_main_window", create_window)

    def verify_started() -> None:
        visible_while_running.append(windows[0].isVisible())
        qapp.quit()

    QTimer.singleShot(0, verify_started)

    assert ui_main.main() == 0
    assert len(windows) == 1
    assert visible_while_running == [True]
    windows[0].close()

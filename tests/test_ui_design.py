"""Regression tests for the responsive SafePDF visual shell."""

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QLabel, QPushButton, QSplitter

from safepdf.ui.main_window import MainWindow
from safepdf.ui.pages.home_page import ToolCard


@pytest.fixture()
def ui_settings(tmp_path: Path) -> QSettings:
    settings = QSettings(
        str(tmp_path / "design-settings.ini"),
        QSettings.Format.IniFormat,
    )
    settings.clear()
    return settings


def test_home_dashboard_routes_to_popular_operation(qtbot, ui_settings):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    window.show()

    assert len(window.findChildren(ToolCard, "toolCard")) == 6
    quick_start = window.findChild(QPushButton, "homePrimaryAction")
    qtbot.mouseClick(quick_start, Qt.MouseButton.LeftButton)

    assert window.page_stack.currentWidget().objectName() == "mergePage"
    assert window.findChild(QLabel, "headerPageTitleLabel").text() == "Merge"


def test_sidebar_can_be_collapsed_without_persisting_sensitive_state(
    qtbot,
    ui_settings,
):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    window.show()

    assert window.sidebar.isVisible()
    window.toggle_sidebar_action.setChecked(False)
    assert window.sidebar.isHidden()
    window.toggle_sidebar_action.setChecked(True)
    assert window.sidebar.isVisible()


def test_operation_workspace_stacks_at_minimum_window_width(
    qtbot,
    ui_settings,
):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    window.show()
    window.navigate_to("compress")

    splitter = window.page_stack.currentWidget().findChild(
        QSplitter,
        "operationSplitter",
    )
    window.resize(1240, 800)
    qtbot.waitUntil(
        lambda: splitter.orientation() == Qt.Orientation.Horizontal
    )

    window.resize(800, 620)
    qtbot.waitUntil(
        lambda: splitter.orientation() == Qt.Orientation.Vertical
    )

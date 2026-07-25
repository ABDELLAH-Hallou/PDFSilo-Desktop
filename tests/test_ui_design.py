"""Regression tests for the responsive SafePDF visual shell."""

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QPushButton,
    QSplitter,
)

from safepdf.ui.dialogs import SettingsDialog
from safepdf.ui.main_window import THEME_SETTING, MainWindow
from safepdf.ui.pages.home_page import ToolCard
from safepdf.ui.theme import (
    APPLICATION_STYLESHEET,
    DARK_STYLESHEET,
    ThemeMode,
    apply_theme,
)


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


def test_explicit_theme_modes_apply_and_persist(qtbot, ui_settings):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    application = QApplication.instance()
    assert application is not None

    window.set_theme_mode(ThemeMode.DARK)
    assert application.styleSheet() == DARK_STYLESHEET
    assert (
        application.palette().color(QPalette.ColorRole.Window).name().upper()
        == "#0B1220"
    )
    assert ui_settings.value(THEME_SETTING) == ThemeMode.DARK.value
    assert window.theme_actions[ThemeMode.DARK].isChecked()

    restored = MainWindow(ui_settings)
    qtbot.addWidget(restored)
    assert restored.theme_actions[ThemeMode.DARK].isChecked()
    assert application.styleSheet() == DARK_STYLESHEET

    window.set_theme_mode(ThemeMode.LIGHT)
    assert application.styleSheet() == APPLICATION_STYLESHEET
    assert (
        application.palette().color(QPalette.ColorRole.Window).name().upper()
        == "#F5F7FB"
    )
    assert ui_settings.value(THEME_SETTING) == ThemeMode.LIGHT.value
    assert window.theme_actions[ThemeMode.LIGHT].isChecked()

    restored.set_theme_mode(ThemeMode.SYSTEM)


def test_settings_dialog_changes_theme_without_sensitive_values(
    qtbot,
    ui_settings,
):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    window.show_settings_dialog()

    dialog = window.findChild(SettingsDialog, "settingsDialog")
    combo = dialog.findChild(QComboBox, "themeModeCombo")
    combo.setCurrentIndex(combo.findData(ThemeMode.DARK.value))

    assert ui_settings.value(THEME_SETTING) == ThemeMode.DARK.value
    assert all(
        "password" not in key.lower()
        for key in ui_settings.allKeys()
    )
    window.set_theme_mode(ThemeMode.SYSTEM)


def test_system_mode_reacts_to_qt_color_scheme_signal(
    qapp,
    monkeypatch,
):
    manager = apply_theme(qapp, ThemeMode.SYSTEM)
    monkeypatch.setattr(
        manager,
        "_resolved_mode",
        lambda: ThemeMode.DARK,
    )

    manager._system_color_scheme_changed(Qt.ColorScheme.Dark)

    assert manager.mode is ThemeMode.SYSTEM
    assert manager.effective_mode is ThemeMode.DARK
    assert qapp.styleSheet() == DARK_STYLESHEET
    monkeypatch.undo()
    apply_theme(qapp, ThemeMode.SYSTEM)

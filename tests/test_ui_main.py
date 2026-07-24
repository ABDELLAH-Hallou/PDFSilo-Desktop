"""Smoke tests for the PySide6 application structure and main shell."""

import xml.etree.ElementTree as ElementTree
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QSettings, QTimer, QSize
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QListWidget,
    QMenu,
    QProgressBar,
    QStackedWidget,
    QToolButton,
    QWidget,
)

from safepdf.ui import main as ui_main
from safepdf.ui.main import create_application, create_main_window
from safepdf.ui.main_window import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    GEOMETRY_SETTING,
    NAVIGATION_SETTING,
    PERSISTED_SETTING_KEYS,
    STATE_SETTING,
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
from safepdf.ui.pages import PAGE_DEFINITIONS
from safepdf.ui.theme import (
    APPLICATION_STYLESHEET,
    FONT_SIZE_BODY,
    SPACE_LG,
    SPACE_MD,
    SPACE_SM,
    SPACE_XL,
    apply_theme,
)


@pytest.fixture()
def ui_settings(tmp_path: Path) -> QSettings:
    settings = QSettings(
        str(tmp_path / "ui-settings.ini"),
        QSettings.Format.IniFormat,
    )
    settings.clear()
    return settings


def test_create_main_window(qtbot, ui_settings):
    window = create_main_window(ui_settings)
    qtbot.addWidget(window)

    assert isinstance(window, MainWindow)
    assert window.windowTitle() == "SafePDF"
    assert window.size() == QSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    assert isinstance(window.centralWidget(), QWidget)
    assert window.findChild(QLabel, "applicationTitleLabel").text() == "SafePDF"
    assert window.statusBar().currentMessage() == "Ready"
    assert not window.windowIcon().isNull()


def test_sidebar_navigation_controls_stacked_pages(qtbot, ui_settings):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    navigation = window.findChild(QListWidget, "navigationList")
    stack = window.findChild(QStackedWidget, "pageStack")

    assert navigation.count() == stack.count() == len(PAGE_DEFINITIONS)
    assert [navigation.item(index).text() for index in range(navigation.count())] == [
        definition.label for definition in PAGE_DEFINITIONS
    ]
    assert navigation.currentRow() == stack.currentIndex() == 0
    assert stack.currentWidget().objectName() == "homePage"

    assert window.navigate_to("split") is True
    assert navigation.currentRow() == stack.currentIndex() == 2
    assert stack.currentWidget().objectName() == "splitPage"
    assert window.statusBar().currentMessage() == "Split selected."
    assert window.navigate_to("not-a-page") is False


def test_navigation_actions_move_between_pages(qtbot, ui_settings):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)

    window.next_page_action.trigger()
    assert window.navigation.currentRow() == 1

    window.previous_page_action.trigger()
    assert window.navigation.currentRow() == 0

    window.navigate_to("compress")
    window.home_action.trigger()
    assert window.navigation.currentRow() == 0


def test_global_status_progress_and_output_controls(qtbot, ui_settings):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    progress = window.findChild(QProgressBar, "globalProgressBar")
    output = window.findChild(QLabel, "outputLocationLabel")

    assert progress.isHidden()
    window.set_progress(3, 5, "Processing page 3.")
    assert not progress.isHidden()
    assert (progress.minimum(), progress.maximum(), progress.value()) == (0, 5, 3)
    assert progress.format() == "3 / 5"
    assert window.statusBar().currentMessage() == "Processing page 3."

    window.set_progress(0, 0)
    assert (progress.minimum(), progress.maximum()) == (0, 0)
    assert progress.format() == "Working…"

    output_path = Path("results") / "output.pdf"
    window.set_output_location(output_path)
    assert str(output_path) in output.text()
    assert output.toolTip() == str(output_path)

    window.clear_progress()
    window.set_output_location(None)
    assert progress.isHidden()
    assert output.text() == "Output: —"


def test_application_menus_shortcuts_and_header_actions(qtbot, ui_settings):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)

    menu_titles = {
        menu.title().replace("&", "")
        for menu in window.menuBar().findChildren(QMenu)
    }
    assert {"File", "Navigate", "Tools", "Help"} <= menu_titles

    expected_actions = {
        "openAction",
        "exitAction",
        "homeAction",
        "previousPageAction",
        "nextPageAction",
        "settingsAction",
        "aboutAction",
    }
    actions = {
        action.objectName(): action
        for action in window.findChildren(QAction)
        if action.objectName()
    }
    assert expected_actions <= actions.keys()
    assert all(
        not actions[name].shortcut().isEmpty()
        for name in expected_actions
    )
    assert actions["homeAction"].shortcut() == QKeySequence("Ctrl+H")
    assert window.findChild(QToolButton, "settingsButton") is not None
    assert window.findChild(QToolButton, "helpButton") is not None


def test_open_action_uses_pdf_file_dialog(
    qtbot,
    ui_settings,
    monkeypatch,
    tmp_path: Path,
):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    selected = tmp_path / "selected.pdf"
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *_args, **_kwargs: (str(selected), "PDF documents (*.pdf)"),
    )

    window.open_action.trigger()

    assert window.selected_input_path == selected
    assert selected.name in window.statusBar().currentMessage()


def test_window_settings_round_trip_is_allowlisted(qtbot, ui_settings):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    window.resize(800, 600)
    window.move(24, 32)
    window.navigation.setCurrentRow(4)
    window.set_output_location("private-output.pdf")
    window.selected_input_path = Path("private-input.pdf")
    window.close()
    ui_settings.sync()

    assert set(ui_settings.allKeys()) == PERSISTED_SETTING_KEYS
    assert ui_settings.contains(GEOMETRY_SETTING)
    assert ui_settings.contains(STATE_SETTING)
    assert ui_settings.value(NAVIGATION_SETTING, type=int) == 4
    assert all("password" not in key.lower() for key in ui_settings.allKeys())
    assert "private" not in Path(ui_settings.fileName()).read_text(
        encoding="utf-8"
    )

    restored = MainWindow(ui_settings)
    qtbot.addWidget(restored)
    assert restored.navigation.currentRow() == 4
    assert restored.page_stack.currentIndex() == 4
    assert restored.size() == QSize(800, 600)
    # Qt clamps the horizontal position to the 800 px offscreen display.
    assert restored.pos().y() == window.pos().y()
    assert restored.pos().x() >= 0


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


def test_main_window_starts_and_stops_local_event_loop(
    qapp,
    ui_settings,
):
    window = MainWindow(ui_settings)
    window.show()
    visible_while_running: list[bool] = []
    event_loop = QEventLoop()

    def verify_started() -> None:
        visible_while_running.append(window.isVisible())
        event_loop.quit()

    QTimer.singleShot(0, verify_started)

    assert event_loop.exec() == 0
    assert visible_while_running == [True]
    window.close()


def test_gui_entry_point_shows_window_and_returns_exit_code(monkeypatch):
    class FakeApplication:
        def exec(self) -> int:
            return 17

    class FakeWindow:
        shown = False

        def show(self) -> None:
            self.shown = True

    application = FakeApplication()
    window = FakeWindow()
    monkeypatch.setattr(
        ui_main,
        "create_application",
        lambda: application,
    )
    monkeypatch.setattr(ui_main, "create_main_window", lambda: window)

    assert ui_main.main() == 17
    assert window.shown

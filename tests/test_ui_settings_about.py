"""Behavior coverage for PDFSilo's Settings and About content."""

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
)

from pdfsilo.core import OperationResult
from pdfsilo.ui.dialogs import AboutDialog, SettingsDialog
from pdfsilo.ui.main_window import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    GEOMETRY_SETTING,
    NAVIGATION_SETTING,
    STATE_SETTING,
    THEME_SETTING,
    MainWindow,
)
from pdfsilo.ui.preferences import (
    CONFIRM_OVERWRITE_SETTING,
    OPEN_OUTPUT_FOLDER_SETTING,
    REOPEN_LAST_TOOL_SETTING,
    RESTORE_WINDOW_SETTING,
    SHOW_INPUT_PREVIEWS_SETTING,
    UiPreferences,
)
from pdfsilo.ui.theme import ThemeMode


@pytest.fixture()
def ui_settings(tmp_path: Path) -> QSettings:
    settings = QSettings(
        str(tmp_path / "settings-about.ini"),
        QSettings.Format.IniFormat,
    )
    settings.clear()
    return settings


def test_settings_present_important_grouped_preferences(
    qtbot,
    ui_settings,
):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    window.show_settings_dialog()

    dialog = window.findChild(SettingsDialog, "settingsDialog")
    assert dialog is not None
    tabs = dialog.findChild(QTabWidget, "settingsTabs")
    assert tabs is not None
    assert [tabs.tabText(index) for index in range(tabs.count())] == [
        "Appearance",
        "Workflow",
        "Startup and privacy",
    ]

    assert dialog.findChild(QComboBox, "themeModeCombo") is not None
    for object_name in (
        "showInputPreviewsCheck",
        "confirmOverwriteCheck",
        "openOutputFolderCheck",
        "restoreWindowCheck",
        "reopenLastToolCheck",
    ):
        checkbox = dialog.findChild(QCheckBox, object_name)
        assert checkbox is not None
        assert checkbox.accessibleName() or checkbox.text()

    privacy = dialog.findChild(QLabel, "settingsPrivacyText")
    assert privacy is not None
    assert "passwords are never stored" in privacy.text()


def test_settings_apply_and_persist_safe_workflow_choices(
    qtbot,
    ui_settings,
):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    window.show_settings_dialog()
    dialog = window.findChild(SettingsDialog, "settingsDialog")
    assert dialog is not None

    window.navigate_to("compress")
    page = window.page_stack.currentWidget()
    assert not page.preview_card.isHidden()

    previews = dialog.findChild(QCheckBox, "showInputPreviewsCheck")
    overwrite = dialog.findChild(QCheckBox, "confirmOverwriteCheck")
    output_folder = dialog.findChild(QCheckBox, "openOutputFolderCheck")
    previews.setChecked(False)
    overwrite.setChecked(False)
    output_folder.setChecked(True)

    assert page.preview_card.isHidden()
    assert page._confirm_overwrite is False
    assert (
        ui_settings.value(
            SHOW_INPUT_PREVIEWS_SETTING,
            type=bool,
        )
        is False
    )
    assert ui_settings.value(CONFIRM_OVERWRITE_SETTING, type=bool) is False
    assert ui_settings.value(OPEN_OUTPUT_FOLDER_SETTING, type=bool) is True
    assert all(
        "password" not in key.lower()
        and "document" not in key.lower()
        and "path" not in key.lower()
        for key in ui_settings.allKeys()
    )


def test_restore_defaults_resets_theme_and_safety_preferences(
    qtbot,
    ui_settings,
):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    window.show_settings_dialog()
    dialog = window.findChild(SettingsDialog, "settingsDialog")
    assert dialog is not None

    dialog.findChild(QComboBox, "themeModeCombo").setCurrentIndex(
        dialog.theme_combo.findData(ThemeMode.DARK.value)
    )
    dialog.findChild(QCheckBox, "confirmOverwriteCheck").setChecked(False)
    dialog.findChild(QCheckBox, "openOutputFolderCheck").setChecked(True)
    qtbot.mouseClick(
        dialog.findChild(QPushButton, "restoreSettingsDefaultsButton"),
        Qt.MouseButton.LeftButton,
    )

    assert ui_settings.value(THEME_SETTING) == ThemeMode.SYSTEM.value
    assert ui_settings.value(CONFIRM_OVERWRITE_SETTING, type=bool) is True
    assert ui_settings.value(OPEN_OUTPUT_FOLDER_SETTING, type=bool) is False
    assert dialog.preferences() == UiPreferences()


def test_disabled_startup_restoration_opens_home_at_default_size(
    qtbot,
    ui_settings,
):
    first = MainWindow(ui_settings)
    qtbot.addWidget(first)
    first.resize(860, 610)
    first.navigate_to("encrypt")
    first.close()
    assert ui_settings.contains(GEOMETRY_SETTING)
    assert ui_settings.contains(STATE_SETTING)
    assert ui_settings.contains(NAVIGATION_SETTING)

    UiPreferences(
        restore_window=False,
        reopen_last_tool=False,
    ).save(ui_settings)
    restored = MainWindow(ui_settings)
    qtbot.addWidget(restored)

    assert restored.size().width() == DEFAULT_WINDOW_WIDTH
    assert restored.size().height() == DEFAULT_WINDOW_HEIGHT
    assert restored.navigation.currentRow() == 0

    restored.close()
    assert not ui_settings.contains(GEOMETRY_SETTING)
    assert not ui_settings.contains(STATE_SETTING)
    assert not ui_settings.contains(NAVIGATION_SETTING)
    assert ui_settings.value(RESTORE_WINDOW_SETTING, type=bool) is False
    assert ui_settings.value(REOPEN_LAST_TOOL_SETTING, type=bool) is False


def test_overwrite_confirmation_keeps_staged_result_until_approved(
    qtbot,
    ui_settings,
    tmp_path,
    monkeypatch,
):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    window.navigate_to("reorder")
    page = window.page_stack.currentWidget()

    destination = tmp_path / "existing.pdf"
    destination.write_bytes(b"existing")
    staged = tmp_path / ".existing.review.pdf"
    staged.write_bytes(b"reviewed")
    page._staged_path = staged
    page._staged_destination = destination
    page._staged_result = OperationResult(
        output_paths=[staged],
        message="Ready",
    )
    page.set_confirm_overwrite(True)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Cancel,
    )

    page._save_staged_output()

    assert destination.read_bytes() == b"existing"
    assert staged.read_bytes() == b"reviewed"
    assert page._staged_result is not None

    page.set_confirm_overwrite(False)
    page._save_staged_output()

    assert destination.read_bytes() == b"reviewed"
    assert not staged.exists()
    assert page._staged_result is None


def test_open_output_folder_preference_uses_system_file_manager(
    qtbot,
    ui_settings,
    tmp_path,
    monkeypatch,
):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    opened = []
    monkeypatch.setattr(
        QDesktopServices,
        "openUrl",
        lambda url: opened.append(url.toLocalFile()) or True,
    )
    window.set_ui_preferences(UiPreferences(open_output_folder=True))
    output = tmp_path / "result.pdf"
    output.write_bytes(b"pdf")

    window.set_output_location(output)

    assert [Path(path) for path in opened] == [tmp_path]


def test_about_dialog_explains_capabilities_privacy_and_runtime(
    qtbot,
    ui_settings,
):
    window = MainWindow(ui_settings)
    qtbot.addWidget(window)
    window.show_about_dialog()

    dialog = window.findChild(AboutDialog, "aboutDialog")
    assert dialog is not None
    assert dialog.windowTitle() == "About PDFSilo"
    assert len(dialog.findChildren(QFrame, "aboutFeatureCard")) == 3
    assert (
        "PDFSilo"
        in dialog.findChild(
            QLabel,
            "aboutProductName",
        ).text()
    )
    privacy = dialog.findChild(QLabel, "aboutPrivacyText").text()
    assert "no uploads, accounts, or telemetry" in privacy
    assert "never written to application settings" in privacy
    runtime = dialog.findChild(QLabel, "aboutRuntimeDetails").text()
    assert "PyMuPDF" in runtime
    assert "PySide6" in runtime
    assert "Python" in runtime

    first_dialog = dialog
    window.show_about_dialog()
    assert window.findChild(AboutDialog, "aboutDialog") is first_dialog

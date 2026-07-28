"""pytest-qt coverage for opt-in update settings, workers, and UI."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings, QThread
from PySide6.QtWidgets import QCheckBox, QLabel

from pdfsilo.ui.dialogs import SettingsDialog, UpdateDialog
from pdfsilo.ui.main_window import MainWindow
from pdfsilo.ui.preferences import (
    CHECK_UPDATES_AUTOMATICALLY_SETTING,
    LAST_UPDATE_CHECK_SETTING,
    SKIPPED_UPDATE_VERSION_SETTING,
    UiPreferences,
)
from pdfsilo.ui.widgets import UpdateBanner
from pdfsilo.ui.workers import UpdateRunner
from pdfsilo.updater import UpdateInfo


@pytest.fixture()
def update_settings(tmp_path: Path) -> QSettings:
    settings = QSettings(
        str(tmp_path / "update-settings.ini"),
        QSettings.Format.IniFormat,
    )
    settings.clear()
    return settings


def _update_info() -> UpdateInfo:
    return UpdateInfo(
        version="0.2.0",
        download_url="https://github.com/example/PDFSilo-0.2.0.exe",
        checksum_sha256="a" * 64,
        signature_url=None,
        release_notes_url="https://github.com/example/releases/v0.2.0",
        published_at="2026-07-27T12:00:00Z",
        asset_name="PDFSilo-0.2.0.exe",
    )


def test_update_preferences_are_opt_in_and_allowlisted(
    qtbot,
    update_settings,
) -> None:
    preferences = UiPreferences.from_settings(update_settings)
    assert preferences.check_updates_automatically is False

    window = MainWindow(update_settings)
    qtbot.addWidget(window)
    window.show_settings_dialog()
    dialog = window.findChild(SettingsDialog, "settingsDialog")
    checkbox = dialog.findChild(
        QCheckBox,
        "checkUpdatesAutomaticallyCheck",
    )
    assert checkbox is not None
    assert checkbox.isChecked() is False
    descriptions = [
        label.text() for label in checkbox.parentWidget().findChildren(QLabel)
    ]
    assert any("GitHub" in text for text in descriptions)

    checkbox.setChecked(True)
    assert update_settings.value(
        CHECK_UPDATES_AUTOMATICALLY_SETTING,
        type=bool,
    )
    assert all(
        "path" not in key.lower()
        and "password" not in key.lower()
        and "document" not in key.lower()
        for key in update_settings.allKeys()
    )


def test_restore_defaults_removes_update_history(update_settings) -> None:
    update_settings.setValue(CHECK_UPDATES_AUTOMATICALLY_SETTING, True)
    update_settings.setValue(LAST_UPDATE_CHECK_SETTING, "2026-07-27T00:00:00Z")
    update_settings.setValue(SKIPPED_UPDATE_VERSION_SETTING, "0.2.0")
    defaults = UiPreferences()
    defaults.save(update_settings)

    assert (
        update_settings.value(
            CHECK_UPDATES_AUTOMATICALLY_SETTING,
            type=bool,
        )
        is False
    )
    assert not update_settings.contains(LAST_UPDATE_CHECK_SETTING)
    assert not update_settings.contains(SKIPPED_UPDATE_VERSION_SETTING)


def test_disabled_automatic_updates_never_call_network(
    qtbot,
    update_settings,
    monkeypatch,
) -> None:
    calls = []
    monkeypatch.setattr(
        "pdfsilo.ui.main_window.check_for_update",
        lambda **_kwargs: calls.append(True),
    )
    window = MainWindow(update_settings)
    qtbot.addWidget(window)
    window.show()
    qtbot.wait(25)
    assert calls == []


def test_automatic_update_throttle(update_settings, qtbot) -> None:
    update_settings.setValue(CHECK_UPDATES_AUTOMATICALLY_SETTING, True)
    update_settings.setValue(
        LAST_UPDATE_CHECK_SETTING,
        datetime.now(UTC).isoformat(),
    )
    window = MainWindow(update_settings)
    qtbot.addWidget(window)
    assert window._automatic_update_check_due() is False

    window._preferences = UiPreferences(
        check_updates_automatically=True,
        last_update_check=(datetime.now(UTC) - timedelta(hours=25)).isoformat(),
    )
    assert window._automatic_update_check_due() is True


def test_update_runner_delivers_result_on_gui_thread(qtbot) -> None:
    runner = UpdateRunner()
    result_threads = []

    def task(*, progress, is_cancelled):
        assert QThread.currentThread() is not runner.thread()
        progress(1, 1, "Checked")
        assert not is_cancelled()
        return _update_info()

    runner.succeeded.connect(
        lambda _result: result_threads.append(QThread.currentThread())
    )
    with qtbot.waitSignal(runner.finished, timeout=3000):
        assert runner.start(task)
    assert result_threads == [runner.thread()]


def test_banner_announces_and_skips_update(qtbot) -> None:
    banner = UpdateBanner()
    qtbot.addWidget(banner)
    skipped = []
    banner.skipRequested.connect(skipped.append)
    banner.show_update(_update_info())

    assert banner.isVisible()
    assert "0.2.0" in banner.message_label.text()
    banner.skip_button.click()
    assert skipped == ["0.2.0"]
    assert banner.isHidden()


def test_main_window_persists_skipped_version(
    qtbot,
    update_settings,
) -> None:
    window = MainWindow(update_settings)
    qtbot.addWidget(window)
    window.skip_update_version("0.2.0")
    assert update_settings.value(SKIPPED_UPDATE_VERSION_SETTING) == "0.2.0"


def test_manual_available_update_uses_download_dialog(
    qtbot,
    update_settings,
) -> None:
    window = MainWindow(update_settings)
    qtbot.addWidget(window)
    window._update_check_manual = True
    window._update_check_succeeded(_update_info())
    dialog = window.findChild(UpdateDialog, "updateDialog")
    assert dialog is not None
    assert (
        "SHA-256"
        in dialog.findChild(
            type(dialog.status_label),
            "updateDialogDescription",
        ).text()
    )

"""Useful, non-sensitive preferences for the PDFSilo desktop interface."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pdfsilo.ui.preferences import UiPreferences
from pdfsilo.ui.theme import SPACE_LG, SPACE_MD, SPACE_SM, ThemeMode

THEME_DESCRIPTIONS = {
    ThemeMode.SYSTEM: (
        "Follow the operating-system appearance and update automatically "
        "when it changes."
    ),
    ThemeMode.LIGHT: "Always use PDFSilo's bright document workspace.",
    ThemeMode.DARK: "Always use PDFSilo's low-light document workspace.",
}


def _description(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("settingDescriptionLabel")
    label.setWordWrap(True)
    return label


def _preference_row(
    checkbox: QCheckBox,
    description: str,
    parent: QWidget,
) -> QFrame:
    row = QFrame(parent)
    row.setObjectName("settingRow")
    layout = QVBoxLayout(row)
    layout.setContentsMargins(SPACE_MD, SPACE_SM, SPACE_MD, SPACE_SM)
    layout.setSpacing(3)
    layout.addWidget(checkbox)
    layout.addWidget(_description(description, row))
    return row


class SettingsDialog(QDialog):
    """Expose focused preferences without storing sensitive values."""

    themeModeChanged = Signal(str)
    preferencesChanged = Signal(object)

    def __init__(
        self,
        mode: ThemeMode,
        parent: QWidget | None = None,
        preferences: UiPreferences | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("settingsDialog")
        self.setWindowTitle("PDFSilo Settings")
        self.setModal(False)
        self.setMinimumSize(620, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_LG, SPACE_LG, SPACE_LG, SPACE_LG)
        layout.setSpacing(SPACE_MD)

        title = QLabel("Settings", self)
        title.setObjectName("settingsTitleLabel")
        introduction = QLabel(
            "Personalize PDFSilo's appearance, workflow, and startup "
            "behavior. Changes apply immediately.",
            self,
        )
        introduction.setObjectName("settingsIntroLabel")
        introduction.setWordWrap(True)

        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("settingsTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._create_appearance_tab(), "Appearance")
        self.tabs.addTab(self._create_workflow_tab(), "Workflow")
        self.tabs.addTab(self._create_startup_tab(), "Startup and privacy")
        self._last_update_check = ""
        self._skipped_update_version = ""

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            parent=self,
        )
        buttons.setObjectName("settingsButtonBox")
        self.restore_defaults_button = QPushButton(
            "Restore defaults",
            buttons,
        )
        self.restore_defaults_button.setObjectName("restoreSettingsDefaultsButton")
        buttons.addButton(
            self.restore_defaults_button,
            QDialogButtonBox.ButtonRole.ResetRole,
        )
        self.restore_defaults_button.clicked.connect(self.restore_defaults)
        buttons.rejected.connect(self.close)

        layout.addWidget(title)
        layout.addWidget(introduction)
        layout.addWidget(self.tabs, 1)
        layout.addWidget(buttons)

        self.theme_combo.currentIndexChanged.connect(self._theme_selected)
        for checkbox in self._preference_checkboxes():
            checkbox.toggled.connect(self._preferences_selected)

        self.set_theme_mode(mode)
        self.set_preferences(preferences or UiPreferences())

    def _create_appearance_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setObjectName("appearanceSettingsTab")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(
            SPACE_MD,
            SPACE_LG,
            SPACE_MD,
            SPACE_MD,
        )
        layout.setSpacing(SPACE_MD)

        heading = QLabel("Application appearance", tab)
        heading.setObjectName("settingsSectionTitle")
        intro = _description(
            "Choose a theme that stays readable during long document sessions.",
            tab,
        )

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(SPACE_MD)
        form.setVerticalSpacing(SPACE_SM)

        self.theme_combo = QComboBox(tab)
        self.theme_combo.setObjectName("themeModeCombo")
        self.theme_combo.setAccessibleName("Application theme")
        self.theme_combo.addItem("System default", ThemeMode.SYSTEM.value)
        self.theme_combo.addItem("Light", ThemeMode.LIGHT.value)
        self.theme_combo.addItem("Dark", ThemeMode.DARK.value)
        form.addRow("&Theme", self.theme_combo)

        self.theme_description = QLabel(tab)
        self.theme_description.setObjectName("themeDescriptionLabel")
        self.theme_description.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addLayout(form)
        layout.addWidget(self.theme_description)
        layout.addStretch(1)
        return tab

    def _create_workflow_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setObjectName("workflowSettingsTab")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(
            SPACE_MD,
            SPACE_LG,
            SPACE_MD,
            SPACE_MD,
        )
        layout.setSpacing(SPACE_SM)

        heading = QLabel("Document workflow", tab)
        heading.setObjectName("settingsSectionTitle")
        intro = _description(
            "Control review, output safety, and what happens after a "
            "successful operation.",
            tab,
        )
        layout.addWidget(heading)
        layout.addWidget(intro)

        self.show_input_previews_check = QCheckBox(
            "Show input document previews",
            tab,
        )
        self.show_input_previews_check.setObjectName("showInputPreviewsCheck")
        self.show_input_previews_check.setAccessibleName("Show input document previews")
        layout.addWidget(
            _preference_row(
                self.show_input_previews_check,
                "Render PDF pages beside operation forms. Turn this off on "
                "slower devices or when screen space is limited.",
                tab,
            )
        )

        self.confirm_overwrite_check = QCheckBox(
            "Ask before replacing an existing output file",
            tab,
        )
        self.confirm_overwrite_check.setObjectName("confirmOverwriteCheck")
        self.confirm_overwrite_check.setAccessibleName(
            "Confirm before replacing output files"
        )
        layout.addWidget(
            _preference_row(
                self.confirm_overwrite_check,
                "Keeps the generated result staged until you explicitly "
                "confirm that an existing destination may be replaced.",
                tab,
            )
        )

        self.open_output_folder_check = QCheckBox(
            "Open the containing folder after saving",
            tab,
        )
        self.open_output_folder_check.setObjectName("openOutputFolderCheck")
        self.open_output_folder_check.setAccessibleName(
            "Open output folder after saving"
        )
        layout.addWidget(
            _preference_row(
                self.open_output_folder_check,
                "Open the system file manager when an operation publishes "
                "its final output.",
                tab,
            )
        )
        layout.addStretch(1)
        return tab

    def _create_startup_tab(self) -> QWidget:
        tab = QWidget(self)
        tab.setObjectName("startupSettingsTab")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(
            SPACE_MD,
            SPACE_LG,
            SPACE_MD,
            SPACE_MD,
        )
        layout.setSpacing(SPACE_SM)

        heading = QLabel("Startup behavior", tab)
        heading.setObjectName("settingsSectionTitle")
        intro = _description(
            "Choose which parts of the workspace are restored the next time "
            "PDFSilo starts.",
            tab,
        )
        layout.addWidget(heading)
        layout.addWidget(intro)

        self.restore_window_check = QCheckBox(
            "Restore window size and position",
            tab,
        )
        self.restore_window_check.setObjectName("restoreWindowCheck")
        layout.addWidget(
            _preference_row(
                self.restore_window_check,
                "Otherwise PDFSilo opens at its standard size in a safe "
                "on-screen position.",
                tab,
            )
        )

        self.reopen_last_tool_check = QCheckBox(
            "Reopen the last-used PDF tool",
            tab,
        )
        self.reopen_last_tool_check.setObjectName("reopenLastToolCheck")
        layout.addWidget(
            _preference_row(
                self.reopen_last_tool_check,
                "Otherwise every new session starts on Home.",
                tab,
            )
        )

        self.check_updates_automatically_check = QCheckBox(
            "Automatically check for PDFSilo updates",
            tab,
        )
        self.check_updates_automatically_check.setObjectName(
            "checkUpdatesAutomaticallyCheck"
        )
        self.check_updates_automatically_check.setAccessibleName(
            "Automatically check for PDFSilo updates"
        )
        layout.addWidget(
            _preference_row(
                self.check_updates_automatically_check,
                "When enabled, PDFSilo contacts GitHub at most once per day "
                "to read the latest version number. No document data, file "
                "paths, credentials, or telemetry are sent.",
                tab,
            )
        )

        privacy = QFrame(tab)
        privacy.setObjectName("settingsPrivacyCard")
        privacy_layout = QVBoxLayout(privacy)
        privacy_layout.setContentsMargins(
            SPACE_MD,
            SPACE_MD,
            SPACE_MD,
            SPACE_MD,
        )
        privacy_layout.setSpacing(SPACE_SM)
        privacy_title = QLabel("What PDFSilo remembers", privacy)
        privacy_title.setObjectName("settingsPrivacyTitle")
        privacy_text = QLabel(
            "Only the choices shown here, the last tool index, and optional "
            "window geometry are remembered. Update checks store only the "
            "last check time and a skipped version. Document paths, document "
            "contents, and passwords are never stored in application "
            "settings.",
            privacy,
        )
        privacy_text.setObjectName("settingsPrivacyText")
        privacy_text.setWordWrap(True)
        privacy_layout.addWidget(privacy_title)
        privacy_layout.addWidget(privacy_text)
        layout.addWidget(privacy)
        layout.addStretch(1)
        return tab

    def _preference_checkboxes(self) -> Iterable[QCheckBox]:
        return (
            self.restore_window_check,
            self.reopen_last_tool_check,
            self.show_input_previews_check,
            self.confirm_overwrite_check,
            self.open_output_folder_check,
            self.check_updates_automatically_check,
        )

    def preferences(self) -> UiPreferences:
        """Return the current non-sensitive preference choices."""
        return UiPreferences(
            restore_window=self.restore_window_check.isChecked(),
            reopen_last_tool=self.reopen_last_tool_check.isChecked(),
            show_input_previews=self.show_input_previews_check.isChecked(),
            confirm_overwrite=self.confirm_overwrite_check.isChecked(),
            open_output_folder=self.open_output_folder_check.isChecked(),
            check_updates_automatically=(
                self.check_updates_automatically_check.isChecked()
            ),
            last_update_check=self._last_update_check,
            skipped_update_version=self._skipped_update_version,
        )

    def set_preferences(self, preferences: UiPreferences) -> None:
        """Synchronize controls without emitting a user change."""
        self._last_update_check = preferences.last_update_check
        self._skipped_update_version = preferences.skipped_update_version
        values = (
            (self.restore_window_check, preferences.restore_window),
            (self.reopen_last_tool_check, preferences.reopen_last_tool),
            (
                self.show_input_previews_check,
                preferences.show_input_previews,
            ),
            (
                self.confirm_overwrite_check,
                preferences.confirm_overwrite,
            ),
            (
                self.open_output_folder_check,
                preferences.open_output_folder,
            ),
            (
                self.check_updates_automatically_check,
                preferences.check_updates_automatically,
            ),
        )
        for checkbox, checked in values:
            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)

    def set_theme_mode(self, mode: ThemeMode) -> None:
        """Synchronize the selector without emitting a user change."""
        index = self.theme_combo.findData(mode.value)
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(max(0, index))
        self.theme_combo.blockSignals(False)
        self.theme_description.setText(THEME_DESCRIPTIONS[mode])

    def restore_defaults(self) -> None:
        """Restore conservative defaults and notify the application."""
        self.set_theme_mode(ThemeMode.SYSTEM)
        self.set_preferences(UiPreferences())
        self.themeModeChanged.emit(ThemeMode.SYSTEM.value)
        self.preferencesChanged.emit(UiPreferences())

    def _theme_selected(self, index: int) -> None:
        mode = ThemeMode(self.theme_combo.itemData(index))
        self.theme_description.setText(THEME_DESCRIPTIONS[mode])
        self.themeModeChanged.emit(mode.value)

    def _preferences_selected(self, _checked: bool) -> None:
        self.preferencesChanged.emit(self.preferences())


__all__ = ["SettingsDialog"]

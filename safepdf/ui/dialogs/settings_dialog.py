"""Non-sensitive appearance settings for the SafePDF desktop interface."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from safepdf.ui.theme import SPACE_LG, SPACE_MD, ThemeMode

THEME_DESCRIPTIONS = {
    ThemeMode.SYSTEM: (
        "Follow the operating-system appearance and update automatically "
        "when it changes."
    ),
    ThemeMode.LIGHT: "Always use SafePDF's bright document workspace.",
    ThemeMode.DARK: "Always use SafePDF's low-light document workspace.",
}


class SettingsDialog(QDialog):
    """Expose appearance preferences without storing sensitive values."""

    themeModeChanged = Signal(str)

    def __init__(
        self,
        mode: ThemeMode,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("settingsDialog")
        self.setWindowTitle("SafePDF Settings")
        self.setModal(False)
        self.setMinimumWidth(430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_LG, SPACE_LG, SPACE_LG, SPACE_LG)
        layout.setSpacing(SPACE_MD)

        title = QLabel("Appearance", self)
        title.setObjectName("sectionTitleLabel")
        introduction = QLabel(
            "Choose how SafePDF should look. This preference contains no "
            "document or password information.",
            self,
        )
        introduction.setObjectName("sectionDescriptionLabel")
        introduction.setWordWrap(True)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(SPACE_MD)

        self.theme_combo = QComboBox(self)
        self.theme_combo.setObjectName("themeModeCombo")
        self.theme_combo.setAccessibleName("Application theme")
        self.theme_combo.addItem("System default", ThemeMode.SYSTEM.value)
        self.theme_combo.addItem("Light", ThemeMode.LIGHT.value)
        self.theme_combo.addItem("Dark", ThemeMode.DARK.value)
        form.addRow("&Theme", self.theme_combo)

        self.theme_description = QLabel(self)
        self.theme_description.setObjectName("themeDescriptionLabel")
        self.theme_description.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            parent=self,
        )
        buttons.setObjectName("settingsButtonBox")
        buttons.rejected.connect(self.close)

        layout.addWidget(title)
        layout.addWidget(introduction)
        layout.addLayout(form)
        layout.addWidget(self.theme_description)
        layout.addStretch(1)
        layout.addWidget(buttons)

        self.theme_combo.currentIndexChanged.connect(self._theme_selected)
        self.set_theme_mode(mode)

    def set_theme_mode(self, mode: ThemeMode) -> None:
        """Synchronize the selector without emitting a user change."""
        index = self.theme_combo.findData(mode.value)
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(max(0, index))
        self.theme_combo.blockSignals(False)
        self.theme_description.setText(THEME_DESCRIPTIONS[mode])

    def _theme_selected(self, index: int) -> None:
        mode = ThemeMode(self.theme_combo.itemData(index))
        self.theme_description.setText(THEME_DESCRIPTIONS[mode])
        self.themeModeChanged.emit(mode.value)


__all__ = ["SettingsDialog"]

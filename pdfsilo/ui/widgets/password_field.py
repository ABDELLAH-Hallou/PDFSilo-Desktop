"""Reusable masked password input with an explicit visibility control."""

from __future__ import annotations

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QToolButton,
    QWidget,
)


class PasswordField(QWidget):
    """Keep a password masked by default and expose deliberate visibility."""

    textChanged = Signal(str)
    visibilityChanged = Signal(bool)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        object_name: str = "passwordField",
        line_edit_object_name: str = "passwordEdit",
        accessible_name: str = "Password",
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.line_edit = QLineEdit(self)
        self.line_edit.setObjectName(line_edit_object_name)
        self.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.setAccessibleName(accessible_name)
        self.line_edit.textChanged.connect(self.textChanged.emit)
        self.setFocusProxy(self.line_edit)

        self.visibility_button = QToolButton(self)
        self.visibility_button.setObjectName(f"{line_edit_object_name}VisibilityButton")
        self.visibility_button.setText("Show")
        self.visibility_button.setCheckable(True)
        self.visibility_button.setAccessibleName(f"Show {accessible_name}")
        self.visibility_button.setToolTip("Show or hide this password on screen")
        self.visibility_button.toggled.connect(self.set_password_visible)

        layout.addWidget(self.line_edit, 1)
        layout.addWidget(self.visibility_button)

    def text(self) -> str:
        return self.line_edit.text()

    def setText(self, text: str) -> None:
        self.line_edit.setText(text)

    def is_password_visible(self) -> bool:
        return self.line_edit.echoMode() == QLineEdit.EchoMode.Normal

    @Slot()
    def clear(self) -> None:
        """Remove the secret and restore the secure masked state."""
        self.line_edit.clear()
        self.visibility_button.setChecked(False)

    @Slot(bool)
    def set_password_visible(self, visible: bool) -> None:
        self.line_edit.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        )
        self.visibility_button.setText("Hide" if visible else "Show")
        self.visibility_button.setAccessibleName(
            ("Hide" if visible else "Show") + f" {self.line_edit.accessibleName()}"
        )
        self.visibilityChanged.emit(visible)


__all__ = ["PasswordField"]

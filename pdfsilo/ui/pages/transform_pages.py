"""Compression, watermarking, and document security screens."""

from __future__ import annotations

import math

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QSpinBox,
)

from pdfsilo.operations import compress, decrypt, encrypt, watermark
from pdfsilo.ui.pages.base_operation_page import (
    OperationInvocation,
    OperationPage,
    set_default_output,
)
from pdfsilo.ui.pages.registry import PageDefinition
from pdfsilo.ui.widgets import (
    OutputFilePicker,
    PasswordField,
    SinglePdfPicker,
)


class CompressPage(OperationPage):
    """Configure PDF image compression quality."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&Source PDF", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputFilePicker(label="&Compressed PDF", parent=self)
        )
        self.quality_spin = QSpinBox(self)
        self.quality_spin.setObjectName("compressionQualitySpin")
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(60)
        self.quality_spin.setSuffix("%")
        self.add_option("Image &quality", self.quality_spin)
        self.input_picker.pathChanged.connect(
            lambda source: set_default_output(
                self.output_picker,
                source,
                "_compressed.pdf",
            )
        )
        self.finish_setup()

    def operation_invocation(self) -> OperationInvocation:
        source = self.input_picker.path()
        output = self.output_picker.path()
        assert source is not None and output is not None
        return (
            compress.execute,
            (source,),
            {
                "output_path": output,
                "quality": self.quality_spin.value(),
            },
        )


class WatermarkPage(OperationPage):
    """Configure and stamp a text watermark."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&Source PDF", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputFilePicker(label="&Watermarked PDF", parent=self)
        )
        self.text_edit = QLineEdit(self)
        self.text_edit.setObjectName("watermarkTextEdit")
        self.text_edit.setPlaceholderText("For example: CONFIDENTIAL")
        self.add_option("Watermark &text", self.text_edit)

        self.opacity_spin = QDoubleSpinBox(self)
        self.opacity_spin.setObjectName("watermarkOpacitySpin")
        self.opacity_spin.setRange(0.0, 1.0)
        self.opacity_spin.setSingleStep(0.05)
        self.opacity_spin.setDecimals(2)
        self.opacity_spin.setValue(0.15)
        self.add_option("&Opacity", self.opacity_spin)

        self.angle_spin = QDoubleSpinBox(self)
        self.angle_spin.setObjectName("watermarkAngleSpin")
        self.angle_spin.setRange(-360.0, 360.0)
        self.angle_spin.setValue(45.0)
        self.angle_spin.setSuffix("°")
        self.add_option("&Angle", self.angle_spin)

        self.font_size_spin = QDoubleSpinBox(self)
        self.font_size_spin.setObjectName("watermarkFontSizeSpin")
        self.font_size_spin.setRange(1.0, 1_000.0)
        self.font_size_spin.setValue(60.0)
        self.font_size_spin.setSuffix(" pt")
        self.add_option("&Font size", self.font_size_spin)

        self.color_edit = QLineEdit("0.5,0.5,0.5", self)
        self.color_edit.setObjectName("watermarkColorEdit")
        self.color_edit.setPlaceholderText("R,G,B values from 0.0 to 1.0")
        self.add_option("&Color", self.color_edit)

        self.watch(self.text_edit.textChanged)
        self.watch(self.color_edit.textChanged)
        self.input_picker.pathChanged.connect(
            lambda source: set_default_output(
                self.output_picker,
                source,
                "_watermarked.pdf",
            )
        )
        self.finish_setup()

    def specific_validation_error(self) -> str:
        if not self.text_edit.text().strip():
            return "Enter watermark text."
        try:
            components = [
                float(part.strip())
                for part in self.color_edit.text().split(",")
            ]
        except ValueError:
            return "Color must be three numbers separated by commas."
        if len(components) != 3:
            return "Color must have exactly three components: R,G,B."
        if not all(
            math.isfinite(component) and 0.0 <= component <= 1.0
            for component in components
        ):
            return "Color components must be between 0.0 and 1.0."
        return ""

    def operation_invocation(self) -> OperationInvocation:
        source = self.input_picker.path()
        output = self.output_picker.path()
        assert source is not None and output is not None
        return (
            watermark.execute,
            (source, self.text_edit.text().strip()),
            {
                "output_path": output,
                "opacity": self.opacity_spin.value(),
                "angle": self.angle_spin.value(),
                "font_size": self.font_size_spin.value(),
                "color": self.color_edit.text().strip(),
            },
        )


class EncryptPage(OperationPage):
    """Protect a PDF and optionally restrict its permissions."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&Source PDF", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputFilePicker(label="&Encrypted PDF", parent=self)
        )
        user_help = QLabel(
            "The user password opens the PDF. Share it with people who "
            "should be able to read the document.",
            self.form_container,
        )
        user_help.setObjectName("passwordRoleLabel")
        user_help.setWordWrap(True)
        self.form_layout.addRow(user_help)

        self.user_password_field = PasswordField(
            self.form_container,
            object_name="userPasswordField",
            line_edit_object_name="userPasswordEdit",
            accessible_name="User password",
        )
        self.user_password_confirmation_field = PasswordField(
            self.form_container,
            object_name="userPasswordConfirmationField",
            line_edit_object_name="userPasswordConfirmationEdit",
            accessible_name="Confirm user password",
        )
        # Preserve the concise QLineEdit aliases used by existing callers.
        self.user_password_edit = self.user_password_field.line_edit
        self.user_password_confirmation_edit = (
            self.user_password_confirmation_field.line_edit
        )
        self.add_option("&User password", self.user_password_field)
        self.add_option(
            "C&onfirm user password",
            self.user_password_confirmation_field,
        )

        owner_help = QLabel(
            "The owner password controls permissions. A distinct owner "
            "password is required when printing, copying, or editing is "
            "restricted.",
            self.form_container,
        )
        owner_help.setObjectName("passwordRoleLabel")
        owner_help.setWordWrap(True)
        self.form_layout.addRow(owner_help)

        self.owner_password_field = PasswordField(
            self.form_container,
            object_name="ownerPasswordField",
            line_edit_object_name="ownerPasswordEdit",
            accessible_name="Owner password",
        )
        self.owner_password_confirmation_field = PasswordField(
            self.form_container,
            object_name="ownerPasswordConfirmationField",
            line_edit_object_name="ownerPasswordConfirmationEdit",
            accessible_name="Confirm owner password",
        )
        self.owner_password_edit = self.owner_password_field.line_edit
        self.owner_password_confirmation_edit = (
            self.owner_password_confirmation_field.line_edit
        )
        self.add_option("&Owner password", self.owner_password_field)
        self.add_option(
            "Confirm o&wner password",
            self.owner_password_confirmation_field,
        )

        self.allow_print_checkbox = self._permission_checkbox(
            "Allow printing",
            "allowPrintCheck",
        )
        self.allow_copy_checkbox = self._permission_checkbox(
            "Allow copying",
            "allowCopyCheck",
        )
        self.allow_edit_checkbox = self._permission_checkbox(
            "Allow editing and annotations",
            "allowEditCheck",
        )
        self.form_layout.addRow(self.allow_print_checkbox)
        self.form_layout.addRow(self.allow_copy_checkbox)
        self.form_layout.addRow(self.allow_edit_checkbox)

        self.watch(self.user_password_edit.textChanged)
        self.watch(self.user_password_confirmation_edit.textChanged)
        self.watch(self.owner_password_edit.textChanged)
        self.watch(self.owner_password_confirmation_edit.textChanged)
        for checkbox in self._permission_checkboxes:
            self.watch(checkbox.toggled)

        self.input_picker.pathChanged.connect(
            lambda source: set_default_output(
                self.output_picker,
                source,
                "_encrypted.pdf",
            )
        )
        self.controller.runner.finished.connect(self._clear_passwords)
        self.finish_setup()

    @property
    def _permission_checkboxes(self) -> tuple[QCheckBox, ...]:
        return (
            self.allow_print_checkbox,
            self.allow_copy_checkbox,
            self.allow_edit_checkbox,
        )

    def _permission_checkbox(
        self,
        text: str,
        object_name: str,
    ) -> QCheckBox:
        checkbox = QCheckBox(text, self)
        checkbox.setObjectName(object_name)
        checkbox.setChecked(True)
        return checkbox

    def _restrictions_requested(self) -> bool:
        return not all(
            checkbox.isChecked()
            for checkbox in self._permission_checkboxes
        )

    def specific_validation_error(self) -> str:
        user_password = self.user_password_edit.text()
        user_confirmation = self.user_password_confirmation_edit.text()
        owner_password = self.owner_password_edit.text()
        owner_confirmation = self.owner_password_confirmation_edit.text()
        if not user_password:
            return "Enter a user password."
        if user_confirmation != user_password:
            return "User password confirmation does not match."
        if self._restrictions_requested() and not owner_password:
            return (
                "A distinct owner password is required when permissions "
                "are restricted."
            )
        if owner_password != owner_confirmation:
            return "Owner password confirmation does not match."
        if (
            self._restrictions_requested()
            and owner_password == user_password
        ):
            return (
                "Owner and user passwords must differ when permissions "
                "are restricted."
            )
        return ""

    def operation_invocation(self) -> OperationInvocation:
        source = self.input_picker.path()
        output = self.output_picker.path()
        assert source is not None and output is not None
        return (
            encrypt.execute,
            (source, self.user_password_edit.text()),
            {
                "owner_password": self.owner_password_edit.text() or None,
                "output_path": output,
                "allow_print": self.allow_print_checkbox.isChecked(),
                "allow_copy": self.allow_copy_checkbox.isChecked(),
                "allow_edit": self.allow_edit_checkbox.isChecked(),
            },
        )

    def _clear_passwords(self) -> None:
        self.user_password_field.clear()
        self.user_password_confirmation_field.clear()
        self.owner_password_field.clear()
        self.owner_password_confirmation_field.clear()


class DecryptPage(OperationPage):
    """Unlock a PDF using a user or owner password."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&Encrypted PDF", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputFilePicker(label="&Decrypted PDF", parent=self)
        )
        password_help = QLabel(
            "Enter either the user password or the owner password used to "
            "unlock this PDF.",
            self.form_container,
        )
        password_help.setObjectName("passwordRoleLabel")
        password_help.setWordWrap(True)
        self.form_layout.addRow(password_help)
        self.password_field = PasswordField(
            self.form_container,
            object_name="decryptPasswordField",
            line_edit_object_name="decryptPasswordEdit",
            accessible_name="PDF password",
        )
        self.password_edit = self.password_field.line_edit
        self.add_option("&Password", self.password_field)
        self.watch(self.password_edit.textChanged)
        self.input_picker.pathChanged.connect(
            lambda source: set_default_output(
                self.output_picker,
                source,
                "_decrypted.pdf",
            )
        )
        self.controller.runner.finished.connect(self.password_field.clear)
        self.finish_setup()

    def specific_validation_error(self) -> str:
        return "" if self.password_edit.text() else "Enter the PDF password."

    def operation_invocation(self) -> OperationInvocation:
        source = self.input_picker.path()
        output = self.output_picker.path()
        assert source is not None and output is not None
        return (
            decrypt.execute,
            (source, self.password_edit.text()),
            {"output_path": output},
        )


__all__ = [
    "CompressPage",
    "DecryptPage",
    "EncryptPage",
    "WatermarkPage",
]

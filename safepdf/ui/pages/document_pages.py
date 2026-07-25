"""Basic document workflow screens."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox, QLineEdit, QSpinBox

from safepdf.operations import concat, extract_range, rotate, split
from safepdf.ui.pages.base_operation_page import (
    OperationInvocation,
    OperationPage,
    set_default_output,
)
from safepdf.ui.pages.registry import PageDefinition
from safepdf.ui.widgets import (
    MultiplePdfPicker,
    OutputDirectoryPicker,
    OutputFilePicker,
    SinglePdfPicker,
)


def _positive_page_list_error(value: str, *, required: bool = False) -> str:
    text = value.strip()
    if not text:
        return "Enter at least one page number." if required else ""
    parts = [part.strip() for part in text.split(",")]
    if any(not part or not part.isdigit() or int(part) < 1 for part in parts):
        return "Page numbers must be positive integers separated by commas."
    return ""


class MergePage(OperationPage):
    """Collect PDF inputs and merge them in their displayed order."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            MultiplePdfPicker(label="&PDF files to merge", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputFilePicker(label="&Merged PDF", parent=self)
        )
        self.target_size_combo = QComboBox(self)
        self.target_size_combo.setObjectName("targetPageSizeCombo")
        self.target_size_combo.addItems(["A4", "Letter"])
        self.add_option("&Target page size", self.target_size_combo)

        self.input_picker.pathChanged.connect(self._set_default_output)
        self.finish_setup()
        assert self.pdf_preview is not None
        self.pdf_preview.set_target_page_size(
            self.target_size_combo.currentText()
        )
        self.target_size_combo.currentTextChanged.connect(
            self.pdf_preview.set_target_page_size
        )

    def _set_default_output(self, source: Path | None) -> None:
        if source is not None and self.output_picker.path() is None:
            self.output_picker.set_path(source.parent / "merged.pdf")

    def operation_invocation(self) -> OperationInvocation:
        output = self.output_picker.path()
        assert output is not None
        return (
            concat.execute,
            (self.input_picker.paths(), output),
            {"target_size": self.target_size_combo.currentText()},
        )


class SplitPage(OperationPage):
    """Split every input page into a separate PDF."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&PDF to split", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputDirectoryPicker(label="Output &folder", parent=self)
        )
        self.input_picker.pathChanged.connect(
            lambda source: (
                self.output_picker.set_path(
                    source.parent / f"{source.stem}_pages"
                )
                if source is not None and self.output_picker.path() is None
                else None
            )
        )
        self.finish_setup()

    def operation_invocation(self) -> OperationInvocation:
        source = self.input_picker.path()
        output = self.output_picker.path()
        assert source is not None and output is not None
        return split.execute, (source, output), {}


class RotatePage(OperationPage):
    """Rotate all pages or a comma-separated page selection."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&PDF to rotate", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputFilePicker(label="&Rotated PDF", parent=self)
        )

        self.angle_combo = QComboBox(self)
        self.angle_combo.setObjectName("rotationAngleCombo")
        self.angle_combo.addItems(["90", "180", "270"])
        self.add_option("Rotation &angle", self.angle_combo)

        self.pages_edit = QLineEdit(self)
        self.pages_edit.setObjectName("pageSelectionEdit")
        self.pages_edit.setPlaceholderText("Leave blank for all pages, or 1,3,5")
        self.add_option("&Pages", self.pages_edit)
        self.watch(self.pages_edit.textChanged)

        self.input_picker.pathChanged.connect(
            lambda source: set_default_output(
                self.output_picker,
                source,
                "_rotated.pdf",
            )
        )
        self.finish_setup()

    def specific_validation_error(self) -> str:
        return _positive_page_list_error(self.pages_edit.text())

    def operation_invocation(self) -> OperationInvocation:
        source = self.input_picker.path()
        output = self.output_picker.path()
        assert source is not None and output is not None
        pages = self.pages_edit.text().strip() or None
        return (
            rotate.execute,
            (source, int(self.angle_combo.currentText())),
            {"pages": pages, "output_path": output},
        )


class ExtractRangePage(OperationPage):
    """Extract an inclusive, one-indexed page range."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&Source PDF", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputFilePicker(label="&Extracted PDF", parent=self)
        )

        self.start_spin = QSpinBox(self)
        self.start_spin.setObjectName("rangeStartSpin")
        self.start_spin.setRange(1, 999_999)
        self.start_spin.setValue(1)
        self.add_option("&First page", self.start_spin)

        self.end_spin = QSpinBox(self)
        self.end_spin.setObjectName("rangeEndSpin")
        self.end_spin.setRange(1, 999_999)
        self.end_spin.setValue(1)
        self.add_option("&Last page", self.end_spin)
        self.watch(self.start_spin.valueChanged)
        self.watch(self.end_spin.valueChanged)

        self.input_picker.pathChanged.connect(self._set_default_output)
        self.finish_setup()

    def _set_default_output(self, source: Path | None) -> None:
        if source is not None and self.output_picker.path() is None:
            self.output_picker.set_path(
                source.with_name(
                    f"{source.stem}_p{self.start_spin.value()}"
                    f"-p{self.end_spin.value()}.pdf"
                )
            )

    def specific_validation_error(self) -> str:
        if self.start_spin.value() > self.end_spin.value():
            return "The first page cannot be after the last page."
        return ""

    def operation_invocation(self) -> OperationInvocation:
        source = self.input_picker.path()
        output = self.output_picker.path()
        assert source is not None and output is not None
        return (
            extract_range.execute,
            (source, self.start_spin.value(), self.end_spin.value()),
            {"output_path": output},
        )


__all__ = [
    "ExtractRangePage",
    "MergePage",
    "RotatePage",
    "SplitPage",
]

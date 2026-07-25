"""Page ordering and image-oriented operation screens."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
)

from pdfsilo.operations import (
    add_images,
    extract_images,
    images_to_pdf,
    reorder,
    to_images,
)
from pdfsilo.ui.pages.base_operation_page import (
    OperationInvocation,
    OperationPage,
    set_default_output,
)
from pdfsilo.ui.pages.registry import PageDefinition
from pdfsilo.ui.widgets import (
    ImageFilePicker,
    OutputDirectoryPicker,
    OutputFilePicker,
    PageReorderEditor,
    SinglePdfPicker,
)


def _format_combo(parent: OperationPage) -> QComboBox:
    combo = QComboBox(parent)
    combo.setObjectName("imageFormatCombo")
    combo.addItem("PNG", "png")
    combo.addItem("JPEG", "jpeg")
    return combo


class ReorderPage(OperationPage):
    """Rearrange, duplicate, or omit pages."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&Source PDF", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputFilePicker(label="&Reordered PDF", parent=self)
        )
        self.page_editor = PageReorderEditor(self.form_container)
        self.add_option("Page &order", self.page_editor)
        self.watch(self.page_editor.orderChanged)
        self.input_picker.pathChanged.connect(self.page_editor.set_pdf)
        self.input_picker.pathChanged.connect(
            lambda source: set_default_output(
                self.output_picker,
                source,
                "_reordered.pdf",
            )
        )
        self.finish_setup(add_pdf_preview=False)

    def specific_validation_error(self) -> str:
        if not self.page_editor.order_string():
            return "Load and keep at least one page in the output order."
        return ""

    def operation_invocation(self) -> OperationInvocation:
        source = self.input_picker.path()
        output = self.output_picker.path()
        assert source is not None and output is not None
        return (
            reorder.execute,
            (source, self.page_editor.order_string()),
            {"output_path": output},
        )


class ToImagesPage(OperationPage):
    """Render each PDF page to a raster image."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&Source PDF", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputDirectoryPicker(label="Output &folder", parent=self)
        )
        self.format_combo = _format_combo(self)
        self.add_option("Image &format", self.format_combo)
        self.dpi_spin = QSpinBox(self)
        self.dpi_spin.setObjectName("renderDpiSpin")
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(150)
        self.dpi_spin.setSuffix(" DPI")
        self.add_option("&Resolution", self.dpi_spin)
        self.input_picker.pathChanged.connect(
            lambda source: (
                self.output_picker.set_path(
                    source.parent / f"{source.stem}_rendered"
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
        return (
            to_images.execute,
            (source, output),
            {
                "fmt": self.format_combo.currentData(),
                "dpi": self.dpi_spin.value(),
            },
        )


class ImagesToPdfPage(OperationPage):
    """Build a PDF from explicitly selected images in displayed order."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            ImageFilePicker(label="&Images in page order", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputFilePicker(label="&Output PDF", parent=self)
        )
        self.target_size_combo = QComboBox(self)
        self.target_size_combo.setObjectName("targetPageSizeCombo")
        self.target_size_combo.addItems(["A4", "Letter"])
        self.add_option("&Target page size", self.target_size_combo)

        self.fit_checkbox = QCheckBox("Scale images to fit the page", self)
        self.fit_checkbox.setObjectName("fitImagesCheck")
        self.fit_checkbox.setChecked(True)
        self.form_layout.addRow(self.fit_checkbox)

        self.margin_spin = QDoubleSpinBox(self)
        self.margin_spin.setObjectName("imageMarginSpin")
        self.margin_spin.setRange(0.0, 250.0)
        self.margin_spin.setDecimals(1)
        self.margin_spin.setValue(36.0)
        self.margin_spin.setSuffix(" pt")
        self.add_option("&Margin", self.margin_spin)
        self.fit_checkbox.toggled.connect(self.margin_spin.setEnabled)

        self.input_picker.pathChanged.connect(self._set_default_output)
        self.finish_setup()

    def _set_default_output(self, image: Path | None) -> None:
        if image is not None and self.output_picker.path() is None:
            self.output_picker.set_path(image.parent / "images.pdf")

    def operation_invocation(self) -> OperationInvocation:
        output = self.output_picker.path()
        assert output is not None
        return (
            images_to_pdf.execute,
            (None,),
            {
                "output_path": output,
                "target_size": self.target_size_combo.currentText(),
                "fit": self.fit_checkbox.isChecked(),
                "margin": self.margin_spin.value(),
                "image_paths": self.input_picker.paths(),
            },
        )


class ExtractImagesPage(OperationPage):
    """Extract unique images embedded in a PDF."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&Source PDF", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputDirectoryPicker(label="Output &folder", parent=self)
        )
        self.format_combo = _format_combo(self)
        self.add_option("Image &format", self.format_combo)
        self.input_picker.pathChanged.connect(
            lambda source: (
                self.output_picker.set_path(
                    source.parent / f"{source.stem}_images"
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
        return (
            extract_images.execute,
            (source, output),
            {"fmt": self.format_combo.currentData()},
        )


class AddImagesPage(OperationPage):
    """Place image files onto PDF pages or append new pages."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__(definition)
        self.input_picker = self.add_picker(
            SinglePdfPicker(label="&Source PDF", parent=self)
        )
        self.images_picker = self.add_picker(
            ImageFilePicker(label="&Images to add", parent=self)
        )
        self.output_picker = self.add_picker(
            OutputFilePicker(label="&Output PDF", parent=self)
        )

        self.append_checkbox = QCheckBox(
            "Append one new page for each image",
            self,
        )
        self.append_checkbox.setObjectName("appendImagesCheck")
        self.form_layout.addRow(self.append_checkbox)

        self.page_spin = QSpinBox(self)
        self.page_spin.setObjectName("targetPageSpin")
        self.page_spin.setRange(0, 999_999)
        self.page_spin.setSpecialValueText("Sequential")
        self.add_option("Target &page", self.page_spin)

        self.x_spin = self._coordinate_spin("imageXSpin", 72.0)
        self.y_spin = self._coordinate_spin("imageYSpin", 72.0)
        self.add_option("&X coordinate", self.x_spin)
        self.add_option("&Y coordinate", self.y_spin)

        self.width_spin = self._dimension_spin("imageWidthSpin")
        self.height_spin = self._dimension_spin("imageHeightSpin")
        self.add_option("Image &width", self.width_spin)
        self.add_option("Image &height", self.height_spin)

        self.append_checkbox.toggled.connect(self.page_spin.setDisabled)
        self.input_picker.pathChanged.connect(
            lambda source: set_default_output(
                self.output_picker,
                source,
                "_with_images.pdf",
            )
        )
        self.finish_setup()

    def _coordinate_spin(
        self,
        object_name: str,
        value: float,
    ) -> QDoubleSpinBox:
        spin = QDoubleSpinBox(self)
        spin.setObjectName(object_name)
        spin.setRange(0.0, 100_000.0)
        spin.setDecimals(1)
        spin.setValue(value)
        spin.setSuffix(" pt")
        return spin

    def _dimension_spin(self, object_name: str) -> QDoubleSpinBox:
        spin = QDoubleSpinBox(self)
        spin.setObjectName(object_name)
        spin.setRange(0.0, 100_000.0)
        spin.setDecimals(1)
        spin.setSpecialValueText("Auto")
        spin.setSuffix(" pt")
        return spin

    @staticmethod
    def _optional_dimension(spin: QDoubleSpinBox) -> float | None:
        return spin.value() if spin.value() > 0 else None

    def operation_invocation(self) -> OperationInvocation:
        source = self.input_picker.path()
        output = self.output_picker.path()
        assert source is not None and output is not None
        page = None if self.append_checkbox.isChecked() else self.page_spin.value()
        return (
            add_images.execute,
            (source, self.images_picker.paths()),
            {
                "output_path": output,
                "page": page or None,
                "position": f"{self.x_spin.value()},{self.y_spin.value()}",
                "width": self._optional_dimension(self.width_spin),
                "height": self._optional_dimension(self.height_spin),
                "append": self.append_checkbox.isChecked(),
            },
        )


__all__ = [
    "AddImagesPage",
    "ExtractImagesPage",
    "ImagesToPdfPage",
    "ReorderPage",
    "ToImagesPage",
]

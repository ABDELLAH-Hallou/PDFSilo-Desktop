"""Specialized PDF and image file pickers."""

from pathlib import Path
from typing import Iterable

from PySide6.QtWidgets import QWidget

from safepdf.ui.widgets.path_picker import PathPicker, PickerMode
from safepdf.utils import IMAGE_EXTENSIONS

PDF_FILTER = "PDF documents (*.pdf);;All files (*)"
IMAGE_FILTER = (
    "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.gif *.webp);;"
    "All files (*)"
)


class SinglePdfPicker(PathPicker):
    """Select and validate one existing PDF."""

    def __init__(
        self,
        *,
        label: str = "&PDF file",
        required: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            label=label,
            mode=PickerMode.OPEN_FILE,
            dialog_title="Choose PDF",
            file_filter=PDF_FILTER,
            allowed_suffixes={".pdf"},
            required=required,
            object_name="singlePdfPicker",
            parent=parent,
        )


class MultiplePdfPicker(PathPicker):
    """Select and validate one or more existing PDFs."""

    def __init__(
        self,
        *,
        label: str = "&PDF files",
        required: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            label=label,
            mode=PickerMode.OPEN_FILES,
            dialog_title="Choose PDF files",
            file_filter=PDF_FILTER,
            allowed_suffixes={".pdf"},
            required=required,
            object_name="multiplePdfPicker",
            parent=parent,
        )


class ImageFilePicker(PathPicker):
    """Select and validate one or more supported image files."""

    def __init__(
        self,
        *,
        label: str = "&Image files",
        required: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            label=label,
            mode=PickerMode.OPEN_FILES,
            dialog_title="Choose image files",
            file_filter=IMAGE_FILTER,
            allowed_suffixes=IMAGE_EXTENSIONS,
            required=required,
            object_name="imageFilePicker",
            parent=parent,
        )

    def set_images(self, paths: Iterable[Path | str]) -> None:
        """Semantic alias used by image-oriented operation pages."""
        self.set_paths(paths)


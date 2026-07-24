"""Reusable output file and directory pickers."""

from typing import Iterable

from PySide6.QtWidgets import QWidget

from safepdf.ui.widgets.path_picker import PathPicker, PickerMode


class OutputFilePicker(PathPicker):
    """Select and validate a writable output-file location."""

    def __init__(
        self,
        *,
        label: str = "&Output file",
        allowed_suffixes: Iterable[str] = (".pdf",),
        file_filter: str = "PDF documents (*.pdf);;All files (*)",
        required: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            label=label,
            mode=PickerMode.SAVE_FILE,
            dialog_title="Choose output file",
            file_filter=file_filter,
            allowed_suffixes=allowed_suffixes,
            required=required,
            object_name="outputFilePicker",
            parent=parent,
        )


class OutputDirectoryPicker(PathPicker):
    """Select an existing or creatable output directory."""

    def __init__(
        self,
        *,
        label: str = "Output &folder",
        required: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            label=label,
            mode=PickerMode.OUTPUT_DIRECTORY,
            dialog_title="Choose output folder",
            required=required,
            object_name="outputDirectoryPicker",
            parent=parent,
        )


"""Reusable existing-folder picker."""

from PySide6.QtWidgets import QWidget

from safepdf.ui.widgets.path_picker import PathPicker, PickerMode


class FolderPicker(PathPicker):
    """Select and validate one existing folder."""

    def __init__(
        self,
        *,
        label: str = "&Folder",
        required: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            label=label,
            mode=PickerMode.EXISTING_DIRECTORY,
            dialog_title="Choose folder",
            required=required,
            object_name="folderPicker",
            parent=parent,
        )


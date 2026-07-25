"""Specialized PDF and image file pickers."""

from pathlib import Path
from typing import Iterable

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from pdfsilo.ui.widgets.path_picker import PathPicker, PickerMode
from pdfsilo.utils import IMAGE_EXTENSIONS

PDF_FILTER = "PDF documents (*.pdf);;All files (*)"
IMAGE_FILTER = (
    "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.gif *.webp);;"
    "All files (*)"
)


class OrderedFilesPicker(PathPicker):
    """Select files incrementally and expose their processing order."""

    def __init__(
        self,
        *,
        label: str,
        dialog_title: str,
        file_filter: str,
        allowed_suffixes: Iterable[str],
        required: bool,
        object_name: str,
        parent: QWidget | None,
    ) -> None:
        super().__init__(
            label=label,
            mode=PickerMode.OPEN_FILES,
            dialog_title=dialog_title,
            file_filter=file_filter,
            allowed_suffixes=allowed_suffixes,
            required=required,
            object_name=object_name,
            parent=parent,
        )
        self._syncing_list = False

        # Keep the inherited line edit as a compatibility/accessibility value
        # store, while presenting multiple inputs as an ordered collection.
        self.line_edit.hide()
        self.browse_button.hide()

        self.file_list = QListWidget(self)
        self.file_list.setObjectName("orderedFileList")
        self.file_list.setAccessibleName(label.replace("&", ""))
        self.file_list.setAccessibleDescription(
            "Files are processed from top to bottom. Drag rows to reorder them."
        )
        self.file_list.setMinimumHeight(148)
        self.file_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.file_list.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove
        )
        self.file_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.file_list.setDropIndicatorShown(True)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(8)

        self.add_button = QPushButton("&Add files…", self)
        self.add_button.setObjectName("addFilesButton")
        self.add_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
        )
        self.add_button.setAccessibleName(
            f"Add {label.replace('&', '').lower()}"
        )

        self.remove_button = QPushButton("&Remove", self)
        self.remove_button.setObjectName("removeFilesButton")
        self.move_up_button = QPushButton("Move &up", self)
        self.move_up_button.setObjectName("moveFileUpButton")
        self.move_down_button = QPushButton("Move &down", self)
        self.move_down_button.setObjectName("moveFileDownButton")
        self.clear_button = QPushButton("C&lear", self)
        self.clear_button.setObjectName("clearFilesButton")

        controls.addWidget(self.add_button)
        controls.addWidget(self.remove_button)
        controls.addWidget(self.move_up_button)
        controls.addWidget(self.move_down_button)
        controls.addWidget(self.clear_button)
        controls.addStretch(1)

        picker_layout = self.layout()
        assert isinstance(picker_layout, QVBoxLayout)
        picker_layout.insertWidget(1, self.file_list)
        picker_layout.insertLayout(2, controls)

        self.label.setBuddy(self.file_list)
        self.add_button.clicked.connect(self.browse)
        self.remove_button.clicked.connect(self.remove_selected)
        self.move_up_button.clicked.connect(lambda: self._move_selected(-1))
        self.move_down_button.clicked.connect(lambda: self._move_selected(1))
        self.clear_button.clicked.connect(self.clear)
        self.file_list.itemSelectionChanged.connect(
            self._update_action_states
        )
        self.file_list.model().rowsMoved.connect(self._order_changed)
        self._update_action_states()

    def _apply_paths(
        self,
        paths: list[Path],
        *,
        update_text: bool = True,
    ) -> None:
        super()._apply_paths(paths, update_text=update_text)
        self._sync_list()

    def _sync_list(self) -> None:
        self._syncing_list = True
        self.file_list.clear()
        for position, path in enumerate(self.paths(), start=1):
            item = QListWidgetItem(f"{position}.  {path.name}")
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(str(path))
            self.file_list.addItem(item)
        self._syncing_list = False
        self._update_action_states()

    def add_paths(self, paths: Iterable[Path | str]) -> None:
        """Append new, non-duplicate files without replacing prior choices."""
        combined = self.paths()
        for candidate in (Path(path).expanduser() for path in paths):
            if candidate not in combined:
                combined.append(candidate)
        self.set_paths(combined)

    def browse(self) -> None:
        """Choose more files and append them to the displayed order."""
        initial = str(self.path().parent if self.path() else Path.cwd())
        selected, _ = QFileDialog.getOpenFileNames(
            self,
            self.dialog_title,
            initial,
            self.file_filter,
        )
        if selected:
            self.add_paths(selected)

    def accept_dropped_paths(self, paths: Iterable[Path | str]) -> bool:
        """Append valid dropped files to the current ordered collection."""
        candidates = [Path(path).expanduser() for path in paths]
        combined = self.paths()
        combined.extend(path for path in candidates if path not in combined)
        valid, message = self._validate_paths(combined)
        if not valid:
            self._set_validation_state("invalid", message)
            self.validationChanged.emit(False, message)
            return False
        self._apply_paths(combined)
        return True

    @Slot()
    def remove_selected(self) -> None:
        selected_rows = {
            self.file_list.row(item)
            for item in self.file_list.selectedItems()
        }
        if not selected_rows:
            return
        self.set_paths(
            path
            for index, path in enumerate(self.paths())
            if index not in selected_rows
        )

    def _move_selected(self, offset: int) -> None:
        selected = self.file_list.selectedItems()
        if len(selected) != 1:
            return
        row = self.file_list.row(selected[0])
        destination = row + offset
        if destination < 0 or destination >= self.file_list.count():
            return
        paths = self.paths()
        paths[row], paths[destination] = paths[destination], paths[row]
        self.set_paths(paths)
        self.file_list.setCurrentRow(destination)

    @Slot()
    def _order_changed(self, *_args: object) -> None:
        if self._syncing_list:
            return
        paths = [
            self.file_list.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self.file_list.count())
        ]
        # The view already performed the move. Update the stable picker API
        # without resetting the model from inside its rowsMoved signal.
        PathPicker._apply_paths(self, [Path(path) for path in paths])
        for row in range(self.file_list.count()):
            item = self.file_list.item(row)
            path = item.data(Qt.ItemDataRole.UserRole)
            item.setText(f"{row + 1}.  {Path(path).name}")
        self._update_action_states()

    @Slot()
    def _update_action_states(self) -> None:
        selected = self.file_list.selectedItems()
        one_selected = len(selected) == 1
        row = self.file_list.row(selected[0]) if one_selected else -1
        self.remove_button.setEnabled(bool(selected))
        self.move_up_button.setEnabled(one_selected and row > 0)
        self.move_down_button.setEnabled(
            one_selected and row + 1 < self.file_list.count()
        )
        self.clear_button.setEnabled(self.file_list.count() > 0)

    def _set_validation_state(self, state: str, message: str) -> None:
        super()._set_validation_state(state, message)
        if not hasattr(self, "file_list"):
            return
        self.file_list.setProperty("validationState", state)
        self.file_list.style().unpolish(self.file_list)
        self.file_list.style().polish(self.file_list)
        self.file_list.update()


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


class MultiplePdfPicker(OrderedFilesPicker):
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
            dialog_title="Choose PDF files",
            file_filter=PDF_FILTER,
            allowed_suffixes={".pdf"},
            required=required,
            object_name="multiplePdfPicker",
            parent=parent,
        )


class ImageFilePicker(OrderedFilesPicker):
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

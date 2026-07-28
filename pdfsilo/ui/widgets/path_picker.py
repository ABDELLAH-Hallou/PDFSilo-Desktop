"""Shared path selection, validation, browsing, and drag-and-drop behavior."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QMimeData, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

PATH_SEPARATOR = "; "


class PickerMode(Enum):
    """Describe how a picker selects and validates paths."""

    OPEN_FILE = "open_file"
    OPEN_FILES = "open_files"
    EXISTING_DIRECTORY = "existing_directory"
    SAVE_FILE = "save_file"
    OUTPUT_DIRECTORY = "output_directory"


def paths_from_mime_data(mime_data: QMimeData) -> list[Path]:
    """Return local filesystem paths from a Qt drag payload."""
    if not mime_data.hasUrls():
        return []
    return [
        Path(url.toLocalFile())
        for url in mime_data.urls()
        if url.isLocalFile() and url.toLocalFile()
    ]


class PathPicker(QWidget):
    """Configurable picker used by all specialized file and folder widgets."""

    pathChanged = Signal(object)
    pathsChanged = Signal(list)
    validityChanged = Signal(bool)
    validationChanged = Signal(bool, str)

    def __init__(
        self,
        *,
        label: str,
        mode: PickerMode,
        dialog_title: str,
        file_filter: str = "All files (*)",
        allowed_suffixes: Iterable[str] = (),
        required: bool = True,
        object_name: str = "pathPicker",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.mode = mode
        self.dialog_title = dialog_title
        self.file_filter = file_filter
        self.allowed_suffixes = frozenset(
            suffix.lower() if suffix.startswith(".") else f".{suffix.lower()}"
            for suffix in allowed_suffixes
        )
        self.required = required
        self._paths: list[Path] = []
        self._last_validity: bool | None = None

        self.setObjectName(object_name)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.label = QLabel(label, self)
        self.label.setObjectName("pathPickerLabel")

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self.line_edit = QLineEdit(self)
        self.line_edit.setObjectName("pathLineEdit")
        self.line_edit.setPlaceholderText(self._placeholder_text())
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.setAcceptDrops(False)
        self.line_edit.setAccessibleName(label.replace("&", ""))
        self.line_edit.setAccessibleDescription(
            "Enter a local path or drop a compatible item onto this picker."
        )
        self.line_edit.textEdited.connect(self._on_text_edited)
        self.label.setBuddy(self.line_edit)

        self.browse_button = QPushButton("&Choose…", self)
        self.browse_button.setObjectName("browseButton")
        icon_type = (
            QStyle.StandardPixmap.SP_DirOpenIcon
            if self.expects_directory
            else QStyle.StandardPixmap.SP_DialogOpenButton
        )
        self.browse_button.setIcon(self.style().standardIcon(icon_type))
        self.browse_button.setAccessibleName(
            f"Browse for {label.replace('&', '').lower()}"
        )
        self.browse_button.clicked.connect(self.browse)

        row.addWidget(self.line_edit, 1)
        row.addWidget(self.browse_button)

        self.error_label = QLabel("", self)
        self.error_label.setObjectName("pathErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        layout.addWidget(self.label)
        layout.addLayout(row)
        layout.addWidget(self.error_label)
        self._set_validation_state("neutral", "")

    @property
    def allows_multiple(self) -> bool:
        return self.mode is PickerMode.OPEN_FILES

    @property
    def expects_directory(self) -> bool:
        return self.mode in {
            PickerMode.EXISTING_DIRECTORY,
            PickerMode.OUTPUT_DIRECTORY,
        }

    @property
    def is_output(self) -> bool:
        return self.mode in {
            PickerMode.SAVE_FILE,
            PickerMode.OUTPUT_DIRECTORY,
        }

    def _placeholder_text(self) -> str:
        if self.allows_multiple:
            return f"Enter paths separated by '{PATH_SEPARATOR.strip()}'"
        if self.expects_directory:
            return "Choose or enter a local folder"
        return "Choose or enter a local file"

    def path(self) -> Path | None:
        """Return the first selected path, if any."""
        return self._paths[0] if self._paths else None

    def paths(self) -> list[Path]:
        """Return a defensive copy of all selected paths."""
        return list(self._paths)

    def set_path(self, path: Path | str | None) -> None:
        """Set or clear the single selected path."""
        self.set_paths([] if path is None else [path])

    def set_paths(self, paths: Iterable[Path | str]) -> None:
        """Set selected paths, validate them, and emit the stable API signals."""
        normalized = [Path(path).expanduser() for path in paths if str(path)]
        if not self.allows_multiple and len(normalized) > 1:
            raise ValueError("This picker accepts only one path.")
        self._apply_paths(normalized)

    def clear(self) -> None:
        """Clear the current selection."""
        self._apply_paths([])

    def _apply_paths(
        self,
        paths: list[Path],
        *,
        update_text: bool = True,
    ) -> None:
        self._paths = paths
        if update_text:
            self.line_edit.setText(PATH_SEPARATOR.join(str(path) for path in paths))
        valid, message = self._validate_paths(paths)
        self._set_validation_state("valid" if valid else "invalid", message)
        self.pathsChanged.emit(self.paths())
        self.pathChanged.emit(self.path())
        self.validationChanged.emit(valid, message)
        if valid != self._last_validity:
            self.validityChanged.emit(valid)
            self._last_validity = valid

    def _on_text_edited(self, text: str) -> None:
        parts = [part.strip().strip('"') for part in text.split(";")]
        paths = [Path(part).expanduser() for part in parts if part]
        if not self.allows_multiple and len(paths) > 1:
            paths = paths[:1]
        self._apply_paths(paths, update_text=False)

    def is_valid(self) -> bool:
        """Return whether the current selection satisfies this picker."""
        valid, _ = self._validate_paths(self._paths)
        return valid

    def validation_message(self) -> str:
        """Return the current validation failure, or an empty string."""
        _, message = self._validate_paths(self._paths)
        return message

    def _validate_paths(self, paths: list[Path]) -> tuple[bool, str]:
        if not paths:
            if self.required:
                return False, "A path is required."
            return True, ""
        if not self.allows_multiple and len(paths) != 1:
            return False, "Choose exactly one path."

        for path in paths:
            if (
                self.allowed_suffixes
                and path.suffix.lower() not in self.allowed_suffixes
            ):
                allowed = ", ".join(sorted(self.allowed_suffixes))
                return False, f"'{path.name}' must use one of: {allowed}."

            if self.mode in {PickerMode.OPEN_FILE, PickerMode.OPEN_FILES}:
                if not path.is_file():
                    return False, f"File not found: '{path}'."
            elif self.mode is PickerMode.EXISTING_DIRECTORY:
                if not path.is_dir():
                    return False, f"Folder not found: '{path}'."
            elif self.mode is PickerMode.SAVE_FILE:
                if path.exists() and not path.is_file():
                    return False, f"Output path is not a file: '{path}'."
                if not path.parent.is_dir():
                    return False, f"Output folder does not exist: '{path.parent}'."
            elif self.mode is PickerMode.OUTPUT_DIRECTORY:
                if path.exists() and not path.is_dir():
                    return False, f"Output path is not a folder: '{path}'."
                if not path.exists() and not path.parent.is_dir():
                    return False, f"Parent folder does not exist: '{path.parent}'."

        return True, ""

    def _set_validation_state(self, state: str, message: str) -> None:
        self.setProperty("validationState", state)
        self.line_edit.setProperty("validationState", state)
        self.error_label.setText(message)
        self.error_label.setVisible(state == "invalid" and bool(message))
        for widget in (self, self.line_edit):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def browse(self) -> None:
        """Open the appropriate native file or directory dialog."""
        initial = str(self.path() or Path.cwd())
        selected_paths: list[Path] = []

        if self.mode is PickerMode.OPEN_FILE:
            selected, _ = QFileDialog.getOpenFileName(
                self,
                self.dialog_title,
                initial,
                self.file_filter,
            )
            if selected:
                selected_paths = [Path(selected)]
        elif self.mode is PickerMode.OPEN_FILES:
            selected, _ = QFileDialog.getOpenFileNames(
                self,
                self.dialog_title,
                initial,
                self.file_filter,
            )
            selected_paths = [Path(path) for path in selected]
        elif self.mode in {
            PickerMode.EXISTING_DIRECTORY,
            PickerMode.OUTPUT_DIRECTORY,
        }:
            selected = QFileDialog.getExistingDirectory(
                self,
                self.dialog_title,
                initial,
            )
            if selected:
                selected_paths = [Path(selected)]
        elif self.mode is PickerMode.SAVE_FILE:
            selected, _ = QFileDialog.getSaveFileName(
                self,
                self.dialog_title,
                initial,
                self.file_filter,
            )
            if selected:
                selected_paths = [Path(selected)]

        if selected_paths:
            self.set_paths(selected_paths)

    def accepts_dropped_paths(self, paths: Iterable[Path | str]) -> bool:
        """Return whether dropped paths are valid for this picker."""
        normalized = [Path(path) for path in paths]
        if not self.allows_multiple:
            normalized = normalized[:1]
        valid, _ = self._validate_paths(normalized)
        return valid

    def accept_dropped_paths(self, paths: Iterable[Path | str]) -> bool:
        """Apply dropped paths when valid and expose rejection styling."""
        normalized = [Path(path) for path in paths]
        if not self.allows_multiple:
            normalized = normalized[:1]
        valid, message = self._validate_paths(normalized)
        if not valid:
            self._set_validation_state("invalid", message)
            self.validationChanged.emit(False, message)
            return False
        self._apply_paths(normalized)
        return True

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        paths = paths_from_mime_data(event.mimeData())
        if paths and self.accepts_dropped_paths(paths):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if self.accept_dropped_paths(paths_from_mime_data(event.mimeData())):
            event.acceptProposedAction()
        else:
            event.ignore()

"""Keyboard-accessible local-file drag-and-drop target."""

from pathlib import Path
from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from safepdf.ui.widgets.path_picker import paths_from_mime_data


class DropZone(QWidget):
    """Accept compatible local files or folders and emit their paths."""

    activated = Signal()
    pathsDropped = Signal(list)
    dropRejected = Signal(str)

    def __init__(
        self,
        *,
        prompt: str = "Drop files here",
        allowed_suffixes: Iterable[str] = (),
        allow_files: bool = True,
        allow_directories: bool = False,
        allow_multiple: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.allowed_suffixes = frozenset(
            suffix.lower() if suffix.startswith(".") else f".{suffix.lower()}"
            for suffix in allowed_suffixes
        )
        self.allow_files = allow_files
        self.allow_directories = allow_directories
        self.allow_multiple = allow_multiple

        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(prompt)
        self.setAccessibleDescription(
            "Drop compatible local paths, or press Enter to browse."
        )
        self.setProperty("validationState", "neutral")

        layout = QVBoxLayout(self)
        label = QLabel(prompt, self)
        label.setObjectName("dropZonePrompt")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)

    def validate_paths(
        self,
        paths: Iterable[Path | str],
    ) -> tuple[bool, str]:
        """Validate a prospective drop without mutating the widget."""
        normalized = [Path(path) for path in paths]
        if not normalized:
            return False, "Drop one or more local paths."
        if not self.allow_multiple and len(normalized) > 1:
            return False, "Only one path can be dropped here."

        for path in normalized:
            if path.is_file():
                if not self.allow_files:
                    return False, "Files are not accepted here."
                if (
                    self.allowed_suffixes
                    and path.suffix.lower() not in self.allowed_suffixes
                ):
                    allowed = ", ".join(sorted(self.allowed_suffixes))
                    return False, f"'{path.name}' must use one of: {allowed}."
            elif path.is_dir():
                if not self.allow_directories:
                    return False, "Folders are not accepted here."
            else:
                return False, f"Path not found: '{path}'."
        return True, ""

    def accept_paths(self, paths: Iterable[Path | str]) -> bool:
        """Validate paths and emit either acceptance or rejection."""
        normalized = [Path(path) for path in paths]
        valid, message = self.validate_paths(normalized)
        self._set_validation_state("valid" if valid else "invalid")
        if valid:
            self.pathsDropped.emit(normalized)
        else:
            self.dropRejected.emit(message)
        return valid

    def _set_validation_state(self, state: str) -> None:
        self.setProperty("validationState", state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        valid, _ = self.validate_paths(paths_from_mime_data(event.mimeData()))
        if valid:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if self.accept_paths(paths_from_mime_data(event.mimeData())):
            event.acceptProposedAction()
        else:
            event.ignore()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in {
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Space,
        }:
            self.activated.emit()
            event.accept()
            return
        super().keyPressEvent(event)

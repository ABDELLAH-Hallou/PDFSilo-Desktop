"""Reusable actions for opening generated output paths."""

from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class OutputActions(QWidget):
    """Open the latest output or its containing directory on user request."""

    openOutputRequested = Signal(object)
    openFolderRequested = Signal(object)
    openFailed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("outputActions")
        self._output_path: Path | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.open_output_button = QPushButton("&Open output", self)
        self.open_output_button.setObjectName("openOutputButton")
        self.open_output_button.setAccessibleName("Open generated output")
        self.open_output_button.clicked.connect(self.open_output)

        self.open_folder_button = QPushButton(
            "Open containing &folder",
            self,
        )
        self.open_folder_button.setObjectName("openFolderButton")
        self.open_folder_button.setAccessibleName(
            "Open folder containing generated output"
        )
        self.open_folder_button.clicked.connect(self.open_containing_folder)

        layout.addWidget(self.open_output_button)
        layout.addWidget(self.open_folder_button)
        layout.addStretch(1)
        self.set_output_path(None)

    def output_path(self) -> Path | None:
        return self._output_path

    def set_output_path(self, output_path: Path | str | None) -> None:
        """Set the output used by both actions."""
        self._output_path = (
            Path(output_path) if output_path is not None else None
        )
        enabled = self._output_path is not None
        self.open_output_button.setEnabled(enabled)
        self.open_folder_button.setEnabled(enabled)

    def open_output(self) -> bool:
        """Ask the desktop to open the current output."""
        path = self._output_path
        if path is None or not path.exists():
            self.openFailed.emit("The output path is no longer available.")
            return False
        self.openOutputRequested.emit(path)
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        if not opened:
            self.openFailed.emit(f"Could not open '{path}'.")
        return opened

    def open_containing_folder(self) -> bool:
        """Ask the desktop to open the output directory."""
        path = self._output_path
        if path is None:
            self.openFailed.emit("No output path is available.")
            return False
        folder = path if path.is_dir() else path.parent
        if not folder.is_dir():
            self.openFailed.emit("The output folder is no longer available.")
            return False
        self.openFolderRequested.emit(folder)
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        if not opened:
            self.openFailed.emit(f"Could not open '{folder}'.")
        return opened


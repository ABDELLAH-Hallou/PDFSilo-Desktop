"""User-initiated, checksum-verified update download dialog."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdfsilo.ui.theme import SPACE_LG, SPACE_MD, SPACE_SM
from pdfsilo.ui.widgets.operation_panel import ProgressDisplay
from pdfsilo.ui.workers import UpdateRunner
from pdfsilo.updater import UpdateInfo, download_verified_update


class UpdateDialog(QDialog):
    """Download and verify a release without executing it."""

    def __init__(
        self,
        info: UpdateInfo,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.info = info
        self.downloaded_path: Path | None = None
        self.runner = UpdateRunner(parent=self)

        self.setObjectName("updateDialog")
        self.setWindowTitle("PDFSilo Update")
        self.setModal(False)
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_LG, SPACE_LG, SPACE_LG, SPACE_LG)
        layout.setSpacing(SPACE_MD)

        title = QLabel(f"PDFSilo {info.version} is available", self)
        title.setObjectName("updateDialogTitle")
        explanation = QLabel(
            "PDFSilo can download this release to your private user cache and "
            "verify its published SHA-256 checksum. Installation remains a "
            "separate, user-initiated step until signed native installers are "
            "available.",
            self,
        )
        explanation.setObjectName("updateDialogDescription")
        explanation.setWordWrap(True)

        self.status_label = QLabel("Ready to download.", self)
        self.status_label.setObjectName("updateDialogStatus")
        self.status_label.setWordWrap(True)
        self.progress = ProgressDisplay(self)

        action_row = QHBoxLayout()
        action_row.setSpacing(SPACE_SM)
        self.release_notes_button = QPushButton("Release notes", self)
        self.release_notes_button.clicked.connect(self.open_release_notes)
        self.open_folder_button = QPushButton("Open containing folder", self)
        self.open_folder_button.setObjectName("openUpdateFolderButton")
        self.open_folder_button.setEnabled(False)
        self.open_folder_button.clicked.connect(self.open_containing_folder)
        self.download_button = QPushButton("Download and verify", self)
        self.download_button.setObjectName("downloadUpdateButton")
        self.download_button.setProperty("primary", True)
        self.download_button.clicked.connect(self.start_download)
        self.cancel_button = QPushButton("Cancel download", self)
        self.cancel_button.setObjectName("cancelUpdateDownloadButton")
        self.cancel_button.clicked.connect(self.runner.cancel)
        self.cancel_button.hide()

        action_row.addWidget(self.release_notes_button)
        action_row.addWidget(self.open_folder_button)
        action_row.addStretch(1)
        action_row.addWidget(self.cancel_button)
        action_row.addWidget(self.download_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            parent=self,
        )
        buttons.rejected.connect(self.close)
        self.close_button = buttons.button(
            QDialogButtonBox.StandardButton.Close
        )

        layout.addWidget(title)
        layout.addWidget(explanation)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        layout.addLayout(action_row)
        layout.addWidget(buttons)

        self.runner.progress.connect(self.progress.set_progress)
        self.runner.succeeded.connect(self._download_succeeded)
        self.runner.failed.connect(self._download_failed)
        self.runner.runningChanged.connect(self._set_running)

    def start_download(self) -> bool:
        self.status_label.setText("Preparing the verified download…")
        return self.runner.start(download_verified_update, self.info)

    def open_release_notes(self) -> bool:
        return QDesktopServices.openUrl(QUrl(self.info.release_notes_url))

    def open_containing_folder(self) -> bool:
        if self.downloaded_path is None:
            return False
        return QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(self.downloaded_path.parent))
        )

    def _set_running(self, running: bool) -> None:
        self.download_button.setEnabled(not running)
        self.release_notes_button.setEnabled(not running)
        self.cancel_button.setVisible(running)
        self.close_button.setEnabled(not running)
        if running:
            self.progress.set_indeterminate("Connecting securely to GitHub…")

    def _download_succeeded(self, path: object) -> None:
        self.progress.reset()
        self.downloaded_path = Path(path)
        self.status_label.setText(
            "Downloaded and SHA-256 verified. Open the containing folder to "
            "start the signed installer manually when one is available."
        )
        self.open_folder_button.setEnabled(True)
        self.download_button.setText("Download again")

    def _download_failed(self, message: str) -> None:
        self.progress.reset()
        self.status_label.setText(message)


__all__ = ["UpdateDialog"]

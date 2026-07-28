"""Non-blocking update notification shown above document work."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
)

from pdfsilo import __version__
from pdfsilo.ui.theme import SPACE_LG, SPACE_MD, SPACE_SM
from pdfsilo.updater import UpdateInfo


class UpdateBanner(QFrame):
    """Announce one newer release without interrupting active work."""

    updateRequested = Signal(object)
    releaseNotesRequested = Signal(object)
    skipRequested = Signal(str)
    dismissed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("updateBanner")
        self._info: UpdateInfo | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACE_LG, SPACE_SM, SPACE_LG, SPACE_SM)
        layout.setSpacing(SPACE_MD)

        self.message_label = QLabel(self)
        self.message_label.setObjectName("updateBannerMessage")
        self.message_label.setWordWrap(True)

        self.release_notes_button = QPushButton("Release notes", self)
        self.release_notes_button.setObjectName("updateReleaseNotesButton")
        self.release_notes_button.clicked.connect(self._request_release_notes)

        self.skip_button = QPushButton("Skip this version", self)
        self.skip_button.setObjectName("skipUpdateButton")
        self.skip_button.clicked.connect(self._skip)

        self.update_button = QPushButton("Update", self)
        self.update_button.setObjectName("startUpdateButton")
        self.update_button.setProperty("primary", True)
        self.update_button.clicked.connect(self._request_update)

        self.dismiss_button = QToolButton(self)
        self.dismiss_button.setObjectName("dismissUpdateButton")
        self.dismiss_button.setText("×")
        self.dismiss_button.setToolTip("Dismiss this notification")
        self.dismiss_button.setAccessibleName("Dismiss update notification")
        self.dismiss_button.clicked.connect(self._dismiss)

        layout.addWidget(self.message_label, 1)
        layout.addWidget(self.release_notes_button)
        layout.addWidget(self.skip_button)
        layout.addWidget(self.update_button)
        layout.addWidget(self.dismiss_button)
        self.hide()

    def show_update(self, info: UpdateInfo) -> None:
        self._info = info
        self.message_label.setText(
            f"PDFSilo {info.version} is available (you have {__version__})."
        )
        self.show()

    def clear(self) -> None:
        self._info = None
        self.hide()

    def update_info(self) -> UpdateInfo | None:
        return self._info

    def _request_update(self) -> None:
        if self._info is not None:
            self.updateRequested.emit(self._info)

    def _request_release_notes(self) -> None:
        if self._info is not None:
            self.releaseNotesRequested.emit(self._info)

    def _skip(self) -> None:
        if self._info is None:
            return
        version = self._info.version
        self.clear()
        self.skipRequested.emit(version)

    def _dismiss(self) -> None:
        self.clear()
        self.dismissed.emit()


__all__ = ["UpdateBanner"]

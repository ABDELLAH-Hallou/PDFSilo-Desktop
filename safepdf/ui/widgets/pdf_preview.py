"""Reusable asynchronous single-page PDF preview widget."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from safepdf.ui.thumbnails import (
    DEFAULT_THUMBNAIL_SCALE,
    ThumbnailData,
    ThumbnailService,
    shared_thumbnail_service,
)


class PdfPreview(QWidget):
    """Show a low-resolution page preview without blocking the UI thread."""

    previewReady = Signal(object, int)
    previewFailed = Signal(str)
    pageChanged = Signal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        service: ThumbnailService | None = None,
        scale: float = DEFAULT_THUMBNAIL_SCALE,
    ) -> None:
        super().__init__(parent)
        self.service = service or shared_thumbnail_service()
        self.scale = scale
        self._source_path: Path | None = None
        self._page_index = 0
        self._page_count = 0
        self._request_id: int | None = None
        self._image: QImage | None = None

        self.setObjectName("pdfPreview")
        self.setAccessibleName("PDF preview")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.image_label = QLabel(self)
        self.image_label.setObjectName("pdfPreviewImage")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(160, 180)
        self.image_label.setMaximumHeight(300)

        self.status_label = QLabel(self)
        self.status_label.setObjectName("pdfPreviewStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)

        navigation = QWidget(self)
        navigation.setObjectName("pdfPreviewNavigation")
        navigation_layout = QHBoxLayout(navigation)
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.setSpacing(8)

        self.previous_button = QPushButton("&Previous", navigation)
        self.previous_button.setObjectName("previewPreviousButton")
        self.previous_button.clicked.connect(self.show_previous_page)
        self.page_label = QLabel("Page —", navigation)
        self.page_label.setObjectName("previewPageLabel")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_button = QPushButton("&Next", navigation)
        self.next_button.setObjectName("previewNextButton")
        self.next_button.clicked.connect(self.show_next_page)

        navigation_layout.addStretch(1)
        navigation_layout.addWidget(self.previous_button)
        navigation_layout.addWidget(self.page_label)
        navigation_layout.addWidget(self.next_button)
        navigation_layout.addStretch(1)

        layout.addWidget(self.image_label)
        layout.addWidget(self.status_label)
        layout.addWidget(navigation)

        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._source_changed)
        self.service.thumbnailReady.connect(self._thumbnail_ready)
        self.service.thumbnailFailed.connect(self._thumbnail_failed)
        self._show_placeholder("Select a PDF to display a preview.")

    def source_path(self) -> Path | None:
        return self._source_path

    def page_index(self) -> int:
        return self._page_index

    def page_count(self) -> int:
        return self._page_count

    @Slot(object)
    def set_pdf(self, path: Path | str | None, page_index: int = 0) -> None:
        """Select a source and request its page preview asynchronously."""
        self._cancel_request()
        self._set_watched_path(None)
        self._source_path = Path(path).expanduser() if path else None
        self._page_index = max(0, page_index)
        self._page_count = 0
        self._image = None

        if self._source_path is None:
            self._show_placeholder("Select a PDF to display a preview.")
            return
        self._set_watched_path(self._source_path)
        self._request_current_page()

    @Slot()
    def show_previous_page(self) -> None:
        if self._page_index > 0:
            self._page_index -= 1
            self._request_current_page()
            self.pageChanged.emit(self._page_index)

    @Slot()
    def show_next_page(self) -> None:
        if self._page_count and self._page_index + 1 < self._page_count:
            self._page_index += 1
            self._request_current_page()
            self.pageChanged.emit(self._page_index)

    def _request_current_page(self) -> None:
        self._cancel_request()
        self._image = None
        self.image_label.clear()
        self.status_label.setText("Loading preview…")
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.page_label.setText(f"Page {self._page_index + 1}")
        assert self._source_path is not None
        self._request_id = self.service.request(
            self._source_path,
            self._page_index,
            self.scale,
        )

    @Slot(int, object)
    def _thumbnail_ready(
        self,
        request_id: int,
        data: ThumbnailData,
    ) -> None:
        if request_id != self._request_id or self._source_path is None:
            return
        self._request_id = None
        self._page_count = data.page_count
        self._image = data.image.copy()
        self.status_label.clear()
        self.page_label.setText(
            f"Page {self._page_index + 1} of {self._page_count}"
        )
        self.previous_button.setEnabled(self._page_index > 0)
        self.next_button.setEnabled(
            self._page_index + 1 < self._page_count
        )
        self._update_pixmap()
        self.previewReady.emit(self._source_path, self._page_index)

    @Slot(int, str)
    def _thumbnail_failed(self, request_id: int, message: str) -> None:
        if request_id != self._request_id:
            return
        self._request_id = None
        self._image = None
        self._show_placeholder(message)
        self.previewFailed.emit(message)

    @Slot(str)
    def _source_changed(self, _path: str) -> None:
        if self._source_path is None:
            return
        self.service.invalidate(self._source_path)
        source = self._source_path
        page_index = self._page_index
        self.set_pdf(source, page_index)

    def _cancel_request(self) -> None:
        if self._request_id is not None:
            self.service.cancel(self._request_id)
            self._request_id = None

    def _set_watched_path(self, path: Path | None) -> None:
        watched = self._watcher.files()
        if watched:
            self._watcher.removePaths(watched)
        if path is not None and path.is_file():
            self._watcher.addPath(str(path.resolve()))

    def _show_placeholder(self, message: str) -> None:
        self.image_label.clear()
        self.image_label.setText("No preview")
        self.status_label.setText(message)
        self.page_label.setText("Page —")
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)

    def _update_pixmap(self) -> None:
        if self._image is None or self._image.isNull():
            return
        target = self.image_label.size()
        pixmap = QPixmap.fromImage(self._image)
        self.image_label.setPixmap(
            pixmap.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_pixmap()


__all__ = ["PdfPreview"]

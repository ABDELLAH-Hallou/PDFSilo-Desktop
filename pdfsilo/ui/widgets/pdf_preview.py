"""Reusable asynchronous, zoomable PDF preview widget."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, Qt, Signal, Slot
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pdfsilo.ui.thumbnails import (
    ThumbnailData,
    ThumbnailService,
    shared_thumbnail_service,
)
from pdfsilo.utils import PAGE_SIZES

PREVIEW_RENDER_SCALE = 1.25
ZOOM_LEVELS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0)


class PdfPreview(QWidget):
    """Show ordered PDF sources and crisp page previews off the UI thread."""

    previewReady = Signal(object, int)
    previewFailed = Signal(str)
    pageChanged = Signal(int)
    documentChanged = Signal(int)
    zoomChanged = Signal(float)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        service: ThumbnailService | None = None,
        scale: float = PREVIEW_RENDER_SCALE,
    ) -> None:
        super().__init__(parent)
        self.service = service or shared_thumbnail_service()
        self.scale = max(0.1, scale)
        self._source_paths: list[Path] = []
        self._source_path: Path | None = None
        self._document_index = 0
        self._page_index = 0
        self._page_count = 0
        self._request_id: int | None = None
        self._image: QImage | None = None
        self._fit_to_window = True
        self._zoom_factor = 1.0
        self._target_page_size: str | None = None

        self.setObjectName("pdfPreview")
        self.setAccessibleName("PDF preview")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.document_row = QWidget(self)
        self.document_row.setObjectName("previewDocumentRow")
        document_layout = QHBoxLayout(self.document_row)
        document_layout.setContentsMargins(0, 0, 0, 0)
        document_layout.setSpacing(8)
        document_label = QLabel("&Document", self.document_row)
        document_label.setObjectName("previewControlLabel")
        self.document_combo = QComboBox(self.document_row)
        self.document_combo.setObjectName("previewDocumentCombo")
        self.document_combo.setAccessibleName("PDF to preview")
        document_label.setBuddy(self.document_combo)
        document_layout.addWidget(document_label)
        document_layout.addWidget(self.document_combo, 1)
        self.document_row.hide()

        self.preview_scroll = QScrollArea(self)
        self.preview_scroll.setObjectName("pdfPreviewScrollArea")
        self.preview_scroll.setWidgetResizable(False)
        self.preview_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_scroll.setMinimumHeight(280)

        self.image_label = QLabel()
        self.image_label.setObjectName("pdfPreviewImage")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(200, 250)
        self.preview_scroll.setWidget(self.image_label)

        self.status_label = QLabel(self)
        self.status_label.setObjectName("pdfPreviewStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)

        self.target_label = QLabel(self)
        self.target_label.setObjectName("previewTargetLabel")
        self.target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.target_label.hide()

        navigation = QWidget(self)
        navigation.setObjectName("pdfPreviewNavigation")
        navigation_layout = QHBoxLayout(navigation)
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.setSpacing(6)

        self.previous_button = QPushButton("&Previous", navigation)
        self.previous_button.setObjectName("previewPreviousButton")
        self.previous_button.clicked.connect(self.show_previous_page)
        self.page_label = QLabel("Page —", navigation)
        self.page_label.setObjectName("previewPageLabel")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_button = QPushButton("&Next", navigation)
        self.next_button.setObjectName("previewNextButton")
        self.next_button.clicked.connect(self.show_next_page)

        zoom_controls = QWidget(self)
        zoom_controls.setObjectName("pdfPreviewZoomControls")
        zoom_layout = QHBoxLayout(zoom_controls)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(6)

        self.zoom_out_button = QPushButton("−", zoom_controls)
        self.zoom_out_button.setObjectName("previewZoomOutButton")
        self.zoom_out_button.setAccessibleName("Zoom out")
        self.zoom_out_button.setToolTip("Zoom out")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_label = QLabel("Fit", zoom_controls)
        self.zoom_label.setObjectName("previewZoomLabel")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_in_button = QPushButton("+", zoom_controls)
        self.zoom_in_button.setObjectName("previewZoomInButton")
        self.zoom_in_button.setAccessibleName("Zoom in")
        self.zoom_in_button.setToolTip("Zoom in")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.fit_button = QPushButton("&Fit", zoom_controls)
        self.fit_button.setObjectName("previewFitButton")
        self.fit_button.clicked.connect(self.fit_to_window)

        navigation_layout.addStretch(1)
        navigation_layout.addWidget(self.previous_button)
        navigation_layout.addWidget(self.page_label)
        navigation_layout.addWidget(self.next_button)
        navigation_layout.addStretch(1)
        zoom_layout.addStretch(1)
        zoom_layout.addWidget(self.zoom_out_button)
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(self.zoom_in_button)
        zoom_layout.addWidget(self.fit_button)
        zoom_layout.addStretch(1)

        layout.addWidget(self.document_row)
        layout.addWidget(self.preview_scroll, 1)
        layout.addWidget(self.status_label)
        layout.addWidget(self.target_label)
        layout.addWidget(navigation)
        layout.addWidget(zoom_controls)

        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._source_changed)
        self.document_combo.currentIndexChanged.connect(
            self._select_document
        )
        self.service.thumbnailReady.connect(self._thumbnail_ready)
        self.service.thumbnailFailed.connect(self._thumbnail_failed)
        self._show_placeholder("Select a PDF to display a preview.")

    def source_path(self) -> Path | None:
        return self._source_path

    def source_paths(self) -> list[Path]:
        return list(self._source_paths)

    def document_index(self) -> int:
        return self._document_index

    def page_index(self) -> int:
        return self._page_index

    def page_count(self) -> int:
        return self._page_count

    def zoom_factor(self) -> float:
        return self._zoom_factor

    def is_fit_to_window(self) -> bool:
        return self._fit_to_window

    @Slot(object)
    def set_pdfs(self, paths: object) -> None:
        """Set all previewable PDFs in their processing order."""
        values = list(paths) if paths else []
        normalized = [Path(path).expanduser() for path in values]
        self._source_paths = normalized
        self.document_combo.blockSignals(True)
        self.document_combo.clear()
        for position, path in enumerate(normalized, start=1):
            self.document_combo.addItem(
                f"{position}. {path.name}",
                path,
            )
            self.document_combo.setItemData(
                position - 1,
                str(path),
                Qt.ItemDataRole.ToolTipRole,
            )
        self.document_combo.blockSignals(False)
        self.document_row.setVisible(len(normalized) > 1)
        self._document_index = 0
        self._set_current_source(normalized[0] if normalized else None, 0)

    @Slot(object)
    def set_pdf(self, path: Path | str | None, page_index: int = 0) -> None:
        """Select a single source and request its page asynchronously."""
        self._source_paths = [Path(path).expanduser()] if path else []
        self.document_combo.blockSignals(True)
        self.document_combo.clear()
        if self._source_paths:
            self.document_combo.addItem(
                self._source_paths[0].name,
                self._source_paths[0],
            )
        self.document_combo.blockSignals(False)
        self.document_row.hide()
        self._document_index = 0
        self._set_current_source(
            self._source_paths[0] if self._source_paths else None,
            page_index,
        )

    @Slot(str)
    def set_target_page_size(self, page_size: str | None) -> None:
        """Preview source content on the selected normalized output canvas."""
        normalized = page_size if page_size in PAGE_SIZES else None
        if normalized == self._target_page_size:
            return
        self._target_page_size = normalized
        self.target_label.setVisible(normalized is not None)
        if normalized:
            self.target_label.setText(f"Output canvas · {normalized}")
        self._update_pixmap()

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

    @Slot()
    def zoom_in(self) -> None:
        current = self._zoom_factor if not self._fit_to_window else 1.0
        next_level = next(
            (level for level in ZOOM_LEVELS if level > current),
            ZOOM_LEVELS[-1],
        )
        self._set_zoom(next_level)

    @Slot()
    def zoom_out(self) -> None:
        current = self._zoom_factor if not self._fit_to_window else 1.0
        previous = [
            level for level in ZOOM_LEVELS if level < current
        ]
        self._set_zoom(previous[-1] if previous else ZOOM_LEVELS[0])

    @Slot()
    def fit_to_window(self) -> None:
        self._fit_to_window = True
        self.zoom_label.setText("Fit")
        self.fit_button.setEnabled(False)
        self._update_zoom_buttons()
        self._update_pixmap()

    def _set_zoom(self, factor: float) -> None:
        factor = min(max(factor, ZOOM_LEVELS[0]), ZOOM_LEVELS[-1])
        render_changed = abs(factor - self._render_scale()) > 0.001
        self._fit_to_window = False
        self._zoom_factor = factor
        self.zoom_label.setText(f"{factor:.0%}")
        self.fit_button.setEnabled(True)
        self._update_zoom_buttons()
        self.zoomChanged.emit(factor)
        if render_changed and self._source_path is not None:
            self._request_current_page()
        else:
            self._update_pixmap()

    def _update_zoom_buttons(self) -> None:
        effective = self._zoom_factor if not self._fit_to_window else 1.0
        self.zoom_out_button.setEnabled(effective > ZOOM_LEVELS[0])
        self.zoom_in_button.setEnabled(effective < ZOOM_LEVELS[-1])

    def _render_scale(self) -> float:
        return self.scale if self._fit_to_window else self._zoom_factor

    @Slot(int)
    def _select_document(self, index: int) -> None:
        if index < 0 or index >= len(self._source_paths):
            return
        self._document_index = index
        self._set_current_source(self._source_paths[index], 0)
        self.documentChanged.emit(index)

    def _set_current_source(
        self,
        path: Path | None,
        page_index: int,
    ) -> None:
        self._cancel_request()
        self._set_watched_path(None)
        self._source_path = path
        self._page_index = max(0, page_index)
        self._page_count = 0
        self._image = None
        if path is None:
            self._show_placeholder("Select a PDF to display a preview.")
            return
        self._set_watched_path(path)
        self._request_current_page()

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
            self._render_scale(),
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
        self._set_current_source(self._source_path, self._page_index)

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
        self.image_label.resize(240, 280)
        self.status_label.setText(message)
        self.page_label.setText("Page —")
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self._update_zoom_buttons()

    def _canvas_pixmap(self) -> QPixmap:
        assert self._image is not None
        source = QPixmap.fromImage(self._image)
        if self._target_page_size is None:
            return source

        target_width, target_height = PAGE_SIZES[self._target_page_size]
        if source.width() > source.height():
            target_width, target_height = (
                max(target_width, target_height),
                min(target_width, target_height),
            )
        else:
            target_width, target_height = (
                min(target_width, target_height),
                max(target_width, target_height),
            )
        scale = self._render_scale()
        canvas_size = (
            max(1, round(target_width * scale)),
            max(1, round(target_height * scale)),
        )
        canvas = QPixmap(*canvas_size)
        canvas.fill(QColor("#FFFFFF"))
        content = source.scaled(
            canvas.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter = QPainter(canvas)
        painter.drawPixmap(
            (canvas.width() - content.width()) // 2,
            (canvas.height() - content.height()) // 2,
            content,
        )
        painter.end()
        return canvas

    def _update_pixmap(self) -> None:
        if self._image is None or self._image.isNull():
            return
        pixmap = self._canvas_pixmap()
        if self._fit_to_window:
            viewport = self.preview_scroll.viewport().size()
            target = viewport
            target.setWidth(max(1, viewport.width() - 12))
            target.setHeight(max(1, viewport.height() - 12))
            pixmap = pixmap.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.image_label.setText("")
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(pixmap.size())

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._fit_to_window:
            self._update_pixmap()


__all__ = ["PREVIEW_RENDER_SCALE", "PdfPreview"]

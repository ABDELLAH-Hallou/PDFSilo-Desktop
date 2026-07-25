"""Background PDF thumbnail rendering and file-signature-aware caching."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from threading import Event

import fitz
from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot
from PySide6.QtGui import QImage

DEFAULT_THUMBNAIL_SCALE = 0.22
MAX_RENDER_JOBS = 2
MAX_CACHE_ENTRIES = 128


@dataclass(frozen=True, slots=True)
class ThumbnailKey:
    """Identify a rendered page and the exact source-file version."""

    path: str
    modification_time_ns: int
    file_size: int
    page_index: int
    scale: float


@dataclass(slots=True)
class ThumbnailData:
    """A detached image plus document metadata returned by a render."""

    image: QImage
    page_count: int


class ThumbnailCache:
    """Small LRU cache that removes stale versions of a changed PDF."""

    def __init__(self, max_entries: int = MAX_CACHE_ENTRIES) -> None:
        if max_entries < 1:
            raise ValueError("Thumbnail cache size must be positive.")
        self.max_entries = max_entries
        self._items: OrderedDict[ThumbnailKey, ThumbnailData] = OrderedDict()

    def key_for(
        self,
        path: Path,
        page_index: int,
        scale: float,
    ) -> ThumbnailKey:
        """Create a key and invalidate entries for older file signatures."""
        resolved = path.expanduser().resolve()
        stat = resolved.stat()
        normalized_path = str(resolved)
        signature = (stat.st_mtime_ns, stat.st_size)
        stale_keys = [
            key
            for key in self._items
            if key.path == normalized_path
            and (key.modification_time_ns, key.file_size) != signature
        ]
        for key in stale_keys:
            self._items.pop(key, None)
        return ThumbnailKey(
            normalized_path,
            stat.st_mtime_ns,
            stat.st_size,
            page_index,
            round(float(scale), 4),
        )

    def get(self, key: ThumbnailKey) -> ThumbnailData | None:
        """Return a detached cached value and mark it recently used."""
        value = self._items.get(key)
        if value is None:
            return None
        self._items.move_to_end(key)
        return ThumbnailData(value.image.copy(), value.page_count)

    def put(self, key: ThumbnailKey, value: ThumbnailData) -> None:
        """Store a detached value and enforce the LRU size bound."""
        self._items[key] = ThumbnailData(
            value.image.copy(),
            value.page_count,
        )
        self._items.move_to_end(key)
        while len(self._items) > self.max_entries:
            self._items.popitem(last=False)

    def invalidate(self, path: Path | None = None) -> None:
        """Clear all entries, or only entries belonging to one path."""
        if path is None:
            self._items.clear()
            return
        normalized_path = str(path.expanduser().resolve())
        for key in [
            key
            for key in self._items
            if key.path == normalized_path
        ]:
            self._items.pop(key, None)

    def __len__(self) -> int:
        return len(self._items)


class _RenderSignals(QObject):
    rendered = Signal(int, object, object)
    failed = Signal(int, str)
    finished = Signal(int)


class _RenderTask(QRunnable):
    """Render one PDF page without creating any GUI-thread-only objects."""

    def __init__(
        self,
        request_id: int,
        key: ThumbnailKey,
        cancelled: Event,
    ) -> None:
        super().__init__()
        self.request_id = request_id
        self.key = key
        self.cancelled = cancelled
        self.signals = _RenderSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            if self.cancelled.is_set():
                return
            with fitz.open(self.key.path) as document:
                if document.needs_pass:
                    raise PermissionError(
                        "Preview unavailable: this PDF is encrypted."
                    )
                page_count = document.page_count
                if not 0 <= self.key.page_index < page_count:
                    raise IndexError(
                        f"Page {self.key.page_index + 1} does not exist."
                    )
                page = document.load_page(self.key.page_index)
                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(self.key.scale, self.key.scale),
                    colorspace=fitz.csRGB,
                    alpha=False,
                )
                try:
                    # copy() detaches the QImage before the PyMuPDF pixmap is
                    # released at the end of this worker scope.
                    image = QImage(
                        pixmap.samples,
                        pixmap.width,
                        pixmap.height,
                        pixmap.stride,
                        QImage.Format.Format_RGB888,
                    ).copy()
                finally:
                    del pixmap

            if not self.cancelled.is_set():
                self.signals.rendered.emit(
                    self.request_id,
                    self.key,
                    ThumbnailData(image, page_count),
                )
        except PermissionError as exc:
            self.signals.failed.emit(self.request_id, str(exc))
        except Exception:
            self.signals.failed.emit(
                self.request_id,
                "Preview unavailable: the PDF is invalid or unreadable.",
            )
        finally:
            self.signals.finished.emit(self.request_id)


class ThumbnailService(QObject):
    """Limit render concurrency and share thumbnails between UI consumers."""

    thumbnailReady = Signal(int, object)
    thumbnailFailed = Signal(int, str)

    def __init__(
        self,
        *,
        max_jobs: int = MAX_RENDER_JOBS,
        cache: ThumbnailCache | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        if max_jobs < 1:
            raise ValueError("At least one render job is required.")
        self.cache = cache if cache is not None else ThumbnailCache()
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(max_jobs)
        self._next_request_id = 1
        self._tasks: dict[int, _RenderTask] = {}
        self._cancellations: dict[int, Event] = {}

    @property
    def max_jobs(self) -> int:
        return self.thread_pool.maxThreadCount()

    def request(
        self,
        path: Path,
        page_index: int = 0,
        scale: float = DEFAULT_THUMBNAIL_SCALE,
    ) -> int:
        """Return a request id and asynchronously emit its result."""
        request_id = self._next_request_id
        self._next_request_id += 1
        if page_index < 0 or scale <= 0:
            QTimer.singleShot(
                0,
                lambda: self.thumbnailFailed.emit(
                    request_id,
                    "Preview unavailable: invalid page or scale.",
                ),
            )
            return request_id

        try:
            key = self.cache.key_for(path, page_index, scale)
        except OSError:
            QTimer.singleShot(
                0,
                lambda: self.thumbnailFailed.emit(
                    request_id,
                    "Preview unavailable: the PDF file was not found.",
                ),
            )
            return request_id

        cached = self.cache.get(key)
        if cached is not None:
            QTimer.singleShot(
                0,
                lambda: self.thumbnailReady.emit(request_id, cached),
            )
            return request_id

        cancelled = Event()
        task = _RenderTask(request_id, key, cancelled)
        task.signals.rendered.connect(self._rendered)
        task.signals.failed.connect(self._failed)
        task.signals.finished.connect(self._finished)
        self._tasks[request_id] = task
        self._cancellations[request_id] = cancelled
        self.thread_pool.start(task)
        return request_id

    def cancel(self, request_id: int) -> None:
        """Suppress delivery for a queued or active render request."""
        cancellation = self._cancellations.get(request_id)
        if cancellation is not None:
            cancellation.set()

    def invalidate(self, path: Path | None = None) -> None:
        self.cache.invalidate(path)

    @Slot(int, object, object)
    def _rendered(
        self,
        request_id: int,
        key: ThumbnailKey,
        data: ThumbnailData,
    ) -> None:
        cancellation = self._cancellations.get(request_id)
        if cancellation is None or cancellation.is_set():
            return
        try:
            current_key = self.cache.key_for(
                Path(key.path),
                key.page_index,
                key.scale,
            )
        except OSError:
            self.thumbnailFailed.emit(
                request_id,
                "Preview unavailable: the PDF file was not found.",
            )
            return
        if current_key != key:
            self.thumbnailFailed.emit(
                request_id,
                "Preview expired because the source PDF changed.",
            )
            return
        self.cache.put(key, data)
        self.thumbnailReady.emit(request_id, data)

    @Slot(int)
    def _finished(self, request_id: int) -> None:
        self._tasks.pop(request_id, None)
        self._cancellations.pop(request_id, None)

    @Slot(int, str)
    def _failed(self, request_id: int, message: str) -> None:
        cancellation = self._cancellations.get(request_id)
        if cancellation is None or cancellation.is_set():
            return
        self.thumbnailFailed.emit(request_id, message)


_shared_service: ThumbnailService | None = None


def shared_thumbnail_service() -> ThumbnailService:
    """Return the process-wide renderer with a bounded dedicated thread pool."""
    global _shared_service
    if _shared_service is None:
        _shared_service = ThumbnailService()
    return _shared_service


__all__ = [
    "DEFAULT_THUMBNAIL_SCALE",
    "MAX_CACHE_ENTRIES",
    "MAX_RENDER_JOBS",
    "ThumbnailCache",
    "ThumbnailData",
    "ThumbnailKey",
    "ThumbnailService",
    "shared_thumbnail_service",
]

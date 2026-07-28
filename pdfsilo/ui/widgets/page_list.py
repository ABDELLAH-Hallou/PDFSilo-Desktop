"""Thumbnail-backed page model and non-destructive reorder editor."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QByteArray,
    QFileSystemWatcher,
    QMimeData,
    QModelIndex,
    QSize,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdfsilo.ui.thumbnails import (
    DEFAULT_THUMBNAIL_SCALE,
    ThumbnailData,
    ThumbnailService,
    shared_thumbnail_service,
)

PAGE_ROWS_MIME_TYPE = "application/x-pdfsilo-page-rows"


@dataclass(slots=True)
class PageListItem:
    """One editable list entry tied to an immutable source-page index."""

    original_index: int
    thumbnail: QImage | None = None


class PdfPageListModel(QAbstractListModel):
    """Expose PDF pages with stable original indexes and lazy thumbnails."""

    orderChanged = Signal(list)
    documentLoaded = Signal(int)
    documentFailed = Signal(str)

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
        self._items: list[PageListItem] = []
        self._document_page_count = 0
        self._requests: dict[int, int] = {}
        self._probe_request: int | None = None
        self.service.thumbnailReady.connect(self._thumbnail_ready)
        self.service.thumbnailFailed.connect(self._thumbnail_failed)

    def source_path(self) -> Path | None:
        return self._source_path

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return f"Page {item.original_index + 1}"
        if role == Qt.ItemDataRole.ToolTipRole:
            return (
                f"Source page {item.original_index + 1}; "
                f"current position {index.row() + 1}"
            )
        if role == Qt.ItemDataRole.UserRole:
            return item.original_index
        if role == Qt.ItemDataRole.DecorationRole:
            if item.thumbnail is None:
                self._request_thumbnail(item.original_index)
                return None
            return QPixmap.fromImage(item.thumbnail)
        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(150, 190)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignHCenter)
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        base = (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsDropEnabled
        )
        if index.isValid():
            base |= Qt.ItemFlag.ItemIsDragEnabled
        return base

    def mimeTypes(self) -> list[str]:
        return [PAGE_ROWS_MIME_TYPE]

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:
        rows = sorted({index.row() for index in indexes if index.isValid()})
        mime_data = QMimeData()
        mime_data.setData(
            PAGE_ROWS_MIME_TYPE,
            QByteArray(json.dumps(rows).encode("ascii")),
        )
        return mime_data

    def supportedDropActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        _column: int,
        parent: QModelIndex,
    ) -> bool:
        if action == Qt.DropAction.IgnoreAction:
            return True
        if action != Qt.DropAction.MoveAction or not data.hasFormat(
            PAGE_ROWS_MIME_TYPE
        ):
            return False
        try:
            rows = sorted(
                {
                    int(value)
                    for value in json.loads(
                        bytes(data.data(PAGE_ROWS_MIME_TYPE)).decode("ascii")
                    )
                }
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            return False
        if not rows or any(not 0 <= value < len(self._items) for value in rows):
            return False

        destination = (
            row if row >= 0 else parent.row() if parent.isValid() else len(self._items)
        )
        destination = min(max(0, destination), len(self._items))
        moved = [self._items[value] for value in rows]
        remaining = [
            item for index, item in enumerate(self._items) if index not in set(rows)
        ]
        adjusted_destination = destination - sum(value < destination for value in rows)
        adjusted_destination = min(
            max(0, adjusted_destination),
            len(remaining),
        )

        self.beginResetModel()
        self._items = (
            remaining[:adjusted_destination] + moved + remaining[adjusted_destination:]
        )
        self.endResetModel()
        self.orderChanged.emit(self.original_indexes())
        return True

    def load_pdf(self, path: Path | str | None) -> None:
        """Reset the model and asynchronously probe the selected document."""
        self._cancel_requests()
        self.beginResetModel()
        self._items = []
        self._document_page_count = 0
        self._source_path = Path(path).expanduser() if path else None
        self.endResetModel()
        self.orderChanged.emit([])
        if self._source_path is None:
            return
        self._probe_request = self.service.request(
            self._source_path,
            0,
            self.scale,
        )

    def original_indexes(self) -> list[int]:
        return [item.original_index for item in self._items]

    def order_string(self) -> str:
        return ",".join(
            str(original_index + 1) for original_index in self.original_indexes()
        )

    def duplicate_rows(self, rows: list[int]) -> None:
        selected = {row for row in rows if 0 <= row < len(self._items)}
        if not selected:
            return
        new_items: list[PageListItem] = []
        for row, item in enumerate(self._items):
            new_items.append(item)
            if row in selected:
                new_items.append(
                    PageListItem(
                        item.original_index,
                        item.thumbnail.copy() if item.thumbnail is not None else None,
                    )
                )
        self._replace_items(new_items)

    def remove_rows(self, rows: list[int]) -> None:
        selected = {row for row in rows if 0 <= row < len(self._items)}
        if not selected:
            return
        self._replace_items(
            [item for row, item in enumerate(self._items) if row not in selected]
        )

    def reverse(self) -> None:
        if len(self._items) > 1:
            self._replace_items(list(reversed(self._items)))

    def reset_order(self) -> None:
        if not self._document_page_count:
            return
        by_original: dict[int, QImage | None] = {}
        for item in self._items:
            by_original.setdefault(item.original_index, item.thumbnail)
        self._replace_items(
            [
                PageListItem(
                    original,
                    by_original[original].copy()
                    if by_original.get(original) is not None
                    else None,
                )
                for original in range(self._document_page_count)
            ]
        )

    def _replace_items(self, items: list[PageListItem]) -> None:
        self.beginResetModel()
        self._items = items
        self.endResetModel()
        self.orderChanged.emit(self.original_indexes())

    def _request_thumbnail(self, original_index: int) -> None:
        if self._source_path is None:
            return
        if original_index in self._requests.values():
            return
        request_id = self.service.request(
            self._source_path,
            original_index,
            self.scale,
        )
        self._requests[request_id] = original_index

    @Slot(int, object)
    def _thumbnail_ready(
        self,
        request_id: int,
        data: ThumbnailData,
    ) -> None:
        if request_id == self._probe_request:
            self._probe_request = None
            self._document_page_count = data.page_count
            self.beginResetModel()
            self._items = [
                PageListItem(original_index)
                for original_index in range(data.page_count)
            ]
            if self._items:
                self._items[0].thumbnail = data.image.copy()
            self.endResetModel()
            self.orderChanged.emit(self.original_indexes())
            self.documentLoaded.emit(data.page_count)
            return

        original_index = self._requests.pop(request_id, None)
        if original_index is None:
            return
        changed_rows = []
        for row, item in enumerate(self._items):
            if item.original_index == original_index:
                item.thumbnail = data.image.copy()
                changed_rows.append(row)
        for row in changed_rows:
            index = self.index(row, 0)
            self.dataChanged.emit(
                index,
                index,
                [Qt.ItemDataRole.DecorationRole],
            )

    @Slot(int, str)
    def _thumbnail_failed(self, request_id: int, message: str) -> None:
        if request_id == self._probe_request:
            self._probe_request = None
            self.documentFailed.emit(message)
            return
        self._requests.pop(request_id, None)

    def _cancel_requests(self) -> None:
        if self._probe_request is not None:
            self.service.cancel(self._probe_request)
            self._probe_request = None
        for request_id in self._requests:
            self.service.cancel(request_id)
        self._requests.clear()


class PageReorderEditor(QWidget):
    """Edit a page sequence in memory and leave the source file untouched."""

    orderChanged = Signal(list)
    documentLoaded = Signal(int)
    documentFailed = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        service: ThumbnailService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pageReorderEditor")
        self.setAccessibleName("Page reorder editor")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.status_label = QLabel(
            "Select a PDF to load its pages.",
            self,
        )
        self.status_label.setObjectName("pageListStatus")
        self.status_label.setWordWrap(True)

        self.view = QListView(self)
        self.view.setObjectName("pageListView")
        self.view.setAccessibleName("PDF pages")
        self.view.setModel(PdfPageListModel(self.view, service=service))
        self.view.setViewMode(QListView.ViewMode.IconMode)
        self.view.setResizeMode(QListView.ResizeMode.Adjust)
        self.view.setMovement(QListView.Movement.Snap)
        self.view.setWrapping(True)
        self.view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.view.setDragEnabled(True)
        self.view.setAcceptDrops(True)
        self.view.setDropIndicatorShown(True)
        self.view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.view.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.view.setMinimumHeight(240)

        actions = QWidget(self)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        self.duplicate_button = QPushButton("&Duplicate selected", actions)
        self.delete_button = QPushButton("&Delete selected", actions)
        self.reverse_button = QPushButton("&Reverse all", actions)
        self.reset_button = QPushButton("R&eset order", actions)
        actions_layout.addWidget(self.duplicate_button)
        actions_layout.addWidget(self.delete_button)
        actions_layout.addWidget(self.reverse_button)
        actions_layout.addWidget(self.reset_button)
        actions_layout.addStretch(1)

        layout.addWidget(self.status_label)
        layout.addWidget(self.view)
        layout.addWidget(actions)

        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._source_changed)
        self.model.orderChanged.connect(self.orderChanged.emit)
        self.model.documentLoaded.connect(self._document_loaded)
        self.model.documentFailed.connect(self._document_failed)
        self.duplicate_button.clicked.connect(self.duplicate_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.reverse_button.clicked.connect(self.model.reverse)
        self.reset_button.clicked.connect(self.model.reset_order)
        self._set_actions_enabled(False)

    @property
    def model(self) -> PdfPageListModel:
        model = self.view.model()
        assert isinstance(model, PdfPageListModel)
        return model

    def set_pdf(self, path: Path | str | None) -> None:
        watched = self._watcher.files()
        if watched:
            self._watcher.removePaths(watched)
        source = Path(path).expanduser() if path else None
        if source is not None and source.is_file():
            self._watcher.addPath(str(source.resolve()))
        self.status_label.setText(
            "Loading page thumbnails…"
            if source is not None
            else "Select a PDF to load its pages."
        )
        self._set_actions_enabled(False)
        self.model.load_pdf(source)

    def order_string(self) -> str:
        return self.model.order_string()

    def selected_rows(self) -> list[int]:
        return sorted(
            {index.row() for index in self.view.selectionModel().selectedIndexes()}
        )

    @Slot()
    def duplicate_selected(self) -> None:
        self.model.duplicate_rows(self.selected_rows())

    @Slot()
    def delete_selected(self) -> None:
        self.model.remove_rows(self.selected_rows())

    @Slot(int)
    def _document_loaded(self, page_count: int) -> None:
        self.status_label.setText(
            f"{page_count} page(s) loaded. Drag thumbnails to reorder."
        )
        self._set_actions_enabled(page_count > 0)
        self.documentLoaded.emit(page_count)

    @Slot(str)
    def _document_failed(self, message: str) -> None:
        self.status_label.setText(message)
        self._set_actions_enabled(False)
        self.documentFailed.emit(message)

    @Slot(str)
    def _source_changed(self, _path: str) -> None:
        source = self.model.source_path()
        if source is not None:
            self.model.service.invalidate(source)
            self.set_pdf(source)

    def _set_actions_enabled(self, enabled: bool) -> None:
        self.view.setEnabled(enabled)
        self.duplicate_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)
        self.reverse_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)


__all__ = [
    "PAGE_ROWS_MIME_TYPE",
    "PageListItem",
    "PageReorderEditor",
    "PdfPageListModel",
]

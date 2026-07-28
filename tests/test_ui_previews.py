"""Tests for Phase 10 preview rendering and page-list editing."""

from threading import get_ident

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QImage, QPixmap

from pdfsilo.ui import thumbnails
from pdfsilo.ui.pages import OPERATION_PAGE_FACTORIES, PAGE_DEFINITIONS
from pdfsilo.ui.thumbnails import (
    MAX_RENDER_JOBS,
    ThumbnailCache,
    ThumbnailData,
    ThumbnailService,
)
from pdfsilo.ui.widgets import (
    PageReorderEditor,
    PdfPageListModel,
    PdfPreview,
)


def _request_success(qtbot, service, path, page=0, scale=0.2):
    results = []
    service.thumbnailReady.connect(
        lambda request_id, data: results.append((request_id, data))
    )
    with qtbot.waitSignal(service.thumbnailReady, timeout=5_000):
        request_id = service.request(path, page, scale)
    matched = [data for result_id, data in results if result_id == request_id]
    assert len(matched) == 1
    return matched[0]


def test_thumbnail_rendering_runs_off_ui_thread_and_returns_detached_image(
    qtbot,
    tmp_multi_pdf,
    monkeypatch,
):
    service = ThumbnailService(max_jobs=2)
    main_thread = get_ident()
    render_threads = []
    real_open = thumbnails.fitz.open

    def tracked_open(*args, **kwargs):
        render_threads.append(get_ident())
        return real_open(*args, **kwargs)

    monkeypatch.setattr(thumbnails.fitz, "open", tracked_open)

    data = _request_success(qtbot, service, tmp_multi_pdf)

    assert render_threads
    assert all(thread_id != main_thread for thread_id in render_threads)
    assert isinstance(data, ThumbnailData)
    assert isinstance(data.image, QImage)
    assert not data.image.isNull()
    assert data.page_count == 5
    assert service.max_jobs == 2


def test_thumbnail_cache_uses_file_signature_page_and_scale(
    qtbot,
    tmp_pdf,
    monkeypatch,
):
    cache = ThumbnailCache(max_entries=4)
    service = ThumbnailService(cache=cache)
    real_open = thumbnails.fitz.open
    open_count = 0

    def counted_open(*args, **kwargs):
        nonlocal open_count
        open_count += 1
        return real_open(*args, **kwargs)

    monkeypatch.setattr(thumbnails.fitz, "open", counted_open)
    _request_success(qtbot, service, tmp_pdf, scale=0.2)
    _request_success(qtbot, service, tmp_pdf, scale=0.2)

    assert open_count == 1
    assert len(cache) == 1

    # A trailing PDF comment changes both the file signature and cache key
    # while keeping the source readable by PyMuPDF.
    with tmp_pdf.open("ab") as stream:
        stream.write(b"\n% preview cache invalidation\n")
    _request_success(qtbot, service, tmp_pdf, scale=0.2)

    assert open_count == 2
    assert len(cache) == 1

    _request_success(qtbot, service, tmp_pdf, scale=0.3)
    assert open_count == 3
    assert len(cache) == 2


def test_thumbnail_service_limits_its_dedicated_pool():
    service = ThumbnailService()

    assert service.max_jobs == MAX_RENDER_JOBS == 2
    assert service.thread_pool is not thumbnails.QThreadPool.globalInstance()


def test_operation_pages_integrate_preview_or_page_editor(qtbot):
    definitions = {definition.key: definition for definition in PAGE_DEFINITIONS}
    standard_preview_keys = {
        "merge",
        "split",
        "rotate",
        "extract_pages",
        "compress",
        "encrypt",
        "decrypt",
        "watermark",
        "extract_images",
        "to_images",
        "add_images",
    }

    for key, factory in OPERATION_PAGE_FACTORIES.items():
        page = factory(definitions[key])
        qtbot.addWidget(page)
        if key in standard_preview_keys:
            assert isinstance(page.pdf_preview, PdfPreview)
        else:
            assert page.pdf_preview is None
        if key == "reorder":
            assert isinstance(page.page_editor, PageReorderEditor)


@pytest.mark.parametrize("source_kind", ["encrypted", "invalid"])
def test_preview_shows_clear_placeholder_for_unavailable_pdf(
    qtbot,
    encrypted_pdf,
    tmp_path,
    source_kind,
):
    if source_kind == "encrypted":
        source = encrypted_pdf[0]
        expected = "encrypted"
    else:
        source = tmp_path / "invalid.pdf"
        source.write_text("not a PDF", encoding="utf-8")
        expected = "invalid or unreadable"

    preview = PdfPreview(service=ThumbnailService())
    qtbot.addWidget(preview)
    failures = []
    preview.previewFailed.connect(failures.append)

    with qtbot.waitSignal(preview.previewFailed, timeout=5_000):
        preview.set_pdf(source)

    assert failures and expected in failures[0]
    assert expected in preview.status_label.text()
    assert preview.image_label.text() == "No preview"
    assert preview.image_label.pixmap().isNull()


def test_pdf_preview_navigation_uses_qpixmap_on_gui_thread(
    qtbot,
    tmp_multi_pdf,
):
    preview = PdfPreview(service=ThumbnailService())
    qtbot.addWidget(preview)

    with qtbot.waitSignal(preview.previewReady, timeout=5_000):
        preview.set_pdf(tmp_multi_pdf)

    assert preview.page_count() == 5
    assert preview.page_index() == 0
    assert isinstance(preview.image_label.pixmap(), QPixmap)
    assert not preview.image_label.pixmap().isNull()
    assert not preview.previous_button.isEnabled()
    assert preview.next_button.isEnabled()

    with qtbot.waitSignal(preview.previewReady, timeout=5_000):
        preview.next_button.click()

    assert preview.page_index() == 1
    assert "Page 2 of 5" == preview.page_label.text()
    assert preview.previous_button.isEnabled()


def test_pdf_preview_switches_merge_inputs_zooms_and_shows_target_canvas(
    qtbot,
    tmp_pdf_folder,
):
    sources = sorted(tmp_pdf_folder.glob("*.pdf"))
    preview = PdfPreview(service=ThumbnailService())
    preview.resize(520, 620)
    qtbot.addWidget(preview)

    with qtbot.waitSignal(preview.previewReady, timeout=5_000):
        preview.set_pdfs(sources)

    assert preview.source_paths() == sources
    assert not preview.document_row.isHidden()
    assert preview.document_combo.count() == len(sources)

    with qtbot.waitSignal(preview.previewReady, timeout=5_000):
        preview.document_combo.setCurrentIndex(1)
    assert preview.source_path() == sources[1]

    preview.set_target_page_size("A4")
    assert preview.target_label.text() == "Output canvas · A4"
    pixmap = preview.image_label.pixmap()
    assert not pixmap.isNull()
    assert pixmap.height() > pixmap.width()

    preview.zoom_in_button.click()
    assert not preview.is_fit_to_window()
    assert preview.zoom_factor() == 1.25
    assert preview.zoom_label.text() == "125%"
    preview.fit_button.click()
    assert preview.is_fit_to_window()
    assert preview.zoom_label.text() == "Fit"


def test_page_model_stores_original_indexes_and_loads_thumbnails_lazily(
    qtbot,
    tmp_multi_pdf,
):
    model = PdfPageListModel(service=ThumbnailService())

    with qtbot.waitSignal(model.documentLoaded, timeout=5_000):
        model.load_pdf(tmp_multi_pdf)

    assert model.rowCount() == 5
    assert model.original_indexes() == [0, 1, 2, 3, 4]
    assert model.data(model.index(2, 0), Qt.ItemDataRole.UserRole) == 2
    assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) == "Page 1"
    first_thumbnail = model.data(
        model.index(0, 0),
        Qt.ItemDataRole.DecorationRole,
    )
    assert isinstance(first_thumbnail, QPixmap)
    assert not first_thumbnail.isNull()

    with qtbot.waitSignal(model.dataChanged, timeout=5_000):
        assert (
            model.data(
                model.index(1, 0),
                Qt.ItemDataRole.DecorationRole,
            )
            is None
        )
    assert isinstance(
        model.data(
            model.index(1, 0),
            Qt.ItemDataRole.DecorationRole,
        ),
        QPixmap,
    )


def test_reorder_editor_actions_and_drag_are_non_destructive(
    qtbot,
    tmp_multi_pdf,
):
    original_bytes = tmp_multi_pdf.read_bytes()
    editor = PageReorderEditor(service=ThumbnailService())
    qtbot.addWidget(editor)

    with qtbot.waitSignal(editor.documentLoaded, timeout=5_000):
        editor.set_pdf(tmp_multi_pdf)

    model = editor.model
    assert model.original_indexes() == [0, 1, 2, 3, 4]

    model.duplicate_rows([0])
    assert model.original_indexes() == [0, 0, 1, 2, 3, 4]
    model.remove_rows([1, 4])
    assert model.original_indexes() == [0, 1, 2, 4]
    model.reverse()
    assert model.original_indexes() == [4, 2, 1, 0]
    model.reset_order()
    assert model.original_indexes() == [0, 1, 2, 3, 4]

    dragged = model.mimeData([model.index(0, 0)])
    assert model.dropMimeData(
        dragged,
        Qt.DropAction.MoveAction,
        model.rowCount(),
        0,
        QModelIndex(),
    )
    assert model.original_indexes() == [1, 2, 3, 4, 0]
    assert model.order_string() == "2,3,4,5,1"
    assert tmp_multi_pdf.read_bytes() == original_bytes

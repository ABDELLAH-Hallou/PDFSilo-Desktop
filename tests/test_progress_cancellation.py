"""Regression tests for framework-independent progress and cancellation."""

import importlib
import inspect
from pathlib import Path

import pytest

from safepdf.core import OperationCancelledError
from safepdf.core.progress import check_cancelled
from safepdf.operations.add_images import execute as add_images
from safepdf.operations.concat import execute as concat_pdfs
from safepdf.operations.extract_images import execute as extract_images
from safepdf.operations.images_to_pdf import execute as images_to_pdf
from safepdf.operations.rotate import execute as rotate_pdf
from safepdf.operations.split import execute as split_pdf
from safepdf.operations.to_images import execute as render_pages


OPERATION_MODULES = [
    "add_images",
    "compress",
    "concat",
    "decrypt",
    "encrypt",
    "extract_images",
    "extract_range",
    "images_to_pdf",
    "reorder",
    "rotate",
    "split",
    "to_images",
    "watermark",
]


@pytest.mark.parametrize("module_name", OPERATION_MODULES)
def test_every_operation_accepts_keyword_only_callbacks(module_name: str):
    module = importlib.import_module(f"safepdf.operations.{module_name}")
    parameters = inspect.signature(module.execute).parameters

    assert parameters["progress"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["is_cancelled"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["progress"].default is None
    assert parameters["is_cancelled"].default is None


def test_cancellation_helper_raises_typed_error():
    with pytest.raises(OperationCancelledError, match="cancelled"):
        check_cancelled(lambda: True)


def test_split_reports_each_page(
    tmp_multi_pdf: Path,
    tmp_path: Path,
):
    events: list[tuple[int, int, str]] = []

    result = split_pdf(
        tmp_multi_pdf,
        tmp_path / "pages",
        progress=lambda current, total, message: events.append(
            (current, total, message)
        ),
    )

    assert result.processed_pages == 5
    assert [(current, total) for current, total, _ in events] == [
        (1, 5),
        (2, 5),
        (3, 5),
        (4, 5),
        (5, 5),
    ]
    assert all(message for _, _, message in events)


def test_concat_reports_each_input_file(
    tmp_pdf_folder: Path,
    tmp_path: Path,
):
    input_files = sorted(tmp_pdf_folder.glob("*.pdf"))
    events: list[tuple[int, int, str]] = []

    concat_pdfs(
        input_files,
        tmp_path / "merged.pdf",
        progress=lambda current, total, message: events.append(
            (current, total, message)
        ),
    )

    assert [(current, total) for current, total, _ in events] == [
        (1, 3),
        (2, 3),
        (3, 3),
    ]


def test_image_operations_report_meaningful_units(
    tmp_pdf: Path,
    pdf_with_image: Path,
    tmp_two_png_images: list[Path],
    tmp_image_folder: Path,
    tmp_path: Path,
):
    events: dict[str, list[tuple[int, int]]] = {
        "add": [],
        "extract": [],
        "build": [],
        "render": [],
    }

    add_images(
        tmp_pdf,
        tmp_two_png_images,
        tmp_path / "with-images.pdf",
        progress=lambda current, total, _message: events["add"].append(
            (current, total)
        ),
    )
    extract_images(
        pdf_with_image,
        tmp_path / "extracted",
        progress=lambda current, total, _message: events["extract"].append(
            (current, total)
        ),
    )
    images_to_pdf(
        tmp_image_folder,
        tmp_path / "images.pdf",
        progress=lambda current, total, _message: events["build"].append(
            (current, total)
        ),
    )
    render_pages(
        tmp_pdf,
        tmp_path / "rendered",
        progress=lambda current, total, _message: events["render"].append(
            (current, total)
        ),
    )

    assert events == {
        "add": [(1, 2), (2, 2)],
        "extract": [(1, 1)],
        "build": [(1, 3), (2, 3), (3, 3)],
        "render": [(1, 1)],
    }


def test_split_cancellation_preserves_existing_folder_and_cleans_staging(
    tmp_multi_pdf: Path,
    tmp_path: Path,
):
    output_directory = tmp_path / "pages"
    output_directory.mkdir()
    existing = output_directory / "keep.txt"
    existing.write_text("keep", encoding="utf-8")
    cancelled = False

    def on_progress(current: int, _total: int, _message: str) -> None:
        nonlocal cancelled
        if current == 2:
            cancelled = True

    with pytest.raises(OperationCancelledError):
        split_pdf(
            tmp_multi_pdf,
            output_directory,
            progress=on_progress,
            is_cancelled=lambda: cancelled,
        )

    assert existing.read_text(encoding="utf-8") == "keep"
    assert list(output_directory.iterdir()) == [existing]
    assert not list(tmp_path.glob(".pages.*.tmp"))


def test_render_cancellation_leaves_no_output_or_staging(
    tmp_multi_pdf: Path,
    tmp_path: Path,
):
    output_directory = tmp_path / "rendered"
    cancelled = False

    def on_progress(current: int, _total: int, _message: str) -> None:
        nonlocal cancelled
        if current == 1:
            cancelled = True

    with pytest.raises(OperationCancelledError):
        render_pages(
            tmp_multi_pdf,
            output_directory,
            progress=on_progress,
            is_cancelled=lambda: cancelled,
        )

    assert not output_directory.exists()
    assert not list(tmp_path.glob(".rendered.*.tmp"))


def test_single_file_cancellation_preserves_existing_destination(
    tmp_multi_pdf: Path,
    tmp_path: Path,
):
    output_path = tmp_path / "rotated.pdf"
    output_path.write_bytes(b"original")
    cancelled = False

    def on_progress(current: int, _total: int, _message: str) -> None:
        nonlocal cancelled
        if current == 2:
            cancelled = True

    with pytest.raises(OperationCancelledError):
        rotate_pdf(
            tmp_multi_pdf,
            90,
            output_path=output_path,
            progress=on_progress,
            is_cancelled=lambda: cancelled,
        )

    assert output_path.read_bytes() == b"original"
    assert not list(tmp_path.glob(".rotated.*.tmp"))

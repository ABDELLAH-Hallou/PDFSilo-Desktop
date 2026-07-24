"""Regression tests for the Phase 3 structured core-operation contracts."""

import importlib
import logging
from pathlib import Path

import pytest

from safepdf.core import (
    InvalidInputError,
    OperationCancelledError,
    OperationResult,
    OutputWriteError,
    PdfPasswordError,
    PdfProcessingError,
    SafePdfError,
)
from safepdf.operations import split
from safepdf.operations.compress import execute as compress_pdf
from safepdf.operations.concat import execute as concat_pdfs
from safepdf.operations.decrypt import execute as decrypt_pdf
from safepdf.operations.rotate import execute as rotate_pdf
from safepdf.operations.split import execute as split_pdf


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


def test_operation_result_defaults():
    output = Path("output.pdf")
    result = OperationResult(output_paths=[output], message="done")

    assert result.output_paths == [output]
    assert result.message == "done"
    assert result.warnings == []
    assert result.source_paths == []
    assert result.metadata == {}


@pytest.mark.parametrize(
    "error_type",
    [
        InvalidInputError,
        OperationCancelledError,
        OutputWriteError,
        PdfPasswordError,
        PdfProcessingError,
    ],
)
def test_typed_errors_share_safe_pdf_base(error_type):
    assert issubclass(error_type, SafePdfError)


@pytest.mark.parametrize("module_name", OPERATION_MODULES)
def test_every_operation_exposes_structured_execute_function(module_name: str):
    module = importlib.import_module(f"safepdf.operations.{module_name}")
    assert callable(module.execute)


def test_split_execute_returns_structured_result(
    tmp_multi_pdf: Path,
    tmp_path: Path,
):
    output_directory = tmp_path / "pages"
    result = split_pdf(tmp_multi_pdf, output_directory)

    assert isinstance(result, OperationResult)
    assert result.source_paths == [tmp_multi_pdf]
    assert result.processed_pages == 5
    assert result.processed_files == 1
    assert len(result.output_paths) == 5
    assert all(path.is_file() for path in result.output_paths)


def test_core_validation_raises_typed_error(tmp_path: Path):
    with pytest.raises(InvalidInputError, match="No PDF files"):
        concat_pdfs([], tmp_path / "output.pdf")


def test_password_failure_raises_typed_error(
    encrypted_pdf: tuple[Path, str],
    tmp_path: Path,
):
    encrypted_path, _ = encrypted_pdf

    with pytest.raises(PdfPasswordError, match="Incorrect password"):
        decrypt_pdf(
            encrypted_path,
            "wrong-password",
            tmp_path / "output.pdf",
        )


def test_pymupdf_failure_retains_original_cause(tmp_path: Path):
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"this is not a valid PDF")

    with pytest.raises(PdfProcessingError) as caught:
        compress_pdf(corrupt_pdf, tmp_path / "output.pdf")

    assert str(corrupt_pdf) in str(caught.value)
    assert caught.value.__cause__ is not None


def test_output_failure_retains_original_cause(
    tmp_pdf: Path,
    tmp_path: Path,
):
    missing_parent = tmp_path / "missing" / "output.pdf"

    with pytest.raises(OutputWriteError) as caught:
        compress_pdf(tmp_pdf, missing_parent)

    assert str(missing_parent) in str(caught.value)
    assert caught.value.__cause__ is not None


def test_core_warnings_are_returned_without_logging(
    tmp_multi_pdf: Path,
    tmp_path: Path,
    caplog,
):
    with caplog.at_level(logging.DEBUG):
        result = rotate_pdf(
            tmp_multi_pdf,
            90,
            pages="0,1",
            output_path=tmp_path / "rotated.pdf",
        )

    assert result.processed_pages == 1
    assert any("out of range" in warning for warning in result.warnings)
    assert not caplog.records


def test_cli_adapter_consumes_structured_success(
    tmp_pdf: Path,
    tmp_path: Path,
    monkeypatch,
    caplog,
):
    output = tmp_path / "output.pdf"
    expected = OperationResult(output_paths=[output], message="structured success")

    monkeypatch.setattr(split, "execute", lambda *_args, **_kwargs: expected)

    class Args:
        input = str(tmp_pdf)
        output = str(tmp_path / "pages")

    with caplog.at_level(logging.INFO):
        assert split.cli_run(Args()) is True
    assert "structured success" in caplog.text


def test_cli_adapter_converts_typed_error_to_false(
    tmp_pdf: Path,
    tmp_path: Path,
    monkeypatch,
    caplog,
):
    def fail(*_args, **_kwargs):
        raise InvalidInputError("structured failure")

    monkeypatch.setattr(split, "execute", fail)

    class Args:
        input = str(tmp_pdf)
        output = str(tmp_path / "pages")

    with caplog.at_level(logging.ERROR):
        assert split.cli_run(Args()) is False
    assert "structured failure" in caplog.text

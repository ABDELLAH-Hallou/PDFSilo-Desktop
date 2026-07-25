"""
decrypt.py — Remove password protection from a PDF you own.

Usage:
    python -m safepdf decrypt <input> [-p PASSWORD] [-o OUTPUT]

Arguments:
    input               Path to the encrypted PDF file
    -p, --password      Password to unlock the document. Omit for a secure prompt.
    -o, --output        Output file path (default: <input_stem>_decrypted.pdf)

Examples:
    safepdf decrypt contract_encrypted.pdf
    safepdf decrypt contract_encrypted.pdf -p s3cr3t -o contract_open.pdf
"""

import logging
from pathlib import Path

import fitz

from safepdf.core import (
    CancellationCheck,
    OperationResult,
    PdfPasswordError,
    PdfProcessingError,
    ProgressCallback,
    SafePdfError,
)
from safepdf.core.output import save_document
from safepdf.core.progress import check_cancelled, report_progress
from safepdf.core.validation import require_pdf
from safepdf.presentation import present_operation

log = logging.getLogger(__name__)


def execute(
    input_path: Path,
    password: str,
    output_path: Path | None = None,
    *,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> OperationResult:
    """Decrypt a PDF and return structured output information."""
    path = require_pdf(input_path)
    out_path = output_path or path.parent / f"{path.stem}_decrypted.pdf"

    check_cancelled(is_cancelled)
    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not open encrypted PDF '{path}': {exc}"
        ) from exc

    try:
        was_encrypted = doc.is_encrypted
        if was_encrypted and doc.authenticate(password) == 0:
            raise PdfPasswordError(f"Incorrect password for '{path.name}'.")

        page_count = doc.page_count
        check_cancelled(is_cancelled)
        save_document(doc, out_path, encryption=fitz.PDF_ENCRYPT_NONE)
        report_progress(
            progress,
            1,
            1,
            f"Decrypted '{path.name}'.",
        )
    except SafePdfError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not decrypt PDF '{path}': {exc}"
        ) from exc
    finally:
        doc.close()

    return OperationResult(
        output_paths=[out_path],
        source_paths=[path],
        processed_pages=page_count,
        processed_files=1,
        metadata={"was_encrypted": was_encrypted},
        message=f"Decrypted PDF saved to '{out_path}'.",
    )


def run(input_path: str, password: str, output_path: str | None = None) -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            password,
            Path(output_path) if output_path else None,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            args.password,
            Path(args.output) if args.output else None,
        ),
        log,
    )

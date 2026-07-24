"""
encrypt.py — Password-protect a PDF.

Usage:
    python -m safepdf encrypt <input> -p PASSWORD [-o OUTPUT] [--owner-password PASSWORD]
                              [--no-print] [--no-copy] [--no-edit]

Arguments:
    input                   Path to the input PDF file
    -p, --password          User password required to open the document (required)
    --owner-password        Owner password for permission control. Required
                            and must differ when restrictions are requested.
    -o, --output            Output file path (default: <input_stem>_encrypted.pdf)
    --no-print              Disallow printing
    --no-copy               Disallow text/image copying
    --no-edit               Disallow editing and annotations

Examples:
    # Basic password protection
    safepdf encrypt contract.pdf -p s3cr3t

    # Full control: separate owner password, no copying allowed
    safepdf encrypt contract.pdf -p s3cr3t --owner-password adm1n --no-copy
"""

import logging
from pathlib import Path

import fitz

from safepdf.core import (
    CancellationCheck,
    InvalidInputError,
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
    user_password: str,
    owner_password: str | None = None,
    output_path: Path | None = None,
    allow_print: bool = True,
    allow_copy: bool = True,
    allow_edit: bool = True,
    *,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> OperationResult:
    """Encrypt a PDF and return structured permission information."""
    path = require_pdf(input_path)
    if not user_password:
        raise InvalidInputError("User password cannot be empty.")

    out_path = output_path or path.parent / f"{path.stem}_encrypted.pdf"
    restrictions_requested = not (allow_print and allow_copy and allow_edit)
    if restrictions_requested and not owner_password:
        raise PdfPasswordError(
            "A distinct owner password is required when permission restrictions are enabled."
        )
    if owner_password and owner_password == user_password and restrictions_requested:
        raise PdfPasswordError(
            "Owner and user passwords must differ when permission restrictions are enabled."
        )

    owner_pw = owner_password or user_password

    permissions = (
        fitz.PDF_PERM_ACCESSIBILITY
        | (fitz.PDF_PERM_PRINT if allow_print else 0)
        | (fitz.PDF_PERM_COPY if allow_copy else 0)
        | (fitz.PDF_PERM_MODIFY if allow_edit else 0)
        | (fitz.PDF_PERM_ANNOTATE if allow_edit else 0)
    )

    try:
        check_cancelled(is_cancelled)
        with fitz.open(str(path)) as doc:
            page_count = doc.page_count
            save_document(
                doc,
                out_path,
                encryption=fitz.PDF_ENCRYPT_AES_256,
                user_pw=user_password,
                owner_pw=owner_pw,
                permissions=permissions,
            )
            report_progress(
                progress,
                1,
                1,
                f"Encrypted '{path.name}'.",
            )

    except SafePdfError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not encrypt PDF '{path}': {exc}"
        ) from exc

    return OperationResult(
        output_paths=[out_path],
        source_paths=[path],
        processed_pages=page_count,
        processed_files=1,
        metadata={
            "allow_print": allow_print,
            "allow_copy": allow_copy,
            "allow_edit": allow_edit,
            "encryption": "AES-256",
        },
        message=f"Encrypted PDF saved to '{out_path}'.",
    )


def run(
    input_path: str,
    user_password: str,
    owner_password: str | None = None,
    output_path: str | None = None,
    allow_print: bool = True,
    allow_copy: bool = True,
    allow_edit: bool = True,
) -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            user_password,
            owner_password,
            Path(output_path) if output_path else None,
            allow_print,
            allow_copy,
            allow_edit,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            args.password,
            args.owner_password,
            Path(args.output) if args.output else None,
            allow_print=not args.no_print,
            allow_copy=not args.no_copy,
            allow_edit=not args.no_edit,
        ),
        log,
    )

"""
encrypt.py — Password-protect a PDF.

Usage:
    python -m safepdf encrypt <input> -p PASSWORD [-o OUTPUT] [--owner-password PASSWORD]
                              [--no-print] [--no-copy] [--no-edit]

Arguments:
    input                   Path to the input PDF file
    -p, --password          User password required to open the document (required)
    --owner-password        Owner password for permission control
                            (defaults to the user password if omitted)
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

from safepdf.utils import validate_pdf

log = logging.getLogger(__name__)


def run(
    input_path: str,
    user_password: str,
    owner_password: str | None = None,
    output_path: str | None = None,
    allow_print: bool = True,
    allow_copy: bool = True,
    allow_edit: bool = True,
) -> bool:
    path = Path(input_path)
    if not validate_pdf(path):
        return False

    out_path = Path(output_path) if output_path else path.parent / f"{path.stem}_encrypted.pdf"
    owner_pw = owner_password or user_password

    permissions = (
        fitz.PDF_PERM_ACCESSIBILITY
        | (fitz.PDF_PERM_PRINT if allow_print else 0)
        | (fitz.PDF_PERM_COPY if allow_copy else 0)
        | (fitz.PDF_PERM_MODIFY if allow_edit else 0)
        | (fitz.PDF_PERM_ANNOTATE if allow_edit else 0)
    )

    try:
        with fitz.open(str(path)) as doc:
            doc.save(
                str(out_path),
                encryption=fitz.PDF_ENCRYPT_AES_256,
                user_pw=user_password,
                owner_pw=owner_pw,
                permissions=permissions,
            )
        log.info("Encrypted PDF saved to '%s'.", out_path)
        return True

    except Exception as e:
        log.error("Error encrypting '%s': %s", path, e)
        return False


def cli_run(args) -> bool:
    return run(
        args.input,
        args.password,
        args.owner_password,
        args.output,
        allow_print=not args.no_print,
        allow_copy=not args.no_copy,
        allow_edit=not args.no_edit,
    )
"""
decrypt.py — Remove password protection from a PDF you own.

Usage:
    python -m safepdf decrypt <input> -p PASSWORD [-o OUTPUT]

Arguments:
    input               Path to the encrypted PDF file
    -p, --password      Password to unlock the document (required)
    -o, --output        Output file path (default: <input_stem>_decrypted.pdf)

Examples:
    safepdf decrypt contract_encrypted.pdf -p s3cr3t
    safepdf decrypt contract_encrypted.pdf -p s3cr3t -o contract_open.pdf
"""

import logging
from pathlib import Path

import fitz

from safepdf.utils import validate_pdf

log = logging.getLogger(__name__)


def run(input_path: str, password: str, output_path: str | None = None) -> bool:
    path = Path(input_path)
    if not validate_pdf(path):
        return False

    out_path = Path(output_path) if output_path else path.parent / f"{path.stem}_decrypted.pdf"

    try:
        doc = fitz.open(str(path))

        if doc.is_encrypted:
            result = doc.authenticate(password)
            if result == 0:
                log.error("Incorrect password for '%s'.", path.name)
                doc.close()
                return False
            log.info("Authentication successful.")
        else:
            log.info("'%s' is not encrypted — saving a clean copy.", path.name)

        doc.save(str(out_path), encryption=fitz.PDF_ENCRYPT_NONE)
        doc.close()
        log.info("Decrypted PDF saved to '%s'.", out_path)
        return True

    except Exception as e:
        log.error("Error decrypting '%s': %s", path, e)
        return False


def cli_run(args) -> bool:
    return run(args.input, args.password, args.output)
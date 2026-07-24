"""
split.py — Split a PDF into one file per page.

Usage:
    python -m safepdf split <input> [-o OUTPUT_FOLDER]

Arguments:
    input               Path to the PDF file to split
    -o, --output        Folder to save split pages (default: <input_stem>_pages/)

Behaviour:
    - Each page is saved as page_001.pdf, page_002.pdf, ...
    - Output folder is created automatically if it does not exist
    - A warning is shown if the output folder already contains files
"""

import logging
from pathlib import Path

import fitz

from safepdf.utils import atomic_output_path, validate_pdf, warn_if_nonempty

log = logging.getLogger(__name__)


def run(input_path: str, output_folder: str | None = None) -> bool:
    path = Path(input_path)
    if not validate_pdf(path):
        return False

    out_dir = Path(output_folder) if output_folder else path.parent / f"{path.stem}_pages"
    warn_if_nonempty(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        with fitz.open(str(path)) as src_doc:
            total = len(src_doc)
            log.info("Splitting '%s' (%d pages) → '%s'", path.name, total, out_dir)

            for page_num in range(total):
                out_doc = fitz.open()
                try:
                    out_doc.insert_pdf(src_doc, from_page=page_num, to_page=page_num)
                    out_path = out_dir / f"page_{page_num + 1:03d}.pdf"
                    with atomic_output_path(out_path) as temporary:
                        out_doc.save(str(temporary))
                    log.info("Saved: %s", out_path.name)
                finally:
                    out_doc.close()

        log.info("Done — %d pages saved to '%s'.", total, out_dir)
        return True

    except Exception as e:
        log.error("Error processing '%s': %s", path, e)
        return False


def cli_run(args) -> bool:
    return run(args.input, args.output)

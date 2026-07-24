"""
concat.py — Merge multiple PDFs into one normalized PDF.

Usage:
    python -m safepdf concat <folder> [-o OUTPUT] [-s {A4,Letter}]

Arguments:
    folder              Folder containing PDF files to merge
    -o, --output        Output file path (default: <folder_name>.pdf)
    -s, --size          Target page size: A4 or Letter (default: A4)

Behaviour:
    - Files are sorted numerically by the first integer in their filename
    - Each page is scaled to fit the target canvas, preserving aspect ratio
    - Landscape pages are detected and target dimensions flipped accordingly
    - Content is centered on the output page
"""

import logging
from pathlib import Path

import fitz

from safepdf.utils import PAGE_SIZES, get_sorted_pdf_files, validate_pdf

log = logging.getLogger(__name__)


def run(input_files: list[str], output_file: str, target_size: str = "A4") -> bool:
    if target_size not in PAGE_SIZES:
        raise ValueError(f"Unsupported page size '{target_size}'. Choose from: {list(PAGE_SIZES)}")

    target_w, target_h = PAGE_SIZES[target_size]
    output_doc = fitz.open()

    try:
        for pdf_path in input_files:
            path = Path(pdf_path)
            if not validate_pdf(path):
                continue

            try:
                with fitz.open(str(path)) as src_doc:
                    for page in src_doc:
                        src_w, src_h = page.rect.width, page.rect.height

                        if src_w > src_h:
                            tw, th = max(target_w, target_h), min(target_w, target_h)
                        else:
                            tw, th = min(target_w, target_h), max(target_w, target_h)

                        scale = min(tw / src_w, th / src_h)
                        scaled_w, scaled_h = src_w * scale, src_h * scale
                        x_offset = (tw - scaled_w) / 2
                        y_offset = (th - scaled_h) / 2

                        new_page = output_doc.new_page(width=tw, height=th)
                        new_page.show_pdf_page(
                            fitz.Rect(x_offset, y_offset,
                                      x_offset + scaled_w, y_offset + scaled_h),
                            src_doc,
                            page.number,
                        )

                    log.info("Added %d pages from '%s'", len(src_doc), path.name)

            except Exception as e:
                log.error("Error processing '%s': %s", path, e)

        if output_doc.page_count > 0:
            output_doc.save(output_file)
            log.info("Created '%s' with %d pages.", output_file, output_doc.page_count)
            return True

        log.warning("No pages to write. No output file created.")
        return False

    finally:
        output_doc.close()


def cli_run(args) -> bool:
    folder = Path(args.folder)
    output = args.output or f"{folder.name}.pdf"
    input_files = get_sorted_pdf_files(folder)
    if not input_files:
        log.error("No PDF files found in '%s'.", folder)
        return False
    return run(input_files, output, args.size)
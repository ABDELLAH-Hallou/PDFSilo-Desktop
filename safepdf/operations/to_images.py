"""
to_images.py — Render each PDF page as a raster image (PNG or JPEG).

Usage:
    python -m safepdf to-images <input> [-o OUTPUT_FOLDER] [--format {png,jpeg}] [--dpi DPI]

Arguments:
    input               Path to the input PDF file
    -o, --output        Folder to save rendered images (default: <input_stem>_rendered/)
    --format            Output image format: png or jpeg (default: png)
    --dpi               Render resolution in dots per inch (default: 150)
                        Use 300 for print-quality output.

Behaviour:
    - Pages are saved as page_001.png, page_002.png, ...
    - Higher DPI produces larger, sharper images

Examples:
    safepdf to-images presentation.pdf
    safepdf to-images presentation.pdf --dpi 300 --format jpeg -o slides/
"""

import logging
from pathlib import Path

import fitz

from safepdf.utils import atomic_output_path, validate_pdf, warn_if_nonempty

log = logging.getLogger(__name__)


def run(input_path: str, output_folder: str | None = None, fmt: str = "png", dpi: int = 150) -> bool:
    path = Path(input_path)
    if not validate_pdf(path):
        return False

    if fmt not in ("png", "jpeg"):
        log.error("Unsupported format '%s'. Choose 'png' or 'jpeg'.", fmt)
        return False

    if dpi < 72 or dpi > 600:
        log.error("DPI must be between 72 and 600, got %d.", dpi)
        return False

    out_dir = Path(output_folder) if output_folder else path.parent / f"{path.stem}_rendered"
    warn_if_nonempty(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    zoom = dpi / 72  # PyMuPDF default is 72 DPI
    mat = fitz.Matrix(zoom, zoom)

    try:
        with fitz.open(str(path)) as doc:
            total = len(doc)
            log.info("Rendering %d pages at %d DPI → '%s'", total, dpi, out_dir)

            for page_num, page in enumerate(doc, start=1):
                pix = page.get_pixmap(matrix=mat, alpha=False)
                out_path = out_dir / f"page_{page_num:03d}.{fmt}"

                with atomic_output_path(out_path) as temporary:
                    if fmt == "png":
                        pix.save(str(temporary), output="png")
                    else:
                        pix.save(str(temporary), output="jpeg", jpg_quality=85)

                log.info("Saved: %s", out_path.name)

        log.info("Done — %d images saved to '%s'.", total, out_dir)
        return True

    except Exception as e:
        log.error("Error rendering '%s': %s", path, e)
        return False


def cli_run(args) -> bool:
    return run(args.input, args.output, args.format, args.dpi)

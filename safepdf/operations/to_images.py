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

from safepdf.core import InvalidInputError, OperationResult, PdfProcessingError, SafePdfError
from safepdf.core.errors import OutputWriteError
from safepdf.core.output import save_pixmap
from safepdf.core.validation import require_pdf
from safepdf.presentation import present_operation

log = logging.getLogger(__name__)


def execute(
    input_path: Path,
    output_folder: Path | None = None,
    fmt: str = "png",
    dpi: int = 150,
) -> OperationResult:
    """Render PDF pages to images and return structured output details."""
    path = require_pdf(input_path)
    if fmt not in ("png", "jpeg"):
        raise InvalidInputError(
            f"Unsupported format '{fmt}'. Choose 'png' or 'jpeg'."
        )

    if dpi < 72 or dpi > 600:
        raise InvalidInputError(f"DPI must be between 72 and 600, got {dpi}.")

    out_dir = output_folder or path.parent / f"{path.stem}_rendered"
    warnings = []
    if out_dir.exists():
        if not out_dir.is_dir():
            raise OutputWriteError(
                f"Output path '{out_dir}' exists and is not a directory."
            )
        if any(out_dir.iterdir()):
            warnings.append(
                f"Output folder '{out_dir}' is not empty — files may be overwritten."
            )
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OutputWriteError(
            f"Could not create output folder '{out_dir}': {exc}"
        ) from exc

    zoom = dpi / 72  # PyMuPDF default is 72 DPI
    mat = fitz.Matrix(zoom, zoom)
    output_paths = []

    try:
        with fitz.open(str(path)) as doc:
            total = len(doc)

            for page_num, page in enumerate(doc, start=1):
                pix = page.get_pixmap(matrix=mat, alpha=False)
                out_path = out_dir / f"page_{page_num:03d}.{fmt}"

                if fmt == "png":
                    save_pixmap(pix, out_path, output="png")
                else:
                    save_pixmap(
                        pix,
                        out_path,
                        output="jpeg",
                        jpg_quality=85,
                    )
                output_paths.append(out_path)

    except SafePdfError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not render PDF '{path}': {exc}"
        ) from exc

    return OperationResult(
        output_paths=output_paths,
        source_paths=[path],
        processed_pages=total,
        processed_files=len(output_paths),
        warnings=warnings,
        metadata={"format": fmt, "dpi": dpi, "output_directory": out_dir},
        message=f"Rendered {total} pages at {dpi} DPI to '{out_dir}'.",
    )


def run(
    input_path: str,
    output_folder: str | None = None,
    fmt: str = "png",
    dpi: int = 150,
) -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            Path(output_folder) if output_folder else None,
            fmt,
            dpi,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            Path(args.output) if args.output else None,
            args.format,
            args.dpi,
        ),
        log,
    )

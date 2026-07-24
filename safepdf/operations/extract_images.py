"""
extract_images.py — Extract all embedded images from a PDF.

Usage:
    python -m safepdf extract-images <input> [-o OUTPUT_FOLDER] [--format {png,jpeg}]

Arguments:
    input               Path to the input PDF file
    -o, --output        Folder to save extracted images (default: <input_stem>_images/)
    --format            Output image format: png or jpeg (default: png)

Behaviour:
    - Images are saved as p<page>_img<index>.<format>
    - Duplicate images (same xref) are only extracted once
    - A warning is shown if no images are found

Examples:
    safepdf extract-images brochure.pdf
    safepdf extract-images brochure.pdf -o imgs/ --format jpeg
"""

import logging
from pathlib import Path

import fitz

from safepdf.core import InvalidInputError, OperationResult, PdfProcessingError, SafePdfError
from safepdf.core.errors import OutputWriteError
from safepdf.core.output import write_bytes
from safepdf.core.validation import require_pdf
from safepdf.presentation import present_operation

log = logging.getLogger(__name__)


def _image_bytes(
    doc: fitz.Document,
    xref: int,
    smask: int,
    fmt: str,
    warnings: list[str] | None = None,
) -> bytes:
    """Decode an embedded image and encode it in the requested format."""
    base = fitz.Pixmap(doc, xref)
    pix = base

    if smask:
        try:
            mask = fitz.Pixmap(doc, smask)
            pix = fitz.Pixmap(base, mask)
        except Exception as exc:
            if warnings is not None:
                warnings.append(
                    f"Could not apply soft mask {smask} to image {xref}: {exc}"
                )

    if fmt == "jpeg" and (pix.alpha or pix.colorspace not in (fitz.csGRAY, fitz.csRGB)):
        pix = fitz.Pixmap(fitz.csRGB, pix)

    if fmt == "jpeg":
        return pix.tobytes("jpeg", jpg_quality=95)
    return pix.tobytes("png")


def execute(
    input_path: Path,
    output_folder: Path | None = None,
    fmt: str = "png",
) -> OperationResult:
    """Extract embedded images and return structured output information."""
    path = require_pdf(input_path)
    if fmt not in ("png", "jpeg"):
        raise InvalidInputError(
            f"Unsupported format '{fmt}'. Choose 'png' or 'jpeg'."
        )

    out_dir = output_folder or path.parent / f"{path.stem}_images"
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

    seen_xrefs: set[int] = set()
    output_paths = []
    failed_images = 0

    try:
        with fitz.open(str(path)) as doc:
            page_count = doc.page_count
            for page_num, page in enumerate(doc, start=1):
                for img_index, img in enumerate(page.get_images(full=True), start=1):
                    xref = img[0]
                    smask = img[1]
                    if xref in seen_xrefs:
                        continue
                    seen_xrefs.add(xref)

                    try:
                        image_bytes = _image_bytes(
                            doc,
                            xref,
                            smask,
                            fmt,
                            warnings,
                        )
                        ext = fmt
                        out_name = f"p{page_num:03d}_img{img_index:02d}.{ext}"
                        out_path = out_dir / out_name
                        write_bytes(out_path, image_bytes)
                        output_paths.append(out_path)
                    except OutputWriteError:
                        raise
                    except Exception as exc:
                        failed_images += 1
                        warnings.append(
                            f"Could not extract image xref {xref}: {exc}"
                        )

    except SafePdfError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not extract images from '{path}': {exc}"
        ) from exc

    if not output_paths:
        warnings.append(f"No images found in '{path.name}'.")

    return OperationResult(
        output_paths=output_paths,
        source_paths=[path],
        processed_pages=page_count,
        processed_files=len(output_paths),
        skipped_files=failed_images,
        warnings=warnings,
        metadata={"format": fmt, "output_directory": out_dir},
        message=f"Extracted {len(output_paths)} image(s) to '{out_dir}'.",
    )


def run(input_path: str, output_folder: str | None = None, fmt: str = "png") -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            Path(output_folder) if output_folder else None,
            fmt,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            Path(args.output) if args.output else None,
            args.format,
        ),
        log,
    )

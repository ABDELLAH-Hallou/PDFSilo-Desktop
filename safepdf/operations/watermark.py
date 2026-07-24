"""
watermark.py — Stamp a text watermark on every page of a PDF.

Usage:
    python -m safepdf watermark <input> -t TEXT [-o OUTPUT]
                                [--opacity OPACITY] [--angle ANGLE] [--size SIZE]
                                [--color COLOR]

Arguments:
    input               Path to the input PDF file
    -t, --text          Watermark text, e.g. "CONFIDENTIAL" (required)
    -o, --output        Output file path (default: <input_stem>_watermarked.pdf)
    --opacity           Opacity 0.0–1.0 (default: 0.15)
    --angle             Rotation angle in degrees (default: 45)
    --size              Font size in points (default: 60)
    --color             Text color as R,G,B floats 0.0–1.0 (default: 0.5,0.5,0.5)

Examples:
    safepdf watermark report.pdf -t "DRAFT"
    safepdf watermark report.pdf -t "CONFIDENTIAL" --opacity 0.2 --color 1,0,0
"""

import logging
import math
from pathlib import Path

import fitz

from safepdf.core import InvalidInputError, OperationResult, PdfProcessingError, SafePdfError
from safepdf.core.output import save_document
from safepdf.core.validation import require_pdf
from safepdf.presentation import present_operation

log = logging.getLogger(__name__)


def parse_color(color_str: str) -> tuple[float, float, float]:
    parts = [float(c.strip()) for c in color_str.split(",")]
    if len(parts) != 3:
        raise ValueError("Color must be three comma-separated floats, e.g. '0.5,0.5,0.5'")
    if not all(math.isfinite(component) and 0.0 <= component <= 1.0 for component in parts):
        raise ValueError("Color components must be finite values between 0.0 and 1.0")
    return tuple(parts)


def execute(
    input_path: Path,
    text: str,
    output_path: Path | None = None,
    opacity: float = 0.15,
    angle: float = 45,
    font_size: float = 60,
    color: str = "0.5,0.5,0.5",
) -> OperationResult:
    """Apply a text watermark and return structured output information."""
    path = require_pdf(input_path)
    if not text:
        raise InvalidInputError("Watermark text cannot be empty.")
    if not math.isfinite(opacity) or not 0.0 <= opacity <= 1.0:
        raise InvalidInputError(
            "Opacity must be a finite value between 0.0 and 1.0."
        )
    if not math.isfinite(angle):
        raise InvalidInputError("Angle must be a finite number.")
    if not math.isfinite(font_size) or font_size <= 0:
        raise InvalidInputError("Font size must be a positive finite number.")

    out_path = output_path or path.parent / f"{path.stem}_watermarked.pdf"

    try:
        rgb = parse_color(color)
    except ValueError as exc:
        raise InvalidInputError(f"Invalid color: {exc}") from exc

    try:
        with fitz.open(str(path)) as doc:
            page_count = doc.page_count
            for page in doc:
                # TextWriter supports arbitrary rotation angles unlike insert_text
                tw = fitz.TextWriter(page.rect, opacity=opacity, color=rgb)
                font = fitz.Font("helv")
                pivot = fitz.Point(page.rect.width / 2, page.rect.height / 2)
                tw.append(
                    pos=pivot,
                    text=text,
                    font=font,
                    fontsize=font_size,
                )
                # Build rotation matrix around the page centre
                rad = math.radians(angle)
                cos_a, sin_a = math.cos(rad), math.sin(rad)
                rot = fitz.Matrix(cos_a, sin_a, -sin_a, cos_a, 0, 0)
                tw.write_text(page, morph=(pivot, rot), overlay=True)
            save_document(doc, out_path)
    except SafePdfError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not watermark PDF '{path}': {exc}"
        ) from exc

    return OperationResult(
        output_paths=[out_path],
        source_paths=[path],
        processed_pages=page_count,
        processed_files=1,
        metadata={
            "text": text,
            "opacity": opacity,
            "angle": angle,
            "font_size": font_size,
            "color": rgb,
        },
        message=f"Watermarked PDF saved to '{out_path}'.",
    )


def run(
    input_path: str,
    text: str,
    output_path: str | None = None,
    opacity: float = 0.15,
    angle: float = 45,
    font_size: float = 60,
    color: str = "0.5,0.5,0.5",
) -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            text,
            Path(output_path) if output_path else None,
            opacity,
            angle,
            font_size,
            color,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            args.text,
            Path(args.output) if args.output else None,
            args.opacity,
            args.angle,
            args.size,
            args.color,
        ),
        log,
    )

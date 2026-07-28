"""Release-validation workflow executed by a frozen PDFSilo application."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import pymupdf

from pdfsilo import __version__
from pdfsilo.operations import compress, decrypt, encrypt, rotate

REPORT_NAME = "pdfsilo-package-self-test.json"


def _validation_directory(root: Path) -> Path:
    segments = (
        "PDFSilo-été-文档-validation",
        "long-path-segment-01-abcdefgh",
        "long-path-segment-02-abcdefgh",
        "long-path-segment-03-abcdefgh",
        "long-path-segment-04-abcdefgh",
    )
    path = root
    for segment in segments:
        path /= segment
    return path


def _create_pdf(path: Path, page_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open() as document:
        for index in range(page_count):
            page = document.new_page()
            page.insert_text(
                (72, 96),
                f"PDFSilo packaged validation page {index + 1}",
                fontsize=16,
            )
            page.insert_text(
                (72, 130),
                "Unicode: été · résumé · 文档 · اختبار",
                fontsize=11,
            )
        document.save(path)


def run_package_self_test(root: Path, *, page_count: int = 120) -> int:
    """Exercise representative PDF operations and write a JSON report."""
    started = perf_counter()
    destination = _validation_directory(root.resolve())
    report_path = root.resolve() / REPORT_NAME
    report: dict[str, object] = {
        "success": False,
        "version": __version__,
        "page_count": page_count,
        "validation_path": str(destination),
        "validation_path_length": len(str(destination)),
    }
    try:
        source = destination / "entrée-document-volumineux.pdf"
        rotated = destination / "sortie-rotation.pdf"
        compressed = destination / "sortie-compression.pdf"
        encrypted = destination / "document-chiffré.pdf"
        decrypted = destination / "document-déchiffré.pdf"
        _create_pdf(source, page_count)

        rotate.execute(source, 90, output_path=rotated)
        compress.execute(source, compressed, quality=60)
        encrypt.execute(
            source,
            "package-test-user",
            "package-test-owner",
            encrypted,
            allow_copy=False,
        )
        decrypt.execute(encrypted, "package-test-owner", decrypted)

        for output in (rotated, compressed, encrypted, decrypted):
            if not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError(f"Expected output was not created: {output}")
        with pymupdf.open(decrypted) as document:
            if document.page_count != page_count:
                raise RuntimeError("Decrypted output page count changed.")

        report.update(
            {
                "success": True,
                "outputs": [
                    str(rotated),
                    str(compressed),
                    str(encrypted),
                    str(decrypted),
                ],
            }
        )
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        report["elapsed_seconds"] = round(perf_counter() - started, 3)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    return 0 if report["success"] else 1


__all__ = ["REPORT_NAME", "run_package_self_test"]

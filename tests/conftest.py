"""
conftest.py — Shared pytest fixtures for SafePDF tests.

All fixtures create real in-memory PDFs using PyMuPDF so that every
operation module can be exercised without needing external PDF files.
"""

import pytest
import fitz
from pathlib import Path


def _make_pdf(path: Path, num_pages: int = 1, text: str = "Test page") -> Path:
    """Create a minimal but valid PDF at *path* with num_pages pages."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=595, height=842)  # A4
        page.insert_text((72, 72), f"{text} {i + 1}", fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture()
def tmp_pdf(tmp_path: Path) -> Path:
    """A single-page PDF file."""
    return _make_pdf(tmp_path / "sample.pdf", num_pages=1)


@pytest.fixture()
def tmp_multi_pdf(tmp_path: Path) -> Path:
    """A five-page PDF file."""
    return _make_pdf(tmp_path / "multi.pdf", num_pages=5)


@pytest.fixture()
def tmp_pdf_folder(tmp_path: Path) -> Path:
    """A folder containing three numbered PDF files."""
    folder = tmp_path / "pdfs"
    folder.mkdir()
    for i in range(1, 4):
        _make_pdf(folder / f"doc_{i:03d}.pdf", num_pages=2, text=f"Page from doc {i}")
    return folder


@pytest.fixture()
def encrypted_pdf(tmp_path: Path) -> tuple[Path, str]:
    """A password-protected PDF and its password."""
    src = _make_pdf(tmp_path / "plain.pdf", num_pages=1)
    enc_path = tmp_path / "encrypted.pdf"
    password = "testpass"

    doc = fitz.open(str(src))
    doc.save(
        str(enc_path),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=password,
        owner_pw=password,
    )
    doc.close()
    return enc_path, password


@pytest.fixture()
def pdf_with_image(tmp_path: Path) -> Path:
    """A PDF that contains an embedded raster image."""
    path = tmp_path / "with_image.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    # Create a tiny 4×4 RGBA pixmap and embed it as an image
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 4, 4))
    pix.set_rect(fitz.IRect(0, 0, 4, 4), (200, 100, 50))
    page.insert_image(fitz.Rect(72, 72, 200, 200), pixmap=pix)

    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture()
def tmp_png_image(tmp_path: Path) -> Path:
    """A small 64×64 RGB PNG image created with fitz (no Pillow required)."""
    img_path = tmp_path / "test_image.png"
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 64, 64))
    pix.set_rect(fitz.IRect(0, 0, 64, 64), (100, 149, 237))  # cornflower blue
    pix.save(str(img_path))
    return img_path


@pytest.fixture()
def tmp_two_png_images(tmp_path: Path) -> list:
    """Two distinct 64×64 PNG images."""
    colors = [(220, 20, 60), (34, 139, 34)]  # crimson, forest-green
    paths: list = []
    for i, color in enumerate(colors):
        p = tmp_path / f"image_{i}.png"
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 64, 64))
        pix.set_rect(fitz.IRect(0, 0, 64, 64), color)
        pix.save(str(p))
        paths.append(p)
    return paths


@pytest.fixture()
def tmp_image_folder(tmp_path: Path) -> Path:
    """A folder with three numbered PNG images (image_001.png … image_003.png)."""
    folder = tmp_path / "images"
    folder.mkdir()
    colors = [(220, 20, 60), (34, 139, 34), (70, 130, 180)]  # crimson, forest-green, steel-blue
    for i, color in enumerate(colors, start=1):
        p = folder / f"image_{i:03d}.png"
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 64, 64))
        pix.set_rect(fitz.IRect(0, 0, 64, 64), color)
        pix.save(str(p))
    return folder


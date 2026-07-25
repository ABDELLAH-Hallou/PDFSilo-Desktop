"""tests/test_to_images.py — Unit tests for pdfsilo.operations.to_images"""

import pytest
from pathlib import Path

from pdfsilo.operations.to_images import run, cli_run


class TestToImagesRun:
    def test_renders_all_pages(self, tmp_multi_pdf: Path, tmp_path: Path):
        out_dir = tmp_path / "rendered"
        assert run(str(tmp_multi_pdf), str(out_dir)) is True
        images = list(out_dir.glob("page_*.png"))
        assert len(images) == 5

    def test_naming_convention(self, tmp_pdf: Path, tmp_path: Path):
        out_dir = tmp_path / "rendered"
        run(str(tmp_pdf), str(out_dir))
        assert (out_dir / "page_001.png").exists()

    def test_jpeg_format(self, tmp_pdf: Path, tmp_path: Path):
        out_dir = tmp_path / "rendered"
        assert run(str(tmp_pdf), str(out_dir), fmt="jpeg") is True
        assert (out_dir / "page_001.jpeg").exists()

    def test_invalid_format(self, tmp_pdf: Path, tmp_path: Path):
        assert run(str(tmp_pdf), str(tmp_path / "out"), fmt="bmp") is False

    def test_dpi_too_low(self, tmp_pdf: Path, tmp_path: Path):
        assert run(str(tmp_pdf), str(tmp_path / "out"), dpi=10) is False

    def test_dpi_too_high(self, tmp_pdf: Path, tmp_path: Path):
        assert run(str(tmp_pdf), str(tmp_path / "out"), dpi=700) is False

    def test_300_dpi(self, tmp_pdf: Path, tmp_path: Path):
        out_dir = tmp_path / "hires"
        assert run(str(tmp_pdf), str(out_dir), dpi=300) is True

    def test_default_output_folder(self, tmp_pdf: Path):
        assert run(str(tmp_pdf)) is True
        expected = tmp_pdf.parent / f"{tmp_pdf.stem}_rendered"
        assert expected.is_dir()

    def test_nonexistent_input(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost.pdf")) is False


class TestToImagesCliRun:
    def test_cli_run_delegates(self, tmp_pdf: Path, tmp_path: Path):
        class Args:
            input = str(tmp_pdf)
            output = str(tmp_path / "cli_rendered")
            format = "png"
            dpi = 150

        assert cli_run(Args()) is True

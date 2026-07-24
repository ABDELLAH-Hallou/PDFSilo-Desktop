"""tests/test_watermark.py — Unit tests for safepdf.operations.watermark"""

import pytest
from pathlib import Path

import fitz

from safepdf.operations.watermark import run, cli_run, parse_color


class TestParseColor:
    def test_valid_color(self):
        assert parse_color("1.0,0.5,0.0") == pytest.approx((1.0, 0.5, 0.0))

    def test_integer_components(self):
        assert parse_color("1,0,0") == pytest.approx((1.0, 0.0, 0.0))

    def test_wrong_component_count(self):
        with pytest.raises(ValueError):
            parse_color("0.5,0.5")


class TestWatermarkRun:
    def test_creates_output(self, tmp_pdf: Path, tmp_path: Path):
        out = tmp_path / "wm.pdf"
        assert run(str(tmp_pdf), "DRAFT", output_path=str(out)) is True
        assert out.exists()

    def test_default_output_name(self, tmp_pdf: Path):
        assert run(str(tmp_pdf), "TEST") is True
        expected = tmp_pdf.parent / f"{tmp_pdf.stem}_watermarked.pdf"
        assert expected.exists()

    def test_invalid_color_returns_false(self, tmp_pdf: Path, tmp_path: Path):
        out = tmp_path / "out.pdf"
        assert run(str(tmp_pdf), "X", output_path=str(out), color="red,green") is False

    def test_output_page_count_unchanged(self, tmp_multi_pdf: Path, tmp_path: Path):
        out = tmp_path / "wm.pdf"
        run(str(tmp_multi_pdf), "CONFIDENTIAL", output_path=str(out))
        doc = fitz.open(str(out))
        assert doc.page_count == 5
        doc.close()

    def test_nonexistent_input(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost.pdf"), "X") is False

    def test_custom_opacity_and_angle(self, tmp_pdf: Path, tmp_path: Path):
        out = tmp_path / "wm.pdf"
        assert run(str(tmp_pdf), "SAMPLE", output_path=str(out),
                   opacity=0.5, angle=30, font_size=40) is True


class TestWatermarkCliRun:
    def test_cli_run_delegates(self, tmp_pdf: Path, tmp_path: Path):
        class Args:
            input = str(tmp_pdf)
            text = "CLI WATERMARK"
            output = str(tmp_path / "cli_wm.pdf")
            opacity = 0.15
            angle = 45
            size = 60
            color = "0.5,0.5,0.5"

        assert cli_run(Args()) is True

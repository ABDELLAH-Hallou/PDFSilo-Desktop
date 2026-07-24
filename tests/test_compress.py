"""tests/test_compress.py — Unit tests for safepdf.operations.compress"""

import pytest
from pathlib import Path

import fitz

from safepdf.operations.compress import run, cli_run


class TestCompressRun:
    def test_compresses_successfully(self, tmp_pdf: Path, tmp_path: Path):
        out = tmp_path / "out.pdf"
        assert run(str(tmp_pdf), str(out)) is True
        assert out.exists()
        assert out.stat().st_size > 0

    def test_default_output_name(self, tmp_pdf: Path):
        assert run(str(tmp_pdf)) is True
        expected = tmp_pdf.parent / f"{tmp_pdf.stem}_compressed.pdf"
        assert expected.exists()

    def test_invalid_quality_low(self, tmp_pdf: Path):
        assert run(str(tmp_pdf), quality=0) is False

    def test_invalid_quality_high(self, tmp_pdf: Path):
        assert run(str(tmp_pdf), quality=101) is False

    def test_nonexistent_input(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost.pdf")) is False

    def test_non_pdf_extension(self, tmp_path: Path):
        bad = tmp_path / "file.txt"
        bad.write_text("not a pdf")
        assert run(str(bad)) is False

    def test_output_is_valid_pdf(self, tmp_pdf: Path, tmp_path: Path):
        out = tmp_path / "out.pdf"
        run(str(tmp_pdf), str(out))
        doc = fitz.open(str(out))
        assert len(doc) >= 1
        doc.close()


class TestCompressCliRun:
    def test_cli_run_delegates(self, tmp_pdf: Path, tmp_path: Path):
        class Args:
            input = str(tmp_pdf)
            output = str(tmp_path / "cli_out.pdf")
            quality = 70
        assert cli_run(Args()) is True

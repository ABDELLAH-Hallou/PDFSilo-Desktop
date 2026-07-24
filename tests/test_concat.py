"""tests/test_concat.py — Unit tests for safepdf.operations.concat"""

import pytest
from pathlib import Path

import fitz

from safepdf.operations.concat import run, cli_run


class TestConcatRun:
    def test_merges_multiple_pdfs(self, tmp_pdf_folder: Path, tmp_path: Path):
        files = [str(f) for f in sorted(tmp_pdf_folder.glob("*.pdf"))]
        out = tmp_path / "merged.pdf"
        assert run(files, str(out)) is True
        assert out.exists()

    def test_page_count(self, tmp_pdf_folder: Path, tmp_path: Path):
        """3 files × 2 pages each → 6 output pages."""
        files = [str(f) for f in sorted(tmp_pdf_folder.glob("*.pdf"))]
        out = tmp_path / "merged.pdf"
        run(files, str(out))
        doc = fitz.open(str(out))
        assert doc.page_count == 6
        doc.close()

    def test_output_page_size_a4(self, tmp_pdf_folder: Path, tmp_path: Path):
        files = [str(f) for f in sorted(tmp_pdf_folder.glob("*.pdf"))]
        out = tmp_path / "merged.pdf"
        run(files, str(out), target_size="A4")
        doc = fitz.open(str(out))
        page = doc[0]
        assert pytest.approx(page.rect.width, abs=1) == 595
        assert pytest.approx(page.rect.height, abs=1) == 842
        doc.close()

    def test_output_page_size_letter(self, tmp_pdf_folder: Path, tmp_path: Path):
        files = [str(f) for f in sorted(tmp_pdf_folder.glob("*.pdf"))]
        out = tmp_path / "merged.pdf"
        run(files, str(out), target_size="Letter")
        doc = fitz.open(str(out))
        page = doc[0]
        assert pytest.approx(page.rect.width, abs=1) == 612
        assert pytest.approx(page.rect.height, abs=1) == 792
        doc.close()

    def test_invalid_page_size(self, tmp_pdf_folder: Path, tmp_path: Path):
        files = [str(f) for f in sorted(tmp_pdf_folder.glob("*.pdf"))]
        with pytest.raises(ValueError, match="Unsupported page size"):
            run(files, str(tmp_path / "out.pdf"), target_size="A3")

    def test_empty_file_list(self, tmp_path: Path):
        """Empty list → no pages → returns False."""
        out = tmp_path / "out.pdf"
        assert run([], str(out)) is False
        assert not out.exists()

    def test_skips_invalid_pdf(self, tmp_path: Path):
        bad = tmp_path / "bad.pdf"
        bad.write_text("not a pdf")
        out = tmp_path / "out.pdf"
        # Single bad file should produce no pages → False
        assert run([str(bad)], str(out)) is False


class TestConcatCliRun:
    def test_cli_run_delegates(self, tmp_pdf_folder: Path, tmp_path: Path):
        class Args:
            folder = str(tmp_pdf_folder)
            output = str(tmp_path / "cli_merged.pdf")
            size = "A4"

        assert cli_run(Args()) is True

    def test_cli_run_empty_folder(self, tmp_path: Path):
        empty = tmp_path / "empty"
        empty.mkdir()

        class Args:
            folder = str(empty)
            output = str(tmp_path / "out.pdf")
            size = "A4"

        assert cli_run(Args()) is False

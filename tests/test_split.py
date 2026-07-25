"""tests/test_split.py — Unit tests for pdfsilo.operations.split"""

import pytest
from pathlib import Path

import fitz

from pdfsilo.operations.split import run, cli_run


class TestSplitRun:
    def test_creates_one_file_per_page(self, tmp_multi_pdf: Path, tmp_path: Path):
        out_dir = tmp_path / "pages"
        assert run(str(tmp_multi_pdf), str(out_dir)) is True
        pages = list(out_dir.glob("page_*.pdf"))
        assert len(pages) == 5

    def test_files_named_correctly(self, tmp_multi_pdf: Path, tmp_path: Path):
        out_dir = tmp_path / "pages"
        run(str(tmp_multi_pdf), str(out_dir))
        names = sorted(p.name for p in out_dir.glob("*.pdf"))
        assert names[0] == "page_001.pdf"
        assert names[-1] == "page_005.pdf"

    def test_each_file_is_single_page(self, tmp_multi_pdf: Path, tmp_path: Path):
        out_dir = tmp_path / "pages"
        run(str(tmp_multi_pdf), str(out_dir))
        for pdf_file in out_dir.glob("*.pdf"):
            doc = fitz.open(str(pdf_file))
            assert doc.page_count == 1
            doc.close()

    def test_default_output_folder_name(self, tmp_multi_pdf: Path):
        assert run(str(tmp_multi_pdf)) is True
        expected = tmp_multi_pdf.parent / f"{tmp_multi_pdf.stem}_pages"
        assert expected.is_dir()

    def test_nonexistent_input(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost.pdf")) is False

    def test_non_pdf_extension(self, tmp_path: Path):
        bad = tmp_path / "file.txt"
        bad.write_text("data")
        assert run(str(bad)) is False


class TestSplitCliRun:
    def test_cli_run_delegates(self, tmp_multi_pdf: Path, tmp_path: Path):
        class Args:
            input = str(tmp_multi_pdf)
            output = str(tmp_path / "cli_pages")

        assert cli_run(Args()) is True

"""tests/test_extract_range.py — Unit tests for pdfsilo.operations.extract_range"""

from pathlib import Path

import fitz

from pdfsilo.operations.extract_range import cli_run, run


class TestExtractRangeRun:
    def test_extracts_correct_pages(self, tmp_multi_pdf: Path, tmp_path: Path):
        out = tmp_path / "range.pdf"
        assert run(str(tmp_multi_pdf), 2, 4, str(out)) is True
        doc = fitz.open(str(out))
        assert doc.page_count == 3
        doc.close()

    def test_single_page_extraction(self, tmp_multi_pdf: Path, tmp_path: Path):
        out = tmp_path / "single.pdf"
        assert run(str(tmp_multi_pdf), 3, 3, str(out)) is True
        doc = fitz.open(str(out))
        assert doc.page_count == 1
        doc.close()

    def test_full_range(self, tmp_multi_pdf: Path, tmp_path: Path):
        out = tmp_path / "full.pdf"
        assert run(str(tmp_multi_pdf), 1, 5, str(out)) is True

    def test_default_output_name(self, tmp_multi_pdf: Path):
        assert run(str(tmp_multi_pdf), 1, 3) is True
        expected = tmp_multi_pdf.parent / f"{tmp_multi_pdf.stem}_p1-p3.pdf"
        assert expected.exists()

    def test_start_before_1(self, tmp_multi_pdf: Path, tmp_path: Path):
        assert run(str(tmp_multi_pdf), 0, 3, str(tmp_path / "out.pdf")) is False

    def test_end_beyond_total(self, tmp_multi_pdf: Path, tmp_path: Path):
        assert run(str(tmp_multi_pdf), 1, 99, str(tmp_path / "out.pdf")) is False

    def test_start_greater_than_end(self, tmp_multi_pdf: Path, tmp_path: Path):
        assert run(str(tmp_multi_pdf), 4, 2, str(tmp_path / "out.pdf")) is False

    def test_nonexistent_input(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost.pdf"), 1, 2) is False


class TestExtractRangeCliRun:
    def test_cli_run_delegates(self, tmp_multi_pdf: Path, tmp_path: Path):
        class Args:
            input = str(tmp_multi_pdf)
            start = 1
            end = 3
            output = str(tmp_path / "cli_range.pdf")

        assert cli_run(Args()) is True

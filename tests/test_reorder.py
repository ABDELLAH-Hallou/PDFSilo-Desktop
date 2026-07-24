"""tests/test_reorder.py — Unit tests for safepdf.operations.reorder"""

import pytest
from pathlib import Path

import fitz

from safepdf.operations.reorder import run, cli_run, parse_order


class TestParseOrder:
    def test_valid_order(self):
        assert parse_order("3,1,2", 3) == [2, 0, 1]

    def test_out_of_range(self):
        assert parse_order("1,6", 5) is None

    def test_invalid_token(self):
        assert parse_order("1,abc", 5) is None

    def test_duplicate_pages_allowed(self):
        assert parse_order("1,1,2", 3) == [0, 0, 1]


class TestReorderRun:
    def test_reorders_pages(self, tmp_multi_pdf: Path, tmp_path: Path):
        out = tmp_path / "reordered.pdf"
        assert run(str(tmp_multi_pdf), "5,4,3,2,1", str(out)) is True
        doc = fitz.open(str(out))
        assert doc.page_count == 5
        doc.close()

    def test_can_reduce_pages(self, tmp_multi_pdf: Path, tmp_path: Path):
        """Omitting pages from the order effectively deletes them."""
        out = tmp_path / "reduced.pdf"
        run(str(tmp_multi_pdf), "1,3", str(out))
        doc = fitz.open(str(out))
        assert doc.page_count == 2
        doc.close()

    def test_can_duplicate_pages(self, tmp_multi_pdf: Path, tmp_path: Path):
        out = tmp_path / "dup.pdf"
        run(str(tmp_multi_pdf), "1,1,1", str(out))
        doc = fitz.open(str(out))
        assert doc.page_count == 3
        doc.close()

    def test_default_output_name(self, tmp_multi_pdf: Path):
        assert run(str(tmp_multi_pdf), "1,2,3,4,5") is True
        expected = tmp_multi_pdf.parent / f"{tmp_multi_pdf.stem}_reordered.pdf"
        assert expected.exists()

    def test_invalid_order_returns_false(self, tmp_multi_pdf: Path, tmp_path: Path):
        assert run(str(tmp_multi_pdf), "0,1", str(tmp_path / "out.pdf")) is False

    def test_nonexistent_input(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost.pdf"), "1,2") is False


class TestReorderCliRun:
    def test_cli_run_delegates(self, tmp_multi_pdf: Path, tmp_path: Path):
        class Args:
            input = str(tmp_multi_pdf)
            order = "2,1,3,4,5"
            output = str(tmp_path / "cli_reorder.pdf")

        assert cli_run(Args()) is True

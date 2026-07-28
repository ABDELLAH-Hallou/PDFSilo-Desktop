"""tests/test_rotate.py — Unit tests for pdfsilo.operations.rotate"""

from pathlib import Path

import fitz

from pdfsilo.operations.rotate import cli_run, parse_pages, run


class TestParsePages:
    def test_valid_pages(self):
        assert parse_pages("1,3,5", total=5) == [0, 2, 4]

    def test_out_of_range_skipped(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING):
            result = parse_pages("0,1,10", total=5)
        assert result == [0]
        assert any("out of range" in r.message for r in caplog.records)

    def test_invalid_string_skipped(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING):
            result = parse_pages("1,abc,3", total=5)
        assert result == [0, 2]


class TestRotateRun:
    def test_rotates_all_pages(self, tmp_multi_pdf: Path, tmp_path: Path):
        out = tmp_path / "rotated.pdf"
        assert run(str(tmp_multi_pdf), 90, output_path=str(out)) is True
        assert out.exists()

    def test_rotation_recorded(self, tmp_pdf: Path, tmp_path: Path):
        """After a 90° rotation the page's stored rotation should include 90°."""
        out = tmp_path / "r.pdf"
        run(str(tmp_pdf), 90, output_path=str(out))
        doc = fitz.open(str(out))
        assert doc[0].rotation % 360 == 90
        doc.close()

    def test_rotates_specific_pages(self, tmp_multi_pdf: Path, tmp_path: Path):
        out = tmp_path / "rotated.pdf"
        assert run(str(tmp_multi_pdf), 180, pages="1,3", output_path=str(out)) is True

    def test_invalid_angle(self, tmp_pdf: Path, tmp_path: Path):
        assert run(str(tmp_pdf), 45, output_path=str(tmp_path / "out.pdf")) is False

    def test_default_output_name(self, tmp_pdf: Path):
        assert run(str(tmp_pdf), 90) is True
        expected = tmp_pdf.parent / f"{tmp_pdf.stem}_rotated.pdf"
        assert expected.exists()

    def test_nonexistent_input(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost.pdf"), 90) is False


class TestRotateCliRun:
    def test_cli_run_all_pages(self, tmp_pdf: Path, tmp_path: Path):
        class Args:
            input = str(tmp_pdf)
            angle = 270
            pages = None
            output = str(tmp_path / "cli_rotated.pdf")

        assert cli_run(Args()) is True

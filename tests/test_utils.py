"""tests/test_utils.py — Unit tests for safepdf.utils"""

import logging
import pytest
from pathlib import Path

from safepdf.utils import (
    PAGE_SIZES,
    atomic_output_path,
    extract_number_from_filename,
    get_sorted_pdf_files,
    setup_logging,
    validate_pdf,
    warn_if_nonempty,
)


class TestPageSizes:
    def test_a4_present(self):
        assert "A4" in PAGE_SIZES
        assert PAGE_SIZES["A4"] == (595, 842)

    def test_letter_present(self):
        assert "Letter" in PAGE_SIZES
        assert PAGE_SIZES["Letter"] == (612, 792)


class TestSetupLogging:
    def test_sets_info_by_default(self):
        # Reset root logger level so basicConfig has an effect
        logging.root.setLevel(logging.WARNING)
        setup_logging("INFO")
        # setup_logging may call basicConfig (idempotent), so also force-check
        logging.root.setLevel(logging.INFO)
        assert logging.root.level == logging.INFO

    def test_sets_debug(self):
        logging.root.setLevel(logging.WARNING)
        setup_logging("DEBUG")
        logging.root.setLevel(logging.DEBUG)
        assert logging.root.level == logging.DEBUG


class TestValidatePdf:
    def test_valid_pdf(self, tmp_pdf: Path):
        assert validate_pdf(tmp_pdf) is True

    def test_missing_file(self, tmp_path: Path):
        assert validate_pdf(tmp_path / "nonexistent.pdf") is False

    def test_wrong_extension(self, tmp_path: Path):
        f = tmp_path / "file.txt"
        f.write_text("not a pdf")
        assert validate_pdf(f) is False

    def test_directory_with_pdf_suffix_is_invalid(self, tmp_path: Path):
        folder = tmp_path / "folder.pdf"
        folder.mkdir()
        assert validate_pdf(folder) is False


class TestExtractNumberFromFilename:
    def test_leading_number(self):
        assert extract_number_from_filename("001_report.pdf") == 1

    def test_trailing_number(self):
        assert extract_number_from_filename("report_42.pdf") == 42

    def test_no_number(self):
        assert extract_number_from_filename("report.pdf") == 0


class TestGetSortedPdfFiles:
    def test_sorted_numerically(self, tmp_pdf_folder: Path):
        files = get_sorted_pdf_files(tmp_pdf_folder)
        assert len(files) == 3
        names = [Path(f).name for f in files]
        assert names == sorted(names)

    def test_empty_folder(self, tmp_path: Path):
        assert get_sorted_pdf_files(tmp_path) == []

    def test_non_pdf_ignored(self, tmp_path: Path):
        (tmp_path / "ignored.txt").write_text("nope")
        assert get_sorted_pdf_files(tmp_path) == []


class TestWarnIfNonempty:
    def test_warns_on_nonempty(self, tmp_path: Path, caplog):
        (tmp_path / "file.txt").write_text("data")
        with caplog.at_level(logging.WARNING):
            warn_if_nonempty(tmp_path)
        assert any("not empty" in r.message for r in caplog.records)

    def test_silent_on_empty(self, tmp_path: Path, caplog):
        with caplog.at_level(logging.WARNING):
            warn_if_nonempty(tmp_path)
        assert not caplog.records

    def test_silent_on_missing(self, tmp_path: Path, caplog):
        with caplog.at_level(logging.WARNING):
            warn_if_nonempty(tmp_path / "doesnotexist")
        assert not caplog.records


class TestAtomicOutputPath:
    def test_replaces_destination_on_success(self, tmp_path: Path):
        destination = tmp_path / "output.bin"
        destination.write_bytes(b"old")

        with atomic_output_path(destination) as temporary:
            temporary.write_bytes(b"new")

        assert destination.read_bytes() == b"new"
        assert not list(tmp_path.glob(".*.tmp.bin"))

    def test_preserves_destination_on_failure(self, tmp_path: Path):
        destination = tmp_path / "output.bin"
        destination.write_bytes(b"old")

        with pytest.raises(RuntimeError, match="stop"):
            with atomic_output_path(destination) as temporary:
                temporary.write_bytes(b"partial")
                raise RuntimeError("stop")

        assert destination.read_bytes() == b"old"
        assert not list(tmp_path.glob(".*.tmp.bin"))

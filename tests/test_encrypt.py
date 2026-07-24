"""tests/test_encrypt.py — Unit tests for safepdf.operations.encrypt"""

import pytest
from pathlib import Path

import fitz

from safepdf.operations.encrypt import run, cli_run


class TestEncryptRun:
    def test_creates_encrypted_pdf(self, tmp_pdf: Path, tmp_path: Path):
        out = tmp_path / "enc.pdf"
        assert run(str(tmp_pdf), "secret", output_path=str(out)) is True
        assert out.exists()

    def test_output_is_encrypted(self, tmp_pdf: Path, tmp_path: Path):
        out = tmp_path / "enc.pdf"
        run(str(tmp_pdf), "secret", output_path=str(out))
        doc = fitz.open(str(out))
        assert doc.is_encrypted
        doc.close()

    def test_correct_password_opens(self, tmp_pdf: Path, tmp_path: Path):
        out = tmp_path / "enc.pdf"
        run(str(tmp_pdf), "mypass", output_path=str(out))
        doc = fitz.open(str(out))
        result = doc.authenticate("mypass")
        assert result != 0
        doc.close()

    def test_wrong_password_fails(self, tmp_pdf: Path, tmp_path: Path):
        out = tmp_path / "enc.pdf"
        run(str(tmp_pdf), "mypass", output_path=str(out))
        doc = fitz.open(str(out))
        result = doc.authenticate("wrongpass")
        assert result == 0
        doc.close()

    def test_default_output_name(self, tmp_pdf: Path):
        assert run(str(tmp_pdf), "pw") is True
        expected = tmp_pdf.parent / f"{tmp_pdf.stem}_encrypted.pdf"
        assert expected.exists()

    def test_nonexistent_input(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost.pdf"), "pw") is False

    def test_non_pdf_extension(self, tmp_path: Path):
        bad = tmp_path / "file.txt"
        bad.write_text("data")
        assert run(str(bad), "pw") is False


class TestEncryptCliRun:
    def test_cli_run_delegates(self, tmp_pdf: Path, tmp_path: Path):
        class Args:
            input = str(tmp_pdf)
            password = "clitest"
            owner_password = None
            output = str(tmp_path / "cli_enc.pdf")
            no_print = False
            no_copy = False
            no_edit = False

        assert cli_run(Args()) is True

    def test_cli_no_copy_flag(self, tmp_pdf: Path, tmp_path: Path):
        class Args:
            input = str(tmp_pdf)
            password = "pw"
            owner_password = None
            output = str(tmp_path / "no_copy.pdf")
            no_print = False
            no_copy = True
            no_edit = False

        assert cli_run(Args()) is True

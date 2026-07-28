"""tests/test_decrypt.py — Unit tests for pdfsilo.operations.decrypt"""

from pathlib import Path

import fitz

from pdfsilo.operations.decrypt import cli_run, run


class TestDecryptRun:
    def test_decrypts_successfully(
        self, encrypted_pdf: tuple[Path, str], tmp_path: Path
    ):
        enc_path, pw = encrypted_pdf
        out = tmp_path / "decrypted.pdf"
        assert run(str(enc_path), pw, str(out)) is True
        assert out.exists()

    def test_output_is_not_encrypted(
        self, encrypted_pdf: tuple[Path, str], tmp_path: Path
    ):
        enc_path, pw = encrypted_pdf
        out = tmp_path / "decrypted.pdf"
        run(str(enc_path), pw, str(out))
        doc = fitz.open(str(out))
        assert not doc.is_encrypted
        doc.close()

    def test_wrong_password_returns_false(
        self, encrypted_pdf: tuple[Path, str], tmp_path: Path
    ):
        enc_path, _ = encrypted_pdf
        out = tmp_path / "out.pdf"
        assert run(str(enc_path), "wrongpassword", str(out)) is False

    def test_default_output_name(self, encrypted_pdf: tuple[Path, str]):
        enc_path, pw = encrypted_pdf
        assert run(str(enc_path), pw) is True
        expected = enc_path.parent / f"{enc_path.stem}_decrypted.pdf"
        assert expected.exists()

    def test_unencrypted_pdf_passthrough(self, tmp_pdf: Path, tmp_path: Path):
        """An already-unencrypted PDF should pass through and be saved."""
        out = tmp_path / "copy.pdf"
        assert run(str(tmp_pdf), "anypassword", str(out)) is True
        assert out.exists()

    def test_nonexistent_input(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost.pdf"), "pw") is False


class TestDecryptCliRun:
    def test_cli_run_delegates(self, encrypted_pdf: tuple[Path, str], tmp_path: Path):
        enc_path, pw = encrypted_pdf

        class Args:
            input = str(enc_path)
            password = pw
            output = str(tmp_path / "cli_dec.pdf")

        assert cli_run(Args()) is True

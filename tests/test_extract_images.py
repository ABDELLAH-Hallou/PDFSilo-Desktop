"""tests/test_extract_images.py — Unit tests for pdfsilo.operations.extract_images"""

from pathlib import Path

from pdfsilo.operations.extract_images import cli_run, run


class TestExtractImagesRun:
    def test_extracts_images(self, pdf_with_image: Path, tmp_path: Path):
        out_dir = tmp_path / "imgs"
        assert run(str(pdf_with_image), str(out_dir)) is True
        images = list(out_dir.glob("*.png"))
        assert len(images) >= 1
        assert images[0].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    def test_default_output_folder(self, pdf_with_image: Path):
        assert run(str(pdf_with_image)) is True
        expected = pdf_with_image.parent / f"{pdf_with_image.stem}_images"
        assert expected.is_dir()

    def test_jpeg_format(self, pdf_with_image: Path, tmp_path: Path):
        out_dir = tmp_path / "imgs"
        assert run(str(pdf_with_image), str(out_dir), fmt="jpeg") is True
        images = list(out_dir.glob("*.jpeg"))
        assert images
        data = images[0].read_bytes()
        assert data.startswith(b"\xff\xd8")
        assert data.endswith(b"\xff\xd9")

    def test_invalid_format(self, pdf_with_image: Path, tmp_path: Path):
        out_dir = tmp_path / "imgs"
        assert run(str(pdf_with_image), str(out_dir), fmt="bmp") is False

    def test_pdf_without_images_returns_true(self, tmp_pdf: Path, tmp_path: Path):
        """run() should still return True even if no images are found (just warns)."""
        out_dir = tmp_path / "no_imgs"
        assert run(str(tmp_pdf), str(out_dir)) is True

    def test_nonexistent_input(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost.pdf"), str(tmp_path / "out")) is False


class TestExtractImagesCliRun:
    def test_cli_run_delegates(self, pdf_with_image: Path, tmp_path: Path):
        class Args:
            input = str(pdf_with_image)
            output = str(tmp_path / "cli_imgs")
            format = "png"

        assert cli_run(Args()) is True

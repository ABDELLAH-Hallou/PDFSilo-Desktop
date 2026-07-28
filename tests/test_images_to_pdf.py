"""tests/test_images_to_pdf.py — Unit tests for pdfsilo.operations.images_to_pdf"""

from pathlib import Path

import fitz
import pytest

from pdfsilo.operations.images_to_pdf import cli_run, execute, run
from pdfsilo.utils import IMAGE_EXTENSIONS, get_sorted_image_files

# ── get_sorted_image_files (utility) ─────────────────────────────────────────


class TestGetSortedImageFiles:
    def test_returns_sorted_by_number(self, tmp_image_folder: Path):
        files = get_sorted_image_files(tmp_image_folder)
        names = [Path(f).name for f in files]
        assert names == ["image_001.png", "image_002.png", "image_003.png"]

    def test_ignores_non_image_files(self, tmp_image_folder: Path):
        (tmp_image_folder / "readme.txt").write_text("ignore me")
        (tmp_image_folder / "data.csv").write_text("ignore me too")
        files = get_sorted_image_files(tmp_image_folder)
        assert all(Path(f).suffix.lower() in IMAGE_EXTENSIONS for f in files)
        assert len(files) == 3

    def test_empty_folder_returns_empty_list(self, tmp_path: Path):
        empty = tmp_path / "empty"
        empty.mkdir()
        assert get_sorted_image_files(empty) == []

    def test_alphabetical_fallback_no_numbers(self, tmp_path: Path):
        """Files without numbers should be sorted lexicographically."""
        folder = tmp_path / "alpha"
        folder.mkdir()
        for name in ["zebra.png", "apple.png", "mango.png"]:
            p = folder / name
            pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 4, 4))
            pix.set_rect(fitz.IRect(0, 0, 4, 4), (0, 0, 0))
            pix.save(str(p))
        names = [Path(f).name for f in get_sorted_image_files(folder)]
        assert names == ["apple.png", "mango.png", "zebra.png"]


# ── run — happy paths ─────────────────────────────────────────────────────────


class TestImagesToPdfRun:
    def test_creates_output_file(self, tmp_image_folder: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        assert run(str(tmp_image_folder), output_path=str(out)) is True
        assert out.exists()

    def test_page_count_equals_image_count(
        self, tmp_image_folder: Path, tmp_path: Path
    ):
        """3 images → 3 pages in the output PDF."""
        out = tmp_path / "result.pdf"
        run(str(tmp_image_folder), output_path=str(out))
        with fitz.open(str(out)) as doc:
            assert doc.page_count == 3

    def test_default_output_name(self, tmp_image_folder: Path):
        """Default output is placed next to the folder, named after the folder."""
        assert run(str(tmp_image_folder)) is True
        expected = tmp_image_folder.parent / f"{tmp_image_folder.name}.pdf"
        assert expected.exists()

    def test_page_size_a4(self, tmp_image_folder: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        run(str(tmp_image_folder), output_path=str(out), target_size="A4")
        with fitz.open(str(out)) as doc:
            page = doc[0]
            # Portrait 64×64 images on A4 → portrait page (595 × 842)
            assert pytest.approx(page.rect.width, abs=1) == 595
            assert pytest.approx(page.rect.height, abs=1) == 842

    def test_page_size_letter(self, tmp_image_folder: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        run(str(tmp_image_folder), output_path=str(out), target_size="Letter")
        with fitz.open(str(out)) as doc:
            page = doc[0]
            assert pytest.approx(page.rect.width, abs=1) == 612
            assert pytest.approx(page.rect.height, abs=1) == 792

    def test_fit_true_default(self, tmp_image_folder: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        assert run(str(tmp_image_folder), output_path=str(out), fit=True) is True

    def test_fit_false(self, tmp_image_folder: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        assert run(str(tmp_image_folder), output_path=str(out), fit=False) is True

    def test_custom_margin(self, tmp_image_folder: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        assert run(str(tmp_image_folder), output_path=str(out), margin=72.0) is True

    def test_landscape_image_gets_landscape_page(self, tmp_path: Path):
        """A wide image (128×32) should produce a landscape page."""
        folder = tmp_path / "landscape"
        folder.mkdir()
        p = folder / "wide_001.png"
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 128, 32))
        pix.set_rect(fitz.IRect(0, 0, 128, 32), (255, 200, 0))
        pix.save(str(p))

        out = tmp_path / "result.pdf"
        assert run(str(folder), output_path=str(out)) is True
        with fitz.open(str(out)) as doc:
            page = doc[0]
            # Landscape: width > height
            assert page.rect.width > page.rect.height

    def test_explicit_image_order_is_preserved(
        self,
        tmp_image_folder: Path,
        tmp_path: Path,
    ):
        images = sorted(tmp_image_folder.glob("*.png"), reverse=True)
        out = tmp_path / "ordered.pdf"

        result = execute(None, out, image_paths=images)

        assert result.source_paths == images
        assert result.processed_pages == len(images)
        assert out.is_file()


# ── run — error / edge cases ──────────────────────────────────────────────────


class TestImagesToPdfRunErrors:
    def test_nonexistent_folder_returns_false(self, tmp_path: Path):
        assert run(str(tmp_path / "ghost_folder")) is False

    def test_file_path_instead_of_folder_returns_false(self, tmp_png_image: Path):
        """Passing a file path (not a directory) must return False."""
        assert run(str(tmp_png_image)) is False

    def test_empty_folder_returns_false(self, tmp_path: Path):
        empty = tmp_path / "empty"
        empty.mkdir()
        assert run(str(empty)) is False

    def test_folder_with_only_non_images_returns_false(self, tmp_path: Path):
        folder = tmp_path / "docs"
        folder.mkdir()
        (folder / "notes.txt").write_text("not an image")
        (folder / "data.pdf").write_bytes(b"%PDF-1.4")
        assert run(str(folder)) is False

    def test_invalid_page_size_raises(self, tmp_image_folder: Path, tmp_path: Path):
        with pytest.raises(ValueError, match="Unsupported page size"):
            run(
                str(tmp_image_folder),
                output_path=str(tmp_path / "out.pdf"),
                target_size="A3",
            )

    @pytest.mark.parametrize("margin", [-1, float("nan"), float("inf")])
    def test_invalid_margin_returns_false(
        self, tmp_image_folder: Path, tmp_path: Path, margin: float
    ):
        assert (
            run(
                str(tmp_image_folder),
                output_path=str(tmp_path / "out.pdf"),
                margin=margin,
            )
            is False
        )

    def test_margin_must_leave_drawable_area(
        self, tmp_image_folder: Path, tmp_path: Path
    ):
        assert (
            run(
                str(tmp_image_folder),
                output_path=str(tmp_path / "out.pdf"),
                margin=298,
            )
            is False
        )


# ── cli_run ───────────────────────────────────────────────────────────────────


class TestImagesToPdfCliRun:
    def test_cli_delegates_correctly(self, tmp_image_folder: Path, tmp_path: Path):
        class Args:
            folder = str(tmp_image_folder)
            output = str(tmp_path / "cli_result.pdf")
            size = "A4"
            fit = True
            margin = 36.0

        assert cli_run(Args()) is True
        assert Path(Args.output).exists()

    def test_cli_no_fit(self, tmp_image_folder: Path, tmp_path: Path):
        class Args:
            folder = str(tmp_image_folder)
            output = str(tmp_path / "no_fit.pdf")
            size = "A4"
            fit = False
            margin = 36.0

        assert cli_run(Args()) is True

    def test_cli_empty_folder(self, tmp_path: Path):
        empty = tmp_path / "empty"
        empty.mkdir()

        class Args:
            folder = str(empty)
            output = str(tmp_path / "out.pdf")
            size = "A4"
            fit = True
            margin = 36.0

        assert cli_run(Args()) is False

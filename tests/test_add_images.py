"""tests/test_add_images.py — Unit tests for pdfsilo.operations.add_images"""

import pytest
from pathlib import Path

import fitz

from pdfsilo.operations.add_images import run, cli_run, _parse_position, SUPPORTED_EXTENSIONS


# ── _parse_position ───────────────────────────────────────────────────────────

class TestParsePosition:
    def test_valid_position(self):
        assert _parse_position("72,100") == pytest.approx((72.0, 100.0))

    def test_float_values(self):
        assert _parse_position("10.5,20.75") == pytest.approx((10.5, 20.75))

    def test_spaces_ignored(self):
        assert _parse_position(" 50 , 80 ") == pytest.approx((50.0, 80.0))

    def test_missing_component_raises(self):
        with pytest.raises(ValueError):
            _parse_position("72")

    def test_too_many_components_raises(self):
        with pytest.raises(ValueError):
            _parse_position("72,80,90")

    @pytest.mark.parametrize("position", ["-1,0", "0,-1", "nan,1", "1,inf"])
    def test_invalid_coordinates_raise(self, position: str):
        with pytest.raises(ValueError):
            _parse_position(position)


# ── run — happy paths ─────────────────────────────────────────────────────────

class TestAddImagesRun:
    def test_creates_output_file(self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        assert run(str(tmp_pdf), [str(tmp_png_image)], output_path=str(out)) is True
        assert out.exists()

    def test_default_output_name(self, tmp_pdf: Path, tmp_png_image: Path):
        assert run(str(tmp_pdf), [str(tmp_png_image)]) is True
        expected = tmp_pdf.parent / f"{tmp_pdf.stem}_with_images.pdf"
        assert expected.exists()

    def test_page_count_unchanged_stamp_mode(
        self, tmp_multi_pdf: Path, tmp_png_image: Path, tmp_path: Path
    ):
        """Stamping onto existing pages must not change page count."""
        out = tmp_path / "result.pdf"
        run(str(tmp_multi_pdf), [str(tmp_png_image)], output_path=str(out))
        with fitz.open(str(out)) as doc:
            assert doc.page_count == 5

    def test_append_mode_adds_pages(
        self, tmp_pdf: Path, tmp_two_png_images: list, tmp_path: Path
    ):
        """--append must add one blank page per image."""
        out = tmp_path / "appended.pdf"
        images = [str(p) for p in tmp_two_png_images]
        assert run(str(tmp_pdf), images, output_path=str(out), append=True) is True
        with fitz.open(str(out)) as doc:
            # original 1 page + 2 appended pages = 3
            assert doc.page_count == 3

    def test_specific_page_target(
        self, tmp_multi_pdf: Path, tmp_png_image: Path, tmp_path: Path
    ):
        """Specifying --page should succeed without raising."""
        out = tmp_path / "result.pdf"
        assert run(
            str(tmp_multi_pdf), [str(tmp_png_image)], output_path=str(out), page=2
        ) is True

    def test_custom_position(self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        assert run(
            str(tmp_pdf), [str(tmp_png_image)],
            output_path=str(out), position="100,200"
        ) is True

    def test_custom_width(self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        assert run(
            str(tmp_pdf), [str(tmp_png_image)],
            output_path=str(out), width=150.0
        ) is True

    def test_custom_width_and_height(self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        assert run(
            str(tmp_pdf), [str(tmp_png_image)],
            output_path=str(out), width=100.0, height=80.0
        ) is True

    def test_only_height_specified(self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path):
        out = tmp_path / "result.pdf"
        assert run(
            str(tmp_pdf), [str(tmp_png_image)],
            output_path=str(out), height=120.0
        ) is True

    def test_multiple_images_sequential(
        self, tmp_multi_pdf: Path, tmp_two_png_images: list, tmp_path: Path
    ):
        """Two images placed sequentially on pages 1 and 2."""
        out = tmp_path / "result.pdf"
        images = [str(p) for p in tmp_two_png_images]
        assert run(str(tmp_multi_pdf), images, output_path=str(out)) is True
        with fitz.open(str(out)) as doc:
            assert doc.page_count == 5  # unchanged


# ── run — error / edge cases ──────────────────────────────────────────────────

class TestAddImagesRunErrors:
    def test_nonexistent_pdf_returns_false(self, tmp_path: Path, tmp_png_image: Path):
        assert run(str(tmp_path / "ghost.pdf"), [str(tmp_png_image)]) is False

    def test_nonexistent_image_returns_false(self, tmp_pdf: Path, tmp_path: Path):
        assert run(str(tmp_pdf), [str(tmp_path / "missing.png")]) is False

    def test_unsupported_image_format_returns_false(
        self, tmp_pdf: Path, tmp_path: Path
    ):
        fake = tmp_path / "file.xyz"
        fake.write_bytes(b"not an image")
        assert run(str(tmp_pdf), [str(fake)]) is False

    def test_empty_image_list_returns_false(self, tmp_pdf: Path):
        assert run(str(tmp_pdf), []) is False

    def test_invalid_position_returns_false(
        self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path
    ):
        out = tmp_path / "result.pdf"
        assert run(str(tmp_pdf), [str(tmp_png_image)],
                   output_path=str(out), position="bad") is False

    def test_page_out_of_range_returns_false(
        self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path
    ):
        """Requesting page 99 on a 1-page PDF must return False."""
        out = tmp_path / "result.pdf"
        assert run(str(tmp_pdf), [str(tmp_png_image)],
                   output_path=str(out), page=99) is False

    def test_page_zero_returns_false(
        self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path
    ):
        out = tmp_path / "result.pdf"
        assert run(str(tmp_pdf), [str(tmp_png_image)],
                   output_path=str(out), page=0) is False

    @pytest.mark.parametrize("width", [0, -1, float("nan"), float("inf")])
    def test_invalid_width_returns_false(
        self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path, width: float
    ):
        assert run(
            str(tmp_pdf),
            [str(tmp_png_image)],
            output_path=str(tmp_path / "result.pdf"),
            width=width,
        ) is False

    @pytest.mark.parametrize("height", [0, -1, float("nan"), float("inf")])
    def test_invalid_height_returns_false(
        self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path, height: float
    ):
        assert run(
            str(tmp_pdf),
            [str(tmp_png_image)],
            output_path=str(tmp_path / "result.pdf"),
            height=height,
        ) is False

    def test_position_outside_page_returns_false(
        self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path
    ):
        assert run(
            str(tmp_pdf),
            [str(tmp_png_image)],
            output_path=str(tmp_path / "result.pdf"),
            position="600,10",
        ) is False

    def test_rectangle_outside_page_returns_false(
        self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path
    ):
        assert run(
            str(tmp_pdf),
            [str(tmp_png_image)],
            output_path=str(tmp_path / "result.pdf"),
            width=600,
        ) is False


# ── cli_run ───────────────────────────────────────────────────────────────────

class TestAddImagesCliRun:
    def test_cli_delegates_correctly(
        self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path
    ):
        class Args:
            input = str(tmp_pdf)
            images = [str(tmp_png_image)]
            output = str(tmp_path / "cli_result.pdf")
            page = None
            position = "72,72"
            width = None
            height = None
            append = False

        assert cli_run(Args()) is True

    def test_cli_append_flag(
        self, tmp_pdf: Path, tmp_png_image: Path, tmp_path: Path
    ):
        out = tmp_path / "cli_append.pdf"

        class Args:
            input = str(tmp_pdf)
            images = [str(tmp_png_image)]
            output = str(out)
            page = None
            position = "72,72"
            width = None
            height = None
            append = True

        assert cli_run(Args()) is True
        with fitz.open(str(out)) as doc:
            assert doc.page_count == 2  # 1 original + 1 appended

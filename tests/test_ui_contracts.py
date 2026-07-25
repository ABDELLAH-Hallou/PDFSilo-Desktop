"""Mocked UI-to-service contracts and keyboard/CLI integration coverage."""

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings, Qt

from safepdf import cli
from safepdf.core import OperationResult
from safepdf.operations import (
    add_images,
    compress,
    concat,
    decrypt,
    encrypt,
    extract_images,
    extract_range,
    images_to_pdf,
    reorder,
    rotate,
    split,
    to_images,
    watermark,
)
from safepdf.ui.main_window import MainWindow
from safepdf.ui.pages import (
    OPERATION_PAGE_FACTORIES,
    PAGE_DEFINITIONS,
    OperationPage,
)

DEFINITIONS = {
    definition.key: definition
    for definition in PAGE_DEFINITIONS
}

OPERATION_MODULES = {
    "merge": concat,
    "split": split,
    "rotate": rotate,
    "extract_pages": extract_range,
    "compress": compress,
    "encrypt": encrypt,
    "decrypt": decrypt,
    "watermark": watermark,
    "extract_images": extract_images,
    "to_images": to_images,
    "reorder": reorder,
    "add_images": add_images,
    "images_to_pdf": images_to_pdf,
}


def _configure_page(
    key,
    page,
    *,
    qtbot,
    tmp_path,
    tmp_pdf,
    tmp_multi_pdf,
    tmp_pdf_folder,
    tmp_image_folder,
    tmp_two_png_images,
):
    output = tmp_path / f"{key}-contract.pdf"

    if key == "merge":
        sources = sorted(tmp_pdf_folder.glob("*.pdf"))
        page.input_picker.set_paths(sources)
        page.output_picker.set_path(output)
        page.target_size_combo.setCurrentText("Letter")
        return (sources, output), {"target_size": "Letter"}, output

    if key == "split":
        destination = tmp_path / "split-contract"
        page.input_picker.set_path(tmp_multi_pdf)
        page.output_picker.set_path(destination)
        return (tmp_multi_pdf, destination), {}, destination

    if key == "rotate":
        page.input_picker.set_path(tmp_multi_pdf)
        page.output_picker.set_path(output)
        page.angle_combo.setCurrentText("270")
        page.pages_edit.setText("1,3")
        return (
            (tmp_multi_pdf, 270),
            {"pages": "1,3", "output_path": output},
            output,
        )

    if key == "extract_pages":
        page.input_picker.set_path(tmp_multi_pdf)
        page.output_picker.set_path(output)
        page.start_spin.setValue(2)
        page.end_spin.setValue(4)
        return (
            (tmp_multi_pdf, 2, 4),
            {"output_path": output},
            output,
        )

    if key == "compress":
        page.input_picker.set_path(tmp_pdf)
        page.output_picker.set_path(output)
        page.quality_spin.setValue(35)
        return (
            (tmp_pdf,),
            {"output_path": output, "quality": 35},
            output,
        )

    if key == "encrypt":
        page.input_picker.set_path(tmp_pdf)
        page.output_picker.set_path(output)
        page.user_password_edit.setText("reader")
        page.user_password_confirmation_edit.setText("reader")
        page.owner_password_edit.setText("owner")
        page.owner_password_confirmation_edit.setText("owner")
        page.allow_print_checkbox.setChecked(False)
        page.allow_copy_checkbox.setChecked(True)
        page.allow_edit_checkbox.setChecked(False)
        return (
            (tmp_pdf, "reader"),
            {
                "owner_password": "owner",
                "output_path": output,
                "allow_print": False,
                "allow_copy": True,
                "allow_edit": False,
            },
            output,
        )

    if key == "decrypt":
        page.input_picker.set_path(tmp_pdf)
        page.output_picker.set_path(output)
        page.password_edit.setText("unlock")
        return (
            (tmp_pdf, "unlock"),
            {"output_path": output},
            output,
        )

    if key == "watermark":
        page.input_picker.set_path(tmp_pdf)
        page.output_picker.set_path(output)
        page.text_edit.setText("INTERNAL")
        page.opacity_spin.setValue(0.4)
        page.angle_spin.setValue(30)
        page.font_size_spin.setValue(42)
        page.color_edit.setText("0.1,0.2,0.3")
        return (
            (tmp_pdf, "INTERNAL"),
            {
                "output_path": output,
                "opacity": 0.4,
                "angle": 30.0,
                "font_size": 42.0,
                "color": "0.1,0.2,0.3",
            },
            output,
        )

    if key == "extract_images":
        destination = tmp_path / "extract-images-contract"
        page.input_picker.set_path(tmp_pdf)
        page.output_picker.set_path(destination)
        page.format_combo.setCurrentIndex(1)
        return (
            (tmp_pdf, destination),
            {"fmt": "jpeg"},
            destination,
        )

    if key == "to_images":
        destination = tmp_path / "render-contract"
        page.input_picker.set_path(tmp_pdf)
        page.output_picker.set_path(destination)
        page.format_combo.setCurrentIndex(1)
        page.dpi_spin.setValue(300)
        return (
            (tmp_pdf, destination),
            {"fmt": "jpeg", "dpi": 300},
            destination,
        )

    if key == "reorder":
        with qtbot.waitSignal(page.page_editor.documentLoaded, timeout=5_000):
            page.input_picker.set_path(tmp_multi_pdf)
        page.output_picker.set_path(output)
        page.page_editor.model.reverse()
        return (
            (tmp_multi_pdf, "5,4,3,2,1"),
            {"output_path": output},
            output,
        )

    if key == "add_images":
        page.input_picker.set_path(tmp_pdf)
        page.images_picker.set_paths(tmp_two_png_images)
        page.output_picker.set_path(output)
        page.page_spin.setValue(2)
        page.x_spin.setValue(3)
        page.y_spin.setValue(4)
        page.width_spin.setValue(100)
        page.height_spin.setValue(50)
        return (
            (tmp_pdf, tmp_two_png_images),
            {
                "output_path": output,
                "page": 2,
                "position": "3.0,4.0",
                "width": 100.0,
                "height": 50.0,
                "append": False,
            },
            output,
        )

    if key == "images_to_pdf":
        page.input_picker.set_path(tmp_image_folder)
        page.output_picker.set_path(output)
        page.target_size_combo.setCurrentText("Letter")
        page.fit_checkbox.setChecked(False)
        page.margin_spin.setValue(20)
        return (
            (tmp_image_folder,),
            {
                "output_path": output,
                "target_size": "Letter",
                "fit": False,
                "margin": 20.0,
            },
            output,
        )

    raise AssertionError(f"Missing contract setup for {key}.")


@pytest.mark.parametrize("page_key", tuple(OPERATION_MODULES))
def test_operation_page_sends_exact_parameters_through_worker(
    page_key,
    qtbot,
    monkeypatch,
    tmp_path,
    tmp_pdf,
    tmp_multi_pdf,
    tmp_pdf_folder,
    tmp_image_folder,
    tmp_two_png_images,
):
    page = OPERATION_PAGE_FACTORIES[page_key](DEFINITIONS[page_key])
    qtbot.addWidget(page)
    assert isinstance(page, OperationPage)
    expected_args, expected_kwargs, result_path = _configure_page(
        page_key,
        page,
        qtbot=qtbot,
        tmp_path=tmp_path,
        tmp_pdf=tmp_pdf,
        tmp_multi_pdf=tmp_multi_pdf,
        tmp_pdf_folder=tmp_pdf_folder,
        tmp_image_folder=tmp_image_folder,
        tmp_two_png_images=tmp_two_png_images,
    )
    calls = []

    def fake_operation(*args, progress, is_cancelled, **kwargs):
        calls.append(
            {
                "args": args,
                "kwargs": kwargs,
                "cancelled": is_cancelled(),
            }
        )
        progress(1, 1, f"Mocked {page_key}.")
        return OperationResult([result_path], f"Mocked {page_key} complete.")

    monkeypatch.setattr(
        OPERATION_MODULES[page_key],
        "execute",
        fake_operation,
    )

    assert page.panel.buttons.run_button.isEnabled()
    with qtbot.waitSignal(page.controller.runner.finished, timeout=5_000):
        page.panel.buttons.run_button.click()

    assert calls == [
        {
            "args": expected_args,
            "kwargs": expected_kwargs,
            "cancelled": False,
        }
    ]
    assert page.panel.result.property("resultState") == "success"


def test_main_window_keyboard_shortcuts_navigate_pages(
    qtbot,
    tmp_path,
):
    settings = QSettings(
        str(tmp_path / "keyboard-navigation.ini"),
        QSettings.Format.IniFormat,
    )
    window = MainWindow(settings)
    qtbot.addWidget(window)
    window.show()
    window.activateWindow()
    window.navigation.setFocus()

    assert window.navigation.currentRow() == 0
    qtbot.keyClick(window.navigation, Qt.Key.Key_Down)
    assert window.navigation.currentRow() == 1
    assert window.page_stack.currentIndex() == 1
    qtbot.keyClick(window.navigation, Qt.Key.Key_Down)
    assert window.navigation.currentRow() == 2
    assert window.page_stack.currentIndex() == 2
    qtbot.keyClick(window.navigation, Qt.Key.Key_Up)
    assert window.navigation.currentRow() == 1
    qtbot.keyClick(window.navigation, Qt.Key.Key_Home)
    assert window.navigation.currentRow() == 0


def test_unified_cli_still_processes_a_real_operation(
    monkeypatch,
    tmp_pdf,
    tmp_path,
):
    output = tmp_path / "cli-rotated.pdf"
    monkeypatch.setattr(
        cli.sys,
        "argv",
        [
            "safepdf",
            "rotate",
            str(tmp_pdf),
            "--angle",
            "90",
            "--output",
            str(output),
        ],
    )

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 0
    assert output.is_file()

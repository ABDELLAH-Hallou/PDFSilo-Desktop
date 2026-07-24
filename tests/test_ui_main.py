"""Smoke tests for the initial PySide6 desktop entry point."""

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QLabel

from safepdf.ui.main import create_main_window


def test_create_main_window(qtbot):
    window = create_main_window()
    qtbot.addWidget(window)

    assert window.windowTitle() == "SafePDF"
    assert window.size() == QSize(900, 600)
    assert isinstance(window.centralWidget(), QLabel)
    assert "desktop foundation is ready" in window.centralWidget().text()

"""Cross-platform visual constants for the SafePDF desktop interface."""

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

# Color palette
COLOR_BACKGROUND = "#F4F7FA"
COLOR_SURFACE = "#FFFFFF"
COLOR_SURFACE_MUTED = "#E9EFF5"
COLOR_PRIMARY = "#147D92"
COLOR_PRIMARY_HOVER = "#0E6577"
COLOR_TEXT = "#172B3A"
COLOR_TEXT_MUTED = "#5C7080"
COLOR_BORDER = "#CAD6E0"
COLOR_DANGER = "#B42318"
COLOR_SUCCESS = "#157347"

# Spacing scale, in device-independent Qt pixels.
SPACE_XXS = 4
SPACE_XS = 8
SPACE_SM = 12
SPACE_MD = 16
SPACE_LG = 24
SPACE_XL = 32
SPACE_XXL = 48

# Typography scale, in points.
FONT_SIZE_CAPTION = 9
FONT_SIZE_BODY = 10
FONT_SIZE_SUBTITLE = 13
FONT_SIZE_TITLE = 22
FONT_WEIGHT_NORMAL = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_BOLD = 700

CONTROL_HEIGHT = 36
BORDER_RADIUS = 8


APPLICATION_STYLESHEET = f"""
QWidget {{
    color: {COLOR_TEXT};
    background-color: {COLOR_BACKGROUND};
    font-size: {FONT_SIZE_BODY}pt;
}}

QMainWindow {{
    background-color: {COLOR_BACKGROUND};
}}

QLabel#titleLabel {{
    color: {COLOR_TEXT};
    font-size: {FONT_SIZE_TITLE}pt;
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#subtitleLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: {FONT_SIZE_SUBTITLE}pt;
}}

QPushButton {{
    min-height: {CONTROL_HEIGHT}px;
    padding: 0 {SPACE_MD}px;
    border: 1px solid {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE};
}}

QPushButton:hover {{
    border-color: {COLOR_PRIMARY};
}}

QPushButton[primary="true"] {{
    color: {COLOR_SURFACE};
    border-color: {COLOR_PRIMARY};
    background-color: {COLOR_PRIMARY};
}}

QPushButton[primary="true"]:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
}}
"""


def apply_theme(application: QApplication) -> None:
    """Apply SafePDF's platform-neutral base style and system font."""
    application.setStyle("Fusion")
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    font.setPointSize(FONT_SIZE_BODY)
    application.setFont(font)
    application.setStyleSheet(APPLICATION_STYLESHEET)


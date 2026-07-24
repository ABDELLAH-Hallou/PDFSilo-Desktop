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

QFrame#applicationHeader {{
    background-color: {COLOR_SURFACE};
    border-bottom: 1px solid {COLOR_BORDER};
}}

QLabel#applicationTitleLabel {{
    color: {COLOR_TEXT};
    font-size: {FONT_SIZE_SUBTITLE}pt;
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#pageTitleLabel {{
    color: {COLOR_TEXT};
    font-size: {FONT_SIZE_TITLE}pt;
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#pageDescriptionLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: {FONT_SIZE_SUBTITLE}pt;
}}

QLabel#privacyLabel {{
    color: {COLOR_SUCCESS};
    font-weight: {FONT_WEIGHT_MEDIUM};
}}

QLabel#placeholderLabel {{
    color: {COLOR_TEXT_MUTED};
}}

QListWidget#navigationList {{
    background-color: {COLOR_SURFACE};
    border: 0;
    border-right: 1px solid {COLOR_BORDER};
    outline: 0;
    padding: {SPACE_SM}px;
}}

QListWidget#navigationList::item {{
    min-height: {CONTROL_HEIGHT}px;
    padding: 0 {SPACE_SM}px;
    margin: {SPACE_XXS}px 0;
    border-radius: {BORDER_RADIUS}px;
}}

QListWidget#navigationList::item:hover {{
    background-color: {COLOR_SURFACE_MUTED};
}}

QListWidget#navigationList::item:selected {{
    color: {COLOR_SURFACE};
    background-color: {COLOR_PRIMARY};
}}

QStackedWidget#pageStack {{
    background-color: {COLOR_BACKGROUND};
}}

QMenuBar, QMenu, QStatusBar {{
    background-color: {COLOR_SURFACE};
}}

QStatusBar {{
    border-top: 1px solid {COLOR_BORDER};
}}

QToolButton {{
    min-height: {CONTROL_HEIGHT}px;
    padding: 0 {SPACE_SM}px;
    border: 0;
    border-radius: {BORDER_RADIUS}px;
    background-color: transparent;
}}

QToolButton:hover {{
    background-color: {COLOR_SURFACE_MUTED};
}}

QProgressBar {{
    min-height: 18px;
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 5px;
    background-color: {COLOR_SURFACE_MUTED};
    text-align: center;
}}

QProgressBar::chunk {{
    border-radius: 4px;
    background-color: {COLOR_PRIMARY};
}}

QLineEdit {{
    min-height: {CONTROL_HEIGHT}px;
    padding: 0 {SPACE_SM}px;
    border: 1px solid {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE};
}}

QLineEdit:focus {{
    border: 2px solid {COLOR_PRIMARY};
}}

QLineEdit[validationState="invalid"] {{
    border: 2px solid {COLOR_DANGER};
}}

QLineEdit[validationState="valid"] {{
    border-color: {COLOR_SUCCESS};
}}

QLabel#pathErrorLabel {{
    color: {COLOR_DANGER};
    font-size: {FONT_SIZE_CAPTION}pt;
}}

QWidget#dropZone {{
    min-height: 96px;
    border: 2px dashed {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE};
}}

QWidget#dropZone:focus {{
    border-color: {COLOR_PRIMARY};
}}

QWidget#dropZone[validationState="valid"] {{
    border-color: {COLOR_SUCCESS};
    background-color: #EDF8F2;
}}

QWidget#dropZone[validationState="invalid"] {{
    border-color: {COLOR_DANGER};
    background-color: #FFF1F0;
}}

QWidget#resultSummary {{
    padding: {SPACE_MD}px;
    border: 1px solid {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE};
}}

QWidget#resultSummary[resultState="success"] {{
    border-color: {COLOR_SUCCESS};
}}

QWidget#resultSummary[resultState="error"] {{
    border-color: {COLOR_DANGER};
}}

QWidget#resultSummary[resultState="cancelled"] {{
    border-color: {COLOR_TEXT_MUTED};
}}

QWidget#resultSummary[resultState="success"] QLabel#resultStatusLabel {{
    color: {COLOR_SUCCESS};
    font-weight: {FONT_WEIGHT_BOLD};
}}

QWidget#resultSummary[resultState="error"] QLabel#resultStatusLabel {{
    color: {COLOR_DANGER};
    font-weight: {FONT_WEIGHT_BOLD};
}}

QWidget#resultSummary[resultState="cancelled"] QLabel#resultStatusLabel {{
    color: {COLOR_TEXT_MUTED};
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#resultMetricsLabel, QLabel#progressMessageLabel {{
    color: {COLOR_TEXT_MUTED};
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

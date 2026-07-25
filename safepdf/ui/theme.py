"""Cross-platform design tokens and stylesheet for the SafePDF desktop UI."""

from __future__ import annotations

import re
from enum import Enum

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

from safepdf.ui.resources import RESOURCE_DIRECTORY

# A calm, high-contrast palette suited to document work.
COLOR_CANVAS = "#F5F7FB"
COLOR_BACKGROUND = COLOR_CANVAS
COLOR_SURFACE = "#FFFFFF"
COLOR_SURFACE_MUTED = "#F0F3F8"
COLOR_SURFACE_HOVER = "#E8EDF5"
COLOR_SIDEBAR = "#101827"
COLOR_SIDEBAR_MUTED = "#96A3B7"
COLOR_PRIMARY = "#2563EB"
COLOR_PRIMARY_HOVER = "#1D4ED8"
COLOR_PRIMARY_PRESSED = "#1E40AF"
COLOR_PRIMARY_SOFT = "#EAF1FF"
COLOR_ACCENT = "#0F9F8F"
COLOR_ON_DARK = "#FDFEFF"
COLOR_ON_PRIMARY = "#FCFDFF"
COLOR_TEXT = "#172033"
COLOR_TEXT_MUTED = "#667085"
COLOR_TEXT_SUBTLE = "#98A2B3"
COLOR_BORDER = "#D9E0EA"
COLOR_BORDER_STRONG = "#C4CEDB"
COLOR_DANGER = "#C4320A"
COLOR_DANGER_SOFT = "#FFF1ED"
COLOR_SUCCESS = "#067647"
COLOR_SUCCESS_SOFT = "#ECFDF3"
COLOR_WARNING = "#B54708"

# Spacing scale, in device-independent Qt pixels.
SPACE_XXS = 4
SPACE_XS = 8
SPACE_SM = 12
SPACE_MD = 16
SPACE_LG = 24
SPACE_XL = 32
SPACE_XXL = 48

# Typography scale, in points.
FONT_SIZE_CAPTION = 8
FONT_SIZE_BODY = 10
FONT_SIZE_SUBTITLE = 12
FONT_SIZE_SECTION = 15
FONT_SIZE_TITLE = 24
FONT_SIZE_HERO = 28
FONT_WEIGHT_NORMAL = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_SEMIBOLD = 600
FONT_WEIGHT_BOLD = 700

CONTROL_HEIGHT = 40
BORDER_RADIUS = 10
CARD_RADIUS = 14
SPIN_UP_ICON = (RESOURCE_DIRECTORY / "spin_up.svg").as_posix()
SPIN_DOWN_ICON = (RESOURCE_DIRECTORY / "spin_down.svg").as_posix()


class ThemeMode(str, Enum):
    """User-selectable application appearance modes."""

    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


def normalize_theme_mode(value: object) -> ThemeMode:
    """Return a supported theme mode, defaulting safely to System."""
    if isinstance(value, ThemeMode):
        return value
    try:
        return ThemeMode(str(value).lower())
    except ValueError:
        return ThemeMode.SYSTEM


APPLICATION_STYLESHEET = f"""
QWidget {{
    color: {COLOR_TEXT};
    font-size: {FONT_SIZE_BODY}pt;
}}

QMainWindow, QWidget#applicationContent, QWidget#applicationBody,
QWidget#homeContent, QScrollArea#homeScrollArea, QDialog#settingsDialog {{
    background-color: {COLOR_CANVAS};
}}

QFrame#applicationHeader {{
    background-color: {COLOR_SURFACE};
    border: 0;
    border-bottom: 1px solid {COLOR_BORDER};
}}

QFrame#brandPanel {{
    background-color: {COLOR_SIDEBAR};
    border: 0;
}}

QLabel#brandMark {{
    color: {COLOR_ON_PRIMARY};
    background-color: {COLOR_PRIMARY};
    border-radius: 9px;
    font-size: 14pt;
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#applicationTitleLabel {{
    color: {COLOR_ON_DARK};
    background: transparent;
    font-size: {FONT_SIZE_SECTION}pt;
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#brandSubtitle, QLabel#navigationSectionLabel {{
    color: {COLOR_SIDEBAR_MUTED};
    background: transparent;
    font-size: {FONT_SIZE_CAPTION}pt;
}}

QLabel#navigationSectionLabel {{
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QLabel#headerEyebrowLabel, QLabel#pageEyebrowLabel {{
    color: {COLOR_PRIMARY};
    background: transparent;
    font-size: {FONT_SIZE_CAPTION}pt;
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#headerPageTitleLabel {{
    color: {COLOR_TEXT};
    background: transparent;
    font-size: {FONT_SIZE_SECTION}pt;
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QLabel#headerDescriptionLabel {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
    font-size: {FONT_SIZE_CAPTION}pt;
}}

QLabel#localBadge {{
    color: {COLOR_SUCCESS};
    background-color: {COLOR_SUCCESS_SOFT};
    border: 1px solid #ABEFC6;
    border-radius: 14px;
    padding: 5px 10px;
    font-size: {FONT_SIZE_CAPTION}pt;
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QLabel#pageTitleLabel {{
    color: {COLOR_TEXT};
    background: transparent;
    font-size: {FONT_SIZE_TITLE}pt;
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#pageDescriptionLabel {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
    font-size: {FONT_SIZE_SUBTITLE}pt;
}}

QLabel#sectionTitleLabel, QLabel#panelTitleLabel, QLabel#previewTitleLabel {{
    color: {COLOR_TEXT};
    background: transparent;
    font-size: {FONT_SIZE_SECTION}pt;
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QLabel#sectionDescriptionLabel, QLabel#panelDescriptionLabel {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
    font-size: {FONT_SIZE_CAPTION}pt;
}}

QLabel#themeDescriptionLabel {{
    color: {COLOR_TEXT_MUTED};
    background-color: {COLOR_SURFACE_MUTED};
    border: 1px solid {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    padding: {SPACE_SM}px;
}}

QLabel#privacyLabel {{
    color: {COLOR_SUCCESS};
    background: transparent;
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QLabel#placeholderLabel {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
}}

QWidget#sidebar {{
    background-color: {COLOR_SIDEBAR};
}}

QListWidget#navigationList {{
    color: #D8E0EC;
    background-color: {COLOR_SIDEBAR};
    border: 0;
    outline: 0;
    padding: 2px {SPACE_SM}px {SPACE_SM}px {SPACE_SM}px;
}}

QListWidget#navigationList::item {{
    min-height: 40px;
    padding: 0 {SPACE_SM}px;
    margin: 2px 0;
    border: 0;
    border-radius: {BORDER_RADIUS}px;
}}

QListWidget#navigationList::item:hover {{
    color: {COLOR_ON_DARK};
    background-color: #1D2939;
}}

QListWidget#navigationList::item:selected {{
    color: {COLOR_ON_PRIMARY};
    background-color: {COLOR_PRIMARY};
}}

QListWidget#navigationList::item:disabled {{
    color: #667085;
}}

QStackedWidget#pageStack, QScrollArea#operationPageScrollArea,
QWidget#operationPageContent {{
    background-color: {COLOR_CANVAS};
    border: 0;
}}

QFrame#homeHero {{
    background-color: {COLOR_SIDEBAR};
    border: 0;
    border-radius: {CARD_RADIUS}px;
}}

QFrame#homeHero QLabel#pageEyebrowLabel {{
    color: #93C5FD;
}}

QFrame#homeHero QLabel#pageTitleLabel {{
    color: {COLOR_ON_DARK};
    font-size: {FONT_SIZE_HERO}pt;
}}

QFrame#homeHero QLabel#pageDescriptionLabel {{
    color: #C5CFDD;
}}

QLabel#heroPrivacyLabel {{
    color: #A7F3D0;
    background: transparent;
    font-weight: {FONT_WEIGHT_MEDIUM};
}}

QFrame#toolCard {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS}px;
}}

QFrame#toolCard:hover {{
    background-color: #FAFCFF;
    border-color: #A9BFEF;
}}

QLabel#toolIconLabel {{
    color: {COLOR_PRIMARY};
    background-color: {COLOR_PRIMARY_SOFT};
    border-radius: 10px;
    font-size: 14pt;
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#toolTitleLabel {{
    color: {COLOR_TEXT};
    background: transparent;
    font-size: {FONT_SIZE_SUBTITLE}pt;
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QLabel#toolDescriptionLabel {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
    font-size: {FONT_SIZE_CAPTION}pt;
}}

QPushButton#toolCardButton {{
    color: {COLOR_PRIMARY};
    background: transparent;
    border: 0;
    padding: 0;
    font-weight: {FONT_WEIGHT_SEMIBOLD};
    text-align: left;
}}

QFrame#operationHeader, QWidget#operationWorkspace {{
    background: transparent;
    border: 0;
}}

QWidget#operationForm, QFrame#previewCard, QWidget#operationPanel {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS}px;
}}

QWidget#operationForm {{
    padding: 0;
}}

QSplitter#operationSplitter::handle {{
    background: transparent;
    width: {SPACE_SM}px;
    height: {SPACE_SM}px;
}}

QLabel#pathPickerLabel, QLabel#optionLabel {{
    color: {COLOR_TEXT};
    background: transparent;
    font-weight: {FONT_WEIGHT_MEDIUM};
}}

QWidget#pathPicker, QWidget#singlePdfPicker, QWidget#multiplePdfPicker,
QWidget#imageFilePicker, QWidget#folderPicker, QWidget#outputFilePicker,
QWidget#outputDirectoryPicker {{
    background: transparent;
}}

QMenuBar {{
    color: {COLOR_TEXT};
    background-color: {COLOR_SURFACE};
    border-bottom: 1px solid {COLOR_BORDER};
}}

QMenuBar::item {{
    padding: 5px 9px;
    background: transparent;
}}

QMenuBar::item:selected, QMenuBar::item:pressed {{
    background-color: {COLOR_SURFACE_HOVER};
    border-radius: 5px;
}}

QMenu {{
    color: {COLOR_TEXT};
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    padding: 5px;
}}

QMenu::item {{
    padding: 7px 28px 7px 10px;
    border-radius: 5px;
}}

QMenu::item:selected {{
    color: {COLOR_TEXT};
    background-color: {COLOR_PRIMARY_SOFT};
}}

QStatusBar {{
    color: {COLOR_TEXT_MUTED};
    background-color: {COLOR_SURFACE};
    border-top: 1px solid {COLOR_BORDER};
    min-height: 28px;
}}

QStatusBar::item {{
    border: 0;
}}

QLabel#outputLocationLabel {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
}}

QToolButton {{
    min-height: {CONTROL_HEIGHT}px;
    padding: 0 {SPACE_SM}px;
    border: 1px solid transparent;
    border-radius: {BORDER_RADIUS}px;
    background-color: transparent;
}}

QToolButton:hover {{
    border-color: {COLOR_BORDER};
    background-color: {COLOR_SURFACE_MUTED};
}}

QToolButton:focus {{
    border: 2px solid {COLOR_PRIMARY};
}}

QProgressBar {{
    min-height: 10px;
    max-height: 10px;
    color: transparent;
    border: 0;
    border-radius: 5px;
    background-color: {COLOR_SURFACE_MUTED};
    text-align: center;
}}

QProgressBar::chunk {{
    border-radius: 5px;
    background-color: {COLOR_PRIMARY};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox,
QDoubleSpinBox {{
    min-height: {CONTROL_HEIGHT}px;
    padding: 0 {SPACE_SM}px;
    border: 1px solid {COLOR_BORDER_STRONG};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE};
    selection-background-color: {COLOR_PRIMARY};
}}

QSpinBox, QDoubleSpinBox {{
    padding-left: {SPACE_SM}px;
    padding-right: 36px;
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 28px;
    border: 0;
    border-left: 1px solid {COLOR_BORDER};
    border-bottom: 1px solid {COLOR_BORDER};
    border-top-right-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE_MUTED};
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 28px;
    border: 0;
    border-left: 1px solid {COLOR_BORDER};
    border-bottom-right-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE_MUTED};
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {COLOR_PRIMARY_SOFT};
}}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url("{SPIN_UP_ICON}");
    width: 10px;
    height: 7px;
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url("{SPIN_DOWN_ICON}");
    width: 9px;
    height: 7px;
}}

QTextEdit, QPlainTextEdit {{
    padding-top: {SPACE_XS}px;
    padding-bottom: {SPACE_XS}px;
}}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QComboBox:hover,
QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: #98A6B8;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {COLOR_PRIMARY};
}}

QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled,
QSpinBox:disabled, QDoubleSpinBox:disabled {{
    color: {COLOR_TEXT_SUBTLE};
    background-color: {COLOR_SURFACE_MUTED};
}}

QLineEdit[validationState="invalid"] {{
    border: 2px solid {COLOR_DANGER};
    background-color: {COLOR_DANGER_SOFT};
}}

QLineEdit[validationState="valid"] {{
    border-color: #6CE9A6;
}}

QComboBox::drop-down {{
    width: 28px;
    border: 0;
}}

QCheckBox {{
    spacing: {SPACE_XS}px;
    background: transparent;
}}

QCheckBox::indicator {{
    width: 17px;
    height: 17px;
}}

QCheckBox::indicator:unchecked {{
    background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER_STRONG};
    border-radius: 5px;
}}

QCheckBox::indicator:checked {{
    background: {COLOR_PRIMARY};
    border: 1px solid {COLOR_PRIMARY};
    border-radius: 5px;
}}

QLabel#pathErrorLabel, QLabel#formErrorLabel {{
    color: {COLOR_DANGER};
    background: transparent;
    font-size: {FONT_SIZE_CAPTION}pt;
}}

QWidget#pdfPreview, QWidget#pageReorderEditor {{
    padding: {SPACE_SM}px;
    border: 0;
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE_MUTED};
}}

QScrollArea#pdfPreviewScrollArea {{
    border: 1px solid {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    background-color: #DDE3EC;
}}

QLabel#pdfPreviewImage {{
    color: {COLOR_TEXT_SUBTLE};
    border: 0;
    background-color: {COLOR_SURFACE};
}}

QLabel#pdfPreviewStatus, QLabel#pageListStatus, QLabel#previewPageLabel,
QLabel#previewZoomLabel, QLabel#previewTargetLabel,
QLabel#previewControlLabel {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
}}

QListView#pageListView, QListWidget#resultWarningList,
QListWidget#resultOutputList, QListWidget#orderedFileList {{
    border: 1px solid {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE};
    outline: 0;
}}

QListWidget#orderedFileList[validationState="invalid"] {{
    border: 2px solid {COLOR_DANGER};
    background-color: {COLOR_DANGER_SOFT};
}}

QListWidget#orderedFileList::item {{
    min-height: 34px;
    padding: 2px {SPACE_XS}px;
    border-radius: 6px;
}}

QListWidget#orderedFileList::item:selected {{
    color: {COLOR_TEXT};
    background-color: {COLOR_PRIMARY_SOFT};
}}

QListView#pageListView::item {{
    padding: {SPACE_XS}px;
    margin: {SPACE_XS}px;
    border: 1px solid transparent;
    border-radius: {BORDER_RADIUS}px;
}}

QListView#pageListView::item:selected {{
    color: {COLOR_TEXT};
    border-color: {COLOR_PRIMARY};
    background-color: {COLOR_PRIMARY_SOFT};
}}

QWidget#dropZone {{
    min-height: 96px;
    border: 2px dashed {COLOR_BORDER_STRONG};
    border-radius: {CARD_RADIUS}px;
    background-color: {COLOR_SURFACE};
}}

QWidget#dropZone:hover, QWidget#dropZone:focus {{
    border-color: {COLOR_PRIMARY};
    background-color: {COLOR_PRIMARY_SOFT};
}}

QWidget#dropZone[validationState="valid"] {{
    border-color: #6CE9A6;
    background-color: {COLOR_SUCCESS_SOFT};
}}

QWidget#dropZone[validationState="invalid"] {{
    border-color: #FDA29B;
    background-color: {COLOR_DANGER_SOFT};
}}

QWidget#resultSummary {{
    padding: {SPACE_MD}px;
    border: 1px solid {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE_MUTED};
}}

QWidget#resultSummary[resultState="success"] {{
    border-color: #ABEFC6;
    background-color: {COLOR_SUCCESS_SOFT};
}}

QWidget#resultSummary[resultState="review"] {{
    border-color: #B2CCFF;
    background-color: {COLOR_PRIMARY_SOFT};
}}

QWidget#resultSummary[resultState="error"] {{
    border-color: #FECDCA;
    background-color: {COLOR_DANGER_SOFT};
}}

QWidget#resultSummary[resultState="cancelled"] {{
    border-color: {COLOR_BORDER_STRONG};
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

QWidget#resultSummary[resultState="review"] QLabel#resultStatusLabel {{
    color: {COLOR_PRIMARY};
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#resultMessageLabel, QLabel#resultMetricsLabel,
QLabel#progressMessageLabel {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
}}

QPushButton {{
    min-height: {CONTROL_HEIGHT}px;
    padding: 0 {SPACE_MD}px;
    border: 1px solid {COLOR_BORDER_STRONG};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE};
    font-weight: {FONT_WEIGHT_MEDIUM};
}}

QPushButton:hover {{
    color: {COLOR_PRIMARY};
    border-color: {COLOR_PRIMARY};
    background-color: {COLOR_PRIMARY_SOFT};
}}

QPushButton:pressed {{
    background-color: #DCE7FF;
}}

QPushButton:focus {{
    border: 2px solid {COLOR_PRIMARY};
}}

QPushButton:disabled {{
    color: {COLOR_TEXT_SUBTLE};
    border-color: {COLOR_BORDER};
    background-color: {COLOR_SURFACE_MUTED};
}}

QPushButton[primary="true"] {{
    color: {COLOR_ON_PRIMARY};
    border-color: {COLOR_PRIMARY};
    background-color: {COLOR_PRIMARY};
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QPushButton[primary="true"]:hover {{
    color: {COLOR_ON_PRIMARY};
    border-color: {COLOR_PRIMARY_HOVER};
    background-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton[primary="true"]:pressed {{
    background-color: {COLOR_PRIMARY_PRESSED};
}}

QPushButton#browseButton {{
    min-width: 88px;
}}

QPushButton#previewZoomOutButton, QPushButton#previewZoomInButton {{
    min-width: 38px;
    max-width: 38px;
    padding: 0;
    font-size: {FONT_SIZE_SUBTITLE}pt;
}}

QPushButton#previewFitButton {{
    min-width: 52px;
    padding: 0 {SPACE_XS}px;
}}

QScrollBar:vertical {{
    width: 10px;
    margin: 2px;
    border: 0;
    background: transparent;
}}

QScrollBar::handle:vertical {{
    min-height: 32px;
    border-radius: 4px;
    background: #C8D0DC;
}}

QScrollBar::handle:vertical:hover {{
    background: #AEB8C6;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: transparent;
}}

QToolTip {{
    color: {COLOR_ON_DARK};
    background-color: {COLOR_SIDEBAR};
    border: 1px solid #344054;
    padding: 6px;
}}
"""

# Dark colors replace the same semantic roles used by the light stylesheet.
# A single-pass replacement prevents one mapped value from being replaced
# again when it happens to match another source color.
DARK_COLOR_REPLACEMENTS = {
    "#F5F7FB": "#0B1220",
    "#FFFFFF": "#111C2E",
    "#F0F3F8": "#182438",
    "#E8EDF5": "#22314A",
    "#101827": "#080E18",
    "#96A3B7": "#9AA8BC",
    "#2563EB": "#5B8DEF",
    "#1D4ED8": "#77A2FF",
    "#1E40AF": "#3F6FD6",
    "#EAF1FF": "#172B50",
    "#0F9F8F": "#36C8B7",
    "#FCFDFF": "#0B1220",
    "#172033": "#F3F6FB",
    "#667085": "#A7B2C3",
    "#98A2B3": "#7F8DA3",
    "#D9E0EA": "#26354B",
    "#C4CEDB": "#3A4A62",
    "#C4320A": "#FF8A70",
    "#FFF1ED": "#3A1D1B",
    "#067647": "#54D6A0",
    "#ECFDF3": "#123427",
    "#B54708": "#FDBA74",
    "#93C5FD": "#9CC8FF",
    "#C5CFDD": "#B8C4D6",
    "#A7F3D0": "#78E7B9",
    "#FAFCFF": "#162238",
    "#A9BFEF": "#507AC9",
    "#D8E0EC": "#D5DEEB",
    "#1D2939": "#1B2B44",
    "#344054": "#40516A",
    "#ABEFC6": "#276749",
    "#98A6B8": "#607089",
    "#6CE9A6": "#35B983",
    "#FDA29B": "#C75C52",
    "#FECDCA": "#7A3935",
    "#DCE7FF": "#213963",
    "#C8D0DC": "#41516A",
    "#AEB8C6": "#5A6A80",
}


def _replace_theme_colors(
    stylesheet: str,
    replacements: dict[str, str],
) -> str:
    pattern = re.compile(
        "|".join(
            re.escape(color)
            for color in sorted(replacements, key=len, reverse=True)
        ),
        re.IGNORECASE,
    )
    return pattern.sub(
        lambda match: replacements[match.group(0).upper()],
        stylesheet,
    )


DARK_STYLESHEET = _replace_theme_colors(
    APPLICATION_STYLESHEET,
    DARK_COLOR_REPLACEMENTS,
)

# The runtime stylesheet uses QPalette roles instead of fixed theme colors.
# It is parsed only once; switching appearance then requires only a palette
# update, which is substantially faster for an application with many pages.
PALETTE_COLOR_REPLACEMENTS = {
    "#F5F7FB": "palette(window)",
    "#FFFFFF": "palette(base)",
    "#F0F3F8": "palette(alternate-base)",
    "#E8EDF5": "palette(midlight)",
    "#101827": "palette(shadow)",
    "#2563EB": "palette(highlight)",
    "#1D4ED8": "palette(link)",
    "#1E40AF": "palette(link-visited)",
    "#EAF1FF": "palette(light)",
    "#0F9F8F": "palette(accent)",
    "#FCFDFF": "palette(highlighted-text)",
    "#FDFEFF": "palette(tooltip-text)",
    "#172033": "palette(text)",
    "#667085": "palette(placeholder-text)",
    "#D9E0EA": "palette(mid)",
    "#C4CEDB": "palette(dark)",
    "#C4320A": "palette(bright-text)",
    "#FFF1ED": "palette(alternate-base)",
    "#067647": "palette(accent)",
    "#ECFDF3": "palette(button)",
    "#FAFCFF": "palette(base)",
    "#A9BFEF": "palette(link)",
    "#344054": "palette(dark)",
    "#ABEFC6": "palette(accent)",
    "#98A6B8": "palette(dark)",
    "#6CE9A6": "palette(accent)",
    "#FDA29B": "palette(bright-text)",
    "#FECDCA": "palette(bright-text)",
    "#DCE7FF": "palette(light)",
    "#C8D0DC": "palette(mid)",
    "#AEB8C6": "palette(dark)",
}

LIGHT_STYLESHEET = APPLICATION_STYLESHEET
STATIC_DARK_STYLESHEET = DARK_STYLESHEET
APPLICATION_STYLESHEET = _replace_theme_colors(
    LIGHT_STYLESHEET,
    PALETTE_COLOR_REPLACEMENTS,
)
# Theme variants intentionally share one palette-aware runtime stylesheet.
DARK_STYLESHEET = APPLICATION_STYLESHEET


def _application_palette(mode: ThemeMode) -> QPalette:
    """Build a native Qt palette matching the active QSS theme."""
    dark = mode is ThemeMode.DARK
    colors = {
        "window": "#0B1220" if dark else "#F5F7FB",
        "surface": "#111C2E" if dark else "#FFFFFF",
        "alternate": "#182438" if dark else "#F0F3F8",
        "text": "#F3F6FB" if dark else "#172033",
        "muted": "#A7B2C3" if dark else "#667085",
        "disabled": "#7F8DA3" if dark else "#98A2B3",
        "primary": "#5B8DEF" if dark else "#2563EB",
        "primary_hover": "#77A2FF" if dark else "#1D4ED8",
        "primary_pressed": "#3F6FD6" if dark else "#1E40AF",
        "primary_soft": "#172B50" if dark else "#EAF1FF",
        "on_primary": "#0B1220" if dark else "#FCFDFF",
        "surface_hover": "#22314A" if dark else "#E8EDF5",
        "border": "#26354B" if dark else "#D9E0EA",
        "border_strong": "#3A4A62" if dark else "#C4CEDB",
        "danger": "#FF8A70" if dark else "#C4320A",
        "success": "#54D6A0" if dark else "#067647",
        "success_soft": "#123427" if dark else "#ECFDF3",
        "tooltip": "#080E18" if dark else "#101827",
    }
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors["window"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors["surface"]))
    palette.setColor(
        QPalette.ColorRole.AlternateBase,
        QColor(colors["alternate"]),
    )
    palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(colors["surface"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["text"]))
    palette.setColor(
        QPalette.ColorRole.BrightText,
        QColor(colors["danger"]),
    )
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["primary"]))
    palette.setColor(
        QPalette.ColorRole.HighlightedText,
        QColor(colors["on_primary"]),
    )
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["tooltip"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFFFFF"))
    palette.setColor(
        QPalette.ColorRole.PlaceholderText,
        QColor(colors["muted"]),
    )
    palette.setColor(
        QPalette.ColorRole.Midlight,
        QColor(colors["surface_hover"]),
    )
    palette.setColor(QPalette.ColorRole.Mid, QColor(colors["border"]))
    palette.setColor(
        QPalette.ColorRole.Dark,
        QColor(colors["border_strong"]),
    )
    palette.setColor(QPalette.ColorRole.Shadow, QColor(colors["tooltip"]))
    palette.setColor(
        QPalette.ColorRole.Light,
        QColor(colors["primary_soft"]),
    )
    palette.setColor(
        QPalette.ColorRole.Link,
        QColor(colors["primary_hover"]),
    )
    palette.setColor(
        QPalette.ColorRole.LinkVisited,
        QColor(colors["primary_pressed"]),
    )
    palette.setColor(
        QPalette.ColorRole.Accent,
        QColor(colors["success"]),
    )
    palette.setColor(
        QPalette.ColorRole.Button,
        QColor(colors["success_soft"]),
    )
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            role,
            QColor(colors["disabled"]),
        )
    return palette


def _apply_application_font(application: QApplication) -> None:
    """Restore the selected UI font after Qt style re-polishing."""
    families = set(QFontDatabase.families())
    if "Segoe UI" in families:
        font = QFont("Segoe UI", FONT_SIZE_BODY)
    else:
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
        font.setPointSize(FONT_SIZE_BODY)
    application.setFont(font)


class ThemeManager(QObject):
    """Apply explicit or operating-system-driven application themes."""

    themeChanged = Signal(str, str)

    def __init__(self, application: QApplication) -> None:
        super().__init__(application)
        self.application = application
        self._mode = ThemeMode.SYSTEM
        self._effective_mode = ThemeMode.LIGHT
        application.styleHints().colorSchemeChanged.connect(
            self._system_color_scheme_changed
        )

    @property
    def mode(self) -> ThemeMode:
        return self._mode

    @property
    def effective_mode(self) -> ThemeMode:
        return self._effective_mode

    def set_mode(self, mode: ThemeMode | str) -> None:
        """Apply a mode immediately; System resolves through Qt style hints."""
        requested_mode = normalize_theme_mode(mode)
        expected_effective = (
            requested_mode
            if requested_mode is not ThemeMode.SYSTEM
            else (
                ThemeMode.DARK
                if self.application.styleHints().colorScheme()
                is Qt.ColorScheme.Dark
                else ThemeMode.LIGHT
            )
        )
        expected_stylesheet = (
            DARK_STYLESHEET
            if expected_effective is ThemeMode.DARK
            else APPLICATION_STYLESHEET
        )
        if (
            requested_mode is self._mode
            and expected_effective is self._effective_mode
            and self.application.styleSheet() == expected_stylesheet
        ):
            return
        self._mode = requested_mode
        self._apply()

    def _resolved_mode(self) -> ThemeMode:
        if self._mode is not ThemeMode.SYSTEM:
            return self._mode
        scheme = self.application.styleHints().colorScheme()
        if scheme is Qt.ColorScheme.Dark:
            return ThemeMode.DARK
        return ThemeMode.LIGHT

    def _apply(self) -> None:
        effective_mode = self._resolved_mode()
        self._effective_mode = effective_mode
        self.application.setPalette(_application_palette(effective_mode))
        if self.application.styleSheet() != APPLICATION_STYLESHEET:
            self.application.setStyleSheet(APPLICATION_STYLESHEET)
        else:
            # Palette-backed QSS brushes are cached by Qt. Re-polishing the
            # application refreshes them without reparsing the stylesheet or
            # walking every operation page in Python.
            style = self.application.style()
            style.unpolish(self.application)
            style.polish(self.application)
        _apply_application_font(self.application)
        self.themeChanged.emit(self._mode.value, effective_mode.value)

    @Slot(Qt.ColorScheme)
    def _system_color_scheme_changed(
        self,
        _scheme: Qt.ColorScheme,
    ) -> None:
        if self._mode is ThemeMode.SYSTEM:
            self._apply()


def theme_manager(application: QApplication) -> ThemeManager:
    """Return the process-wide theme manager, creating it when needed."""
    manager = getattr(application, "_safepdf_theme_manager", None)
    if not isinstance(manager, ThemeManager):
        manager = ThemeManager(application)
        setattr(application, "_safepdf_theme_manager", manager)
    return manager


def apply_theme(
    application: QApplication,
    mode: ThemeMode | str = ThemeMode.SYSTEM,
) -> ThemeManager:
    """Apply typography and the requested application-wide appearance."""
    existing_manager = getattr(
        application,
        "_safepdf_theme_manager",
        None,
    )
    if not isinstance(existing_manager, ThemeManager):
        application.setStyle("Fusion")
    manager = theme_manager(application)
    manager.set_mode(mode)
    _apply_application_font(application)
    return manager

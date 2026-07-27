"""Cross-platform design tokens and stylesheet for the PDFSilo desktop UI."""

from __future__ import annotations

import re
from enum import Enum

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

from pdfsilo.ui.resources import RESOURCE_DIRECTORY

# Official PDFSilo indigo and teal brand scale.
BRAND_50 = "#EEF2FF"
BRAND_100 = "#E0E7FF"
BRAND_200 = "#C7D2FE"
BRAND_300 = "#A5B4FC"
BRAND_400 = "#818CF8"
BRAND_500 = "#5B6EE1"
BRAND_600 = "#4353C7"
BRAND_700 = "#3342A5"
BRAND_800 = "#27347F"
BRAND_900 = "#1B2559"
BRAND_950 = "#111936"

ACCENT_300 = "#5DE5DC"
ACCENT_400 = "#2DD4C7"
ACCENT_500 = "#16B8AE"
ACCENT_600 = "#0E918A"

# Light-mode semantic aliases used by the palette-backed stylesheet.
COLOR_CANVAS = "#F7F8FC"
COLOR_BACKGROUND = COLOR_CANVAS
COLOR_SURFACE = "#FFFFFF"
COLOR_SURFACE_MUTED = "#F8FAFC"
COLOR_SURFACE_HOVER = "#F1F3FF"
COLOR_SIDEBAR = "#F0F2F8"
COLOR_SIDEBAR_MUTED = "#4D566B"
COLOR_PRIMARY = BRAND_600
COLOR_PRIMARY_HOVER = BRAND_700
COLOR_PRIMARY_PRESSED = BRAND_800
COLOR_PRIMARY_SOFT = BRAND_50
COLOR_ACCENT = ACCENT_500
COLOR_ON_DARK = "#F4F6FB"
COLOR_ON_PRIMARY = "#FCFDFF"
COLOR_TEXT = "#151A2D"
COLOR_TEXT_MUTED = "#4D566B"
COLOR_TEXT_SUBTLE = "#747D91"
COLOR_BORDER = "#D9DDE7"
COLOR_BORDER_STRONG = "#B8BFCE"
COLOR_DANGER = "#A52432"
COLOR_DANGER_SOFT = "#FFF0F1"
COLOR_SUCCESS = "#187A3F"
COLOR_SUCCESS_SOFT = "#ECFDF3"
COLOR_WARNING = "#855B00"
COLOR_WARNING_SOFT = "#FFF8E5"
COLOR_INFO = "#235F9D"
COLOR_INFO_SOFT = "#EEF6FF"

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
QWidget#homeContent, QScrollArea#homeScrollArea, QDialog#settingsDialog,
QDialog#aboutDialog {{
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
    border-bottom: 1px solid {COLOR_BORDER};
}}

QLabel#brandLogoLabel {{
    background: transparent;
}}

QLabel#applicationTitleLabel {{
    color: {COLOR_TEXT};
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
    border: 1px solid #86E5AA;
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

QLabel#settingsTitleLabel, QLabel#aboutProductName {{
    color: {COLOR_TEXT};
    background: transparent;
    font-size: {FONT_SIZE_TITLE}pt;
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#settingsIntroLabel, QLabel#aboutTagline {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
    font-size: {FONT_SIZE_SUBTITLE}pt;
}}

QLabel#settingsSectionTitle, QLabel#aboutPrivacyTitle,
QLabel#aboutFeatureTitle, QLabel#settingsPrivacyTitle {{
    color: {COLOR_TEXT};
    background: transparent;
    font-size: {FONT_SIZE_SUBTITLE}pt;
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QLabel#settingDescriptionLabel, QLabel#aboutFeatureDescription,
QLabel#aboutPrivacyText, QLabel#settingsPrivacyText,
QLabel#aboutRuntimeDetails, QLabel#aboutLicenseLabel,
QLabel#aboutVersion {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
    font-size: {FONT_SIZE_CAPTION}pt;
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

QTabWidget#settingsTabs::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS}px;
    background-color: {COLOR_SURFACE};
}}

QTabWidget#settingsTabs QTabBar::tab {{
    min-width: 120px;
    min-height: 34px;
    padding: 0 {SPACE_MD}px;
    margin-right: 3px;
    color: {COLOR_TEXT_MUTED};
    border: 1px solid transparent;
    border-bottom: 0;
    border-top-left-radius: {BORDER_RADIUS}px;
    border-top-right-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE_MUTED};
}}

QTabWidget#settingsTabs QTabBar::tab:selected {{
    color: {COLOR_PRIMARY};
    border-color: {COLOR_BORDER};
    background-color: {COLOR_SURFACE};
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QTabWidget#settingsTabs QTabBar::tab:hover:!selected {{
    color: {COLOR_TEXT};
    background-color: {COLOR_SURFACE_HOVER};
}}

QFrame#settingRow, QFrame#aboutFeatureCard, QFrame#aboutHero {{
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS}px;
    background-color: {COLOR_SURFACE};
}}

QFrame#settingRow:hover {{
    border-color: {COLOR_BORDER_STRONG};
    background-color: {COLOR_SURFACE_MUTED};
}}

QFrame#aboutHero {{
    border-color: {BRAND_300};
    background-color: {COLOR_PRIMARY_SOFT};
}}

QFrame#aboutPrivacyCard, QFrame#settingsPrivacyCard {{
    border: 1px solid #86E5AA;
    border-radius: {CARD_RADIUS}px;
    background-color: {COLOR_SUCCESS_SOFT};
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
    color: {COLOR_TEXT_MUTED};
    background-color: {COLOR_SIDEBAR};
    border: 0;
    outline: 0;
    padding: 2px {SPACE_SM}px {SPACE_SM}px {SPACE_SM}px;
}}

QListWidget#navigationList::item {{
    min-height: 40px;
    padding: 0 {SPACE_SM}px 0 9px;
    margin: 2px 0;
    border: 0;
    border-left: 3px solid transparent;
    border-radius: {BORDER_RADIUS}px;
}}

QListWidget#navigationList::item:hover {{
    color: {COLOR_TEXT};
    background-color: #E9ECF7;
}}

QListWidget#navigationList::item:selected {{
    color: {COLOR_TEXT};
    background-color: {BRAND_100};
    border-left: 3px solid {COLOR_PRIMARY};
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QListWidget#navigationList::item:disabled {{
    color: {COLOR_TEXT_SUBTLE};
}}

QStackedWidget#pageStack, QScrollArea#operationPageScrollArea,
QWidget#operationPageContent {{
    background-color: {COLOR_CANVAS};
    border: 0;
}}

QFrame#homeHero {{
    background-color: {BRAND_900};
    border: 0;
    border-radius: {CARD_RADIUS}px;
}}

QFrame#homeHero QLabel#pageEyebrowLabel {{
    color: {BRAND_300};
}}

QFrame#homeHero QLabel#pageTitleLabel {{
    color: {COLOR_ON_DARK};
    font-size: {FONT_SIZE_HERO}pt;
}}

QFrame#homeHero QLabel#pageDescriptionLabel {{
    color: {BRAND_200};
}}

QLabel#heroPrivacyLabel {{
    color: {ACCENT_300};
    background: transparent;
    font-weight: {FONT_WEIGHT_MEDIUM};
}}

QFrame#toolCard {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS}px;
}}

QFrame#toolCard:hover {{
    background-color: {COLOR_SURFACE_MUTED};
    border-color: {BRAND_300};
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
    border-color: {COLOR_BORDER_STRONG};
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
    border-color: #86E5AA;
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
    background-color: #E1E5ED;
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
    border-color: #86E5AA;
    background-color: {COLOR_SUCCESS_SOFT};
}}

QWidget#dropZone[validationState="invalid"] {{
    border-color: #F3A2AA;
    background-color: {COLOR_DANGER_SOFT};
}}

QWidget#resultSummary {{
    padding: {SPACE_MD}px;
    border: 1px solid {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE_MUTED};
}}

QWidget#resultSummary[resultState="success"] {{
    border-color: #86E5AA;
    background-color: {COLOR_SUCCESS_SOFT};
}}

QWidget#resultSummary[resultState="review"] {{
    border-color: {BRAND_200};
    background-color: {COLOR_PRIMARY_SOFT};
}}

QWidget#resultSummary[resultState="error"] {{
    border-color: #F3A2AA;
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
    background-color: {BRAND_100};
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
    background: #B8BFCE;
}}

QScrollBar::handle:vertical:hover {{
    background: #929AAF;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: transparent;
}}

QToolTip {{
    color: {COLOR_ON_DARK};
    background-color: {BRAND_900};
    border: 1px solid {BRAND_800};
    padding: 6px;
}}
"""

# Dark colors replace the same semantic roles used by the light stylesheet.
# A single-pass replacement prevents one mapped value from being replaced
# again when it happens to match another source color.
DARK_COLOR_REPLACEMENTS = {
    "#F7F8FC": "#0D1224",
    "#FFFFFF": "#171F38",
    "#F8FAFC": "#1D2744",
    "#F1F3FF": "#232E50",
    "#F0F2F8": "#11182E",
    "#4D566B": "#C1C7D6",
    "#4353C7": "#6879EA",
    "#3342A5": "#7F8DF0",
    "#27347F": "#5264D5",
    "#EEF2FF": "#202A55",
    "#E0E7FF": "#293665",
    "#16B8AE": "#2DD4C7",
    "#FCFDFF": "#FFFFFF",
    "#151A2D": "#F4F6FB",
    "#747D91": "#929AAF",
    "#D9DDE7": "#303A56",
    "#B8BFCE": "#46516F",
    "#A52432": "#FF9AA5",
    "#FFF0F1": "#3D171D",
    "#187A3F": "#76E39C",
    "#ECFDF3": "#123523",
    "#855B00": "#FFD36A",
    "#FFF8E5": "#3A2C0D",
    "#235F9D": "#86C7FF",
    "#EEF6FF": "#142D48",
    "#86E5AA": "#2D8A52",
    "#E9ECF7": "#1D2744",
    "#E1E5ED": "#252E47",
    "#F3A2AA": "#B24754",
    "#929AAF": "#46516F",
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
LIGHT_STYLESHEET = APPLICATION_STYLESHEET
STATIC_DARK_STYLESHEET = DARK_STYLESHEET


def _application_palette(mode: ThemeMode) -> QPalette:
    """Build a native Qt palette matching the active QSS theme."""
    dark = mode is ThemeMode.DARK
    colors = {
        "window": "#0D1224" if dark else "#F7F8FC",
        "surface": "#171F38" if dark else "#FFFFFF",
        "alternate": "#1D2744" if dark else "#F8FAFC",
        "text": "#F4F6FB" if dark else "#151A2D",
        "muted": "#929AAF" if dark else "#747D91",
        "disabled": "#666F85" if dark else "#A3A9B7",
        "primary": "#6879EA" if dark else "#4353C7",
        "primary_hover": "#7F8DF0" if dark else "#3342A5",
        "primary_pressed": "#5264D5" if dark else "#27347F",
        "primary_soft": "#202A55" if dark else "#EEF2FF",
        "on_primary": "#FFFFFF",
        "surface_hover": "#232E50" if dark else "#F1F3FF",
        "border": "#303A56" if dark else "#D9DDE7",
        "border_strong": "#46516F" if dark else "#B8BFCE",
        "danger": "#FF9AA5" if dark else "#A52432",
        "accent": "#2DD4C7" if dark else "#16B8AE",
        "sidebar": "#11182E" if dark else "#F0F2F8",
        "tooltip": "#11182E" if dark else "#1B2559",
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
    palette.setColor(QPalette.ColorRole.Shadow, QColor(colors["sidebar"]))
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
        QColor(colors["accent"]),
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
        stylesheet = (
            DARK_STYLESHEET
            if effective_mode is ThemeMode.DARK
            else LIGHT_STYLESHEET
        )
        if self.application.styleSheet() != stylesheet:
            self.application.setStyleSheet(stylesheet)
        else:
            # Re-polish native controls when the system re-emits its current
            # colour scheme without requiring a new stylesheet parse.
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
    manager = getattr(application, "_pdfsilo_theme_manager", None)
    if not isinstance(manager, ThemeManager):
        manager = ThemeManager(application)
        setattr(application, "_pdfsilo_theme_manager", manager)
    return manager


def apply_theme(
    application: QApplication,
    mode: ThemeMode | str = ThemeMode.SYSTEM,
) -> ThemeManager:
    """Apply typography and the requested application-wide appearance."""
    existing_manager = getattr(
        application,
        "_pdfsilo_theme_manager",
        None,
    )
    if not isinstance(existing_manager, ThemeManager):
        application.setStyle("Fusion")
    manager = theme_manager(application)
    manager.set_mode(mode)
    _apply_application_font(application)
    return manager

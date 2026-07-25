"""Cross-platform design tokens and stylesheet for the SafePDF desktop UI."""

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

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


APPLICATION_STYLESHEET = f"""
QWidget {{
    color: {COLOR_TEXT};
    font-size: {FONT_SIZE_BODY}pt;
}}

QMainWindow, QWidget#applicationContent, QWidget#applicationBody,
QWidget#homeContent, QScrollArea#homeScrollArea {{
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
    color: {COLOR_SURFACE};
    background-color: {COLOR_PRIMARY};
    border-radius: 9px;
    font-size: 14pt;
    font-weight: {FONT_WEIGHT_BOLD};
}}

QLabel#applicationTitleLabel {{
    color: {COLOR_SURFACE};
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
    color: {COLOR_SURFACE};
    background-color: #1D2939;
}}

QListWidget#navigationList::item:selected {{
    color: {COLOR_SURFACE};
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
    color: {COLOR_SURFACE};
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

QLabel#pdfPreviewImage {{
    color: {COLOR_TEXT_SUBTLE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE};
}}

QLabel#pdfPreviewStatus, QLabel#pageListStatus, QLabel#previewPageLabel {{
    color: {COLOR_TEXT_MUTED};
    background: transparent;
}}

QListView#pageListView, QListWidget#resultWarningList,
QListWidget#resultOutputList {{
    border: 1px solid {COLOR_BORDER};
    border-radius: {BORDER_RADIUS}px;
    background-color: {COLOR_SURFACE};
    outline: 0;
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
    color: {COLOR_SURFACE};
    border-color: {COLOR_PRIMARY};
    background-color: {COLOR_PRIMARY};
    font-weight: {FONT_WEIGHT_SEMIBOLD};
}}

QPushButton[primary="true"]:hover {{
    color: {COLOR_SURFACE};
    border-color: {COLOR_PRIMARY_HOVER};
    background-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton[primary="true"]:pressed {{
    background-color: {COLOR_PRIMARY_PRESSED};
}}

QPushButton#browseButton {{
    min-width: 88px;
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
    color: {COLOR_SURFACE};
    background-color: {COLOR_SIDEBAR};
    border: 1px solid #344054;
    padding: 6px;
}}
"""


def apply_theme(application: QApplication) -> None:
    """Apply SafePDF's platform-neutral style and a dependable UI font."""
    application.setStyle("Fusion")
    families = set(QFontDatabase.families())
    if "Segoe UI" in families:
        font = QFont("Segoe UI", FONT_SIZE_BODY)
    else:
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
        font.setPointSize(FONT_SIZE_BODY)
    application.setFont(font)
    application.setStyleSheet(APPLICATION_STYLESHEET)

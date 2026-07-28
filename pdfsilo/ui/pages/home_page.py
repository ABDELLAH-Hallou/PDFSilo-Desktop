"""Modern landing dashboard for the PDFSilo application shell."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pdfsilo.ui.pages.registry import PAGE_DEFINITIONS
from pdfsilo.ui.theme import SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL

POPULAR_TOOL_KEYS = (
    "merge",
    "split",
    "compress",
    "to_images",
    "encrypt",
    "reorder",
)

TOOL_MARKS = {
    "merge": "MG",
    "split": "SP",
    "compress": "CP",
    "to_images": "IM",
    "encrypt": "LK",
    "reorder": "PG",
}


class ToolCard(QFrame):
    """Compact, keyboard-accessible operation shortcut."""

    requested = Signal(str)

    def __init__(
        self,
        key: str,
        title: str,
        description: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.key = key
        self.setObjectName("toolCard")
        self.setMinimumHeight(154)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_MD, SPACE_MD, SPACE_MD, SPACE_MD)
        layout.setSpacing(SPACE_SM)

        top = QHBoxLayout()
        top.setSpacing(SPACE_SM)

        mark = QLabel(TOOL_MARKS.get(key, "PDF"), self)
        mark.setObjectName("toolIconLabel")
        mark.setFixedSize(42, 42)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title, self)
        title_label.setObjectName("toolTitleLabel")
        top.addWidget(mark)
        top.addWidget(title_label, 1)

        description_label = QLabel(description, self)
        description_label.setObjectName("toolDescriptionLabel")
        description_label.setWordWrap(True)

        open_button = QPushButton("Open tool  →", self)
        open_button.setObjectName("toolCardButton")
        open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        open_button.setAccessibleName(f"Open {title}")
        open_button.clicked.connect(lambda: self.requested.emit(self.key))

        layout.addLayout(top)
        layout.addWidget(description_label)
        layout.addStretch(1)
        layout.addWidget(open_button)


class HomePage(QWidget):
    """Landing dashboard with clear routes into common PDF workflows."""

    operationRequested = Signal(str)

    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        self.setObjectName("homePage")
        self._cards: list[ToolCard] = []
        self._column_count = 0

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setObjectName("homeScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget(scroll)
        content.setObjectName("homeContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACE_LG, SPACE_LG, SPACE_LG, SPACE_XL)
        layout.setSpacing(SPACE_LG)

        hero = QFrame(content)
        hero.setObjectName("homeHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(
            SPACE_XL,
            SPACE_XL,
            SPACE_XL,
            SPACE_XL,
        )
        hero_layout.setSpacing(SPACE_LG)

        copy = QWidget(hero)
        copy_layout = QVBoxLayout(copy)
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(SPACE_SM)

        eyebrow = QLabel("PRIVATE PDF TOOLKIT", copy)
        eyebrow.setObjectName("pageEyebrowLabel")

        title_label = QLabel(title, copy)
        title_label.setObjectName("pageTitleLabel")

        description_label = QLabel(
            "Merge, split, protect, and transform PDFs without uploading "
            "your documents.",
            copy,
        )
        description_label.setObjectName("pageDescriptionLabel")
        description_label.setWordWrap(True)
        description_label.setMaximumWidth(640)

        privacy_label = QLabel(
            "●  Files never leave this device",
            copy,
        )
        privacy_label.setObjectName("heroPrivacyLabel")

        copy_layout.addWidget(eyebrow)
        copy_layout.addWidget(title_label)
        copy_layout.addWidget(description_label)
        copy_layout.addWidget(privacy_label)

        quick_start = QPushButton("Merge PDFs", hero)
        quick_start.setObjectName("homePrimaryAction")
        quick_start.setProperty("primary", True)
        quick_start.setMinimumWidth(142)
        quick_start.setAccessibleName("Open Merge PDFs")
        quick_start.clicked.connect(lambda: self.operationRequested.emit("merge"))

        hero_layout.addWidget(copy, 1)
        hero_layout.addWidget(
            quick_start,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        section_header = QWidget(content)
        section_layout = QVBoxLayout(section_header)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(3)
        section_title = QLabel("Popular tools", section_header)
        section_title.setObjectName("sectionTitleLabel")
        section_description = QLabel(
            "Start a common workflow or choose any tool from the sidebar.",
            section_header,
        )
        section_description.setObjectName("sectionDescriptionLabel")
        section_layout.addWidget(section_title)
        section_layout.addWidget(section_description)

        self.card_grid = QGridLayout()
        self.card_grid.setContentsMargins(0, 0, 0, 0)
        self.card_grid.setHorizontalSpacing(SPACE_MD)
        self.card_grid.setVerticalSpacing(SPACE_MD)

        definitions = {definition.key: definition for definition in PAGE_DEFINITIONS}
        for key in POPULAR_TOOL_KEYS:
            definition = definitions[key]
            card = ToolCard(
                key,
                definition.title,
                definition.description,
                content,
            )
            card.requested.connect(self.operationRequested.emit)
            self._cards.append(card)

        layout.addWidget(hero)
        layout.addWidget(section_header)
        layout.addLayout(self.card_grid)
        layout.addStretch(1)

        scroll.setWidget(content)
        page_layout.addWidget(scroll)
        self._arrange_cards(3)

    def _arrange_cards(self, columns: int) -> None:
        if columns == self._column_count:
            return
        while self.card_grid.count():
            self.card_grid.takeAt(0)
        for index, card in enumerate(self._cards):
            self.card_grid.addWidget(
                card,
                index // columns,
                index % columns,
            )
        for column in range(columns):
            self.card_grid.setColumnStretch(column, 1)
        self._column_count = columns

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Keep cards readable when the main window becomes narrow."""
        super().resizeEvent(event)
        self._arrange_cards(3 if event.size().width() >= 900 else 2)


__all__ = ["HomePage", "ToolCard"]

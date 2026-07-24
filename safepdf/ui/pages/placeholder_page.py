"""Placeholder content used until operation forms are implemented."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from safepdf.ui.pages.registry import PageDefinition
from safepdf.ui.theme import SPACE_LG


class OperationPlaceholderPage(QWidget):
    """Identify a future operation page without implementing its form."""

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__()
        self.definition = definition
        self.setObjectName(f"{definition.key}Page")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_LG, SPACE_LG, SPACE_LG, SPACE_LG)
        layout.setSpacing(SPACE_LG)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(definition.title, self)
        title.setObjectName("pageTitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description = QLabel(definition.description, self)
        description.setObjectName("pageDescriptionLabel")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)

        availability = QLabel(
            "The operation form will be added in a later UI phase.",
            self,
        )
        availability.setObjectName("placeholderLabel")
        availability.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(availability)


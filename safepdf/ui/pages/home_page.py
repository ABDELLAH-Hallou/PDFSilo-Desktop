"""Home content for the SafePDF application shell."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from safepdf.ui.theme import SPACE_LG


class HomePage(QWidget):
    """Simple landing page shown when the desktop application starts."""

    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        self.setObjectName("homePage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_LG, SPACE_LG, SPACE_LG, SPACE_LG)
        layout.setSpacing(SPACE_LG)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title, self)
        title_label.setObjectName("pageTitleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description_label = QLabel(description, self)
        description_label.setObjectName("pageDescriptionLabel")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)

        privacy_label = QLabel(
            "All processing stays on this device.",
            self,
        )
        privacy_label.setObjectName("privacyLabel")
        privacy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addWidget(privacy_label)


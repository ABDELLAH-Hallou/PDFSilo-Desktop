"""Top-level SafePDF desktop window."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from safepdf.ui.metadata import WINDOW_TITLE
from safepdf.ui.resources import application_icon
from safepdf.ui.theme import SPACE_XXL

DEFAULT_WINDOW_WIDTH = 960
DEFAULT_WINDOW_HEIGHT = 640
MINIMUM_WINDOW_WIDTH = 720
MINIMUM_WINDOW_HEIGHT = 480


class MainWindow(QMainWindow):
    """Empty application shell populated with a Phase 5 placeholder."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(application_icon())
        self.setMinimumSize(MINIMUM_WINDOW_WIDTH, MINIMUM_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        content = QWidget(self)
        content.setObjectName("applicationContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(
            SPACE_XXL,
            SPACE_XXL,
            SPACE_XXL,
            SPACE_XXL,
        )
        layout.setSpacing(SPACE_XXL // 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("SafePDF", content)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "The desktop application structure is ready.",
            content,
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.setCentralWidget(content)


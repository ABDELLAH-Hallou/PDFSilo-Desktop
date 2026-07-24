"""Top-level SafePDF desktop application shell."""

from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from safepdf.ui.metadata import APPLICATION_VERSION, WINDOW_TITLE
from safepdf.ui.pages import (
    HomePage,
    OperationPlaceholderPage,
    PAGE_DEFINITIONS,
    PAGE_INDEX_BY_KEY,
)
from safepdf.ui.resources import application_icon
from safepdf.ui.theme import SPACE_LG, SPACE_MD, SPACE_SM

DEFAULT_WINDOW_WIDTH = 1080
DEFAULT_WINDOW_HEIGHT = 720
MINIMUM_WINDOW_WIDTH = 800
MINIMUM_WINDOW_HEIGHT = 540
SIDEBAR_WIDTH = 210

GEOMETRY_SETTING = "window/geometry"
STATE_SETTING = "window/state"
NAVIGATION_SETTING = "navigation/current_index"
PERSISTED_SETTING_KEYS = frozenset(
    {
        GEOMETRY_SETTING,
        STATE_SETTING,
        NAVIGATION_SETTING,
    }
)


class MainWindow(QMainWindow):
    """Application shell shared by all SafePDF operation screens."""

    def __init__(self, settings: QSettings | None = None) -> None:
        super().__init__()
        self.settings = settings if settings is not None else QSettings()
        self.selected_input_path: Path | None = None
        self._page_indexes = dict(PAGE_INDEX_BY_KEY)

        self.setObjectName("mainWindow")
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(application_icon())
        self.setMinimumSize(MINIMUM_WINDOW_WIDTH, MINIMUM_WINDOW_HEIGHT)

        self._create_actions()
        self._create_menus()
        self._create_content()
        self._create_status_bar()
        self._restore_settings()

    def _create_actions(self) -> None:
        self.open_action = QAction("Open PDF…", self)
        self.open_action.setObjectName("openAction")
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.setStatusTip("Choose a PDF file")
        self.open_action.triggered.connect(self.choose_input_file)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setObjectName("exitAction")
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.setStatusTip("Close SafePDF")
        self.exit_action.triggered.connect(self.close)

        self.home_action = QAction("Home", self)
        self.home_action.setObjectName("homeAction")
        self.home_action.setShortcut(QKeySequence("Ctrl+H"))
        self.home_action.setStatusTip("Show the home page")
        self.home_action.triggered.connect(lambda: self.navigate_to("home"))

        self.previous_page_action = QAction("Previous Page", self)
        self.previous_page_action.setObjectName("previousPageAction")
        self.previous_page_action.setShortcut(QKeySequence("Ctrl+Up"))
        self.previous_page_action.triggered.connect(self.select_previous_page)

        self.next_page_action = QAction("Next Page", self)
        self.next_page_action.setObjectName("nextPageAction")
        self.next_page_action.setShortcut(QKeySequence("Ctrl+Down"))
        self.next_page_action.triggered.connect(self.select_next_page)

        self.settings_action = QAction("Settings", self)
        self.settings_action.setObjectName("settingsAction")
        self.settings_action.setShortcut(QKeySequence("Ctrl+,"))
        self.settings_action.setStatusTip("Open application settings")
        self.settings_action.triggered.connect(self.show_settings_placeholder)

        self.about_action = QAction("About SafePDF", self)
        self.about_action.setObjectName("aboutAction")
        self.about_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        self.about_action.setStatusTip("About SafePDF")
        self.about_action.triggered.connect(self.show_about_dialog)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.setObjectName("fileMenu")
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        navigate_menu = self.menuBar().addMenu("&Navigate")
        navigate_menu.setObjectName("navigateMenu")
        navigate_menu.addAction(self.home_action)
        navigate_menu.addAction(self.previous_page_action)
        navigate_menu.addAction(self.next_page_action)

        tools_menu = self.menuBar().addMenu("&Tools")
        tools_menu.setObjectName("toolsMenu")
        tools_menu.addAction(self.settings_action)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.setObjectName("helpMenu")
        help_menu.addAction(self.about_action)

    def _create_content(self) -> None:
        root = QWidget(self)
        root.setObjectName("applicationContent")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._create_header())

        body = QWidget(root)
        body.setObjectName("applicationBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.navigation = QListWidget(body)
        self.navigation.setObjectName("navigationList")
        self.navigation.setAccessibleName("PDF operations")
        self.navigation.setFixedWidth(SIDEBAR_WIDTH)
        self.navigation.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.navigation.setUniformItemSizes(True)

        self.page_stack = QStackedWidget(body)
        self.page_stack.setObjectName("pageStack")

        for definition in PAGE_DEFINITIONS:
            item = QListWidgetItem(definition.label)
            item.setData(Qt.ItemDataRole.UserRole, definition.key)
            item.setToolTip(definition.description)
            self.navigation.addItem(item)

            if definition.key == "home":
                page = HomePage(definition.title, definition.description)
            else:
                page = OperationPlaceholderPage(definition)
            self.page_stack.addWidget(page)

        self.navigation.currentRowChanged.connect(
            self._on_navigation_changed
        )

        body_layout.addWidget(self.navigation)
        body_layout.addWidget(self.page_stack, 1)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

    def _create_header(self) -> QFrame:
        header = QFrame(self)
        header.setObjectName("applicationHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(SPACE_LG, SPACE_SM, SPACE_MD, SPACE_SM)
        layout.setSpacing(SPACE_SM)

        title = QLabel("SafePDF", header)
        title.setObjectName("applicationTitleLabel")
        layout.addWidget(title)
        layout.addStretch(1)

        settings_button = QToolButton(header)
        settings_button.setObjectName("settingsButton")
        settings_button.setDefaultAction(self.settings_action)
        settings_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextOnly
        )
        settings_button.setAutoRaise(True)

        help_button = QToolButton(header)
        help_button.setObjectName("helpButton")
        help_button.setDefaultAction(self.about_action)
        help_button.setText("Help")
        help_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        help_button.setAutoRaise(True)

        layout.addWidget(settings_button)
        layout.addWidget(help_button)
        return header

    def _create_status_bar(self) -> None:
        status_bar = self.statusBar()
        status_bar.setObjectName("globalStatusBar")
        status_bar.setSizeGripEnabled(True)

        self.output_label = QLabel("Output: —", status_bar)
        self.output_label.setObjectName("outputLocationLabel")
        self.output_label.setMinimumWidth(180)
        self.output_label.setMaximumWidth(360)

        self.progress_bar = QProgressBar(status_bar)
        self.progress_bar.setObjectName("globalProgressBar")
        self.progress_bar.setMinimumWidth(180)
        self.progress_bar.setMaximumWidth(260)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()

        status_bar.addPermanentWidget(self.output_label)
        status_bar.addPermanentWidget(self.progress_bar)
        status_bar.showMessage("Ready")

    def _restore_settings(self) -> None:
        geometry = self.settings.value(GEOMETRY_SETTING)
        if not (
            isinstance(geometry, QByteArray)
            and not geometry.isEmpty()
            and self.restoreGeometry(geometry)
        ):
            self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        state = self.settings.value(STATE_SETTING)
        if isinstance(state, QByteArray) and not state.isEmpty():
            self.restoreState(state)

        raw_index = self.settings.value(NAVIGATION_SETTING, 0)
        try:
            index = int(raw_index)
        except (TypeError, ValueError):
            index = 0
        if not 0 <= index < self.navigation.count():
            index = 0
        self.navigation.setCurrentRow(index)
        self.statusBar().showMessage("Ready")

    def _save_settings(self) -> None:
        # Deliberately persist only non-sensitive UI state. Passwords and file
        # contents have no path into this allowlisted settings contract.
        self.settings.setValue(GEOMETRY_SETTING, self.saveGeometry())
        self.settings.setValue(STATE_SETTING, self.saveState())
        self.settings.setValue(
            NAVIGATION_SETTING,
            self.navigation.currentRow(),
        )
        self.settings.sync()

    def _on_navigation_changed(self, index: int) -> None:
        if not 0 <= index < self.page_stack.count():
            return
        self.page_stack.setCurrentIndex(index)
        self.set_status(f"{PAGE_DEFINITIONS[index].label} selected.")

    def navigate_to(self, page_key: str) -> bool:
        """Select a page by its stable key, returning whether it exists."""
        index = self._page_indexes.get(page_key)
        if index is None:
            return False
        self.navigation.setCurrentRow(index)
        return True

    def select_previous_page(self) -> None:
        """Move to the previous navigation item."""
        self.navigation.setCurrentRow(
            max(0, self.navigation.currentRow() - 1)
        )

    def select_next_page(self) -> None:
        """Move to the next navigation item."""
        self.navigation.setCurrentRow(
            min(
                self.navigation.count() - 1,
                self.navigation.currentRow() + 1,
            )
        )

    def set_status(self, message: str, timeout_ms: int = 0) -> None:
        """Display a concise application-level status message."""
        self.statusBar().showMessage(message, timeout_ms)

    def set_progress(
        self,
        current: int,
        total: int,
        message: str | None = None,
    ) -> None:
        """Update and reveal the global progress control."""
        if total <= 0:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat("Working…")
        else:
            bounded_current = min(max(0, current), total)
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(bounded_current)
            self.progress_bar.setFormat(f"{bounded_current} / {total}")
        self.progress_bar.show()
        if message:
            self.set_status(message)

    def clear_progress(self) -> None:
        """Reset and hide the global progress control."""
        self.progress_bar.reset()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.hide()

    def set_output_location(self, output_path: Path | str | None) -> None:
        """Show the latest output location without persisting it."""
        if output_path is None:
            self.output_label.setText("Output: —")
            self.output_label.setToolTip("")
            return
        path_text = str(output_path)
        self.output_label.setText(f"Output: {path_text}")
        self.output_label.setToolTip(path_text)

    def choose_input_file(self) -> None:
        """Choose a PDF for a future operation screen."""
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF",
            "",
            "PDF documents (*.pdf);;All files (*)",
        )
        if selected:
            self.selected_input_path = Path(selected)
            self.set_status(f"Selected '{self.selected_input_path.name}'.")

    def show_settings_placeholder(self) -> None:
        """Report availability until the settings dialog is implemented."""
        self.set_status("Settings will be available in a later UI phase.")

    def show_about_dialog(self) -> None:
        """Display application identity and privacy information."""
        QMessageBox.about(
            self,
            "About SafePDF",
            (
                f"SafePDF {APPLICATION_VERSION}\n\n"
                "Privacy-first PDF tools. All processing stays on this device."
            ),
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """Persist allowlisted UI state before the window closes."""
        self._save_settings()
        super().closeEvent(event)


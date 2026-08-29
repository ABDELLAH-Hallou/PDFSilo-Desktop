"""Top-level PDFSilo desktop application shell."""

import logging
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QCloseEvent,
    QDesktopServices,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QStackedWidget,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from pdfsilo.ui.dialogs import AboutDialog, SettingsDialog, UpdateDialog
from pdfsilo.ui.metadata import WINDOW_TITLE
from pdfsilo.ui.pages import (
    OPERATION_PAGE_FACTORIES,
    PAGE_DEFINITIONS,
    PAGE_INDEX_BY_KEY,
    HomePage,
    OperationPage,
)
from pdfsilo.ui.preferences import (
    PREFERENCE_SETTING_KEYS,
    UiPreferences,
)
from pdfsilo.ui.resources import (
    application_icon,
    brand_logo_pixmap,
    sidebar_toggle_icon,
)
from pdfsilo.ui.theme import (
    SPACE_LG,
    SPACE_MD,
    SPACE_SM,
    SPACE_XS,
    ThemeMode,
    normalize_theme_mode,
    theme_manager,
)
from pdfsilo.ui.widgets import UpdateBanner
from pdfsilo.ui.workers import UpdateRunner
from pdfsilo.updater import UpdateInfo, check_for_update

log = logging.getLogger(__name__)

DEFAULT_WINDOW_WIDTH = 1240
DEFAULT_WINDOW_HEIGHT = 800
MINIMUM_WINDOW_WIDTH = 800
MINIMUM_WINDOW_HEIGHT = 540
SIDEBAR_WIDTH = 232

PAGE_ICONS = {
    "home": QStyle.StandardPixmap.SP_DesktopIcon,
    "merge": QStyle.StandardPixmap.SP_FileDialogNewFolder,
    "split": QStyle.StandardPixmap.SP_FileDialogDetailedView,
    "rotate": QStyle.StandardPixmap.SP_BrowserReload,
    "extract_pages": QStyle.StandardPixmap.SP_FileDialogListView,
    "compress": QStyle.StandardPixmap.SP_ArrowDown,
    "encrypt": QStyle.StandardPixmap.SP_DialogApplyButton,
    "decrypt": QStyle.StandardPixmap.SP_DialogResetButton,
    "watermark": QStyle.StandardPixmap.SP_FileDialogContentsView,
    "extract_images": QStyle.StandardPixmap.SP_DialogSaveButton,
    "to_images": QStyle.StandardPixmap.SP_FileIcon,
    "reorder": QStyle.StandardPixmap.SP_ArrowUp,
    "add_images": QStyle.StandardPixmap.SP_DialogOpenButton,
    "images_to_pdf": QStyle.StandardPixmap.SP_DriveFDIcon,
}

GEOMETRY_SETTING = "window/geometry"
STATE_SETTING = "window/state"
NAVIGATION_SETTING = "navigation/current_index"
THEME_SETTING = "appearance/theme"
PERSISTED_SETTING_KEYS = frozenset(
    {
        GEOMETRY_SETTING,
        STATE_SETTING,
        NAVIGATION_SETTING,
        THEME_SETTING,
        *PREFERENCE_SETTING_KEYS,
    }
)


def _standard_shortcut(
    standard_key: QKeySequence.StandardKey,
    fallback: str,
) -> QKeySequence:
    """Return a usable shortcut even under a headless Qt platform plug-in."""
    bindings = QKeySequence.keyBindings(standard_key)
    return bindings[0] if bindings else QKeySequence(fallback)


class MainWindow(QMainWindow):
    """Application shell shared by all PDFSilo operation screens."""

    def __init__(self, settings: QSettings | None = None) -> None:
        super().__init__()
        self.settings = settings if settings is not None else QSettings()
        self.selected_input_path: Path | None = None
        self._page_indexes = dict(PAGE_INDEX_BY_KEY)
        self._running_pages: set[OperationPage] = set()
        self._settings_dialog: SettingsDialog | None = None
        self._about_dialog: AboutDialog | None = None
        self._update_dialog: UpdateDialog | None = None
        self._update_check_manual = False
        self._preferences = UiPreferences.from_settings(self.settings)
        self._theme_mode = normalize_theme_mode(
            self.settings.value(
                THEME_SETTING,
                ThemeMode.SYSTEM.value,
            )
        )
        application = QApplication.instance()
        assert application is not None
        self._theme_manager = theme_manager(application)
        self._theme_manager.set_mode(self._theme_mode)

        self.setObjectName("mainWindow")
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(application_icon())
        self.setMinimumSize(MINIMUM_WINDOW_WIDTH, MINIMUM_WINDOW_HEIGHT)

        self._create_actions()
        self._create_menus()
        self._create_content()
        self._create_status_bar()
        self._update_runner = UpdateRunner(parent=self)
        self._update_runner.succeeded.connect(self._update_check_succeeded)
        self._update_runner.failed.connect(self._update_check_failed)
        self._update_runner.finished.connect(self._update_check_finished)
        self._update_runner.runningChanged.connect(
            self.check_updates_action.setDisabled
        )
        self._theme_manager.themeChanged.connect(self._theme_assets_changed)
        self._theme_assets_changed(
            self._theme_mode.value,
            self._theme_manager.effective_mode.value,
        )
        self._restore_settings()
        QTimer.singleShot(0, self._maybe_check_automatically)

    def _create_actions(self) -> None:
        self.open_action = QAction("Open PDF…", self)
        self.open_action.setObjectName("openAction")
        self.open_action.setShortcut(
            _standard_shortcut(QKeySequence.StandardKey.Open, "Ctrl+O")
        )
        self.open_action.setStatusTip("Choose a PDF file")
        self.open_action.triggered.connect(self.choose_input_file)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setObjectName("exitAction")
        self.exit_action.setShortcut(
            _standard_shortcut(QKeySequence.StandardKey.Quit, "Ctrl+Q")
        )
        self.exit_action.setStatusTip("Close PDFSilo")
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

        self.toggle_sidebar_action = QAction("Hide Sidebar", self)
        self.toggle_sidebar_action.setObjectName("toggleSidebarAction")
        self.toggle_sidebar_action.setShortcut(QKeySequence("Ctrl+B"))
        self.toggle_sidebar_action.setCheckable(True)
        self.toggle_sidebar_action.setChecked(True)
        self.toggle_sidebar_action.setIcon(sidebar_toggle_icon(True))
        self.toggle_sidebar_action.setStatusTip("Show or hide the operation sidebar")
        self.toggle_sidebar_action.toggled.connect(self._set_sidebar_visible)

        self.settings_action = QAction("Settings", self)
        self.settings_action.setObjectName("settingsAction")
        self.settings_action.setShortcut(QKeySequence("Ctrl+,"))
        self.settings_action.setStatusTip("Open application settings")
        self.settings_action.triggered.connect(self.show_settings_dialog)

        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setObjectName("themeActionGroup")
        self.theme_action_group.setExclusive(True)
        self.theme_actions: dict[ThemeMode, QAction] = {}
        for mode, label in (
            (ThemeMode.SYSTEM, "System Default"),
            (ThemeMode.LIGHT, "Light"),
            (ThemeMode.DARK, "Dark"),
        ):
            action = QAction(label, self.theme_action_group)
            action.setObjectName(f"{mode.value}ThemeAction")
            action.setCheckable(True)
            action.setChecked(mode is self._theme_mode)
            action.setData(mode.value)
            action.triggered.connect(
                lambda _checked=False, selected=mode: self.set_theme_mode(selected)
            )
            self.theme_actions[mode] = action

        self.about_action = QAction("About PDFSilo", self)
        self.about_action.setObjectName("aboutAction")
        self.about_action.setShortcut(
            _standard_shortcut(QKeySequence.StandardKey.HelpContents, "F1")
        )
        self.about_action.setStatusTip("About PDFSilo")
        self.about_action.triggered.connect(self.show_about_dialog)

        self.check_updates_action = QAction("Check for Updates…", self)
        self.check_updates_action.setObjectName("checkUpdatesAction")
        self.check_updates_action.setStatusTip(
            "Check GitHub for a newer PDFSilo release"
        )
        self.check_updates_action.triggered.connect(
            lambda: self.start_update_check(manual=True)
        )

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
        navigate_menu.addSeparator()
        navigate_menu.addAction(self.toggle_sidebar_action)

        tools_menu = self.menuBar().addMenu("&Tools")
        tools_menu.setObjectName("toolsMenu")
        tools_menu.addAction(self.settings_action)
        appearance_menu = tools_menu.addMenu("&Appearance")
        appearance_menu.setObjectName("appearanceMenu")
        appearance_menu.addActions(self.theme_action_group.actions())

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.setObjectName("helpMenu")
        help_menu.addAction(self.check_updates_action)
        help_menu.addSeparator()
        help_menu.addAction(self.about_action)

    def _create_content(self) -> None:
        root = QWidget(self)
        root.setObjectName("applicationContent")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._create_header())
        self.update_banner = UpdateBanner(root)
        self.update_banner.updateRequested.connect(self.show_update_dialog)
        self.update_banner.releaseNotesRequested.connect(self.open_update_release_notes)
        self.update_banner.skipRequested.connect(self.skip_update_version)
        root_layout.addWidget(self.update_banner)

        body = QWidget(root)
        body.setObjectName("applicationBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = QWidget(body)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        sidebar_layout.addWidget(self._create_brand_panel(self.sidebar))

        section_label = QLabel("PDF TOOLS", self.sidebar)
        section_label.setObjectName("navigationSectionLabel")
        section_label.setContentsMargins(
            SPACE_LG,
            SPACE_MD,
            SPACE_SM,
            SPACE_XS,
        )
        sidebar_layout.addWidget(section_label)

        self.navigation = QListWidget(self.sidebar)
        self.navigation.setObjectName("navigationList")
        self.navigation.setAccessibleName("PDF operations")
        self.navigation.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.navigation.setUniformItemSizes(True)
        self.navigation.setIconSize(QSize(18, 18))
        self.navigation.setSpacing(1)

        self.page_stack = QStackedWidget(body)
        self.page_stack.setObjectName("pageStack")

        for definition in PAGE_DEFINITIONS:
            item = QListWidgetItem(definition.label)
            item.setData(Qt.ItemDataRole.UserRole, definition.key)
            item.setToolTip(definition.description)
            item.setIcon(
                self.style().standardIcon(
                    PAGE_ICONS.get(
                        definition.key,
                        QStyle.StandardPixmap.SP_FileIcon,
                    )
                )
            )
            self.navigation.addItem(item)

            if definition.key == "home":
                page = HomePage(definition.title, definition.description)
                page.operationRequested.connect(self.navigate_to)
            else:
                page_factory = OPERATION_PAGE_FACTORIES[definition.key]
                page = page_factory(definition)
                self._connect_operation_page(page)
            self.page_stack.addWidget(page)

        self.navigation.currentRowChanged.connect(self._on_navigation_changed)

        sidebar_layout.addWidget(self.navigation, 1)
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.page_stack, 1)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

    def _connect_operation_page(self, page: OperationPage) -> None:
        """Connect one operation screen to application-wide shell state."""
        page.set_input_previews_enabled(self._preferences.show_input_previews)
        page.set_confirm_overwrite(self._preferences.confirm_overwrite)
        page.statusChanged.connect(self.set_status)
        page.progressChanged.connect(self.set_progress)
        page.progressCleared.connect(self.clear_progress)
        page.outputChanged.connect(self.set_output_location)
        page.runningChanged.connect(
            lambda running, current_page=page: self._operation_running_changed(
                current_page,
                running,
            )
        )

    def _operation_running_changed(
        self,
        page: OperationPage,
        running: bool,
    ) -> None:
        """Prevent navigation and input replacement during active work."""
        if running:
            self._running_pages.add(page)
        else:
            self._running_pages.discard(page)

        can_navigate = not self._running_pages
        self.navigation.setEnabled(can_navigate)
        self.open_action.setEnabled(can_navigate)
        self.home_action.setEnabled(can_navigate)
        self.previous_page_action.setEnabled(can_navigate)
        self.next_page_action.setEnabled(can_navigate)

    def _create_header(self) -> QFrame:
        header = QFrame(self)
        header.setObjectName("applicationHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(SPACE_LG, SPACE_XS, SPACE_MD, SPACE_XS)
        layout.setSpacing(SPACE_SM)

        sidebar_button = QToolButton(header)
        sidebar_button.setObjectName("sidebarButton")
        sidebar_button.setDefaultAction(self.toggle_sidebar_action)
        sidebar_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        sidebar_button.setAccessibleName("Show or hide sidebar")
        layout.addWidget(sidebar_button)

        context = QWidget(header)
        context.setObjectName("headerContext")
        context_layout = QVBoxLayout(context)
        context_layout.setContentsMargins(0, 0, 0, 0)
        context_layout.setSpacing(1)

        self.header_title = QLabel("Home", context)
        self.header_title.setObjectName("headerPageTitleLabel")
        self.header_description = QLabel(
            "Your local PDF workspace",
            context,
        )
        self.header_description.setObjectName("headerDescriptionLabel")
        context_layout.addWidget(self.header_title)
        context_layout.addWidget(self.header_description)

        layout.addWidget(context)
        layout.addStretch(1)

        local_badge = QLabel("●  Processing stays local", header)
        local_badge.setObjectName("localBadge")
        local_badge.setAccessibleName("All processing stays on this device")
        layout.addWidget(local_badge)

        settings_button = QToolButton(header)
        settings_button.setObjectName("settingsButton")
        settings_button.setDefaultAction(self.settings_action)
        settings_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
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

    def _create_brand_panel(self, parent: QWidget) -> QFrame:
        """Create the persistent product identity in the sidebar."""
        panel = QFrame(parent)
        panel.setObjectName("brandPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(SPACE_LG, SPACE_MD, SPACE_LG, SPACE_MD)
        layout.setSpacing(2)

        self.brand_logo_label = QLabel(panel)
        self.brand_logo_label.setObjectName("brandLogoLabel")
        self.brand_logo_label.setAccessibleName("PDFSilo")
        self.brand_logo_label.setFixedSize(184, 58)
        self.brand_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Private PDF workspace", panel)
        subtitle.setObjectName("brandSubtitle")
        layout.addWidget(self.brand_logo_label)
        layout.addWidget(subtitle)
        return panel

    def _theme_assets_changed(
        self,
        _requested_mode: str,
        effective_mode: str,
    ) -> None:
        """Keep identity assets legible when the effective theme changes."""
        dark = effective_mode == ThemeMode.DARK.value
        icon = application_icon(dark=dark)
        self.setWindowIcon(icon)
        application = QApplication.instance()
        if application is not None:
            application.setWindowIcon(icon)
        if hasattr(self, "brand_logo_label"):
            self.brand_logo_label.setProperty("darkMode", dark)
            self.brand_logo_label.setPixmap(
                brand_logo_pixmap(
                    dark=dark,
                    size=QSize(168, 48),
                )
            )
            style = self.brand_logo_label.style()
            style.unpolish(self.brand_logo_label)
            style.polish(self.brand_logo_label)
        if self._about_dialog is not None:
            self._about_dialog.set_dark_mode(dark)

    def _set_sidebar_visible(self, visible: bool) -> None:
        """Expose more workspace without changing persisted preferences."""
        if hasattr(self, "sidebar"):
            self.sidebar.setVisible(visible)
        self.toggle_sidebar_action.setIcon(sidebar_toggle_icon(visible))
        self.toggle_sidebar_action.setText(
            "Hide Sidebar" if visible else "Show Sidebar"
        )
        self.toggle_sidebar_action.setStatusTip(
            "Hide the operation sidebar" if visible else "Show the operation sidebar"
        )

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
        geometry_restored = False
        if self._preferences.restore_window:
            geometry = self.settings.value(GEOMETRY_SETTING)
            geometry_restored = (
                isinstance(geometry, QByteArray)
                and not geometry.isEmpty()
                and self.restoreGeometry(geometry)
            )
        if not geometry_restored:
            self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        if self._preferences.restore_window:
            state = self.settings.value(STATE_SETTING)
            if isinstance(state, QByteArray) and not state.isEmpty():
                self.restoreState(state)

        raw_index = (
            self.settings.value(NAVIGATION_SETTING, 0)
            if self._preferences.reopen_last_tool
            else 0
        )
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
        if self._preferences.restore_window:
            self.settings.setValue(GEOMETRY_SETTING, self.saveGeometry())
            self.settings.setValue(STATE_SETTING, self.saveState())
        else:
            self.settings.remove(GEOMETRY_SETTING)
            self.settings.remove(STATE_SETTING)
        if self._preferences.reopen_last_tool:
            self.settings.setValue(
                NAVIGATION_SETTING,
                self.navigation.currentRow(),
            )
        else:
            self.settings.remove(NAVIGATION_SETTING)
        self.settings.setValue(THEME_SETTING, self._theme_mode.value)
        self._preferences.save(self.settings)
        self.settings.sync()

    def _on_navigation_changed(self, index: int) -> None:
        if not 0 <= index < self.page_stack.count():
            return
        self.page_stack.setCurrentIndex(index)
        definition = PAGE_DEFINITIONS[index]
        self.header_title.setText(definition.label)
        self.header_description.setText(definition.description)
        self.set_status(f"{definition.label} selected.")

    def navigate_to(self, page_key: str) -> bool:
        """Select a page by its stable key, returning whether it exists."""
        index = self._page_indexes.get(page_key)
        if index is None:
            return False
        self.navigation.setCurrentRow(index)
        return True

    def select_previous_page(self) -> None:
        """Move to the previous navigation item."""
        self.navigation.setCurrentRow(max(0, self.navigation.currentRow() - 1))

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
        if self._preferences.open_output_folder:
            path = Path(output_path)
            folder = path if path.is_dir() else path.parent
            if folder.is_dir() and not QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(folder))
            ):
                self.set_status(
                    f"Saved output, but could not open '{folder}'.",
                    5_000,
                )

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
            current_page = self.page_stack.currentWidget()
            if isinstance(current_page, OperationPage):
                input_picker = getattr(current_page, "input_picker", None)
                if input_picker is not None and not input_picker.allows_multiple:
                    input_picker.set_path(self.selected_input_path)
            self.set_status(f"Selected '{self.selected_input_path.name}'.")

    def set_theme_mode(self, mode: ThemeMode | str) -> None:
        """Apply and persist a non-sensitive appearance preference."""
        self._theme_mode = normalize_theme_mode(mode)
        self._theme_manager.set_mode(self._theme_mode)
        self.theme_actions[self._theme_mode].setChecked(True)
        self.settings.setValue(THEME_SETTING, self._theme_mode.value)
        self.settings.sync()
        if self._settings_dialog is not None:
            self._settings_dialog.set_theme_mode(self._theme_mode)
        label = self.theme_actions[self._theme_mode].text()
        self.set_status(f"{label} theme selected.")

    def show_settings_dialog(self) -> None:
        """Show the reusable, non-modal application settings dialog."""
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog(
                self._theme_mode,
                self,
                self._preferences,
            )
            self._settings_dialog.themeModeChanged.connect(self.set_theme_mode)
            self._settings_dialog.preferencesChanged.connect(self.set_ui_preferences)
        else:
            self._settings_dialog.set_theme_mode(self._theme_mode)
            self._settings_dialog.set_preferences(self._preferences)
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def set_ui_preferences(self, preferences: UiPreferences) -> None:
        """Apply and persist safe workflow and startup preferences."""
        if not isinstance(preferences, UiPreferences):
            return
        automatic_checks_were_enabled = self._preferences.check_updates_automatically
        self._preferences = preferences
        self._preferences.save(self.settings)
        if not preferences.restore_window:
            self.settings.remove(GEOMETRY_SETTING)
            self.settings.remove(STATE_SETTING)
        if not preferences.reopen_last_tool:
            self.settings.remove(NAVIGATION_SETTING)
        self.settings.sync()

        for index in range(self.page_stack.count()):
            page = self.page_stack.widget(index)
            if isinstance(page, OperationPage):
                page.set_input_previews_enabled(preferences.show_input_previews)
                page.set_confirm_overwrite(preferences.confirm_overwrite)
        if self._settings_dialog is not None:
            self._settings_dialog.set_preferences(preferences)
        self.set_status("Settings updated.", 3_000)
        if (
            preferences.check_updates_automatically
            and not automatic_checks_were_enabled
        ):
            QTimer.singleShot(0, self._maybe_check_automatically)

    def _automatic_update_check_due(self) -> bool:
        if not self._preferences.check_updates_automatically:
            return False
        raw_timestamp = self._preferences.last_update_check
        if not raw_timestamp:
            return True
        try:
            checked_at = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
            if checked_at.tzinfo is None:
                checked_at = checked_at.replace(tzinfo=UTC)
        except ValueError:
            return True
        return datetime.now(UTC) - checked_at >= timedelta(hours=24)

    def _maybe_check_automatically(self) -> None:
        if self._automatic_update_check_due():
            self.start_update_check(manual=False)

    def start_update_check(self, *, manual: bool = True) -> bool:
        """Start one explicit or opt-in update check in the background."""
        if self._update_runner.is_running():
            if manual:
                self.set_status("An update check is already running.", 3_000)
            return False
        self._update_check_manual = manual
        if manual:
            self.set_status("Checking for PDFSilo updates…")
        return self._update_runner.start(check_for_update)

    def _record_update_check(self) -> None:
        self._preferences = replace(
            self._preferences,
            last_update_check=datetime.now(UTC).isoformat(),
        )
        self._preferences.save(self.settings)
        self.settings.sync()
        if self._settings_dialog is not None:
            self._settings_dialog.set_preferences(self._preferences)

    def _update_check_succeeded(self, result: object) -> None:
        self._record_update_check()
        if result is None:
            if self._update_check_manual:
                QMessageBox.information(
                    self,
                    "PDFSilo Updates",
                    "You already have the latest PDFSilo version.",
                )
            return
        if not isinstance(result, UpdateInfo):
            self._update_check_failed(
                "The update service returned an invalid response."
            )
            return
        if (
            not self._update_check_manual
            and result.version == self._preferences.skipped_update_version
        ):
            return
        if self._update_check_manual:
            self.show_update_dialog(result)
        else:
            self.update_banner.show_update(result)
            self.set_status(f"PDFSilo {result.version} is available.", 5_000)

    def _update_check_failed(self, message: str) -> None:
        self._record_update_check()
        if self._update_check_manual:
            QMessageBox.warning(
                self,
                "Could Not Check for Updates",
                message,
            )
        else:
            log.info("Automatic update check failed: %s", message)

    def _update_check_finished(self) -> None:
        if self._update_check_manual:
            self.set_status("Update check finished.", 3_000)
        self._update_check_manual = False

    def show_update_dialog(self, info: object) -> None:
        if not isinstance(info, UpdateInfo):
            return
        if self._update_dialog is not None:
            self._update_dialog.close()
        self._update_dialog = UpdateDialog(info, self)
        self._update_dialog.show()
        self._update_dialog.raise_()
        self._update_dialog.activateWindow()

    def open_update_release_notes(self, info: object) -> bool:
        if not isinstance(info, UpdateInfo):
            return False
        return QDesktopServices.openUrl(QUrl(info.release_notes_url))

    def skip_update_version(self, version: str) -> None:
        self._preferences = replace(
            self._preferences,
            skipped_update_version=version,
        )
        self._preferences.save(self.settings)
        self.settings.sync()
        if self._settings_dialog is not None:
            self._settings_dialog.set_preferences(self._preferences)
        self.set_status(f"PDFSilo {version} will be skipped.", 4_000)

    def show_about_dialog(self) -> None:
        """Display useful product, privacy, and runtime information."""
        if self._about_dialog is None:
            self._about_dialog = AboutDialog(self)
        self._about_dialog.set_dark_mode(
            self._theme_manager.effective_mode is ThemeMode.DARK
        )
        self._about_dialog.show()
        self._about_dialog.raise_()
        self._about_dialog.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Persist allowlisted UI state before the window closes."""
        self._update_runner.cancel()
        if self._update_dialog is not None:
            self._update_dialog.runner.cancel()
        self._save_settings()
        super().closeEvent(event)

"""Non-sensitive desktop preferences and their persistent keys."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings

RESTORE_WINDOW_SETTING = "startup/restore_window"
REOPEN_LAST_TOOL_SETTING = "startup/reopen_last_tool"
SHOW_INPUT_PREVIEWS_SETTING = "workflow/show_input_previews"
CONFIRM_OVERWRITE_SETTING = "workflow/confirm_overwrite"
OPEN_OUTPUT_FOLDER_SETTING = "workflow/open_output_folder"
CHECK_UPDATES_AUTOMATICALLY_SETTING = "updates/check_automatically"
LAST_UPDATE_CHECK_SETTING = "updates/last_check_timestamp"
SKIPPED_UPDATE_VERSION_SETTING = "updates/skipped_version"


@dataclass(frozen=True, slots=True)
class UiPreferences:
    """Safe, non-sensitive behavior preferences for the desktop UI."""

    restore_window: bool = True
    reopen_last_tool: bool = True
    show_input_previews: bool = True
    confirm_overwrite: bool = True
    open_output_folder: bool = False
    check_updates_automatically: bool = False
    last_update_check: str = ""
    skipped_update_version: str = ""

    @classmethod
    def from_settings(cls, settings: QSettings) -> "UiPreferences":
        """Load preferences with conservative defaults."""
        defaults = cls()
        return cls(
            restore_window=settings.value(
                RESTORE_WINDOW_SETTING,
                defaults.restore_window,
                type=bool,
            ),
            reopen_last_tool=settings.value(
                REOPEN_LAST_TOOL_SETTING,
                defaults.reopen_last_tool,
                type=bool,
            ),
            show_input_previews=settings.value(
                SHOW_INPUT_PREVIEWS_SETTING,
                defaults.show_input_previews,
                type=bool,
            ),
            confirm_overwrite=settings.value(
                CONFIRM_OVERWRITE_SETTING,
                defaults.confirm_overwrite,
                type=bool,
            ),
            open_output_folder=settings.value(
                OPEN_OUTPUT_FOLDER_SETTING,
                defaults.open_output_folder,
                type=bool,
            ),
            check_updates_automatically=settings.value(
                CHECK_UPDATES_AUTOMATICALLY_SETTING,
                defaults.check_updates_automatically,
                type=bool,
            ),
            last_update_check=str(
                settings.value(
                    LAST_UPDATE_CHECK_SETTING,
                    defaults.last_update_check,
                )
                or ""
            ),
            skipped_update_version=str(
                settings.value(
                    SKIPPED_UPDATE_VERSION_SETTING,
                    defaults.skipped_update_version,
                )
                or ""
            ),
        )

    def save(self, settings: QSettings) -> None:
        """Persist only allowlisted, non-sensitive preference values."""
        settings.setValue(RESTORE_WINDOW_SETTING, self.restore_window)
        settings.setValue(REOPEN_LAST_TOOL_SETTING, self.reopen_last_tool)
        settings.setValue(
            SHOW_INPUT_PREVIEWS_SETTING,
            self.show_input_previews,
        )
        settings.setValue(
            CONFIRM_OVERWRITE_SETTING,
            self.confirm_overwrite,
        )
        settings.setValue(
            OPEN_OUTPUT_FOLDER_SETTING,
            self.open_output_folder,
        )
        settings.setValue(
            CHECK_UPDATES_AUTOMATICALLY_SETTING,
            self.check_updates_automatically,
        )
        if self.last_update_check:
            settings.setValue(
                LAST_UPDATE_CHECK_SETTING,
                self.last_update_check,
            )
        else:
            settings.remove(LAST_UPDATE_CHECK_SETTING)
        if self.skipped_update_version:
            settings.setValue(
                SKIPPED_UPDATE_VERSION_SETTING,
                self.skipped_update_version,
            )
        else:
            settings.remove(SKIPPED_UPDATE_VERSION_SETTING)


PREFERENCE_SETTING_KEYS = frozenset(
    {
        RESTORE_WINDOW_SETTING,
        REOPEN_LAST_TOOL_SETTING,
        SHOW_INPUT_PREVIEWS_SETTING,
        CONFIRM_OVERWRITE_SETTING,
        OPEN_OUTPUT_FOLDER_SETTING,
        CHECK_UPDATES_AUTOMATICALLY_SETTING,
        LAST_UPDATE_CHECK_SETTING,
        SKIPPED_UPDATE_VERSION_SETTING,
    }
)

__all__ = [
    "CHECK_UPDATES_AUTOMATICALLY_SETTING",
    "CONFIRM_OVERWRITE_SETTING",
    "LAST_UPDATE_CHECK_SETTING",
    "OPEN_OUTPUT_FOLDER_SETTING",
    "PREFERENCE_SETTING_KEYS",
    "REOPEN_LAST_TOOL_SETTING",
    "RESTORE_WINDOW_SETTING",
    "SHOW_INPUT_PREVIEWS_SETTING",
    "SKIPPED_UPDATE_VERSION_SETTING",
    "UiPreferences",
]

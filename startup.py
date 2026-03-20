"""Manage Windows startup registry entry for MeetLink."""

import logging
import sys
import winreg

log = logging.getLogger(__name__)

REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "MeetLink"


def _get_exe_path() -> str:
    """Return the path to the running executable."""
    return sys.executable


def is_startup_enabled() -> bool:
    """Check if MeetLink is registered to run at Windows startup."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        log.warning("Failed to read startup registry key", exc_info=True)
        return False


def set_startup_enabled(enabled: bool) -> None:
    """Add or remove MeetLink from Windows startup."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_exe_path())
                log.info("Added MeetLink to Windows startup")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    log.info("Removed MeetLink from Windows startup")
                except FileNotFoundError:
                    pass
    except OSError:
        log.error("Failed to update startup registry key", exc_info=True)

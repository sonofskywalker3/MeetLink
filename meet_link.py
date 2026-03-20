"""MeetLink — system tray app for one-time Calendly scheduling links."""

import json
import logging
import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import pystray
from dotenv import load_dotenv, set_key
from PIL import Image, ImageDraw, ImageFont

from calendly import (
    EventType,
    create_single_use_link,
    get_current_user,
    list_event_types,
)
from clipboard import copy_html_to_clipboard
from ui import CustomLinkWindow, SettingsWindow, TokenDialog

log = logging.getLogger(__name__)

ENV_FILE = Path("~/Documents/Projects/.env").expanduser()
CONFIG_FILE = Path("~/.meetlink/config.json").expanduser()
ENV_VAR_NAME = "CALENDLY_API_TOKEN"


class MeetLinkApp:
    """System tray application for generating Calendly links."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.token: str = ""
        self.user: object = None  # calendly.UserInfo
        self.event_types: list[EventType] = []
        self.default_event_type: EventType | None = None
        self.icon: pystray.Icon | None = None

    def run(self) -> None:
        self.token = self._get_token()
        if not self.token:
            sys.exit(1)

        try:
            self.user = get_current_user(self.token)
            self.event_types = list_event_types(self.token, self.user.uri)
        except Exception as exc:
            messagebox.showerror("MeetLink", f"Failed to load event types:\n{exc}")
            sys.exit(1)

        if not self.event_types:
            messagebox.showerror("MeetLink", "No active event types found in Calendly.")
            sys.exit(1)

        self._load_config()

        log.info("Loaded %d event types", len(self.event_types))
        for et in self.event_types:
            log.info("  %s (%d min, options=%s)", et.name, et.duration, et.duration_options)
        log.info("Default: %s", self.default_event_type.name if self.default_event_type else "None")

        self.icon = self._create_tray_icon()
        threading.Thread(target=self.icon.run, daemon=True).start()

        self.root.mainloop()

    # -- Token management --

    def _get_token(self) -> str:
        load_dotenv(ENV_FILE)
        token = os.environ.get(ENV_VAR_NAME)
        if token:
            return token

        dialog = TokenDialog(self.root)
        self.root.wait_window(dialog)
        token = dialog.result

        if token:
            set_key(str(ENV_FILE), ENV_VAR_NAME, token)
            os.environ[ENV_VAR_NAME] = token

        return token or ""

    # -- Config persistence --

    def _load_config(self) -> None:
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text())
            uri = data.get("default_event_type_uri")
            if uri:
                self.default_event_type = next(
                    (et for et in self.event_types if et.uri == uri), None
                )

        if not self.default_event_type:
            self.default_event_type = self.event_types[0]
            self._save_config()

    def _save_config(self) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if self.default_event_type:
            data["default_event_type_uri"] = self.default_event_type.uri
        CONFIG_FILE.write_text(json.dumps(data, indent=2))

    # -- Tray icon --

    def _create_tray_icon(self) -> pystray.Icon:
        tooltip = "MeetLink — One-time meeting link"

        menu = pystray.Menu(
            pystray.MenuItem(
                "New Link", self._on_new_link, default=True, visible=False
            ),
            pystray.MenuItem("Custom Link...", self._on_custom_link),
            pystray.MenuItem("Settings...", self._on_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._on_exit),
        )
        return pystray.Icon("MeetLink", _create_icon_image(), tooltip, menu)

    # -- Tray actions --

    def _on_new_link(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        if not self.default_event_type:
            icon.notify("No default event type. Right-click → Settings.", "MeetLink")
            return

        try:
            url = create_single_use_link(self.token, self.default_event_type.uri)
            html = f'<a href="{url}">{self.default_event_type.name}</a>'
            copy_html_to_clipboard(html, f"{self.default_event_type.name}: {url}")
            icon.notify("One-time meeting link copied!", "MeetLink")
        except Exception as exc:
            log.error("Failed to create link: %s", exc)
            icon.notify(f"Error: {exc}", "MeetLink")

    def _on_custom_link(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self._show_custom_link)

    def _show_custom_link(self) -> None:
        log.info("Opening custom link window")

        def on_copy(event_type: EventType, overrides: dict | None) -> bool:
            log.info("Custom link copy: %s, overrides=%s", event_type.name, overrides)
            try:
                url = create_single_use_link(
                    self.token, event_type.uri, overrides,
                )
                html = f'<a href="{url}">{event_type.name}</a>'
                copy_html_to_clipboard(html, f"{event_type.name}: {url}")
                if self.icon:
                    self.icon.notify("One-time meeting link copied!", "MeetLink")
                return True
            except Exception as exc:
                messagebox.showerror("MeetLink", f"Error creating link:\n{exc}")
                return False

        assert self.user is not None
        CustomLinkWindow(
            self.root, self.event_types, self.user.timezone, on_copy,
        )

    def _on_settings(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self._show_settings)

    def _show_settings(self) -> None:
        def on_save(event_type: EventType) -> None:
            self.default_event_type = event_type
            self._save_config()
            if self.icon:
                self.icon.title = "MeetLink — One-time meeting link"

        SettingsWindow(self.root, self.event_types, self.default_event_type, on_save)

    def _on_exit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        icon.stop()
        self.root.after(0, self.root.quit)


def _create_icon_image() -> Image.Image:
    """Generate the tray icon: blue rounded square with white M."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([2, 2, 62, 62], radius=10, fill="#0069FF")
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except OSError:
        font = ImageFont.load_default()
    draw.text((32, 34), "M", fill="white", font=font, anchor="mm")
    return img


LOG_FILE = Path("~/.meetlink/meetlink.log").expanduser()


def main() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, mode="w"),
        ],
    )
    app = MeetLinkApp()
    app.run()


if __name__ == "__main__":
    main()

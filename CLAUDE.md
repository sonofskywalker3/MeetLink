# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

MeetLink is a Windows system tray app for generating one-time Calendly scheduling links. Left-click the tray icon to instantly copy a link; right-click for custom event type selection or settings. Links are copied as HTML hyperlinks ready to paste into Zammad tickets.

## Running

```bash
uv run meet_link.py
```

No build step, no tests.

## Environment

- Requires `CALENDLY_API_TOKEN` — loaded from `~/Documents/Projects/.env` via `python-dotenv`. If missing, a GUI dialog prompts and saves it on first run.
- App settings (default event type) stored in `~/.meetlink/config.json`
- Windows-only: uses `ctypes.windll` for clipboard (CF_HTML + CF_UNICODETEXT) and `pystray` for system tray

## Architecture

- `meet_link.py` — `MeetLinkApp` class: tray icon setup, orchestration, config persistence. Tray runs in a daemon thread; tkinter mainloop on the main thread.
- `calendly.py` — API client: `get_current_user_uri()`, `list_event_types()`, `create_single_use_link()`. All event types fetched dynamically at startup.
- `clipboard.py` — `copy_html_to_clipboard()`: Windows clipboard with CF_HTML header + CF_UNICODETEXT fallback
- `ui.py` — tkinter dialogs: `TokenDialog`, `CustomLinkWindow`, `SettingsWindow`. All are `tk.Toplevel` windows parented to a hidden root.

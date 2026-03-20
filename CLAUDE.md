# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

MeetLink generates a one-time Calendly scheduling link ("Meet with Jeff") and copies it to the Windows clipboard as an HTML hyperlink, ready to paste into Zammad tickets.

## Running

```bash
uv run meet_link.py
```

No build step, no tests. Single-file script.

## Environment

- Requires `CALENDLY_API_TOKEN` — loaded from `~/Documents/Projects/.env` via `python-dotenv`
- Windows-only: uses `ctypes.windll` for clipboard access (CF_HTML + CF_UNICODETEXT)

## Architecture

Single module (`meet_link.py`) with three functions:
- `create_single_use_link()` — POST to Calendly `/scheduling_links` API
- `copy_html_to_clipboard()` — Windows clipboard with HTML Format header + plaintext fallback
- `main()` — orchestrates: load env, create link, copy, log

The Calendly event type URI is hardcoded as `MEET_WITH_JEFF_URI` (Jeff's "Meet with Jeff" event type).

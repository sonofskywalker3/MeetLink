# MeetLink

Windows system tray app for generating one-time Calendly scheduling links. Left-click the tray icon to instantly copy a link; right-click for custom options or settings.

Links are copied as HTML hyperlinks, ready to paste into email clients, ticketing systems, or any rich-text editor.

## Features

- **One-click links** — Left-click the tray icon to generate and copy a single-use scheduling link using your default event type
- **Custom links** — Choose event type, duration, and limit availability (days/hours) for a specific link
- **HTML clipboard** — Links are copied as clickable `<a>` tags with a plaintext fallback
- **Run at startup** — Optional Windows startup via Settings

## Setup

1. Download `MeetLink.exe` from the [latest release](https://github.com/sonofskywalker3/MeetLink/releases/latest)
2. Run it — on first launch, you'll be guided to create a [Calendly Personal Access Token](https://calendly.com/integrations/api_webhooks)
3. Paste your token and click OK

The token is saved to your local `.env` file and never leaves your machine.

## Usage

| Action | Result |
|---|---|
| **Left-click** tray icon | Copy a one-time link using your default event type |
| **Right-click** → Custom Link | Pick event type, duration, and availability window |
| **Right-click** → Settings | Set default event type, toggle startup |
| **Right-click** → Exit | Quit MeetLink |

## Building from source

Requires [uv](https://docs.astral.sh/uv/):

```bash
# Run directly
uv run meet_link.py

# Build standalone exe
uv add --dev pyinstaller
uv run pyinstaller --onefile --noconsole --name MeetLink meet_link.py
# Output: dist/MeetLink.exe
```

## License

MIT

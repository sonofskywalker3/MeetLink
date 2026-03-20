"""Generate a one-time Calendly 'Meet with Jeff' link and copy to clipboard as a formatted hyperlink."""

import ctypes
import logging
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

log = logging.getLogger(__name__)

ENV_FILE = Path("~/Documents/Projects/.env").expanduser()
ENV_VAR_NAME = "CALENDLY_API_TOKEN"
MEET_WITH_JEFF_URI = (
    "https://api.calendly.com/event_types/31d28f5b-7018-4a6a-b0bb-eb30b57af007"
)
LINK_TEXT = "Meet with Jeff"


def create_single_use_link(token: str) -> str:
    """Create a single-use Calendly scheduling link."""
    resp = requests.post(
        "https://api.calendly.com/scheduling_links",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "max_event_count": 1,
            "owner": MEET_WITH_JEFF_URI,
            "owner_type": "EventType",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["resource"]["booking_url"]


def copy_html_to_clipboard(html: str, plaintext: str) -> None:
    """Copy HTML and plaintext fallback to the Windows clipboard."""
    header_template = (
        "Version:0.9\r\n"
        "StartHTML:{start_html:010d}\r\n"
        "EndHTML:{end_html:010d}\r\n"
        "StartFragment:{start_frag:010d}\r\n"
        "EndFragment:{end_frag:010d}\r\n"
    )
    dummy_header = header_template.format(
        start_html=0, end_html=0, start_frag=0, end_frag=0
    )
    prefix = "<html><body>\r\n<!--StartFragment-->"
    suffix = "<!--EndFragment-->\r\n</body></html>"

    start_html = len(dummy_header.encode("utf-8"))
    start_frag = start_html + len(prefix.encode("utf-8"))
    end_frag = start_frag + len(html.encode("utf-8"))
    end_html = end_frag + len(suffix.encode("utf-8"))

    cf_html_payload = (
        header_template.format(
            start_html=start_html,
            end_html=end_html,
            start_frag=start_frag,
            end_frag=end_frag,
        )
        + prefix
        + html
        + suffix
    )

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    # Set proper 64-bit return/arg types for Windows API
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]

    CF_UNICODETEXT = 13
    CF_HTML = user32.RegisterClipboardFormatW("HTML Format")
    GMEM_MOVEABLE = 0x0002

    if not user32.OpenClipboard(0):
        raise OSError("Cannot open clipboard")

    try:
        user32.EmptyClipboard()

        # HTML format
        html_bytes = cf_html_payload.encode("utf-8") + b"\x00"
        h_html = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(html_bytes))
        p_html = kernel32.GlobalLock(h_html)
        ctypes.memmove(p_html, html_bytes, len(html_bytes))
        kernel32.GlobalUnlock(h_html)
        user32.SetClipboardData(CF_HTML, h_html)

        # Plaintext fallback
        text_bytes = plaintext.encode("utf-16-le") + b"\x00\x00"
        h_text = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
        p_text = kernel32.GlobalLock(h_text)
        ctypes.memmove(p_text, text_bytes, len(text_bytes))
        kernel32.GlobalUnlock(h_text)
        user32.SetClipboardData(CF_UNICODETEXT, h_text)
    finally:
        user32.CloseClipboard()


def get_token() -> str:
    """Load the Calendly API token from env, prompting and saving if missing."""
    load_dotenv(ENV_FILE)
    token = os.environ.get(ENV_VAR_NAME)
    if token:
        return token

    log.info("No %s found in %s", ENV_VAR_NAME, ENV_FILE)
    token = input("Paste your Calendly API token: ").strip()
    if not token:
        log.error("No token provided.")
        sys.exit(1)

    set_key(str(ENV_FILE), ENV_VAR_NAME, token)
    os.environ[ENV_VAR_NAME] = token
    log.info("Token saved to %s", ENV_FILE)
    return token


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    token = get_token()

    log.info("Creating single-use scheduling link...")
    try:
        url = create_single_use_link(token)
    except requests.RequestException as exc:
        log.error("Calendly API error: %s", exc)
        sys.exit(1)

    html = f'<a href="{url}">{LINK_TEXT}</a>'
    copy_html_to_clipboard(html, f"{LINK_TEXT}: {url}")

    log.info("Copied to clipboard: %s", LINK_TEXT)
    log.info("Link: %s", url)
    log.info("Paste into Zammad to insert formatted link.")


if __name__ == "__main__":
    main()

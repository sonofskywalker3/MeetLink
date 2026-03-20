"""Windows clipboard operations for HTML and plaintext content."""

import ctypes


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
        if not h_html:
            raise MemoryError("GlobalAlloc failed for HTML clipboard data")
        p_html = kernel32.GlobalLock(h_html)
        ctypes.memmove(p_html, html_bytes, len(html_bytes))
        kernel32.GlobalUnlock(h_html)
        user32.SetClipboardData(CF_HTML, h_html)

        # Plaintext fallback
        text_bytes = plaintext.encode("utf-16-le") + b"\x00\x00"
        h_text = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
        if not h_text:
            raise MemoryError("GlobalAlloc failed for text clipboard data")
        p_text = kernel32.GlobalLock(h_text)
        ctypes.memmove(p_text, text_bytes, len(text_bytes))
        kernel32.GlobalUnlock(h_text)
        user32.SetClipboardData(CF_UNICODETEXT, h_text)
    finally:
        user32.CloseClipboard()

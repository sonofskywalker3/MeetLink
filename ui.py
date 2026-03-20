"""Tkinter UI dialogs for MeetLink."""

import tkinter as tk
from tkinter import messagebox, ttk

from calendly import EventType


class TokenDialog(tk.Toplevel):
    """Prompt for Calendly API token on first run."""

    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.result: str | None = None

        self.title("MeetLink - Setup")
        self.geometry("450x150")
        self.resizable(False, False)
        self._center()

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Enter your Calendly API token:").pack(anchor="w")

        self.token_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=self.token_var, width=50, show="*")
        entry.pack(fill="x", pady=(5, 10))
        entry.focus_set()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(
            side="right"
        )

        self.bind("<Return>", lambda _: self._on_ok())
        self.bind("<Escape>", lambda _: self._on_cancel())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.grab_set()

    def _center(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 450) // 2
        y = (self.winfo_screenheight() - 150) // 2
        self.geometry(f"+{x}+{y}")

    def _on_ok(self) -> None:
        token = self.token_var.get().strip()
        if token:
            self.result = token
            self.destroy()
        else:
            messagebox.showwarning("MeetLink", "Please enter a token.", parent=self)

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


class CustomLinkWindow(tk.Toplevel):
    """Pick an event type and copy a one-time link."""

    def __init__(
        self,
        parent: tk.Tk,
        event_types: list[EventType],
        on_copy: "callable[[EventType], bool]",
    ) -> None:
        super().__init__(parent)
        self.event_types = event_types
        self.on_copy = on_copy

        self.title("MeetLink - Custom Link")
        self.geometry("380x130")
        self.resizable(False, False)
        self._center()

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Event type:").pack(anchor="w")

        self.display_names = [
            f"{et.name} ({et.duration} min)" for et in event_types
        ]
        self.combo_var = tk.StringVar()
        combo = ttk.Combobox(
            frame,
            textvariable=self.combo_var,
            values=self.display_names,
            state="readonly",
            width=45,
        )
        combo.pack(fill="x", pady=(5, 10))
        if self.display_names:
            combo.current(0)

        self.copy_btn = ttk.Button(frame, text="Copy Link", command=self._on_copy)
        self.copy_btn.pack(side="right")

        self.bind("<Escape>", lambda _: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.lift()
        self.focus_force()

    def _center(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 380) // 2
        y = (self.winfo_screenheight() - 130) // 2
        self.geometry(f"+{x}+{y}")

    def _on_copy(self) -> None:
        idx = self.display_names.index(self.combo_var.get())
        event_type = self.event_types[idx]
        self.copy_btn.configure(text="Creating...", state="disabled")
        self.update()

        success = self.on_copy(event_type)
        if success:
            self.destroy()
        else:
            self.copy_btn.configure(text="Copy Link", state="normal")


class SettingsWindow(tk.Toplevel):
    """Configure default event type for left-click."""

    def __init__(
        self,
        parent: tk.Tk,
        event_types: list[EventType],
        current_default: EventType | None,
        on_save: "callable[[EventType], None]",
    ) -> None:
        super().__init__(parent)
        self.event_types = event_types
        self.on_save = on_save

        self.title("MeetLink - Settings")
        self.geometry("380x130")
        self.resizable(False, False)
        self._center()

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Default event type (left-click):").pack(anchor="w")

        self.display_names = [
            f"{et.name} ({et.duration} min)" for et in event_types
        ]
        self.combo_var = tk.StringVar()
        combo = ttk.Combobox(
            frame,
            textvariable=self.combo_var,
            values=self.display_names,
            state="readonly",
            width=45,
        )
        combo.pack(fill="x", pady=(5, 10))

        default_idx = 0
        if current_default:
            default_idx = next(
                (i for i, et in enumerate(event_types) if et.uri == current_default.uri),
                0,
            )
        if self.display_names:
            combo.current(default_idx)

        ttk.Button(frame, text="Save", command=self._on_save).pack(side="right")

        self.bind("<Escape>", lambda _: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.lift()
        self.focus_force()

    def _center(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 380) // 2
        y = (self.winfo_screenheight() - 130) // 2
        self.geometry(f"+{x}+{y}")

    def _on_save(self) -> None:
        idx = self.display_names.index(self.combo_var.get())
        self.on_save(self.event_types[idx])
        self.destroy()

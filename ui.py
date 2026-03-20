"""Tkinter UI dialogs for MeetLink."""

import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import messagebox, ttk

from calendly import EventType
from startup import is_startup_enabled

WEEKDAY_LABELS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
WEEKDAY_API_NAMES = (
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
)


def _build_time_list() -> list[str]:
    """Half-hour increments from 6:00 AM to 9:00 PM."""
    times = []
    for h in range(6, 22):
        for m in (0, 30):
            display_h = h % 12 or 12
            suffix = "AM" if h < 12 else "PM"
            times.append(f"{display_h}:{m:02d} {suffix}")
    return times


def _to_24h(time_str: str) -> str:
    """Convert '9:00 AM' to '09:00'."""
    return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")


TIMES = _build_time_list()


CALENDLY_TOKEN_URL = "https://calendly.com/integrations/api_webhooks"


class TokenDialog(tk.Toplevel):
    """Prompt for Calendly API token on first run."""

    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.result: str | None = None

        self.title("MeetLink - Setup")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="MeetLink needs a Calendly Personal Access Token.",
            font=("", 10, "bold"),
        ).pack(anchor="w")

        instructions = ttk.Label(
            frame,
            text=(
                "1. Click the link below to open Calendly Integrations\n"
                "2. Under Personal Access Tokens, click Create New Token\n"
                "3. Copy the token and paste it here"
            ),
            justify="left",
        )
        instructions.pack(anchor="w", pady=(6, 4))

        link = ttk.Label(
            frame,
            text="Open Calendly Integrations page",
            foreground="blue",
            cursor="hand2",
        )
        link.pack(anchor="w", pady=(0, 10))
        link.bind(
            "<Button-1>",
            lambda _: webbrowser.open(CALENDLY_TOKEN_URL),
        )

        ttk.Label(frame, text="Personal Access Token:").pack(anchor="w")
        self.token_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=self.token_var, width=55, show="*")
        entry.pack(fill="x", pady=(2, 10))
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

        self.update_idletasks()
        w = self.winfo_reqwidth() + 20
        h = self.winfo_reqheight() + 10
        self._center(w, h)

    def _center(self, w: int, h: int) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

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
    """Create a one-time link with custom duration and availability."""

    def __init__(
        self,
        parent: tk.Tk,
        event_types: list[EventType],
        user_timezone: str,
        on_copy: "callable[[EventType, dict | None], bool]",
    ) -> None:
        super().__init__(parent)
        self.event_types = event_types
        self.user_timezone = user_timezone
        self.on_copy = on_copy
        self.title("MeetLink - Custom Link")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        # -- Event type --
        ttk.Label(frame, text="Event type:").pack(anchor="w")
        self.et_display = [f"{et.name} ({et.duration} min)" for et in event_types]
        self.et_var = tk.StringVar()
        self.et_combo = ttk.Combobox(
            frame, textvariable=self.et_var, values=self.et_display,
            state="readonly", width=45,
        )
        self.et_combo.pack(fill="x", pady=(2, 8))
        self.et_combo.current(0)
        self.et_combo.bind("<<ComboboxSelected>>", self._on_event_type_changed)

        # -- Duration checkboxes --
        ttk.Label(frame, text="Duration:").pack(anchor="w")
        self.dur_frame = ttk.Frame(frame)
        self.dur_frame.pack(anchor="w", pady=(2, 8))
        self.dur_vars: dict[int, tk.BooleanVar] = {}
        self._build_duration_checkboxes()

        # -- Limit availability toggle --
        self.limit_avail_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, text="Limit availability",
            variable=self.limit_avail_var, command=self._toggle_availability,
        ).pack(anchor="w", pady=(4, 4))

        # -- Availability controls (hidden by default) --
        self.avail_frame = ttk.LabelFrame(frame, text="Availability", padding=8)

        days_frame = ttk.Frame(self.avail_frame)
        days_frame.pack(anchor="w")
        self.day_vars: dict[str, tk.BooleanVar] = {}
        for i, day in enumerate(WEEKDAY_LABELS):
            var = tk.BooleanVar(value=(i < 5))  # Mon-Fri pre-checked
            ttk.Checkbutton(days_frame, text=day, variable=var).grid(
                row=0, column=i, padx=2,
            )
            self.day_vars[day] = var

        time_frame = ttk.Frame(self.avail_frame)
        time_frame.pack(anchor="w", pady=(6, 0))
        ttk.Label(time_frame, text="From:").pack(side="left")
        self.from_var = tk.StringVar(value="9:00 AM")
        ttk.Combobox(
            time_frame, textvariable=self.from_var, values=TIMES,
            state="readonly", width=10,
        ).pack(side="left", padx=(4, 12))
        ttk.Label(time_frame, text="To:").pack(side="left")
        self.to_var = tk.StringVar(value="5:00 PM")
        ttk.Combobox(
            time_frame, textvariable=self.to_var, values=TIMES,
            state="readonly", width=10,
        ).pack(side="left", padx=4)

        # -- Copy button --
        self.copy_btn = ttk.Button(frame, text="Copy Link", command=self._on_copy)
        self.copy_btn.pack(side="right", pady=(10, 0))

        self._center_auto()
        self.bind("<Escape>", lambda _: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.lift()
        self.focus_force()

    def _center_auto(self) -> None:
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_duration_checkboxes(self) -> None:
        for widget in self.dur_frame.winfo_children():
            widget.destroy()
        self.dur_vars.clear()

        idx = self.et_display.index(self.et_var.get())
        et = self.event_types[idx]
        options = et.duration_options or (et.duration,)
        for i, dur in enumerate(options):
            label = f"{dur} min" if dur < 60 else f"{dur // 60} hr"
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(self.dur_frame, text=label, variable=var).grid(
                row=0, column=i, padx=4,
            )
            self.dur_vars[dur] = var

    def _on_event_type_changed(self, _event: tk.Event) -> None:
        self._build_duration_checkboxes()
        self._center_auto()

    def _toggle_availability(self) -> None:
        if self.limit_avail_var.get():
            self.avail_frame.pack(fill="x", pady=(0, 4), before=self.copy_btn)
        else:
            self.avail_frame.pack_forget()
        self._center_auto()

    def _build_overrides(self) -> dict | None:
        overrides: dict = {}

        # Duration — only override if not all options are checked
        selected = [dur for dur, var in self.dur_vars.items() if var.get()]
        all_options = list(self.dur_vars.keys())
        if not selected:
            selected = all_options  # must have at least one
        if sorted(selected) != sorted(all_options):
            overrides["duration_options"] = sorted(selected)
            overrides["duration"] = selected[0]

        # Availability override
        if self.limit_avail_var.get():
            from_time = _to_24h(self.from_var.get())
            to_time = _to_24h(self.to_var.get())
            rules = []
            for i, day in enumerate(WEEKDAY_LABELS):
                if self.day_vars[day].get():
                    rules.append({
                        "type": "wday",
                        "wday": WEEKDAY_API_NAMES[i],
                        "intervals": [{"from": from_time, "to": to_time}],
                    })
            if rules:
                overrides["availability_rule"] = {
                    "rules": rules,
                    "timezone": self.user_timezone,
                }

        return overrides or None

    def _on_copy(self) -> None:
        idx = self.et_display.index(self.et_var.get())
        event_type = self.event_types[idx]
        share_override = self._build_overrides()

        self.copy_btn.configure(text="Creating...", state="disabled")
        self.update()

        success = self.on_copy(event_type, share_override)
        if success:
            self.destroy()
        else:
            self.copy_btn.configure(text="Copy Link", state="normal")


class SettingsWindow(tk.Toplevel):
    """Configure default event type and startup behavior."""

    def __init__(
        self,
        parent: tk.Tk,
        event_types: list[EventType],
        current_default: EventType | None,
        on_save: "callable[[EventType, bool], None]",
    ) -> None:
        super().__init__(parent)
        self.event_types = event_types
        self.on_save = on_save

        self.title("MeetLink - Settings")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Default event type (left-click):").pack(anchor="w")

        self.display_names = [
            f"{et.name} ({et.duration} min)" for et in event_types
        ]
        self.combo_var = tk.StringVar()
        combo = ttk.Combobox(
            frame, textvariable=self.combo_var,
            values=self.display_names, state="readonly", width=45,
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

        self.startup_var = tk.BooleanVar(value=is_startup_enabled())
        ttk.Checkbutton(
            frame, text="Run at Windows startup",
            variable=self.startup_var,
        ).pack(anchor="w", pady=(0, 10))

        ttk.Button(frame, text="Save", command=self._on_save).pack(side="right")

        self.bind("<Escape>", lambda _: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.lift()
        self.focus_force()

        self.update_idletasks()
        w = max(self.winfo_reqwidth() + 20, 380)
        h = self.winfo_reqheight() + 10
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_save(self) -> None:
        idx = self.display_names.index(self.combo_var.get())
        self.on_save(self.event_types[idx], self.startup_var.get())
        self.destroy()

"""Virtual calculator keypad with state-driven theme and event bus."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pyqalculate_gui.event_bus import EXPRESSION_SUBMITTED, EventBus
from pyqalculate_gui.theme import LIGHT, ButtonStyle, Theme

# (label, action_type, value, style_key)
_ButtonDef = tuple[str, str, str, str]

BUTTON_DEFS: list[list[_ButtonDef]] = [
    [
        ("AC", "clear", "", "action"),
        ("DEL", "backspace", "", "action"),
        ("(", "insert", "(", "op"),
        (")", "insert", ")", "op"),
        ("÷", "insert", "/", "op"),
    ],
    [
        ("7", "insert", "7", "digit"),
        ("8", "insert", "8", "digit"),
        ("9", "insert", "9", "digit"),
        ("×", "insert", "*", "op"),
        ("x²", "insert", "^2", "op"),
    ],
    [
        ("4", "insert", "4", "digit"),
        ("5", "insert", "5", "digit"),
        ("6", "insert", "6", "digit"),
        ("−", "insert", "-", "op"),
        ("√", "insert", "sqrt(", "func"),
    ],
    [
        ("1", "insert", "1", "digit"),
        ("2", "insert", "2", "digit"),
        ("3", "insert", "3", "digit"),
        ("+", "insert", "+", "op"),
        ("xʸ", "insert", "^", "op"),
    ],
    [
        ("0", "insert", "0", "digit"),
        (".", "insert", ".", "digit"),
        ("EXP", "insert", "E", "digit"),
        ("±", "negate", "", "op"),
        ("=", "submit", "", "equals"),
    ],
    [
        ("sin", "insert", "sin(", "func"),
        ("cos", "insert", "cos(", "func"),
        ("tan", "insert", "tan(", "func"),
        ("ln", "insert", "ln(", "func"),
        ("log", "insert", "log(", "func"),
    ],
]

_STYLE_KEYS = {"digit", "op", "func", "action", "equals"}


def _style_for_button(
    theme: Theme, style_key: str
) -> ButtonStyle:
    """Return ButtonStyle for a key, defaulting to digit."""
    if style_key not in _STYLE_KEYS:
        style_key = "digit"
    return getattr(theme, f"keypad_{style_key}")


class KeypadWidget(ttk.Frame):
    """Virtual calculator keypad with grid layout.

    Emits events via EventBus:
        keypad_insert(value)   – insert text at cursor
        keypad_clear           – clear expression
        keypad_backspace       – delete character before cursor
        keypad_negate          – negate expression
        EXPRESSION_SUBMITTED   – evaluate expression
    """

    def __init__(
        self,
        parent: tk.Misc,
        theme: Theme = LIGHT,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._event_bus = event_bus
        self._buttons: dict[str, tk.Button] = {}
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        for row_idx, row in enumerate(BUTTON_DEFS):
            self.rowconfigure(row_idx, weight=1)
            for col_idx, (label, action, value, style_key) in enumerate(row):
                self.columnconfigure(col_idx, weight=1)

                style = _style_for_button(self._theme, style_key)
                btn = tk.Button(
                    self,
                    text=label,
                    font=style.font,
                    bg=style.bg,
                    fg=style.fg,
                    activebackground=style.hover_bg,
                    relief=tk.FLAT,
                    borderwidth=0,
                    highlightthickness=0,
                    cursor="hand2",
                    takefocus=False,
                    command=lambda a=action, v=value: self._on_button(a, v),
                )
                btn.grid(
                    row=row_idx,
                    column=col_idx,
                    sticky="nsew",
                    padx=1,
                    pady=1,
                )
                self._buttons[label] = btn

                btn.bind(
                    "<Enter>",
                    lambda e, b=btn, h=style.hover_bg: b.config(bg=h),
                )
                btn.bind(
                    "<Leave>",
                    lambda e, b=btn, c=style.bg: b.config(bg=c),
                )

    # ------------------------------------------------------------------
    # Event dispatch
    # ------------------------------------------------------------------

    def _on_button(self, action: str, value: str) -> None:
        if self._event_bus is None:
            return
        if action == "insert":
            self._event_bus.emit("keypad_insert", value)
        elif action == "clear":
            self._event_bus.emit("keypad_clear")
        elif action == "backspace":
            self._event_bus.emit("keypad_backspace")
        elif action == "negate":
            self._event_bus.emit("keypad_negate")
        elif action == "submit":
            self._event_bus.emit(EXPRESSION_SUBMITTED, "")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_theme(self, theme: Theme) -> None:
        """Update theme for all buttons."""
        self._theme = theme
        for label, btn in self._buttons.items():
            for row in BUTTON_DEFS:
                for l, _, _, style_key in row:
                    if l == label:
                        style = _style_for_button(theme, style_key)
                        btn.config(
                            bg=style.bg,
                            fg=style.fg,
                            font=style.font,
                            activebackground=style.hover_bg,
                        )

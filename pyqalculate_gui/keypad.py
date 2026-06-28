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

# Dropdown menu items for function buttons: {button_label: [(menu_label, insert_string), ...]}
# Left-click inserts the primary function; right-click shows alternatives.
_DROPDOWN_MAP: dict[str, list[tuple[str, str]]] = {
    "sin": [
        ("asin", "asin("),
        ("sinh", "sinh("),
        ("asinh", "asinh("),
    ],
    "cos": [
        ("acos", "acos("),
        ("cosh", "cosh("),
        ("acosh", "acosh("),
    ],
    "tan": [
        ("atan", "atan("),
        ("tanh", "tanh("),
        ("atanh", "atanh("),
    ],
    "√": [
        ("∛ (cbrt)", "cbrt("),
    ],
    "ln": [
        ("log", "log("),
        ("log₂", "log2("),
        ("log₁₀", "log10("),
    ],
    "log": [
        ("log₂", "log2("),
        ("log₁₀", "log10("),
    ],
    "x²": [
        ("x³", "^3"),
    ],
    "xʸ": [
        ("x^(1/y)", "^(1/)"),
    ],
}

_STYLE_KEYS = {"digit", "op", "func", "action", "equals"}


def _darken(hex_color: str, factor: float = 0.8) -> str:
    """Return a darker version of *hex_color* (e.g. '#aabbcc')."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


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
        self._buttons: dict[str, tk.Button | tk.Menubutton] = {}
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _create_dropdown_button(
        self,
        parent: tk.Misc,
        label: str,
        style: ButtonStyle,
        action: str,
        value: str,
        menu_items: list[tuple[str, str]],
    ) -> tk.Menubutton:
        """Create a Menubutton with dropdown menu for related functions.

        Left-click inserts the primary function.  Right-click shows a dropdown
        menu with alternative functions.
        """
        btn = tk.Menubutton(
            parent,
            text=label,
            font=style.font,
            bg=style.bg,
            fg=style.fg,
            activebackground=_darken(style.bg),
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            takefocus=False,
        )

        # Left-click inserts primary function.
        # Return "break" to prevent the default Menubutton menu posting.
        btn.bind(
            "<Button-1>",
            lambda e, a=action, v=value: (self._on_button(a, v), "break")[-1],
        )

        # Build dropdown menu with alternative functions.
        menu = tk.Menu(btn, tearoff=0)
        for menu_label, insert_str in menu_items:
            menu.add_command(
                label=menu_label,
                command=lambda s=insert_str: self._on_button("insert", s),
            )
        btn.config(menu=menu)

        # Right-click shows the dropdown menu.
        btn.bind(
            "<Button-3>",
            lambda e, m=menu: m.post(e.x_root, e.y_root),
        )

        return btn

    def _build_ui(self) -> None:
        for row_idx, row in enumerate(BUTTON_DEFS):
            self.rowconfigure(row_idx, weight=1)
            for col_idx, (label, action, value, style_key) in enumerate(row):
                self.columnconfigure(col_idx, weight=1)

                style = _style_for_button(self._theme, style_key)

                if label in _DROPDOWN_MAP:
                    btn = self._create_dropdown_button(
                        self, label, style, action, value, _DROPDOWN_MAP[label]
                    )
                else:
                    btn = tk.Button(
                        self,
                        text=label,
                        font=style.font,
                        bg=style.bg,
                        fg=style.fg,
                        activebackground=_darken(style.bg),
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
                            activebackground=_darken(style.bg),
                        )

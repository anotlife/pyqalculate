"""Virtual keypad widget for PyQalculate GUI.

Provides an on-screen button grid with:
- Digits 0-9 and decimal point
- Arithmetic operators (+, -, *, /, ^)
- Scientific functions (sin, cos, tan, log, ln, sqrt, etc.)
- Constants (pi, e)
- Variables (ans, x, y, z)
- Parentheses, clear, backspace, and equals
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


# Button definition: (label, insert_text, tooltip, style_tag)
# insert_text is None for action buttons (clear, backspace, equals)
# style_tag groups buttons visually: "digit", "op", "func", "const", "var", "action", "equals"
_ButtonDef = tuple[str, str | None, str, str]
_BUTTON_DEFS: list[list[_ButtonDef]] = [
    # Row 0: Trig functions + log/ln
    [
        ("sin",  "sin(",  "Sine",           "func"),
        ("cos",  "cos(",  "Cosine",         "func"),
        ("tan",  "tan(",  "Tangent",        "func"),
        ("log",  "log(",  "Log base 10",    "func"),
        ("ln",   "ln(",   "Natural log",    "func"),
    ],
    # Row 1: More functions + digits 7-8
    [
        ("\u221a", "sqrt(", "Square root",   "func"),
        ("x\u00b2", "^2",  "Square",         "func"),
        ("x\u207b\u00b9", "^(-1)", "Reciprocal", "func"),
        ("7",    "7",      "Digit 7",        "digit"),
        ("8",    "8",      "Digit 8",        "digit"),
    ],
    # Row 2: Constants + abs + digits 9,6
    [
        ("\u03c0", "pi",   "Pi (3.14159\u2026)",  "const"),
        ("e",    "e",      "Euler\u2019s number",  "const"),
        ("|x|",  "abs(",   "Absolute value",       "func"),
        ("9",    "9",      "Digit 9",              "digit"),
        ("6",    "6",      "Digit 6",              "digit"),
    ],
    # Row 3: Variables + digits 4-5
    [
        ("ans",  "ans",   "Last answer",    "var"),
        ("x",    "x",     "Variable x",     "var"),
        ("y",    "y",     "Variable y",     "var"),
        ("4",    "4",     "Digit 4",        "digit"),
        ("5",    "5",     "Digit 5",        "digit"),
    ],
    # Row 4: Variable z + parens + digits 1-2
    [
        ("z",    "z",     "Variable z",     "var"),
        ("(",    "(",     "Left paren",     "op"),
        (")",    ")",     "Right paren",    "op"),
        ("1",    "1",     "Digit 1",        "digit"),
        ("2",    "2",     "Digit 2",        "digit"),
    ],
    # Row 5: Power, clear, backspace, divide, 3
    [
        ("x^y",  "^",     "Power",          "op"),
        ("C",    "",      "Clear all",      "action"),
        ("\u232b", "",    "Backspace",      "action"),
        ("\u00f7", "/",   "Divide",         "op"),
        ("3",    "3",     "Digit 3",        "digit"),
    ],
    # Row 6: Decimal, add, subtract, multiply, 0
    [
        (".",    ".",     "Decimal point",  "digit"),
        ("+",    "+",     "Add",            "op"),
        ("\u2212", "-",   "Subtract",       "op"),
        ("\u00d7", "*",   "Multiply",       "op"),
        ("0",    "0",     "Digit 0",        "digit"),
    ],
    # Row 7: Factorial, negate, EXP, equals
    [
        ("!",    "!",     "Factorial",      "op"),
        ("\u00b1", "(-)", "Negate",         "op"),
        ("mod",  " mod ", "Modulo",         "op"),
        ("=",    "",      "Calculate",      "equals"),
        ("",     "",      "",               "digit"),  # empty spacer
    ],
]


class KeypadWidget(ttk.Frame):
    """Virtual calculator keypad with grid layout.

    Signals:
        on_insert(text: str)  - insert text at cursor in expression
        on_clear()            - clear the expression
        on_backspace()        - delete character before cursor
        on_submit()           - calculate the expression
    """

    _COLS = 5

    # Color palette per button category: (bg, fg, hover_bg, font_family, font_size)
    _STYLES: dict[str, tuple[str, str, str, tuple[str, int]]] = {
        "digit":  ("#2d2d2d", "#ffffff", "#404040", ("Segoe UI", 14)),
        "op":     ("#4a3728", "#ffd5a0", "#5e4a38", ("Segoe UI", 14)),
        "func":   ("#1a3a4a", "#8ad4f0", "#244e62", ("Segoe UI", 11)),
        "const":  ("#1a3a2a", "#80e0a0", "#245e3a", ("Segoe UI", 13)),
        "var":    ("#3a2a4a", "#c8a0f0", "#4e3a62", ("Segoe UI", 13)),
        "action": ("#5a1a1a", "#ff9090", "#7a2a2a", ("Segoe UI", 13)),
        "equals": ("#1a5a1a", "#90ff90", "#2a7a2a", ("Segoe UI", 16)),
    }

    def __init__(
        self,
        parent: tk.Misc,
        on_insert: Callable[[str], None] | None = None,
        on_clear: Callable[[], None] | None = None,
        on_backspace: Callable[[], None] | None = None,
        on_submit: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_insert = on_insert
        self._on_clear = on_clear
        self._on_backspace = on_backspace
        self._on_submit = on_submit
        self._buttons: list[tk.Button] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the keypad grid."""
        # Configure grid: equal-weight columns that expand
        for col in range(self._COLS):
            self.columnconfigure(col, weight=1, uniform="keypad")

        for row_idx, row_def in enumerate(_BUTTON_DEFS):
            self.rowconfigure(row_idx, weight=1)

            for col_idx, (label, insert_text, tooltip, style_tag) in enumerate(row_def):
                bg, fg, hover_bg, btn_font = self._STYLES.get(
                    style_tag, self._STYLES["digit"]
                )

                # Skip empty spacer cells
                if not label and not tooltip:
                    spacer = ttk.Frame(self)
                    spacer.grid(row=row_idx, column=col_idx, sticky="nsew")
                    continue

                # Determine command
                if style_tag == "action" and label == "C":
                    cmd: Callable[[], None] | None = self._do_clear
                elif style_tag == "action" and label == "\u232b":
                    cmd = self._do_backspace
                elif style_tag == "equals":
                    cmd = self._do_submit
                else:
                    # Capture insert_text in closure default arg
                    cmd = lambda t=insert_text: self._fire_insert(t)  # type: ignore[arg-type]

                btn = tk.Button(
                    self,
                    text=label,
                    command=cmd if cmd else lambda: None,
                    bg=bg,
                    fg=fg,
                    activebackground=hover_bg,
                    activeforeground=fg,
                    relief=tk.FLAT,
                    borderwidth=0,
                    highlightthickness=0,
                    font=btn_font,
                    cursor="hand2",
                    takefocus=False,
                    height=1,
                )
                btn.grid(
                    row=row_idx,
                    column=col_idx,
                    sticky="nsew",
                    padx=1,
                    pady=1,
                )

                # Hover effect
                btn.bind(
                    "<Enter>",
                    lambda e, b=btn, h=hover_bg: b.config(bg=h),  # type: ignore[arg-type]
                )
                btn.bind(
                    "<Leave>",
                    lambda e, b=btn, c=bg: b.config(bg=c),  # type: ignore[arg-type]
                )

                # Tooltip
                if tooltip:
                    self._create_tooltip(btn, tooltip)

                self._buttons.append(btn)

    def _create_tooltip(self, widget: tk.Widget, text: str) -> None:
        """Attach a tooltip to a widget."""
        tip_win: tk.Toplevel | None = None

        def _show(event: tk.Event) -> None:
            nonlocal tip_win
            if tip_win is not None:
                return
            x = event.x_root + 8
            y = event.y_root - 20
            tip_win = tk.Toplevel(widget)
            tip_win.wm_overrideredirect(True)
            tip_win.wm_geometry(f"+{x}+{y}")
            tk.Label(
                tip_win,
                text=text,
                background="#ffffdd",
                foreground="#333333",
                font=("Segoe UI", 9),
                padx=6,
                pady=2,
                relief=tk.SOLID,
                borderwidth=1,
            ).pack()

        def _hide(event: tk.Event) -> None:
            nonlocal tip_win
            if tip_win is not None:
                tip_win.destroy()
                tip_win = None

        widget.bind("<Enter>", _show, add="+")
        widget.bind("<Leave>", _hide, add="+")

    # ------------------------------------------------------------------
    # Signal dispatch
    # ------------------------------------------------------------------

    def _fire_insert(self, text: str) -> None:
        """Dispatch insert signal."""
        if self._on_insert:
            self._on_insert(text)

    def _do_clear(self) -> None:
        """Dispatch clear signal."""
        if self._on_clear:
            self._on_clear()

    def _do_backspace(self) -> None:
        """Dispatch backspace signal."""
        if self._on_backspace:
            self._on_backspace()

    def _do_submit(self) -> None:
        """Dispatch submit signal."""
        if self._on_submit:
            self._on_submit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_callbacks(
        self,
        on_insert: Callable[[str], None] | None = None,
        on_clear: Callable[[], None] | None = None,
        on_backspace: Callable[[], None] | None = None,
        on_submit: Callable[[], None] | None = None,
    ) -> None:
        """Update callback references (used for late binding)."""
        if on_insert is not None:
            self._on_insert = on_insert
        if on_clear is not None:
            self._on_clear = on_clear
        if on_backspace is not None:
            self._on_backspace = on_backspace
        if on_submit is not None:
            self._on_submit = on_submit

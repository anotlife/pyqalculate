"""Expression status bar widget below the expression editor.

Two-column layout:
  Left  — parsed expression, function hints, errors, autocalc results
  Right — mode indicator badges (EXACT, RPN, CHN, base, angle, …)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pyqalculate_gui.event_bus import MODE_CHANGED, EventBus
from pyqalculate_gui.theme import LIGHT, Theme

# Status text source constants (mirror qalculate-gtk)
STATUS_TEXT_NONE = 0
STATUS_TEXT_FUNCTION = 1
STATUS_TEXT_ERROR = 2
STATUS_TEXT_PARSED = 3
STATUS_TEXT_AUTOCALC = 4


class ExpressionStatusBar(ttk.Frame):
    """Two-column status bar below expression editor.

    Layout::

        ┌──────────────────────────────────────────────────────┐
        │ [left_label: parsed expr/errors]  [right_label: modes] │
        └──────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme = LIGHT,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._event_bus = event_bus

        # State
        self._status_text_source: int = STATUS_TEXT_NONE
        self._current_function: str | None = None
        self._current_function_index: int = 0

        # Subscribe to events
        if self._event_bus:
            self._event_bus.subscribe(MODE_CHANGED, self._on_mode_changed)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the status bar UI."""
        # Left label: parsed expression / errors
        self._left_label = tk.Label(
            self,
            font=self._theme.info_font,
            bg=self._theme.bg,
            fg=self._theme.fg,
            anchor="w",
            padx=9,
            pady=2,
        )
        self._left_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Right label: mode indicators
        self._right_label = tk.Label(
            self,
            font=self._theme.info_font,
            bg=self._theme.bg,
            fg=self._theme.fg,
            anchor="e",
            padx=12,
            pady=2,
        )
        self._right_label.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_mode_changed(self, mode_info: dict) -> None:
        """Handle mode change events."""
        self.update_mode_indicators(mode_info)

    # ------------------------------------------------------------------
    # Public API — left label
    # ------------------------------------------------------------------

    def show_parsed_expression(self, text: str) -> None:
        """Show parsed expression in left label."""
        self._left_label.config(text=text, fg=self._theme.fg)
        self._status_text_source = STATUS_TEXT_PARSED

    def show_function_hint(
        self,
        func_name: str,
        arg_index: int,
        arg_name: str,
        arg_type: str,
    ) -> None:
        """Show function argument hint with current argument highlighted."""
        hint = f"{func_name}("
        for i in range(1, arg_index):
            hint += f"arg{i}, "
        hint += f"**{arg_name}**: {arg_type}"
        hint += ")"

        self._left_label.config(text=hint, fg=self._theme.fg)
        self._status_text_source = STATUS_TEXT_FUNCTION

    def show_error(self, error: str) -> None:
        """Show error message in left label."""
        self._left_label.config(text=error, fg=self._theme.error_fg)
        self._status_text_source = STATUS_TEXT_ERROR

    def show_warning(self, warning: str) -> None:
        """Show warning message in left label."""
        self._left_label.config(text=warning, fg=self._theme.warning_fg)
        self._status_text_source = STATUS_TEXT_ERROR

    def show_autocalc_result(self, result: str, exact: bool = True) -> None:
        """Show auto-calculated result."""
        prefix = "=" if exact else "≈"
        self._left_label.config(text=f"{prefix} {result}", fg=self._theme.fg)
        self._status_text_source = STATUS_TEXT_AUTOCALC

    def clear(self) -> None:
        """Clear the status bar."""
        self._left_label.config(text="")
        self._status_text_source = STATUS_TEXT_NONE

    # ------------------------------------------------------------------
    # Public API — right label (mode indicators)
    # ------------------------------------------------------------------

    def update_mode_indicators(self, mode_info: dict) -> None:
        """Update right label with mode indicators."""
        indicators: list[str] = []

        # Approximation mode
        if mode_info.get("exact", False):
            indicators.append("EXACT")

        # RPN mode
        if mode_info.get("rpn", False):
            indicators.append("RPN")

        # Chain mode
        if mode_info.get("chain", False):
            indicators.append("CHN")

        # Number base
        base = mode_info.get("base", 10)
        base_map = {2: "BIN", 8: "OCT", 12: "DUO", 16: "HEX"}
        if base in base_map:
            indicators.append(base_map[base])
        elif base != 10:
            indicators.append(str(base))

        # Angle unit
        angle = mode_info.get("angle", "degrees")
        angle_map = {"degrees": "DEG", "radians": "RAD", "gradians": "GRA"}
        if angle in angle_map:
            indicators.append(angle_map[angle])

        # Disabled features
        if not mode_info.get("functions_enabled", True):
            indicators.append("FUNC")
        if not mode_info.get("units_enabled", True):
            indicators.append("UNIT")
        if not mode_info.get("variables_enabled", True):
            indicators.append("VAR")

        # Update label
        self._right_label.config(text="  ".join(indicators))

    def set_theme(self, theme: Theme) -> None:
        """Update the widget's theme."""
        self._theme = theme
        self._left_label.config(font=theme.info_font, bg=theme.bg, fg=theme.fg)
        self._right_label.config(font=theme.info_font, bg=theme.bg, fg=theme.fg)

"""Result display widget with theme and event integration.

Shows calculation results with expression echo, exact/approximate
indication, and error/info display. All visual properties derive
from the theme — zero hardcoded colors or fonts.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from PIL import ImageTk

from pyqalculate_gui.event_bus import (
    EXPRESSION_SUBMITTED,
    HISTORY_RECALLED,
    RESULT_DISPLAYED,
    EventBus,
)
from pyqalculate_gui.math_renderer import MathRenderer
from pyqalculate_gui.theme import LIGHT, Theme
from pyqalculate_gui.i18n import _

SEPARATOR_LEN = 40


class ResultView(ttk.Frame):
    """Display area for calculation results.

    Renders expression echo and result with formatted text tags.
    Subscribes to EXPRESSION_SUBMITTED for auto-echo and emits
    RESULT_DISPLAYED after each result.
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
        self._last_result: str = ""
        self._math_renderer = MathRenderer(dpi=96)
        self._photo_refs: list = []  # prevent GC of embedded images
        self._expressions: list[str] = []
        self._results: list[str] = []
        self._expression_lines: list[tuple[str, int]] = []

        if self._event_bus is not None:
            self._event_bus.subscribe(
                EXPRESSION_SUBMITTED, self._on_expression_submitted
            )

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the result display."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(self)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self._text = tk.Text(
            self,
            font=self._theme.result_font,
            bg=self._theme.bg,
            fg=self._theme.fg,
            state=tk.DISABLED,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
        )
        self._text.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self._text.yview)
        self._text.bind("<Double-1>", self._on_double_click)

        self._text.tag_configure(
            "expression", foreground=self._theme.expression_fg
        )
        self._text.tag_configure(
            "result",
            foreground=self._theme.result_fg,
            font=self._theme.result_font,
        )
        self._text.tag_configure(
            "approx", foreground=self._theme.result_approx_fg
        )
        self._text.tag_configure("error", foreground=self._theme.error_fg)
        self._text.tag_configure("separator", foreground=self._theme.separator_fg)
        self._text.tag_configure(
            "info",
            foreground=self._theme.info_fg,
            font=self._theme.info_font,
        )

    def _on_expression_submitted(self, expression: str) -> None:
        """Handle expression submission — show the expression."""
        if not expression:
            return  # Skip empty expression echo (e.g., from = button)
        self._expressions.append(expression)
        line = int(self._text.index(tk.END).split('.')[0]) - 1
        self._expression_lines.append((expression, line))
        self._append(f">>> {expression}\n", "expression")

    def show_result(self, expression: str, result: str, exact: bool = True) -> None:
        """Show a calculation result.

        Attempts to render the result as a typeset math image first.
        Falls back to plain text if rendering fails.
        """
        self._last_result = result
        self._results.append(result)
        tag = "result" if exact else "approx"
        color = self._theme.result_fg if exact else self._theme.result_approx_fg

        photo = self._math_renderer.render(
            result, font_size=12, color=color, master=self
        )
        if photo is not None:
            self._insert_image(photo)
        else:
            self._append(f"{result}\n", tag)

        self._append("─" * SEPARATOR_LEN + "\n", "separator")
        if self._event_bus is not None:
            self._event_bus.emit(RESULT_DISPLAYED, expression, result, exact)

    def show_error(self, error: str) -> None:
        """Show an error message."""
        self._append(_("Error: {}").format(error) + "\n", "error")
        self._append("─" * SEPARATOR_LEN + "\n", "separator")

    def show_info(self, info: str) -> None:
        """Show an info message."""
        self._append(f"{info}\n", "info")

    def clear(self) -> None:
        """Clear all content."""
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.config(state=tk.DISABLED)
        self._last_result = ""
        self._photo_refs.clear()
        self._expressions.clear()
        self._results.clear()
        self._expression_lines.clear()

    def get_last_result(self) -> str:
        """Return the last result string."""
        return self._last_result

    def get_answer(self, n: int) -> str | None:
        """Get answer at position N (1-indexed). answer(1) = most recent."""
        if 1 <= n <= len(self._results):
            return self._results[-n]
        return None

    def _on_double_click(self, event: tk.Event) -> None:
        """Handle double-click — recall the expression at that line."""
        index = self._text.index(f"@{event.x},{event.y}")
        line = int(index.split(".")[0])
        # Find the nearest expression at or before the clicked line
        expr = None
        for expression, expr_line in reversed(self._expression_lines):
            if expr_line <= line:
                expr = expression
                break
        if expr and self._event_bus is not None:
            self._event_bus.emit(HISTORY_RECALLED, expr)

    def _append(self, text: str, tag: str = "") -> None:
        """Append text with optional tag."""
        self._text.config(state=tk.NORMAL)
        if tag:
            self._text.insert(tk.END, text, tag)
        else:
            self._text.insert(tk.END, text)
        self._text.config(state=tk.DISABLED)
        self._text.see(tk.END)

    def _insert_image(self, photo: ImageTk.PhotoImage) -> None:
        """Insert a rendered math image at the end of the text widget."""
        self._photo_refs.append(photo)
        self._text.config(state=tk.NORMAL)
        self._text.image_create(tk.END, image=photo)
        self._text.insert(tk.END, "\n")
        self._text.config(state=tk.DISABLED)
        self._text.see(tk.END)

    def set_theme(self, theme: Theme) -> None:
        """Update the widget's theme."""
        self._theme = theme
        self._text.config(
            font=theme.result_font,
            bg=theme.bg,
            fg=theme.fg,
        )
        self._text.tag_configure("expression", foreground=theme.expression_fg)
        self._text.tag_configure(
            "result", foreground=theme.result_fg, font=theme.result_font,
        )
        self._text.tag_configure("approx", foreground=theme.result_approx_fg)
        self._text.tag_configure("error", foreground=theme.error_fg)
        self._text.tag_configure("separator", foreground=theme.separator_fg)
        self._text.tag_configure(
            "info", foreground=theme.info_fg, font=theme.info_font,
        )

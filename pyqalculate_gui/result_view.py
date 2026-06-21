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
    RESULT_DISPLAYED,
    EventBus,
)
from pyqalculate_gui.math_renderer import MathRenderer
from pyqalculate_gui.theme import LIGHT, Theme

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
        self._append(f">>> {expression}\n", "expression")

    def show_result(self, expression: str, result: str, exact: bool = True) -> None:
        """Show a calculation result.

        Attempts to render the result as a typeset math image first.
        Falls back to plain text if rendering fails.
        """
        self._last_result = result
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
        self._append(f"Error: {error}\n", "error")
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

    def get_last_result(self) -> str:
        """Return the last result string."""
        return self._last_result

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

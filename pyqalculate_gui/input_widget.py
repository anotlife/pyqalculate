"""Expression input widget with history navigation.

Provides a text entry field for entering mathematical expressions,
a submit button, mode toggle (exact/approximate), and up/down arrow
history navigation.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class InputWidget(ttk.Frame):
    """Expression input area with history and mode controls.

    Signals:
        on_submit(expression: str) - fired when user submits an expression
        on_mode_change(exact: bool) - fired when mode toggles
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_submit: Callable[[str], None] | None = None,
        on_mode_change: Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_submit = on_submit
        self._on_mode_change = on_mode_change
        self._history: list[str] = []
        self._history_index: int = -1
        self._exact_mode = True

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the input area UI."""
        # Row: [Entry] [Submit] [Mode toggle]
        self.columnconfigure(0, weight=1)

        # Expression entry
        self._entry = ttk.Entry(self, font=("Consolas", 12))
        self._entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._entry.bind("<Return>", self._on_enter)
        self._entry.bind("<Up>", self._on_history_up)
        self._entry.bind("<Down>", self._on_history_down)
        self._entry.focus_set()

        # Submit button
        self._submit_btn = ttk.Button(self, text="=", width=3, command=self._do_submit)
        self._submit_btn.grid(row=0, column=1, padx=(0, 5))

        # Mode toggle button
        self._mode_btn = ttk.Button(
            self, text="Exact", width=8, command=self._toggle_mode
        )
        self._mode_btn.grid(row=0, column=2)

    def _on_enter(self, event: tk.Event) -> None:
        """Handle Enter key press."""
        self._do_submit()

    def _on_history_up(self, event: tk.Event) -> None:
        """Navigate history backward (older entries)."""
        if not self._history:
            return
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            idx = len(self._history) - 1 - self._history_index
            self._entry.delete(0, tk.END)
            self._entry.insert(0, self._history[idx])

    def _on_history_down(self, event: tk.Event) -> None:
        """Navigate history forward (newer entries)."""
        if not self._history:
            return
        if self._history_index > 0:
            self._history_index -= 1
            idx = len(self._history) - 1 - self._history_index
            self._entry.delete(0, tk.END)
            self._entry.insert(0, self._history[idx])
        elif self._history_index == 0:
            self._history_index = -1
            self._entry.delete(0, tk.END)

    def _do_submit(self) -> None:
        """Submit the current expression."""
        expr = self._entry.get().strip()
        if not expr:
            return

        # Add to history (avoid consecutive duplicates)
        if not self._history or self._history[-1] != expr:
            self._history.append(expr)
        self._history_index = -1

        # Clear entry
        self._entry.delete(0, tk.END)

        # Fire callback
        if self._on_submit:
            self._on_submit(expr)

    def _toggle_mode(self) -> None:
        """Toggle between exact and approximate mode."""
        self._exact_mode = not self._exact_mode
        self._mode_btn.config(text="Exact" if self._exact_mode else "Approx")
        if self._on_mode_change:
            self._on_mode_change(self._exact_mode)

    def get_expression(self) -> str:
        """Return the current expression text."""
        return self._entry.get().strip()

    def set_expression(self, expr: str) -> None:
        """Set the expression text (e.g., from sidebar double-click)."""
        self._entry.delete(0, tk.END)
        self._entry.insert(0, expr)
        self._entry.focus_set()

    def append_to_expression(self, text: str) -> None:
        """Append text to the current expression."""
        current = self._entry.get()
        self._entry.delete(0, tk.END)
        self._entry.insert(0, current + text)
        self._entry.focus_set()

    def is_exact_mode(self) -> bool:
        """Return True if in exact mode."""
        return self._exact_mode

    def get_history(self) -> list[str]:
        """Return a copy of the expression history."""
        return list(self._history)

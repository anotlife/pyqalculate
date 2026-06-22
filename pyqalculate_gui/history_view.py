"""History panel for browsing past calculations.

Provides a scrollable list of expressions, results, and errors with:
- Double-click to recall expression via EventBus
- answer(N) support for referencing past results
- Theme-driven colors throughout
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass

from pyqalculate_gui.theme import Theme, LIGHT
from pyqalculate_gui.event_bus import EventBus, HISTORY_RECALLED


# ---------------------------------------------------------------------------
# History entry
# ---------------------------------------------------------------------------

@dataclass
class HistoryEntry:
    """A single history entry."""

    expression: str
    result: str
    exact: bool
    entry_type: str  # "expression", "result", "error"


# ---------------------------------------------------------------------------
# HistoryView widget
# ---------------------------------------------------------------------------

class HistoryView(ttk.Frame):
    """Scrollable history of past calculations.

    Uses Theme for all colors/fonts and EventBus for recall events.
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
        self._entries: list[HistoryEntry] = []

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the history list."""
        # Scrollbar
        scrollbar = ttk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox
        self._listbox = tk.Listbox(
            self,
            font=self._theme.info_font,
            bg=self._theme.bg,
            fg=self._theme.fg,
            selectbackground=self._theme.select_bg,
            yscrollcommand=scrollbar.set,
        )
        self._listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._listbox.yview)

        # Double-click to recall
        self._listbox.bind("<Double-1>", self._on_recall)

    # ------------------------------------------------------------------
    # Recall handling
    # ------------------------------------------------------------------

    def _on_recall(self, event: tk.Event | None = None) -> None:
        """Handle double-click — emit expression via EventBus."""
        selection = self._listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx >= len(self._entries):
            return

        entry = self._entries[idx]
        if self._event_bus and entry.expression:
            self._event_bus.emit(HISTORY_RECALLED, entry.expression)

    # ------------------------------------------------------------------
    # Public API — adding entries
    # ------------------------------------------------------------------

    def add_expression(self, expression: str) -> None:
        """Add an expression to history."""
        entry = HistoryEntry(
            expression=expression,
            result="",
            exact=True,
            entry_type="expression",
        )
        self._entries.append(entry)
        self._listbox.insert(tk.END, f">>> {expression}")
        self._listbox.see(tk.END)

    def add_result(self, result: str, exact: bool = True) -> None:
        """Add a result to history."""
        entry = HistoryEntry(
            expression="",
            result=result,
            exact=exact,
            entry_type="result",
        )
        self._entries.append(entry)
        prefix = "=" if exact else "≈"
        self._listbox.insert(tk.END, f"{prefix} {result}")
        self._listbox.see(tk.END)

    def add_error(self, error: str) -> None:
        """Add an error to history."""
        entry = HistoryEntry(
            expression="",
            result=error,
            exact=False,
            entry_type="error",
        )
        self._entries.append(entry)
        self._listbox.insert(tk.END, f"Error: {error}")
        self._listbox.see(tk.END)

    # ------------------------------------------------------------------
    # answer(N) support
    # ------------------------------------------------------------------

    def get_answer(self, n: int) -> str | None:
        """Get answer at position N (1-indexed). answer(1) = most recent."""
        results = [e for e in self._entries if e.entry_type == "result"]
        if 1 <= n <= len(results):
            return results[-n].result
        return None

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Clear all history."""
        self._entries.clear()
        self._listbox.delete(0, tk.END)

    def set_theme(self, theme: Theme) -> None:
        """Update the widget's theme."""
        self._theme = theme
        self._listbox.config(
            font=theme.info_font,
            bg=theme.bg,
            fg=theme.fg,
            selectbackground=theme.select_bg,
        )

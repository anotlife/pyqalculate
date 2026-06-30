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
from pyqalculate_gui.event_bus import EventBus, HISTORY_RECALLED, HISTORY_UPDATED
from pyqalculate_gui.i18n import _


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
        emit_updates: bool = False,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._event_bus = event_bus
        self._emit_updates = emit_updates
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
        if self._emit_updates and self._event_bus:
            self._event_bus.emit(HISTORY_UPDATED, "expression", expression)

    def add_result(self, result: str, exact: bool = True) -> None:
        """Add a result to history."""
        entry = HistoryEntry(
            expression="",
            result=result,
            exact=exact,
            entry_type="result",
        )
        self._entries.append(entry)
        prefix = "=" if exact else "\u2248"
        self._listbox.insert(tk.END, f"{prefix} {result}")
        self._listbox.see(tk.END)
        if self._emit_updates and self._event_bus:
            self._event_bus.emit(HISTORY_UPDATED, "result", result, exact)

    def add_error(self, error: str) -> None:
        """Add an error to history."""
        entry = HistoryEntry(
            expression="",
            result=error,
            exact=False,
            entry_type="error",
        )
        self._entries.append(entry)
        self._listbox.insert(tk.END, _("Error: {}").format(error))
        self._listbox.see(tk.END)
        if self._emit_updates and self._event_bus:
            self._event_bus.emit(HISTORY_UPDATED, "error", error)

    # ------------------------------------------------------------------
    # answer(N) support
    # ------------------------------------------------------------------

    def get_answer(self, n: int) -> str | None:
        """Get answer at position N (1-indexed). answer(1) = most recent."""
        results = [e for e in self._entries if e.entry_type == "result"]
        if 1 <= n <= len(results):
            return results[-n].result
        return None

    def get_all_entries(self) -> list[HistoryEntry]:
        """Return a copy of all history entries."""
        return list(self._entries)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Clear all history."""
        self._entries.clear()
        self._listbox.delete(0, tk.END)
        if self._emit_updates and self._event_bus:
            self._event_bus.emit(HISTORY_UPDATED, "clear")

    def set_theme(self, theme: Theme) -> None:
        """Update the widget's theme."""
        self._theme = theme
        self._listbox.config(
            font=theme.info_font,
            bg=theme.bg,
            fg=theme.fg,
            selectbackground=theme.select_bg,
        )


class HistoryWindow:
    """Toplevel window wrapping a HistoryView for the Tools menu.

    Subscribes to ``HISTORY_UPDATED`` from the main event-bus so the
    window stays in sync with the main panel's history.  The contained
    view never emits ``HISTORY_UPDATED`` itself (``emit_updates=False``)
    to avoid feedback loops, but it does emit ``HISTORY_RECALLED`` so
    double-click recall still works.
    """

    def __init__(
        self,
        parent: tk.Misc,
        theme: Theme = LIGHT,
        event_bus: EventBus | None = None,
        source_view: HistoryView | None = None,
    ) -> None:
        self._window = tk.Toplevel(parent)
        self._window.title(_("History"))
        self._window.geometry("500x400")
        self._window.transient(parent)

        self._event_bus = event_bus
        self._source_view = source_view

        self._view = HistoryView(
            self._window, theme=theme, event_bus=event_bus, emit_updates=False,
        )
        self._view.pack(fill=tk.BOTH, expand=True)

        if self._event_bus is not None:
            self._event_bus.subscribe(HISTORY_UPDATED, self._on_history_updated)

        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._sync_from_source()
        self._centred = False

    def _on_close(self) -> None:
        """Clean up subscriptions and destroy the window."""
        if self._event_bus is not None:
            self._event_bus.unsubscribe(HISTORY_UPDATED, self._on_history_updated)
        self._window.destroy()

    def _sync_from_source(self) -> None:
        """Copy all entries from the source view into the window view."""
        if self._source_view is None:
            return
        for entry in self._source_view.get_all_entries():
            if entry.entry_type == "expression":
                self._view.add_expression(entry.expression)
            elif entry.entry_type == "result":
                self._view.add_result(entry.result, entry.exact)
            elif entry.entry_type == "error":
                self._view.add_error(entry.result)

    def _on_history_updated(self, action: str, *args) -> None:
        """Sync an update from the main history to this window."""
        if not self.is_alive():
            return
        if action == "expression":
            self._view.add_expression(args[0])
        elif action == "result":
            self._view.add_result(args[0], args[1])
        elif action == "error":
            self._view.add_error(args[0])
        elif action == "clear":
            self._view.clear()

    def show(self) -> None:
        """Show the window, centring on first display."""
        if not self._centred:
            self._window.update_idletasks()
            pw = self._window.winfo_parent()
            parent_widget = self._window.nametowidget(pw) if pw else self._window.master
            x = parent_widget.winfo_x() + (parent_widget.winfo_width() - self._window.winfo_width()) // 2
            y = parent_widget.winfo_y() + (parent_widget.winfo_height() - self._window.winfo_height()) // 2
            self._window.geometry(f"+{x}+{y}")
            self._centred = True
        self._window.deiconify()
        self._window.lift()

    def focus(self) -> None:
        """Bring window to front."""
        self.show()

    def is_alive(self) -> bool:
        """Return True if the Toplevel window still exists."""
        try:
            return self._window.winfo_exists()
        except tk.TclError:
            return False

    @property
    def view(self) -> HistoryView:
        """Return the contained HistoryView."""
        return self._view

    def set_theme(self, theme: Theme) -> None:
        """Push theme to the contained HistoryView."""
        self._view.set_theme(theme)

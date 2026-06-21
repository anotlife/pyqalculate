"""Expression input widget with undo/redo and event-driven submit.

Provides a styled text entry for mathematical expressions with:
- Enter to submit via EventBus
- Manual undo/redo with bounded stacks
- Theme-aware colors and fonts
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections import deque

from pyqalculate_gui.theme import Theme, LIGHT
from pyqalculate_gui.event_bus import EventBus, EXPRESSION_SUBMITTED
from pyqalculate_gui.state import AppState

_MAX_UNDO = 100


class ExpressionEdit(ttk.Frame):
    """Expression input area with undo/redo and keyboard shortcuts.

    Uses Theme for all visual properties, EventBus for submit notifications,
    and AppState for shared state access.
    """

    def __init__(
        self,
        parent: tk.Misc,
        theme: Theme = LIGHT,
        event_bus: EventBus | None = None,
        state: AppState | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._event_bus = event_bus
        self._state = state

        # Undo/redo stacks (local UI concern)
        self._undo_stack: deque[str] = deque(maxlen=_MAX_UNDO)
        self._redo_stack: deque[str] = deque(maxlen=_MAX_UNDO)
        self._current_text = ""

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the expression entry widget."""
        self._entry = tk.Text(
            self,
            font=self._theme.expression_font,
            bg=self._theme.entry_bg,
            fg=self._theme.expression_fg,
            insertbackground=self._theme.fg,
            selectbackground=self._theme.select_bg,
            height=3,
            wrap=tk.WORD,
            undo=False,  # We manage undo ourselves
        )
        self._entry.pack(fill=tk.BOTH, expand=True)

        # Bindings
        self._entry.bind("<Return>", self._on_submit)
        self._entry.bind("<Key>", self._on_key)

    # ------------------------------------------------------------------
    # Keyboard handling
    # ------------------------------------------------------------------

    def _on_submit(self, event: tk.Event | None = None) -> str:
        """Handle Enter key — emit expression via EventBus."""
        expr = self.get_expression()
        if expr.strip() and self._event_bus:
            self._event_bus.emit(EXPRESSION_SUBMITTED, expr)
        return "break"

    def _on_key(self, event: tk.Event) -> None:
        """Track changes for undo."""
        skip = ("Shift_L", "Shift_R", "Control_L", "Control_R")
        if event.keysym not in skip:
            self._entry.after_idle(self._track_change)

    def _track_change(self) -> None:
        """Record text snapshot if content changed."""
        text = self.get_expression()
        if text != self._current_text:
            self._undo_stack.append(self._current_text)
            self._redo_stack.clear()
            self._current_text = text

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_expression(self) -> str:
        """Return the current expression text."""
        return self._entry.get("1.0", tk.END).strip()

    def set_expression(self, text: str) -> None:
        """Replace the expression text."""
        self._entry.delete("1.0", tk.END)
        self._entry.insert("1.0", text)
        self._current_text = text

    def insert_at_cursor(self, text: str) -> None:
        """Insert text at the current cursor position."""
        self._entry.insert(tk.INSERT, text)
        self._track_change()

    def clear(self) -> None:
        """Clear the expression."""
        self._entry.delete("1.0", tk.END)
        self._current_text = ""

    def focus_input(self) -> None:
        """Focus the expression entry."""
        self._entry.focus_set()

    def undo(self) -> None:
        """Undo the last change."""
        if self._undo_stack:
            self._redo_stack.append(self._current_text)
            self._current_text = self._undo_stack.pop()
            self._entry.delete("1.0", tk.END)
            self._entry.insert("1.0", self._current_text)

    def redo(self) -> None:
        """Redo the last undone change."""
        if self._redo_stack:
            self._undo_stack.append(self._current_text)
            self._current_text = self._redo_stack.pop()
            self._entry.delete("1.0", tk.END)
            self._entry.insert("1.0", self._current_text)

    def activate_completion(self) -> None:
        """Activate the first completion suggestion.

        Stub for future completion popup integration.
        """
        # TODO: integrate with completion popup when available

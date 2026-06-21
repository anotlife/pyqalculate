"""Expression input widget with history and undo/redo.

Provides a styled text entry for mathematical expressions with:
- Enter to calculate
- Up/Down arrow for expression history
- Escape to clear
- Ctrl+Z/Y for undo/redo
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections import deque
from typing import Callable


class ExpressionEdit(ttk.Frame):
    """Expression input area with history, undo/redo, and keyboard shortcuts.

    Signals:
        on_submit(expression: str) - fired when user presses Enter
    """

    _MAX_HISTORY = 100
    _MAX_UNDO = 100

    def __init__(
        self,
        parent: tk.Misc,
        on_submit: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_submit = on_submit

        # Expression history (Up/Down arrows)
        self._history: list[str] = []
        self._history_index: int = -1
        self._saved_current: str = ""  # text before history navigation

        # Undo/redo buffers
        self._undo_stack: deque[str] = deque(maxlen=self._MAX_UNDO)
        self._redo_stack: deque[str] = deque(maxlen=self._MAX_UNDO)
        self._block_undo: bool = False

        self._build_ui()
        self._bind_events()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the expression entry layout."""
        self.columnconfigure(0, weight=1)

        self._entry = ttk.Entry(self, font=("Consolas", 13))
        self._entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._entry.focus_set()

        self._submit_btn = ttk.Button(self, text="=", width=3, command=self._do_submit)
        self._submit_btn.grid(row=0, column=1)

    def _bind_events(self) -> None:
        """Bind keyboard shortcuts."""
        self._entry.bind("<Return>", lambda e: self._do_submit())
        self._entry.bind("<Escape>", lambda e: self.clear())
        self._entry.bind("<Up>", lambda e: self._history_up())
        self._entry.bind("<Down>", lambda e: self._history_down())
        self._entry.bind("<Control-z>", lambda e: self._undo())
        self._entry.bind("<Control-y>", lambda e: self._redo())
        self._entry.bind("<Key>", self._on_key)

    # ------------------------------------------------------------------
    # Keyboard handling
    # ------------------------------------------------------------------

    def _on_key(self, event: tk.Event) -> None:
        """Record undo snapshot before each keystroke."""
        if event.keysym in ("Up", "Down", "Escape", "Return"):
            return  # handled by dedicated bindings
        if isinstance(event.state, int) and event.state & 0x4:  # Ctrl held
            return  # let Ctrl+Z/Y through
        self._push_undo()

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------

    def _do_submit(self) -> None:
        """Submit the current expression."""
        expr = self._entry.get().strip()
        if not expr:
            return

        # Record in history (deduplicate consecutive)
        if not self._history or self._history[-1] != expr:
            self._history.append(expr)
            if len(self._history) > self._MAX_HISTORY:
                self._history.pop(0)
        self._history_index = -1
        self._saved_current = ""

        # Clear undo/redo for the new session of this expression
        self._undo_stack.clear()
        self._redo_stack.clear()

        self._entry.delete(0, tk.END)

        if self._on_submit:
            self._on_submit(expr)

    # ------------------------------------------------------------------
    # History navigation
    # ------------------------------------------------------------------

    def _history_up(self) -> str:
        """Navigate to older expression in history."""
        if not self._history:
            return "break"
        if self._history_index == -1:
            self._saved_current = self._entry.get()
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            idx = len(self._history) - 1 - self._history_index
            self._set_text(self._history[idx])
        return "break"

    def _history_down(self) -> str:
        """Navigate to newer expression in history."""
        if not self._history:
            return "break"
        if self._history_index > 0:
            self._history_index -= 1
            idx = len(self._history) - 1 - self._history_index
            self._set_text(self._history[idx])
        elif self._history_index == 0:
            self._history_index = -1
            self._set_text(self._saved_current)
        return "break"

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------

    def _push_undo(self) -> None:
        """Save current text to undo stack."""
        if self._block_undo:
            return
        current = self._entry.get()
        if not self._undo_stack or self._undo_stack[-1] != current:
            self._undo_stack.append(current)
            self._redo_stack.clear()

    def _undo(self) -> str:
        """Undo last edit."""
        current = self._entry.get()
        if self._undo_stack:
            self._redo_stack.append(current)
            self._set_text(self._undo_stack.pop())
        return "break"

    def _redo(self) -> str:
        """Redo last undone edit."""
        current = self._entry.get()
        if self._redo_stack:
            self._undo_stack.append(current)
            self._set_text(self._redo_stack.pop())
        return "break"

    # ------------------------------------------------------------------
    # Text manipulation helpers
    # ------------------------------------------------------------------

    def _set_text(self, text: str) -> None:
        """Replace entry contents without triggering undo."""
        self._block_undo = True
        self._entry.delete(0, tk.END)
        self._entry.insert(0, text)
        self._block_undo = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_expression(self) -> str:
        """Return the current expression text."""
        return self._entry.get().strip()

    def set_expression(self, expr: str) -> None:
        """Set the expression text (e.g., from history recall)."""
        self._set_text(expr)
        self._entry.icursor(tk.END)
        self._entry.focus_set()

    def append_to_expression(self, text: str) -> None:
        """Append text to the current expression."""
        current = self._entry.get()
        self._set_text(current + text)
        self._entry.icursor(tk.END)
        self._entry.focus_set()

    def insert_at_cursor(self, text: str) -> None:
        """Insert text at the current cursor position in the entry.

        Used by the virtual keypad to insert buttons at the cursor
        rather than always appending to the end.
        """
        try:
            pos = self._entry.index(tk.INSERT)
        except tk.TclError:
            pos = self._entry.index(tk.END)
        self._entry.insert(pos, text)
        self._entry.focus_set()

    def clear(self) -> str:
        """Clear the expression entry."""
        self._set_text("")
        self._history_index = -1
        self._saved_current = ""
        return "break"

    def get_history(self) -> list[str]:
        """Return a copy of the expression history."""
        return list(self._history)

    def focus_input(self) -> None:
        """Focus the expression entry."""
        self._entry.focus_set()

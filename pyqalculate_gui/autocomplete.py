"""Autocomplete popup for the expression editor.

Shows a popup with matching functions, variables, and units as the user
types.  Uses the scoring algorithm from the qalculate-gtk specification
(Section 7) to rank results by relevance.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

from pyqalculate_gui.theme import LIGHT, Theme
from pyqalculate_gui.i18n import _

if TYPE_CHECKING:
    from pyqalculate_gui.calculator_service import CalculatorService

# Characters that terminate a "word" for current-object detection.
_BREAK_CHARS = frozenset(" \t+-*/^()=,;<>!|&%²³")

_MAX_VISIBLE = 20


def _score_item(name: str, title: str, prefix: str) -> int:  # noqa: C901
    """Score a completion item against *prefix* (0–6).

    Scoring mirrors ``completion_sort_func`` in qalculate-gtk:

    * 6 — exact name match
    * 5 — name starts with prefix
    * 4 — title starts with prefix
    * 3 — name contains prefix
    * 2 — title contains prefix
    * 0 — no match
    """
    p = prefix.lower()
    n = name.lower()
    t = title.lower()

    if n == p:
        return 6
    if n.startswith(p):
        return 5
    if t.startswith(p):
        return 4
    if p in n:
        return 3
    if p in t:
        return 2
    return 0


class AutoComplete:
    """Autocomplete popup for the expression editor.

    Displays matching functions, variables, and units in a ``Toplevel``
    popup positioned below the parent widget.
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme = LIGHT,
        calculator: CalculatorService | None = None,
    ) -> None:
        self._parent = parent
        self._theme = theme
        self._calc = calculator

        # Popup state
        self._popup: tk.Toplevel | None = None
        self._tree: ttk.Treeview | None = None
        self._items: list[Tuple[str, str, str]] = []  # (name, title, type)
        self._filtered: list[Tuple[str, str, int]] = []  # (name, title, score)
        self._selected_index: int = 0
        self._visible: bool = False

        # Settings
        self._enabled: bool = True
        self._completion_min: int = 1
        self._completion_delay: int = 0  # ms
        self._delay_id: str | None = None

        # Callbacks
        self._on_select: Callable[[str], None] | None = None

        self._populate_items()

    # ------------------------------------------------------------------
    # Data population
    # ------------------------------------------------------------------

    def _populate_items(self) -> None:
        """Populate completion items from the calculator engine."""
        if not self._calc:
            return

        self._items = []

        for func in self._calc.get_functions():
            self._items.append((func, _("Function: {}").format(func), "function"))

        for var in self._calc.get_variables():
            self._items.append((var, _("Variable: {}").format(var), "variable"))

        for unit in self._calc.get_units():
            self._items.append((unit, _("Unit: {}").format(unit), "unit"))

        self._items.sort(key=lambda x: x[0].lower())

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _filter_items(self, prefix: str) -> None:
        """Score and filter items by *prefix*, keeping the top matches."""
        if not prefix:
            self._filtered = []
            return

        scored: list[Tuple[str, str, int]] = []
        for name, title, _type in self._items:
            score = _score_item(name, title, prefix)
            if score > 0:
                scored.append((name, title, score))

        # Sort: score descending, then name ascending
        scored.sort(key=lambda x: (-x[2], x[0].lower()))
        self._filtered = scored[:_MAX_VISIBLE]

    # ------------------------------------------------------------------
    # Popup lifecycle
    # ------------------------------------------------------------------

    def _create_popup(self) -> None:
        """Create the ``Toplevel`` popup window."""
        if self._popup is not None:
            return

        self._popup = tk.Toplevel(self._parent)
        self._popup.overrideredirect(True)
        self._popup.attributes("-topmost", True)

        frame = tk.Frame(self._popup, relief="solid", bd=1)
        frame.pack(fill=tk.BOTH, expand=True)

        self._tree = ttk.Treeview(
            frame,
            columns=("name", "title"),
            show="headings",
            height=8,
        )
        self._tree.heading("name", text=_("Name"))
        self._tree.heading("title", text=_("Description"))
        self._tree.column("name", width=150)
        self._tree.column("title", width=250)

        scrollbar = ttk.Scrollbar(
            frame, orient=tk.VERTICAL, command=self._tree.yview,
        )
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bindings
        self._tree.bind("<Double-1>", self._on_item_select)
        self._tree.bind("<Return>", self._on_item_select)
        self._popup.bind("<Escape>", lambda _e: self.hide())
        self._popup.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_out(self, event: tk.Event) -> None:
        """Hide popup when focus leaves — but not if focus moved to tree."""
        if self._popup is None:
            return
        try:
            focused = self._popup.focus_get()
        except (KeyError, tk.TclError):
            focused = None
        if focused is None or focused != self._tree:
            self.hide()

    def _update_popup(self) -> None:
        """Refresh the treeview contents and show or hide the popup."""
        if self._popup is None:
            self._create_popup()
        assert self._tree is not None

        for item in self._tree.get_children():
            self._tree.delete(item)

        for name, title, _score in self._filtered:
            self._tree.insert("", tk.END, values=(name, title))

        if self._filtered:
            self._show_popup()
            children = self._tree.get_children()
            if children:
                self._tree.selection_set(children[0])
                self._selected_index = 0
        else:
            self.hide()

    def _show_popup(self) -> None:
        """Position and display the popup below the parent widget."""
        if self._popup is None:
            return

        x = self._parent.winfo_rootx()
        y = self._parent.winfo_rooty() + self._parent.winfo_height()

        # Clamp to screen bounds
        sw = self._parent.winfo_screenwidth()
        sh = self._parent.winfo_screenheight()
        pw = self._popup.winfo_reqwidth()
        ph = self._popup.winfo_reqheight()
        if x + pw > sw:
            x = sw - pw
        if y + ph > sh:
            y = self._parent.winfo_rooty() - ph

        self._popup.geometry(f"+{x}+{y}")
        self._popup.deiconify()
        self._popup.focus_set()
        self._visible = True

    # ------------------------------------------------------------------
    # Selection handling
    # ------------------------------------------------------------------

    def _on_item_select(self, event: tk.Event | None = None) -> None:
        """Insert the selected completion and hide the popup."""
        if self._tree is None:
            return
        selection = self._tree.selection()
        if selection:
            name = self._tree.item(selection[0])["values"][0]
            if self._on_select is not None:
                self._on_select(str(name))
            self.hide()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_on_select(self, callback: Callable[[str], None]) -> None:
        """Register *callback* invoked with the selected item name."""
        self._on_select = callback

    def update(self, text: str, cursor_pos: int) -> None:
        """Update completions for *text* at *cursor_pos* (flat char index)."""
        if not self._enabled:
            self.hide()
            return

        # Walk backward to find the current word
        word_start = cursor_pos
        while word_start > 0 and text[word_start - 1] not in _BREAK_CHARS:
            word_start -= 1

        current_word = text[word_start:cursor_pos]

        if len(current_word) < self._completion_min:
            self.hide()
            return

        # Cancel any pending delayed completion
        if self._delay_id is not None:
            self._parent.after_cancel(self._delay_id)
            self._delay_id = None

        if self._completion_delay > 0:
            self._delay_id = self._parent.after(
                self._completion_delay,
                lambda: self._do_completion(current_word),
            )
        else:
            self._do_completion(current_word)

    def _do_completion(self, prefix: str) -> None:
        """Run the actual filter + popup update."""
        self._delay_id = None
        self._filter_items(prefix)
        self._update_popup()

    def hide(self) -> None:
        """Withdraw the popup."""
        if self._popup is not None:
            self._popup.withdraw()
        self._visible = False

    def is_visible(self) -> bool:
        """Return ``True`` when the popup is shown."""
        return self._visible

    def select_next(self) -> None:
        """Move selection to the next item."""
        if not self._visible or self._tree is None:
            return
        children = self._tree.get_children()
        if children:
            self._selected_index = (self._selected_index + 1) % len(children)
            self._tree.selection_set(children[self._selected_index])
            self._tree.see(children[self._selected_index])

    def select_previous(self) -> None:
        """Move selection to the previous item."""
        if not self._visible or self._tree is None:
            return
        children = self._tree.get_children()
        if children:
            self._selected_index = (self._selected_index - 1) % len(children)
            self._tree.selection_set(children[self._selected_index])
            self._tree.see(children[self._selected_index])

    def get_selected(self) -> str | None:
        """Return the name of the currently selected item, or ``None``."""
        if self._tree is None:
            return None
        selection = self._tree.selection()
        if selection:
            return str(self._tree.item(selection[0])["values"][0])
        return None

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the autocomplete system."""
        self._enabled = enabled
        if not enabled:
            self.hide()

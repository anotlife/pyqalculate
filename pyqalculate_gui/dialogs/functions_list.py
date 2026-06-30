"""Functions List dialog for browsing/searching mathematical functions.

Provides a searchable list of all available functions with descriptions.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pyqalculate_gui.calculator_service import CalculatorService, FunctionInfo
from pyqalculate_gui.dialogs.base import ModalDialog
from pyqalculate_gui.event_bus import EventBus
from pyqalculate_gui.i18n import _
from pyqalculate_gui.theme import LIGHT, Theme


class FunctionsListDialog(ModalDialog):
    """Dialog for browsing and searching mathematical functions."""

    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme = LIGHT,
        event_bus: EventBus | None = None,
        calculator: CalculatorService | None = None,
    ) -> None:
        super().__init__(
            parent,
            title=_("Functions"),
            size=(600, 500),
            resizable=(True, True),
            theme=theme,
            show_ok=False,
        )
        self._calculator = calculator
        self._event_bus = event_bus
        self._functions: list[str] = []
        self._search_var = tk.StringVar()
        self._name_var = tk.StringVar()
        self._listbox: tk.Listbox | None = None
        self._desc_text: tk.Text | None = None

    # ------------------------------------------------------------------
    # Content (ModalDialog contract)
    # ------------------------------------------------------------------

    def _build_content(self, parent: ttk.Frame) -> None:
        """Build the functions list dialog content."""
        # Search
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(search_frame, text=_("Search:")).pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self._search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        search_entry.bind("<KeyRelease>", self._on_search)

        # Split pane: list | details
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(paned)
        self._listbox = tk.Listbox(
            list_frame,
            font=self._theme.info_font,
            bg=self._theme.bg,
            fg=self._theme.fg,
            selectbackground=self._theme.select_bg,
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=scrollbar.set)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)
        paned.add(list_frame, weight=1)

        # Details pane
        details_frame = ttk.Frame(paned)
        ttk.Label(
            details_frame, textvariable=self._name_var, font=self._theme.result_font,
        ).pack(anchor=tk.W, pady=(0, 5))

        self._desc_text = tk.Text(
            details_frame,
            font=self._theme.info_font,
            bg=self._theme.bg,
            fg=self._theme.fg,
            wrap=tk.WORD,
            height=10,
            state=tk.DISABLED,
        )
        self._desc_text.pack(fill=tk.BOTH, expand=True)

        paned.add(details_frame, weight=2)

        self._load_functions()

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def _load_functions(self) -> None:
        """Load all functions from calculator."""
        if self._calculator is None:
            return
        self._functions = self._calculator.get_functions()
        self._update_list(self._functions)

    def _update_list(self, functions: list[str]) -> None:
        """Replace the listbox contents."""
        if self._listbox is None:
            return
        self._listbox.delete(0, tk.END)
        for func in functions:
            self._listbox.insert(tk.END, func)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_search(self, event: tk.Event | None = None) -> None:
        """Filter functions based on search text."""
        search = self._search_var.get().lower()
        if not search:
            self._update_list(self._functions)
        else:
            self._update_list([f for f in self._functions if search in f.lower()])

    def _on_select(self, event: tk.Event | None = None) -> None:
        """Show details for the selected function."""
        if self._listbox is None:
            return
        selection = self._listbox.curselection()
        if not selection:
            return
        func_name = self._listbox.get(selection[0])
        self._show_detail(func_name)

    def _show_detail(self, func_name: str) -> None:
        """Update the detail pane for *func_name*."""
        info = self._get_info(func_name)
        self._name_var.set(info.name)

        if self._desc_text is None:
            return
        self._desc_text.config(state=tk.NORMAL)
        self._desc_text.delete("1.0", tk.END)

        if info.description:
            self._desc_text.insert(tk.END, info.description + "\n\n")
        if info.category:
            self._desc_text.insert(tk.END, f"Category: {info.category}\n")
        self._desc_text.insert(tk.END, self._format_args(info))
        self._desc_text.config(state=tk.DISABLED)

    def _get_info(self, func_name: str) -> FunctionInfo:
        """Return metadata for *func_name*, falling back to defaults."""
        if self._calculator is not None:
            info = self._calculator.get_function_info(func_name)
            if info is not None:
                return info
        return FunctionInfo(
            name=func_name, title="", description="", category="",
            min_args=0, max_args=0,
        )

    @staticmethod
    def _format_args(info: FunctionInfo) -> str:
        """Format the argument-count line."""
        if info.min_args == info.max_args:
            return _("Arguments: {}").format(info.min_args)
        if info.max_args == -1:
            return _("Arguments: {} or more").format(info.min_args)
        return _("Arguments: {} to {}").format(info.min_args, info.max_args)

    def _insert_function(self) -> None:
        """Insert selected function name into the expression."""
        func_name = self._name_var.get()
        if func_name and self._event_bus is not None:
            self._event_bus.emit("keypad_insert", f"{func_name}(")
            self._result = True
            self._close()

    def _add_extra_buttons(self, btn_frame: ttk.Frame) -> None:
        ttk.Button(
            btn_frame, text=_("Insert into Expression"),
            command=self._insert_function,
        ).pack(side=tk.RIGHT, padx=5)

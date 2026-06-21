"""Sidebar widget for browsing variables, functions, and units.

Provides a tabbed view with searchable/filterable lists of calculator
definitions. Double-click inserts the item name into the input field.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from pyqalculate.calculator import Calculator


class SidebarWidget(ttk.Frame):
    """Tabbed sidebar showing variables, functions, and units.

    Signals:
        on_insert(text: str) - fired when user double-clicks an item
    """

    def __init__(
        self,
        parent: tk.Widget,
        calculator: Calculator,
        on_insert: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._calculator = calculator
        self._on_insert = on_insert
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the sidebar UI with tabs."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Search bar
        search_frame = ttk.Frame(self)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Filter:").grid(row=0, column=0, padx=(0, 4))
        self._search_var = tk.StringVar()
        self._search_entry = ttk.Entry(search_frame, textvariable=self._search_var)
        self._search_entry.grid(row=0, column=1, sticky="ew")
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        # Notebook (tabs)
        self._notebook = ttk.Notebook(self)
        self._notebook.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)

        # Variables tab
        self._vars_frame = ttk.Frame(self._notebook)
        self._notebook.add(self._vars_frame, text="Variables")
        self._vars_list = self._create_listbox(self._vars_frame)

        # Functions tab
        self._funcs_frame = ttk.Frame(self._notebook)
        self._notebook.add(self._funcs_frame, text="Functions")
        self._funcs_list = self._create_listbox(self._funcs_frame)

        # Units tab
        self._units_frame = ttk.Frame(self._notebook)
        self._notebook.add(self._units_frame, text="Units")
        self._units_list = self._create_listbox(self._units_frame)

        # Status label
        self._status_var = tk.StringVar(value="")
        self._status_label = ttk.Label(
            self, textvariable=self._status_var, foreground="#666666"
        )
        self._status_label.grid(row=2, column=0, sticky="w", pady=(2, 0))

        # Populate lists
        self.refresh()

    def _create_listbox(self, parent: tk.Widget) -> tk.Listbox:
        """Create a scrollable listbox in a parent frame."""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        listbox = tk.Listbox(
            frame,
            font=("Consolas", 10),
            activestyle="none",
            selectmode=tk.SINGLE,
            exportselection=False,
        )
        listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        listbox.config(yscrollcommand=scrollbar.set)

        # Double-click to insert
        listbox.bind("<Double-Button-1>", self._on_double_click)

        return listbox

    def refresh(self) -> None:
        """Refresh all lists from calculator definitions."""
        self._populate_variables()
        self._populate_functions()
        self._populate_units()
        self._update_status()

    def _populate_variables(self) -> None:
        """Populate the variables list."""
        self._vars_list.delete(0, tk.END)
        calc = self._calculator

        # Collect unique variables (avoid duplicates from name indexing)
        seen = set()
        for key, var in sorted(calc._variables.items()):
            if id(var) in seen:
                continue
            seen.add(id(var))
            name = var.name()
            category = var.category()
            if category:
                display = f"{name}  [{category}]"
            else:
                display = name
            self._vars_list.insert(tk.END, display)
            # Store reference for lookup
            self._vars_list._items = getattr(self._vars_list, "_items", [])
            if len(self._vars_list._items) < self._vars_list.size():
                self._vars_list._items.append(name)

    def _populate_functions(self) -> None:
        """Populate the functions list."""
        self._funcs_list.delete(0, tk.END)
        calc = self._calculator

        seen = set()
        for key, func in sorted(calc._functions.items()):
            if id(func) in seen:
                continue
            seen.add(id(func))
            name = func.name()
            category = func.category()
            argc = func.min_args()
            max_argc = func.max_args()
            if max_argc != argc:
                args_str = f"({argc}-{max_argc})"
            else:
                args_str = f"({argc})"
            if category:
                display = f"{name}{args_str}  [{category}]"
            else:
                display = f"{name}{args_str}"
            self._funcs_list.insert(tk.END, display)
            self._funcs_list._items = getattr(self._funcs_list, "_items", [])
            if len(self._funcs_list._items) < self._funcs_list.size():
                self._funcs_list._items.append(name)

    def _populate_units(self) -> None:
        """Populate the units list."""
        self._units_list.delete(0, tk.END)
        calc = self._calculator

        seen = set()
        for key, unit in sorted(calc._units.items()):
            if id(unit) in seen:
                continue
            seen.add(id(unit))
            name = unit.name()
            abbrev = unit.abbreviation()
            category = unit.category()
            if abbrev and abbrev != name:
                display = f"{name} ({abbrev})"
            else:
                display = name
            if category:
                display += f"  [{category}]"
            self._units_list.insert(tk.END, display)
            self._units_list._items = getattr(self._units_list, "_items", [])
            if len(self._units_list._items) < self._units_list.size():
                self._units_list._items.append(name)

    def _update_status(self) -> None:
        """Update the status label with counts."""
        calc = self._calculator
        n_vars = len(set(id(v) for v in calc._variables.values()))
        n_funcs = len(set(id(f) for f in calc._functions.values()))
        n_units = len(set(id(u) for u in calc._units.values()))
        self._status_var.set(
            f"Variables: {n_vars} | Functions: {n_funcs} | Units: {n_units}"
        )

    def _apply_filter(self) -> None:
        """Filter lists based on search text."""
        query = self._search_var.get().lower().strip()

        for listbox in (self._vars_list, self._funcs_list, self._units_list):
            items = getattr(listbox, "_items", [])
            listbox.delete(0, tk.END)

            # Rebuild from stored items + full display text
            # We need to re-populate with filter
            self._repopulate_filtered(listbox, query)

    def _repopulate_filtered(self, listbox: tk.Listbox, query: str) -> None:
        """Repopulate a listbox with filtered items."""
        # Determine which type this listbox is
        if listbox is self._vars_list:
            self._populate_variables_filtered(query)
        elif listbox is self._funcs_list:
            self._populate_functions_filtered(query)
        elif listbox is self._units_list:
            self._populate_units_filtered(query)

    def _populate_variables_filtered(self, query: str) -> None:
        """Populate variables list with filter."""
        self._vars_list.delete(0, tk.END)
        self._vars_list._items = []
        calc = self._calculator
        seen = set()
        for key, var in sorted(calc._variables.items()):
            if id(var) in seen:
                continue
            seen.add(id(var))
            name = var.name()
            category = var.category()
            # Check filter
            if query and query not in name.lower() and query not in category.lower():
                continue
            if category:
                display = f"{name}  [{category}]"
            else:
                display = name
            self._vars_list.insert(tk.END, display)
            self._vars_list._items.append(name)

    def _populate_functions_filtered(self, query: str) -> None:
        """Populate functions list with filter."""
        self._funcs_list.delete(0, tk.END)
        self._funcs_list._items = []
        calc = self._calculator
        seen = set()
        for key, func in sorted(calc._functions.items()):
            if id(func) in seen:
                continue
            seen.add(id(func))
            name = func.name()
            category = func.category()
            if query and query not in name.lower() and query not in category.lower():
                continue
            argc = func.min_args()
            max_argc = func.max_args()
            if max_argc != argc:
                args_str = f"({argc}-{max_argc})"
            else:
                args_str = f"({argc})"
            if category:
                display = f"{name}{args_str}  [{category}]"
            else:
                display = f"{name}{args_str}"
            self._funcs_list.insert(tk.END, display)
            self._funcs_list._items.append(name)

    def _populate_units_filtered(self, query: str) -> None:
        """Populate units list with filter."""
        self._units_list.delete(0, tk.END)
        self._units_list._items = []
        calc = self._calculator
        seen = set()
        for key, unit in sorted(calc._units.items()):
            if id(unit) in seen:
                continue
            seen.add(id(unit))
            name = unit.name()
            abbrev = unit.abbreviation()
            category = unit.category()
            if query and query not in name.lower() and query not in abbrev.lower() and query not in category.lower():
                continue
            if abbrev and abbrev != name:
                display = f"{name} ({abbrev})"
            else:
                display = name
            if category:
                display += f"  [{category}]"
            self._units_list.insert(tk.END, display)
            self._units_list._items.append(name)

    def _on_double_click(self, event: tk.Event) -> None:
        """Handle double-click on a list item."""
        listbox = event.widget
        selection = listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        items = getattr(listbox, "_items", [])
        if idx < len(items):
            name = items[idx]
            if self._on_insert:
                self._on_insert(name)

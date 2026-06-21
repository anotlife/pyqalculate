"""Unit conversion panel for PyQalculate GUI.

Provides a two-panel interface:
- Left: category tree (Length, Mass, Time, etc.)
- Right: unit list filtered by selected category
- Bottom: value input, target unit selector, result display

Supports real-time conversion, category filtering, unit search,
and copy-to-clipboard.
"""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from pyqalculate.calculator import Calculator


class ConversionView(ttk.Frame):
    """Unit conversion widget with category tree, unit list, and result display.

    Signals:
        on_convert(expr: str, result: str) - fired after successful conversion
    """

    # Category prefixes to strip for display
    _CATEGORY_PREFIXES = ("!units!",)

    def __init__(
        self,
        parent: tk.Misc,
        calculator: Calculator,
        on_convert: Callable[[str, str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._calc = calculator
        self._on_convert = on_convert

        # Category data: display_name -> full category string
        self._categories: dict[str, str] = {}
        # Unit data per category: category_str -> list of (display_name, unit_name)
        self._units_by_category: dict[str, list[tuple[str, str]]] = {}

        self._build_ui()
        self._populate_categories()

    # ==================================================================
    # UI construction
    # ==================================================================

    def _build_ui(self) -> None:
        """Build the conversion panel layout."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  # tree/list area expands
        self.rowconfigure(1, weight=0)  # conversion controls fixed

        # --- Top: category tree + unit list (paned) ---
        top_frame = ttk.Frame(self)
        top_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=2)
        top_frame.rowconfigure(0, weight=1)

        # Category tree (left)
        cat_frame = ttk.LabelFrame(top_frame, text="Categories", padding=4)
        cat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        cat_frame.columnconfigure(0, weight=1)
        cat_frame.rowconfigure(0, weight=1)

        self._cat_tree = ttk.Treeview(
            cat_frame, show="tree", selectmode="browse", height=12
        )
        self._cat_tree.grid(row=0, column=0, sticky="nsew")

        cat_scroll = ttk.Scrollbar(
            cat_frame, orient=tk.VERTICAL, command=self._cat_tree.yview
        )
        cat_scroll.grid(row=0, column=1, sticky="ns")
        self._cat_tree.config(yscrollcommand=cat_scroll.set)

        self._cat_tree.bind("<<TreeviewSelect>>", self._on_category_select)

        # Unit list (right) with search
        unit_frame = ttk.LabelFrame(top_frame, text="Units", padding=4)
        unit_frame.grid(row=0, column=1, sticky="nsew")
        unit_frame.columnconfigure(0, weight=1)
        unit_frame.rowconfigure(1, weight=1)

        # Unit search bar
        search_frame = ttk.Frame(unit_frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 4))
        self._unit_search_var = tk.StringVar()
        self._unit_search_entry = ttk.Entry(
            search_frame, textvariable=self._unit_search_var
        )
        self._unit_search_entry.grid(row=0, column=1, sticky="ew")
        self._unit_search_var.trace_add("write", lambda *_: self._filter_units())

        # Unit listbox
        list_frame = ttk.Frame(unit_frame)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._unit_listbox = tk.Listbox(
            list_frame,
            font=("Consolas", 10),
            activestyle="none",
            selectmode=tk.SINGLE,
            exportselection=False,
        )
        self._unit_listbox.grid(row=0, column=0, sticky="nsew")

        unit_scroll = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self._unit_listbox.yview
        )
        unit_scroll.grid(row=0, column=1, sticky="ns")
        self._unit_listbox.config(yscrollcommand=unit_scroll.set)

        self._unit_listbox.bind("<<ListboxSelect>>", self._on_unit_select)
        self._unit_listbox.bind("<Double-Button-1>", self._on_unit_double_click)

        # --- Bottom: conversion controls ---
        conv_frame = ttk.LabelFrame(self, text="Convert", padding=6)
        conv_frame.grid(row=1, column=0, sticky="ew")
        conv_frame.columnconfigure(1, weight=1)

        # Value input
        ttk.Label(conv_frame, text="Value:").grid(
            row=0, column=0, padx=(0, 4), sticky="w"
        )
        self._value_var = tk.StringVar(value="1")
        self._value_entry = ttk.Entry(
            conv_frame, textvariable=self._value_var, width=16, font=("Consolas", 11)
        )
        self._value_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self._value_var.trace_add("write", lambda *_: self._on_value_changed())

        # From unit display
        ttk.Label(conv_frame, text="From:").grid(
            row=0, column=2, padx=(0, 4), sticky="w"
        )
        self._from_unit_var = tk.StringVar(value="(select a unit)")
        self._from_unit_label = ttk.Label(
            conv_frame,
            textvariable=self._from_unit_var,
            font=("Consolas", 10, "bold"),
            foreground="#1a5276",
            width=16,
            anchor="w",
        )
        self._from_unit_label.grid(row=0, column=3, sticky="w", padx=(0, 8))

        # Target unit selector
        ttk.Label(conv_frame, text="To:").grid(
            row=1, column=0, padx=(0, 4), sticky="w", pady=(4, 0)
        )
        self._to_unit_var = tk.StringVar()
        self._to_unit_entry = ttk.Entry(
            conv_frame,
            textvariable=self._to_unit_var,
            width=16,
            font=("Consolas", 10),
        )
        self._to_unit_entry.grid(
            row=1, column=1, sticky="ew", padx=(0, 8), pady=(4, 0)
        )
        self._to_unit_entry.bind("<Return>", lambda e: self._do_convert())
        self._to_unit_var.trace_add("write", lambda *_: self._on_target_changed())

        # Convert button
        self._convert_btn = ttk.Button(
            conv_frame, text="Convert", command=self._do_convert
        )
        self._convert_btn.grid(row=1, column=2, columnspan=2, pady=(4, 0), sticky="ew")

        # Result display
        result_frame = ttk.Frame(conv_frame)
        result_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        result_frame.columnconfigure(0, weight=1)

        self._result_var = tk.StringVar(value="")
        self._result_label = ttk.Label(
            result_frame,
            textvariable=self._result_var,
            font=("Consolas", 12, "bold"),
            foreground="#1e8449",
            anchor="w",
            wraplength=500,
        )
        self._result_label.grid(row=0, column=0, sticky="ew")

        self._error_var = tk.StringVar(value="")
        self._error_label = ttk.Label(
            result_frame,
            textvariable=self._error_var,
            font=("Consolas", 10),
            foreground="#c0392b",
            anchor="w",
        )
        self._error_label.grid(row=1, column=0, sticky="ew")

        # Copy result button
        btn_row = ttk.Frame(result_frame)
        btn_row.grid(row=2, column=0, sticky="e", pady=(4, 0))
        self._copy_btn = ttk.Button(
            btn_row, text="Copy Result", command=self._copy_result
        )
        self._copy_btn.pack(side=tk.RIGHT)

        # Status label
        self._status_var = tk.StringVar(value="")
        ttk.Label(
            conv_frame,
            textvariable=self._status_var,
            foreground="#666666",
            font=("TkDefaultFont", 8),
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(4, 0))

    # ==================================================================
    # Category tree population
    # ==================================================================

    def _populate_categories(self) -> None:
        """Build the category tree from calculator units."""
        # Collect all categories
        cat_set: set[str] = set()
        for unit in self._calc._units.values():
            cat = unit.category()
            if cat:
                cat_set.add(cat)

        # Build parent->children mapping
        # Categories like "Electricity/Capacitance" have parent "Electricity"
        self._categories.clear()
        self._units_by_category.clear()

        # Normalize category names for display
        def display_name(cat: str) -> str:
            """Convert category string to display name."""
            name = cat
            for prefix in self._CATEGORY_PREFIXES:
                if name.startswith(prefix):
                    name = name[len(prefix):]
            # Handle subcategory: take last part
            if "/" in name:
                return name.split("/")[-1]
            return name

        # Organize into tree structure
        tree_data: dict[str, list[str]] = {}  # parent -> [children]
        root_cats: list[str] = []

        for cat in sorted(cat_set):
            parts = cat.split("/")
            if len(parts) == 1:
                root_cats.append(cat)
            else:
                parent = "/".join(parts[:-1])
                if parent not in tree_data:
                    tree_data[parent] = []
                tree_data[parent].append(cat)

        # Insert into treeview
        self._cat_tree.delete(*self._cat_tree.get_children())

        # Add "All" root node
        self._cat_tree.insert("", tk.END, iid="__all__", text="All Units", open=True)

        # Add root categories
        for cat in sorted(root_cats):
            dname = display_name(cat)
            iid = self._cat_tree.insert(
                "__all__", tk.END, text=dname, open=False
            )
            self._categories[iid] = cat

            # Add subcategories
            children = tree_data.get(cat, [])
            for child in sorted(children):
                cdname = display_name(child)
                ciid = self._cat_tree.insert(iid, tk.END, text=cdname)
                self._categories[ciid] = child

        # Pre-build unit lists per category
        self._build_unit_lists()

    def _build_unit_lists(self) -> None:
        """Build unit lists for each category."""
        self._units_by_category.clear()

        for unit in self._calc._units.values():
            if not unit.is_active():
                continue
            cat = unit.category()
            if not cat:
                cat = "Uncategorized"

            name = unit.name()
            abbrev = unit.abbreviation()
            singular = unit.singular()

            # Build display: "meter (m)" or just "meter"
            if abbrev and abbrev != name:
                display = f"{name} ({abbrev})"
            else:
                display = name

            if cat not in self._units_by_category:
                self._units_by_category[cat] = []
            self._units_by_category[cat].append((display, name))

        # Sort each category
        for cat in self._units_by_category:
            self._units_by_category[cat].sort(key=lambda x: x[0].lower())

    # ==================================================================
    # Event handlers
    # ==================================================================

    def _on_category_select(self, event: tk.Event) -> None:
        """Handle category selection change."""
        sel = self._cat_tree.selection()
        if not sel:
            return

        iid = sel[0]
        if iid == "__all__":
            # Show all units
            self._show_all_units()
        else:
            cat = self._categories.get(iid, "")
            self._show_units_for_category(cat)

        # Clear search
        self._unit_search_var.set("")

    def _show_all_units(self) -> None:
        """Show all units across all categories."""
        self._unit_listbox.delete(0, tk.END)
        self._current_units = []

        seen = set()
        for cat_units in self._units_by_category.values():
            for display, name in cat_units:
                if name not in seen:
                    seen.add(name)
                    self._current_units.append((display, name))

        self._current_units.sort(key=lambda x: x[0].lower())
        for display, _ in self._current_units:
            self._unit_listbox.insert(tk.END, display)

        self._status_var.set(f"{len(self._current_units)} units")

    def _show_units_for_category(self, category: str) -> None:
        """Show units for a specific category."""
        self._unit_listbox.delete(0, tk.END)
        self._current_units = []

        # Collect units from this category and subcategories
        seen = set()
        for cat, units in self._units_by_category.items():
            if cat == category or cat.startswith(category + "/"):
                for display, name in units:
                    if name not in seen:
                        seen.add(name)
                        self._current_units.append((display, name))

        self._current_units.sort(key=lambda x: x[0].lower())
        for display, _ in self._current_units:
            self._unit_listbox.insert(tk.END, display)

        self._status_var.set(f"{len(self._current_units)} units in {category}")

    def _filter_units(self) -> None:
        """Filter unit list by search text."""
        query = self._unit_search_var.get().lower().strip()
        self._unit_listbox.delete(0, tk.END)

        if not query:
            # Show current category units
            for display, _ in getattr(self, "_current_units", []):
                self._unit_listbox.insert(tk.END, display)
            return

        filtered = []
        for display, name in getattr(self, "_current_units", []):
            if query in display.lower() or query in name.lower():
                filtered.append((display, name))

        for display, _ in filtered:
            self._unit_listbox.insert(tk.END, display)

        self._status_var.set(f"{len(filtered)} matching units")

    def _on_unit_select(self, event: tk.Event) -> None:
        """Handle unit selection - update from unit display."""
        sel = self._unit_listbox.curselection()
        if not sel:
            return

        idx = sel[0]
        units = getattr(self, "_current_units", [])
        if idx >= len(units):
            return

        display, name = units[idx]
        self._from_unit_var.set(display)
        self._selected_from_unit = name

        # Auto-convert if value is set
        self._maybe_auto_convert()

    def _on_unit_double_click(self, event: tk.Event) -> None:
        """Handle double-click on unit - convert immediately."""
        sel = self._unit_listbox.curselection()
        if not sel:
            return

        idx = sel[0]
        units = getattr(self, "_current_units", [])
        if idx >= len(units):
            return

        display, name = units[idx]
        self._from_unit_var.set(display)
        self._selected_from_unit = name
        self._do_convert()

    def _on_value_changed(self) -> None:
        """Handle value input change."""
        self._maybe_auto_convert()

    def _on_target_changed(self) -> None:
        """Handle target unit input change."""
        self._maybe_auto_convert()

    def _maybe_auto_convert(self) -> None:
        """Auto-convert if all fields are set."""
        value_str = self._value_var.get().strip()
        target = self._to_unit_var.get().strip()
        from_unit = getattr(self, "_selected_from_unit", None)

        if value_str and target and from_unit:
            self._do_convert()

    # ==================================================================
    # Conversion logic
    # ==================================================================

    def _do_convert(self) -> None:
        """Perform the unit conversion."""
        # Clear previous results
        self._result_var.set("")
        self._error_var.set("")

        # Validate inputs
        value_str = self._value_var.get().strip()
        if not value_str:
            self._error_var.set("Enter a value to convert")
            return

        try:
            value = float(value_str)
        except ValueError:
            self._error_var.set(f"Invalid number: {value_str}")
            return

        from_unit_name = getattr(self, "_selected_from_unit", None)
        if not from_unit_name:
            self._error_var.set("Select a source unit from the list")
            return

        target_str = self._to_unit_var.get().strip()
        if not target_str:
            self._error_var.set("Enter a target unit")
            return

        # Look up units
        from_unit = self._calc.get_unit(from_unit_name)
        to_unit = self._calc.get_unit(target_str)

        if from_unit is None:
            self._error_var.set(f"Unknown unit: {from_unit_name}")
            return

        if to_unit is None:
            # Try common aliases
            to_unit = self._try_resolve_unit(target_str)
            if to_unit is None:
                self._error_var.set(f"Unknown target unit: {target_str}")
                return

        # Perform conversion
        try:
            result = self._calc.convert(value, from_unit, to_unit)
        except Exception as e:
            self._error_var.set(f"Conversion error: {e}")
            return

        if result is None:
            self._error_var.set(
                f"Cannot convert {from_unit.name()} to {to_unit.name()}"
            )
            return

        # Format result
        result_str = self._format_result(result, to_unit)
        self._result_var.set(result_str)
        self._error_var.set("")

        # Notify callback
        expr = f"{value} {from_unit.abbreviation()} to {to_unit.abbreviation()}"
        if self._on_convert:
            self._on_convert(expr, result_str)

    def _try_resolve_unit(self, name: str):
        """Try various strategies to resolve a unit name."""
        # Direct lookup
        unit = self._calc.get_unit(name)
        if unit:
            return unit

        # Try as abbreviation
        for u in self._calc._units.values():
            if u.abbreviation().lower() == name.lower():
                return u
            if u.singular().lower() == name.lower():
                return u
            if u.plural().lower() == name.lower():
                return u

        return None

    def _format_result(self, value: float, unit) -> str:
        """Format a conversion result for display."""
        # Format number
        if abs(value) == 0:
            num_str = "0"
        elif abs(value) >= 1e15 or (abs(value) < 1e-6 and abs(value) > 0):
            num_str = f"{value:.6e}"
        elif value == int(value):
            num_str = str(int(value))
        else:
            # Smart decimal places
            num_str = f"{value:.10g}"

        abbrev = unit.abbreviation()
        if abbrev and abbrev != unit.name():
            return f"{num_str} {abbrev}"
        return f"{num_str} {unit.name()}"

    # ==================================================================
    # Clipboard
    # ==================================================================

    def _copy_result(self) -> None:
        """Copy the last result to clipboard."""
        result = self._result_var.get()
        if result:
            self.clipboard_clear()
            self.clipboard_append(result)

    # ==================================================================
    # Public API
    # ==================================================================

    def get_last_result(self) -> str:
        """Return the last conversion result string."""
        return self._result_var.get()

    def set_value(self, value: str) -> None:
        """Set the input value."""
        self._value_var.set(value)

    def set_from_unit(self, unit_name: str) -> None:
        """Set the source unit by name."""
        unit = self._calc.get_unit(unit_name)
        if unit:
            self._selected_from_unit = unit.name()
            abbrev = unit.abbreviation()
            if abbrev and abbrev != unit.name():
                self._from_unit_var.set(f"{unit.name()} ({abbrev})")
            else:
                self._from_unit_var.set(unit.name())

    def set_target_unit(self, unit_name: str) -> None:
        """Set the target unit by name."""
        self._to_unit_var.set(unit_name)

    def convert(self, value: str, from_unit: str, to_unit: str) -> str | None:
        """Programmatic conversion. Returns result string or None."""
        self.set_value(value)
        self.set_from_unit(from_unit)
        self.set_target_unit(to_unit)
        self._do_convert()
        result = self._result_var.get()
        return result if result else None

    def focus_target(self) -> None:
        """Focus the target unit entry."""
        self._to_unit_entry.focus_set()

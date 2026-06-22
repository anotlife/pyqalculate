"""Unit conversion panel for PyQalculate GUI.

Two-panel interface: category tree on the left, unit list on the right.
Bottom bar holds value input, target unit entry, and result display.
All colours and fonts derive from the active Theme — zero hardcoded
values.  Communication uses the EventBus (``CONVERSION_RESULT`` event).

Public API
----------
``set_value(v)``       – set the numeric input
``set_target_unit(u)`` – set the target unit entry
``convert()``          – trigger conversion programmatically
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pyqalculate_gui.calculator_service import CalculatorService
from pyqalculate_gui.event_bus import CONVERSION_RESULT, EventBus
from pyqalculate_gui.theme import LIGHT, Theme

# Treeview sentinel that represents "show every unit"
_ALL_NODE = "__all__"


class ConversionView(ttk.Frame):
    """Unit-conversion widget with category tree, unit list, and result."""

    def __init__(
        self,
        parent: tk.Misc,
        theme: Theme = LIGHT,
        event_bus: EventBus | None = None,
        calculator: CalculatorService | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._event_bus = event_bus
        self._calc = calculator

        # Internal state --------------------------------------------------
        # category iid → raw category string (e.g. "Length", "Electricity/Capacitance")
        self._cat_map: dict[str, str] = {}
        # raw category → list of (display_name, unit_key)
        self._units_by_cat: dict[str, list[tuple[str, str]]] = {}
        # flat list currently shown in the listbox
        self._current_units: list[tuple[str, str]] = []
        # key of the source unit selected from the list
        self._selected_from_key: str | None = None

        self._build_ui()
        if self._calc is not None:
            self._populate_categories()

    # ==================================================================
    # UI construction
    # ==================================================================

    def _build_ui(self) -> None:
        """Build the full conversion panel layout."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  # tree/list area expands
        self.rowconfigure(1, weight=0)  # conversion controls fixed

        self._build_browse_area()
        self._build_conversion_area()

    def _build_browse_area(self) -> None:
        """Category tree + unit list with search."""
        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(0, weight=1)

        # --- category tree (left) ---
        cat_outer = ttk.LabelFrame(frame, text="Categories", padding=4)
        cat_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        cat_outer.columnconfigure(0, weight=1)
        cat_outer.rowconfigure(0, weight=1)

        self._cat_tree = ttk.Treeview(
            cat_outer, show="tree", selectmode="browse", height=12,
        )
        self._cat_tree.grid(row=0, column=0, sticky="nsew")

        cat_scroll = ttk.Scrollbar(
            cat_outer, orient=tk.VERTICAL, command=self._cat_tree.yview,
        )
        cat_scroll.grid(row=0, column=1, sticky="ns")
        self._cat_tree.config(yscrollcommand=cat_scroll.set)
        self._cat_tree.bind("<<TreeviewSelect>>", self._on_category_select)

        # --- unit list (right) with search ---
        unit_outer = ttk.LabelFrame(frame, text="Units", padding=4)
        unit_outer.grid(row=0, column=1, sticky="nsew")
        unit_outer.columnconfigure(0, weight=1)
        unit_outer.rowconfigure(1, weight=1)

        # search bar
        search_frame = ttk.Frame(unit_outer)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 4))
        self._search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self._search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        self._search_var.trace_add("write", lambda *_: self._filter_units())

        # listbox
        list_frame = ttk.Frame(unit_outer)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._unit_listbox = tk.Listbox(
            list_frame,
            font=self._theme.info_font,
            activestyle="none",
            selectmode=tk.SINGLE,
            exportselection=False,
        )
        self._unit_listbox.grid(row=0, column=0, sticky="nsew")

        unit_scroll = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self._unit_listbox.yview,
        )
        unit_scroll.grid(row=0, column=1, sticky="ns")
        self._unit_listbox.config(yscrollcommand=unit_scroll.set)

        self._unit_listbox.bind("<<ListboxSelect>>", self._on_unit_select)
        self._unit_listbox.bind("<Double-Button-1>", self._on_unit_double_click)

    def _build_conversion_area(self) -> None:
        """Value entry, from/to display, convert button, result."""
        conv = ttk.LabelFrame(self, text="Convert", padding=6)
        conv.grid(row=1, column=0, sticky="ew")
        conv.columnconfigure(1, weight=1)

        # row 0 – value + from unit
        ttk.Label(conv, text="Value:").grid(row=0, column=0, sticky="w", padx=(0, 4))
        self._value_var = tk.StringVar(value="1")
        self._value_entry = ttk.Entry(
            conv, textvariable=self._value_var, width=16,
            font=self._theme.expression_font,
        )
        self._value_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self._value_var.trace_add("write", lambda *_: self._maybe_auto_convert())

        ttk.Label(conv, text="From:").grid(row=0, column=2, sticky="w", padx=(0, 4))
        self._from_var = tk.StringVar(value="(select a unit)")
        self._from_label = ttk.Label(
            conv,
            textvariable=self._from_var,
            font=self._theme.info_font,
            foreground=self._theme.result_fg,
            width=18,
            anchor="w",
        )
        self._from_label.grid(row=0, column=3, sticky="w")

        # row 1 – target unit + convert
        ttk.Label(conv, text="To:").grid(
            row=1, column=0, sticky="w", padx=(0, 4), pady=(4, 0),
        )
        self._to_var = tk.StringVar()
        to_entry = ttk.Entry(
            conv, textvariable=self._to_var, width=16,
            font=self._theme.info_font,
        )
        to_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(4, 0))
        to_entry.bind("<Return>", lambda _: self._do_convert())
        self._to_var.trace_add("write", lambda *_: self._maybe_auto_convert())

        ttk.Button(conv, text="Convert", command=self._do_convert).grid(
            row=1, column=2, columnspan=2, sticky="ew", pady=(4, 0),
        )

        # row 2 – result + error + copy
        result_frame = ttk.Frame(conv)
        result_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        result_frame.columnconfigure(0, weight=1)

        self._result_var = tk.StringVar()
        self._result_label = ttk.Label(
            result_frame,
            textvariable=self._result_var,
            font=self._theme.result_font,
            foreground=self._theme.result_fg,
            anchor="w",
            wraplength=500,
        )
        self._result_label.grid(row=0, column=0, sticky="ew")

        self._error_var = tk.StringVar()
        self._error_label = ttk.Label(
            result_frame,
            textvariable=self._error_var,
            font=self._theme.info_font,
            foreground=self._theme.error_fg,
            anchor="w",
        )
        self._error_label.grid(row=1, column=0, sticky="ew")

        btn_row = ttk.Frame(result_frame)
        btn_row.grid(row=2, column=0, sticky="e", pady=(4, 0))
        ttk.Button(btn_row, text="Copy Result", command=self._copy_result).pack(
            side=tk.RIGHT,
        )

        # status line
        self._status_var = tk.StringVar()
        self._status_label = ttk.Label(
            conv,
            textvariable=self._status_var,
            foreground=self._theme.separator_fg,
            font=self._theme.info_font,
        )
        self._status_label.grid(row=3, column=0, columnspan=4, sticky="w", pady=(4, 0))

    # ==================================================================
    # Category tree population
    # ==================================================================

    def _populate_categories(self) -> None:
        """Build the category tree from calculator unit data."""
        if self._calc is None:
            return
        raw_cats = self._calc.get_unit_categories()

        # Organize into parent → children mapping
        tree_children: dict[str, list[str]] = {}
        roots: list[str] = []
        for cat in sorted(raw_cats):
            parts = cat.split("/")
            if len(parts) == 1:
                roots.append(cat)
            else:
                parent = "/".join(parts[:-1])
                tree_children.setdefault(parent, []).append(cat)

        self._cat_tree.delete(*self._cat_tree.get_children())
        self._cat_map.clear()
        self._units_by_cat.clear()

        # "All Units" root node
        all_iid = self._cat_tree.insert(
            "", tk.END, iid=_ALL_NODE, text="All Units", open=True,
        )

        for cat in sorted(roots):
            display = cat.split("/")[-1]
            iid = self._cat_tree.insert(all_iid, tk.END, text=display, open=False)
            self._cat_map[iid] = cat

            for child in sorted(tree_children.get(cat, [])):
                child_display = child.split("/")[-1]
                ciid = self._cat_tree.insert(iid, tk.END, text=child_display)
                self._cat_map[ciid] = child

        # Pre-build per-category unit lists
        calc = self._calc
        for cat, keys in raw_cats.items():
            entries = [
                (calc.get_unit_display_name(k), k) for k in keys
            ]
            entries.sort(key=lambda e: e[0].lower())
            self._units_by_cat[cat] = entries

    # ==================================================================
    # Event handlers
    # ==================================================================

    def _on_category_select(self, _event: tk.Event) -> None:
        """Rebuild the unit list for the chosen category."""
        sel = self._cat_tree.selection()
        if not sel:
            return
        iid = sel[0]
        if iid == _ALL_NODE:
            self._show_all_units()
        else:
            cat = self._cat_map.get(iid, "")
            self._show_units_for_category(cat)
        self._search_var.set("")

    def _show_all_units(self) -> None:
        """Populate the listbox with every active unit."""
        seen: set[str] = set()
        self._current_units = []
        for entries in self._units_by_cat.values():
            for display, key in entries:
                if key not in seen:
                    seen.add(key)
                    self._current_units.append((display, key))
        self._current_units.sort(key=lambda e: e[0].lower())
        self._refresh_listbox()
        self._status_var.set(f"{len(self._current_units)} units")

    def _show_units_for_category(self, category: str) -> None:
        """Populate the listbox for *category* and its sub-categories."""
        seen: set[str] = set()
        self._current_units = []
        for cat, entries in self._units_by_cat.items():
            if cat == category or cat.startswith(category + "/"):
                for display, key in entries:
                    if key not in seen:
                        seen.add(key)
                        self._current_units.append((display, key))
        self._current_units.sort(key=lambda e: e[0].lower())
        self._refresh_listbox()
        self._status_var.set(f"{len(self._current_units)} units in {category}")

    def _filter_units(self) -> None:
        """Filter the listbox by search text."""
        query = self._search_var.get().lower().strip()
        if not query:
            self._refresh_listbox()
            return
        filtered = [
            (d, k) for d, k in self._current_units
            if query in d.lower() or query in k.lower()
        ]
        self._unit_listbox.delete(0, tk.END)
        for display, _ in filtered:
            self._unit_listbox.insert(tk.END, display)
        self._status_var.set(f"{len(filtered)} matching units")

    def _refresh_listbox(self) -> None:
        """Reload the listbox from ``_current_units``."""
        self._unit_listbox.delete(0, tk.END)
        for display, _ in self._current_units:
            self._unit_listbox.insert(tk.END, display)

    def _on_unit_select(self, _event: tk.Event) -> None:
        """Single-click: select source unit."""
        self._apply_selection()

    def _on_unit_double_click(self, _event: tk.Event) -> None:
        """Double-click: select source unit and convert immediately."""
        self._apply_selection()
        self._do_convert()

    def _apply_selection(self) -> None:
        """Update the *From* display from the current listbox selection."""
        sel = self._unit_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._current_units):
            return
        display, key = self._current_units[idx]
        self._from_var.set(display)
        self._selected_from_key = key
        self._maybe_auto_convert()

    def _maybe_auto_convert(self) -> None:
        """Auto-convert when all three fields are populated."""
        if self._value_var.get().strip() and self._to_var.get().strip() and self._selected_from_key:
            self._do_convert()

    # ==================================================================
    # Conversion logic
    # ==================================================================

    def _do_convert(self) -> None:
        """Perform the unit conversion."""
        self._result_var.set("")
        self._error_var.set("")

        value_str = self._value_var.get().strip()
        if not value_str:
            self._error_var.set("Enter a value to convert")
            return

        from_key = self._selected_from_key
        if not from_key:
            self._error_var.set("Select a source unit from the list")
            return

        to_str = self._to_var.get().strip()
        if not to_str:
            self._error_var.set("Enter a target unit")
            return

        if not self._calc:
            self._error_var.set("No calculator available")
            return

        try:
            result = self._calc.convert(value_str, from_key, to_str)
        except Exception as exc:
            self._error_var.set(f"Conversion error: {exc}")
            return

        if not result:
            self._error_var.set(f"Cannot convert {from_key} to {to_str}")
            return

        self._result_var.set(result)
        if self._event_bus is not None:
            expr = f"{value_str} {from_key} to {to_str}"
            self._event_bus.emit(CONVERSION_RESULT, expr, result)

    # ==================================================================
    # Clipboard
    # ==================================================================

    def _copy_result(self) -> None:
        result = self._result_var.get()
        if result:
            self.clipboard_clear()
            self.clipboard_append(result)

    # ==================================================================
    # Public API
    # ==================================================================

    def set_value(self, value: str) -> None:
        """Set the numeric input value."""
        self._value_var.set(value)

    def set_target_unit(self, unit: str) -> None:
        """Set the target unit entry."""
        self._to_var.set(unit)

    def convert(self) -> None:
        """Trigger conversion programmatically."""
        self._do_convert()

    def get_last_result(self) -> str:
        """Return the last conversion result string."""
        return self._result_var.get()

    def focus_target(self) -> None:
        """Focus the target unit entry."""
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame) and child.cget("text") == "Convert":
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Entry) and sub.cget("textvariable") == str(self._to_var):
                        sub.focus_set()
                        return

    def set_theme(self, theme: Theme) -> None:
        """Update the widget's theme."""
        self._theme = theme
        self._unit_listbox.config(
            font=theme.info_font,
            bg=theme.bg,
            fg=theme.fg,
        )
        self._from_label.config(font=theme.info_font, foreground=theme.result_fg)
        self._result_label.config(font=theme.result_font, foreground=theme.result_fg)
        self._error_label.config(font=theme.info_font, foreground=theme.error_fg)
        self._status_label.config(font=theme.info_font, foreground=theme.separator_fg)

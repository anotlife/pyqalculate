"""Export CSV dialog for PyQalculate GUI.

Provides a dialog for exporting matrix/vector data from the calculator
to CSV files. Supports exporting either the current result or a named
variable, with configurable delimiters.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable

from pyqalculate_gui.calculator_service import CalculatorService
from pyqalculate_gui.dialogs.base import ModalDialog
from pyqalculate_gui.theme import LIGHT, Theme


_DELIMITER_MAP: dict[str, str] = {
    "comma": ",",
    "tab": "\t",
    "semicolon": ";",
    "space": " ",
}


class ExportCsvDialog(ModalDialog):
    """Modal dialog for exporting data to CSV.

    Fields:
    - Data source (current result or named variable)
    - Variable name entry (for named variable source)
    - File path (with save-as browse button)
    - Delimiter (comma / tab / semicolon / space / other)
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme = LIGHT,
        calculator: CalculatorService | None = None,
        get_last_result: Callable[[], object | None] | None = None,
    ) -> None:
        super().__init__(parent, "Export CSV", size=(480, 340), theme=theme)
        self._calc = calculator
        self._get_last_result = get_last_result

    def _build_content(self, parent: ttk.Frame) -> None:
        """Build the dialog UI."""
        # --- Data source ---
        ttk.Label(parent, text="Source:").grid(row=0, column=0, sticky="w", pady=4)
        source_frame = ttk.Frame(parent)
        source_frame.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)
        parent.columnconfigure(1, weight=1)

        self._source_var = tk.StringVar(value="variable")
        ttk.Radiobutton(
            source_frame, text="Named variable",
            variable=self._source_var, value="variable",
            command=self._on_source_change,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            source_frame, text="Current result",
            variable=self._source_var, value="result",
            command=self._on_source_change,
        ).pack(anchor=tk.W)

        # --- Variable name ---
        ttk.Label(parent, text="Variable:").grid(row=1, column=0, sticky="w", pady=4)
        self._var_name_var = tk.StringVar()
        self._var_name_entry = ttk.Entry(parent, textvariable=self._var_name_var, width=30)
        self._var_name_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)

        # --- File path ---
        ttk.Label(parent, text="File:").grid(row=2, column=0, sticky="w", pady=4)
        file_frame = ttk.Frame(parent)
        file_frame.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)

        self._file_var = tk.StringVar()
        self._file_entry = ttk.Entry(file_frame, textvariable=self._file_var, width=35)
        self._file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse...", command=self._browse_file).pack(
            side=tk.LEFT, padx=(4, 0),
        )

        # --- Delimiter ---
        ttk.Label(parent, text="Delimiter:").grid(row=3, column=0, sticky="w", pady=4)
        delim_frame = ttk.Frame(parent)
        delim_frame.grid(row=3, column=1, columnspan=2, sticky="ew", pady=4)

        self._delimiter_var = tk.StringVar(value=",")
        self._delimiter_choice = tk.StringVar(value="comma")

        delim_options = [
            ("Comma", "comma"),
            ("Tab", "tab"),
            ("Semicolon", "semicolon"),
            ("Space", "space"),
            ("Other", "other"),
        ]
        for text, val in delim_options:
            ttk.Radiobutton(
                delim_frame, text=text, variable=self._delimiter_choice,
                value=val, command=self._on_delimiter_change,
            ).pack(side=tk.LEFT, padx=2)

        self._other_delim_entry = ttk.Entry(
            delim_frame, textvariable=self._delimiter_var, width=4, state="disabled",
        )
        self._other_delim_entry.pack(side=tk.LEFT, padx=(8, 0))

    # ------------------------------------------------------------------
    # UI callbacks
    # ------------------------------------------------------------------

    def _on_source_change(self) -> None:
        """Toggle variable name entry based on source selection."""
        if self._source_var.get() == "variable":
            self._var_name_entry.config(state="normal")
        else:
            self._var_name_entry.config(state="disabled")

    def _on_delimiter_change(self) -> None:
        """Handle delimiter radio button change."""
        choice = self._delimiter_choice.get()
        if choice == "other":
            self._other_delim_entry.config(state="normal")
        else:
            self._other_delim_entry.config(state="disabled")
            self._delimiter_var.set(_DELIMITER_MAP.get(choice, ","))

    def _browse_file(self) -> None:
        """Open save-file dialog."""
        path = filedialog.asksaveasfilename(
            parent=self._dialog,  # type: ignore[arg-type]
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self._file_var.set(path)

    # ------------------------------------------------------------------
    # Override ModalDialog hooks
    # ------------------------------------------------------------------

    def _on_ok(self) -> None:
        """Validate inputs and perform the CSV export."""
        filename = self._file_var.get().strip()
        if not filename:
            messagebox.showerror(
                "Error", "Please specify an output file.",
                parent=self._dialog,  # type: ignore[arg-type]
            )
            return

        delimiter = self._delimiter_var.get() or ","

        # Resolve the data source
        mstruct = None

        if self._source_var.get() == "variable":
            var_name = self._var_name_var.get().strip()
            if not var_name:
                messagebox.showerror(
                    "Error", "Please enter a variable name.",
                    parent=self._dialog,  # type: ignore[arg-type]
                )
                return
            if self._calc is None:
                messagebox.showerror(
                    "Error", "No calculator available.",
                    parent=self._dialog,  # type: ignore[arg-type]
                )
                return
            var = self._calc._calc.get_variable(var_name)
            if var is None:
                messagebox.showerror(
                    "Error", f"Variable '{var_name}' not found.",
                    parent=self._dialog,  # type: ignore[arg-type]
                )
                return
            from pyqalculate.variable import KnownVariable

            if isinstance(var, KnownVariable):
                mstruct = var.get()
        else:
            if self._get_last_result is not None:
                mstruct = self._get_last_result()

        if mstruct is None or self._calc is None:
            messagebox.showerror(
                "Error", "No data to export.",
                parent=self._dialog,  # type: ignore[arg-type]
            )
            return

        try:
            success = self._calc._calc.exportCSV(mstruct, filename, delimiter=delimiter)  # type: ignore[union-attr]
            if success:
                messagebox.showinfo(
                    "Export Successful",
                    f"Data exported to {filename}",
                    parent=self._dialog,  # type: ignore[arg-type]
                )
                super()._on_ok()
            else:
                messagebox.showerror(
                    "Export Failed",
                    "Could not write the CSV file.",
                    parent=self._dialog,  # type: ignore[arg-type]
                )
        except Exception as e:
            messagebox.showerror(
                "Export Error", str(e),
                parent=self._dialog,  # type: ignore[arg-type]
            )

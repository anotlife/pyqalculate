"""Export CSV dialog for PyQalculate GUI.

Provides a dialog for exporting matrix/vector data from the calculator
to CSV files. Supports exporting either the current result or a named
variable, with configurable delimiters.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from pyqalculate.calculator import Calculator
    from pyqalculate.math_structure import MathStructure


class ExportCsvDialog:
    """Modal dialog for exporting data to CSV.

    Fields:
    - Data source (current result or named variable)
    - Variable name entry (for named variable source)
    - File path (with save-as browse button)
    - Delimiter (comma / tab / semicolon / space / other)
    """

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        calculator: Calculator,
        get_last_result: Optional[Callable[[], Optional[MathStructure]]] = None,
    ) -> None:
        self._parent = parent
        self._calculator = calculator
        self._get_last_result = get_last_result
        self._dialog: tk.Toplevel | None = None

    def show(self, variable_name: str = "") -> None:
        """Open the export CSV dialog.

        Args:
            variable_name: Pre-fill the variable name (e.g., when called
                          from a variables dialog).
        """
        if self._dialog is not None and self._dialog.winfo_exists():
            self._dialog.lift()
            return

        self._dialog = tk.Toplevel(self._parent)
        self._dialog.title("Export CSV")
        self._dialog.geometry("480x340")
        self._dialog.resizable(False, False)
        self._dialog.transient(self._parent)
        self._dialog.grab_set()

        self._build_ui(variable_name)
        self._dialog.protocol("WM_DELETE_WINDOW", self._close)

    def _build_ui(self, prefill_name: str) -> None:
        """Build the dialog UI."""
        frame = ttk.Frame(self._dialog, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        # --- Data source ---
        ttk.Label(frame, text="Source:").grid(row=0, column=0, sticky="w", pady=4)
        source_frame = ttk.Frame(frame)
        source_frame.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)
        frame.columnconfigure(1, weight=1)

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
        ttk.Label(frame, text="Variable:").grid(row=1, column=0, sticky="w", pady=4)
        self._var_name_var = tk.StringVar(value=prefill_name)
        self._var_name_entry = ttk.Entry(frame, textvariable=self._var_name_var, width=30)
        self._var_name_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)

        # --- File path ---
        ttk.Label(frame, text="File:").grid(row=2, column=0, sticky="w", pady=4)
        file_frame = ttk.Frame(frame)
        file_frame.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)

        self._file_var = tk.StringVar()
        self._file_entry = ttk.Entry(file_frame, textvariable=self._file_var, width=35)
        self._file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse...", command=self._browse_file).pack(
            side=tk.LEFT, padx=(4, 0)
        )

        # --- Delimiter ---
        ttk.Label(frame, text="Delimiter:").grid(row=3, column=0, sticky="w", pady=4)
        delim_frame = ttk.Frame(frame)
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
            delim_frame, textvariable=self._delimiter_var, width=4, state="disabled"
        )
        self._other_delim_entry.pack(side=tk.LEFT, padx=(8, 0))

        # --- Buttons ---
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=(16, 0))

        ttk.Button(btn_frame, text="Export", command=self._do_export).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_frame, text="Cancel", command=self._close).pack(
            side=tk.LEFT, padx=4
        )

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
            delim_map = {
                "comma": ",",
                "tab": "\t",
                "semicolon": ";",
                "space": " ",
            }
            self._delimiter_var.set(delim_map.get(choice, ","))

    def _browse_file(self) -> None:
        """Open save-file dialog."""
        path = filedialog.asksaveasfilename(
            parent=self._dialog,
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self._file_var.set(path)

    def _do_export(self) -> None:
        """Validate inputs and perform the CSV export."""
        filename = self._file_var.get().strip()
        if not filename:
            messagebox.showerror("Error", "Please specify an output file.", parent=self._dialog)  # type: ignore[arg-type]
            return

        delimiter = self._delimiter_var.get()
        if not delimiter:
            delimiter = ","

        # Resolve the data source
        mstruct: MathStructure | None = None

        if self._source_var.get() == "variable":
            var_name = self._var_name_var.get().strip()
            if not var_name:
                messagebox.showerror("Error", "Please enter a variable name.", parent=self._dialog)  # type: ignore[arg-type]
                return
            var = self._calculator.get_variable(var_name)
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
            # Current result
            if self._get_last_result is not None:
                mstruct = self._get_last_result()

        if mstruct is None:
            messagebox.showerror(
                "Error", "No data to export.",
                parent=self._dialog,  # type: ignore[arg-type]
            )
            return

        try:
            success = self._calculator.exportCSV(mstruct, filename, delimiter=delimiter)
            if success:
                messagebox.showinfo(
                    "Export Successful",
                    f"Data exported to {filename}",
                    parent=self._dialog,  # type: ignore[arg-type]
                )
                self._close()
            else:
                messagebox.showerror(
                    "Export Failed",
                    "Could not write the CSV file.",
                    parent=self._dialog,  # type: ignore[arg-type]
                )
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self._dialog)  # type: ignore[arg-type]

    def _close(self) -> None:
        """Close the dialog."""
        if self._dialog is not None:
            self._dialog.grab_release()
            self._dialog.destroy()
            self._dialog = None

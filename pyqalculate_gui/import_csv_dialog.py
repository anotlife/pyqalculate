"""Import CSV dialog for PyQalculate GUI.

Provides a dialog for importing CSV files as matrix/vector variables
into the calculator. Supports configurable delimiters, first-row
header detection, and output format selection.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyqalculate.calculator import Calculator


class ImportCsvDialog:
    """Modal dialog for importing CSV files.

    Fields:
    - File path (with browse button)
    - Variable name (auto-populated from filename)
    - First row (spin button for header row)
    - Delimiter (comma / tab / semicolon / space / other)
    - Headers checkbox
    - Output format (matrix vs. per-column vectors)
    """

    def __init__(self, parent: tk.Tk | tk.Toplevel, calculator: Calculator) -> None:
        self._parent = parent
        self._calculator = calculator
        self._dialog: tk.Toplevel | None = None

    def show(self) -> None:
        """Open the import CSV dialog."""
        if self._dialog is not None and self._dialog.winfo_exists():
            self._dialog.lift()
            return

        self._dialog = tk.Toplevel(self._parent)
        self._dialog.title("Import CSV")
        self._dialog.geometry("480x380")
        self._dialog.resizable(False, False)
        self._dialog.transient(self._parent)
        self._dialog.grab_set()

        self._build_ui()
        self._dialog.protocol("WM_DELETE_WINDOW", self._close)

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        frame = ttk.Frame(self._dialog, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        # --- File path ---
        ttk.Label(frame, text="File:").grid(row=0, column=0, sticky="w", pady=4)
        file_frame = ttk.Frame(frame)
        file_frame.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)
        frame.columnconfigure(1, weight=1)

        self._file_var = tk.StringVar()
        self._file_entry = ttk.Entry(file_frame, textvariable=self._file_var, width=35)
        self._file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse...", command=self._browse_file).pack(
            side=tk.LEFT, padx=(4, 0)
        )

        # --- Variable name ---
        ttk.Label(frame, text="Name:").grid(row=1, column=0, sticky="w", pady=4)
        self._name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._name_var, width=30).grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=4
        )

        # --- First row ---
        ttk.Label(frame, text="First row:").grid(row=2, column=0, sticky="w", pady=4)
        self._first_row_var = tk.IntVar(value=1)
        ttk.Spinbox(frame, from_=1, to=10000, textvariable=self._first_row_var, width=8).grid(
            row=2, column=1, sticky="w", pady=4
        )

        # --- Headers checkbox ---
        self._headers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="First row contains headers", variable=self._headers_var).grid(
            row=3, column=0, columnspan=3, sticky="w", pady=4
        )

        # --- Delimiter ---
        ttk.Label(frame, text="Delimiter:").grid(row=4, column=0, sticky="w", pady=4)
        delim_frame = ttk.Frame(frame)
        delim_frame.grid(row=4, column=1, columnspan=2, sticky="ew", pady=4)

        self._delimiter_var = tk.StringVar(value=",")
        self._delimiter_choice = tk.StringVar(value="comma")

        delim_options = [
            ("Comma", "comma"),
            ("Tab", "tab"),
            ("Semicolon", "semicolon"),
            ("Space", "space"),
            ("Other", "other"),
        ]
        for i, (text, val) in enumerate(delim_options):
            ttk.Radiobutton(
                delim_frame, text=text, variable=self._delimiter_choice,
                value=val, command=self._on_delimiter_change
            ).pack(side=tk.LEFT, padx=2)

        self._other_delim_entry = ttk.Entry(
            delim_frame, textvariable=self._delimiter_var, width=4, state="disabled"
        )
        self._other_delim_entry.pack(side=tk.LEFT, padx=(8, 0))

        # --- Output format ---
        ttk.Label(frame, text="Format:").grid(row=5, column=0, sticky="w", pady=4)
        format_frame = ttk.Frame(frame)
        format_frame.grid(row=5, column=1, columnspan=2, sticky="ew", pady=4)

        self._format_var = tk.StringVar(value="vectors")
        ttk.Radiobutton(
            format_frame, text="Separate vectors per column",
            variable=self._format_var, value="vectors"
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            format_frame, text="Single matrix variable",
            variable=self._format_var, value="matrix"
        ).pack(anchor=tk.W)

        # --- Buttons ---
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=(16, 0))

        ttk.Button(btn_frame, text="Import", command=self._do_import).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_frame, text="Cancel", command=self._close).pack(
            side=tk.LEFT, padx=4
        )

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
        """Open file chooser dialog."""
        path = filedialog.askopenfilename(
            parent=self._dialog,
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self._file_var.set(path)
            # Auto-populate name from filename
            import os
            name = os.path.splitext(os.path.basename(path))[0]
            self._name_var.set(name)

    def _do_import(self) -> None:
        """Validate inputs and perform the CSV import."""
        filename = self._file_var.get().strip()
        if not filename:
            messagebox.showerror("Error", "Please select a CSV file.", parent=self._dialog)  # type: ignore[arg-type]
            return

        name = self._name_var.get().strip()
        first_row = self._first_row_var.get()
        headers = self._headers_var.get()
        delimiter = self._delimiter_var.get()
        to_matrix = self._format_var.get() == "matrix"

        if not delimiter:
            delimiter = ","

        try:
            result = self._calculator.importCSV(
                filename=filename,
                first_row=first_row,
                headers=headers,
                delimiter=delimiter,
                to_matrix=to_matrix,
                name=name,
            )

            if result.is_undefined():
                messagebox.showerror(
                    "Import Failed",
                    "Could not import the CSV file. Check the file path and format.",
                    parent=self._dialog,  # type: ignore[arg-type]
                )
                return

            # Show success message
            if to_matrix:
                msg = f"Imported as matrix variable '{name}'."
            else:
                msg = f"Imported columns as variables with prefix '{name}'."

            messagebox.showinfo("Import Successful", msg, parent=self._dialog)  # type: ignore[arg-type]
            self._close()

        except Exception as e:
            messagebox.showerror("Import Error", str(e), parent=self._dialog)  # type: ignore[arg-type]

    def _close(self) -> None:
        """Close the dialog."""
        if self._dialog is not None:
            self._dialog.grab_release()
            self._dialog.destroy()
            self._dialog = None

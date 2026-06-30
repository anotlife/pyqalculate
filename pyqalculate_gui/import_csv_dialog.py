"""Import CSV dialog for PyQalculate GUI.

Provides a dialog for importing CSV files as matrix/vector variables
into the calculator. Supports configurable delimiters, first-row
header detection, and output format selection.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from pyqalculate_gui.theme import Theme, LIGHT
from pyqalculate_gui.dialogs.base import ModalDialog
from pyqalculate_gui.calculator_service import CalculatorService
from pyqalculate_gui.i18n import _


class ImportCsvDialog(ModalDialog):
    """Modal dialog for importing CSV files.

    Fields:
    - File path (with browse button)
    - Variable name (auto-populated from filename)
    - First row (spin button for header row)
    - Delimiter (comma / tab / semicolon / space / other)
    - Headers checkbox
    - Output format (matrix vs. per-column vectors)
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme = LIGHT,
        calculator: CalculatorService | None = None,
    ) -> None:
        super().__init__(parent, _("Import CSV"), size=(480, 380), theme=theme)
        self._calc = calculator
        self._file_path = ""

    def _build_content(self, parent: ttk.Frame) -> None:
        """Build the import CSV UI."""
        # --- File path ---
        ttk.Label(parent, text=_("File:")).grid(row=0, column=0, sticky="w", pady=4)
        file_frame = ttk.Frame(parent)
        file_frame.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)
        parent.columnconfigure(1, weight=1)

        self._file_var = tk.StringVar()
        self._file_entry = ttk.Entry(file_frame, textvariable=self._file_var, width=35)
        self._file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_frame, text=_("Browse..."), command=self._browse_file).pack(
            side=tk.LEFT, padx=(4, 0)
        )

        # --- Variable name ---
        ttk.Label(parent, text=_("Name:")).grid(row=1, column=0, sticky="w", pady=4)
        self._name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self._name_var, width=30).grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=4
        )

        # --- First row ---
        ttk.Label(parent, text=_("First row:")).grid(row=2, column=0, sticky="w", pady=4)
        self._first_row_var = tk.IntVar(value=1)
        ttk.Spinbox(
            parent, from_=1, to=10000, textvariable=self._first_row_var, width=8
        ).grid(row=2, column=1, sticky="w", pady=4)

        # --- Headers checkbox ---
        self._headers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            parent, text=_("First row contains headers"), variable=self._headers_var
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=4)

        # --- Delimiter ---
        ttk.Label(parent, text=_("Delimiter:")).grid(row=4, column=0, sticky="w", pady=4)
        delim_frame = ttk.Frame(parent)
        delim_frame.grid(row=4, column=1, columnspan=2, sticky="ew", pady=4)

        self._delimiter_var = tk.StringVar(value=",")
        self._delimiter_choice = tk.StringVar(value="comma")

        delim_options = [
            (_("Comma"), "comma"),
            (_("Tab"), "tab"),
            (_("Semicolon"), "semicolon"),
            (_("Space"), "space"),
            (_("Other"), "other"),
        ]
        for text, val in delim_options:
            ttk.Radiobutton(
                delim_frame,
                text=text,
                variable=self._delimiter_choice,
                value=val,
                command=self._on_delimiter_change,
            ).pack(side=tk.LEFT, padx=2)

        self._other_delim_entry = ttk.Entry(
            delim_frame, textvariable=self._delimiter_var, width=4, state="disabled"
        )
        self._other_delim_entry.pack(side=tk.LEFT, padx=(8, 0))

        # --- Output format ---
        ttk.Label(parent, text=_("Format:")).grid(row=5, column=0, sticky="w", pady=4)
        format_frame = ttk.Frame(parent)
        format_frame.grid(row=5, column=1, columnspan=2, sticky="ew", pady=4)

        self._format_var = tk.StringVar(value="vectors")
        ttk.Radiobutton(
            format_frame,
            text=_("Separate vectors per column"),
            variable=self._format_var,
            value="vectors",
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            format_frame,
            text=_("Single matrix variable"),
            variable=self._format_var,
            value="matrix",
        ).pack(anchor=tk.W)

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
        assert self._dialog is not None
        path = filedialog.askopenfilename(
            parent=self._dialog,
            title=_("Select CSV File"),
            filetypes=[(_("CSV files"), "*.csv"), (_("All files"), "*.*")],
        )
        if path:
            self._file_var.set(path)
            self._file_path = path
            # Auto-populate name from filename
            name = Path(path).stem
            self._name_var.set(name)

    def _on_ok(self) -> None:
        """Validate inputs and perform the CSV import."""
        assert self._dialog is not None
        filename = self._file_var.get().strip()
        if not filename:
            messagebox.showerror(
                _("Error"), _("Please select a CSV file."), parent=self._dialog
            )
            return

        name = self._name_var.get().strip()
        first_row = self._first_row_var.get()
        headers = self._headers_var.get()
        delimiter = self._delimiter_var.get()
        to_matrix = self._format_var.get() == "matrix"

        if not delimiter:
            delimiter = ","

        if self._calc is None:
            super()._on_ok()
            return

        try:
            result = self._calc.import_csv(
                filename=filename,
                first_row=first_row,
                headers=headers,
                delimiter=delimiter,
                to_matrix=to_matrix,
                name=name,
            )

            if result.is_undefined():
                messagebox.showerror(
                    _("Import Failed"),
                    _("Could not import the CSV file. Check the file path and format."),
                    parent=self._dialog,
                )
                return

            # Show success message
            if to_matrix:
                msg = _("Imported as matrix variable '{}'.").format(name)
            else:
                msg = _("Imported columns as variables with prefix '{}'.").format(name)

            messagebox.showinfo(_("Import Successful"), msg, parent=self._dialog)
            super()._on_ok()

        except Exception as e:
            messagebox.showerror(_("Import Error"), str(e), parent=self._dialog)

    # Public API
    def get_file_path(self) -> str:
        """Get selected file path."""
        return self._file_path

    def get_name(self) -> str:
        """Get variable name."""
        return self._name_var.get().strip()

    def get_delimiter(self) -> str:
        """Get selected delimiter."""
        return self._delimiter_var.get()

    def get_first_row(self) -> int:
        """Get first row number."""
        return self._first_row_var.get()

    def get_headers(self) -> bool:
        """Get whether first row contains headers."""
        return self._headers_var.get()

    def get_to_matrix(self) -> bool:
        """Get whether output format is matrix."""
        return self._format_var.get() == "matrix"

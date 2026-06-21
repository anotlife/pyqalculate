"""Preferences dialog for PyQalculate GUI.

Provides a tabbed dialog for configuring calculator behavior, display
options, and appearance.  Settings are persisted to a JSON file in the
user's home directory and applied immediately to the Calculator engine.
"""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Any

from pyqalculate.types import (
    AngleUnit,
    ApproximationMode,
    EvaluationOptions,
    ExpDisplay,
    NumberFractionFormat,
    PrintOptions,
    UnicodeSigns,
)

if TYPE_CHECKING:
    from pyqalculate.calculator import Calculator

# ---------------------------------------------------------------------------
# Settings file location
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path.home() / ".pyqalculate"
_CONFIG_FILE = _CONFIG_DIR / "preferences.json"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_DEFAULTS: dict[str, Any] = {
    # Calculation
    "precision": 8,
    "approximation": "exact",           # exact | try_exact | approximate
    "angle_unit": "degrees",            # none | radians | degrees | gradians

    # Display
    "number_format": "decimal",         # decimal | scientific | engineering
    "digit_grouping": False,
    "unicode_signs": False,
    "exp_display": "default",           # default | uppercase_e | lowercase_e | power_of_10

    # Appearance
    "font_family": "Consolas",
    "font_size": 11,
    "theme": "light",                   # light | dark
}


class PreferencesDialog:
    """Modal preferences dialog for PyQalculate.

    Organised into tabs:
      - Calculation: precision, approximation mode, angle unit
      - Display: number format, digit grouping, exponent display
      - Appearance: font family/size, theme
    """

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        calculator: Calculator,
        on_apply: Any = None,
    ) -> None:
        self._parent = parent
        self._calc = calculator
        self._on_apply = on_apply          # callback after applying settings
        self._dialog: tk.Toplevel | None = None

        # Current settings (loaded from file or defaults)
        self._settings: dict[str, Any] = dict(_DEFAULTS)
        self._load_settings()

        # Tk variables (bound to widgets)
        self._vars: dict[str, tk.Variable] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Open (or raise) the preferences dialog."""
        if self._dialog is not None and self._dialog.winfo_exists():
            self._dialog.lift()
            return
        self._create_dialog()

    def get_settings(self) -> dict[str, Any]:
        """Return a copy of the current settings."""
        return dict(self._settings)

    def apply_settings(self) -> None:
        """Apply current settings to the Calculator engine (no dialog)."""
        self._apply_to_calculator()

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def _load_settings(self) -> None:
        """Load settings from the JSON config file."""
        if not _CONFIG_FILE.is_file():
            return
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Merge: only accept known keys
            for key in _DEFAULTS:
                if key in data:
                    self._settings[key] = data[key]
        except (json.JSONDecodeError, OSError):
            pass  # ignore corrupt files

    def _save_settings(self) -> None:
        """Persist current settings to the JSON config file."""
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(_CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(self._settings, fh, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Dialog construction
    # ------------------------------------------------------------------

    def _create_dialog(self) -> None:
        """Build the full preferences dialog."""
        dlg = tk.Toplevel(self._parent)
        dlg.title("Preferences")
        dlg.geometry("520x440")
        dlg.minsize(440, 380)
        dlg.transient(self._parent)
        dlg.grab_set()
        self._dialog = dlg

        dlg.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Notebook (tabs)
        notebook = ttk.Notebook(dlg, padding=4)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 0))

        self._build_calc_tab(notebook)
        self._build_display_tab(notebook)
        self._build_appearance_tab(notebook)

        # Bottom buttons
        self._build_buttons(dlg)

    # ---- Calculation tab ----

    def _build_calc_tab(self, notebook: ttk.Notebook) -> None:
        """Build the Calculation settings tab."""
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="  Calculation  ")

        row = 0

        # Precision
        ttk.Label(frame, text="Precision (significant digits):", font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        prec_var = tk.IntVar(value=self._settings["precision"])
        self._vars["precision"] = prec_var
        prec_spin = ttk.Spinbox(
            frame, from_=1, to=100, textvariable=prec_var, width=8,
        )
        prec_spin.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # Approximation mode
        ttk.Label(frame, text="Approximation mode:", font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        approx_var = tk.StringVar(value=self._settings["approximation"])
        self._vars["approximation"] = approx_var
        approx_frame = ttk.Frame(frame)
        approx_frame.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        for i, (label, val) in enumerate([
            ("Exact", "exact"),
            ("Try Exact", "try_exact"),
            ("Approximate", "approximate"),
        ]):
            ttk.Radiobutton(
                approx_frame, text=label, variable=approx_var, value=val,
            ).pack(side=tk.LEFT, padx=(0, 8))
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # Angle unit
        ttk.Label(frame, text="Angle unit:", font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        angle_var = tk.StringVar(value=self._settings["angle_unit"])
        self._vars["angle_unit"] = angle_var
        angle_combo = ttk.Combobox(
            frame,
            textvariable=angle_var,
            values=["none", "radians", "degrees", "gradians"],
            state="readonly",
            width=14,
        )
        angle_combo.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))

        frame.columnconfigure(1, weight=1)

    # ---- Display tab ----

    def _build_display_tab(self, notebook: ttk.Notebook) -> None:
        """Build the Display settings tab."""
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="  Display  ")

        row = 0

        # Number format
        ttk.Label(frame, text="Number format:", font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        fmt_var = tk.StringVar(value=self._settings["number_format"])
        self._vars["number_format"] = fmt_var
        fmt_frame = ttk.Frame(frame)
        fmt_frame.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        for label, val in [("Decimal", "decimal"), ("Scientific", "scientific"), ("Engineering", "engineering")]:
            ttk.Radiobutton(
                fmt_frame, text=label, variable=fmt_var, value=val,
            ).pack(side=tk.LEFT, padx=(0, 8))
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # Digit grouping
        grouping_var = tk.BooleanVar(value=self._settings["digit_grouping"])
        self._vars["digit_grouping"] = grouping_var
        ttk.Checkbutton(
            frame, text="Enable digit grouping (e.g. 1,000,000)",
            variable=grouping_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        row += 1

        # Unicode signs
        unicode_var = tk.BooleanVar(value=self._settings["unicode_signs"])
        self._vars["unicode_signs"] = unicode_var
        ttk.Checkbutton(
            frame, text="Use Unicode signs (\u00d7, \u00f7, \u221a, \u2248)",
            variable=unicode_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # Exponent display
        ttk.Label(frame, text="Exponent display:", font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        exp_var = tk.StringVar(value=self._settings["exp_display"])
        self._vars["exp_display"] = exp_var
        exp_combo = ttk.Combobox(
            frame,
            textvariable=exp_var,
            values=["default", "uppercase_e", "lowercase_e", "power_of_10"],
            state="readonly",
            width=16,
        )
        exp_combo.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))

        frame.columnconfigure(1, weight=1)

    # ---- Appearance tab ----

    def _build_appearance_tab(self, notebook: ttk.Notebook) -> None:
        """Build the Appearance settings tab."""
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="  Appearance  ")

        row = 0

        # Font family
        ttk.Label(frame, text="Font family:", font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        family_var = tk.StringVar(value=self._settings["font_family"])
        self._vars["font_family"] = family_var
        family_combo = ttk.Combobox(
            frame,
            textvariable=family_var,
            values=["Consolas", "Courier New", "Cascadia Code", "Fira Code", "Source Code Pro", "Monaco", "Menlo", "monospace"],
            width=18,
        )
        family_combo.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        row += 1

        # Font size
        ttk.Label(frame, text="Font size:", font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        size_var = tk.IntVar(value=self._settings["font_size"])
        self._vars["font_size"] = size_var
        size_spin = ttk.Spinbox(
            frame, from_=8, to=24, textvariable=size_var, width=8,
        )
        size_spin.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # Theme
        ttk.Label(frame, text="Theme:", font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4)
        )
        theme_var = tk.StringVar(value=self._settings["theme"])
        self._vars["theme"] = theme_var
        theme_frame = ttk.Frame(frame)
        theme_frame.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        ttk.Radiobutton(
            theme_frame, text="Light", variable=theme_var, value="light",
        ).pack(side=tk.LEFT, padx=(0, 16))
        ttk.Radiobutton(
            theme_frame, text="Dark", variable=theme_var, value="dark",
        ).pack(side=tk.LEFT)

        frame.columnconfigure(1, weight=1)

    # ---- Buttons ----

    def _build_buttons(self, parent: tk.Toplevel) -> None:
        """Build the bottom button row."""
        btn_frame = ttk.Frame(parent, padding=(8, 8, 8, 4))
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Reset Defaults", command=self._on_reset).pack(
            side=tk.LEFT
        )

        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(
            side=tk.RIGHT, padx=(4, 0)
        )
        ttk.Button(btn_frame, text="Apply", command=self._on_apply_click).pack(
            side=tk.RIGHT, padx=(4, 0)
        )
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(
            side=tk.RIGHT, padx=(4, 0)
        )

    # ------------------------------------------------------------------
    # Apply settings to Calculator
    # ------------------------------------------------------------------

    def _sync_from_widgets(self) -> None:
        """Read current widget values into the settings dict."""
        for key, var in self._vars.items():
            self._settings[key] = var.get()

    def _apply_to_calculator(self) -> None:
        """Push current settings into the Calculator engine."""
        s = self._settings

        # -- Precision --
        self._calc.set_precision(int(s["precision"]))

        # -- PrintOptions --
        po = PrintOptions()
        po.max_decimals = int(s["precision"])

        if s["number_format"] == "scientific":
            po.min_exp = 3      # EXP_SCIENTIFIC
        elif s["number_format"] == "engineering":
            po.min_exp = -3     # EXP_BASE_3
        else:
            po.min_exp = 0      # EXP_NONE / default

        if s["digit_grouping"]:
            from pyqalculate.types import DigitGrouping
            po.digit_grouping = DigitGrouping.STANDARD

        if s["unicode_signs"]:
            po.use_unicode_signs = UnicodeSigns.ON
        else:
            po.use_unicode_signs = UnicodeSigns.OFF

        # Exponent display
        exp_map = {
            "default": ExpDisplay.DEFAULT,
            "uppercase_e": ExpDisplay.UPPERCASE_E,
            "lowercase_e": ExpDisplay.LOWERCASE_E,
            "power_of_10": ExpDisplay.POWER_OF_10,
        }
        po.exp_display = exp_map.get(s["exp_display"], ExpDisplay.DEFAULT)

        # Store for MainWindow to use
        self._current_po = po

        # -- EvaluationOptions (angle unit) --
        eo = EvaluationOptions()
        angle_map = {
            "none": AngleUnit.NONE,
            "radians": AngleUnit.RADIANS,
            "degrees": AngleUnit.DEGREES,
            "gradians": AngleUnit.GRADIANS,
        }
        eo.parse_options.angle_unit = angle_map.get(s["angle_unit"], AngleUnit.NONE)

        # Approximation mode
        approx_map = {
            "exact": ApproximationMode.EXACT,
            "try_exact": ApproximationMode.TRY_EXACT,
            "approximate": ApproximationMode.APPROXIMATE,
        }
        eo.approximation = approx_map.get(s["approximation"], ApproximationMode.EXACT)

        self._current_eo = eo

    def _apply_theme(self) -> None:
        """Apply the selected theme to the application."""
        theme = self._settings.get("theme", "light")
        style = ttk.Style()

        if theme == "dark":
            bg = "#2b2b2b"
            fg = "#e0e0e0"
            entry_bg = "#3c3f41"
            select_bg = "#4a6fa5"
            style.theme_use("clam")
            style.configure(".", background=bg, foreground=fg, fieldbackground=entry_bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TFrame", background=bg)
            style.configure("TCheckbutton", background=bg, foreground=fg)
            style.configure("TRadiobutton", background=bg, foreground=fg)
            style.configure("TButton", background="#45494a", foreground=fg)
            style.configure("TEntry", fieldbackground=entry_bg, foreground=fg)
            style.configure("TSpinbox", fieldbackground=entry_bg, foreground=fg)
            style.configure("TCombobox", fieldbackground=entry_bg, foreground=fg)
            style.configure("TNotebook", background=bg)
            style.configure("TNotebook.Tab", background="#3c3f41", foreground=fg)
            style.map("TNotebook.Tab", background=[("selected", "#4a6fa5")])
        else:
            style.theme_use("default")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_ok(self) -> None:
        """OK: save, apply, close."""
        self._sync_from_widgets()
        self._save_settings()
        self._apply_to_calculator()
        self._apply_theme()
        if self._on_apply:
            self._on_apply()
        self._close()

    def _on_apply_click(self) -> None:
        """Apply: save and apply without closing."""
        self._sync_from_widgets()
        self._save_settings()
        self._apply_to_calculator()
        self._apply_theme()
        if self._on_apply:
            self._on_apply()

    def _on_cancel(self) -> None:
        """Cancel: discard changes, close."""
        self._close()

    def _on_reset(self) -> None:
        """Reset all settings to defaults."""
        self._settings = dict(_DEFAULTS)
        # Update all widgets
        for key, var in self._vars.items():
            if key in _DEFAULTS:
                var.set(_DEFAULTS[key])

    def _close(self) -> None:
        """Destroy the dialog."""
        if self._dialog is not None:
            self._dialog.destroy()
            self._dialog = None

"""Preferences dialog for PyQalculate GUI.

Provides a tabbed dialog for configuring calculator behavior, display
options, and appearance.  Settings are persisted to a JSON file in the
user's home directory and broadcast via the EventBus.
"""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from pyqalculate_gui.dialogs.base import ModalDialog
from pyqalculate_gui.event_bus import EventBus, PREFERENCE_APPLIED
from pyqalculate_gui.i18n import _
from pyqalculate_gui.theme import LIGHT, Theme

_LANG_DISPLAY_TO_CODE = {"English": "en", "中文（简体）": "zh_CN"}
_LANG_CODE_TO_DISPLAY = {"en": "English", "zh_CN": "中文（简体）"}

# ---------------------------------------------------------------------------
# Settings file location
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path.home() / ".pyqalculate"
_CONFIG_FILE = _CONFIG_DIR / "preferences.json"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_SETTINGS: dict[str, Any] = {
    # Calculation
    "approximation": "exact",  # exact | try_exact | approximate
    "angle_unit": "degrees",  # none | radians | degrees | gradians
    "precision": 8,

    # Display
    "number_format": "decimal",  # decimal | scientific | engineering
    "digit_grouping": False,
    "unicode_signs": False,
    "exp_display": "default",  # default | uppercase_e | lowercase_e | power_of_10

    # Appearance
    "font_family": "Consolas",
    "font_size": 11,
    "theme": "light",  # light | dark
    "language": "en",  # en | zh_CN
}


class PreferencesDialog(ModalDialog):
    """Modal preferences dialog for PyQalculate.

    Organised into tabs:
      - Calculation: precision, approximation mode, angle unit
      - Display: number format, digit grouping, exponent display
      - Appearance: font family/size, theme
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme = LIGHT,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(parent, _("Preferences"), size=(520, 500), theme=theme)
        self._event_bus = event_bus
        self._settings = self._load_settings()
        self._vars: dict[str, tk.Variable] = {}

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def _load_settings(self) -> dict[str, Any]:
        """Load settings from the JSON config file."""
        if not _CONFIG_FILE.is_file():
            return dict(DEFAULT_SETTINGS)
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            merged = dict(DEFAULT_SETTINGS)
            for key in DEFAULT_SETTINGS:
                if key in data:
                    merged[key] = data[key]
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(DEFAULT_SETTINGS)

    def _save_settings(self) -> None:
        """Persist current settings to the JSON config file."""
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(_CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(self._settings, fh, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_settings(self) -> dict[str, Any]:
        """Return a copy of the current settings."""
        return dict(self._settings)

    def apply_settings(self) -> None:
        """Apply current settings via the EventBus (no dialog)."""
        if self._event_bus is not None:
            self._event_bus.emit(PREFERENCE_APPLIED, self._settings)

    # ------------------------------------------------------------------
    # Content building (ModalDialog contract)
    # ------------------------------------------------------------------

    def _build_content(self, parent: ttk.Frame) -> None:
        """Build the tabbed preferences UI."""
        notebook = ttk.Notebook(parent, padding=4)
        notebook.pack(fill=tk.BOTH, expand=True)

        self._build_calc_tab(notebook)
        self._build_display_tab(notebook)
        self._build_appearance_tab(notebook)

    # ---- Calculation tab ----

    def _build_calc_tab(self, notebook: ttk.Notebook) -> None:
        """Build the Calculation settings tab."""
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="  " + _("Calculation") + "  ")

        row = 0

        # Precision
        ttk.Label(frame, text=_("Precision (significant digits):"), font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4),
        )
        prec_var = tk.IntVar(value=self._settings["precision"])
        self._vars["precision"] = prec_var
        ttk.Spinbox(
            frame, from_=1, to=100, textvariable=prec_var, width=8,
        ).grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8,
        )
        row += 1

        # Approximation mode
        ttk.Label(frame, text=_("Approximation mode:"), font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4),
        )
        approx_var = tk.StringVar(value=self._settings["approximation"])
        self._vars["approximation"] = approx_var
        approx_frame = ttk.Frame(frame)
        approx_frame.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        for label, val in [
            (_("Exact"), "exact"),
            (_("Try Exact"), "try_exact"),
            (_("Approximate"), "approximate"),
        ]:
            ttk.Radiobutton(
                approx_frame, text=label, variable=approx_var, value=val,
            ).pack(side=tk.LEFT, padx=(0, 8))
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8,
        )
        row += 1

        # Angle unit
        ttk.Label(frame, text=_("Angle unit:"), font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4),
        )
        # Map internal keys to translated display values
        _ANGLE_DISPLAY = {
            "none": _("none"),
            "radians": _("radians"),
            "degrees": _("degrees"),
            "gradians": _("gradians"),
        }
        _ANGLE_REVERSE = {v: k for k, v in _ANGLE_DISPLAY.items()}
        angle_var = tk.StringVar(value=_ANGLE_DISPLAY.get(self._settings["angle_unit"], _("degrees")))
        self._vars["angle_unit"] = angle_var
        self._angle_display = _ANGLE_DISPLAY  # store for sync
        self._angle_reverse = _ANGLE_REVERSE
        ttk.Combobox(
            frame,
            textvariable=angle_var,
            values=list(_ANGLE_DISPLAY.values()),
            state="readonly",
            width=14,
        ).grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))

        frame.columnconfigure(1, weight=1)

    # ---- Display tab ----

    def _build_display_tab(self, notebook: ttk.Notebook) -> None:
        """Build the Display settings tab."""
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="  " + _("Display") + "  ")

        row = 0

        # Number format
        ttk.Label(frame, text=_("Number format:"), font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4),
        )
        fmt_var = tk.StringVar(value=self._settings["number_format"])
        self._vars["number_format"] = fmt_var
        fmt_frame = ttk.Frame(frame)
        fmt_frame.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        for label, val in [
            (_("Decimal"), "decimal"),
            (_("Scientific"), "scientific"),
            (_("Engineering"), "engineering"),
        ]:
            ttk.Radiobutton(
                fmt_frame, text=label, variable=fmt_var, value=val,
            ).pack(side=tk.LEFT, padx=(0, 8))
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8,
        )
        row += 1

        # Digit grouping
        grouping_var = tk.BooleanVar(value=self._settings["digit_grouping"])
        self._vars["digit_grouping"] = grouping_var
        ttk.Checkbutton(
            frame,
            text=_("Enable digit grouping (e.g. 1,000,000)"),
            variable=grouping_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        row += 1

        # Unicode signs
        unicode_var = tk.BooleanVar(value=self._settings["unicode_signs"])
        self._vars["unicode_signs"] = unicode_var
        ttk.Checkbutton(
            frame,
            text=_("Use Unicode signs (\u00d7, \u00f7, \u221a, \u2248)"),
            variable=unicode_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8,
        )
        row += 1

        # Exponent display
        ttk.Label(frame, text=_("Exponent display:"), font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4),
        )
        exp_var = tk.StringVar(value=self._settings["exp_display"])
        self._vars["exp_display"] = exp_var
        ttk.Combobox(
            frame,
            textvariable=exp_var,
            values=["default", "uppercase_e", "lowercase_e", "power_of_10"],
            state="readonly",
            width=16,
        ).grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))

        frame.columnconfigure(1, weight=1)

    # ---- Appearance tab ----

    def _build_appearance_tab(self, notebook: ttk.Notebook) -> None:
        """Build the Appearance settings tab."""
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="  " + _("Appearance") + "  ")

        row = 0

        # Font family
        ttk.Label(frame, text=_("Font family:"), font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4),
        )
        family_var = tk.StringVar(value=self._settings["font_family"])
        self._vars["font_family"] = family_var
        ttk.Combobox(
            frame,
            textvariable=family_var,
            values=[
                "Consolas", "Courier New", "Cascadia Code",
                "Fira Code", "Source Code Pro", "Monaco",
                "Menlo", "Noto Sans CJK SC", "Microsoft YaHei",
                "monospace",
            ],
            width=18,
        ).grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        row += 1

        # Font size
        ttk.Label(frame, text=_("Font size:"), font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4),
        )
        size_var = tk.IntVar(value=self._settings["font_size"])
        self._vars["font_size"] = size_var
        ttk.Spinbox(
            frame, from_=8, to=24, textvariable=size_var, width=8,
        ).grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8,
        )
        row += 1

        # Theme
        ttk.Label(frame, text=_("Theme:"), font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4),
        )
        theme_var = tk.StringVar(value=self._settings["theme"])
        self._vars["theme"] = theme_var
        theme_frame = ttk.Frame(frame)
        theme_frame.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))
        ttk.Radiobutton(
            theme_frame, text=_("Light"), variable=theme_var, value="light",
        ).pack(side=tk.LEFT, padx=(0, 16))
        ttk.Radiobutton(
            theme_frame, text=_("Dark"), variable=theme_var, value="dark",
        ).pack(side=tk.LEFT)
        row += 1

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8,
        )
        row += 1

        # Language
        ttk.Label(frame, text=_("Language:"), font=("", 10)).grid(
            row=row, column=0, sticky="w", pady=(0, 4),
        )
        lang_display = _LANG_CODE_TO_DISPLAY.get(
            self._settings.get("language", "en"), "English"
        )
        lang_var = tk.StringVar(value=lang_display)
        self._vars["language"] = lang_var
        ttk.Combobox(
            frame,
            textvariable=lang_var,
            values=["English", "中文（简体）"],
            state="readonly",
            width=18,
        ).grid(row=row, column=1, sticky="w", padx=(12, 0), pady=(0, 4))

        frame.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def _on_ok(self) -> None:
        """Sync widgets, save, emit event, then close."""
        self._sync_from_widgets()
        self._save_settings()
        if self._event_bus is not None:
            self._event_bus.emit(PREFERENCE_APPLIED, self._settings)
        super()._on_ok()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sync_from_widgets(self) -> None:
        """Read current widget values into the settings dict."""
        for key, var in self._vars.items():
            value = var.get()
            if key == "angle_unit":
                value = self._angle_reverse.get(value, value)
            self._settings[key] = value
        lang_display = self._settings.get("language", "English")
        self._settings["language"] = _LANG_DISPLAY_TO_CODE.get(lang_display, "en")

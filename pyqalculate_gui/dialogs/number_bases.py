"""Number Bases conversion dialog.

Shows the current result in multiple bases simultaneously:
decimal, binary, octal, hexadecimal, duodecimal, and roman numerals.
Allows editing in any base to convert to others.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from pyqalculate_gui.dialogs.base import ModalDialog
from pyqalculate_gui.theme import LIGHT, Theme
from pyqalculate_gui.i18n import _

if TYPE_CHECKING:
    from pyqalculate_gui.calculator_service import CalculatorService

# (display_label, entry_key, calculator_prefix)
_BASES: list[tuple[str, str, str]] = [
    (_("Decimal"), "10", ""),
    (_("Binary"), "2", "0b"),
    (_("Octal"), "8", "0o"),
    (_("Hexadecimal"), "16", "0x"),
    (_("Duodecimal"), "12", ""),
    (_("Roman"), "roman", ""),
]


class NumberBasesDialog(ModalDialog):
    """Dialog for converting numbers between different bases."""

    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme = LIGHT,
        calculator: CalculatorService | None = None,
        initial_value: str = "",
    ) -> None:
        super().__init__(
            parent,
            title=_("Number Bases"),
            size=(500, 400),
            resizable=(True, True),
            theme=theme,
        )
        self._calculator = calculator
        self._initial_value = initial_value
        self._entries: dict[str, ttk.Entry] = {}
        self._updating = False

    # ------------------------------------------------------------------
    # Content building (ModalDialog contract)
    # ------------------------------------------------------------------

    def _build_content(self, parent: ttk.Frame) -> None:
        """Build the number bases dialog content."""
        ttk.Label(
            parent,
            text=_("Enter a value in any field to convert to other bases."),
            font=self._theme.info_font,
        ).pack(anchor=tk.W, pady=(0, 10))

        for label, key, _prefix in _BASES:
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, pady=2)

            ttk.Label(frame, text=_("{}:").format(label), width=14).pack(side=tk.LEFT)

            entry = ttk.Entry(frame, font=self._theme.expression_font)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
            entry.bind(
                "<KeyRelease>",
                lambda _e, k=key: self._on_entry_change(k),
            )
            self._entries[key] = entry

        if self._initial_value and self._calculator:
            self._convert_from_value(self._initial_value, "10")

    # ------------------------------------------------------------------
    # Conversion logic
    # ------------------------------------------------------------------

    def _on_entry_change(self, base_key: str) -> None:
        """Handle entry value change — convert to other bases."""
        if self._updating:
            return
        value = self._entries[base_key].get().strip()
        if not value:
            return
        self._convert_from_value(value, base_key)

    def _convert_from_value(self, value: str, from_key: str) -> None:
        """Convert a value from one base to all other bases."""
        if not self._calculator:
            return

        self._updating = True
        try:
            decimal_val = self._parse_to_decimal(value, from_key)
            if decimal_val is None:
                return

            self._set_entry("10", str(decimal_val))
            self._set_entry("2", self._to_base(decimal_val, 2))
            self._set_entry("8", self._to_base(decimal_val, 8))
            self._set_entry("16", self._to_base(decimal_val, 16).upper())
            self._set_entry("12", self._to_duodecimal(decimal_val))
            self._set_entry("roman", self._to_roman(decimal_val))
        finally:
            self._updating = False

    def _parse_to_decimal(self, value: str, from_key: str) -> int | None:
        """Parse a value from the given base to a decimal integer."""
        if from_key == "roman":
            return self._from_roman(value)
        if from_key == "12":
            return self._from_duodecimal(value)

        if not self._calculator:
            return None

        prefix_map = {"2": "0b", "8": "0o", "16": "0x"}
        expr = f"{prefix_map.get(from_key, '')}{value}"
        result = self._calculator.calculate(expr)
        if result.error:
            return None
        try:
            return int(float(result.result))
        except (ValueError, OverflowError):
            return None

    def _set_entry(self, key: str, value: str) -> None:
        """Set an entry's value, clearing first."""
        entry = self._entries.get(key)
        if entry is None:
            return
        entry.delete(0, tk.END)
        entry.insert(0, value)

    # ------------------------------------------------------------------
    # Pure conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_base(n: int, base: int) -> str:
        """Convert integer to string in given base (2-16)."""
        if n == 0:
            return "0"
        negative = n < 0
        n = abs(n)
        digits = "0123456789abcdef"
        result: list[str] = []
        while n > 0:
            result.append(digits[n % base])
            n //= base
        if negative:
            result.append("-")
        return "".join(reversed(result))

    @staticmethod
    def _to_duodecimal(n: int) -> str:
        """Convert integer to duodecimal (base 12) representation.

        Uses ↊ for 10 and ↋ for 11 (Dozenal Society glyphs).
        """
        if n == 0:
            return "0"
        digits = "0123456789↊↋"
        result: list[str] = []
        while n > 0:
            result.append(digits[n % 12])
            n //= 12
        return "".join(reversed(result))

    @staticmethod
    def _from_duodecimal(s: str) -> int | None:
        """Parse duodecimal string to integer.  Returns None on invalid input."""
        digit_map = {c: i for i, c in enumerate("0123456789↊↋")}
        result = 0
        for ch in s:
            if ch not in digit_map:
                return None
            result = result * 12 + digit_map[ch]
        return result

    @staticmethod
    def _to_roman(n: int) -> str:
        """Convert integer to Roman numerals (1-3999)."""
        if not (0 < n < 4000):
            return ""
        values = [
            (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
            (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
            (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
        ]
        result: list[str] = []
        for val, numeral in values:
            while n >= val:
                result.append(numeral)
                n -= val
        return "".join(result)

    @staticmethod
    def _from_roman(s: str) -> int | None:
        """Parse Roman numeral string to integer.  Returns None on invalid input."""
        roman_values = {
            "I": 1, "V": 5, "X": 10, "L": 50,
            "C": 100, "D": 500, "M": 1000,
        }
        s = s.upper().strip()
        if not s or any(c not in roman_values for c in s):
            return None
        result = 0
        prev = 0
        for c in reversed(s):
            val = roman_values[c]
            if val < prev:
                result -= val
            else:
                result += val
            prev = val
        return result if result > 0 else None

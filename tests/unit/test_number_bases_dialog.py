"""Tests for pyqalculate_gui.dialogs.number_bases."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from pyqalculate_gui.dialogs.number_bases import NumberBasesDialog
from pyqalculate_gui.theme import DARK, LIGHT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HAS_DISPLAY = bool(
    os.environ.get("DISPLAY")
    or os.environ.get("WAYLAND_DISPLAY")
    or os.name == "nt"
)


def _make_root() -> tk.Tk:
    """Create a withdrawn Tk root for testing."""
    root = tk.Tk()
    root.withdraw()
    return root


# ---------------------------------------------------------------------------
# Pure function tests — no display required
# ---------------------------------------------------------------------------


class TestBaseConversion:
    """Given: integer values\nWhen:  converting to arbitrary base\nThen:  correct representation."""

    def test_zero(self) -> None:
        assert NumberBasesDialog._to_base(0, 2) == "0"

    def test_binary_255(self) -> None:
        assert NumberBasesDialog._to_base(255, 2) == "11111111"

    def test_octal_255(self) -> None:
        assert NumberBasesDialog._to_base(255, 8) == "377"

    def test_hex_255(self) -> None:
        assert NumberBasesDialog._to_base(255, 16) == "ff"

    def test_negative_binary(self) -> None:
        assert NumberBasesDialog._to_base(-1, 2) == "-1"

    def test_negative_hex(self) -> None:
        assert NumberBasesDialog._to_base(-255, 16) == "-ff"


class TestDuodecimalConversion:
    """Given: integer values\nWhen:  converting to duodecimal\nThen:  correct representation."""

    def test_zero(self) -> None:
        assert NumberBasesDialog._to_duodecimal(0) == "0"

    def test_ten(self) -> None:
        assert NumberBasesDialog._to_duodecimal(10) == "\u218a"

    def test_eleven(self) -> None:
        assert NumberBasesDialog._to_duodecimal(11) == "\u218b"

    def test_twelve(self) -> None:
        assert NumberBasesDialog._to_duodecimal(12) == "10"

    def test_two_hundred_fifty_five(self) -> None:
        assert NumberBasesDialog._to_duodecimal(255) == "193"


class TestDuodecimalParsing:
    """Given: duodecimal strings\nWhen:  parsing to integer\nThen:  correct value."""

    def test_parse_zero(self) -> None:
        assert NumberBasesDialog._from_duodecimal("0") == 0

    def test_parse_ten(self) -> None:
        assert NumberBasesDialog._from_duodecimal("\u218a") == 10

    def test_parse_twelve(self) -> None:
        assert NumberBasesDialog._from_duodecimal("10") == 12

    def test_parse_invalid_returns_none(self) -> None:
        assert NumberBasesDialog._from_duodecimal("Z") is None


class TestRomanConversion:
    """Given: integer values\nWhen:  converting to Roman numerals\nThen:  correct representation."""

    def test_one(self) -> None:
        assert NumberBasesDialog._to_roman(1) == "I"

    def test_four(self) -> None:
        assert NumberBasesDialog._to_roman(4) == "IV"

    def test_nine(self) -> None:
        assert NumberBasesDialog._to_roman(9) == "IX"

    def test_twenty_four(self) -> None:
        assert NumberBasesDialog._to_roman(24) == "XXIV"

    def test_ninety_nine(self) -> None:
        assert NumberBasesDialog._to_roman(99) == "XCIX"

    def test_two_thousand_twenty_four(self) -> None:
        assert NumberBasesDialog._to_roman(2024) == "MMXXIV"

    def test_out_of_range_returns_empty(self) -> None:
        assert NumberBasesDialog._to_roman(0) == ""
        assert NumberBasesDialog._to_roman(4000) == ""
        assert NumberBasesDialog._to_roman(-1) == ""


class TestRomanParsing:
    """Given: Roman numeral strings\nWhen:  parsing to integer\nThen:  correct value."""

    def test_parse_i(self) -> None:
        assert NumberBasesDialog._from_roman("I") == 1

    def test_parse_iv(self) -> None:
        assert NumberBasesDialog._from_roman("IV") == 4

    def test_parse_mmxxiv(self) -> None:
        assert NumberBasesDialog._from_roman("MMXXIV") == 2024

    def test_parse_lowercase(self) -> None:
        assert NumberBasesDialog._from_roman("mmxxiv") == 2024

    def test_parse_invalid_returns_none(self) -> None:
        assert NumberBasesDialog._from_roman("ABC") is None
        assert NumberBasesDialog._from_roman("") is None


# ---------------------------------------------------------------------------
# Instantiation tests — no display required
# ---------------------------------------------------------------------------


class TestDialogInstantiation:
    """Given: the NumberBasesDialog class\nWhen:  constructing instances\nThen:  internal state is correct."""

    def test_extends_modal_dialog(self) -> None:
        from pyqalculate_gui.dialogs.base import ModalDialog
        assert issubclass(NumberBasesDialog, ModalDialog)

    def test_default_theme_is_light(self) -> None:
        root = _make_root()
        try:
            dlg = NumberBasesDialog(root)
            assert dlg._theme is LIGHT
        finally:
            root.destroy()

    def test_custom_theme(self) -> None:
        root = _make_root()
        try:
            dlg = NumberBasesDialog(root, theme=DARK)
            assert dlg._theme is DARK
        finally:
            root.destroy()

    def test_default_size(self) -> None:
        root = _make_root()
        try:
            dlg = NumberBasesDialog(root)
            assert dlg._size == (500, 400)
        finally:
            root.destroy()

    def test_resizable(self) -> None:
        root = _make_root()
        try:
            dlg = NumberBasesDialog(root)
            assert dlg._resizable == (True, True)
        finally:
            root.destroy()

    def test_entries_start_empty(self) -> None:
        root = _make_root()
        try:
            dlg = NumberBasesDialog(root)
            assert dlg._entries == {}
        finally:
            root.destroy()

    def test_updating_flag_starts_false(self) -> None:
        root = _make_root()
        try:
            dlg = NumberBasesDialog(root)
            assert dlg._updating is False
        finally:
            root.destroy()


# ---------------------------------------------------------------------------
# Integration — requires display
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="ModalDialog.wait_window causes Tk event loop hang on teardown")
class TestDialogIntegration:
    """Given: a display is available\nWhen:  showing the dialog\nThen:  UI creates correctly."""

    def test_show_and_cancel(self) -> None:
        root = _make_root()
        try:
            dlg = NumberBasesDialog(root)
            root.after(50, dlg._on_cancel)
            dlg.show()
            assert dlg.get_result() is False
            assert dlg._dialog is None
        finally:
            root.destroy()

    def test_show_and_ok(self) -> None:
        root = _make_root()
        try:
            dlg = NumberBasesDialog(root)
            root.after(50, dlg._on_ok)
            dlg.show()
            assert dlg.get_result() is True
        finally:
            root.destroy()

    def test_entries_created(self) -> None:
        root = _make_root()
        try:
            dlg = NumberBasesDialog(root)

            def check_and_cancel() -> None:
                assert len(dlg._entries) == 6
                assert "10" in dlg._entries
                assert "2" in dlg._entries
                assert "8" in dlg._entries
                assert "16" in dlg._entries
                assert "12" in dlg._entries
                assert "roman" in dlg._entries
                dlg._on_cancel()

            root.after(50, check_and_cancel)
            dlg.show()
        finally:
            root.destroy()

"""Tests for pyqalculate_gui.export_csv_dialog."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock, patch

import pytest

from pyqalculate_gui.dialogs.base import ModalDialog
from pyqalculate_gui.export_csv_dialog import ExportCsvDialog
from pyqalculate_gui.theme import LIGHT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HAS_DISPLAY = bool(
    os.environ.get("DISPLAY")
    or os.environ.get("WAYLAND_DISPLAY")
    or os.name == "nt"
)


def _make_dialog(
    parent: tk.Widget,
    calculator: object | None = None,
    get_last_result: object | None = None,
) -> ExportCsvDialog:
    """Construct an ExportCsvDialog with mocked dependencies."""
    return ExportCsvDialog(
        parent,
        calculator=calculator,
        get_last_result=get_last_result,
    )


def _make_mock_calculator() -> MagicMock:
    """Create a mock CalculatorService with a _calc attribute."""
    calc_service = MagicMock()
    calc_service._calc = MagicMock()
    calc_service._calc.get_variable = MagicMock(return_value=None)
    calc_service._calc.exportCSV = MagicMock(return_value=True)
    return calc_service


# ---------------------------------------------------------------------------
# Unit tests (no display required)
# ---------------------------------------------------------------------------


class TestInheritance:
    """ExportCsvDialog should extend ModalDialog."""

    def test_extends_modal_dialog(self) -> None:
        """Given: ExportCsvDialog\nWhen:  checked\nThen:  is a subclass of ModalDialog."""
        assert issubclass(ExportCsvDialog, ModalDialog)


class TestConstructor:
    """__init__ stores parameters correctly."""

    def test_default_theme_is_light(self) -> None:
        """Given: no theme argument\nWhen:  construct dialog\nThen:  theme is LIGHT."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root)
            assert dlg._theme is LIGHT
        finally:
            root.destroy()

    def test_calculator_stored(self) -> None:
        """Given: a calculator mock\nWhen:  construct dialog\nThen:  _calc stores it."""
        root = tk.Tk()
        root.withdraw()
        try:
            calc = _make_mock_calculator()
            dlg = _make_dialog(root, calculator=calc)
            assert dlg._calc is calc
        finally:
            root.destroy()

    def test_get_last_result_stored(self) -> None:
        """Given: a get_last_result callable\nWhen:  construct dialog\nThen:  _get_last_result stores it."""
        root = tk.Tk()
        root.withdraw()
        try:
            fn = lambda: None
            dlg = _make_dialog(root, get_last_result=fn)
            assert dlg._get_last_result is fn
        finally:
            root.destroy()

    def test_custom_size(self) -> None:
        """Given: default construction\nWhen:  inspect _size\nThen:  (480, 340)."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root)
            assert dlg._size == (480, 340)
        finally:
            root.destroy()


class TestSourceChange:
    """_on_source_change toggles variable entry state."""

    def test_variable_source_enables_entry(self) -> None:
        """Given: source set to 'variable'\nWhen:  _on_source_change\nThen:  entry is normal."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root)
            # Build content manually to create widgets
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._source_var.set("variable")
            dlg._on_source_change()
            assert str(dlg._var_name_entry.cget("state")) == "normal"
        finally:
            root.destroy()

    def test_result_source_disables_entry(self) -> None:
        """Given: source set to 'result'\nWhen:  _on_source_change\nThen:  entry is disabled."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._source_var.set("result")
            dlg._on_source_change()
            assert str(dlg._var_name_entry.cget("state")) == "disabled"
        finally:
            root.destroy()


class TestDelimiterChange:
    """_on_delimiter_change updates delimiter value."""

    def test_comma_sets_comma(self) -> None:
        """Given: delimiter choice 'comma'\nWhen:  _on_delimiter_change\nThen:  delimiter_var is ','."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._delimiter_choice.set("comma")
            dlg._on_delimiter_change()
            assert dlg._delimiter_var.get() == ","
        finally:
            root.destroy()

    def test_tab_sets_tab(self) -> None:
        """Given: delimiter choice 'tab'\nWhen:  _on_delimiter_change\nThen:  delimiter_var is '\\t'."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._delimiter_choice.set("tab")
            dlg._on_delimiter_change()
            assert dlg._delimiter_var.get() == "\t"
        finally:
            root.destroy()

    def test_other_enables_entry(self) -> None:
        """Given: delimiter choice 'other'\nWhen:  _on_delimiter_change\nThen:  entry is normal."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._delimiter_choice.set("other")
            dlg._on_delimiter_change()
            assert str(dlg._other_delim_entry.cget("state")) == "normal"
        finally:
            root.destroy()

    def test_semicolon_sets_semicolon(self) -> None:
        """Given: delimiter choice 'semicolon'\nWhen:  _on_delimiter_change\nThen:  delimiter_var is ';'."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._delimiter_choice.set("semicolon")
            dlg._on_delimiter_change()
            assert dlg._delimiter_var.get() == ";"
        finally:
            root.destroy()


class TestOnOk:
    """_on_ok validates inputs and performs export."""

    def test_shows_error_when_no_file(self) -> None:
        """Given: empty file path\nWhen:  _on_ok\nThen:  shows error, result stays None."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._dialog = root  # fake dialog for messagebox parent
            with patch("pyqalculate_gui.export_csv_dialog.messagebox"):
                dlg._on_ok()
            assert dlg.get_result() is None
        finally:
            root.destroy()

    def test_shows_error_when_no_variable_name(self) -> None:
        """Given: file path set but no variable name\nWhen:  _on_ok with variable source\nThen:  shows error."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._dialog = root
            dlg._file_var.set("/tmp/test.csv")
            dlg._source_var.set("variable")
            with patch("pyqalculate_gui.export_csv_dialog.messagebox"):
                dlg._on_ok()
            assert dlg.get_result() is None
        finally:
            root.destroy()

    def test_shows_error_when_no_calculator(self) -> None:
        """Given: variable name set but no calculator\nWhen:  _on_ok\nThen:  shows error."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root, calculator=None)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._dialog = root
            dlg._file_var.set("/tmp/test.csv")
            dlg._source_var.set("variable")
            dlg._var_name_var.set("myvar")
            with patch("pyqalculate_gui.export_csv_dialog.messagebox"):
                dlg._on_ok()
            assert dlg.get_result() is None
        finally:
            root.destroy()

    def test_shows_error_when_variable_not_found(self) -> None:
        """Given: variable name not in calculator\nWhen:  _on_ok\nThen:  shows error."""
        root = tk.Tk()
        root.withdraw()
        try:
            calc = _make_mock_calculator()
            calc._calc.get_variable.return_value = None
            dlg = _make_dialog(root, calculator=calc)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._dialog = root
            dlg._file_var.set("/tmp/test.csv")
            dlg._source_var.set("variable")
            dlg._var_name_var.set("nonexistent")
            with patch("pyqalculate_gui.export_csv_dialog.messagebox"):
                dlg._on_ok()
            assert dlg.get_result() is None
        finally:
            root.destroy()

    def test_shows_error_when_no_data(self) -> None:
        """Given: result source but no get_last_result\nWhen:  _on_ok\nThen:  shows error."""
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = _make_dialog(root, calculator=_make_mock_calculator(), get_last_result=None)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._dialog = root
            dlg._file_var.set("/tmp/test.csv")
            dlg._source_var.set("result")
            with patch("pyqalculate_gui.export_csv_dialog.messagebox"):
                dlg._on_ok()
            assert dlg.get_result() is None
        finally:
            root.destroy()

    def test_export_success_via_result(self) -> None:
        """Given: valid inputs via result source and successful export\nWhen:  _on_ok\nThen:  result is True."""
        root = tk.Tk()
        root.withdraw()
        try:
            calc = _make_mock_calculator()
            calc._calc.exportCSV.return_value = True
            mock_result = MagicMock()
            dlg = _make_dialog(
                root, calculator=calc,
                get_last_result=lambda: mock_result,
            )
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            # Use a mock Toplevel so _close() doesn't destroy root
            mock_toplevel = MagicMock(spec=tk.Toplevel)
            dlg._dialog = mock_toplevel
            dlg._file_var.set("/tmp/test.csv")
            dlg._source_var.set("result")

            with patch("pyqalculate_gui.export_csv_dialog.messagebox"):
                dlg._on_ok()
            assert dlg.get_result() is True
        finally:
            root.destroy()

    def test_export_failure(self) -> None:
        """Given: exportCSV returns False\nWhen:  _on_ok\nThen:  shows error, result stays None."""
        root = tk.Tk()
        root.withdraw()
        try:
            calc = _make_mock_calculator()
            calc._calc.exportCSV.return_value = False
            dlg = _make_dialog(root, calculator=calc)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._dialog = root
            dlg._file_var.set("/tmp/test.csv")
            dlg._source_var.set("variable")
            dlg._var_name_var.set("myvar")

            mock_var = MagicMock()
            mock_var.get.return_value = "mock_mstruct"
            calc._calc.get_variable.return_value = mock_var

            with patch("pyqalculate_gui.export_csv_dialog.messagebox"):
                dlg._on_ok()
            assert dlg.get_result() is None
        finally:
            root.destroy()

    def test_export_exception(self) -> None:
        """Given: exportCSV raises an exception\nWhen:  _on_ok\nThen:  shows error, result stays None."""
        root = tk.Tk()
        root.withdraw()
        try:
            calc = _make_mock_calculator()
            calc._calc.exportCSV.side_effect = RuntimeError("disk full")
            dlg = _make_dialog(root, calculator=calc)
            frame = ttk.Frame(root)
            dlg._build_content(frame)
            dlg._dialog = root
            dlg._file_var.set("/tmp/test.csv")
            dlg._source_var.set("variable")
            dlg._var_name_var.set("myvar")

            mock_var = MagicMock()
            mock_var.get.return_value = "mock_mstruct"
            calc._calc.get_variable.return_value = mock_var

            with patch("pyqalculate_gui.export_csv_dialog.messagebox"):
                dlg._on_ok()
            assert dlg.get_result() is None
        finally:
            root.destroy()


# ---------------------------------------------------------------------------
# Integration — requires a display (skip in headless CI)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_DISPLAY, reason="No display available for GUI")
def test_show_and_cancel() -> None:
    """Given: an ExportCsvDialog\nWhen:  show() then cancel\nThen:  result is False."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = _make_dialog(root)
        root.after(50, dlg._on_cancel)
        dlg.show()
        assert dlg.get_result() is False
    finally:
        root.destroy()


@pytest.mark.skipif(not HAS_DISPLAY, reason="No display available for GUI")
def test_show_and_ok() -> None:
    """Given: an ExportCsvDialog\nWhen:  show() then OK (no file set — shows error, stays open)\nThen:  result stays None."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = _make_dialog(root)
        # Schedule ok after 50ms; it will fail validation and stay open
        # Then force cancel after another 100ms
        root.after(50, dlg._on_ok)
        root.after(200, dlg._on_cancel)
        dlg.show()
        # _on_ok fails (no file), _on_cancel closes with False
        assert dlg.get_result() is False
    finally:
        root.destroy()

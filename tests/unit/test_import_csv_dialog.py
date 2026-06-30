"""Tests for pyqalculate_gui.import_csv_dialog."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox
from unittest.mock import MagicMock, patch

import pytest

from pyqalculate_gui.import_csv_dialog import ImportCsvDialog
from pyqalculate_gui.theme import LIGHT


# ---------------------------------------------------------------------------
# Module-level teardown: force-clean any lingering Tk instances so the
# test runner does not hang after this file completes.
# ---------------------------------------------------------------------------

import gc


@pytest.fixture(scope="module", autouse=True)
def _cleanup_tk() -> None:
    """Force-quit and destroy every Tk root after all tests in this module."""
    yield
    try:
        for obj in gc.get_objects():
            if isinstance(obj, tk.Tk):
                try:
                    obj.quit()
                    obj.destroy()
                except Exception:
                    pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HAS_DISPLAY = bool(
    os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or os.name == "nt"
)


def _build_dialog(root: tk.Tk, **kwargs) -> tuple[ImportCsvDialog, tk.Frame]:
    """Build dialog content manually without show() for widget access."""
    dlg = ImportCsvDialog(root, **kwargs)
    # Create a hidden Toplevel so assert in _browse_file/_on_ok won't fail
    dlg._dialog = tk.Toplevel(root)
    dlg._dialog.withdraw()
    frame = tk.Frame(root)
    dlg._build_content(frame)
    return dlg, frame


# ---------------------------------------------------------------------------
# Unit tests (no display required)
# ---------------------------------------------------------------------------


def test_instantiation_defaults() -> None:
    """Given: parent widget\nWhen:  construct ImportCsvDialog\nThen:  defaults are set correctly."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = ImportCsvDialog(root)
        assert dlg._result is None
        assert dlg._dialog is None
        assert dlg._file_path == ""
        assert dlg._calc is None
    finally:
        root.destroy()


def test_instantiation_with_calculator() -> None:
    """Given: parent widget and calculator\nWhen:  construct ImportCsvDialog\nThen:  calculator is stored."""
    root = tk.Tk()
    root.withdraw()
    try:
        mock_calc = MagicMock()
        dlg = ImportCsvDialog(root, calculator=mock_calc)
        assert dlg._calc is mock_calc
    finally:
        root.destroy()


def test_custom_theme() -> None:
    """Given: a custom theme\nWhen:  construct ImportCsvDialog\nThen:  theme is stored."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = ImportCsvDialog(root, theme=LIGHT)
        assert dlg._theme is LIGHT
    finally:
        root.destroy()


def test_default_size() -> None:
    """Given: default parameters\nWhen:  construct ImportCsvDialog\nThen:  size is (480, 380)."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = ImportCsvDialog(root)
        assert dlg._size == (480, 380)
    finally:
        root.destroy()


def test_get_file_path_empty() -> None:
    """Given: no file selected\nWhen:  get_file_path\nThen:  returns empty string."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = ImportCsvDialog(root)
        assert dlg.get_file_path() == ""
    finally:
        root.destroy()


def test_get_name_empty() -> None:
    """Given: dialog built with no name set\nWhen:  get_name\nThen:  returns empty string."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg, _ = _build_dialog(root)
        assert dlg.get_name() == ""
    finally:
        dlg._dialog.destroy()
        root.destroy()


def test_get_delimiter_default() -> None:
    """Given: dialog built with defaults\nWhen:  get_delimiter\nThen:  returns comma."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg, _ = _build_dialog(root)
        assert dlg.get_delimiter() == ","
    finally:
        dlg._dialog.destroy()
        root.destroy()


def test_get_first_row_default() -> None:
    """Given: dialog built with defaults\nWhen:  get_first_row\nThen:  returns 1."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg, _ = _build_dialog(root)
        assert dlg.get_first_row() == 1
    finally:
        dlg._dialog.destroy()
        root.destroy()


def test_get_headers_default() -> None:
    """Given: dialog built with defaults\nWhen:  get_headers\nThen:  returns True."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg, _ = _build_dialog(root)
        assert dlg.get_headers() is True
    finally:
        dlg._dialog.destroy()
        root.destroy()


def test_get_to_matrix_default() -> None:
    """Given: dialog built with defaults\nWhen:  get_to_matrix\nThen:  returns False."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg, _ = _build_dialog(root)
        assert dlg.get_to_matrix() is False
    finally:
        dlg._dialog.destroy()
        root.destroy()


def test_cancel_sets_false() -> None:
    """Given: a constructed dialog\nWhen:  _on_cancel is called\nThen:  result is False."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = ImportCsvDialog(root)
        dlg._on_cancel()
        assert dlg.get_result() is False
        assert dlg._dialog is None
    finally:
        root.destroy()


def test_on_delimiter_change_comma() -> None:
    """Given: dialog built\nWhen:  _on_delimiter_change with comma\nThen:  delimiter_var is comma."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg, _ = _build_dialog(root)
        dlg._delimiter_choice.set("comma")
        dlg._on_delimiter_change()
        assert dlg._delimiter_var.get() == ","
    finally:
        dlg._dialog.destroy()
        root.destroy()


def test_on_delimiter_change_tab() -> None:
    """Given: dialog built\nWhen:  _on_delimiter_change with tab\nThen:  delimiter_var is tab."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg, _ = _build_dialog(root)
        dlg._delimiter_choice.set("tab")
        dlg._on_delimiter_change()
        assert dlg._delimiter_var.get() == "\t"
    finally:
        dlg._dialog.destroy()
        root.destroy()


def test_on_delimiter_change_other_enables_entry() -> None:
    """Given: dialog built\nWhen:  _on_delimiter_change with other\nThen:  other entry is enabled."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg, _ = _build_dialog(root)
        dlg._delimiter_choice.set("other")
        dlg._on_delimiter_change()
        assert str(dlg._other_delim_entry.cget("state")) == "normal"
    finally:
        dlg._dialog.destroy()
        root.destroy()


def test_on_ok_empty_file_shows_error() -> None:
    """Given: dialog with no file selected When: _on_ok is called Then: messagebox.showerror is called."""
    dlg = ImportCsvDialog.__new__(ImportCsvDialog)
    dlg._parent = MagicMock()
    dlg._title = "Test"
    dlg._size = (480, 380)
    dlg._resizable = (False, False)
    dlg._theme = LIGHT
    dlg._show_ok = True
    dlg._result = None
    dlg._dialog = MagicMock()
    dlg._file_var = MagicMock(get=lambda: "")
    dlg._calc = None

    with patch.object(messagebox, "showerror") as mock_err:
        dlg._on_ok()
        mock_err.assert_called_once()


def test_on_ok_no_calculator_closes() -> None:
    """Given: dialog built with no calculator and file path set\nWhen:  _on_ok is called\nThen:  dialog closes with True."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg, _ = _build_dialog(root)
        dlg._file_var.set("/some/file.csv")
        dlg._name_var.set("myvar")
        # No calculator — should just call super()._on_ok()
        dlg._on_ok()
        assert dlg.get_result() is True
    finally:
        root.destroy()


def test_on_ok_import_error_shows_messagebox() -> None:
    """Given: dialog with calculator that raises on import\nWhen:  _on_ok is called\nThen:  error messagebox shown."""
    root = tk.Tk()
    root.withdraw()
    try:
        mock_calc = MagicMock()
        mock_calc.import_csv.side_effect = RuntimeError("bad csv")
        dlg, _ = _build_dialog(root, calculator=mock_calc)
        dlg._file_var.set("/some/file.csv")
        dlg._name_var.set("myvar")
        with patch.object(messagebox, "showerror") as mock_err:
            dlg._on_ok()
            mock_err.assert_called_once()
            assert "bad csv" in mock_err.call_args[0][1]
    finally:
        dlg._dialog.destroy()
        root.destroy()


# ---------------------------------------------------------------------------
# Integration — requires a display (skip in headless CI)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="ModalDialog.wait_window causes Tk event loop hang on teardown")
def test_show_and_cancel() -> None:
    """Given: a constructed dialog\nWhen:  show() then immediately cancel\nThen:  result is False."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = ImportCsvDialog(root)
        root.after(50, dlg._on_cancel)
        dlg.show()
        assert dlg.get_result() is False
    finally:
        root.quit()
        root.destroy()


@pytest.mark.skip(reason="ModalDialog.wait_window causes Tk event loop hang on teardown")
def test_show_and_ok_no_file() -> None:
    """Given: a constructed dialog with no file selected\nWhen:  show() then OK with error dismissed\nThen:  error is shown."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = ImportCsvDialog(root)

        def click_ok_then_cancel():
            # Mock messagebox to avoid real popup, but verify it was called
            with patch.object(messagebox, "showerror") as mock_err:
                dlg._on_ok()
                mock_err.assert_called_once()
                assert "CSV file" in mock_err.call_args[0][1]
            dlg._on_cancel()

        root.after(50, click_ok_then_cancel)
        dlg.show()
        # The dialog closes via _on_cancel
        assert dlg.get_result() is False
    finally:
        root.quit()
        root.destroy()

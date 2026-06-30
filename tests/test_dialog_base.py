"""Tests for pyqalculate_gui.dialogs.base."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk

import pytest

from pyqalculate_gui.dialogs.base import ModalDialog
from pyqalculate_gui.theme import LIGHT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class SimpleDialog(ModalDialog):
    """Minimal concrete subclass for testing."""

    def _build_content(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Hello").pack()


# ---------------------------------------------------------------------------
# Unit tests (no display required)
# ---------------------------------------------------------------------------

def test_modal_dialog_is_abstract() -> None:
    """Given: ModalDialog is abstract\nWhen:  instantiate directly\nThen:  raises TypeError."""
    with pytest.raises(TypeError, match="abstract method"):
        # parent=None is fine — the error fires before __init__ body runs
        ModalDialog(None, "test")  # type: ignore[arg-type]


def test_subclass_instantiation() -> None:
    """Given: a concrete subclass\nWhen:  construct it\nThen:  _result defaults to None, no dialog yet."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = SimpleDialog(root, "Test")
        assert dlg._result is None
        assert dlg._dialog is None
        assert dlg._title == "Test"
        assert dlg._size == (400, 300)
    finally:
        root.destroy()


def test_result_false_after_cancel() -> None:
    """Given: a constructed dialog\nWhen:  _on_cancel is called directly\nThen:  result is False."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = SimpleDialog(root, "Test")
        dlg._on_cancel()
        assert dlg.get_result() is False
        assert dlg._dialog is None
    finally:
        root.destroy()


def test_result_true_after_ok() -> None:
    """Given: a constructed dialog\nWhen:  _on_ok is called directly\nThen:  result is True."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = SimpleDialog(root, "Test")
        dlg._on_ok()
        assert dlg.get_result() is True
        assert dlg._dialog is None
    finally:
        root.destroy()


def test_theme_defaults_to_light() -> None:
    """Given: no theme argument\nWhen:  construct SimpleDialog\nThen:  theme is LIGHT."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = SimpleDialog(root, "Test")
        assert dlg._theme is LIGHT
    finally:
        root.destroy()


def test_custom_size() -> None:
    """Given: custom size tuple\nWhen:  construct dialog\nThen:  size stored correctly."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = SimpleDialog(root, "Test", size=(600, 400))
        assert dlg._size == (600, 400)
    finally:
        root.destroy()


def test_show_ok_defaults_true() -> None:
    """Given: no show_ok argument\nWhen: construct SimpleDialog\nThen: _show_ok is True."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = SimpleDialog(root, "Test")
        assert dlg._show_ok is True
    finally:
        root.destroy()


def test_show_ok_false_stored() -> None:
    """Given: show_ok=False\nWhen: construct SimpleDialog\nThen: _show_ok is False."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = SimpleDialog(root, "Test", show_ok=False)
        assert dlg._show_ok is False
    finally:
        root.destroy()


# ---------------------------------------------------------------------------
# Integration — requires a display (skip in headless CI)
# ---------------------------------------------------------------------------

HAS_DISPLAY = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or os.name == "nt")


@pytest.mark.skipif(not HAS_DISPLAY, reason="No display available for GUI")
def test_show_and_cancel() -> None:
    """Given: a concrete dialog\nWhen:  show() then immediately cancel\nThen:  result is False."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = SimpleDialog(root, "Test", size=(200, 100))
        # Schedule cancel after 50ms so the dialog has time to open
        root.after(50, dlg._on_cancel)
        dlg.show()
        assert dlg.get_result() is False
    finally:
        root.destroy()


@pytest.mark.skipif(not HAS_DISPLAY, reason="No display available for GUI")
def test_show_and_ok() -> None:
    """Given: a concrete dialog\nWhen:  show() then click OK\nThen:  result is True."""
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = SimpleDialog(root, "Test", size=(200, 100))
        root.after(50, dlg._on_ok)
        dlg.show()
        assert dlg.get_result() is True
    finally:
        root.destroy()

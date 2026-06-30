"""Tests for the ExpressionEdit widget."""

from __future__ import annotations

import os
import sys
import tkinter as tk

import pytest

from pyqalculate_gui.event_bus import EventBus, EXPRESSION_SUBMITTED
from pyqalculate_gui.state import AppState
from pyqalculate_gui.theme import LIGHT


def _no_display() -> bool:
    """Check if a display is available."""
    if sys.platform == "win32":
        return False
    return not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")


# Skip all tests if no display is available (CI environments)
pytestmark = pytest.mark.skipif(
    _no_display(),
    reason="No display available for tkinter",
)


@pytest.fixture
def root():
    """Create a root Tk window for testing."""
    try:
        root = tk.Tk()
        root.withdraw()  # hide window
    except tk.TclError:
        pytest.skip("tkinter Tcl libraries not available")
    yield root
    root.destroy()


@pytest.fixture
def bus():
    """Create an EventBus for testing."""
    return EventBus()


@pytest.fixture
def state():
    """Create AppState for testing."""
    return AppState()


@pytest.fixture
def edit(root, bus, state):
    """Create an ExpressionEdit widget for testing."""
    from pyqalculate_gui.expression_edit import ExpressionEdit

    return ExpressionEdit(root, theme=LIGHT, event_bus=bus, state=state)


class TestGetSetExpression:
    def test_get_expression_empty(self, edit) -> None:
        assert edit.get_expression() == ""

    def test_set_expression(self, edit) -> None:
        edit.set_expression("2+3")
        assert edit.get_expression() == "2+3"

    def test_set_expression_replaces(self, edit) -> None:
        edit.set_expression("abc")
        edit.set_expression("xyz")
        assert edit.get_expression() == "xyz"

    def test_set_expression_strips_whitespace(self, edit) -> None:
        edit.set_expression("  hello  ")
        assert edit.get_expression() == "hello"


class TestClear:
    def test_clear(self, edit) -> None:
        edit.set_expression("test")
        edit.clear()
        assert edit.get_expression() == ""

    def test_clear_empty(self, edit) -> None:
        edit.clear()
        assert edit.get_expression() == ""


class TestInsertAtCursor:
    def test_insert_at_cursor(self, edit) -> None:
        edit.insert_at_cursor("abc")
        assert edit.get_expression() == "abc"

    def test_insert_multiple(self, edit) -> None:
        edit.insert_at_cursor("a")
        edit.insert_at_cursor("b")
        edit.insert_at_cursor("c")
        assert edit.get_expression() == "abc"


class TestSubmit:
    def test_submit_emits_event(self, edit, bus) -> None:
        received: list[str] = []
        bus.subscribe(EXPRESSION_SUBMITTED, lambda expr: received.append(expr))
        edit.set_expression("2+2")
        edit._on_submit()
        assert received == ["2+2"]

    def test_submit_empty_does_not_emit(self, edit, bus) -> None:
        received: list[str] = []
        bus.subscribe(EXPRESSION_SUBMITTED, lambda expr: received.append(expr))
        edit._on_submit()
        assert received == []


class TestUndoRedo:
    @staticmethod
    def _simulate_type(widget, text: str) -> None:
        """Simulate user typing by updating current_text, undo stack, and widget."""
        widget._undo_stack.append(widget._current_text)
        widget._redo_stack.clear()
        widget._current_text = text
        widget._entry.delete("1.0", tk.END)
        widget._entry.insert("1.0", text)

    def test_undo_restores_previous(self, edit) -> None:
        self._simulate_type(edit, "first")
        self._simulate_type(edit, "second")
        edit.undo()
        assert edit.get_expression() == "first"

    def test_redo_after_undo(self, edit) -> None:
        self._simulate_type(edit, "first")
        self._simulate_type(edit, "second")
        edit.undo()
        edit.redo()
        assert edit.get_expression() == "second"

    def test_undo_clears_redo_on_new_change(self, edit) -> None:
        self._simulate_type(edit, "a")
        self._simulate_type(edit, "b")
        edit.undo()
        # New change should clear redo
        self._simulate_type(edit, "c")
        edit.redo()
        assert edit.get_expression() == "c"  # redo stack was cleared

    def test_undo_empty_stack(self, edit) -> None:
        edit.undo()  # should not raise
        assert edit.get_expression() == ""

    def test_redo_empty_stack(self, edit) -> None:
        edit.redo()  # should not raise
        assert edit.get_expression() == ""

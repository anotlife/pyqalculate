"""Tests for the HistoryView widget."""

from __future__ import annotations

import os
import sys
import tkinter as tk

import pytest

from pyqalculate_gui.event_bus import EventBus, HISTORY_RECALLED
from pyqalculate_gui.history_view import HistoryView, HistoryEntry
from pyqalculate_gui.i18n import _
from pyqalculate_gui.theme import LIGHT, DARK


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


@pytest.fixture(scope="session")
def root():
    """Create a single root Tk window shared across all tests."""
    root = tk.Tk()
    root.withdraw()  # hide window
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def bus():
    """Create an EventBus."""
    return EventBus()


# ------------------------------------------------------------------
# HistoryEntry dataclass
# ------------------------------------------------------------------


class TestHistoryEntry:
    def test_creation(self) -> None:
        """Given: fields for an entry When: creating HistoryEntry Then: all fields stored."""
        entry = HistoryEntry(
            expression="2+2",
            result="4",
            exact=True,
            entry_type="expression",
        )
        assert entry.expression == "2+2"
        assert entry.result == "4"
        assert entry.exact is True
        assert entry.entry_type == "expression"


# ------------------------------------------------------------------
# HistoryView — add_expression
# ------------------------------------------------------------------


class TestAddExpression:
    def test_add_expression_stores_entry(self, root: tk.Tk) -> None:
        """Given: empty history When: adding expression Then: entry stored."""
        view = HistoryView(root)
        view.add_expression("2+2")
        assert len(view._entries) == 1
        assert view._entries[0].expression == "2+2"
        assert view._entries[0].entry_type == "expression"

    def test_add_expression_updates_listbox(self, root: tk.Tk) -> None:
        """Given: empty history When: adding expression Then: listbox shows >>> prefix."""
        view = HistoryView(root)
        view.add_expression("pi")
        assert view._listbox.size() == 1
        assert view._listbox.get(0) == ">>> pi"

    def test_add_multiple_expressions(self, root: tk.Tk) -> None:
        """Given: empty history When: adding multiple expressions Then: all appear."""
        view = HistoryView(root)
        view.add_expression("a")
        view.add_expression("b")
        view.add_expression("c")
        assert view._listbox.size() == 3
        assert view._listbox.get(2) == ">>> c"


# ------------------------------------------------------------------
# HistoryView — add_result
# ------------------------------------------------------------------


class TestAddResult:
    def test_add_exact_result(self, root: tk.Tk) -> None:
        """Given: empty history When: adding exact result Then: = prefix shown."""
        view = HistoryView(root)
        view.add_result("4", exact=True)
        assert view._listbox.size() == 1
        assert view._listbox.get(0) == "= 4"

    def test_add_approximate_result(self, root: tk.Tk) -> None:
        """Given: empty history When: adding approximate result Then: ≈ prefix shown."""
        view = HistoryView(root)
        view.add_result("3.14159", exact=False)
        assert view._listbox.get(0) == "≈ 3.14159"

    def test_add_result_stores_entry(self, root: tk.Tk) -> None:
        """Given: empty history When: adding result Then: entry stored."""
        view = HistoryView(root)
        view.add_result("42", exact=True)
        assert len(view._entries) == 1
        assert view._entries[0].result == "42"
        assert view._entries[0].exact is True
        assert view._entries[0].entry_type == "result"


# ------------------------------------------------------------------
# HistoryView — add_error
# ------------------------------------------------------------------


class TestAddError:
    def test_add_error(self, root: tk.Tk) -> None:
        """Given: empty history When: adding error Then: Error: prefix shown."""
        view = HistoryView(root)
        view.add_error("parse failed")
        assert view._listbox.size() == 1
        assert view._listbox.get(0) == _("Error: {}").format("parse failed")

    def test_add_error_stores_entry(self, root: tk.Tk) -> None:
        """Given: empty history When: adding error Then: entry stored as error type."""
        view = HistoryView(root)
        view.add_error("division by zero")
        assert view._entries[0].entry_type == "error"
        assert view._entries[0].result == "division by zero"


# ------------------------------------------------------------------
# HistoryView — get_answer
# ------------------------------------------------------------------


class TestGetAnswer:
    def test_answer_returns_most_recent(self, root: tk.Tk) -> None:
        """Given: two results When: get_answer(1) Then: most recent returned."""
        view = HistoryView(root)
        view.add_result("first", exact=True)
        view.add_result("second", exact=True)
        assert view.get_answer(1) == "second"

    def test_answer_returns_nth_from_end(self, root: tk.Tk) -> None:
        """Given: three results When: get_answer(2) Then: second most recent."""
        view = HistoryView(root)
        view.add_result("a", exact=True)
        view.add_result("b", exact=True)
        view.add_result("c", exact=True)
        assert view.get_answer(2) == "b"

    def test_answer_oldest(self, root: tk.Tk) -> None:
        """Given: three results When: get_answer(3) Then: oldest returned."""
        view = HistoryView(root)
        view.add_result("x", exact=True)
        view.add_result("y", exact=True)
        view.add_result("z", exact=True)
        assert view.get_answer(3) == "x"

    def test_answer_out_of_range_returns_none(self, root: tk.Tk) -> None:
        """Given: one result When: get_answer(5) Then: None returned."""
        view = HistoryView(root)
        view.add_result("42", exact=True)
        assert view.get_answer(5) is None

    def test_answer_zero_returns_none(self, root: tk.Tk) -> None:
        """Given: results exist When: get_answer(0) Then: None returned."""
        view = HistoryView(root)
        view.add_result("42", exact=True)
        assert view.get_answer(0) is None

    def test_answer_negative_returns_none(self, root: tk.Tk) -> None:
        """Given: results exist When: get_answer(-1) Then: None returned."""
        view = HistoryView(root)
        view.add_result("42", exact=True)
        assert view.get_answer(-1) is None

    def test_answer_ignores_errors(self, root: tk.Tk) -> None:
        """Given: error then result When: get_answer(1) Then: only result counted."""
        view = HistoryView(root)
        view.add_error("bad input")
        view.add_result("42", exact=True)
        assert view.get_answer(1) == "42"

    def test_answer_ignores_expressions(self, root: tk.Tk) -> None:
        """Given: expression then result When: get_answer(1) Then: only result counted."""
        view = HistoryView(root)
        view.add_expression("2+2")
        view.add_result("4", exact=True)
        assert view.get_answer(1) == "4"

    def test_answer_empty_history(self, root: tk.Tk) -> None:
        """Given: empty history When: get_answer(1) Then: None returned."""
        view = HistoryView(root)
        assert view.get_answer(1) is None


# ------------------------------------------------------------------
# HistoryView — clear
# ------------------------------------------------------------------


class TestClear:
    def test_clear_removes_all_entries(self, root: tk.Tk) -> None:
        """Given: entries exist When: clear Then: entries list empty."""
        view = HistoryView(root)
        view.add_expression("2+2")
        view.add_result("4", exact=True)
        view.clear()
        assert view._entries == []

    def test_clear_removes_listbox_items(self, root: tk.Tk) -> None:
        """Given: entries exist When: clear Then: listbox empty."""
        view = HistoryView(root)
        view.add_expression("2+2")
        view.add_result("4", exact=True)
        view.clear()
        assert view._listbox.size() == 0

    def test_can_add_after_clear(self, root: tk.Tk) -> None:
        """Given: cleared history When: adding new entry Then: works correctly."""
        view = HistoryView(root)
        view.add_result("old", exact=True)
        view.clear()
        view.add_result("new", exact=True)
        assert view.get_answer(1) == "new"


# ------------------------------------------------------------------
# HistoryView — EventBus integration
# ------------------------------------------------------------------


class TestEventBus:
    def test_double_click_emits_recall(self, root: tk.Tk, bus: EventBus) -> None:
        """Given: expression in history When: simulating double-click Then: event emitted."""
        view = HistoryView(root, event_bus=bus)
        view.add_expression("pi")

        received: list[str] = []
        bus.subscribe(HISTORY_RECALLED, lambda expr: received.append(expr))

        # Select first item and simulate double-click
        view._listbox.select_set(0)
        view._on_recall()

        assert received == ["pi"]

    def test_no_event_without_bus(self, root: tk.Tk) -> None:
        """Given: no event_bus When: double-click Then: no crash."""
        view = HistoryView(root)
        view.add_expression("pi")
        view._listbox.select_set(0)
        # Should not raise
        view._on_recall()

    def test_recall_on_result_does_nothing(self, root: tk.Tk, bus: EventBus) -> None:
        """Given: result entry When: double-click result Then: no event (no expression)."""
        view = HistoryView(root, event_bus=bus)
        view.add_result("42", exact=True)

        received: list[str] = []
        bus.subscribe(HISTORY_RECALLED, lambda expr: received.append(expr))

        view._listbox.select_set(0)
        view._on_recall()

        assert received == []


# ------------------------------------------------------------------
# HistoryView — theme
# ------------------------------------------------------------------


class TestTheme:
    def test_default_theme_is_light(self, root: tk.Tk) -> None:
        """Given: no theme specified When: creating view Then: uses LIGHT theme."""
        view = HistoryView(root)
        assert view._theme is LIGHT

    def test_custom_theme(self, root: tk.Tk) -> None:
        """Given: DARK theme When: creating view Then: theme applied."""
        view = HistoryView(root, theme=DARK)
        assert view._theme is DARK

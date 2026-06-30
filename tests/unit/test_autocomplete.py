"""Tests for the AutoComplete popup system."""

from __future__ import annotations

import os
import sys
import tkinter as tk

import pytest

from pyqalculate_gui.autocomplete import AutoComplete, _score_item
from pyqalculate_gui.theme import LIGHT


# Skip all tests if no display is available (CI environments)
def _no_display() -> bool:
    if sys.platform == "win32":
        return False
    return not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")


pytestmark = pytest.mark.skipif(
    _no_display(),
    reason="No display available for tkinter",
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def root():
    """Create a root Tk window for testing."""
    try:
        r = tk.Tk()
        r.withdraw()
    except tk.TclError:
        pytest.skip("tkinter Tcl libraries not available")
    yield r
    r.destroy()


@pytest.fixture
def frame(root):
    """Create a parent frame."""
    f = tk.Frame(root)
    f.pack()
    return f


@pytest.fixture
def ac(frame):
    """Create an AutoComplete instance without calculator (items set manually)."""
    return AutoComplete(parent=frame, theme=LIGHT, calculator=None)


# ------------------------------------------------------------------
# _score_item — module-level scoring function
# ------------------------------------------------------------------


class TestScoreItem:
    def test_exact_match_returns_6(self) -> None:
        assert _score_item("sin", "Function: sin", "sin") == 6

    def test_exact_match_case_insensitive(self) -> None:
        assert _score_item("sin", "Function: sin", "SIN") == 6

    def test_name_starts_with_returns_5(self) -> None:
        assert _score_item("sinh", "Function: sinh", "sin") == 5

    def test_title_starts_with_returns_4(self) -> None:
        assert _score_item("foo", "Function: bar", "Function") == 4

    def test_name_contains_returns_3(self) -> None:
        assert _score_item("asin", "Function: asin", "sin") == 3

    def test_title_contains_returns_2(self) -> None:
        assert _score_item("foo", "Variable: special", "special") == 2

    def test_no_match_returns_0(self) -> None:
        assert _score_item("pi", "Variable: pi", "xyz") == 0

    def test_empty_prefix_matches_via_startswith(self) -> None:
        # str.startswith("") is always True → score 5
        # Guard lives in update(), not in _score_item
        assert _score_item("sin", "Function: sin", "") == 5


# ------------------------------------------------------------------
# _filter_items
# ------------------------------------------------------------------


class TestFilterItems:
    @staticmethod
    def _seed(ac: AutoComplete) -> None:
        """Manually populate items for testing without a calculator."""
        ac._items = [
            ("sin", "Function: sin", "function"),
            ("sinh", "Function: sinh", "function"),
            ("asin", "Function: asin", "function"),
            ("cos", "Function: cos", "function"),
            ("pi", "Variable: pi", "variable"),
            ("meter", "Unit: meter", "unit"),
        ]

    def test_prefix_filters_correctly(self, ac: AutoComplete) -> None:
        self._seed(ac)
        ac._filter_items("sin")
        names = [name for name, _title, _score in ac._filtered]
        assert "sin" in names
        assert "sinh" in names
        assert "asin" in names
        assert "cos" not in names

    def test_exact_match_ranks_first(self, ac: AutoComplete) -> None:
        self._seed(ac)
        ac._filter_items("sin")
        # sin (score 6) should be first, then sinh (5), then asin (3)
        assert ac._filtered[0][0] == "sin"

    def test_empty_prefix_returns_empty(self, ac: AutoComplete) -> None:
        self._seed(ac)
        ac._filter_items("")
        assert ac._filtered == []

    def test_no_match_returns_empty(self, ac: AutoComplete) -> None:
        self._seed(ac)
        ac._filter_items("zzz")
        assert ac._filtered == []

    def test_case_insensitive(self, ac: AutoComplete) -> None:
        self._seed(ac)
        ac._filter_items("SIN")
        names = [name for name, _title, _score in ac._filtered]
        assert "sin" in names

    def test_limits_to_max_visible(self, ac: AutoComplete) -> None:
        # Create more than _MAX_VISIBLE items matching "a"
        ac._items = [
            (f"alpha{i}", f"Function: alpha{i}", "function")
            for i in range(30)
        ]
        ac._filter_items("alpha")
        assert len(ac._filtered) <= 20


# ------------------------------------------------------------------
# select_next / select_previous
# ------------------------------------------------------------------


class TestNavigation:
    @staticmethod
    def _show_with_items(ac: AutoComplete) -> None:
        """Populate, filter, and show the popup with test items."""
        ac._items = [
            ("sin", "Function: sin", "function"),
            ("cos", "Function: cos", "function"),
            ("tan", "Function: tan", "function"),
        ]
        ac._filter_items("s")
        # "sin" starts with "s" → score 5; cos, tan don't match "s"
        # Let's use a broader prefix
        ac._filter_items("")  # reset
        ac._items = [
            ("alpha", "Function: alpha", "function"),
            ("beta", "Function: beta", "function"),
            ("gamma", "Function: gamma", "function"),
        ]
        # Use a prefix that matches all three via title
        ac._filter_items("Function")
        if not ac._filtered:
            # Fallback: just set filtered directly
            ac._filtered = [
                ("alpha", "Function: alpha", 4),
                ("beta", "Function: beta", 4),
                ("gamma", "Function: gamma", 4),
            ]
        ac._update_popup()

    def test_select_next_wraps_around(self, ac: AutoComplete) -> None:
        self._show_with_items(ac)
        assert ac.is_visible()
        assert ac._tree is not None

        children = ac._tree.get_children()
        count = len(children)
        assert count >= 2

        # Move to end then wrap
        for _ in range(count):
            ac.select_next()
        assert ac._selected_index == 0

    def test_select_previous_wraps_around(self, ac: AutoComplete) -> None:
        self._show_with_items(ac)
        assert ac._tree is not None
        assert ac._selected_index == 0

        ac.select_previous()
        children = ac._tree.get_children()
        assert ac._selected_index == len(children) - 1

    def test_select_next_changes_index(self, ac: AutoComplete) -> None:
        self._show_with_items(ac)
        assert ac._selected_index == 0
        ac.select_next()
        assert ac._selected_index == 1


# ------------------------------------------------------------------
# get_selected
# ------------------------------------------------------------------


class TestGetSelected:
    def test_returns_none_when_no_tree(self, ac: AutoComplete) -> None:
        assert ac.get_selected() is None

    def test_returns_selected_name(self, ac: AutoComplete) -> None:
        ac._filtered = [
            ("sin", "Function: sin", 5),
            ("cos", "Function: cos", 5),
        ]
        ac._update_popup()
        assert ac.get_selected() == "sin"

    def test_returns_none_when_no_selection(self, ac: AutoComplete) -> None:
        ac._filtered = [("sin", "Function: sin", 5)]
        ac._create_popup()
        assert ac._tree is not None
        # Clear selection
        for item in ac._tree.get_children():
            ac._tree.selection_remove(item)
        assert ac.get_selected() is None


# ------------------------------------------------------------------
# set_enabled
# ------------------------------------------------------------------


class TestSetEnabled:
    def test_disabling_hides_popup(self, ac: AutoComplete) -> None:
        ac._filtered = [("sin", "Function: sin", 5)]
        ac._update_popup()
        assert ac.is_visible()

        ac.set_enabled(False)
        assert not ac.is_visible()

    def test_enabled_default(self, ac: AutoComplete) -> None:
        assert ac._enabled is True

    def test_update_skipped_when_disabled(self, ac: AutoComplete) -> None:
        ac._items = [("sin", "Function: sin", "function")]
        ac.set_enabled(False)
        ac.update("sin", 3)
        assert not ac.is_visible()

    def test_re_enable_allows_update(self, ac: AutoComplete) -> None:
        ac._items = [("sin", "Function: sin", "function")]
        ac.set_enabled(False)
        ac.set_enabled(True)
        ac.update("sin", 3)
        assert ac.is_visible()


# ------------------------------------------------------------------
# hide / is_visible
# ------------------------------------------------------------------


class TestVisibility:
    def test_initially_hidden(self, ac: AutoComplete) -> None:
        assert not ac.is_visible()

    def test_hide_when_no_popup(self, ac: AutoComplete) -> None:
        ac.hide()  # should not raise
        assert not ac.is_visible()

    def test_visible_after_update(self, ac: AutoComplete) -> None:
        ac._items = [("sin", "Function: sin", "function")]
        ac.update("sin", 3)
        assert ac.is_visible()

    def test_hide_on_short_input(self, ac: AutoComplete) -> None:
        ac._items = [("sin", "Function: sin", "function")]
        ac.update("s", 1)
        # completion_min is 1, so "s" should trigger
        assert ac.is_visible()
        ac.update("", 0)
        assert not ac.is_visible()


# ------------------------------------------------------------------
# update — word extraction
# ------------------------------------------------------------------


class TestUpdate:
    def test_extracts_word_at_cursor(self, ac: AutoComplete) -> None:
        ac._items = [("sin", "Function: sin", "function")]
        ac.update("2 + sin", 7)
        assert ac.is_visible()

    def test_stops_at_operator(self, ac: AutoComplete) -> None:
        ac._items = [("sin", "Function: sin", "function")]
        ac.update("2+sin", 5)
        assert ac.is_visible()

    def test_stops_at_paren(self, ac: AutoComplete) -> None:
        ac._items = [("sin", "Function: sin", "function")]
        ac.update("(sin", 4)
        assert ac.is_visible()

    def test_no_match_hides(self, ac: AutoComplete) -> None:
        ac._items = [("cos", "Function: cos", "function")]
        ac.update("sin", 3)
        assert not ac.is_visible()


# ------------------------------------------------------------------
# set_on_select callback
# ------------------------------------------------------------------


class TestOnSelect:
    def test_callback_invoked_on_selection(self, ac: AutoComplete) -> None:
        received: list[str] = []
        ac.set_on_select(lambda name: received.append(name))

        ac._filtered = [("sin", "Function: sin", 5)]
        ac._update_popup()

        ac._on_item_select()
        assert received == ["sin"]
        assert not ac.is_visible()

    def test_callback_not_invoked_when_no_selection(
        self, ac: AutoComplete,
    ) -> None:
        received: list[str] = []
        ac.set_on_select(lambda name: received.append(name))

        ac._filtered = [("sin", "Function: sin", 5)]
        ac._create_popup()
        assert ac._tree is not None
        for item in ac._tree.get_children():
            ac._tree.selection_remove(item)

        ac._on_item_select()
        assert received == []

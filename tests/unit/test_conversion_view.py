"""Tests for ConversionView widget."""

from __future__ import annotations

import os
import sys
import tkinter as tk
from unittest.mock import MagicMock

import pytest

from pyqalculate_gui.event_bus import CONVERSION_RESULT, EventBus
from pyqalculate_gui.theme import DARK, LIGHT, Theme


def _no_display() -> bool:
    """Check if a display is available."""
    if sys.platform == "win32":
        return False
    return not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")


pytestmark = pytest.mark.skipif(
    _no_display(),
    reason="No display available for tkinter",
)

# Single shared root — avoids Windows tcl_findLibrary crash from many Tk()
_root = tk.Tk()
_root.withdraw()


@pytest.fixture(autouse=True)
def _shared_root():
    yield _root


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def mock_calc():
    """A mock CalculatorService with predictable data."""
    calc = MagicMock()
    calc.get_unit_categories.return_value = {
        "Length": ["m", "km", "ft"],
        "Mass": ["kg", "lb"],
    }
    calc.get_unit_display_name.side_effect = lambda k: {
        "m": "meter (m)",
        "km": "kilometer (km)",
        "ft": "foot (ft)",
        "kg": "kilogram (kg)",
        "lb": "pound (lb)",
    }.get(k, k)
    calc.convert.return_value = "1000 meter (m)"
    return calc


@pytest.fixture
def view(mock_calc):
    """Create a ConversionView with a mock calculator."""
    from pyqalculate_gui.conversion_view import ConversionView

    return ConversionView(_root, theme=LIGHT, calculator=mock_calc)


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class TestConstructor:
    def test_default_theme(self, mock_calc) -> None:
        from pyqalculate_gui.conversion_view import ConversionView

        v = ConversionView(_root, calculator=mock_calc)
        assert v._theme is LIGHT
        assert v._event_bus is None
        assert v._calc is mock_calc

    def test_custom_theme(self, mock_calc) -> None:
        from pyqalculate_gui.conversion_view import ConversionView

        v = ConversionView(_root, theme=DARK, calculator=mock_calc)
        assert v._theme is DARK

    def test_no_calculator(self) -> None:
        """Widget builds without error when calculator is None."""
        from pyqalculate_gui.conversion_view import ConversionView

        v = ConversionView(_root, calculator=None)
        assert v._calc is None
        assert v._cat_map == {}

    def test_categories_populated(self, view, mock_calc) -> None:
        """Category tree is built from calculator data."""
        mock_calc.get_unit_categories.assert_called_once()
        # "All Units" + Length + Mass = 3+ nodes
        children = view._cat_tree.get_children()
        assert len(children) >= 1


# ---------------------------------------------------------------------------
# Category browsing
# ---------------------------------------------------------------------------


class TestCategoryBrowsing:
    def test_all_units_node_exists(self, view) -> None:
        from pyqalculate_gui.conversion_view import _ALL_NODE

        assert any(c == _ALL_NODE for c in view._cat_tree.get_children())

    def test_select_category_populates_units(self, view) -> None:
        """Selecting a category node fills the listbox."""
        length_iid = None
        for iid in view._cat_tree.get_children():
            for child in view._cat_tree.get_children(iid):
                if view._cat_tree.item(child, "text") == "Length":
                    length_iid = child
                    break
            if length_iid:
                break

        if length_iid is None:
            pytest.skip("Length category not found in tree")

        view._cat_tree.selection_set(length_iid)
        view._cat_tree.event_generate("<<TreeviewSelect>>")
        assert view._unit_listbox.size() > 0


# ---------------------------------------------------------------------------
# Unit selection
# ---------------------------------------------------------------------------


class TestUnitSelection:
    def test_select_unit_sets_from_display(self, view) -> None:
        """Selecting a unit in the listbox updates the From label."""
        view._current_units = [("meter (m)", "m"), ("kilometer (km)", "km")]
        view._unit_listbox.delete(0, tk.END)
        for display, _ in view._current_units:
            view._unit_listbox.insert(tk.END, display)

        view._unit_listbox.selection_set(0)
        view._apply_selection()

        assert view._from_var.get() == "meter (m)"
        assert view._selected_from_key == "m"

    def test_double_click_triggers_convert(self, view, mock_calc) -> None:
        """Double-click selects and converts."""
        view._current_units = [("meter (m)", "m")]
        view._unit_listbox.delete(0, tk.END)
        view._unit_listbox.insert(tk.END, "meter (m)")
        view._unit_listbox.selection_set(0)
        view._to_var.set("km")
        mock_calc.reset_mock()

        view._on_unit_double_click(None)

        mock_calc.convert.assert_called()


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------


class TestConversion:
    def test_convert_with_valid_inputs(self, view, mock_calc) -> None:
        """Successful conversion displays result."""
        view._selected_from_key = "m"
        view._to_var.set("km")
        view._value_var.set("1000")
        mock_calc.reset_mock()

        view._do_convert()

        mock_calc.convert.assert_called_once_with("1000", "m", "km")
        assert view._result_var.get() == "1000 meter (m)"

    def test_convert_missing_value(self, view) -> None:
        view._value_var.set("")
        view._selected_from_key = "m"
        view._to_var.set("km")
        view._do_convert()
        assert "Enter a value" in view._error_var.get()

    def test_convert_missing_from_unit(self, view) -> None:
        view._value_var.set("1")
        view._selected_from_key = None
        view._to_var.set("km")
        view._do_convert()
        assert "Select a source unit" in view._error_var.get()

    def test_convert_missing_target(self, view) -> None:
        view._value_var.set("1")
        view._selected_from_key = "m"
        view._to_var.set("")
        view._do_convert()
        assert "Enter a target unit" in view._error_var.get()

    def test_convert_exception(self, view, mock_calc) -> None:
        mock_calc.convert.side_effect = RuntimeError("bad unit")
        view._selected_from_key = "m"
        view._to_var.set("km")
        view._value_var.set("1")

        view._do_convert()
        assert "Conversion error" in view._error_var.get()

    def test_convert_empty_result(self, view, mock_calc) -> None:
        mock_calc.convert.return_value = ""
        view._selected_from_key = "m"
        view._to_var.set("km")
        view._value_var.set("1")

        view._do_convert()
        assert "Cannot convert" in view._error_var.get()

    def test_convert_no_calculator(self) -> None:
        from pyqalculate_gui.conversion_view import ConversionView

        v = ConversionView(_root, calculator=None)
        v._selected_from_key = "m"
        v._to_var.set("km")
        v._value_var.set("1")
        v._do_convert()
        assert "No calculator" in v._error_var.get()


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------


class TestEventBus:
    def test_emit_conversion_result(self, view, mock_calc, bus) -> None:
        events: list[tuple[str, str]] = []
        bus.subscribe(CONVERSION_RESULT, lambda expr, res: events.append((expr, res)))

        # Set state first (triggers auto-convert via traces)
        view._selected_from_key = "m"
        view._to_var.set("km")
        view._value_var.set("1000")
        mock_calc.reset_mock()

        # Attach bus AFTER setup so auto-convert doesn't emit
        view._event_bus = bus
        events.clear()

        view._do_convert()

        assert len(events) == 1
        assert events[0][0] == "1000 m to km"
        assert events[0][1] == "1000 meter (m)"

    def test_no_event_bus_no_emit(self, view, mock_calc) -> None:
        view._event_bus = None
        view._selected_from_key = "m"
        view._to_var.set("km")
        view._value_var.set("1000")
        view._do_convert()  # should not raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class TestPublicAPI:
    def test_set_value(self, view) -> None:
        view.set_value("42")
        assert view._value_var.get() == "42"

    def test_set_target_unit(self, view) -> None:
        view.set_target_unit("ft")
        assert view._to_var.get() == "ft"

    def test_get_last_result_default(self, view) -> None:
        assert view.get_last_result() == ""

    def test_get_last_result_after_convert(self, view, mock_calc) -> None:
        view._selected_from_key = "m"
        view._to_var.set("km")
        view._value_var.set("1000")
        mock_calc.reset_mock()
        view._do_convert()
        assert view.get_last_result() == "1000 meter (m)"

    def test_convert_programmatic(self, view, mock_calc) -> None:
        view._selected_from_key = "m"
        view._to_var.set("km")
        view._value_var.set("1000")
        mock_calc.reset_mock()
        view.convert()
        mock_calc.convert.assert_called()


# ---------------------------------------------------------------------------
# Search filtering
# ---------------------------------------------------------------------------


class TestSearch:
    def test_filter_by_query(self, view) -> None:
        view._current_units = [
            ("meter (m)", "m"),
            ("kilometer (km)", "km"),
            ("foot (ft)", "ft"),
        ]
        view._refresh_listbox()
        view._search_var.set("kilo")
        assert view._unit_listbox.size() == 1
        assert "kilometer" in view._unit_listbox.get(0)

    def test_empty_search_shows_all(self, view) -> None:
        view._current_units = [("meter (m)", "m"), ("foot (ft)", "ft")]
        view._refresh_listbox()
        view._search_var.set("x")
        assert view._unit_listbox.size() == 0
        view._search_var.set("")
        assert view._unit_listbox.size() == 2


# ---------------------------------------------------------------------------
# Copy result
# ---------------------------------------------------------------------------


class TestCopyResult:
    def test_copy_result(self, view) -> None:
        view._result_var.set("42 km")
        view._copy_result()
        clipboard = view.clipboard_get()
        assert clipboard == "42 km"

    def test_copy_empty_noop(self, view) -> None:
        view._result_var.set("")
        view._copy_result()  # should not raise

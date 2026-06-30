"""Tests for ExpressionStatusBar widget."""

from __future__ import annotations

import tkinter as tk

from pyqalculate_gui.event_bus import MODE_CHANGED, EventBus
from pyqalculate_gui.expression_status import (
    ExpressionStatusBar,
    STATUS_TEXT_AUTOCALC,
    STATUS_TEXT_ERROR,
    STATUS_TEXT_FUNCTION,
    STATUS_TEXT_NONE,
    STATUS_TEXT_PARSED,
)
from pyqalculate_gui.theme import DARK, LIGHT
from pyqalculate_gui.i18n import _

# Single module-level root avoids Tcl flake from rapid Tk() creation/teardown.
_root: tk.Tk | None = None


def _get_root() -> tk.Tk:
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()
    return _root


def _bar(**kwargs: object) -> ExpressionStatusBar:
    """Create an ExpressionStatusBar inside the shared root."""
    return ExpressionStatusBar(_get_root(), **kwargs)  # type: ignore[arg-type]


def teardown_module() -> None:
    global _root
    if _root is not None:
        _root.destroy()
        _root = None


# --- Constructor ---


class TestConstructor:
    def test_default_theme(self) -> None:
        bar = _bar()
        assert bar._theme is LIGHT
        assert bar._event_bus is None

    def test_custom_theme(self) -> None:
        bar = _bar(theme=DARK)
        assert bar._theme is DARK

    def test_event_bus_subscribes_to_mode_changed(self) -> None:
        bus = EventBus()
        bar = _bar(event_bus=bus)
        assert MODE_CHANGED in bus._subscribers

    def test_initial_state(self) -> None:
        bar = _bar()
        assert bar._status_text_source == STATUS_TEXT_NONE
        assert bar._current_function is None
        assert bar._current_function_index == 0


# --- show_parsed_expression ---


class TestShowParsedExpression:
    def test_sets_text(self) -> None:
        bar = _bar()
        bar.show_parsed_expression("2 + 3")
        assert bar._left_label.cget("text") == "2 + 3"

    def test_sets_foreground_to_theme_fg(self) -> None:
        bar = _bar()
        bar.show_parsed_expression("x")
        assert bar._left_label.cget("fg") == LIGHT.fg

    def test_sets_status_source(self) -> None:
        bar = _bar()
        bar.show_parsed_expression("sin(pi)")
        assert bar._status_text_source == STATUS_TEXT_PARSED


# --- show_function_hint ---


class TestShowFunctionHint:
    def test_single_arg(self) -> None:
        bar = _bar()
        bar.show_function_hint("sin", 1, "x", "number")
        text = bar._left_label.cget("text")
        assert "sin(" in text
        assert "**x**" in text
        assert "number" in text

    def test_multi_arg_current_index(self) -> None:
        bar = _bar()
        bar.show_function_hint("integrate", 2, "from", "expression")
        text = bar._left_label.cget("text")
        assert "integrate(" in text
        assert "arg1" in text
        assert "**from**" in text

    def test_sets_status_source(self) -> None:
        bar = _bar()
        bar.show_function_hint("f", 1, "x", "number")
        assert bar._status_text_source == STATUS_TEXT_FUNCTION


# --- show_error ---


class TestShowError:
    def test_sets_error_text(self) -> None:
        bar = _bar()
        bar.show_error("Syntax error")
        assert bar._left_label.cget("text") == "Syntax error"

    def test_sets_error_color(self) -> None:
        bar = _bar()
        bar.show_error("fail")
        assert bar._left_label.cget("fg") == LIGHT.error_fg

    def test_sets_status_source(self) -> None:
        bar = _bar()
        bar.show_error("err")
        assert bar._status_text_source == STATUS_TEXT_ERROR


# --- show_warning ---


class TestShowWarning:
    def test_sets_warning_text(self) -> None:
        bar = _bar()
        bar.show_warning("Low precision")
        assert bar._left_label.cget("text") == "Low precision"

    def test_uses_warning_color(self) -> None:
        bar = _bar()
        bar.show_warning("warn")
        assert bar._left_label.cget("fg") == LIGHT.warning_fg


# --- show_autocalc_result ---


class TestShowAutocalcResult:
    def test_exact_result(self) -> None:
        bar = _bar()
        bar.show_autocalc_result("42", exact=True)
        assert bar._left_label.cget("text") == "= 42"

    def test_approx_result(self) -> None:
        bar = _bar()
        bar.show_autocalc_result("3.14159", exact=False)
        assert bar._left_label.cget("text") == "≈ 3.14159"

    def test_sets_status_source(self) -> None:
        bar = _bar()
        bar.show_autocalc_result("1")
        assert bar._status_text_source == STATUS_TEXT_AUTOCALC


# --- clear ---


class TestClear:
    def test_clears_text(self) -> None:
        bar = _bar()
        bar.show_error("oops")
        bar.clear()
        assert bar._left_label.cget("text") == ""

    def test_resets_status_source(self) -> None:
        bar = _bar()
        bar.show_error("oops")
        bar.clear()
        assert bar._status_text_source == STATUS_TEXT_NONE


# --- update_mode_indicators ---


class TestUpdateModeIndicators:
    def test_default_empty(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({})
        # Default angle is "degrees" → shows DEG
        # Default exact=False due to APPROXIMATE badge → shows Approximate
        indicator_text = bar._right_label.cget("text")
        assert indicator_text == _("Approximate") + "  " + _("DEG")

    def test_exact_mode(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"exact": True})
        text = bar._right_label.cget("text")
        assert "EXACT" in text
        # Default angle is "degrees" → DEG also present
        assert "DEG" in text

    def test_rpn_mode(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"rpn": True})
        assert "RPN" in bar._right_label.cget("text")

    def test_chain_mode(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"chain": True})
        assert "CHN" in bar._right_label.cget("text")

    def test_hex_base(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"base": 16})
        assert "HEX" in bar._right_label.cget("text")

    def test_oct_base(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"base": 8})
        assert "OCT" in bar._right_label.cget("text")

    def test_bin_base(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"base": 2})
        assert "BIN" in bar._right_label.cget("text")

    def test_duo_base(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"base": 12})
        assert "DUO" in bar._right_label.cget("text")

    def test_decimal_base_hidden(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"base": 10})
        # Base 10 is hidden, but default angle "degrees" shows DEG
        # Default exact=False due to APPROXIMATE badge → shows Approximate
        indicator_text = bar._right_label.cget("text")
        assert indicator_text == _("Approximate") + "  " + _("DEG")

    def test_custom_base(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"base": 3})
        assert "3" in bar._right_label.cget("text")

    def test_angle_degrees(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"angle": "degrees"})
        assert "DEG" in bar._right_label.cget("text")

    def test_angle_radians(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"angle": "radians"})
        assert "RAD" in bar._right_label.cget("text")

    def test_angle_gradians(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"angle": "gradians"})
        assert "GRA" in bar._right_label.cget("text")

    def test_disabled_functions(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"functions_enabled": False})
        assert "FUNC" in bar._right_label.cget("text")

    def test_disabled_units(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"units_enabled": False})
        assert "UNIT" in bar._right_label.cget("text")

    def test_disabled_variables(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({"variables_enabled": False})
        assert "VAR" in bar._right_label.cget("text")

    def test_multiple_modes_combined(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({
            "exact": True,
            "rpn": True,
            "base": 16,
            "angle": "radians",
        })
        text = bar._right_label.cget("text")
        assert "EXACT" in text
        assert "RPN" in text
        assert "HEX" in text
        assert "RAD" in text

    def test_disabled_features_combined(self) -> None:
        bar = _bar()
        bar.update_mode_indicators({
            "functions_enabled": False,
            "units_enabled": False,
            "variables_enabled": False,
        })
        text = bar._right_label.cget("text")
        assert "FUNC" in text
        assert "UNIT" in text
        assert "VAR" in text


# --- EventBus integration ---


class TestEventBusIntegration:
    def test_mode_changed_updates_indicators(self) -> None:
        bus = EventBus()
        bar = _bar(event_bus=bus)
        bus.emit(MODE_CHANGED, {"exact": True, "base": 16})
        text = bar._right_label.cget("text")
        assert "EXACT" in text
        assert "HEX" in text

    def test_mode_changed_empty_dict(self) -> None:
        bus = EventBus()
        bar = _bar(event_bus=bus)
        bus.emit(MODE_CHANGED, {})
        # Empty dict → mode_info.get("exact", False) is False → shows Approximate
        indicator_text = bar._right_label.cget("text")
        assert indicator_text == _("Approximate") + "  " + _("DEG")

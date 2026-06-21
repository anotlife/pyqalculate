"""Integration tests for the PyQalculate GUI v3 rebuild.

Covers:
- App instantiation and widget tree
- Calculation flow (expression -> result)
- answer(N) resolution from history
- Event bus wiring between components
- Theme loading and application
"""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from pyqalculate_gui.app import App
from pyqalculate_gui.calculator_service import CalculatorService, CalculationResult
from pyqalculate_gui.event_bus import (
    CLEAR_ALL,
    EXPRESSION_SUBMITTED,
    HISTORY_RECALLED,
    RESULT_DISPLAYED,
    EventBus,
)
from pyqalculate_gui.history_view import HistoryView
from pyqalculate_gui.result_view import ResultView
from pyqalculate_gui.state import AppState
from pyqalculate_gui.theme import DARK, LIGHT, Theme, get_theme


HAS_DISPLAY = bool(
    os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or os.name == "nt"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def root():
    """Create a withdrawn Tk root for headless testing."""
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def bus():
    """Create a fresh EventBus."""
    return EventBus()


@pytest.fixture
def service():
    """Create a CalculatorService."""
    return CalculatorService()


@pytest.fixture
def app():
    """Create an App instance with withdrawn root."""
    a = App()
    a._root.withdraw()
    yield a
    a._root.destroy()


# ---------------------------------------------------------------------------
# 1. App instantiation
# ---------------------------------------------------------------------------


class TestAppInstantiation:
    """Verify App creates the expected widget tree."""

    def test_root_exists(self, app: App) -> None:
        """App._root is a valid Tk window."""
        assert app._root is not None
        assert isinstance(app._root, tk.Tk)

    def test_title(self, app: App) -> None:
        """Window title is 'PyQalculate'."""
        assert app._root.title() == "PyQalculate"

    def test_state_initialized(self, app: App) -> None:
        """AppState is created with defaults."""
        assert isinstance(app._state, AppState)
        assert app._state.expression == ""
        assert app._state.exact_mode is True

    def test_event_bus_initialized(self, app: App) -> None:
        """EventBus is created."""
        assert isinstance(app._event_bus, EventBus)

    def test_calculator_service_initialized(self, app: App) -> None:
        """CalculatorService is created."""
        assert isinstance(app._calculator, CalculatorService)

    def test_theme_defaults_to_light(self, app: App) -> None:
        """Default theme is LIGHT."""
        assert app._theme is LIGHT

    def test_widgets_created(self, app: App) -> None:
        """All expected widgets are created."""
        assert hasattr(app, "_expr_edit")
        assert hasattr(app, "_keypad")
        assert hasattr(app, "_result_view")
        assert hasattr(app, "_history_view")
        assert hasattr(app, "_status_bar")
        assert hasattr(app, "_menu_bar")

    def test_status_bar_populated(self, app: App) -> None:
        """Status bar shows calculator statistics."""
        stats_text = app._status_bar._stats_var.get()
        assert "Functions:" in stats_text
        assert "Units:" in stats_text
        assert "Variables:" in stats_text


# ---------------------------------------------------------------------------
# 2. Calculation flow
# ---------------------------------------------------------------------------


class TestCalculationFlow:
    """Verify expression -> result pipeline."""

    def test_simple_calculation(self, app: App) -> None:
        """2 + 2 produces a result."""
        app._on_expression_submitted("2 + 2")
        result = app._result_view.get_last_result()
        assert result != ""
        assert "4" in result

    def test_expression_cleared_after_submit(self, app: App) -> None:
        """Expression edit is cleared after submission."""
        app._on_expression_submitted("1 + 1")
        expr = app._expr_edit.get_expression()
        assert expr == ""

    def test_history_records_expression(self, app: App) -> None:
        """History captures the expression."""
        app._on_expression_submitted("3 * 5")
        assert len(app._history_view._entries) >= 2  # expression + result

    def test_history_records_result(self, app: App) -> None:
        """History captures the result."""
        app._on_expression_submitted("10 / 2")
        results = [e for e in app._history_view._entries if e.entry_type == "result"]
        assert len(results) >= 1
        assert "5" in results[-1].result

    def test_error_handling(self, app: App) -> None:
        """Invalid expressions show errors gracefully."""
        app._on_expression_submitted("1/0")
        # Should not raise — error is displayed in result view
        entries = app._history_view._entries
        assert len(entries) >= 1

    def test_multiple_calculations(self, app: App) -> None:
        """Multiple sequential calculations work."""
        app._on_expression_submitted("1 + 1")
        app._on_expression_submitted("2 + 2")
        app._on_expression_submitted("3 + 3")
        results = [e for e in app._history_view._entries if e.entry_type == "result"]
        assert len(results) >= 3


# ---------------------------------------------------------------------------
# 3. answer(N) resolution
# ---------------------------------------------------------------------------


class TestAnswerResolution:
    """Verify answer(N) references to past results."""

    def test_answer_1_returns_last_result(self, app: App) -> None:
        """answer(1) resolves to the most recent result."""
        app._on_expression_submitted("42")
        resolved = app._resolve_answer_refs("answer(1)")
        assert "42" in resolved

    def test_answer_2_returns_second_last(self, app: App) -> None:
        """answer(2) resolves to the second most recent result."""
        app._on_expression_submitted("10")
        app._on_expression_submitted("20")
        resolved = app._resolve_answer_refs("answer(2)")
        assert "10" in resolved

    def test_answer_unresolved_stays_literal(self, app: App) -> None:
        """answer(N) with N > history length stays as-is."""
        resolved = app._resolve_answer_refs("answer(99)")
        assert "answer(99)" in resolved

    def test_answer_in_expression(self, app: App) -> None:
        """answer(1) can be used in a new calculation."""
        app._on_expression_submitted("7")
        app._on_expression_submitted("answer(1) * 2")
        results = [e for e in app._history_view._entries if e.entry_type == "result"]
        assert len(results) >= 2
        assert "14" in results[-1].result


# ---------------------------------------------------------------------------
# 4. Event bus wiring
# ---------------------------------------------------------------------------


class TestEventBusWiring:
    """Verify events propagate correctly between components."""

    def test_expression_submitted_reaches_result_view(self, root: tk.Tk, bus: EventBus) -> None:
        """EXPRESSION_SUBMITTED triggers result view echo."""
        result_view = ResultView(root, theme=LIGHT, event_bus=bus)
        result_view.pack()

        bus.emit(EXPRESSION_SUBMITTED, "test_expr")
        # Result view should have content (the expression echo)
        content = result_view._text.get("1.0", tk.END).strip()
        assert "test_expr" in content

    def test_result_displayed_event(self, root: tk.Tk, bus: EventBus) -> None:
        """RESULT_DISPLAYED event fires after show_result."""
        received: list[tuple[str, bool]] = []
        bus.subscribe(RESULT_DISPLAYED, lambda expr, r, e: received.append((r, e)))

        result_view = ResultView(root, theme=LIGHT, event_bus=bus)
        result_view.pack()
        result_view.show_result("2+2", "4", exact=True)

        assert len(received) == 1
        assert received[0] == ("4", True)

    def test_history_recalled_event(self, root: tk.Tk, bus: EventBus) -> None:
        """HISTORY_RECALLED event propagates."""
        received: list[str] = []
        bus.subscribe(HISTORY_RECALLED, lambda expr: received.append(expr))

        history = HistoryView(root, theme=LIGHT, event_bus=bus)
        history.pack()
        history.add_expression("old_expr")
        history.add_result("42")

        # Simulate double-click recall
        history._listbox.selection_set(0)
        history._on_recall()

        assert "old_expr" in received

    def test_clear_all_wires_to_components(self, app: App) -> None:
        """CLEAR_ALL resets expression, result, and history."""
        app._on_expression_submitted("99")
        app._on_clear_all()

        assert app._expr_edit.get_expression() == ""
        assert app._result_view.get_last_result() == ""
        assert len(app._history_view._entries) == 0


# ---------------------------------------------------------------------------
# 5. Theme loading
# ---------------------------------------------------------------------------


class TestThemeLoading:
    """Verify theme system works correctly."""

    def test_light_theme_exists(self) -> None:
        """LIGHT theme is a valid Theme."""
        assert isinstance(LIGHT, Theme)
        assert LIGHT.bg == "#ffffff"

    def test_dark_theme_exists(self) -> None:
        """DARK theme is a valid Theme."""
        assert isinstance(DARK, Theme)
        assert DARK.bg == "#1e1e1e"

    def test_get_theme_light(self) -> None:
        """get_theme('light') returns LIGHT."""
        assert get_theme("light") is LIGHT

    def test_get_theme_dark(self) -> None:
        """get_theme('dark') returns DARK."""
        assert get_theme("dark") is DARK

    def test_get_theme_unknown_defaults_to_light(self) -> None:
        """Unknown theme name defaults to LIGHT."""
        assert get_theme("nonexistent") is LIGHT

    def test_theme_case_insensitive(self) -> None:
        """Theme lookup is case-insensitive."""
        assert get_theme("LIGHT") is LIGHT
        assert get_theme("Dark") is DARK

    def test_theme_is_frozen(self) -> None:
        """Theme dataclass is immutable."""
        with pytest.raises(AttributeError):
            LIGHT.bg = "#000000"  # type: ignore[misc]

    def test_button_styles_exist(self) -> None:
        """All keypad button styles are defined."""
        assert LIGHT.keypad_digit is not None
        assert LIGHT.keypad_op is not None
        assert LIGHT.keypad_func is not None
        assert LIGHT.keypad_equals is not None


# ---------------------------------------------------------------------------
# 6. CalculatorService
# ---------------------------------------------------------------------------


class TestCalculatorServiceIntegration:
    """Verify CalculatorService works through the GUI pipeline."""

    def test_calculate_basic(self, service: CalculatorService) -> None:
        """Basic arithmetic via CalculatorService."""
        result = service.calculate("2 + 3")
        assert result.result == "5"
        assert result.error is None

    def test_calculate_returns_typed_result(self, service: CalculatorService) -> None:
        """Result is a CalculationResult dataclass."""
        result = service.calculate("10 * 10")
        assert isinstance(result, CalculationResult)
        assert result.expression == "10 * 10"
        assert result.result == "100"

    def test_calculate_error_handling(self, service: CalculatorService) -> None:
        """Division by zero returns an error string, not an exception."""
        result = service.calculate("1/0")
        # Should not raise; result or error should be set
        assert result is not None

    def test_unit_conversion(self, service: CalculatorService) -> None:
        """Unit conversion through service."""
        result = service.convert("5", "ft", "m")
        assert "1.52" in result

    def test_get_functions_non_empty(self, service: CalculatorService) -> None:
        """Functions list is populated."""
        funcs = service.get_functions()
        assert len(funcs) > 100
        assert "sin" in funcs

    def test_get_units_non_empty(self, service: CalculatorService) -> None:
        """Units list is populated."""
        units = service.get_units()
        assert len(units) > 100

    def test_get_variables_non_empty(self, service: CalculatorService) -> None:
        """Variables list is populated."""
        variables = service.get_variables()
        assert len(variables) > 0

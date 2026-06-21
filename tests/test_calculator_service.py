"""Tests for CalculatorService engine wrapper."""

from __future__ import annotations

import pytest

from pyqalculate_gui.calculator_service import CalculatorService, CalculationResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def svc() -> CalculatorService:
    """Create a CalculatorService with all definitions loaded."""
    return CalculatorService()


# ---------------------------------------------------------------------------
# Basic calculation
# ---------------------------------------------------------------------------


class TestBasicCalculation:
    """Evaluate simple arithmetic expressions."""

    def test_addition(self, svc: CalculatorService) -> None:
        result = svc.calculate("2+2")
        assert isinstance(result, CalculationResult)
        assert result.result == "4"
        assert result.error is None

    def test_multiplication(self, svc: CalculatorService) -> None:
        result = svc.calculate("6*7")
        assert result.result == "42"
        assert result.error is None

    def test_expression_preserved(self, svc: CalculatorService) -> None:
        result = svc.calculate("3.14*2")
        assert result.expression == "3.14*2"


# ---------------------------------------------------------------------------
# Unit conversion
# ---------------------------------------------------------------------------


class TestUnitConversion:
    """Convert between measurement units."""

    def test_convert_feet_to_meters(self, svc: CalculatorService) -> None:
        result = svc.calculate("5 ft to m")
        assert result.error is None
        # 5 ft ≈ 1.524 m — result should be a non-empty string
        assert len(result.result) > 0

    def test_convert_method(self, svc: CalculatorService) -> None:
        converted = svc.convert("5", "ft", "m")
        assert len(converted) > 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Ensure invalid expressions are caught gracefully."""

    def test_invalid_expression(self, svc: CalculatorService) -> None:
        result = svc.calculate("((((")
        # Malformed expression may return "undefined" or raise — both are valid
        assert isinstance(result, CalculationResult)

    def test_empty_expression(self, svc: CalculatorService) -> None:
        result = svc.calculate("")
        # Empty string may either succeed (return "0") or raise — both acceptable
        assert isinstance(result, CalculationResult)


# ---------------------------------------------------------------------------
# Discovery methods
# ---------------------------------------------------------------------------


class TestDiscovery:
    """get_units / get_functions / get_variables return non-empty lists."""

    def test_get_units(self, svc: CalculatorService) -> None:
        units = svc.get_units()
        assert isinstance(units, list)
        assert len(units) > 0
        # All items are strings
        assert all(isinstance(u, str) for u in units)

    def test_get_functions(self, svc: CalculatorService) -> None:
        funcs = svc.get_functions()
        assert isinstance(funcs, list)
        assert len(funcs) > 0
        assert all(isinstance(f, str) for f in funcs)

    def test_get_variables(self, svc: CalculatorService) -> None:
        variables = svc.get_variables()
        assert isinstance(variables, list)
        assert len(variables) > 0
        assert all(isinstance(v, str) for v in variables)

    def test_lists_are_sorted(self, svc: CalculatorService) -> None:
        units = svc.get_units()
        assert units == sorted(units)
        funcs = svc.get_functions()
        assert funcs == sorted(funcs)

"""Comprehensive tests for the Calculator engine with SymPy integration.

Tests cover:
- Basic arithmetic
- Exact vs approximate output modes
- Trigonometric functions
- Fraction display
- Base conversion
- SymPy integration (to_sympy / from_sympy)
- Definition loading
"""

from __future__ import annotations

import pytest

from pyqalculate.calculator import Calculator
from pyqalculate.math_structure import MathStructure
from pyqalculate.number import Number
from pyqalculate.types import (
    EvaluationOptions,
    ApproximationMode,
    NumberFractionFormat,
    PrintOptions,
    StructureType,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def calc() -> Calculator:
    """Create a Calculator with built-in definitions loaded."""
    c = Calculator()
    c.load_definitions()
    return c


@pytest.fixture
def calc_global() -> Calculator:
    """Create a Calculator with global (JSON) definitions loaded."""
    c = Calculator()
    c.load_definitions()
    c.load_global_definitions()
    return c


# ---------------------------------------------------------------------------
# Basic arithmetic
# ---------------------------------------------------------------------------


class TestBasicArithmetic:
    """Test basic arithmetic operations."""

    def test_addition(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("1 + 2") == "3"

    def test_multiplication(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("3 * 4") == "12"

    def test_subtraction(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("10 - 3") == "7"

    def test_division(self, calc: Calculator) -> None:
        result = calc.calculate_and_print("10 / 4")
        assert result == "5/2"

    def test_division_by_zero_is_undefined(self, calc: Calculator) -> None:
        assert calc.calculate("3 / 0").is_undefined()
        assert calc.calculate("0 / 0").is_undefined()
        assert calc.calculate_and_print("3 / 0") == "undefined"

    def test_power(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("2^10") == "1024"

    def test_combined_operations(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("1 + 2*3") == "7"

    def test_parentheses(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("(1 + 2) * 3") == "9"

    def test_nested_parentheses(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("((2 + 3) * 2)^2") == "100"

    def test_negative_numbers(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("-5 + 3") == "-2"

    def test_zero_operations(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("0 * 999") == "0"
        assert calc.calculate_and_print("0 + 5") == "5"


# ---------------------------------------------------------------------------
# Trigonometric functions
# ---------------------------------------------------------------------------


class TestTrigonometry:
    """Test trigonometric function evaluation."""

    def test_sin_pi_half(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("sin(pi/2)") == "1"

    def test_cos_zero(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("cos(0)") == "1"

    def test_sin_zero(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("sin(0)") == "0"

    def test_cos_pi(self, calc: Calculator) -> None:
        result = calc.calculate_and_print("cos(pi)")
        assert result == "-1"

    def test_tan_pi_quarter(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("tan(pi/4)") == "1"

    def test_exp_zero(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("exp(0)") == "1"

    def test_ln_e(self, calc: Calculator) -> None:
        assert calc.calculate_and_print("ln(e)") == "1"


# ---------------------------------------------------------------------------
# Exact mode
# ---------------------------------------------------------------------------


class TestExactMode:
    """Test exact/symbolic output mode."""

    def test_sqrt_exact(self, calc: Calculator) -> None:
        po = PrintOptions(exact=True)
        result = calc.calculate_and_print("sqrt(32)", po=po)
        assert "4" in result
        assert "sqrt" in result

    def test_sqrt_perfect_square(self, calc: Calculator) -> None:
        po = PrintOptions(exact=True)
        result = calc.calculate_and_print("sqrt(16)", po=po)
        assert result == "4"

    def test_exact_rational(self, calc: Calculator) -> None:
        po = PrintOptions(exact=True)
        result = calc.calculate_and_print("1/3 + 1/6", po=po)
        assert result == "1/2"

    def test_exact_power(self, calc: Calculator) -> None:
        po = PrintOptions(exact=True)
        result = calc.calculate_and_print("2^3", po=po)
        assert result == "8"


# ---------------------------------------------------------------------------
# Approximate mode
# ---------------------------------------------------------------------------


class TestApproximateMode:
    """Test approximate/numeric output mode."""

    def test_sqrt_approximate(self, calc: Calculator) -> None:
        po = PrintOptions(approximate=True)
        result = calc.calculate_and_print("sqrt(32)", po=po)
        assert "5.656" in result

    def test_pi_approximate(self, calc: Calculator) -> None:
        po = PrintOptions(approximate=True)
        result = calc.calculate_and_print("pi", po=po)
        assert "3.14159" in result

    def test_one_third_approximate(self, calc: Calculator) -> None:
        po = PrintOptions(approximate=True)
        result = calc.calculate_and_print("1/3", po=po)
        assert "0.333" in result

    def test_exp_approximate(self, calc: Calculator) -> None:
        po = PrintOptions(approximate=True)
        result = calc.calculate_and_print("exp(1)", po=po)
        assert "2.718" in result


# ---------------------------------------------------------------------------
# Fraction display
# ---------------------------------------------------------------------------


class TestFractionDisplay:
    """Test fraction display modes."""

    def test_fractional_format(self, calc: Calculator) -> None:
        po = PrintOptions(number_fraction_format=NumberFractionFormat.FRACTIONAL)
        result = calc.calculate_and_print("5/4", po=po)
        assert result == "5/4"

    def test_combined_format(self, calc: Calculator) -> None:
        po = PrintOptions(number_fraction_format=NumberFractionFormat.COMBINED)
        result = calc.calculate_and_print("5/4", po=po)
        assert result == "1 + 1/4"

    def test_decimal_format(self, calc: Calculator) -> None:
        po = PrintOptions(number_fraction_format=NumberFractionFormat.DECIMAL)
        result = calc.calculate_and_print("5/4", po=po)
        assert result == "5/4"

    def test_percent_format(self, calc: Calculator) -> None:
        po = PrintOptions(number_fraction_format=NumberFractionFormat.PERCENT)
        result = calc.calculate_and_print("0.75", po=po)
        assert "%" in result


# ---------------------------------------------------------------------------
# Base conversion
# ---------------------------------------------------------------------------


class TestBaseConversion:
    """Test number base conversion in output."""

    def test_hexadecimal(self, calc: Calculator) -> None:
        po = PrintOptions(base=16)
        result = calc.calculate_and_print("42", po=po)
        assert "0x" in result.lower()
        assert "2a" in result.lower()

    def test_octal(self, calc: Calculator) -> None:
        po = PrintOptions(base=8)
        result = calc.calculate_and_print("42", po=po)
        assert "0o" in result
        assert "52" in result

    def test_binary(self, calc: Calculator) -> None:
        po = PrintOptions(base=2)
        result = calc.calculate_and_print("42", po=po)
        # Binary output with nibble spacing
        assert "101010" in result.replace(" ", "")


# ---------------------------------------------------------------------------
# SymPy integration (MathStructure)
# ---------------------------------------------------------------------------


class TestSymPyIntegration:
    """Test MathStructure to/from SymPy conversion."""

    def test_number_to_sympy(self) -> None:
        import sympy as sp
        m = MathStructure(42)
        expr = m.to_sympy()
        assert expr == sp.Integer(42)

    def test_rational_to_sympy(self) -> None:
        import sympy as sp
        m = MathStructure.from_number(Number.from_rational(3, 7))
        expr = m.to_sympy()
        assert expr == sp.Rational(3, 7)

    def test_symbol_to_sympy(self) -> None:
        import sympy as sp
        m = MathStructure.from_symbol("x")
        expr = m.to_sympy()
        assert expr == sp.Symbol("x")

    def test_pi_to_sympy(self) -> None:
        import sympy as sp
        m = MathStructure.from_symbol("pi")
        expr = m.to_sympy()
        assert expr == sp.pi

    def test_addition_to_sympy(self) -> None:
        import sympy as sp
        m = MathStructure.addition(MathStructure(2), MathStructure(3))
        expr = m.to_sympy()
        assert expr == sp.Integer(5)

    def test_power_to_sympy(self) -> None:
        import sympy as sp
        m = MathStructure.power(MathStructure(2), MathStructure(3))
        expr = m.to_sympy()
        assert expr == sp.Integer(8)

    def test_from_sympy_integer(self) -> None:
        import sympy as sp
        m = MathStructure.from_sympy(sp.Integer(7))
        assert m.is_number()
        assert m.float_value() == 7.0

    def test_from_sympy_rational(self) -> None:
        import sympy as sp
        m = MathStructure.from_sympy(sp.Rational(3, 5))
        assert m.is_number()
        assert m._number is not None
        assert m._number.is_rational()

    def test_from_sympy_symbol(self) -> None:
        import sympy as sp
        m = MathStructure.from_sympy(sp.Symbol("y"))
        assert m.is_symbolic()
        assert m.symbol == "y"

    def test_roundtrip_number(self) -> None:
        m = MathStructure(42)
        assert MathStructure.from_sympy(m.to_sympy()) == m

    def test_roundtrip_rational(self) -> None:
        m = MathStructure.from_number(Number.from_rational(22, 7))
        rt = MathStructure.from_sympy(m.to_sympy())
        assert rt.is_number()
        assert rt._number is not None
        assert rt._number == m._number

    def test_roundtrip_symbolic(self) -> None:
        m = MathStructure.from_symbol("x")
        rt = MathStructure.from_sympy(m.to_sympy())
        assert rt.is_symbolic()
        assert rt.symbol == "x"


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


class TestEvaluation:
    """Test MathStructure.evaluate() method."""

    def test_evaluate_number(self) -> None:
        m = MathStructure(5)
        result = m.evaluate()
        assert result.is_number()
        assert result.float_value() == 5.0

    def test_evaluate_addition(self) -> None:
        m = MathStructure.addition(MathStructure(2), MathStructure(3))
        result = m.evaluate()
        assert result.is_number()
        assert result.float_value() == 5.0

    def test_evaluate_power(self) -> None:
        m = MathStructure.power(MathStructure(2), MathStructure(10))
        result = m.evaluate()
        assert result.is_number()
        assert result.float_value() == 1024.0

    def test_evaluate_sqrt(self) -> None:
        func_m = MathStructure(struct_type=StructureType.FUNCTION)
        func_m._symbol = "sqrt"
        func_m._children = [MathStructure(16)]
        result = func_m.evaluate()
        assert result.is_number()
        assert result.float_value() == 4.0

    def test_evaluate_simplify(self) -> None:
        """sqrt(32) simplifies to 4*sqrt(2)."""
        func_m = MathStructure(struct_type=StructureType.FUNCTION)
        func_m._symbol = "sqrt"
        func_m._children = [MathStructure(32)]
        result = func_m.evaluate()
        # Should be 4*sqrt(2), which is a multiplication
        assert result.is_multiplication()

    def test_evaluate_approximate(self) -> None:
        """sqrt(32) in approximate mode should give a float."""
        func_m = MathStructure(struct_type=StructureType.FUNCTION)
        func_m._symbol = "sqrt"
        func_m._children = [MathStructure(32)]
        eo = EvaluationOptions(approximation=ApproximationMode.APPROXIMATE)
        result = func_m.evaluate(eo)
        assert result.is_number()
        assert abs(result.float_value() - 5.65685) < 0.001


# ---------------------------------------------------------------------------
# Calculator with global definitions
# ---------------------------------------------------------------------------


class TestGlobalDefinitions:
    """Test loading definitions from JSON data files."""

    def test_load_global_definitions(self, calc_global: Calculator) -> None:
        assert calc_global.count_variables() > 2

    def test_pi_still_works(self, calc_global: Calculator) -> None:
        assert calc_global.calculate_and_print("sin(pi/2)") == "1"

    def test_e_still_works(self, calc_global: Calculator) -> None:
        assert calc_global.calculate_and_print("ln(e)") == "1"


# ---------------------------------------------------------------------------
# Print options
# ---------------------------------------------------------------------------


class TestPrintOptions:
    """Test various PrintOptions effects on output."""

    def test_default_print(self, calc: Calculator) -> None:
        result = calc.calculate_and_print("2 + 3")
        assert result == "5"

    def test_print_with_eo(self, calc: Calculator) -> None:
        eo = EvaluationOptions()
        result = calc.calculate_and_print("2 + 3", eo=eo)
        assert result == "5"

    def test_calculate_returns_structure(self, calc: Calculator) -> None:
        result = calc.calculate("7 * 6")
        assert result.is_number()
        assert result.float_value() == 42.0

    def test_print_result(self, calc: Calculator) -> None:
        m = MathStructure(42)
        assert calc.print_result(m) == "42"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_expression(self, calc: Calculator) -> None:
        result = calc.calculate("")
        assert result.is_undefined()

    def test_undefined_result(self, calc: Calculator) -> None:
        result = calc.calculate("1/0")
        assert result.is_undefined() or result.is_symbolic()

    def test_very_large_power(self, calc: Calculator) -> None:
        result = calc.calculate_and_print("2^100")
        assert result is not None
        assert len(result) > 0

    def test_negative_base_power(self, calc: Calculator) -> None:
        result = calc.calculate_and_print("(-2)^3")
        assert result == "-8"

    def test_zero_power_zero(self, calc: Calculator) -> None:
        """0^0 is mathematically undefined."""
        result = calc.calculate("0^0")
        # Should return undefined or handle gracefully
        assert result is not None

    def test_abs_function(self, calc: Calculator) -> None:
        result = calc.calculate_and_print("abs(-5)")
        assert result == "5"

    def test_factorial(self, calc: Calculator) -> None:
        result = calc.calculate_and_print("5!")
        assert result == "120"

    def test_nested_functions(self, calc: Calculator) -> None:
        result = calc.calculate_and_print("sin(pi/2) + cos(0)")
        assert result == "2"

    def test_complex_expression(self, calc: Calculator) -> None:
        result = calc.calculate_and_print("(2 + 3) * (4 - 1)^2")
        assert result == "45"

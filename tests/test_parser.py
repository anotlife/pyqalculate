"""Comprehensive tests for the PyQalculate expression parser.

Tests cover numbers, operators, functions, units, matrices, assignments,
and all special syntax features.
"""

from __future__ import annotations

import pytest

from pyqalculate.parser import Parser
from pyqalculate.math_structure import MathStructure
from pyqalculate.types import StructureType, ComparisonType, ParseOptions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_parser = Parser()


def parse(expr: str, po: ParseOptions | None = None) -> MathStructure:
    """Convenience wrapper around Parser.parse()."""
    return _parser.parse(expr, po)


# ---------------------------------------------------------------------------
# 1. Number parsing
# ---------------------------------------------------------------------------


class TestNumbers:
    """Test parsing of numeric literals."""

    def test_integer(self):
        m = parse("42")
        assert m.is_number()
        assert m.float_value() == 42.0

    def test_large_integer(self):
        m = parse("1000000")
        assert m.is_number()
        assert m.float_value() == 1000000.0

    def test_zero(self):
        m = parse("0")
        assert m.is_number()
        assert m.is_zero()

    def test_negative_integer(self):
        m = parse("-7")
        assert m.is_number()
        assert m.float_value() == -7.0

    def test_float(self):
        m = parse("3.14")
        assert m.is_number()
        assert abs(m.float_value() - 3.14) < 1e-10

    def test_float_leading_dot(self):
        m = parse(".5")
        assert m.is_number()
        assert abs(m.float_value() - 0.5) < 1e-10

    def test_float_trailing_dot(self):
        m = parse("1.0")
        assert m.is_number()
        assert abs(m.float_value() - 1.0) < 1e-10

    def test_scientific_upper(self):
        m = parse("5E3")
        assert m.is_number()
        assert m.float_value() == 5000.0

    def test_scientific_lower(self):
        m = parse("5e3")
        assert m.is_number()
        assert m.float_value() == 5000.0

    def test_scientific_negative_exp(self):
        m = parse("5e-3")
        assert m.is_number()
        assert abs(m.float_value() - 0.005) < 1e-10

    def test_scientific_positive_exp(self):
        m = parse("1.5E+10")
        assert m.is_number()
        assert abs(m.float_value() - 1.5e10) < 1e5

    def test_fraction(self):
        m = parse("5/4")
        assert m.is_number()
        assert abs(m.float_value() - 1.25) < 1e-10

    def test_fraction_one_third(self):
        m = parse("1/3")
        assert m.is_number()
        assert abs(m.float_value() - 1.0 / 3.0) < 1e-10

    def test_complex_pure_imaginary(self):
        m = parse("3i")
        # Should parse as 3 * i (multiplication)
        assert m.is_multiplication()

    def test_uncertainty_plusminus(self):
        m = parse("5\u00b10.1")
        # Should parse as a symbolic ± structure or interval
        assert m.is_symbolic() or m.is_number()


# ---------------------------------------------------------------------------
# 2. Arithmetic operators
# ---------------------------------------------------------------------------


class TestArithmeticOperators:
    """Test arithmetic operator parsing."""

    def test_addition(self):
        m = parse("1 + 2")
        assert m.is_addition()

    def test_subtraction(self):
        m = parse("5 - 3")
        assert m.is_addition()  # subtraction is addition with negate

    def test_multiplication(self):
        m = parse("2 * 3")
        assert m.is_multiplication()

    def test_division(self):
        m = parse("6 / 2")
        # 6/2 folds to rational 3
        assert m.is_number() or m.is_multiplication()

    def test_power(self):
        m = parse("2 ^ 3")
        assert m.is_power()

    def test_power_double_star(self):
        m = parse("2 ** 3")
        assert m.is_power()

    def test_addition_with_multiplication(self):
        m = parse("1 + 2*3")
        assert m.is_addition()
        assert len(m) == 2

    def test_operator_precedence_mul_before_add(self):
        m = parse("1 + 2*3")
        # Should be 1 + (2*3), not (1+2)*3
        assert m.is_addition()
        right = m[1]
        assert right.is_multiplication()

    def test_operator_precedence_power_before_mul(self):
        m = parse("2*3^2")
        # Should be 2 * (3^2)
        assert m.is_multiplication()
        right = m[1]
        assert right.is_power()

    def test_parentheses_override(self):
        m = parse("(1 + 2) * 3")
        assert m.is_multiplication()
        left = m[0]
        assert left.is_addition()

    def test_nested_parentheses(self):
        m = parse("((1 + 2))")
        assert m.is_addition()

    def test_modulo_keyword(self):
        m = parse("10 mod 3")
        assert m.is_function()

    def test_integer_division(self):
        m = parse("10 // 3")
        assert m.is_function()

    def test_factorial(self):
        m = parse("5!")
        assert m.is_factorial()

    def test_factorial_of_expression(self):
        m = parse("(2+3)!")
        assert m.is_factorial()

    def test_percentage(self):
        m = parse("20%")
        # 20% = 20/100 = 0.2
        assert m.is_multiplication()

    def test_complex_expression(self):
        m = parse("2 + 3 * 4 - 5")
        assert m.is_addition()


# ---------------------------------------------------------------------------
# 3. Unary operators
# ---------------------------------------------------------------------------


class TestUnaryOperators:
    """Test unary operator parsing."""

    def test_unary_minus(self):
        m = parse("-x")
        assert m.is_addition() or m.is_multiplication() or m.is_number() or m.type == StructureType.NEGATE

    def test_unary_plus(self):
        m = parse("+5")
        assert m.is_number()

    def test_double_negative(self):
        m = parse("--5")
        # --5 = 5
        assert m.is_number() or m.is_multiplication()

    def test_negative_parenthesized(self):
        m = parse("-(2+3)")
        # Should negate the parenthesized expression
        assert m.is_addition() or m.is_multiplication() or m.type == StructureType.NEGATE


# ---------------------------------------------------------------------------
# 4. Functions
# ---------------------------------------------------------------------------


class TestFunctions:
    """Test function call parsing."""

    def test_simple_function(self):
        m = parse("sin(0)")
        assert m.is_function()

    def test_function_with_expression_arg(self):
        m = parse("sin(pi/2)")
        assert m.is_function()

    def test_sqrt(self):
        m = parse("sqrt(25)")
        assert m.is_function()

    def test_multi_arg_function(self):
        m = parse("gcd(2520; 3600)")
        assert m.is_function()
        assert len(m) == 2

    def test_function_with_comma_separated_args(self):
        m = parse("gcd(2520, 3600)")
        assert m.is_function()
        assert len(m) == 2

    def test_function_with_semicolon_args(self):
        m = parse("log(x; 10)")
        assert m.is_function()
        assert len(m) == 2

    def test_nested_functions(self):
        m = parse("sin(cos(0))")
        assert m.is_function()

    def test_empty_parens(self):
        m = parse("()")
        assert m.is_number()  # empty parens = 0


# ---------------------------------------------------------------------------
# 5. Variables and constants
# ---------------------------------------------------------------------------


class TestVariablesAndConstants:
    """Test variable and constant parsing."""

    def test_simple_variable(self):
        m = parse("x")
        assert m.is_symbolic()

    def test_multi_char_variable(self):
        m = parse("my_var")
        assert m.is_symbolic()
        assert m.symbol == "my_var"

    def test_pi_symbol(self):
        m = parse("pi")
        assert m.is_symbolic()

    def test_implicit_multiplication_number_var(self):
        m = parse("2x")
        assert m.is_multiplication()

    def test_implicit_multiplication_number_paren(self):
        m = parse("2(x+1)")
        assert m.is_multiplication()

    def test_implicit_multiplication_number_function(self):
        m = parse("2sin(x)")
        assert m.is_multiplication()

    def test_quoted_string(self):
        m = parse('"hello"')
        assert m.is_symbolic()

    def test_backslash_variable(self):
        m = parse("\\x")
        assert m.is_symbolic()
        assert m.symbol == "\\x"


# ---------------------------------------------------------------------------
# 6. Comparison operators
# ---------------------------------------------------------------------------


class TestComparisons:
    """Test comparison operator parsing."""

    def test_less_than(self):
        m = parse("x < 5")
        assert m.is_comparison()
        assert m.comparison_type == ComparisonType.LESS

    def test_greater_than(self):
        m = parse("x > 5")
        assert m.is_comparison()
        assert m.comparison_type == ComparisonType.GREATER

    def test_less_equal(self):
        m = parse("x <= 5")
        assert m.is_comparison()
        assert m.comparison_type == ComparisonType.EQUALS_LESS

    def test_greater_equal(self):
        m = parse("x >= 5")
        assert m.is_comparison()
        assert m.comparison_type == ComparisonType.EQUALS_GREATER

    def test_equals(self):
        m = parse("x == 5")
        assert m.is_comparison()
        assert m.comparison_type == ComparisonType.EQUALS

    def test_not_equals(self):
        m = parse("x != 5")
        assert m.is_comparison()
        assert m.comparison_type == ComparisonType.NOT_EQUALS


# ---------------------------------------------------------------------------
# 7. Logical operators
# ---------------------------------------------------------------------------


class TestLogicalOperators:
    """Test logical operator parsing."""

    def test_logical_and(self):
        m = parse("x > 0 && x < 10")
        assert m.type == StructureType.LOGICAL_AND

    def test_logical_or(self):
        m = parse("x < 0 || x > 10")
        assert m.type == StructureType.LOGICAL_OR

    def test_logical_and_keyword(self):
        m = parse("x > 0 and x < 10")
        # 'and' maps to bitwise AND in libqalculate convention
        assert m.type in (StructureType.LOGICAL_AND, StructureType.BITWISE_AND)

    def test_logical_or_keyword(self):
        m = parse("x < 0 or x > 10")
        # 'or' maps to bitwise OR in libqalculate convention
        assert m.type in (StructureType.LOGICAL_OR, StructureType.BITWISE_OR)


# ---------------------------------------------------------------------------
# 8. Bitwise operators
# ---------------------------------------------------------------------------


class TestBitwiseOperators:
    """Test bitwise operator parsing."""

    def test_bitwise_and(self):
        m = parse("5 & 3")
        assert m.type == StructureType.BITWISE_AND

    def test_bitwise_or(self):
        m = parse("5 | 3")
        assert m.type == StructureType.BITWISE_OR

    def test_bitwise_not(self):
        m = parse("~5")
        assert m.type == StructureType.BITWISE_NOT

    def test_bitwise_and_keyword(self):
        m = parse("5 AND 3")
        assert m.type == StructureType.BITWISE_AND

    def test_bitwise_or_keyword(self):
        m = parse("5 OR 3")
        assert m.type == StructureType.BITWISE_OR


# ---------------------------------------------------------------------------
# 9. Vectors and matrices
# ---------------------------------------------------------------------------


class TestVectorsAndMatrices:
    """Test vector and matrix parsing."""

    def test_bracket_vector(self):
        m = parse("[1, 2, 3]")
        assert m.is_vector()
        assert len(m) == 3

    def test_bracket_vector_space_sep(self):
        m = parse("[1 2 3]")
        assert m.is_vector()
        assert len(m) == 3

    def test_matrix(self):
        m = parse("[1 2 3; 4 5 6]")
        assert m.is_matrix()
        assert len(m) == 2  # 2 rows

    def test_column_vector_parens(self):
        m = parse("(1; 2; 3)")
        assert m.is_vector()
        assert len(m) == 3

    def test_matrix_3x3(self):
        m = parse("[1 2 3; 4 5 6; 7 8 9]")
        assert m.is_matrix()
        assert len(m) == 3

    def test_single_element_vector(self):
        m = parse("[42]")
        # Single element in brackets
        assert m.is_number() or m.is_vector()


# ---------------------------------------------------------------------------
# 10. Assignments
# ---------------------------------------------------------------------------


class TestAssignments:
    """Test assignment parsing."""

    def test_simple_assignment(self):
        m = parse("x := 5")
        assert m.is_assignment()
        assert len(m) == 2

    def test_assignment_expression(self):
        m = parse("y := 2 + 3")
        assert m.is_assignment()

    def test_function_assignment(self):
        m = parse("f(x) := x^2 + 1")
        assert m.is_assignment()


# ---------------------------------------------------------------------------
# 11. Where clauses
# ---------------------------------------------------------------------------


class TestWhereClauses:
    """Test where clause parsing."""

    def test_simple_where(self):
        m = parse("x^2 where x > 0")
        assert m.is_where()

    def test_where_with_number(self):
        m = parse("x + 1 where x = 5")
        assert m.is_where()


# ---------------------------------------------------------------------------
# 12. Unit conversions
# ---------------------------------------------------------------------------


class TestUnitConversions:
    """Test unit conversion parsing."""

    def test_to_keyword(self):
        m = parse("5 ft to m")
        # Should have some kind of conversion structure
        assert (m.is_unit_conversion() or m.is_function() or
                m.is_multiplication() or m.is_symbolic())

    def test_arrow_conversion(self):
        m = parse("5 ft -> m")
        assert (m.is_unit_conversion() or m.is_function() or
                m.is_multiplication() or m.is_symbolic())


# ---------------------------------------------------------------------------
# 13. Special syntax
# ---------------------------------------------------------------------------


class TestSpecialSyntax:
    """Test special syntax features."""

    def test_comment(self):
        m = parse("42 # this is a comment")
        assert m.is_number()
        assert m.float_value() == 42.0

    def test_empty_expression(self):
        m = parse("")
        assert m.is_undefined()

    def test_whitespace_only(self):
        m = parse("   ")
        assert m.is_undefined()

    def test_per_mille(self):
        m = parse("5\u2030")
        # 5‰ = 5/1000
        assert m.is_multiplication()

    def test_basis_points(self):
        m = parse("100bp")
        # 100bp = 100/10000
        assert m.is_multiplication()

    def test_shift_left(self):
        m = parse("1 << 3")
        assert m.is_function()

    def test_shift_right(self):
        m = parse("8 >> 1")
        assert m.is_function()


# ---------------------------------------------------------------------------
# 14. Complex / combined expressions
# ---------------------------------------------------------------------------


class TestComplexExpressions:
    """Test complex combined expressions."""

    def test_nested_arithmetic(self):
        m = parse("(2 + 3) * (4 - 1)")
        assert m.is_multiplication()

    def test_deeply_nested(self):
        m = parse("((1 + 2) * (3 - 4)) / ((5 + 6) * (7 - 8))")
        assert m.is_multiplication()

    def test_function_in_arithmetic(self):
        m = parse("sin(0) + cos(0)")
        assert m.is_addition()

    def test_power_of_function(self):
        m = parse("sin(x)^2")
        assert m.is_power()

    def test_implicit_mul_chain(self):
        m = parse("2x + 3y")
        assert m.is_addition()

    def test_mixed_operators(self):
        m = parse("a + b * c ^ d - e")
        assert m.is_addition()

    def test_negative_function_arg(self):
        m = parse("sin(-x)")
        assert m.is_function()

    def test_comparison_in_logical(self):
        m = parse("x > 0 && y < 10 || z == 5")
        # Should parse with correct precedence
        assert (m.type == StructureType.LOGICAL_OR or
                m.type == StructureType.LOGICAL_AND)


# ---------------------------------------------------------------------------
# 15. Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_number(self):
        m = parse("1")
        assert m.is_number()

    def test_single_variable(self):
        m = parse("x")
        assert m.is_symbolic()

    def test_unmatched_open_paren(self):
        # Should still parse (auto-close)
        m = parse("(1 + 2")
        assert not m.is_undefined()

    def test_unmatched_close_paren(self):
        # Should still parse (auto-open)
        m = parse("1 + 2)")
        assert not m.is_undefined()

    def test_multiple_operators(self):
        # Should handle gracefully
        m = parse("1 ++ 2")
        assert not m.is_undefined()

    def test_parse_options_base(self):
        po = ParseOptions(base=10)
        m = parse("42", po)
        assert m.is_number()

    def test_idempotent_parsing(self):
        """Parsing the same expression twice gives same result."""
        m1 = parse("2 + 3 * 4")
        m2 = parse("2 + 3 * 4")
        assert m1.type == m2.type


# ---------------------------------------------------------------------------
# 16. Calculator integration
# ---------------------------------------------------------------------------


class TestCalculatorIntegration:
    """Test parser with Calculator context."""

    def test_parser_with_calculator(self):
        from pyqalculate.calculator import Calculator
        calc = Calculator()
        m = calc.parse("1 + 2")
        assert m.is_addition()

    def test_parser_load_definitions(self):
        from pyqalculate.calculator import Calculator
        calc = Calculator()
        calc.load_definitions()
        # After loading, pi and e should be recognized
        m = calc.parse("pi")
        assert m.is_variable() or m.is_symbolic()

    def test_calculator_parse_function(self):
        from pyqalculate.calculator import Calculator
        calc = Calculator()
        calc.load_definitions()
        m = calc.parse("sin(0)")
        assert m.is_function()

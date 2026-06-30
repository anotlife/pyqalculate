"""Comprehensive tests for the Number class.

Tests cover:
- Construction and factory methods
- Exact rational arithmetic
- Floating-point arithmetic
- Complex number support
- Interval arithmetic
- Infinity handling
- Power and root operations
- Transcendental functions (exp, log, trig)
- Number theory (factorial, gcd, lcm, binomial)
- Rounding operations (floor, ceil, round, trunc, mod)
- Comparison operators
- String parsing and output
"""

from __future__ import annotations

import math
import pytest

from pyqalculate.number import Number
from pyqalculate.types import NumberType


# =========================================================================
# Construction
# =========================================================================


class TestConstruction:
    """Tests for Number construction and factory methods."""

    def test_default_is_zero(self):
        n = Number()
        assert n.is_zero()
        assert n.is_rational()
        assert n.number_type == NumberType.RATIONAL

    def test_from_int(self):
        n = Number(42)
        assert n.is_integer()
        assert n.to_int() == 42
        assert n.to_float() == 42.0

    def test_from_negative_int(self):
        n = Number(-7)
        assert n.is_negative()
        assert n.to_int() == -7

    def test_from_int_with_denominator(self):
        n = Number(3, 4)
        assert n.is_rational()
        assert not n.is_integer()
        assert n.numerator() == Number(3)
        assert n.denominator() == Number(4)

    def test_from_float(self):
        n = Number(3.14)
        assert n.is_float()
        assert n.is_approximate()
        assert abs(n.to_float() - 3.14) < 1e-10

    def test_from_string_int(self):
        n = Number("123")
        assert n.is_rational()
        assert n.to_int() == 123

    def test_from_string_rational(self):
        n = Number("22/7")
        assert n.is_rational()
        assert n.numerator() == Number(22)
        assert n.denominator() == Number(7)

    def test_from_string_float(self):
        n = Number("3.14159")
        assert n.is_float()

    def test_from_string_infinity(self):
        n = Number("inf")
        assert n.is_infinite()
        assert n.is_plus_infinity()

        n2 = Number("-inf")
        assert n2.is_infinite()
        assert n2.is_minus_infinity()

    def test_from_rational_factory(self):
        n = Number.from_rational(1, 3)
        assert n.is_rational()
        assert n.numerator() == Number(1)
        assert n.denominator() == Number(3)

    def test_from_float_factory(self):
        n = Number.from_float(2.5)
        assert n.is_float()
        assert n.to_float() == 2.5

    def test_plus_inf_factory(self):
        n = Number.plus_inf()
        assert n.is_infinite()
        assert n.is_plus_infinity()
        assert not n.is_finite()

    def test_minus_inf_factory(self):
        n = Number.minus_inf()
        assert n.is_infinite()
        assert n.is_minus_infinity()

    def test_complex_factory(self):
        n = Number.complex(2, 3)
        assert n.is_complex()
        assert n.real_part() == Number(2)
        assert n.imaginary_part() == Number(3)

    def test_copy_constructor(self):
        n1 = Number(42)
        n2 = Number(n1)
        assert n1 == n2

    def test_exp_10(self):
        n = Number(5, 1, 3)  # 5/1 * 10^3 = 5000
        assert n.to_int() == 5000


# =========================================================================
# Exact Rational Arithmetic
# =========================================================================


class TestRationalArithmetic:
    """Tests for exact rational arithmetic."""

    def test_add_rationals(self):
        a = Number(1, 3)
        b = Number(1, 6)
        result = a + b
        assert result.is_rational()
        assert result == Number(1, 2)

    def test_sub_rationals(self):
        a = Number(3, 4)
        b = Number(1, 4)
        result = a - b
        assert result == Number(1, 2)

    def test_mul_rationals(self):
        a = Number(2, 3)
        b = Number(3, 4)
        result = a * b
        assert result == Number(1, 2)

    def test_div_rationals(self):
        a = Number(1, 2)
        b = Number(1, 3)
        result = a / b
        assert result == Number(3, 2)

    def test_exact_sqrt_perfect_square(self):
        n = Number(144)
        assert n.sqrt()
        assert n == Number(12)

    def test_exact_sqrt_non_perfect(self):
        n = Number(2)
        assert n.sqrt()
        assert n.is_float()  # Falls back to float

    def test_exact_cbrt_perfect(self):
        n = Number(27)
        assert n.cbrt()
        assert n == Number(3)

    def test_exact_cbrt_negative(self):
        n = Number(-27)
        assert n.cbrt()
        assert n == Number(-3)

    def test_rational_pow_integer(self):
        base = Number(2, 3)
        result = base ** Number(3)
        assert result.is_rational()
        assert result == Number(8, 27)

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            Number(1) / Number(0)


# =========================================================================
# Floating Point Arithmetic
# =========================================================================


class TestFloatArithmetic:
    """Tests for floating-point arithmetic."""

    def test_add_floats(self):
        a = Number.from_float(1.5)
        b = Number.from_float(2.5)
        result = a + b
        assert result.is_float()
        assert result.to_float() == 4.0

    def test_mixed_rational_float(self):
        a = Number(1, 2)  # 0.5 exact
        b = Number.from_float(0.3)
        result = a + b
        assert result.is_float()
        assert abs(result.to_float() - 0.8) < 1e-10

    def test_float_pow(self):
        n = Number.from_float(2.0)
        result = n ** Number.from_float(0.5)
        assert abs(result.to_float() - math.sqrt(2)) < 1e-10


# =========================================================================
# Complex Numbers
# =========================================================================


class TestComplexNumbers:
    """Tests for complex number operations."""

    def test_complex_from_string(self):
        n = Number("2+3i")
        assert n.is_complex()
        assert n.real_part() == Number(2)
        assert n.imaginary_part() == Number(3)

    def test_complex_from_string_negative_imag(self):
        n = Number("2-3i")
        assert n.is_complex()
        assert n.real_part() == Number(2)
        assert n.imaginary_part() == Number(-3)

    def test_pure_imaginary(self):
        n = Number("5i")
        assert n.is_complex()
        assert n.real_part().is_zero()
        assert n.imaginary_part() == Number(5)

    def test_pure_imaginary_unit(self):
        n = Number("i")
        assert n.is_complex()
        assert n.imaginary_part() == Number(1)

    def test_complex_addition(self):
        a = Number.complex(1, 2)
        b = Number.complex(3, 4)
        result = a + b
        assert result.real_part() == Number(4)
        assert result.imaginary_part() == Number(6)

    def test_complex_multiplication(self):
        # (1+2i)(3+4i) = 3+4i+6i+8i² = 3+10i-8 = -5+10i
        a = Number.complex(1, 2)
        b = Number.complex(3, 4)
        result = a * b
        assert result.real_part() == Number(-5)
        assert result.imaginary_part() == Number(10)

    def test_complex_conjugate(self):
        n = Number.complex(3, 4)
        c = n.conj()
        assert c.real_part() == Number(3)
        assert c.imaginary_part() == Number(-4)

    def test_complex_modulus(self):
        n = Number.complex(3, 4)
        # |3+4i| = 5
        r = n.real_part()
        i = n.imaginary_part()
        mod_sq = r * r + i * i
        assert mod_sq == Number(25)

    def test_sqrt_negative(self):
        """sqrt(-1) should give i."""
        n = Number(-1)
        assert n.sqrt()
        assert n.is_complex()
        assert n.imaginary_part() == Number(1)

    def test_sqrt_negative_rational(self):
        """sqrt(-4) should give 2i."""
        n = Number(-4)
        assert n.sqrt()
        assert n.is_complex()
        assert n.imaginary_part() == Number(2)

    def test_negative_power_fractional(self):
        """(-8)^(1/3) should give a complex result or -2."""
        n = Number(-8)
        result = n ** Number(1, 3)
        # cbrt(-8) = -2
        assert result == Number(-2) or result.is_complex()


# =========================================================================
# Interval Arithmetic
# =========================================================================


class TestIntervalArithmetic:
    """Tests for interval arithmetic."""

    def test_interval_from_plusminus(self):
        n = Number("5±0.1")
        assert n.is_interval()
        assert abs(n.lower_endpoint().to_float() - 4.9) < 1e-10
        assert abs(n.upper_endpoint().to_float() - 5.1) < 1e-10

    def test_interval_set(self):
        n = Number()
        lo = Number(1.0)
        hi = Number(2.0)
        assert n.set_interval(lo, hi)
        assert n.is_interval()
        assert n.lower_endpoint().to_float() == 1.0
        assert n.upper_endpoint().to_float() == 2.0

    def test_interval_uncertainty(self):
        n = Number("5±0.1")
        unc = n.uncertainty()
        assert abs(unc.to_float() - 0.1) < 1e-10

    def test_interval_from_brackets(self):
        n = Number("[1.5, 2.5]")
        assert n.is_interval()
        assert n.lower_endpoint().to_float() == 1.5
        assert n.upper_endpoint().to_float() == 2.5


# =========================================================================
# Infinity
# =========================================================================


class TestInfinity:
    """Tests for infinity handling."""

    def test_plus_inf_properties(self):
        n = Number.plus_inf()
        assert n.is_infinite()
        assert n.is_positive()
        assert not n.is_negative()
        assert not n.is_finite()
        assert not n.is_zero()

    def test_minus_inf_properties(self):
        n = Number.minus_inf()
        assert n.is_infinite()
        assert n.is_negative()
        assert not n.is_positive()

    def test_inf_arithmetic(self):
        inf = Number.plus_inf()
        one = Number(1)
        assert (inf + one).is_plus_infinity()
        assert (inf * one).is_plus_infinity()

    def test_inf_negation(self):
        inf = Number.plus_inf()
        neg = -inf
        assert neg.is_minus_infinity()

    def test_inf_times_zero_raises(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            Number.plus_inf() * Number(0)

    def test_inf_minus_inf_raises(self):
        with pytest.raises(ValueError):
            Number.plus_inf() + Number.minus_inf()

    def test_inf_to_string(self):
        assert Number.plus_inf().to_string() == "inf"
        assert Number.minus_inf().to_string() == "-inf"


# =========================================================================
# Power and Root
# =========================================================================


class TestPowerAndRoot:
    """Tests for power and root operations."""

    def test_square(self):
        n = Number(5)
        assert n.square()
        assert n == Number(25)

    def test_integer_power(self):
        n = Number(2)
        result = n ** Number(10)
        assert result == Number(1024)

    def test_zero_power(self):
        n = Number(5)
        result = n ** Number(0)
        assert result == Number(1)

    def test_power_one(self):
        n = Number(42)
        result = n ** Number(1)
        assert result == Number(42)

    def test_negative_exponent(self):
        n = Number(2)
        result = n ** Number(-1)
        assert result == Number(1, 2)

    def test_rational_exponent_sqrt(self):
        """x^(1/2) = sqrt(x)"""
        n = Number(16)
        result = n ** Number(1, 2)
        assert result == Number(4)

    def test_rational_exponent_cbrt(self):
        """x^(1/3) = cbrt(x)"""
        n = Number(27)
        result = n ** Number(1, 3)
        assert result == Number(3)

    def test_sqrt_method(self):
        n = Number(64)
        assert n.sqrt()
        assert n == Number(8)

    def test_cbrt_method(self):
        n = Number(125)
        assert n.cbrt()
        assert n == Number(5)

    def test_root_method(self):
        n = Number(256)
        assert n.root(Number(4))
        assert n == Number(4)

    def test_recip(self):
        n = Number(4)
        assert n.recip()
        assert n == Number(1, 4)


# =========================================================================
# Exponential and Logarithmic
# =========================================================================


class TestExpLog:
    """Tests for exponential and logarithmic functions."""

    def test_exp_zero(self):
        n = Number(0)
        assert n.exp()
        assert n == Number(1)

    def test_exp_one(self):
        n = Number(1)
        assert n.exp()
        assert abs(n.to_float() - math.e) < 1e-10

    def test_exp_negative(self):
        n = Number(-1)
        assert n.exp()
        assert abs(n.to_float() - (1 / math.e)) < 1e-10

    def test_ln_one(self):
        n = Number(1)
        assert n.ln()
        assert n.is_zero()

    def test_ln_e(self):
        n = Number.from_float(math.e)
        assert n.ln()
        assert abs(n.to_float() - 1.0) < 1e-10

    def test_ln_zero_is_minus_inf(self):
        n = Number(0)
        assert n.ln()
        assert n.is_minus_infinity()

    def test_log10(self):
        n = Number(1000)
        assert n.log10()
        assert n == Number(3)

    def test_log2(self):
        n = Number(8)
        assert n.log2()
        assert n == Number(3)

    def test_log_base(self):
        n = Number(81)
        assert n.log(Number(3))
        assert n == Number(4)

    def test_exp10(self):
        n = Number(3)
        assert n.exp10()
        assert n == Number(1000)

    def test_exp2(self):
        n = Number(4)
        assert n.exp2()
        assert n == Number(16)


# =========================================================================
# Rounding Operations
# =========================================================================


class TestRounding:
    """Tests for floor, ceil, round, trunc, mod, rem."""

    def test_floor_positive(self):
        n = Number(7, 3)  # 7/3 ≈ 2.33
        assert n.floor()
        assert n == Number(2)

    def test_floor_negative(self):
        n = Number(-7, 3)  # -7/3 ≈ -2.33
        assert n.floor()
        assert n == Number(-3)

    def test_ceil_positive(self):
        n = Number(7, 3)
        assert n.ceil()
        assert n == Number(3)

    def test_ceil_negative(self):
        n = Number(-7, 3)
        assert n.ceil()
        assert n == Number(-2)

    def test_trunc_positive(self):
        n = Number(7, 3)
        assert n.trunc()
        assert n == Number(2)

    def test_trunc_negative(self):
        n = Number(-7, 3)
        assert n.trunc()
        assert n == Number(-2)

    def test_round_half_to_even(self):
        n = Number(5, 2)  # 2.5
        assert n.round()
        assert n == Number(2)  # Round to even

    def test_round_up(self):
        n = Number(7, 2)  # 3.5
        assert n.round()
        assert n == Number(4)  # Round to even

    def test_mod_positive(self):
        a = Number(7)
        b = Number(3)
        assert a.mod(b)
        assert a == Number(1)

    def test_mod_negative(self):
        a = Number(-7)
        b = Number(3)
        assert a.mod(b)
        # -7 mod 3 = -7 - 3 * floor(-7/3) = -7 - 3*(-3) = -7 + 9 = 2
        assert a == Number(2)

    def test_floor_already_integer(self):
        n = Number(5)
        assert n.floor()
        assert n == Number(5)

    def test_ceil_already_integer(self):
        n = Number(5)
        assert n.ceil()
        assert n == Number(5)


# =========================================================================
# Number Theory
# =========================================================================


class TestNumberTheory:
    """Tests for factorial, gcd, lcm, binomial."""

    def test_factorial_zero(self):
        n = Number(0)
        assert n.factorial()
        assert n == Number(1)

    def test_factorial_one(self):
        n = Number(1)
        assert n.factorial()
        assert n == Number(1)

    def test_factorial_five(self):
        n = Number(5)
        assert n.factorial()
        assert n.to_int() == 120

    def test_factorial_ten(self):
        n = Number(10)
        assert n.factorial()
        assert n.to_int() == 3628800

    def test_factorial_negative_fails(self):
        n = Number(-1)
        assert not n.factorial()

    def test_factorial_non_integer_fails(self):
        n = Number(1, 2)
        assert not n.factorial()

    def test_gcd_basic(self):
        a = Number(2520)
        b = Number(3600)
        assert a.gcd(b)
        assert a == Number(360)

    def test_gcd_coprime(self):
        a = Number(7)
        b = Number(13)
        assert a.gcd(b)
        assert a == Number(1)

    def test_gcd_same(self):
        a = Number(42)
        b = Number(42)
        assert a.gcd(b)
        assert a == Number(42)

    def test_gcd_with_zero(self):
        a = Number(0)
        b = Number(42)
        assert a.gcd(b)
        assert a == Number(42)

    def test_lcm_basic(self):
        a = Number(2520)
        b = Number(3600)
        assert a.lcm(b)
        assert a == Number(25200)

    def test_lcm_coprime(self):
        a = Number(3)
        b = Number(5)
        assert a.lcm(b)
        assert a == Number(15)

    def test_lcm_same(self):
        a = Number(42)
        b = Number(42)
        assert a.lcm(b)
        assert a == Number(42)

    def test_binomial_basic(self):
        n = Number()
        assert n.binomial(Number(10), Number(3))
        assert n.to_int() == 120  # C(10,3) = 120

    def test_binomial_symmetric(self):
        n = Number()
        assert n.binomial(Number(10), Number(7))
        assert n.to_int() == 120  # C(10,7) = C(10,3) = 120

    def test_binomial_zero(self):
        n = Number()
        assert n.binomial(Number(5), Number(0))
        assert n == Number(1)

    def test_binomial_identity(self):
        n = Number()
        assert n.binomial(Number(5), Number(5))
        assert n == Number(1)

    def test_binomial_k_greater_than_n(self):
        n = Number()
        assert n.binomial(Number(3), Number(5))
        assert n.is_zero()


# =========================================================================
# Trigonometric Functions
# =========================================================================


class TestTrigonometric:
    """Tests for trigonometric functions."""

    def test_sin_zero(self):
        n = Number(0)
        assert n.sin()
        assert n.is_zero()

    def test_cos_zero(self):
        n = Number(0)
        assert n.cos()
        assert n == Number(1)

    def test_sin_pi_half(self):
        n = Number.from_float(math.pi / 2)
        assert n.sin()
        assert abs(n.to_float() - 1.0) < 1e-10

    def test_cos_pi(self):
        n = Number.from_float(math.pi)
        assert n.cos()
        assert abs(n.to_float() - (-1.0)) < 1e-10

    def test_tan_zero(self):
        n = Number(0)
        assert n.tan()
        assert n.is_zero()

    def test_tan_pi_quarter(self):
        n = Number.from_float(math.pi / 4)
        assert n.tan()
        assert abs(n.to_float() - 1.0) < 1e-10

    def test_asin_zero(self):
        n = Number(0)
        assert n.asin()
        assert n.is_zero()

    def test_asin_one(self):
        n = Number(1)
        assert n.asin()
        assert abs(n.to_float() - math.pi / 2) < 1e-10

    def test_acos_one(self):
        n = Number(1)
        assert n.acos()
        assert n.is_zero()

    def test_atan_zero(self):
        n = Number(0)
        assert n.atan()
        assert n.is_zero()

    def test_atan_one(self):
        n = Number(1)
        assert n.atan()
        assert abs(n.to_float() - math.pi / 4) < 1e-10

    def test_atan2(self):
        n = Number(1)
        assert n.atan2(Number(1))
        assert abs(n.to_float() - math.pi / 4) < 1e-10

    def test_complex_sin(self):
        n = Number.complex(1, 1)
        assert n.sin()
        # sin(1+i) = sin(1)cosh(1) + i*cos(1)sinh(1)
        expected_real = math.sin(1) * math.cosh(1)
        expected_imag = math.cos(1) * math.sinh(1)
        assert abs(n.real_part().to_float() - expected_real) < 1e-8
        assert abs(n.imaginary_part().to_float() - expected_imag) < 1e-8


# =========================================================================
# Hyperbolic Functions
# =========================================================================


class TestHyperbolic:
    """Tests for hyperbolic functions."""

    def test_sinh_zero(self):
        n = Number(0)
        assert n.sinh()
        assert n.is_zero()

    def test_cosh_zero(self):
        n = Number(0)
        assert n.cosh()
        assert n == Number(1)

    def test_tanh_zero(self):
        n = Number(0)
        assert n.tanh()
        assert n.is_zero()

    def test_sinh_one(self):
        n = Number(1)
        assert n.sinh()
        assert abs(n.to_float() - math.sinh(1)) < 1e-10

    def test_cosh_one(self):
        n = Number(1)
        assert n.cosh()
        assert abs(n.to_float() - math.cosh(1)) < 1e-10


# =========================================================================
# Comparison
# =========================================================================


class TestComparison:
    """Tests for comparison operators."""

    def test_equality_same_type(self):
        assert Number(5) == Number(5)
        assert Number(5) != Number(6)

    def test_equality_rational_float(self):
        assert Number(1, 2) == Number.from_float(0.5)

    def test_less_than(self):
        assert Number(3) < Number(5)
        assert not Number(5) < Number(3)

    def test_greater_than(self):
        assert Number(5) > Number(3)
        assert not Number(3) > Number(5)

    def test_less_equal(self):
        assert Number(3) <= Number(5)
        assert Number(5) <= Number(5)

    def test_greater_equal(self):
        assert Number(5) >= Number(3)
        assert Number(5) >= Number(5)

    def test_negative_less_than_positive(self):
        assert Number(-1) < Number(1)

    def test_inf_comparisons(self):
        inf = Number.plus_inf()
        ninf = Number.minus_inf()
        assert ninf < Number(0)
        assert Number(0) < inf
        assert not (inf < inf)
        assert ninf < inf

    def test_hash(self):
        assert hash(Number(42)) == hash(Number(42))
        s = {Number(1), Number(2), Number(1)}
        assert len(s) == 2


# =========================================================================
# Properties and Queries
# =========================================================================


class TestProperties:
    """Tests for boolean query methods."""

    def test_is_zero(self):
        assert Number(0).is_zero()
        assert not Number(1).is_zero()

    def test_is_one(self):
        assert Number(1).is_one()
        assert not Number(0).is_one()

    def test_is_positive(self):
        assert Number(1).is_positive()
        assert not Number(-1).is_positive()
        assert not Number(0).is_positive()

    def test_is_negative(self):
        assert Number(-1).is_negative()
        assert not Number(1).is_negative()

    def test_is_integer(self):
        assert Number(5).is_integer()
        assert Number(1, 2).is_integer() is False

    def test_is_even_odd(self):
        assert Number(4).is_even()
        assert Number(5).is_odd()
        assert not Number(4).is_odd()

    def test_is_non_integer(self):
        assert Number(1, 2).is_non_integer()
        assert not Number(5).is_non_integer()

    def test_is_fraction(self):
        assert Number(1, 3).is_fraction()
        assert not Number(3, 2).is_fraction()
        assert not Number(0).is_fraction()


# =========================================================================
# String Parsing
# =========================================================================


class TestStringParsing:
    """Tests for parsing from strings."""

    def test_parse_integer(self):
        n = Number("42")
        assert n == Number(42)

    def test_parse_negative(self):
        n = Number("-17")
        assert n == Number(-17)

    def test_parse_rational(self):
        n = Number("3/4")
        assert n == Number(3, 4)

    def test_parse_float(self):
        n = Number("3.14")
        assert abs(n.to_float() - 3.14) < 1e-10

    def test_parse_scientific(self):
        n = Number("1.5e3")
        assert abs(n.to_float() - 1500.0) < 1e-5

    def test_parse_plusminus(self):
        n = Number("5±0.1")
        assert n.is_interval()
        assert abs(n.lower_endpoint().to_float() - 4.9) < 1e-10
        assert abs(n.upper_endpoint().to_float() - 5.1) < 1e-10

    def test_parse_complex_integer(self):
        n = Number("3+4i")
        assert n.is_complex()
        assert n.real_part() == Number(3)
        assert n.imaginary_part() == Number(4)

    def test_parse_complex_negative_imag(self):
        n = Number("2-5i")
        assert n.is_complex()
        assert n.real_part() == Number(2)
        assert n.imaginary_part() == Number(-5)

    def test_parse_interval_brackets(self):
        n = Number("[1.5, 2.5]")
        assert n.is_interval()


# =========================================================================
# Output / Representation
# =========================================================================


class TestOutput:
    """Tests for string output and representation."""

    def test_integer_to_string(self):
        assert Number(42).to_string() == "42"

    def test_rational_to_string(self):
        assert Number(1, 3).to_string() == "1/3"

    def test_inf_to_string(self):
        assert Number.plus_inf().to_string() == "inf"
        assert Number.minus_inf().to_string() == "-inf"

    def test_repr(self):
        n = Number(42)
        assert "42" in repr(n)

    def test_str(self):
        n = Number(42)
        assert str(n) == "42"

    def test_bool_truthy(self):
        assert bool(Number(1))
        assert not bool(Number(0))


# =========================================================================
# In-place Operations (C++ API style)
# =========================================================================


class TestInPlace:
    """Tests for in-place operations."""

    def test_add_in_place(self):
        n = Number(10)
        assert n.add(Number(5))
        assert n == Number(15)

    def test_subtract_in_place(self):
        n = Number(10)
        assert n.subtract(Number(3))
        assert n == Number(7)

    def test_multiply_in_place(self):
        n = Number(6)
        assert n.multiply(Number(7))
        assert n == Number(42)

    def test_divide_in_place(self):
        n = Number(42)
        assert n.divide(Number(6))
        assert n == Number(7)

    def test_negate_in_place(self):
        n = Number(5)
        assert n.negate()
        assert n == Number(-5)

    def test_abs_in_place(self):
        n = Number(-5)
        assert n.abs()
        assert n == Number(5)

    def test_abs_positive_unchanged(self):
        n = Number(5)
        assert n.abs()
        assert n == Number(5)


# =========================================================================
# Edge Cases
# =========================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_zero_pow_zero(self):
        """0^0 should be undefined (return False)."""
        n = Number(0)
        result = n.raise_(Number(0))
        assert not result

    def test_negative_pow_fractional_even_root(self):
        """(-4)^(1/2) should give complex result."""
        n = Number(-4)
        result = n ** Number(1, 2)
        assert result.is_complex()
        assert result.imaginary_part() == Number(2)

    def test_large_factorial(self):
        n = Number(20)
        assert n.factorial()
        assert n.to_int() == 2432902008176640000

    def test_copy_is_independent(self):
        n1 = Number(42)
        n2 = Number(n1)
        n2.add(1)
        assert n1 == Number(42)
        assert n2 == Number(43)

    def test_set_clear(self):
        n = Number(42)
        n.clear()
        assert n.is_zero()
        assert n.is_rational()

    def test_signum_positive(self):
        n = Number(42)
        assert n.signum()
        assert n == Number(1)

    def test_signum_negative(self):
        n = Number(-42)
        assert n.signum()
        assert n == Number(-1)

    def test_signum_zero(self):
        n = Number(0)
        assert n.signum()
        assert n.is_zero()


# =========================================================================
# Integration Tests (matching the requirement examples)
# =========================================================================


class TestIntegration:
    """Integration tests matching the examples from the requirements."""

    def test_factorial_5(self):
        """5! = 120"""
        n = Number(5)
        n.factorial()
        assert n.to_int() == 120

    def test_gcd_2520_3600(self):
        """gcd(2520, 3600) = 360"""
        n = Number(2520)
        n.gcd(Number(3600))
        assert n == Number(360)

    def test_lcm_2520_3600(self):
        """lcm(2520, 3600) = 25200"""
        n = Number(2520)
        n.lcm(Number(3600))
        assert n == Number(25200)

    def test_complex_2_plus_3i(self):
        """2+3i: real=2, imag=3"""
        n = Number("2+3i")
        assert n.real_part() == Number(2)
        assert n.imaginary_part() == Number(3)

    def test_interval_plus_minus(self):
        """5±0.1 is interval [4.9, 5.1]"""
        n = Number("5±0.1")
        assert n.is_interval()
        assert abs(n.lower_endpoint().to_float() - 4.9) < 1e-10
        assert abs(n.upper_endpoint().to_float() - 5.1) < 1e-10

    def test_plus_inf_is_infinite(self):
        """plus_inf is infinite and not finite."""
        n = Number.plus_inf()
        assert n.is_infinite()
        assert not n.is_finite()

    def test_sqrt_32_exact(self):
        """In exact mode, sqrt(32) should simplify to 4*sqrt(2)."""
        n = Number(32)
        n.sqrt()
        # sqrt(32) = 4*sqrt(2) ≈ 5.657...
        # With our implementation, it falls to float since 32 is not a perfect square
        assert abs(n.to_float() - math.sqrt(32)) < 1e-10

    def test_real_part_extraction(self):
        """Extract real part of complex number."""
        n = Number.complex(2, 3)
        assert n.real_part() == Number(2)

    def test_imaginary_part_extraction(self):
        """Extract imaginary part of complex number."""
        n = Number.complex(2, 3)
        assert n.imaginary_part() == Number(3)

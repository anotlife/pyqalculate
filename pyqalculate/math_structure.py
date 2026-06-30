"""MathStructure - tree representation of mathematical expressions.

Mirrors libqalculate's MathStructure class. A MathStructure can be a
container representing an operation with children, or a simple value
(number, variable, unit, symbolic).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import sympy as sp

from pyqalculate.number import Number
from pyqalculate.types import (
    ApproximationMode,
    ComparisonType,
    EvaluationOptions,
    MathOperation,
    NumberFractionFormat,
    ParseOptions,
    PrintOptions,
    StructureType,
)

if TYPE_CHECKING:
    from pyqalculate.function import MathFunction
    from pyqalculate.unit import Unit
    from pyqalculate.variable import Variable


# ---------------------------------------------------------------------------
# SymPy function mapping (name → SymPy function)
# ---------------------------------------------------------------------------

def _gcd_multi(*args):
    result = args[0]
    for a in args[1:]:
        result = sp.gcd(result, a)
    return result

def _lcm_multi(*args):
    result = args[0]
    for a in args[1:]:
        result = sp.lcm(result, a)
    return result

def _sinc(x):
    """SymPy-compatible sinc: sin(x)/x, with sinc(0)=1."""
    return sp.Piecewise((sp.sin(x) / x, sp.Ne(x, 0)), (1, True))
    """SymPy-compatible sinc: sin(x)/x, with sinc(0)=1."""
    return sp.Piecewise((sp.sin(x) / x, sp.Ne(x, 0)), (1, True))

def _atan2(y, x):
    return sp.atan2(y, x)

def _logn(x, base):
    return sp.log(x) / sp.log(base)

def _exp2(x):
    return sp.Pow(2, x)

def _exp10(x):
    return sp.Pow(10, x)

def _square(x):
    return sp.Pow(x, 2)

def _cbrt(x):
    return sp.Pow(x, sp.Rational(1, 3))

def _root(x, n):
    return sp.Pow(x, sp.Rational(1, n))

def _signum(x):
    return sp.sign(x)

def _round(x, n=None):
    try:
        if n is not None:
            return sp.Float(round(float(x), int(n)))
        return sp.Integer(round(float(x)))
    except (TypeError, ValueError):
        return sp.Function('round')(x, n) if n is not None else sp.Function('round')(x)

def _trunc(x):
    try:
        return sp.Integer(int(float(x)))
    except (TypeError, ValueError):
        return sp.Function('trunc')(x)

def _rem(a, b):
    return sp.Mod(a, b)

def _is_prime(n):
    return sp.Integer(1) if sp.isprime(int(n)) else sp.Integer(0)

def _next_prime(n):
    return sp.Integer(int(sp.nextprime(int(n))))

def _prev_prime(n):
    return sp.Integer(int(sp.prevprime(int(n))))

def _nth_prime(n):
    return sp.Integer(int(sp.prime(int(n))))

def _prime_count(n):
    return sp.Integer(int(sp.primepi(int(n))))

def _numerator(x):
    return sp.numer(x)

def _denominator(x):
    return sp.denom(x)

def _int_part(x):
    return sp.Integer(int(float(x)))

def _frac_part(x):
    return x - sp.floor(x)

def _totient(n):
    return sp.totient(int(n))

def _bernoulli(n):
    return sp.bernoulli(int(n))

def _re_func(z):
    return sp.re(z)

def _im_func(z):
    return sp.im(z)

def _arg_func(z):
    return sp.arg(z)

def _binomial(n, k):
    return sp.binomial(n, k)

def _double_factorial(n):
    return sp.factorial2(int(n))

def _multinomial(*args):
    total = sum(args)
    result = sp.factorial(total)
    for a in args:
        result = result / sp.factorial(a)
    return result

def _zeta(s):
    return sp.zeta(s)

def _beta(a, b):
    return sp.beta(a, b)

def _erf(x):
    return sp.erf(x)

def _erfc(x):
    return sp.erfc(x)

def _besselj(n, x):
    return sp.besselj(n, x)

def _bessely(n, x):
    return sp.bessely(n, x)

def _airy(x):
    return sp.airyai(x)

def _fresnels(x):
    return sp.fresnels(x)

def _fresnelc(x):
    return sp.fresnelc(x)

def _digamma(x):
    return sp.digamma(x)

def _heaviside(x):
    return sp.Heaviside(x)

def _dirac(x):
    return sp.DiracDelta(x)

def _lambertw(x, branch=0):
    return sp.LambertW(x, int(branch))

def _cis(x):
    return sp.cos(x) + sp.I * sp.sin(x)

def _bitand(a, b):
    return sp.Integer(int(a) & int(b))

def _bitor(a, b):
    return sp.Integer(int(a) | int(b))

def _bitxor(a, b):
    return sp.Integer(int(a) ^ int(b))

def _bitnot(x, bits=32):
    return sp.Integer(~int(x) & ((1 << int(bits)) - 1))

def _shift(x, n):
    n = int(n)
    if n >= 0:
        return sp.Integer(int(x) << n)
    return sp.Integer(int(x) >> (-n))

def _logical_and(*args):
    return sp.Integer(1 if all(int(a) != 0 for a in args) else 0)

def _logical_or(*args):
    return sp.Integer(1 if any(int(a) != 0 for a in args) else 0)

def _logical_xor(a, b):
    return sp.Integer(1 if (int(a) != 0) ^ (int(b) != 0) else 0)

def _logical_not(x):
    return sp.Integer(0 if int(x) != 0 else 1)

def _is_number(x):
    return sp.Integer(1 if x.is_number else 0)

def _is_real(x):
    return sp.Integer(1 if x.is_real else 0)

def _is_rational(x):
    return sp.Integer(1 if x.is_rational else 0)

def _is_integer(x):
    return sp.Integer(1 if x.is_integer else 0)

def _odd(x):
    return sp.Integer(1 if int(x) % 2 != 0 else 0)

def _even(x):
    return sp.Integer(1 if int(x) % 2 == 0 else 0)

def _parallel(*args):
    try:
        total = sp.Integer(0)
        for a in args:
            a_val = sp.nsimplify(a)
            if a_val == 0:
                return sp.zoo
            total += 1 / a_val
        if total == 0:
            return sp.zoo
        return 1 / total
    except Exception:
        return sp.Function('parallel')(*args)

def _powermod(base, exp, mod):
    return sp.Integer(pow(int(base), int(exp), int(mod)))

def _diff(expr, var, n=1):
    return sp.diff(expr, var, int(n))

def _integrate_func(expr, var, a=None, b=None):
    if a is not None and b is not None:
        return sp.integrate(expr, (var, a, b))
    return sp.integrate(expr, var)

def _limit(expr, var, val, direction='+'):
    return sp.limit(expr, var, val, str(direction))

def _summation(expr, var, lo, hi):
    return sp.summation(expr, (var, lo, hi))

def _product(expr, var, lo, hi):
    return sp.product(expr, (var, lo, hi))

def _solve(expr, var):
    solutions = sp.solve(expr, var)
    if not solutions:
        return sp.Symbol('undefined')
    if len(solutions) == 1:
        return solutions[0]
    return sp.Tuple(*solutions)

def _factor(expr):
    return sp.factor(expr)

def _expand(expr):
    return sp.expand(expr)

def _coeff(poly, var, n):
    return sp.Poly(poly, var).nth(int(n))

def _degree(poly, var):
    return sp.Integer(int(sp.degree(sp.Poly(poly, var))))

def _roman(n):
    n = int(n)
    if not (1 <= n <= 3999):
        return sp.Symbol('undefined')
    val_map = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),
               (100,'C'),(90,'XC'),(50,'L'),(40,'XL'),
               (10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    result = ''
    for val, sym in val_map:
        while n >= val:
            result += sym
            n -= val
    return sp.Symbol(result)

def _base(n, b):
    n, b = int(n), int(b)
    if not (2 <= b <= 36):
        return sp.Symbol('undefined')
    import string
    digits = string.digits + string.ascii_lowercase
    if n == 0:
        return sp.Symbol('0')
    result = ""
    neg = n < 0
    n = abs(n)
    while n:
        result = digits[n % b] + result
        n //= b
    return sp.Symbol(('-' + result) if neg else result)

def _bin_func(n):
    bits = format(abs(int(n)), 'b')
    while len(bits) % 4 != 0:
        bits = '0' + bits
    formatted = ' '.join(bits[i:i+4] for i in range(0, len(bits), 4))
    sign = '-' if int(n) < 0 else ''
    return sp.Symbol(sign + formatted)

def _oct_func(n):
    sign = '-' if int(n) < 0 else ''
    return sp.Symbol(sign + '0' + format(abs(int(n)), 'o'))

def _hex_func(n):
    sign = '-' if int(n) < 0 else ''
    return sp.Symbol(sign + '0x' + format(abs(int(n)), 'X'))

def _quartile(v, q):
    import numpy as _np
    if hasattr(v, '__iter__'):
        vals = [float(x) for x in v]
    else:
        vals = [float(v)]
    return sp.Float(float(_np.percentile(vals, int(q) * 25)))

def _percentile(v, p):
    import numpy as _np
    if hasattr(v, '__iter__'):
        vals = [float(x) for x in v]
    else:
        vals = [float(v)]
    return sp.Float(float(_np.percentile(vals, float(p))))


def _if_func(cond, then_val, else_val=None):
    """Evaluate if(cond, then, else) - safe for symbolic args"""
    try:
        cond_num = complex(cond)
        if cond_num != 0:
            return then_val
        return else_val if else_val is not None else sp.Integer(0)
    except (TypeError, ValueError):
        # Symbolic condition
        return sp.Piecewise((then_val, sp.Ne(cond, 0)), (else_val if else_val is not None else sp.Integer(0), True))

def _for_func(var, start, end, expr):
    """Evaluate for(var, start, end, expr) - safe for symbolic args"""
    try:
        s = int(start)
        e = int(end)
        total = sp.Integer(0)
        for i in range(s, e + 1):
            total += expr.subs(var, i)
        return total
    except (TypeError, ValueError):
        return sp.Sum(expr, (var, start, end)).doit()

def _rand_func(max_val=None):
    import random
    if max_val is not None:
        return sp.Float(random.uniform(0, float(max_val)))
    return sp.Float(random.random())

def _timestamp_func(date_str=None):
    import time as _time
    import datetime as _dt
    if date_str is not None:
        try:
            d = _dt.date.fromisoformat(str(date_str))
            return sp.Integer(int(_dt.datetime(d.year, d.month, d.day).timestamp()))
        except Exception:
            pass
    return sp.Integer(int(_time.time()))

def _stamptodate_func(ts):
    import datetime
    return sp.Symbol(datetime.datetime.fromtimestamp(float(ts)).isoformat())

def _days_func(d1, d2):
    import datetime
    try:
        date1 = datetime.date.fromisoformat(str(d1))
        date2 = datetime.date.fromisoformat(str(d2))
        return sp.Integer((date2 - date1).days)
    except:
        return sp.Symbol('undefined')

def _weeks_func(d1, d2):
    return sp.Integer(int(_days_func(d1, d2)) // 7)

def _months_func(d1, d2):
    import datetime
    try:
        date1 = datetime.date.fromisoformat(str(d1))
        date2 = datetime.date.fromisoformat(str(d2))
        return sp.Integer((date2.year - date1.year) * 12 + date2.month - date1.month)
    except:
        return sp.Symbol('undefined')

def _years_func(d1, d2):
    import datetime
    try:
        date1 = datetime.date.fromisoformat(str(d1))
        date2 = datetime.date.fromisoformat(str(d2))
        return sp.Integer(date2.year - date1.year)
    except:
        return sp.Symbol('undefined')

def _now_func():
    import datetime
    return sp.Symbol(datetime.datetime.now().isoformat())

def _today_func():
    import datetime
    return sp.Symbol(str(datetime.date.today()))

def _lunarphase_func():
    import datetime
    d = datetime.date.today()
    days_since = (d - datetime.date(2000, 1, 6)).days
    phase = (days_since % 29.53059) / 29.53059
    names = ["New Moon","Waxing Crescent","First Quarter","Waxing Gibbous",
             "Full Moon","Waning Gibbous","Last Quarter","Waning Crescent"]
    return sp.Symbol(f"{names[int(phase * 8) % 8]} ({phase:.1%})")

def _genvector_func(expr, var, n):
    return sp.Tuple(*[expr.subs(var, i) for i in range(1, int(n) + 1)])

def _replace_func(text, old, new):
    return sp.Symbol(str(text).replace(str(old), str(new)))

def _tostring_func(x):
    return sp.Symbol(str(x))

def _length_func(s):
    if hasattr(s, '__len__'):
        return sp.Integer(len(s))
    return sp.Integer(len(str(s)))

def _concatenate_func(*args):
    return sp.Symbol(''.join(str(a) for a in args))

def _load_func(filename):
    return sp.Symbol('undefined')

def _date_func(y, m, d):
    import datetime
    try:
        return sp.Symbol(str(datetime.date(int(y), int(m), int(d))))
    except:
        return sp.Symbol('undefined')

def _bessely_func(n, x):
    return sp.bessely(n, x)

def _bernoulli2(n):
    return sp.bernoulli(int(n))

def _solve2(expr, var):
    solutions = sp.solve(expr, var)
    if not solutions:
        return sp.Symbol('undefined')
    if len(solutions) == 1:
        return solutions[0]
    return sp.Tuple(*solutions)

def _integrate2(expr, var, a=None, b=None):
    if a is not None and b is not None:
        return sp.integrate(expr, (var, a, b))
    return sp.integrate(expr, var)

def _limit2(expr, var, val, direction='+'):
    return sp.limit(expr, var, val, str(direction))

def _summation2(expr, var, lo, hi):
    return sp.summation(expr, (var, lo, hi))

def _product2(expr, var, lo, hi):
    return sp.product(expr, (var, lo, hi))

def _roman2(n):
    n = int(n)
    if not (1 <= n <= 3999):
        return sp.Symbol('undefined')
    val_map = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),
               (100,'C'),(90,'XC'),(50,'L'),(40,'XL'),
               (10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    result = ''
    for val, sym in val_map:
        while n >= val:
            result += sym
            n -= val
    return sp.Symbol(result)

def _base2(n, b):
    n, b = int(n), int(b)
    if not (2 <= b <= 36):
        return sp.Symbol('undefined')
    import string
    digits = string.digits + string.ascii_lowercase
    if n == 0:
        return sp.Symbol('0')
    result = ""
    neg = n < 0
    n = abs(n)
    while n:
        result = digits[n % b] + result
        n //= b
    return sp.Symbol(('-' + result) if neg else result)


_SYMPY_FUNC_MAP: dict[str, Any] = {
    # Trig
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "arcsin": sp.asin,
    "acos": sp.acos,
    "arccos": sp.acos,
    "atan": sp.atan,
    "arctan": sp.atan,
    "atan2": _atan2,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "asinh": sp.asinh,
    "acosh": sp.acosh,
    "atanh": sp.atanh,
    "sinc": _sinc,
    # Exp/Log
    "exp": sp.exp,
    "sqrt": sp.sqrt,
    # "cbrt" intentionally omitted — SymPy's default handles negative reals correctly
    "root": _root,
    "square": _square,
    "ln": sp.log,
    "log": sp.log,
    "log2": lambda x: sp.log(x) / sp.log(2),
    "log10": lambda x: sp.log(x, 10),
    "logn": _logn,
    "exp2": _exp2,
    "exp10": _exp10,
    "lambertw": _lambertw,
    "cis": _cis,
    # Abs/Sign
    "abs": sp.Abs,
    "sign": sp.sign,
    "signum": _signum,
    # Rounding
    "floor": sp.floor,
    "ceil": sp.ceiling,
    "round": _round,
    "trunc": _trunc,
    # Number Theory
    "gcd": _gcd_multi,
    "lcm": _lcm_multi,
    "mod": sp.Mod,
    "rem": _rem,
    "is_prime": _is_prime,
    "next_prime": _next_prime,
    "prev_prime": _prev_prime,
    "nth_prime": _nth_prime,
    "prime_count": _prime_count,
    "numerator": _numerator,
    "denominator": _denominator,
    "int": _int_part,
    "frac": _frac_part,
    "totient": _totient,
    "bernoulli": _bernoulli2,
    "re": _re_func,
    "im": _im_func,
    "arg": _arg_func,
    "powermod": _powermod,
    "parallel": _parallel,
    # Combinatorics
    "factorial": sp.factorial,
    "double_factorial": _double_factorial,
    "multinomial": _multinomial,
    "binomial": _binomial,
    "gamma": sp.gamma,
    # Special Functions
    "zeta": _zeta,
    "beta": _beta,
    "erf": _erf,
    "erfc": _erfc,
    "besselj": _besselj,
    "bessely": _bessely_func,
    "airy": _airy,
    "fresnels": _fresnels,
    "fresnelc": _fresnelc,
    "digamma": _digamma,
    "heaviside": _heaviside,
    "dirac": _dirac,
    # Bitwise
    "bitand": _bitand,
    "bitor": _bitor,
    "bitxor": _bitxor,
    "bitnot": _bitnot,
    "shift": _shift,
    # Calculus — diff/integrate/limit are NOT here so their registered
    # BuiltinFunction.calculate() methods are used (they handle variable
    # auto-detection, +C for indefinite integrals, etc.)
    # "factor", "expand", "coeff", "degree" are also excluded so their
    # registered BuiltinFunction.calculate() methods are used directly.
    # Putting them here causes sp.simplify() to re-expand factored results.
    # "sum" and "product" are excluded to allow 3-arg auto-variable detection.
    "solve": _solve2,
    # Base Conversion
    "bin": _bin_func,
    "oct": _oct_func,
    "hex": _hex_func,
    "base": _base2,
    "roman": _roman2,
    # Utility
    "is_number": _is_number,
    "is_real": _is_real,
    "is_rational": _is_rational,
    "is_integer": _is_integer,
    "odd": _odd,
    "even": _even,
    "min": sp.Min,
    "max": sp.Max,
    # Control flow & utility
    "if": _if_func,
    "for": _for_func,
    "rand": _rand_func,
    "timestamp": _timestamp_func,
    "stamptodate": _stamptodate_func,
    "days": _days_func,
    "weeks": _weeks_func,
    "months": _months_func,
    "years": _years_func,
    "now": _now_func,
    "today": _today_func,
    "lunarphase": _lunarphase_func,
    "genvector": _genvector_func,
    "replace": _replace_func,
    "tostring": _tostring_func,
    "length": _length_func,
    "concatenate": _concatenate_func,
    "date": _date_func,
}

# Reverse mapping: SymPy function class → function name string
_SP_FUNC_TO_NAME: dict[type, str] = {
    sp.sin: "sin",
    sp.cos: "cos",
    sp.tan: "tan",
    sp.asin: "asin",
    sp.acos: "acos",
    sp.atan: "atan",
    sp.sinh: "sinh",
    sp.cosh: "cosh",
    sp.tanh: "tanh",
    sp.asinh: "asinh",
    sp.acosh: "acosh",
    sp.atanh: "atanh",
    sp.Abs: "abs",
    sp.log: "ln",
    sp.exp: "exp",
    sp.floor: "floor",
    sp.ceiling: "ceil",
    sp.sign: "sign",
    sp.factorial: "factorial",
    sp.gamma: "gamma",
    sp.Mod: "mod",
    sp.Max: "max",
    sp.Min: "min",
    sp.LambertW: "lambertw",
    sp.erf: "erf",
    sp.erfc: "erfc",
    sp.besselj: "besselj",
    sp.bessely: "bessely",
    sp.zeta: "zeta",
    sp.beta: "beta",
    sp.airyai: "airyai",
    sp.airybi: "airybi",
    sp.fresnels: "fresnels",
    sp.fresnelc: "fresnelc",
    sp.digamma: "digamma",
    sp.Heaviside: "heaviside",
    sp.DiracDelta: "dirac",
    sp.atan2: "atan2",
}

# Known symbolic constants
_SYMPY_CONSTANTS: dict[str, sp.Expr] = {
    "pi": sp.pi,
    "\u03c0": sp.pi,
    "e": sp.E,
    "i": sp.I,
    "j": sp.I,
    "inf": sp.oo,
    "infinity": sp.oo,
    "euler": sp.EulerGamma,
    "catalan": sp.Catalan,
    "golden_ratio": sp.GoldenRatio,
    "phi": sp.GoldenRatio,
}


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _number_to_sympy(num: Number | None) -> sp.Expr:
    """Convert a Number to a SymPy expression."""
    if num is None:
        return sp.Symbol("undefined")
    if num.is_plus_infinity():
        return sp.oo
    if num.is_minus_infinity():
        return -sp.oo
    if num.is_complex():
        real = _number_to_sympy(num.real_part())
        imag = _number_to_sympy(num.imaginary_part())
        return real + sp.I * imag
    if num.is_rational():
        p = int(num._rational.numerator)
        q = int(num._rational.denominator)
        return sp.Rational(p, q)
    # Float type — detect known constants that lost their symbolic form
    f = num.to_float()
    _E_TOL = 2.718281828459045
    _PI_TOL = 3.141592653589793
    if abs(f - _E_TOL) / _E_TOL < 1e-10:
        return sp.E
    if abs(f - _PI_TOL) / _PI_TOL < 1e-10:
        return sp.pi
    _GOLDEN_RATIO_VAL = 1.618033988749895
    _CATALAN_VAL = 0.9159655941772190
    _EULER_GAMMA_VAL = 0.5772156649015329
    if abs(f - _GOLDEN_RATIO_VAL) / _GOLDEN_RATIO_VAL < 1e-10:
        return sp.GoldenRatio
    if abs(f - _CATALAN_VAL) / _CATALAN_VAL < 1e-10:
        return sp.Catalan
    if abs(f - _EULER_GAMMA_VAL) / _EULER_GAMMA_VAL < 1e-10:
        return sp.EulerGamma
    return sp.Float(f)


def _apply_sympy_function(name: str, args: list[sp.Expr]) -> sp.Expr:
    """Apply a named function to SymPy arguments."""
    name_lower = name.lower()
    func = _SYMPY_FUNC_MAP.get(name_lower)
    if func is not None:
        try:
            return func(*args)
        except Exception:
            return sp.Symbol(f"{name}({', '.join(str(a) for a in args)})")
    # Special handling for diff — use Derivative to preserve symbolic form
    if name_lower == "diff":
        if len(args) >= 2:
            return sp.Derivative(args[0], *args[1:])
        elif len(args) == 1:
            return sp.Derivative(args[0], sp.Symbol('x'))
    # Unknown function — create an undefined SymPy function
    f = sp.Function(name)
    return f(*args)


class MathStructure:
    """A structure representing a mathematical value/expression/result.

    Can be a container (addition, multiplication, power, function, comparison,
    vector, etc.) with ordered children, or a leaf value (number, variable,
    unit, symbolic text, undefined).

    Container types:
    - Addition: terms (x + y + ...)
    - Multiplication: factors (x * y * ...)
    - Power: base and exponent (x ^ y)
    - Function: function reference + arguments
    - Comparison: two expressions with a comparison sign

    Value types:
    - Number: rational, float, complex, or infinite
    - Variable: reference to a Variable object
    - Unit: reference to a Unit object
    - Symbolic: text string
    - Undefined: undefined value
    """

    __slots__ = (
        "_type", "_number", "_unit", "_prefix", "_variable", "_function",
        "_symbol", "_children", "_comparison_type", "_datetime",
        "_number_fraction_format", "_error_message",
    )

    def __init__(
        self,
        value: int | float | str | Number | None = None,
        struct_type: StructureType | None = None,
    ) -> None:
        """Create a MathStructure.

        Args:
            value: Initial value (int, float, string, Number, or None for undefined).
            struct_type: Explicit structure type (auto-detected if None).
        """
        self._type = StructureType.UNDEFINED
        self._number: Number | None = None
        self._unit: Unit | None = None
        self._prefix: object | None = None
        self._variable: Variable | None = None
        self._function: MathFunction | None = None
        self._symbol: str = ""
        self._children: list[MathStructure] = []
        self._comparison_type: ComparisonType | None = None
        self._datetime: object | None = None
        self._number_fraction_format: NumberFractionFormat | None = None
        self._error_message: str | None = None

        if struct_type is not None:
            self._type = struct_type
        elif value is not None:
            if isinstance(value, (int, float)):
                self._number = Number(value)
                self._type = StructureType.NUMBER
            elif isinstance(value, Number):
                self._number = value
                self._type = StructureType.NUMBER
            elif isinstance(value, str):
                self._symbol = value
                self._type = StructureType.SYMBOLIC

    # -- Factory constructors --

    @classmethod
    def from_number(cls, number: Number) -> MathStructure:
        m = cls()
        m._number = number
        m._type = StructureType.NUMBER
        return m

    @classmethod
    def from_variable(cls, variable: Variable) -> MathStructure:
        m = cls()
        m._variable = variable
        m._type = StructureType.VARIABLE
        return m

    @classmethod
    def from_unit(cls, unit: Unit, prefix: object = None) -> MathStructure:
        m = cls()
        m._unit = unit
        m._prefix = prefix
        m._type = StructureType.UNIT
        return m

    @classmethod
    def from_symbol(cls, symbol: str) -> MathStructure:
        m = cls()
        m._symbol = symbol
        m._type = StructureType.SYMBOLIC
        return m

    @classmethod
    def undefined(cls, message: str | None = None) -> MathStructure:
        m = cls(struct_type=StructureType.UNDEFINED)
        if message is not None:
            m._error_message = message
        return m

    @classmethod
    def addition(cls, *children: MathStructure) -> MathStructure:
        m = cls(struct_type=StructureType.ADDITION)
        m._children = list(children)
        return m

    @classmethod
    def multiplication(cls, *children: MathStructure) -> MathStructure:
        m = cls(struct_type=StructureType.MULTIPLICATION)
        m._children = list(children)
        return m

    @classmethod
    def power(cls, base: MathStructure, exponent: MathStructure) -> MathStructure:
        m = cls(struct_type=StructureType.POWER)
        m._children = [base, exponent]
        return m

    @classmethod
    def comparison(
        cls,
        left: MathStructure,
        right: MathStructure,
        comp_type: ComparisonType,
    ) -> MathStructure:
        m = cls(struct_type=StructureType.COMPARISON)
        m._children = [left, right]
        m._comparison_type = comp_type
        return m

    @classmethod
    def vector(cls, *elements: MathStructure) -> MathStructure:
        m = cls(struct_type=StructureType.VECTOR)
        m._children = list(elements)
        return m

    @classmethod
    def matrix(cls, rows: list[MathStructure]) -> MathStructure:
        """Create a matrix (vector of row-vectors)."""
        m = cls(struct_type=StructureType.MATRIX)
        m._children = list(rows)
        return m

    @classmethod
    def assignment(cls, name: MathStructure, value: MathStructure) -> MathStructure:
        m = cls(struct_type=StructureType.ASSIGNMENT)
        m._children = [name, value]
        return m

    @classmethod
    def unit_conversion(cls, value: MathStructure, target: MathStructure) -> MathStructure:
        m = cls(struct_type=StructureType.UNIT_CONVERSION)
        m._children = [value, target]
        return m

    @classmethod
    def factorial(cls, operand: MathStructure) -> MathStructure:
        m = cls(struct_type=StructureType.FACTORIAL)
        m._children = [operand]
        return m

    @classmethod
    def where_clause(cls, expr: MathStructure, conditions: list[MathStructure]) -> MathStructure:
        m = cls(struct_type=StructureType.WHERE)
        m._children = [expr] + list(conditions)
        return m

    # ------------------------------------------------------------------
    # SymPy conversion
    # ------------------------------------------------------------------

    def to_sympy(self) -> sp.Expr:
        """Convert this MathStructure to a SymPy expression."""
        if self._type == StructureType.NUMBER:
            return _number_to_sympy(self._number)

        if self._type == StructureType.SYMBOLIC:
            name = self._symbol.strip()
            lower = name.lower()
            if lower in _SYMPY_CONSTANTS:
                return _SYMPY_CONSTANTS[lower]
            return sp.Symbol(name)

        if self._type == StructureType.UNIT and self._unit is not None:
            # Units used in symbolic contexts (e.g., calculus variables)
            # are converted to SymPy symbols by name
            return sp.Symbol(self._unit.name())

        if self._type == StructureType.VARIABLE:
            if self._variable is not None:
                # Check if variable name maps to a SymPy constant
                var_name = self._variable.name().lower()
                if var_name in _SYMPY_CONSTANTS:
                    return _SYMPY_CONSTANTS[var_name]
                if hasattr(self._variable, "is_known") and self._variable.is_known():
                    get_fn = getattr(self._variable, "get", None)
                    if get_fn is not None:
                        val = get_fn()
                        if val is not None:
                            return val.to_sympy()
                    # Handle expression-based known variables
                    expr_fn = getattr(self._variable, "expression", None)
                    if expr_fn is not None:
                        expr_str = expr_fn()
                        if expr_str:
                            # Try to parse using the calculator if available
                            try:
                                from pyqalculate.calculator import _calculator
                                if _calculator is not None:
                                    parsed = _calculator.parse(expr_str)
                                    return parsed.to_sympy()
                            except Exception:
                                pass
                            # Fallback to direct SymPy parsing
                            try:
                                sympy_str = expr_str.replace("^", "**")
                                return sp.sympify(sympy_str)
                            except Exception:
                                pass
                return sp.Symbol(self._variable.name())
            return sp.Symbol("unknown")

        if self._type == StructureType.FUNCTION:
            name = self._symbol
            if not name and self._function is not None:
                name = self._function.name()
            sympy_args = [c.to_sympy() for c in self._children]
            return _apply_sympy_function(name, sympy_args)

        if self._type == StructureType.ADDITION:
            return sp.Add(*[c.to_sympy() for c in self._children])

        if self._type == StructureType.MULTIPLICATION:
            return sp.Mul(*[c.to_sympy() for c in self._children])

        if self._type == StructureType.POWER and len(self._children) == 2:
            return sp.Pow(self._children[0].to_sympy(), self._children[1].to_sympy())

        # MATRIX → SymPy ImmutableDenseMatrix
        if self._type == StructureType.MATRIX:
            rows = []
            for row in self._children:
                if row.is_vector():
                    rows.append([c.to_sympy() for c in row])
                else:
                    rows.append([row.to_sympy()])
            return sp.Matrix(rows)

        # VECTOR → SymPy column vector (Matrix with one column)
        if self._type == StructureType.VECTOR:
            # Check if all children are vectors (i.e., this is a matrix)
            if self._children and all(c.is_vector() for c in self._children):
                rows = [[c.to_sympy() for c in row] for row in self._children]
                return sp.Matrix(rows)
            return sp.Matrix([c.to_sympy() for c in self._children])

        if self._type == StructureType.NEGATE and self._children:
            return -self._children[0].to_sympy()

        if self._type == StructureType.INVERSE and self._children:
            return sp.Pow(self._children[0].to_sympy(), -1)

        if self._type == StructureType.FACTORIAL and self._children:
            return sp.factorial(self._children[0].to_sympy())

        # Comparison / equation
        if self._type == StructureType.COMPARISON and len(self._children) == 2:
            lhs = self._children[0].to_sympy()
            rhs = self._children[1].to_sympy()
            ct = self._comparison_type
            if ct == ComparisonType.EQUALS:
                return sp.Eq(lhs, rhs)
            if ct == ComparisonType.LESS:
                return sp.StrictLessThan(lhs, rhs)
            if ct == ComparisonType.GREATER:
                return sp.StrictGreaterThan(lhs, rhs)
            if ct == ComparisonType.EQUALS_LESS:
                return sp.LessThan(lhs, rhs)
            if ct == ComparisonType.EQUALS_GREATER:
                return sp.GreaterThan(lhs, rhs)
            if ct == ComparisonType.NOT_EQUALS:
                return sp.Ne(lhs, rhs)
            return sp.Eq(lhs, rhs)

        # WHERE clause: evaluate the main expression (conditions are advisory)
        if self._type == StructureType.WHERE and self._children:
            return self._children[0].to_sympy()

        # Bitwise operations
        if self._type == StructureType.BITWISE_AND and len(self._children) == 2:
            return sp.Integer(int(self._children[0].to_sympy()) & int(self._children[1].to_sympy()))
        if self._type == StructureType.BITWISE_OR and len(self._children) == 2:
            return sp.Integer(int(self._children[0].to_sympy()) | int(self._children[1].to_sympy()))
        if self._type == StructureType.BITWISE_XOR and len(self._children) == 2:
            return sp.Integer(int(self._children[0].to_sympy()) ^ int(self._children[1].to_sympy()))

        # Fallback
        return sp.Symbol("unsupported")

    @classmethod
    def from_sympy(cls, expr: Any) -> MathStructure:
        """Create a MathStructure from a SymPy expression."""
        # Special constants
        if expr == sp.pi:
            return cls.from_symbol("pi")
        if expr == sp.E:
            return cls.from_symbol("e")
        if expr == sp.I:
            return cls.from_symbol("i")
        if expr == sp.oo:
            return cls.from_number(Number.plus_inf())
        if expr == -sp.oo:
            return cls.from_number(Number.minus_inf())
        if expr == sp.zoo:
            return cls.undefined()
        if expr is sp.nan:
            return cls.undefined()
        if hasattr(expr, 'is_nan') and expr.is_nan:
            return cls.undefined()

        # Numbers
        if isinstance(expr, sp.Integer):
            return cls(int(expr))
        if isinstance(expr, sp.Rational):
            return cls.from_number(Number.from_rational(int(expr.p), int(expr.q)))
        if isinstance(expr, sp.Float):
            return cls(float(expr))

        # Matrix (from SymPy)
        if isinstance(expr, sp.Matrix):
            mat = expr
            if mat.cols == 1:
                # Column vector → matrix of single-element rows
                rows = [cls.vector(cls.from_sympy(mat[i, 0])) for i in range(mat.rows)]
                return cls.matrix(rows)
            rows = []
            for i in range(mat.rows):
                row_elems = [cls.from_sympy(mat[i, j]) for j in range(mat.cols)]
                rows.append(cls.vector(*row_elems))
            return cls.matrix(rows)

        # Symbol
        if isinstance(expr, sp.Symbol):
            name = str(expr)
            lower = name.lower()
            if lower in _SYMPY_CONSTANTS:
                return cls.from_symbol(lower)
            return cls.from_symbol(name)

        # Add
        if isinstance(expr, sp.Add):
            children = [cls.from_sympy(arg) for arg in expr.args]  # type: ignore[arg-type]
            result = children[0]
            for c in children[1:]:
                result = result + c
            return result

        # Mul
        if isinstance(expr, sp.Mul):
            children = [cls.from_sympy(arg) for arg in expr.args]  # type: ignore[arg-type]
            result = children[0]
            for c in children[1:]:
                result = result * c
            return result

        # Pow
        if isinstance(expr, sp.Pow) and len(expr.args) == 2:
            base = cls.from_sympy(expr.args[0])
            exp = cls.from_sympy(expr.args[1])
            return base ** exp

        # Relational (Eq, Ne, Lt, Gt, Le, Ge)
        if isinstance(expr, sp.Equality):
            return cls.comparison(
                cls.from_sympy(expr.lhs), cls.from_sympy(expr.rhs), ComparisonType.EQUALS)
        if isinstance(expr, sp.Unequality):
            return cls.comparison(
                cls.from_sympy(expr.lhs), cls.from_sympy(expr.rhs), ComparisonType.NOT_EQUALS)
        if isinstance(expr, sp.StrictLessThan):
            return cls.comparison(
                cls.from_sympy(expr.lhs), cls.from_sympy(expr.rhs), ComparisonType.LESS)
        if isinstance(expr, sp.StrictGreaterThan):
            return cls.comparison(
                cls.from_sympy(expr.lhs), cls.from_sympy(expr.rhs), ComparisonType.GREATER)
        if isinstance(expr, sp.LessThan):
            return cls.comparison(
                cls.from_sympy(expr.lhs), cls.from_sympy(expr.rhs), ComparisonType.EQUALS_LESS)
        if isinstance(expr, sp.GreaterThan):
            return cls.comparison(
                cls.from_sympy(expr.lhs), cls.from_sympy(expr.rhs), ComparisonType.EQUALS_GREATER)

        # Derivative — represent as diff(y, x[, n])
        if isinstance(expr, sp.Derivative):
            m = cls(struct_type=StructureType.FUNCTION)
            m._symbol = "diff"
            # expr.args is (func, (var, order), (var2, order2), ...)
            children = [cls.from_sympy(expr.args[0])]
            for deriv_arg in expr.args[1:]:
                if isinstance(deriv_arg, sp.Tuple) and len(deriv_arg) == 2:
                    children.append(cls.from_sympy(deriv_arg[0]))  # variable
                    order = deriv_arg[1]
                    if order != 1:
                        children.append(cls.from_sympy(order))  # order when > 1
                else:
                    children.append(cls.from_sympy(deriv_arg))
            m._children = children
            return m

        # Known function types
        func_name = _SP_FUNC_TO_NAME.get(expr.func)
        if func_name and hasattr(expr, "args"):
            m = cls(struct_type=StructureType.FUNCTION)
            m._symbol = func_name
            m._children = [cls.from_sympy(arg) for arg in expr.args]
            return m

        # Generic SymPy function (undefined function applied)
        if hasattr(expr, "func") and hasattr(expr, "args"):
            func_obj = expr.func
            if isinstance(func_obj, sp.core.function.UndefinedFunction):
                m = cls(struct_type=StructureType.FUNCTION)
                m._symbol = str(func_obj)
                m._children = [cls.from_sympy(arg) for arg in expr.args]
                return m
            # sqrt is sometimes represented as Pow(x, Rational(1,2))
            # which we already handle above in Pow

        # Fallback
        return cls.from_symbol(str(expr))

    # -- Properties --

    @property
    def type(self) -> StructureType:
        return self._type

    @property
    def number(self) -> Number | None:
        return self._number

    @property
    def unit(self) -> Unit | None:
        return self._unit

    @property
    def variable(self) -> Variable | None:
        return self._variable

    @property
    def function(self) -> MathFunction | None:
        return self._function

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def comparison_type(self) -> ComparisonType | None:
        return self._comparison_type

    # -- Children --

    def __len__(self) -> int:
        return len(self._children)

    def __getitem__(self, index: int) -> MathStructure:
        return self._children[index]

    def __iter__(self):
        return iter(self._children)

    def append_child(self, child: MathStructure) -> None:
        self._children.append(child)

    def insert_child(self, index: int, child: MathStructure) -> None:
        self._children.insert(index, child)

    def del_child(self, index: int) -> None:
        del self._children[index]

    def clear_children(self) -> None:
        self._children.clear()

    @property
    def size(self) -> int:
        return len(self._children)

    # -- Type checks --

    def is_number(self) -> bool:
        return self._type == StructureType.NUMBER

    def is_symbolic(self) -> bool:
        return self._type == StructureType.SYMBOLIC

    def is_unit(self) -> bool:
        return self._type == StructureType.UNIT

    def is_variable(self) -> bool:
        return self._type == StructureType.VARIABLE

    def is_function(self) -> bool:
        return self._type == StructureType.FUNCTION

    def is_addition(self) -> bool:
        return self._type == StructureType.ADDITION

    def is_multiplication(self) -> bool:
        return self._type == StructureType.MULTIPLICATION

    def is_power(self) -> bool:
        return self._type == StructureType.POWER

    def is_comparison(self) -> bool:
        return self._type == StructureType.COMPARISON

    def is_vector(self) -> bool:
        return self._type == StructureType.VECTOR

    def is_undefined(self) -> bool:
        return self._type == StructureType.UNDEFINED

    def is_assignment(self) -> bool:
        return self._type == StructureType.ASSIGNMENT

    def is_matrix(self) -> bool:
        return self._type == StructureType.MATRIX

    def is_factorial(self) -> bool:
        return self._type == StructureType.FACTORIAL

    def is_where(self) -> bool:
        return self._type == StructureType.WHERE

    def is_unit_conversion(self) -> bool:
        return self._type == StructureType.UNIT_CONVERSION

    def has_unit_conversion(self) -> bool:
        """Check if this structure or any child has a unit conversion."""
        if self._type == StructureType.UNIT_CONVERSION:
            return True
        return any(c.has_unit_conversion() for c in self._children)

    def is_zero(self) -> bool:
        return self.is_number() and self._number is not None and self._number.is_zero()

    def is_one(self) -> bool:
        return self.is_number() and self._number is not None and self._number.is_one()

    def is_minus_one(self) -> bool:
        if not self.is_number() or self._number is None:
            return False
        return self._number == Number(-1)

    def is_negative(self) -> bool:
        return self.is_number() and self._number is not None and self._number.is_negative()

    def is_positive(self) -> bool:
        return self.is_number() and self._number is not None and self._number.is_positive()

    def is_integer(self) -> bool:
        return self.is_number() and self._number is not None and self._number.is_integer()

    # -- Represents checks (simplified) --

    def represents_positive(self, allow_units: bool = False) -> bool:
        return self.is_positive()

    def represents_negative(self, allow_units: bool = False) -> bool:
        return self.is_negative()

    def represents_non_negative(self, allow_units: bool = False) -> bool:
        return self.is_number() and self._number is not None and not self._number.is_negative()

    def represents_integer(self, allow_units: bool = False) -> bool:
        return self.is_integer()

    def represents_number(self, allow_units: bool = False) -> bool:
        return self.is_number()

    def represents_real(self, allow_units: bool = False) -> bool:
        return self.is_number() and not (self._number is not None and self._number.is_complex())

    def represents_non_zero(self, allow_units: bool = False) -> bool:
        return self.is_number() and not self.is_zero()

    def represents_non_matrix(self) -> bool:
        return not self.is_vector() or all(c.is_number() for c in self._children)

    def represents_scalar(self) -> bool:
        return not self.is_vector()

    def represents_boolean(self) -> bool:
        return False

    # -- Value access --

    def number_value(self) -> Number | None:
        """Return the Number value if this is a number structure."""
        return self._number

    def float_value(self) -> float:
        """Return the float value if this is a number structure."""
        if self._number is not None:
            return self._number.to_float()
        return 0.0

    # -- Structural operations --

    def negate(self) -> MathStructure:
        """Return negation of this structure."""
        if self.is_number() and self._number is not None:
            return MathStructure.from_number(-self._number)
        m = MathStructure(struct_type=StructureType.NEGATE)
        m._children = [self]
        return m

    def inverse(self) -> MathStructure:
        """Return the inverse (1/x)."""
        m = MathStructure(struct_type=StructureType.INVERSE)
        m._children = [self]
        return m

    def __add__(self, other: MathStructure) -> MathStructure:
        if self.is_undefined() or other.is_undefined():
            return MathStructure.undefined()
        if self.is_zero():
            return other
        if other.is_zero():
            return self
        return MathStructure.addition(self, other)

    def __sub__(self, other: MathStructure) -> MathStructure:
        if self.is_undefined() or other.is_undefined():
            return MathStructure.undefined()
        return self + other.negate()

    def __mul__(self, other: MathStructure) -> MathStructure:
        if self.is_undefined() or other.is_undefined():
            return MathStructure.undefined()
        if self.is_zero() and not other.is_unit():
            return MathStructure(0)
        if other.is_zero() and not self.is_unit():
            return MathStructure(0)
        if self.is_one():
            return other
        if other.is_one():
            return self
        return MathStructure.multiplication(self, other)

    def __truediv__(self, other: MathStructure) -> MathStructure:
        if other.is_zero():
            return MathStructure.undefined()
        return self * other.inverse()

    def __pow__(self, other: MathStructure) -> MathStructure:
        if other.is_one():
            return self
        if other.is_zero():
            return MathStructure(1)
        return MathStructure.power(self, other)

    def __neg__(self) -> MathStructure:
        return self.negate()

    # ------------------------------------------------------------------
    # Evaluation via SymPy
    # ------------------------------------------------------------------

    @staticmethod
    def _is_unit_power(node: "MathStructure") -> bool:
        """Check if node is POWER(UNIT, NUMBER) — a unit raised to a numeric power."""
        return (node._type == StructureType.POWER
                and len(node._children) == 2
                and node._children[0]._type == StructureType.UNIT
                and node._children[1]._type == StructureType.NUMBER)

    @staticmethod
    def _extract_unit_exponents(node: "MathStructure") -> dict[str, float] | None:
        """Recursively extract unit-name → total-exponent mapping from a node.

        Handles nested MULTIPLICATION, POWER(UNIT, n), POWER(POWER(UNIT,n), m),
        INVERSE(MULTIPLICATION(...)), and plain UNIT nodes.
        Returns None if no units found.
        """

        def _walk(n: "MathStructure", sign: float, acc: dict[str, float]) -> None:
            if n._type == StructureType.UNIT and n._unit is not None:
                name = n._unit.name()
                acc[name] = acc.get(name, 0.0) + sign
            elif n._type == StructureType.POWER and len(n._children) == 2:
                base, exp_node = n._children[0], n._children[1]
                # Case 1: POWER(UNIT, NUMBER) — direct unit^exponent
                if (base._type == StructureType.UNIT
                        and base._unit is not None
                        and exp_node._type == StructureType.NUMBER
                        and exp_node._number is not None):
                    name = base._unit.name()
                    exp_val = exp_node._number.to_float()
                    acc[name] = acc.get(name, 0.0) + sign * exp_val
                # Case 2: POWER(POWER(UNIT, n), m) — nested power simplification
                # e.g., (s^2)^0.5 → s^(2*0.5) = s^1 = s
                elif (base._type == StructureType.POWER
                      and len(base._children) == 2
                      and base._children[0]._type == StructureType.UNIT
                      and base._children[0]._unit is not None
                      and base._children[1]._type == StructureType.NUMBER
                      and base._children[1]._number is not None
                      and exp_node._type == StructureType.NUMBER
                      and exp_node._number is not None):
                    name = base._children[0]._unit.name()
                    inner_exp = base._children[1]._number.to_float()
                    outer_exp = exp_node._number.to_float()
                    acc[name] = acc.get(name, 0.0) + sign * inner_exp * outer_exp
                else:
                    # Non-unit power — try to extract from base (e.g., sqrt of expression)
                    extracted = MathStructure._extract_unit_exponents(base)
                    if extracted is not None and exp_node._type == StructureType.NUMBER and exp_node._number is not None:
                        exp_val = exp_node._number.to_float()
                        for uname, uexp in extracted.items():
                            acc[uname] = acc.get(uname, 0.0) + sign * uexp * exp_val
            elif n._type == StructureType.MULTIPLICATION:
                for child in n._children:
                    _walk(child, sign, acc)
            elif n._type == StructureType.INVERSE and n._children:
                _walk(n._children[0], -sign, acc)

        acc: dict[str, float] = {}
        _walk(node, 1.0, acc)
        return acc if acc else None

    @staticmethod
    def _rebuild_units_from_exponents(
        exponents: dict[str, float],
        unit_sources: "dict[str, Unit] | None" = None,
    ) -> list["MathStructure"]:
        """Rebuild unit MathStructure nodes from a name→exponent mapping.

        Args:
            exponents: Mapping of unit name → total exponent.
            unit_sources: Optional mapping of unit name → original Unit object.
                When provided, the original unit is reused instead of creating
                a new bare Unit, preserving alias chains and metadata.

        Returns a list of UNIT or POWER(UNIT, exp) nodes, skipping exponent 0.
        Exponent 1 produces a plain UNIT node; other values produce POWER(UNIT, exp).
        """
        from pyqalculate.unit import Unit
        if unit_sources is None:
            unit_sources = {}
        result: list[MathStructure] = []
        for name, exp_val in sorted(exponents.items()):
            if abs(exp_val) < 1e-12:
                continue  # unit^0 = 1, omit
            unit_node = MathStructure(struct_type=StructureType.UNIT)
            # Reuse the original unit object when available to preserve
            # alias chains (AliasUnit → base CompositeUnit) and metadata.
            original_unit = unit_sources.get(name)
            if original_unit is not None:
                unit_node._unit = original_unit
            else:
                unit_node._unit = Unit(name=name, is_local=False, is_builtin=True)
                unit_node._unit.add_name(name)
            if abs(exp_val - 1.0) < 1e-12:
                result.append(unit_node)
            else:
                exp_node = MathStructure(Number(exp_val))
                power_node = MathStructure(struct_type=StructureType.POWER)
                power_node._children = [unit_node, exp_node]
                result.append(power_node)
        return result

    @staticmethod
    def _collect_unit_sources(node: "MathStructure", acc: "dict[str, Unit]") -> None:
        """Walk a MathStructure tree and collect unit name → original Unit object.

        This preserves the original Unit (which may be an AliasUnit with a full
        alias chain) so that _rebuild_units_from_exponents can reuse it instead of
        creating a bare Unit that loses alias metadata.
        """
        if node._type == StructureType.UNIT and node._unit is not None:
            name = node._unit.name()
            if name not in acc:
                acc[name] = node._unit
        elif node._type == StructureType.POWER and len(node._children) == 2:
            base = node._children[0]
            if base._type == StructureType.UNIT and base._unit is not None:
                name = base._unit.name()
                if name not in acc:
                    acc[name] = base._unit
            elif base._type == StructureType.POWER and len(base._children) == 2:
                inner = base._children[0]
                if inner._type == StructureType.UNIT and inner._unit is not None:
                    name = inner._unit.name()
                    if name not in acc:
                        acc[name] = inner._unit
        elif node._type == StructureType.MULTIPLICATION:
            for child in node._children:
                MathStructure._collect_unit_sources(child, acc)
        elif node._type == StructureType.INVERSE and node._children:
            MathStructure._collect_unit_sources(node._children[0], acc)

    @staticmethod
    def _extract_numeric_coefficient(node: "MathStructure") -> float:
        """Extract the numeric coefficient from a factor containing units.

        Walks the expression tree and multiplies all NUMBER nodes, applying
        sign inversion for INVERSE nodes, while treating UNIT and
        POWER(UNIT, exp) nodes as coefficient 1.

        Examples:
            INVERSE(MULTIPLICATION(12, min)) → 1/12 ≈ 0.08333
            MULTIPLICATION(3.5, mi)          → 3.5
            INVERSE(UNIT(min))               → 1.0
        """
        if node._type == StructureType.NUMBER:
            return node._number.to_float() if node._number is not None else 1.0
        if node._type == StructureType.MULTIPLICATION:
            result = 1.0
            for c in node._children:
                result *= MathStructure._extract_numeric_coefficient(c)
            return result
        if node._type == StructureType.INVERSE and node._children:
            inner = MathStructure._extract_numeric_coefficient(node._children[0])
            return 1.0 / inner if inner != 0 else 1.0
        if node._type == StructureType.UNIT:
            return 1.0
        if node._type == StructureType.POWER and len(node._children) == 2:
            # POWER(UNIT, exp) — unit power, numeric coeff is 1.0
            if node._children[0]._type == StructureType.UNIT:
                return 1.0
        return 1.0

    def _simplify_unit_mul(self) -> "MathStructure | None":
        """Simplify a multiplication that contains units.

        Flattens nested multiplications, collects numeric coefficients,
        handles POWER(UNIT, exp) nodes, merges exponents for matching base
        units, removes units with exponent 0 (they become 1), and simplifies
        remaining powers.

        Returns None if no simplification was possible (no units found).
        """
        if self._type != StructureType.MULTIPLICATION:
            return None

        # Collect all factors by flattening nested multiplications
        factors: list[MathStructure] = []
        def _collect(node: MathStructure) -> None:
            if node._type == StructureType.MULTIPLICATION:
                for c in node._children:
                    _collect(c)
            else:
                factors.append(node)
        _collect(self)

        # Check if any factor contains units (handles nested POWER, INVERSE, etc.)
        has_unit = False
        for f in factors:
            if f._type == StructureType.UNIT:
                has_unit = True
                break
            if self._extract_unit_exponents(f) is not None:
                has_unit = True
                break
        if not has_unit:
            return None

        # Separate numeric parts, unit parts, and other parts
        numeric_parts: list[MathStructure] = []
        unit_exponents: dict[str, float] = {}
        unit_sources: "dict[str, Unit]" = {}  # name → original Unit object
        other_parts: list[MathStructure] = []

        for f in factors:
            if f._type == StructureType.NUMBER:
                numeric_parts.append(f)
                continue

            # Try to extract unit exponents from this factor
            extracted = self._extract_unit_exponents(f)
            if extracted is not None:
                for name, exp_val in extracted.items():
                    unit_exponents[name] = unit_exponents.get(name, 0.0) + exp_val
                # Collect original unit objects to preserve alias chains
                self._collect_unit_sources(f, unit_sources)
                # Also extract numeric coefficients hidden inside this factor.
                # e.g., INVERSE(MULTIPLICATION(12, min)) has a 12 that
                # _extract_unit_exponents ignores but must be preserved.
                num_coeff = self._extract_numeric_coefficient(f)
                if abs(num_coeff - 1.0) > 1e-15:
                    numeric_parts.append(MathStructure.from_number(Number(num_coeff)))
            else:
                other_parts.append(f)

        # Rebuild simplified unit nodes, reusing original unit objects
        rebuilt_units = self._rebuild_units_from_exponents(unit_exponents, unit_sources)

        # Multiply numeric parts together
        combined_num: MathStructure | None = None
        if len(numeric_parts) > 1:
            result_num = numeric_parts[0]._number
            for np in numeric_parts[1:]:
                if np._number is not None and result_num is not None:
                    result_num = result_num * np._number
            if result_num is not None:
                combined_num = MathStructure.from_number(result_num)
        elif len(numeric_parts) == 1:
            combined_num = numeric_parts[0]

        # Assemble final parts
        final_parts: list[MathStructure] = []
        if combined_num is not None:
            final_parts.append(combined_num)
        final_parts.extend(rebuilt_units)
        final_parts.extend(other_parts)

        if not final_parts:
            return MathStructure(1)
        if len(final_parts) == 1:
            return final_parts[0]
        m = MathStructure(struct_type=StructureType.MULTIPLICATION)
        m._children = final_parts
        return m

    def _flatten_same_type(self) -> "MathStructure":
        """Flatten nested structures of the same type (e.g. nested additions).

        Turns ADDITION(ADDITION(a,b), c) into ADDITION(a,b,c).
        Only flattens one level of nesting for the same type.
        """
        target_type = self._type
        if target_type not in (StructureType.ADDITION, StructureType.MULTIPLICATION):
            return self
        flattened: list[MathStructure] = []
        changed = False
        for child in self._children:
            if child._type == target_type:
                flattened.extend(child._children)
                changed = True
            else:
                flattened.append(child)
        if not changed:
            return self
        result = MathStructure(struct_type=target_type)
        result._children = flattened
        return result

    def _is_sympy_evaluable(self) -> bool:
        """Check if this node can be converted to a SymPy expression.

        Returns True for numbers, known SymPy constants (i, pi, e),
        and compound expressions where all leaves are evaluable.
        """
        if self._type == StructureType.NUMBER:
            return True
        if self._type == StructureType.SYMBOLIC:
            lower = self._symbol.strip().lower() if self._symbol else ""
            return lower in _SYMPY_CONSTANTS
        if self._type in (StructureType.ADDITION, StructureType.MULTIPLICATION):
            return all(c._is_sympy_evaluable() for c in self._children)
        if self._type == StructureType.POWER and len(self._children) == 2:
            return (self._children[0]._is_sympy_evaluable()
                    and self._children[1]._is_sympy_evaluable())
        if self._type == StructureType.NEGATE and self._children:
            return self._children[0]._is_sympy_evaluable()
        if self._type == StructureType.INVERSE and self._children:
            return self._children[0]._is_sympy_evaluable()
        if self._type == StructureType.FUNCTION:
            return all(c._is_sympy_evaluable() for c in self._children)
        return False

    def _has_interval_number(self) -> bool:
        """Check if this structure or any descendant has an interval number."""
        if self._type == StructureType.NUMBER and self._number is not None:
            return self._number.is_interval()
        return any(c._has_interval_number() for c in self._children)

    def _has_unit(self) -> bool:
        """Check if this structure or any descendant is a unit."""
        if self._type == StructureType.UNIT:
            return True
        return any(c._has_unit() for c in self._children)

    def _eval_interval_arithmetic(self) -> "MathStructure | None":
        """Try to evaluate using Number arithmetic for interval propagation.

        Returns a MathStructure result, or None if not evaluable as pure arithmetic.
        """
        if self._type == StructureType.NUMBER:
            return self.format()

        # Handle symbolic constants (pi, e, etc.) by converting to number
        if self._type == StructureType.SYMBOLIC:
            lower = self._symbol.strip().lower() if self._symbol else ""
            if lower in _SYMPY_CONSTANTS:
                try:
                    val = float(sp.N(_SYMPY_CONSTANTS[lower], 15))
                    return MathStructure(Number(val))
                except Exception:
                    pass
            return None

        if self._type == StructureType.ADDITION:
            result = self._children[0]._eval_interval_arithmetic()
            if result is None or not result.is_number():
                return None
            for c in self._children[1:]:
                r = c._eval_interval_arithmetic()
                if r is None or not r.is_number():
                    return None
                result = MathStructure.from_number(result.number + r.number)
            return result

        if self._type == StructureType.NEGATE and self._children:
            child = self._children[0]._eval_interval_arithmetic()
            if child is not None and child.is_number() and child.number is not None:
                return MathStructure.from_number(-child.number)
            return None

        if self._type == StructureType.MULTIPLICATION:
            # Check if this multiplication has units anywhere in the tree
            has_unit = self._has_unit()
            has_interval = self._has_interval_number()
            
            if has_unit and has_interval:
                # Try to separate numeric and unit parts for interval propagation
                return self._eval_interval_with_units()
            
            # Pure numeric path
            result = self._children[0]._eval_interval_arithmetic()
            if result is None or not result.is_number():
                return None
            for c in self._children[1:]:
                r = c._eval_interval_arithmetic()
                if r is None or not r.is_number():
                    return None
                result = MathStructure.from_number(result.number * r.number)
            return result

        if self._type == StructureType.INVERSE and self._children:
            child = self._children[0]._eval_interval_arithmetic()
            if child is not None and child.is_number() and child.number is not None:
                one = Number(1)
                return MathStructure.from_number(one / child.number)
            return None

        if self._type == StructureType.POWER and len(self._children) == 2:
            base = self._children[0]._eval_interval_arithmetic()
            exp = self._children[1]._eval_interval_arithmetic()
            if (base is not None and base.is_number() and base.number is not None
                    and exp is not None and exp.is_number() and exp.number is not None):
                return MathStructure.from_number(base.number ** exp.number)
            return None

        if self._type == StructureType.FACTORIAL and self._children:
            child = self._children[0]._eval_interval_arithmetic()
            if child is not None and child.is_number() and child.number is not None:
                return MathStructure.from_number(child.number.factorial())
            return None

        # Can't evaluate as pure arithmetic
        return None

    def _eval_interval_with_units(self) -> "MathStructure | None":
        """Evaluate a multiplication that contains both intervals and units.
        
        Separates numeric and unit parts, computes the numeric result using
        interval arithmetic, and recombines with the unit parts.
        """
        numeric_parts = []
        other_parts = []
        
        def _extract_parts(node):
            """Recursively extract numeric and non-numeric parts."""
            if node._type == StructureType.NUMBER:
                numeric_parts.append(node.number)
            elif node._type == StructureType.SYMBOLIC:
                # Evaluate known symbolic constants (pi, e, etc.) as numbers
                lower = node._symbol.strip().lower() if node._symbol else ""
                if lower in _SYMPY_CONSTANTS:
                    try:
                        val = float(sp.N(_SYMPY_CONSTANTS[lower], 15))
                        numeric_parts.append(Number(val))
                    except Exception:
                        other_parts.append(node)
                else:
                    other_parts.append(node)
            elif node._type == StructureType.MULTIPLICATION:
                # Extract all numeric-like children, including non-interval numbers
                # and symbolic constants, to combine them with interval arithmetic
                has_num = False
                for child in node._children:
                    if child._type == StructureType.NUMBER:
                        numeric_parts.append(child.number)
                        has_num = True
                    elif child._type == StructureType.SYMBOLIC:
                        lower = child._symbol.strip().lower() if child._symbol else ""
                        if lower in _SYMPY_CONSTANTS:
                            try:
                                val = float(sp.N(_SYMPY_CONSTANTS[lower], 15))
                                numeric_parts.append(Number(val))
                                has_num = True
                            except Exception:
                                pass
                        if not has_num:
                            pass  # will be handled below
                if has_num:
                    # Keep non-numeric parts as a multiplication
                    non_numeric = [c for c in node._children
                                   if c._type != StructureType.NUMBER
                                   and not (c._type == StructureType.SYMBOLIC
                                            and c._symbol and c._symbol.strip().lower() in _SYMPY_CONSTANTS)]
                    if non_numeric:
                        if len(non_numeric) == 1:
                            other_parts.append(non_numeric[0])
                        else:
                            mul_m = MathStructure(struct_type=StructureType.MULTIPLICATION)
                            mul_m._children = non_numeric
                            other_parts.append(mul_m)
                else:
                    # No numeric or constant parts found, try recursion
                    all_have_num = any(
                        c._has_interval_number() for c in node._children
                    )
                    if all_have_num:
                        for child in node._children:
                            _extract_parts(child)
                    else:
                        other_parts.append(node)
            elif node._type == StructureType.INVERSE and len(node._children) == 1:
                inner = node._children[0]
                if inner._type == StructureType.NUMBER:
                    numeric_parts.append(Number(1) / inner.number)
                elif inner._type == StructureType.MULTIPLICATION:
                    # Recursively extract from inverse of multiplication
                    inner_numeric = []
                    inner_other = []
                    
                    def _extract_from_mul(n):
                        if n._type == StructureType.NUMBER:
                            inner_numeric.append(n.number)
                        elif n._type == StructureType.MULTIPLICATION:
                            for child in n._children:
                                _extract_from_mul(child)
                        else:
                            inner_other.append(n)
                    
                    _extract_from_mul(inner)
                    
                    for n in inner_numeric:
                        numeric_parts.append(Number(1) / n)
                    if inner_other:
                        if len(inner_other) == 1:
                            inv_m = MathStructure(struct_type=StructureType.INVERSE)
                            inv_m._children = inner_other
                            other_parts.append(inv_m)
                        else:
                            mul_m = MathStructure(struct_type=StructureType.MULTIPLICATION)
                            mul_m._children = inner_other
                            inv_m = MathStructure(struct_type=StructureType.INVERSE)
                            inv_m._children = [mul_m]
                            other_parts.append(inv_m)
                else:
                    other_parts.append(node)
            else:
                other_parts.append(node)
        
        for child in self._children:
            _extract_parts(child)
        
        # Multiply all numeric parts together
        if not numeric_parts:
            return None
        
        result_num = numeric_parts[0]
        for n in numeric_parts[1:]:
            result_num = result_num * n
        
        if not result_num.is_interval():
            return None
        
        # Combine with non-numeric parts
        result = MathStructure.from_number(result_num)
        if other_parts:
            all_parts = [result] + other_parts
            m = MathStructure(struct_type=StructureType.MULTIPLICATION)
            m._children = all_parts
            return m
        return result

    def evaluate(self, eo: EvaluationOptions | None = None) -> MathStructure:
        """Evaluate this structure. Returns a new MathStructure.

        For FUNCTION structures with a registered MathFunction that is NOT
        in the SymPy function map, tries the function's calculate() method
        first (handles statistics, datetime, base conversion, etc.).
        Falls back to SymPy evaluation for standard math functions.
        """
        if eo is None:
            eo = EvaluationOptions()

        # Undefined stays undefined
        if self._type == StructureType.UNDEFINED:
            return MathStructure.undefined(self._error_message)

        # Leaf types: return as-is (no evaluation needed)
        if self._type in (StructureType.NUMBER, StructureType.UNIT):
            return self

        # VARIABLE: resolve known variables to their numeric values.
        # This handles constants like electron_mass which are defined as
        # expressions referencing other variables (e.g., (2*rydberg*planck)/(c*fine_structure^2)).
        if self._type == StructureType.VARIABLE and self._variable is not None:
            var = self._variable
            # Try direct value first (cached)
            if hasattr(var, 'get'):
                val = var.get()
                if val is not None:
                    return val.evaluate(eo) if hasattr(val, 'evaluate') else val
            # Try expression string and evaluate through calculator
            if hasattr(var, 'expression'):
                expr_str = var.expression()
                if expr_str:
                    try:
                        from pyqalculate.calculator import _calculator
                        if _calculator is not None:
                            parsed = _calculator.parse(expr_str)
                            return parsed.evaluate(eo)
                    except Exception:
                        pass
            return self

        # VECTOR: evaluate each child element, return reconstructed vector
        if self._type == StructureType.VECTOR:
            evaluated_children = [child.evaluate(eo) for child in self._children]
            return MathStructure.vector(*evaluated_children)

        # MATRIX: evaluate each row vector, return reconstructed matrix
        if self._type == StructureType.MATRIX:
            evaluated_rows = [child.evaluate(eo) for child in self._children]
            return MathStructure.matrix(evaluated_rows)

        # DATETIME: return as-is
        if self._type == StructureType.DATETIME:
            return self.format()

        # COMPARISON: evaluate children but preserve the comparison structure
        # (equations/inequalities must not be simplified through SymPy)
        if self._type == StructureType.COMPARISON and len(self._children) == 2:
            left = self._children[0].evaluate(eo)
            right = self._children[1].evaluate(eo)
            ct = self._comparison_type if self._comparison_type is not None else ComparisonType.EQUALS
            return MathStructure.comparison(left, right, ct)

        # WHERE: evaluate main expression, pass through
        if self._type == StructureType.WHERE and self._children:
            return self._children[0].evaluate(eo)

        # Interval arithmetic: if the expression contains interval numbers,
        # use Number arithmetic to propagate intervals correctly
        if self._has_interval_number():
            result = self._eval_interval_arithmetic()
            if result is not None:
                # Apply unit simplification to interval results that contain
                # unsimplified unit expressions (e.g., m^0.5 * (m/s^2)^-0.5)
                if result._type == StructureType.MULTIPLICATION:
                    simplified = result._simplify_unit_mul()
                    if simplified is not None:
                        return simplified
                return result

        # For non-FUNCTION, non-leaf types: recursively evaluate children first,
        # then re-check for interval arithmetic or try SymPy on the evaluated tree
        if self._type in (StructureType.ADDITION, StructureType.MULTIPLICATION,
                          StructureType.POWER, StructureType.NEGATE,
                          StructureType.INVERSE, StructureType.FACTORIAL,
                          StructureType.DIVISION,
                          StructureType.BITWISE_AND, StructureType.BITWISE_OR,
                          StructureType.BITWISE_XOR):
            evaluated_children = [child.evaluate(eo) for child in self._children]
            if any(c.is_undefined() for c in evaluated_children):
                msg = next((c._error_message for c in evaluated_children if c.is_undefined() and c._error_message), None)
                return MathStructure.undefined(msg)
            # Reconstruct with evaluated children
            if self._type == StructureType.ADDITION:
                rebuilt = evaluated_children[0]
                for c in evaluated_children[1:]:
                    rebuilt = rebuilt + c
            elif self._type == StructureType.MULTIPLICATION:
                # Check for matrix/matrix or matrix/vector multiplication via numpy
                has_matrix = any(c.is_matrix() for c in evaluated_children)
                if has_matrix:
                    try:
                        import numpy as np
                        from pyqalculate.builtin_functions import _mstruct_to_ndarray, _ndarray_to_mstruct
                        result_arr = _mstruct_to_ndarray(evaluated_children[0])
                        for c in evaluated_children[1:]:
                            c_arr = _mstruct_to_ndarray(c)
                            result_arr = np.matmul(result_arr, c_arr)
                        return _ndarray_to_mstruct(result_arr)
                    except Exception:
                        pass
                rebuilt = evaluated_children[0]
                for c in evaluated_children[1:]:
                    rebuilt = rebuilt * c
            elif self._type == StructureType.POWER and len(evaluated_children) == 2:
                base, exponent = evaluated_children[0], evaluated_children[1]
                # Handle matrix^-1 (matrix inverse) directly via numpy
                if base.is_matrix() and exponent.is_number() and exponent.number is not None and exponent.number.to_float() == -1.0:
                    try:
                        import numpy as np
                        from pyqalculate.builtin_functions import _mstruct_to_ndarray, _ndarray_to_mstruct
                        arr = _mstruct_to_ndarray(base)
                        if arr.ndim == 2:
                            inv = np.linalg.inv(arr)
                            return _ndarray_to_mstruct(inv)
                    except Exception:
                        pass
                # Complex principal root: when allow_complex=True and we have
                # negative base ^ rational exponent with odd denominator,
                # compute the principal complex root directly via Number.raise_()
                # instead of going through SymPy (which returns the real root
                # or a symbolic form like "3 * cbrt(-1)").
                if (eo.allow_complex
                        and base.is_number() and base._number is not None
                        and base._number.is_negative()
                        and base._number.is_rational()
                        and not base._number.is_complex()
                        and exponent.is_number() and exponent._number is not None
                        and exponent._number.is_rational()
                        and not exponent._number.is_integer()):
                    exp_rat = exponent._number._rational
                    q = int(exp_rat.denominator)
                    if q % 2 != 0:
                        # Odd denominator: principal complex root exists
                        import cmath
                        base_f = base._number.to_float()
                        exp_f = float(exp_rat)
                        val = cmath.exp(complex(exp_f) * cmath.log(complex(base_f)))
                        # Return as Addition(real, imag*i) matching SymPy format
                        real_part = MathStructure.from_number(
                            Number.from_float(val.real))
                        if abs(val.imag) > 1e-15:
                            imag_part = MathStructure.from_number(
                                Number.from_float(val.imag))
                            imag_i = MathStructure.multiplication(
                                imag_part, MathStructure.from_symbol("i"))
                            return MathStructure.addition(real_part, imag_i)
                        return real_part
                rebuilt = base ** exponent
            elif self._type == StructureType.NEGATE and evaluated_children:
                rebuilt = -evaluated_children[0]
            elif self._type == StructureType.INVERSE and evaluated_children:
                rebuilt = evaluated_children[0].inverse()
            elif self._type == StructureType.FACTORIAL and evaluated_children:
                rebuilt = MathStructure.factorial(evaluated_children[0])
            elif self._type == StructureType.BITWISE_AND and len(evaluated_children) == 2:
                left, right = evaluated_children
                if left.is_number() and right.is_number() and left._number is not None and right._number is not None:
                    result_val = int(left._number.to_float()) & int(right._number.to_float())
                    rebuilt = MathStructure(result_val)
                else:
                    rebuilt = self
            elif self._type == StructureType.BITWISE_OR and len(evaluated_children) == 2:
                left, right = evaluated_children
                if left.is_number() and right.is_number() and left._number is not None and right._number is not None:
                    result_val = int(left._number.to_float()) | int(right._number.to_float())
                    rebuilt = MathStructure(result_val)
                else:
                    rebuilt = self
            elif self._type == StructureType.BITWISE_XOR and len(evaluated_children) == 2:
                left, right = evaluated_children
                if left.is_number() and right.is_number() and left._number is not None and right._number is not None:
                    result_val = int(left._number.to_float()) ^ int(right._number.to_float())
                    rebuilt = MathStructure(result_val)
                else:
                    rebuilt = self
            else:
                rebuilt = self

            # If children changed, try evaluating the rebuilt expression
            if rebuilt is not self:
                # Check for interval arithmetic on rebuilt tree
                if rebuilt._has_interval_number():
                    result = rebuilt._eval_interval_arithmetic()
                    if result is not None:
                        # Apply unit simplification to interval results that contain
                        # unsimplified unit expressions (e.g., m^0.5 * (m/s^2)^-0.5)
                        if result._type == StructureType.MULTIPLICATION:
                            simplified = result._simplify_unit_mul()
                            if simplified is not None:
                                return simplified
                        return result
                # Flatten nested same-type structures for SymPy evaluation
                rebuilt = rebuilt._flatten_same_type()
                # If all children are evaluable (numbers or contain only known
                # constants like i, pi, e), try SymPy to combine them
                if rebuilt._children and all(
                    c._is_sympy_evaluable() for c in rebuilt._children
                ):
                    try:
                        sympy_expr = rebuilt.to_sympy()
                        if sympy_expr is not None:
                            if eo.approximation == ApproximationMode.APPROXIMATE:
                                result_expr = sp.N(sympy_expr, 15)
                            else:
                                result_expr = sp.simplify(sympy_expr)
                            return MathStructure.from_sympy(result_expr)
                    except Exception:
                        pass
                # Unit-aware simplification: if expression contains units,
                # multiply numeric coefficients and flatten nested multiplications
                if rebuilt._type == StructureType.MULTIPLICATION:
                    simplified = rebuilt._simplify_unit_mul()
                    if simplified is not None:
                        return simplified
                return rebuilt

        # For FUNCTION structures, try registered function's calculate() first
        # but ONLY for functions that aren't in the SymPy function map
        # (statistics, datetime, base conversion, etc.)
        # ALSO try for functions with interval arguments (SymPy can't handle intervals)
        if self._type == StructureType.FUNCTION and self._function is not None:
            func_name = self._function.name().lower() if self._function else ""
            # Check if any argument has an interval
            has_interval_arg = any(
                child._has_interval_number() for child in self._children
            )
            if func_name and (func_name not in _SYMPY_FUNC_MAP or has_interval_arg):
                try:
                    # Evaluate child arguments first
                    evaluated_args = [child.evaluate(eo) for child in self._children]
                    result = self._function.calculate(evaluated_args, eo)
                    if result is not None and not result.is_undefined():
                        return result
                except Exception:
                    pass  # Fall through to SymPy path

        try:
            sympy_expr = self.to_sympy()
        except Exception:
            return MathStructure.undefined()

        if sympy_expr is None:
            return MathStructure.undefined()

        # Preserve symbolic derivatives for ODE context — when the expression
        # does not depend on the variable of differentiation (e.g., y w.r.t. x),
        # sp.simplify would wrongly evaluate to 0. Only preserve when none of
        # the differentiation variables appear in the expression's free symbols.
        if isinstance(sympy_expr, sp.Derivative):
            expr_free = sympy_expr.args[0].free_symbols
            deriv_vars = set()
            for arg in sympy_expr.args[1:]:
                if isinstance(arg, sp.Tuple):
                    deriv_vars.add(arg[0])
                else:
                    deriv_vars.add(arg)
            if not deriv_vars & expr_free:
                return MathStructure.from_sympy(sympy_expr)

        try:
            if eo.approximation == ApproximationMode.APPROXIMATE:
                result_expr = sp.N(sympy_expr, 15)
            elif eo.approximation == ApproximationMode.EXACT:
                result_expr = sp.simplify(sympy_expr)
            else:
                # TRY_EXACT: simplify, keep exact if possible
                result_expr = sp.simplify(sympy_expr)

            if result_expr is sp.zoo or result_expr is sp.nan or (hasattr(result_expr, 'is_nan') and result_expr.is_nan):
                return MathStructure.undefined()
            return MathStructure.from_sympy(result_expr)
        except Exception:
            return MathStructure.undefined()

    def format(self, po: PrintOptions | None = None) -> MathStructure:
        """Format for display."""
        # Return a copy — shallow clone of this structure
        clone = MathStructure(struct_type=self._type)
        clone._number = self._number
        clone._unit = self._unit
        clone._prefix = self._prefix
        clone._variable = self._variable
        clone._function = self._function
        clone._symbol = self._symbol
        clone._children = list(self._children)
        clone._comparison_type = self._comparison_type
        clone._datetime = self._datetime
        return clone

    def print(self, po: PrintOptions | None = None) -> str:
        """Return a string representation.

        When ``po.precision`` is set (> 0) and this structure is not already
        a plain number, attempts to evaluate the expression numerically to
        *precision* significant digits via SymPy's ``evalf()``.  This
        converts symbolic results like ``tanh(40)``, ``sqrt(2)``,
        ``sin(1)`` into their numeric equivalents — but only when the
        expression contains no free symbols (i.e. no unresolved variables).
        """
        if po is None:
            po = PrintOptions()
        # When precision is set and result is not already a number,
        # attempt numeric evaluation of symbolic expressions.
        if po.precision > 0 and not self.is_number():
            try:
                sympy_expr = self.to_sympy()
                if sympy_expr is not None and not sympy_expr.free_symbols:
                    numeric_expr = sp.N(sympy_expr, po.precision)
                    numeric_ms = MathStructure.from_sympy(numeric_expr)
                    return numeric_ms._print_internal(po)
            except Exception:
                pass  # Fall through to normal printing
        return self._print_internal(po)

    def _print_internal(self, po: PrintOptions) -> str:
        """Internal print implementation with exact/approximate/fraction modes."""
        if self._type == StructureType.NUMBER and self._number is not None:
            return self._print_number(po)
        if self._type == StructureType.SYMBOLIC:
            return self._symbol
        if self._type == StructureType.VARIABLE and self._variable is not None:
            return self._variable.name()
        if self._type == StructureType.UNIT and self._unit is not None:
            return self._unit.name()
        if self._type == StructureType.UNDEFINED:
            return "undefined"
        if self._type == StructureType.FUNCTION:
            return self._print_function(po)
        if self._type == StructureType.ADDITION:
            return self._print_addition(po)
        if self._type == StructureType.MULTIPLICATION:
            return self._print_multiplication(po)
        if self._type == StructureType.POWER and len(self._children) == 2:
            return self._print_power(po)
        if self._type == StructureType.NEGATE and self._children:
            inner = self._children[0]._print_internal(po)
            return f"-({inner})"
        if self._type == StructureType.FACTORIAL and self._children:
            inner = self._children[0]._print_internal(po)
            return f"({inner})!"
        if self._type == StructureType.INVERSE and self._children:
            inner = self._children[0]._print_internal(po)
            return f"1/({inner})"
        if self._type == StructureType.VECTOR:
            return "[" + "  ".join(c._print_internal(po) for c in self._children) + "]"
        if self._type == StructureType.MATRIX:
            rows = []
            for row in self._children:
                if row.is_vector():
                    rows.append("  ".join(c._print_internal(po) for c in row))
                else:
                    rows.append(row._print_internal(po))
            return "[" + "; ".join(rows) + "]"
        if self._type == StructureType.COMPARISON and len(self._children) == 2:
            left = self._children[0]._print_internal(po)
            right = self._children[1]._print_internal(po)
            comp_map = {
                ComparisonType.EQUALS: " = ",
                ComparisonType.NOT_EQUALS: " != ",
                ComparisonType.LESS: " < ",
                ComparisonType.GREATER: " > ",
                ComparisonType.EQUALS_LESS: " <= ",
                ComparisonType.EQUALS_GREATER: " >= ",
            }
            op = comp_map.get(self._comparison_type if self._comparison_type is not None else ComparisonType.EQUALS, " = ")
            return left + op + right
        return f"<{self._type.name}>"

    def _print_number(self, po: PrintOptions) -> str:
        """Print a number value respecting print options."""
        num = self._number
        if num is None:
            return "undefined"

        # Per-structure fraction format override (e.g., from "to fraction")
        if self._number_fraction_format is not None:
            nff = self._number_fraction_format
            if nff == NumberFractionFormat.COMBINED and num.is_rational() and not num.is_integer():
                int_part = int(num._rational)
                frac_num = int(num._rational.numerator) - int_part * int(num._rational.denominator)
                frac_den = int(num._rational.denominator)
                if frac_num == 0:
                    return str(int_part)
                if int_part == 0:
                    return f"{frac_num}/{frac_den}"
                return f"{int_part} + {frac_num}/{frac_den}"
            if nff == NumberFractionFormat.FRACTIONAL and num.is_rational() and not num.is_integer():
                return f"{int(num._rational.numerator)}/{int(num._rational.denominator)}"

        # Approximate mode: force float display
        if po.approximate:
            if num.is_rational() and not num.is_integer():
                return self._format_float(num.to_float(), po)
            if num.is_rational():
                return self._format_float(float(num._rational), po)
            # Float type — round to reasonable precision
            return self._format_float(num.to_float(), po)

        # Fraction mode
        nff = po.number_fraction_format
        if nff == NumberFractionFormat.FRACTIONAL and num.is_rational() and not num.is_integer():
            return f"{int(num._rational.numerator)}/{int(num._rational.denominator)}"
        if nff == NumberFractionFormat.COMBINED and num.is_rational() and not num.is_integer():
            int_part = int(num._rational)
            frac_num = int(num._rational.numerator) - int_part * int(num._rational.denominator)
            frac_den = int(num._rational.denominator)
            if frac_num == 0:
                return str(int_part)
            if int_part == 0:
                return f"{frac_num}/{frac_den}"
            return f"{int_part} + {frac_num}/{frac_den}"
        if nff == NumberFractionFormat.PERCENT:
            val = num.to_float() * 100
            return f"{self._format_float(val, po)}%"

        # Base conversion
        if po.base not in (10, 0) and num.is_integer():
            val = num.to_int()
            if po.base == 16:
                hex_str = format(val, "x") if po.lower_case_numbers else format(val, "X")
                return f"0x{hex_str}"
            if po.base == 8:
                return f"0o{format(val, 'o')}"
            if po.base == 2:
                bits = format(abs(val), 'b')
                # Apply binary_bits padding if specified
                if po.binary_bits > 0:
                    min_bits = po.binary_bits
                else:
                    min_bits = ((len(bits) + 3) // 4) * 4
                bits = bits.zfill(min_bits)
                formatted = ' '.join(bits[i:i+4] for i in range(0, len(bits), 4))
                sign = '-' if val < 0 else ''
                return sign + formatted
            return num.to_string(po.base)

        # Default
        # For interval numbers, always use to_string which handles intervals
        if num.is_interval():
            return num.to_string(po.base)
        # For non-rational (float) numbers, round to eliminate floating-point noise
        if not num.is_rational():
            return self._format_float(num.to_float(), po)
        return num.to_string(po.base)

    def _format_float(self, val: float, po: PrintOptions) -> str:
        """Format a float value respecting print options."""
        import math
        if math.isinf(val):
            return "inf" if val > 0 else "-inf"
        if math.isnan(val):
            return "NaN"
        if val == int(val) and abs(val) < 1e15:
            return str(int(val))
        if po.max_decimals >= 0:
            return f"{val:.{po.max_decimals}f}"
        # Use precision from print options when set, otherwise default to 8
        # significant digits to eliminate floating-point noise
        sig_digits = po.precision if po.precision > 0 else 8
        s = f"{val:.{sig_digits}g}"
        # Strip trailing zeros after decimal point for cleanliness
        if '.' in s and 'e' not in s.lower():
            s = s.rstrip('0').rstrip('.')
        return s

    def _print_function(self, po: PrintOptions) -> str:
        """Print a function call."""
        name = self._symbol
        if not name and self._function is not None:
            name = self._function.name()
        args = ", ".join(c._print_internal(po) for c in self._children)
        return f"{name}({args})"

    def _print_addition(self, po: PrintOptions) -> str:
        """Print an addition, handling negative terms."""
        if not self._children:
            return "0"
        parts: list[str] = []
        for c in self._children:
            s = c._print_internal(po)
            # Detect negative number
            if c.is_number() and c._number is not None and c._number.is_negative():
                abs_s = MathStructure.from_number(-c._number)._print_internal(po)
                parts.append(f"- {abs_s}")
            # Detect negation node
            elif c._type == StructureType.NEGATE and c._children:
                inner = c._children[0]._print_internal(po)
                parts.append(f"- {inner}")
            # Detect multiplication by -1
            elif (c.is_multiplication() and c._children
                  and c._children[0].is_number()
                  and c._children[0]._number is not None
                  and c._children[0]._number.is_negative()):
                rest = MathStructure.multiplication(*c._children[1:]) if len(c._children) > 2 else c._children[1]
                rest_s = rest._print_internal(po)
                neg_coeff = MathStructure.from_number(-c._children[0]._number)
                if neg_coeff.is_one():
                    parts.append(f"- {rest_s}")
                else:
                    parts.append(f"- {neg_coeff._print_internal(po)}*{rest_s}")
            else:
                parts.append(s)

        result = parts[0]
        for p in parts[1:]:
            if p.startswith("- "):
                result += f" - {p[2:]}"
            else:
                result += f" + {p}"
        return result

    def _print_multiplication(self, po: PrintOptions) -> str:
        """Print a multiplication, handling number * unit patterns."""
        if not self._children:
            return "1"

        # Check for number * unit pattern (e.g., "1.524 m")
        if len(self._children) == 2:
            num_child = None
            unit_child = None
            for c in self._children:
                if c.is_number():
                    num_child = c
                elif c.is_unit():
                    unit_child = c

            if num_child is not None and unit_child is not None:
                num_str = num_child._print_number(po)
                unit_str = ""
                if unit_child._unit is not None:
                    base_name = unit_child._unit.print_unit(
                        plural=True, short=po.abbreviate_names
                    )
                    # Include prefix if present (e.g., "k" + "m" = "km")
                    if unit_child._prefix is not None and hasattr(unit_child._prefix, 'short_name'):
                        pfx_name = unit_child._prefix.short_name()
                        unit_str = pfx_name + base_name
                    else:
                        unit_str = base_name
                return f"{num_str} {unit_str}"

        parts: list[str] = []
        for c in self._children:
            s = c._print_internal(po)
            # Parenthesize addition/negation children to preserve meaning:
            # 2 * (a + b) instead of 2 * a + b
            if c._type in (StructureType.ADDITION, StructureType.NEGATE):
                s = f"({s})"
            parts.append(s)
        sep = " * "
        return sep.join(parts)

    def _print_power(self, po: PrintOptions) -> str:
        """Print a power, detecting sqrt/cbrt patterns."""
        base_m = self._children[0]
        exp_m = self._children[1]

        # Check for sqrt (exponent = 1/2)
        if (exp_m.is_number() and exp_m._number is not None
                and exp_m._number.is_rational()
                and exp_m._number == Number.from_rational(1, 2)):
            return f"sqrt({base_m._print_internal(po)})"

        # Check for cbrt (exponent = 1/3)
        if (exp_m.is_number() and exp_m._number is not None
                and exp_m._number.is_rational()
                and exp_m._number == Number.from_rational(1, 3)):
            return f"cbrt({base_m._print_internal(po)})"

        # Check for integer negative exponent: x^(-n) → 1/(x^n)
        if (exp_m.is_number() and exp_m._number is not None
                and exp_m._number.is_negative()):
            pos_exp = MathStructure.from_number(-exp_m._number)
            inner = MathStructure.power(base_m, pos_exp)
            return f"1/({inner._print_internal(po)})"

        return f"({base_m._print_internal(po)})^({exp_m._print_internal(po)})"

    # -- Representation --

    def __repr__(self) -> str:
        if self._type == StructureType.NUMBER and self._number is not None:
            return f"MathStructure({self._number!r})"
        if self._type == StructureType.SYMBOLIC:
            return f"MathStructure({self._symbol!r})"
        return f"MathStructure({self._type.name})"

    def __str__(self) -> str:
        return self.print()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MathStructure):
            return NotImplemented
        if self._type != other._type:
            return False
        if self._type == StructureType.NUMBER:
            return self._number == other._number
        if self._type == StructureType.SYMBOLIC:
            return self._symbol == other._symbol
        if len(self._children) != len(other._children):
            return False
        return all(c1 == c2 for c1, c2 in zip(self._children, other._children))

    def __hash__(self) -> int:
        if self._type == StructureType.NUMBER and self._number is not None:
            return hash(("MS", self._type, self._number))
        return hash(("MS", self._type, self._symbol, len(self._children)))


# Commonly used constants
m_zero = MathStructure(0)
m_one = MathStructure(1)
m_minus_one = MathStructure(-1)
m_undefined = MathStructure.undefined()

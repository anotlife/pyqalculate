"""Basic tests for PyQalculate package structure and imports."""

from __future__ import annotations


def test_package_import():
    """Test that the pyqalculate package can be imported."""
    import pyqalculate
    assert hasattr(pyqalculate, "__version__")
    assert pyqalculate.__version__ == "0.1.0"


def test_types_import():
    """Test that types module imports successfully."""
    from pyqalculate.types import (
        StructureType,
        MathOperation,
        ComparisonType,
        EvaluationOptions,
        ParseOptions,
        PrintOptions,
        PlotParameters,
    )
    assert StructureType.NUMBER == 6
    assert MathOperation.ADD == 2


def test_number_basic():
    """Test basic Number operations."""
    from pyqalculate.number import Number

    n = Number(5)
    assert n.is_integer()
    assert not n.is_zero()
    assert n.is_positive()

    z = Number(0)
    assert z.is_zero()
    assert not z.is_negative()


def test_number_arithmetic():
    """Test Number arithmetic."""
    from pyqalculate.number import Number

    a = Number(3)
    b = Number(4)
    assert (a + b).to_float() == 7.0
    assert (a * b).to_float() == 12.0
    assert (b - a).to_float() == 1.0
    assert (b / a).to_float() == 4 / 3


def test_math_structure():
    """Test MathStructure basics."""
    from pyqalculate.math_structure import MathStructure

    m = MathStructure(42)
    assert m.is_number()
    assert not m.is_undefined()
    assert m.float_value() == 42.0

    s = MathStructure.from_symbol("x")
    assert s.is_symbolic()
    assert s.symbol == "x"


def test_calculator_creation():
    """Test Calculator can be created and used."""
    from pyqalculate.calculator import Calculator

    calc = Calculator()
    assert calc.get_precision() == 8
    calc.set_precision(20)
    assert calc.get_precision() == 20


def test_variable_classes():
    """Test variable classes."""
    from pyqalculate.variable import (
        Assumptions,
        KnownVariable,
        UnknownVariable,
        AssumptionType,
        AssumptionSign,
    )

    uv = UnknownVariable("", "x")
    assert not uv.is_known()
    assert uv.assumptions.type == AssumptionType.NUMBER

    kv = KnownVariable("", "pi", "3.14")
    assert kv.is_known()
    assert kv.is_expression()


def test_unit_classes():
    """Test unit classes."""
    from pyqalculate.unit import Unit, AliasUnit

    u = Unit("Length", "meter", "meters", "meter", "Metre")
    assert u.name() == "meter"
    assert u.plural() == "meters"

    au = AliasUnit("Time", "hour", "hours", "hour", "Hour", base_unit=u, relation="3600")
    assert au.subtype() == 1  # ALIAS_UNIT


def test_prefix_classes():
    """Test prefix classes."""
    from pyqalculate.prefix import DecimalPrefix

    kilo = DecimalPrefix(3, "kilo", "k")
    assert kilo.exponent() == 3
    assert kilo.short_name() == "k"
    assert kilo.long_name() == "kilo"


def test_datetime_ext():
    """Test DateTimeExt class."""
    from pyqalculate.datetime_ext import DateTimeExt

    dt = DateTimeExt(2024, 6, 15)
    assert dt.year == 2024
    assert dt.month == 6
    assert dt.day == 15
    assert dt.is_leap_year()  # 2024 is a leap year


def test_function_base():
    """Test MathFunction base class."""
    from pyqalculate.function import MathFunction, NumberArgument

    # Can't instantiate abstract class directly, use a concrete one
    from pyqalculate.builtin_functions import SqrtFunction

    f = SqrtFunction()
    assert f.name() == "sqrt"
    assert f.args() == 1
    assert f.id() == 1200


def test_dataset():
    """Test DataSet class."""
    from pyqalculate.dataset import DataSet, DataProperty, DataObject

    ds = DataSet("Astronomy", "planets", title="Planets")
    dp = DataProperty(ds, "name", "Name")
    dp.set_key(True)
    ds.add_property(dp)

    obj = DataObject(ds)
    obj.set_property("name", "Earth")
    ds.add_object(obj)

    assert ds.count_properties() == 1
    assert ds.count_objects() == 1


def test_expression_item():
    """Test ExpressionItem base class."""
    from pyqalculate.expression_item import ExpressionItem, ExpressionName

    # ExpressionItem is abstract for type(), so test ExpressionName
    en = ExpressionName("test")
    assert en.name == "test"
    assert not en.abbreviation  # "test" has len 4, so abbreviation is False

    en2 = ExpressionName("m")
    assert en2.abbreviation  # single char is abbreviation
    assert en2.case_sensitive  # single char is case sensitive

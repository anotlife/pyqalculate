"""Unit classes - base units, alias units, and composite units.

Mirrors libqalculate's Unit hierarchy for measurement units.
Provides chain conversion through alias units and composite unit support.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pyqalculate.expression_item import ExpressionItem, ExpressionName
from pyqalculate.types import ExpressionItemType, UnitSubtype

if TYPE_CHECKING:
    from pyqalculate.math_structure import MathStructure
    from pyqalculate.number import Number
    from pyqalculate.prefix import Prefix


class Unit(ExpressionItem):
    """A unit for measurement.

    The Unit class represents both a base unit and is the base class for
    other unit types. Base units are defined as the basis for other units
    (e.g., meters, seconds).

    Base units normally have three names: abbreviation (e.g., "m"),
    singular ("meter"), and plural ("meters").
    """

    def __init__(
        self,
        category: str = "",
        name: str = "",
        plural: str = "",
        singular: str = "",
        title: str = "",
        is_local: bool = True,
        is_builtin: bool = False,
        is_active: bool = True,
    ) -> None:
        super().__init__(category, name, title, "", is_local, is_builtin, is_active)
        self._system = ""
        self._countries = ""
        self._is_si = False
        self._use_with_prefixes = True
        self._max_preferred_prefix = 0
        self._min_preferred_prefix = 0
        self._default_prefix = 0

        if plural:
            self.add_name(plural)
        if singular:
            ename = ExpressionName(singular)
            ename.abbreviation = False
            self.add_name(ename)

    def type(self) -> ExpressionItemType:
        return ExpressionItemType.UNIT

    def subtype(self) -> int:
        return UnitSubtype.BASE_UNIT

    def is_si_unit(self) -> bool:
        return self._is_si

    def set_as_si_unit(self) -> None:
        self._is_si = True
        self._system = "SI"

    def system(self) -> str:
        return self._system

    def set_system(self, system: str) -> None:
        self._system = system
        self._is_si = system.upper() == "SI"

    def use_with_prefixes_by_default(self) -> bool:
        return self._use_with_prefixes

    def set_use_with_prefixes_by_default(self, use: bool) -> None:
        self._use_with_prefixes = use

    def max_preferred_prefix(self) -> int:
        return self._max_preferred_prefix

    def set_max_preferred_prefix(self, exp: int) -> None:
        self._max_preferred_prefix = exp

    def min_preferred_prefix(self) -> int:
        return self._min_preferred_prefix

    def set_min_preferred_prefix(self, exp: int) -> None:
        self._min_preferred_prefix = exp

    def default_prefix(self) -> int:
        return self._default_prefix

    def set_default_prefix(self, exp: int) -> None:
        self._default_prefix = exp

    def is_currency(self) -> bool:
        return self._category.lower().startswith("currency")

    def countries(self) -> str:
        return self._countries

    def set_countries(self, countries: str) -> None:
        self._countries = countries

    def plural(self) -> str:
        """Return the plural name."""
        for n in self._names:
            if n.plural:
                return n.name
        if len(self._names) > 1:
            return self._names[1].name
        return self.name()

    def singular(self) -> str:
        """Return the singular name."""
        for n in self._names:
            if not n.abbreviation and not n.plural:
                return n.name
        return self.name()

    def abbreviation(self) -> str:
        """Return the abbreviation."""
        for n in self._names:
            if n.abbreviation and not n.unicode:
                return n.name
        return self.name()

    def base_unit(self) -> Unit | None:
        """Return the base unit (self for base units)."""
        return self

    def first_base_unit(self) -> Unit:
        """Return the first base unit in the chain (self for base units)."""
        return self

    def first_base_exponent(self) -> int:
        """Return the first base exponent (1 for base units)."""
        return 1

    def is_child_of(self, u: Unit) -> bool:
        """Check if this unit has u as a base unit."""
        return False

    def is_parent_of(self, u: Unit) -> bool:
        """Check if u has this as a base unit."""
        return u.is_child_of(self)

    def has_nonlinear_relation_to(self, u: Unit) -> bool:
        return False

    def has_nonlinear_relation_to_base(self) -> bool:
        return False

    def convert_to_base_unit(
        self, value: float, exponent: int = 1
    ) -> tuple[float, int]:
        """Convert a value in this unit to the base unit.

        For base units, this is the identity transformation.

        Args:
            value: The numeric value in this unit.
            exponent: The exponent of this unit.

        Returns:
            Tuple of (value_in_base_unit, new_exponent).
        """
        return value, exponent

    def convert_from_base_unit(
        self, value: float, exponent: int = 1
    ) -> tuple[float, int]:
        """Convert a value from the base unit to this unit.

        For base units, this is the identity transformation.

        Args:
            value: The numeric value in the base unit.
            exponent: The exponent of this unit.

        Returns:
            Tuple of (value_in_this_unit, new_exponent).
        """
        return value, exponent

    def convert_to_base_expression(self) -> str:
        """Return the expression to convert 1 of this unit to base unit."""
        return "1"

    def convert_from_base_expression(self) -> str:
        """Return the expression to convert 1 of base unit to this unit."""
        return "1"

    def generate_math_structure(self, make_division: bool = False) -> MathStructure:
        """Create a MathStructure representing this unit's base expression."""
        from pyqalculate.math_structure import MathStructure
        return MathStructure.from_unit(self)

    def print_unit(
        self,
        plural: bool = True,
        short: bool = True,
        use_unicode: bool = False,
    ) -> str:
        """Return a display string for the unit."""
        if short:
            return self.abbreviation()
        return self.plural() if plural else self.singular()

    def copy(self) -> Unit:
        u = Unit(self._category, self.name(), self.plural(), self.singular(),
                 self._title, self._is_local, self._is_builtin, self._is_active)
        u._system = self._system
        u._countries = self._countries
        u._is_si = self._is_si
        u._use_with_prefixes = self._use_with_prefixes
        u._max_preferred_prefix = self._max_preferred_prefix
        u._min_preferred_prefix = self._min_preferred_prefix
        u._default_prefix = self._default_prefix
        return u


class AliasUnit(Unit):
    """A unit defined in relation to another unit.

    For example, hours are defined as an alias unit that equals 60 minutes.
    The relation is: alias_unit = relation * base_unit^exponent.

    For complex units like degrees Celsius, the relation is an expression
    like "\\x + 273.15" where \\x is replaced by the quantity.
    """

    def __init__(
        self,
        category: str = "",
        name: str = "",
        plural: str = "",
        singular: str = "",
        title: str = "",
        base_unit: Unit | None = None,
        relation: str = "1",
        exponent: int = 1,
        inverse: str = "",
        is_local: bool = True,
        is_builtin: bool = False,
        is_active: bool = True,
    ) -> None:
        super().__init__(category, name, plural, singular, title,
                         is_local, is_builtin, is_active)
        self._base_unit = base_unit
        self._relation = relation
        self._inverse = inverse
        self._uncertainty = ""
        self._is_relative_uncertainty = False
        self._exponent = exponent
        self._mix_with_base = 0
        self._mix_with_base_minimum = 0

    def subtype(self) -> int:
        return UnitSubtype.ALIAS_UNIT

    def base_unit(self) -> Unit | None:
        return self._base_unit

    def set_base_unit(self, unit: Unit) -> None:
        self._base_unit = unit

    def first_base_unit(self) -> Unit:
        """Return the first base unit in the chain."""
        if self._base_unit is None:
            return self
        if self._base_unit.subtype() == UnitSubtype.ALIAS_UNIT:
            return self._base_unit.first_base_unit()
        return self._base_unit

    def first_base_exponent(self) -> int:
        """Return the exponent of the first base unit in the chain."""
        if self._base_unit is None:
            return self._exponent
        if self._base_unit.subtype() == UnitSubtype.ALIAS_UNIT:
            return self._exponent * self._base_unit.first_base_exponent()
        return self._exponent

    def expression(self) -> str:
        """Return the relation expression."""
        return self._relation

    def inverse_expression(self) -> str:
        """Return the inverse relation expression."""
        return self._inverse

    def set_expression(self, relation: str) -> None:
        self._relation = relation

    def set_inverse_expression(self, inverse: str) -> None:
        self._inverse = inverse

    def uncertainty(self) -> str:
        return self._uncertainty

    def set_uncertainty(self, uncertainty: str, is_relative: bool = False) -> None:
        self._uncertainty = uncertainty
        self._is_relative_uncertainty = is_relative

    def exponent(self) -> int:
        return self._exponent

    def set_exponent(self, exp: int) -> None:
        self._exponent = exp

    def has_nonlinear_expression(self) -> bool:
        """Check if the relation expression contains \\x."""
        return "\\x" in self._relation

    def has_nonlinear_relation_to_base(self) -> bool:
        return self.has_nonlinear_expression()

    def mix_with_base(self) -> int:
        return self._mix_with_base

    def set_mix_with_base(self, priority: int = 1) -> None:
        self._mix_with_base = priority

    def mix_with_base_minimum(self) -> int:
        return self._mix_with_base_minimum

    def set_mix_with_base_minimum(self, minimum: int) -> None:
        self._mix_with_base_minimum = minimum

    def is_child_of(self, u: Unit) -> bool:
        """Check if this unit has u as a base unit (following the chain)."""
        if self._base_unit is None:
            return False
        if self._base_unit is u:
            return True
        return self._base_unit.is_child_of(u)

    def convert_to_base_unit(
        self, value: float, exponent: int = 1
    ) -> tuple[float, int]:
        """Convert a value in this unit to the base unit.

        The relation defines: 1 alias_unit = relation * base_unit^unit_exponent

        When exponent > 1, the relation must be raised to the exponent power
        to properly handle dimensional units (e.g., fl_oz = relation * in^3).

        Args:
            value: The numeric value in this unit.
            exponent: The current exponent (typically 1).

        Returns:
            Tuple of (value_in_base_unit, new_exponent).
        """
        if self._base_unit is None:
            return value, exponent

        if self.has_nonlinear_expression():
            result = _eval_nonlinear(self._relation, value)
            return result, exponent

        try:
            rel = _eval_numeric_expression(self._relation)
        except (ValueError, ZeroDivisionError):
            return value, exponent

        new_exponent = exponent * self._exponent
        if exponent != 1:
            new_value = value * (rel ** exponent)
        else:
            new_value = value * rel
        return new_value, new_exponent

    def convert_from_base_unit(
        self, value: float, exponent: int = 1
    ) -> tuple[float, int]:
        """Convert a value from the base unit to this unit.

        Args:
            value: The numeric value in the base unit.
            exponent: The current exponent (typically 1).

        Returns:
            Tuple of (value_in_this_unit, new_exponent).
        """
        if self._base_unit is None:
            return value, exponent

        if self.has_nonlinear_expression():
            inv = self._inverse if self._inverse else self._relation
            result = _eval_nonlinear_inverse(inv, value)
            return result, exponent

        try:
            rel = _eval_numeric_expression(self._relation)
        except (ValueError, ZeroDivisionError):
            return value, exponent

        new_exponent = exponent // self._exponent if self._exponent != 0 else exponent
        if exponent != 1:
            new_value = value / (rel ** exponent)
        else:
            new_value = value / rel
        return new_value, new_exponent

    def convert_to_base_expression(self) -> str:
        """Return the expression to convert 1 of this unit to base."""
        return self._relation

    def convert_from_base_expression(self) -> str:
        """Return the expression to convert 1 of base to this unit."""
        if self._inverse:
            return self._inverse
        if self._relation and self._relation != "0":
            return f"1/({self._relation})"
        return "1"

    def generate_math_structure(self, make_division: bool = False) -> MathStructure:
        """Create a MathStructure representing this unit's base expression."""
        from pyqalculate.math_structure import MathStructure
        if self._base_unit is None:
            return MathStructure.from_unit(self)
        # Build: relation * base_unit^exponent
        rel_val = _eval_numeric_expression(self._relation)
        base_m: MathStructure = self._base_unit.generate_math_structure(make_division)
        if self._exponent != 1:
            exp_m = MathStructure(self._exponent)
            base_m = MathStructure.power(base_m, exp_m)
        if rel_val != 1.0:
            rel_m = MathStructure(rel_val)
            base_m = MathStructure.multiplication(rel_m, base_m)
        return base_m

    def copy(self) -> AliasUnit:
        u = AliasUnit(self._category, self.name(), self.plural(), self.singular(),
                      self._title, self._base_unit, self._relation, self._exponent,
                      self._inverse, self._is_local, self._is_builtin, self._is_active)
        u._uncertainty = self._uncertainty
        u._is_relative_uncertainty = self._is_relative_uncertainty
        u._mix_with_base = self._mix_with_base
        u._mix_with_base_minimum = self._mix_with_base_minimum
        return u


class AliasUnitComposite(AliasUnit):
    """A subunit in a CompositeUnit. Should normally not be used directly."""

    def __init__(
        self,
        base_unit: Unit | None = None,
        exponent: int = 1,
        prefix: Prefix | None = None,
    ) -> None:
        super().__init__("", "", "", "", "", base_unit, "1", exponent)
        self._prefix: Prefix | None = prefix

    def prefix(self) -> Prefix | None:
        return self._prefix

    def set(self, unit: Unit, exponent: int = 1, prefix: Prefix | None = None) -> None:
        self._base_unit = unit
        self._exponent = exponent
        self._prefix = prefix


class CompositeUnit(Unit):
    """A unit consisting of a number of other units.

    Composite units are defined by a unit expression with multiple units.
    For example, a joule is defined as an alias of "Newton * meter".

    Composite units are parsed from an expression (e.g., "cm^3/g") or
    built by adding sub-units one by one with add().
    """

    def __init__(
        self,
        category: str = "",
        name: str = "",
        title: str = "",
        base_expression: str = "",
        is_local: bool = True,
        is_builtin: bool = False,
        is_active: bool = True,
    ) -> None:
        super().__init__(category, name, "", "", title, is_local, is_builtin, is_active)
        self._units: list[AliasUnitComposite] = []
        if base_expression:
            self.set_base_expression(base_expression)

    def subtype(self) -> int:
        return UnitSubtype.COMPOSITE_UNIT

    def add(self, unit: Unit, exponent: int = 1, prefix: Prefix | None = None) -> None:
        """Add a sub/base unit with specified exponent and optional prefix."""
        self._units.append(AliasUnitComposite(unit, exponent, prefix))

    def get(self, index: int) -> AliasUnitComposite | None:
        """Retrieve sub-unit at 1-based index."""
        if 1 <= index <= len(self._units):
            return self._units[index - 1]
        return None

    def count_units(self) -> int:
        return len(self._units)

    def clear(self) -> None:
        """Remove all sub/base units."""
        self._units.clear()

    def set_base_expression(self, expression: str) -> None:
        """Parse a unit expression string and set sub-units.

        Supports expressions like "m*s^-2", "kg*m/s^2", "cm^3/g".
        Requires calculator reference to resolve unit names.
        """
        # This is handled during JSON loading, not here
        pass

    def is_child_of(self, u: Unit) -> bool:
        """Check if any sub-unit is a child of u."""
        for su in self._units:
            bu = su.base_unit()
            if bu is not None and bu.is_child_of(u):
                return True
        return False

    def has_nonlinear_relation_to_base(self) -> bool:
        return False

    def generate_math_structure(self, make_division: bool = False) -> MathStructure:
        """Create a MathStructure representing this composite unit.

        E.g., for N = kg*m/s^2, generates kg*m*s^(-2).
        """
        from pyqalculate.math_structure import MathStructure
        result: MathStructure | None = None
        for su in self._units:
            base_u = su.base_unit()
            if base_u is None:
                continue
            exp = su.exponent()
            pfx = su.prefix()

            # Get the base unit's math structure (resolve through chain)
            sub_struct: MathStructure = base_u.generate_math_structure(make_division)

            # Apply prefix if present
            if pfx is not None:
                prefix_val = pfx.value(exp)
                prefix_m = MathStructure(prefix_val.to_float())
                sub_struct = MathStructure.multiplication(prefix_m, sub_struct)

            # Apply exponent
            if exp != 1:
                if exp < 0 and make_division:
                    # Use division for negative exponents
                    exp_m = MathStructure(-exp)
                    sub_struct = MathStructure.power(sub_struct, exp_m)
                    sub_struct = MathStructure.inverse(sub_struct)
                else:
                    exp_m = MathStructure(exp)
                    sub_struct = MathStructure.power(sub_struct, exp_m)

            if result is None:
                result = sub_struct
            else:
                result = MathStructure.multiplication(result, sub_struct)

        if result is None:
            return MathStructure.from_unit(self)
        return result

    def print_unit(
        self,
        plural: bool = True,
        short: bool = True,
        use_unicode: bool = False,
    ) -> str:
        """Return a display string for the composite unit."""
        parts = []
        for su in self._units:
            base_u = su.base_unit()
            if base_u is None:
                continue
            exp = su.exponent()
            prefix = su.prefix()

            name = base_u.abbreviation() if short else base_u.plural() if plural else base_u.singular()

            if prefix is not None:
                prefix_name = prefix.short_name()
                name = prefix_name + name

            if exp == -1:
                parts.append(f"/{name}")
            elif exp != 1:
                if exp < 0:
                    parts.append(f"{name}^({exp})")
                else:
                    parts.append(f"{name}^{exp}")
            else:
                parts.append(name)

        if not parts:
            return self.name()

        # Format: positive units first, then divisions
        positives = [p for p in parts if not p.startswith("/")]
        negatives = [p[1:] for p in parts if p.startswith("/")]

        result = "*".join(positives) if positives else "1"
        if negatives:
            result += "/" + "*".join(negatives)
        return result

    def copy(self) -> CompositeUnit:
        u = CompositeUnit(self._category, self.name(), self._title, "",
                          self._is_local, self._is_builtin, self._is_active)
        for su in self._units:
            u._units.append(AliasUnitComposite(su.base_unit(), su.exponent(), su.prefix()))
        return u


# ---------------------------------------------------------------------------
# Expression evaluation helpers
# ---------------------------------------------------------------------------


def _eval_numeric_expression(expr: str) -> float:
    """Evaluate a numeric expression string that may contain simple math.

    Supports: numbers, *, /, +, -, ^, parentheses, and known constants like pi.
    Does NOT support \\x (nonlinear expressions).
    """
    if not expr or expr.strip() == "":
        return 1.0

    expr = expr.strip()

    # Replace known constants
    expr = expr.replace("pi", str(3.14159265358979323846))

    # Handle simple fraction: "a/b"
    if "/" in expr and "^" not in expr and "*" not in expr and "+" not in expr and "-" not in expr.replace("/", "").lstrip("-"):
        parts = expr.split("/")
        if len(parts) == 2:
            try:
                num = float(parts[0].strip())
                den = float(parts[1].strip())
                if den != 0:
                    return num / den
            except ValueError:
                pass

    # Use Python's eval safely for numeric expressions
    # Replace ^ with ** for exponentiation
    eval_expr = expr.replace("^", "**")

    # Only allow safe characters
    allowed = set("0123456789.+-*/() eE")
    if all(c in allowed for c in eval_expr):
        try:
            return float(eval(eval_expr))
        except (SyntaxError, NameError, TypeError, ZeroDivisionError):
            pass

    # Fallback: try direct float conversion
    try:
        return float(expr)
    except ValueError:
        return 1.0


def _eval_nonlinear(relation: str, value: float) -> float:
    """Evaluate a nonlinear relation expression with \\x replaced by value."""
    expr = relation.replace("\\x", f"({value})")
    return _eval_numeric_expression(expr)


def _eval_nonlinear_inverse(inverse: str, value: float) -> float:
    """Evaluate a nonlinear inverse expression with \\x replaced by value."""
    expr = inverse.replace("\\x", f"({value})")
    return _eval_numeric_expression(expr)


# ---------------------------------------------------------------------------
# Names parsing helper
# ---------------------------------------------------------------------------


def parse_unit_names(names_str: str) -> list[ExpressionName]:
    """Parse a unit names string into a list of ExpressionName objects.

    Names format: "ar:ft,foot,p:feet"
    Prefixes:
        a = abbreviation (short, e.g. "ft")
        r = reference name (primary identifier)
        p = plural
        as = suffix abbreviation
        au = unicode abbreviation
        s = suffix
        e = abbreviation for plural
        o = case-sensitive override
        c = case-sensitive name
        i = completion-only (hidden from input)
    """
    result: list[ExpressionName] = []
    if not names_str:
        return result

    for entry in names_str.split(","):
        entry = entry.strip()
        if not entry:
            continue

        if ":" in entry:
            prefix, name = entry.split(":", 1)
            name = name.strip()
            if not name:
                continue

            en = ExpressionName(name)

            # Parse prefix flags
            is_abbrev = False
            is_plural = False
            is_reference = False
            is_unicode = False
            is_suffix = False
            is_case_sensitive = False
            is_completion_only = False

            i = 0
            while i < len(prefix):
                ch = prefix[i]
                if ch == "a":
                    is_abbrev = True
                elif ch == "r":
                    is_reference = True
                elif ch == "p":
                    is_plural = True
                elif ch == "u":
                    is_unicode = True
                elif ch == "s":
                    is_suffix = True
                elif ch == "o":
                    is_case_sensitive = True
                elif ch == "c":
                    is_case_sensitive = True
                elif ch == "i":
                    is_completion_only = True
                elif ch == "e":
                    is_abbrev = True
                    is_plural = True
                i += 1

            en.abbreviation = is_abbrev
            en.plural = is_plural
            en.reference = is_reference
            en.unicode = is_unicode
            en.suffix = is_suffix
            en.case_sensitive = is_case_sensitive
            en.completion_only = is_completion_only

            result.append(en)
        else:
            # No prefix - default behavior
            en = ExpressionName(entry)
            result.append(en)

    return result

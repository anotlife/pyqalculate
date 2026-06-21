"""Variable classes - known, unknown, and dynamic variables.

Mirrors libqalculate's Variable hierarchy: Variable (abstract base),
UnknownVariable (with assumptions), KnownVariable (with value or expression),
and DynamicVariable (recalculated on precision change).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyqalculate.expression_item import ExpressionItem
from pyqalculate.types import (
    AssumptionType,
    AssumptionSign,
    ExpressionItemType,
    VariableSubtype,
)

if TYPE_CHECKING:
    from pyqalculate.math_structure import MathStructure


class Assumptions:
    """Assumptions about an unknown mathematical value.

    Has a type (number, integer, real, etc.) and a sign (positive, negative, etc.).
    Also optionally has min and max bounds.
    """

    def __init__(self) -> None:
        self._type = AssumptionType.NUMBER
        self._sign = AssumptionSign.UNKNOWN
        self._min: float | None = None
        self._max: float | None = None
        self._include_equals_min = False
        self._include_equals_max = False

    @property
    def type(self) -> AssumptionType:
        return self._type

    @type.setter
    def type(self, value: AssumptionType) -> None:
        self._type = value

    @property
    def sign(self) -> AssumptionSign:
        return self._sign

    @sign.setter
    def sign(self, value: AssumptionSign) -> None:
        self._sign = value

    def is_positive(self) -> bool:
        return self._sign == AssumptionSign.POSITIVE

    def is_negative(self) -> bool:
        return self._sign == AssumptionSign.NEGATIVE

    def is_non_negative(self) -> bool:
        return self._sign in (AssumptionSign.POSITIVE, AssumptionSign.NONNEGATIVE)

    def is_non_positive(self) -> bool:
        return self._sign in (AssumptionSign.NEGATIVE, AssumptionSign.NONPOSITIVE)

    def is_integer(self) -> bool:
        return self._type == AssumptionType.INTEGER

    def is_boolean(self) -> bool:
        return self._type == AssumptionType.BOOLEAN

    def is_number(self) -> bool:
        return self._type >= AssumptionType.NUMBER

    def is_rational(self) -> bool:
        return self._type >= AssumptionType.RATIONAL

    def is_real(self) -> bool:
        return self._type >= AssumptionType.REAL

    def is_complex(self) -> bool:
        return self._type >= AssumptionType.COMPLEX

    def is_non_zero(self) -> bool:
        return self._sign == AssumptionSign.NONZERO

    def set_min(self, min_val: float | None) -> None:
        self._min = min_val

    def set_max(self, max_val: float | None) -> None:
        self._max = max_val


class Variable(ExpressionItem):
    """Abstract base class for variables.

    A variable is an alpha-numerical representation of a known or unknown value.
    """

    def __init__(
        self,
        category: str = "",
        name: str = "",
        title: str = "",
        is_local: bool = True,
        is_builtin: bool = False,
        is_active: bool = True,
    ) -> None:
        super().__init__(category, name, title, "", is_local, is_builtin, is_active)

    def type(self) -> ExpressionItemType:
        return ExpressionItemType.VARIABLE

    def subtype(self) -> int:
        return VariableSubtype.VARIABLE

    def is_known(self) -> bool:
        """Return True if the variable has a known value."""
        raise NotImplementedError

    def represents_positive(self) -> bool:
        return False

    def represents_negative(self) -> bool:
        return False

    def represents_non_negative(self) -> bool:
        return False

    def represents_integer(self) -> bool:
        return False

    def represents_real(self) -> bool:
        return False

    def represents_non_zero(self) -> bool:
        return False

    def represents_boolean(self) -> bool:
        return False


class UnknownVariable(Variable):
    """A variable with unknown value and associated assumptions."""

    def __init__(
        self,
        category: str = "",
        name: str = "",
        title: str = "",
        is_local: bool = True,
        is_builtin: bool = False,
        is_active: bool = True,
    ) -> None:
        super().__init__(category, name, title, is_local, is_builtin, is_active)
        self._assumptions = Assumptions()

    def subtype(self) -> int:
        return VariableSubtype.UNKNOWN_VARIABLE

    def is_known(self) -> bool:
        return False

    @property
    def assumptions(self) -> Assumptions:
        return self._assumptions

    def set_assumptions(self, assumptions: Assumptions) -> None:
        self._assumptions = assumptions

    def represents_positive(self) -> bool:
        return self._assumptions.is_positive()

    def represents_negative(self) -> bool:
        return self._assumptions.is_negative()

    def represents_non_negative(self) -> bool:
        return self._assumptions.is_non_negative()

    def represents_integer(self) -> bool:
        return self._assumptions.is_integer()

    def represents_real(self) -> bool:
        return self._assumptions.is_real()

    def represents_non_zero(self) -> bool:
        return self._assumptions.is_non_zero()

    def represents_boolean(self) -> bool:
        return self._assumptions.is_boolean()

    def copy(self) -> UnknownVariable:
        v = UnknownVariable(self._category, self.name(), self._title,
                            self._is_local, self._is_builtin, self._is_active)
        v._assumptions = self._assumptions
        return v


class KnownVariable(Variable):
    """A variable with a known value.

    The value can be a simple number or a full mathematical expression.
    The value can be provided as an expression string or as a MathStructure.
    The text string is parsed when needed.
    """

    def __init__(
        self,
        category: str = "",
        name: str = "",
        value: MathStructure | str | None = None,
        title: str = "",
        is_local: bool = True,
        is_builtin: bool = False,
        is_active: bool = True,
    ) -> None:
        super().__init__(category, name, title, is_local, is_builtin, is_active)
        self._value: MathStructure | None = None
        self._expression: str = ""
        self._uncertainty: str = ""
        self._unit: str = ""
        self._is_relative_uncertainty = False

        if isinstance(value, str):
            self._expression = value
        elif value is not None:
            self._value = value

    def subtype(self) -> int:
        return VariableSubtype.KNOWN_VARIABLE

    def is_known(self) -> bool:
        return True

    def is_expression(self) -> bool:
        """Return True if the variable has a text string expression."""
        return bool(self._expression) and self._value is None

    def expression(self) -> str:
        return self._expression

    def uncertainty(self) -> str:
        return self._uncertainty

    def unit(self) -> str:
        return self._unit

    def set(self, value: MathStructure | str) -> None:
        """Set the value from a MathStructure or expression string."""
        if isinstance(value, str):
            self._expression = value
            self._value = None
        else:
            self._value = value
            self._expression = ""

    def set_uncertainty(self, uncertainty: str, is_relative: bool = False) -> None:
        self._uncertainty = uncertainty
        self._is_relative_uncertainty = is_relative

    def set_unit(self, unit: str) -> None:
        self._unit = unit

    def get(self) -> MathStructure | None:
        """Return the value, parsing the expression if needed."""
        if self._value is not None:
            return self._value
        # If we have an expression string, try to parse and cache it
        if self._expression:
            try:
                # Try to parse as a number using gmpy2 for high precision
                import gmpy2
                from pyqalculate.number import Number
                from pyqalculate.math_structure import MathStructure
                # Try rational first (e.g., "3/4")
                if '/' in self._expression:
                    parts = self._expression.split('/')
                    if len(parts) == 2:
                        p = int(parts[0].strip())
                        q = int(parts[1].strip())
                        if q != 0:
                            self._value = MathStructure.from_number(Number.from_rational(p, q))
                            return self._value
                # Try high-precision float via gmpy2
                mpfr_val = gmpy2.mpfr(self._expression)
                self._value = MathStructure(float(mpfr_val))
                return self._value
            except Exception:
                pass
        return None

    def copy(self) -> KnownVariable:
        v = KnownVariable(self._category, self.name(), None, self._title,
                          self._is_local, self._is_builtin, self._is_active)
        v._value = self._value
        v._expression = self._expression
        v._uncertainty = self._uncertainty
        v._unit = self._unit
        return v


class DynamicVariable(KnownVariable):
    """Variable with a value that is recalculated when precision changes.

    Abstract base for constants like pi and e that need recalculation
    at different precisions.
    """

    def __init__(
        self,
        category: str = "",
        name: str = "",
        title: str = "",
        is_local: bool = False,
        is_builtin: bool = True,
        is_active: bool = True,
    ) -> None:
        super().__init__(category, name, None, title, is_local, is_builtin, is_active)
        self._always_recalculate = False
        self._calculated_precision = 0

    def get(self) -> MathStructure | None:
        """Return the value, recalculating if precision changed."""
        # Subclasses must implement _calculate()
        return self._value

    def _calculate(self) -> MathStructure:
        """Calculate the value. Must be implemented by subclasses."""
        raise NotImplementedError

    def calculated_precision(self) -> int:
        return self._calculated_precision


# -- Builtin variable IDs --

VARIABLE_ID_E = 100
VARIABLE_ID_PI = 101
VARIABLE_ID_EULER = 102
VARIABLE_ID_CATALAN = 103
VARIABLE_ID_PRECISION = 140
VARIABLE_ID_TODAY = 161
VARIABLE_ID_TOMORROW = 162
VARIABLE_ID_YESTERDAY = 163
VARIABLE_ID_NOW = 164
VARIABLE_ID_UPTIME = 170

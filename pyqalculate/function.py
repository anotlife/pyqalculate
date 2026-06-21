"""Function base classes and argument definitions.

Mirrors libqalculate's MathFunction and Argument hierarchy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyqalculate.expression_item import ExpressionItem
from pyqalculate.types import (
    ArgumentType,
    ArgumentMinMaxPreDefinition,
    EvaluationOptions,
    ExpressionItemType,
    FunctionSubtype,
    ParseOptions,
)

if TYPE_CHECKING:
    from pyqalculate.math_structure import MathStructure


class Argument:
    """Base class for function argument definitions.

    A free argument accepts any value. Subclasses restrict the type.
    """

    def __init__(
        self,
        name: str = "",
        does_test: bool = True,
        does_error: bool = True,
    ) -> None:
        self._name = name
        self._condition = ""
        self._test = does_test
        self._error = does_error
        self._zero_forbidden = False
        self._matrix_allowed = False
        self._handle_vector = False
        self._is_last = False
        self._rational_polynomial = False

    def name(self) -> str:
        return self._name

    def set_name(self, name: str) -> None:
        self._name = name

    def tests(self) -> bool:
        return self._test

    def alerts(self) -> bool:
        return self._error

    def zero_forbidden(self) -> bool:
        return self._zero_forbidden

    def set_zero_forbidden(self, forbid: bool) -> None:
        self._zero_forbidden = forbid

    def matrix_allowed(self) -> bool:
        return self._matrix_allowed

    def set_matrix_allowed(self, allow: bool) -> None:
        self._matrix_allowed = allow

    def handles_vector(self) -> bool:
        return self._handle_vector

    def set_handle_vector(self, handle: bool) -> None:
        self._handle_vector = handle

    def rational_polynomial(self) -> bool:
        return self._rational_polynomial

    def set_rational_polynomial(self, rational: bool) -> None:
        self._rational_polynomial = rational

    def custom_condition(self) -> str:
        return self._condition

    def set_custom_condition(self, condition: str) -> None:
        self._condition = condition

    def type(self) -> ArgumentType:
        return ArgumentType.FREE

    def copy(self) -> Argument:
        a = Argument(self._name, self._test, self._error)
        a._condition = self._condition
        a._zero_forbidden = self._zero_forbidden
        return a

    def print_short(self) -> str:
        return "any"

    def print_long(self) -> str:
        return "Any value"


class NumberArgument(Argument):
    """Argument that accepts numerical values."""

    def __init__(
        self,
        name: str = "",
        min_max: ArgumentMinMaxPreDefinition = ArgumentMinMaxPreDefinition.NONE,
        does_test: bool = True,
        does_error: bool = True,
    ) -> None:
        super().__init__(name, does_test, does_error)
        self._min: float | None = None
        self._max: float | None = None
        self._include_equals_min = False
        self._include_equals_max = False
        self._complex_allowed = True
        self._rational_number = False

    def type(self) -> ArgumentType:
        return ArgumentType.NUMBER

    def complex_allowed(self) -> bool:
        return self._complex_allowed

    def set_complex_allowed(self, allow: bool) -> None:
        self._complex_allowed = allow

    def print_short(self) -> str:
        return "number"


class IntegerArgument(Argument):
    """Argument that accepts integer values."""

    def __init__(
        self,
        name: str = "",
        min_max: ArgumentMinMaxPreDefinition = ArgumentMinMaxPreDefinition.NONE,
        does_test: bool = True,
        does_error: bool = True,
    ) -> None:
        super().__init__(name, does_test, does_error)
        self._min: int | None = None
        self._max: int | None = None

    def type(self) -> ArgumentType:
        return ArgumentType.INTEGER

    def print_short(self) -> str:
        return "integer"


class SymbolicArgument(Argument):
    """Argument that accepts variables and symbolic structures."""

    def type(self) -> ArgumentType:
        return ArgumentType.SYMBOLIC

    def print_short(self) -> str:
        return "symbolic"


class TextArgument(Argument):
    """Argument that accepts text (symbolic) structures."""

    def type(self) -> ArgumentType:
        return ArgumentType.TEXT

    def print_short(self) -> str:
        return "text"


class DateArgument(Argument):
    """Argument that accepts date values."""

    def type(self) -> ArgumentType:
        return ArgumentType.DATE

    def print_short(self) -> str:
        return "date"


class VectorArgument(Argument):
    """Argument that accepts vectors."""

    def type(self) -> ArgumentType:
        return ArgumentType.VECTOR

    def print_short(self) -> str:
        return "vector"


class MatrixArgument(Argument):
    """Argument that accepts matrices."""

    def __init__(self, name: str = "", does_test: bool = True, does_error: bool = True) -> None:
        super().__init__(name, does_test, does_error)
        self._square_demanded = False

    def type(self) -> ArgumentType:
        return ArgumentType.MATRIX

    def square_demanded(self) -> bool:
        return self._square_demanded

    def set_square_demanded(self, square: bool) -> None:
        self._square_demanded = square

    def print_short(self) -> str:
        return "matrix"


class BooleanArgument(Argument):
    """Argument that accepts zero or one."""

    def type(self) -> ArgumentType:
        return ArgumentType.BOOLEAN

    def print_short(self) -> str:
        return "boolean"


class MathFunction(ExpressionItem):
    """Abstract base class for mathematical functions.

    A mathematical function should reimplement calculate() and copy().
    Argument definitions should be added in the constructor.
    """

    def __init__(
        self,
        name: str = "",
        argc: int = 0,
        max_argc: int = 0,
        category: str = "",
        title: str = "",
        description: str = "",
        is_active: bool = True,
    ) -> None:
        super().__init__(category, name, title, description, True, False, is_active)
        self._argc = argc
        self._max_argc = max_argc if max_argc > 0 else argc
        self._default_values: list[str] = []
        self._argument_defs: dict[int, Argument] = {}
        self._condition = ""
        self._example = ""

    def type(self) -> ExpressionItemType:
        return ExpressionItemType.FUNCTION

    def subtype(self) -> int:
        return FunctionSubtype.FUNCTION

    def args(self) -> int:
        """Return the minimum number of arguments."""
        return self._argc

    def min_args(self) -> int:
        return self._argc

    def max_args(self) -> int:
        """Return the maximum number of arguments, or -1 for unlimited."""
        return self._max_argc

    def set_argument_definition(self, index: int, argdef: Argument) -> None:
        """Set the argument definition for an argument index."""
        self._argument_defs[index] = argdef

    def get_argument_definition(self, index: int) -> Argument | None:
        return self._argument_defs.get(index)

    def clear_argument_definitions(self) -> None:
        self._argument_defs.clear()

    def set_default_value(self, arg: int, value: str) -> None:
        """Set the default value for an optional argument."""
        while len(self._default_values) <= arg:
            self._default_values.append("")
        self._default_values[arg] = value

    def get_default_value(self, arg: int) -> str:
        if arg < len(self._default_values):
            return self._default_values[arg]
        return ""

    def condition(self) -> str:
        return self._condition

    def set_condition(self, condition: str) -> None:
        self._condition = condition

    def example(self) -> str:
        return self._example

    def set_example(self, example: str) -> None:
        self._example = example

    def calculate(
        self,
        vargs: list[MathStructure],
        eo: EvaluationOptions | None = None,
    ) -> MathStructure:
        """Calculate the function value from arguments.

        Subclasses must implement this method.

        Args:
            vargs: List of MathStructure arguments.
            eo: Optional evaluation options.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.calculate() not implemented")

    def copy(self) -> MathFunction:
        raise NotImplementedError

    def represents_positive(self, vargs: list[MathStructure]) -> bool:
        return False

    def represents_negative(self, vargs: list[MathStructure]) -> bool:
        return False

    def represents_real(self, vargs: list[MathStructure]) -> bool:
        return False

    def represents_integer(self, vargs: list[MathStructure]) -> bool:
        return False


class UserFunction(MathFunction):
    """A user-defined mathematical function.

    Defined using expression strings with placeholders:
    - \\x, \\y, \\z for arguments 1, 2, 3
    - \\a to \\u for arguments 4 to 24
    - Optional args use uppercase: \\X{default_value}
    """

    def __init__(
        self,
        category: str = "",
        name: str = "",
        formula: str = "",
        is_local: bool = True,
        argc: int = -1,
        title: str = "",
        description: str = "",
        max_argc: int = 0,
        is_active: bool = True,
    ) -> None:
        super().__init__(name, argc, max_argc, category, title, description, is_active)
        self._is_local = is_local
        self._formula = formula
        self._formula_calc = ""
        self._subfunctions: list[str] = []
        self._precalculate: list[bool] = []

        if argc < 0 and formula:
            # Auto-detect argument count from formula
            self._argc = self._detect_argc(formula)

    def subtype(self) -> int:
        return FunctionSubtype.USER_FUNCTION

    def formula(self) -> str:
        return self._formula

    def internal_formula(self) -> str:
        return self._formula_calc or self._formula

    def set_formula(self, formula: str, argc: int = -1, max_argc: int = 0) -> None:
        self._formula = formula
        if argc >= 0:
            self._argc = argc
            self._max_argc = max_argc if max_argc > 0 else argc
        else:
            self._argc = self._detect_argc(formula)

    def add_subfunction(self, subfunction: str, precalculate: bool = True) -> None:
        self._subfunctions.append(subfunction)
        self._precalculate.append(precalculate)

    def count_subfunctions(self) -> int:
        return len(self._subfunctions)

    def copy(self) -> UserFunction:
        f = UserFunction(self._category, self.name(), self._formula, self._is_local,
                         self._argc, self._title, self._description, self._max_argc,
                         self._is_active)
        return f

    @staticmethod
    def _detect_argc(formula: str) -> int:
        """Auto-detect the number of arguments from the formula."""
        max_arg = 0
        arg_chars = set("xyzabcdefghijklmnopqrstu")
        i = 0
        while i < len(formula):
            if formula[i] == "\\":
                if i + 1 < len(formula):
                    c = formula[i + 1].lower()
                    if c in arg_chars:
                        idx = "xyzabcdefghijklmnopqrstu".index(c) + 1
                        max_arg = max(max_arg, idx)
                    elif c.isdigit():
                        # Subfunction reference
                        pass
                i += 2
            else:
                i += 1
        return max_arg

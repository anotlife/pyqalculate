"""Enums, constants, and option structures for PyQalculate.

This module mirrors the enums and option structs from libqalculate's includes.h,
providing Python equivalents for all the core types used throughout the library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

QALCULATE_MAJOR_VERSION = 5
QALCULATE_MINOR_VERSION = 11
QALCULATE_MICRO_VERSION = 0

# ---------------------------------------------------------------------------
# Expression item types
# ---------------------------------------------------------------------------


class ExpressionItemType(IntEnum):
    """Type of ExpressionItem."""
    VARIABLE = 0
    FUNCTION = 1
    UNIT = 2


# ---------------------------------------------------------------------------
# Structure types (MathStructure node types)
# ---------------------------------------------------------------------------


class StructureType(IntEnum):
    """Types for MathStructure nodes."""
    MULTIPLICATION = 0
    INVERSE = 1
    DIVISION = 2
    ADDITION = 3
    NEGATE = 4
    POWER = 5
    NUMBER = 6
    UNIT = 7
    SYMBOLIC = 8
    FUNCTION = 9
    VARIABLE = 10
    VECTOR = 11
    BITWISE_AND = 12
    BITWISE_OR = 13
    BITWISE_XOR = 14
    BITWISE_NOT = 15
    LOGICAL_AND = 16
    LOGICAL_OR = 17
    LOGICAL_XOR = 18
    LOGICAL_NOT = 19
    COMPARISON = 20
    UNDEFINED = 21
    ABORTED = 22
    DATETIME = 23
    ASSIGNMENT = 24
    MATRIX = 25
    UNIT_CONVERSION = 26
    FACTORIAL = 27
    WHERE = 28


# ---------------------------------------------------------------------------
# Math operations
# ---------------------------------------------------------------------------


class MathOperation(IntEnum):
    """Mathematical operations."""
    MULTIPLY = 0
    DIVIDE = 1
    ADD = 2
    SUBTRACT = 3
    RAISE = 4
    EXP10 = 5
    LOGICAL_AND = 6
    LOGICAL_OR = 7
    LOGICAL_XOR = 8
    BITWISE_AND = 9
    BITWISE_OR = 10
    BITWISE_XOR = 11
    LESS = 12
    GREATER = 13
    EQUALS_LESS = 14
    EQUALS_GREATER = 15
    EQUALS = 16
    NOT_EQUALS = 17


# ---------------------------------------------------------------------------
# Comparison types
# ---------------------------------------------------------------------------


class ComparisonType(IntEnum):
    """Comparison signs for comparison structures."""
    LESS = 0
    GREATER = 1
    EQUALS_LESS = 2
    EQUALS_GREATER = 3
    EQUALS = 4
    NOT_EQUALS = 5


class ComparisonResult(IntEnum):
    """Result of comparing two values."""
    EQUAL = 0
    GREATER = 1
    LESS = 2
    EQUAL_OR_GREATER = 3
    EQUAL_OR_LESS = 4
    NOT_EQUAL = 5
    UNKNOWN = 6
    EQUAL_LIMITS = 7
    CONTAINS = 8
    CONTAINED = 9
    OVERLAPPING_LESS = 10
    OVERLAPPING_GREATER = 11


# ---------------------------------------------------------------------------
# Number types
# ---------------------------------------------------------------------------


class NumberType(IntEnum):
    """Types of Number values."""
    RATIONAL = 0
    FLOAT = 1
    PLUS_INFINITY = 2
    MINUS_INFINITY = 3


class IntegerType(IntEnum):
    """Integer type constraints."""
    NONE = 0
    SINT = 1
    UINT = 2
    ULONG = 3
    SLONG = 4
    SIZE = 5


# ---------------------------------------------------------------------------
# Assumptions
# ---------------------------------------------------------------------------


class AssumptionType(IntEnum):
    """Type assumption for unknown variables. Each type is a subset of the one above."""
    NONE = 0
    NONMATRIX = 1
    NUMBER = 2
    COMPLEX = 3
    REAL = 4
    RATIONAL = 5
    INTEGER = 6
    BOOLEAN = 7


class AssumptionSign(IntEnum):
    """Signedness assumption."""
    UNKNOWN = 0
    POSITIVE = 1
    NONNEGATIVE = 2
    NEGATIVE = 3
    NONPOSITIVE = 4
    NONZERO = 5


# ---------------------------------------------------------------------------
# Variable subtypes
# ---------------------------------------------------------------------------


class VariableSubtype(IntEnum):
    """Type of variable."""
    VARIABLE = 0
    UNKNOWN_VARIABLE = 1
    KNOWN_VARIABLE = 2


# ---------------------------------------------------------------------------
# Unit subtypes
# ---------------------------------------------------------------------------


class UnitSubtype(IntEnum):
    """Type of unit."""
    BASE_UNIT = 0
    ALIAS_UNIT = 1
    COMPOSITE_UNIT = 2


# ---------------------------------------------------------------------------
# Prefix types
# ---------------------------------------------------------------------------


class PrefixType(IntEnum):
    """Types for prefix classes."""
    DECIMAL = 0
    BINARY = 1
    NUMBER = 2


# ---------------------------------------------------------------------------
# Function subtypes and argument types
# ---------------------------------------------------------------------------


class FunctionSubtype(IntEnum):
    """Type of mathematical function."""
    FUNCTION = 0
    USER_FUNCTION = 1
    DATA_SET = 2


class ArgumentType(IntEnum):
    """Argument types for function definitions."""
    FREE = 0
    SYMBOLIC = 1
    TEXT = 2
    DATE = 3
    FILE = 4
    INTEGER = 5
    NUMBER = 6
    VECTOR = 7
    MATRIX = 8
    EXPRESSION_ITEM = 9
    FUNCTION = 10
    UNIT = 11
    BOOLEAN = 12
    VARIABLE = 13
    ANGLE = 14
    SET = 15
    DATA_OBJECT = 16
    DATA_PROPERTY = 17


class ArgumentMinMaxPreDefinition(IntEnum):
    """Predefined max/min values for number and integer arguments."""
    NONE = 0
    POSITIVE = 1
    NONZERO = 2
    NONNEGATIVE = 3
    NEGATIVE = 4


# ---------------------------------------------------------------------------
# Data property types
# ---------------------------------------------------------------------------


class PropertyType(IntEnum):
    """Data property value types."""
    EXPRESSION = 0
    NUMBER = 1
    STRING = 2


# ---------------------------------------------------------------------------
# Parsing modes
# ---------------------------------------------------------------------------


class ParsingMode(IntEnum):
    """Expression parsing modes."""
    ADAPTIVE = 0
    IMPLICIT_MULTIPLICATION_FIRST = 1
    CONVENTIONAL = 2
    CHAIN = 3
    RPN = 4


# ---------------------------------------------------------------------------
# Approximation / evaluation modes
# ---------------------------------------------------------------------------


class ApproximationMode(IntEnum):
    """How exact the result must be."""
    EXACT = 0
    TRY_EXACT = 1
    APPROXIMATE = 2
    EXACT_VARIABLES = 3


class StructuringMode(IntEnum):
    """How the result is structured."""
    NONE = 0
    EXPAND = 1
    FACTORIZE = 2
    HYBRID = 3


class AutoPostConversion(IntEnum):
    """Automatic unit conversion after calculation."""
    NONE = 0
    OPTIMAL_SI = 1
    BASE = 2
    OPTIMAL = 3


class MixedUnitsConversion(IntEnum):
    """How mixed units are handled."""
    NONE = 0
    DOWNWARDS_KEEP = 1
    DOWNWARDS = 2
    DEFAULT = 3
    FORCE_INTEGER = 4
    FORCE_ALL = 5


class ReadPrecisionMode(IntEnum):
    """How precision is read from number of digits."""
    DONT_READ = 0
    ALWAYS_READ = 1
    WHEN_DECIMALS = 2


class AngleUnit(IntEnum):
    """Default angle unit for trigonometric functions."""
    NONE = 0
    RADIANS = 1
    DEGREES = 2
    GRADIANS = 3
    CUSTOM = 4


class ComplexNumberForm(IntEnum):
    """Complex number display form."""
    RECTANGULAR = 0
    EXPONENTIAL = 1
    POLAR = 2
    CIS = 3


class IntervalCalculation(IntEnum):
    """Algorithm for uncertainty propagation / intervals."""
    NONE = 0
    VARIANCE_FORMULA = 1
    INTERVAL_ARITHMETIC = 2
    SIMPLE_INTERVAL_ARITHMETIC = 3


# ---------------------------------------------------------------------------
# Print / display options
# ---------------------------------------------------------------------------


class NumberFractionFormat(IntEnum):
    """How rational numbers are displayed."""
    DECIMAL = 0
    DECIMAL_EXACT = 1
    FRACTIONAL = 2
    COMBINED = 3
    FRACTIONAL_FIXED_DENOMINATOR = 4
    COMBINED_FIXED_DENOMINATOR = 5
    PERCENT = 6
    PERMILLE = 7
    PERMYRIAD = 8


class MultiplicationSign(IntEnum):
    """Sign used for display of multiplication."""
    ASTERISK = 0
    DOT = 1
    X = 2
    ALTDOT = 3


class DivisionSign(IntEnum):
    """Sign used for display of division."""
    SLASH = 0
    DIVISION_SLASH = 1
    DIVISION = 2


class BaseDisplay(IntEnum):
    """How prefixes for numbers in non-decimal bases are displayed."""
    NONE = 0
    NORMAL = 1
    ALTERNATIVE = 2
    SUFFIX = 3


class IntervalDisplay(IntEnum):
    """How number intervals are displayed."""
    SIGNIFICANT_DIGITS = 0
    INTERVAL = 1
    PLUSMINUS = 2
    MIDPOINT = 3
    LOWER = 4
    UPPER = 5
    CONCISE = 6
    RELATIVE = 7


class DigitGrouping(IntEnum):
    """Digit grouping separator mode."""
    NONE = 0
    STANDARD = 1
    LOCALE = 2


class DateTimeFormat(IntEnum):
    """Format for time and date."""
    ISO = 0
    LOCALE = 1


class TimeZone(IntEnum):
    """Time zone handling."""
    UTC = 0
    LOCAL = 1
    CUSTOM = 2


class ExpDisplay(IntEnum):
    """How scientific notation exponents are displayed."""
    DEFAULT = 0
    UPPERCASE_E = 1
    LOWERCASE_E = 2
    POWER_OF_10 = 3


class RoundingMode(IntEnum):
    """Rounding methods."""
    HALF_AWAY_FROM_ZERO = 0
    HALF_TO_EVEN = 1
    HALF_TO_ODD = 2
    HALF_TOWARD_ZERO = 3
    HALF_UP = 4
    HALF_DOWN = 5
    HALF_RANDOM = 6
    TOWARD_ZERO = 7
    AWAY_FROM_ZERO = 8
    UP = 9
    DOWN = 10


class UnicodeSigns(IntEnum):
    """Unicode sign display modes."""
    OFF = 0
    ON = 1
    ONLY_UNIT_EXPONENTS = 2
    WITHOUT_EXPONENTS = 3


class RepeatingDecimals(IntEnum):
    """Repeating decimal display modes."""
    OFF = 0
    ELLIPSIS = 1
    OVERLINE = 2


class SortFlags(IntEnum):
    """Sort flags."""
    DEFAULT = 1
    SCIENTIFIC = 2


# ---------------------------------------------------------------------------
# Plot enums
# ---------------------------------------------------------------------------


class PlotLegendPlacement(IntEnum):
    """Placement of legend in plots."""
    NONE = 0
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4
    BELOW = 5
    OUTSIDE = 6


class PlotStyle(IntEnum):
    """Plot type/style."""
    LINES = 0
    POINTS = 1
    POINTS_LINES = 2
    BOXES = 3
    HISTOGRAM = 4
    STEPS = 5
    CANDLESTICKS = 6
    DOTS = 7
    POLAR = 8


class PlotSmoothing(IntEnum):
    """Smoothing for plotted lines."""
    NONE = 0
    UNIQUE = 1
    CSPLINES = 2
    BEZIER = 3
    SBEZIER = 4


class PlotFileType(IntEnum):
    """File type for saving plot to image."""
    AUTO = 0
    PNG = 1
    PS = 2
    EPS = 3
    LATEX = 4
    SVG = 5
    FIG = 6
    PDF = 7


# ---------------------------------------------------------------------------
# Special base constants
# ---------------------------------------------------------------------------

BASE_ROMAN_NUMERALS = -1
BASE_TIME = -2
BASE_BINARY = 2
BASE_OCTAL = 8
BASE_DECIMAL = 10
BASE_DUODECIMAL = 12
BASE_HEXADECIMAL = 16
BASE_SEXAGESIMAL = 60
BASE_SEXAGESIMAL_2 = 62
BASE_SEXAGESIMAL_3 = 63
BASE_LATITUDE = 70
BASE_LATITUDE_2 = 71
BASE_LONGITUDE = 72
BASE_LONGITUDE_2 = 73
BASE_CUSTOM = -3
BASE_UNICODE = -4
BASE_GOLDEN_RATIO = -5
BASE_SUPER_GOLDEN_RATIO = -6
BASE_PI = -7
BASE_E = -8
BASE_SQRT2 = -9
BASE_BINARY_DECIMAL = -20
BASE_BIJECTIVE_26 = -26
BASE_FP16 = -30
BASE_FP32 = -31
BASE_FP64 = -32
BASE_FP128 = -33
BASE_FP80 = -34

# Special values for min_exp
EXP_BASE_3 = -3
EXP_PRECISION = -1
EXP_NONE = 0
EXP_PURE = 1
EXP_SCIENTIFIC = 3

# Unicode sign constants
SIGN_DEGREE = "°"
SIGN_POWER_0 = "⁰"
SIGN_POWER_1 = "¹"
SIGN_POWER_2 = "²"
SIGN_POWER_3 = "³"
SIGN_POWER_4 = "⁴"
SIGN_POWER_5 = "⁵"
SIGN_POWER_6 = "⁶"
SIGN_POWER_7 = "⁷"
SIGN_POWER_8 = "⁸"
SIGN_POWER_9 = "⁹"
SIGN_EURO = "€"
SIGN_POUND = "£"
SIGN_CENT = "¢"
SIGN_YEN = "¥"
SIGN_MICRO = "µ"
SIGN_PI = "π"
SIGN_MULTIPLICATION = "×"
SIGN_MULTIDOT = "⋅"
SIGN_DIVISION_SLASH = "∕"
SIGN_DIVISION = "÷"
SIGN_MINUS = "−"
SIGN_SQRT = "√"
SIGN_ALMOST_EQUAL = "≈"
SIGN_LESS_OR_EQUAL = "≤"
SIGN_GREATER_OR_EQUAL = "≥"
SIGN_NOT_EQUAL = "≠"
SIGN_INFINITY = "∞"
SIGN_PLUSMINUS = "±"

# Precision constants
DEFAULT_PRECISION = 8
EQUALS_PRECISION_DEFAULT = -1
EQUALS_PRECISION_LOWEST = -2
EQUALS_PRECISION_HIGHEST = -3


# ---------------------------------------------------------------------------
# Sort options
# ---------------------------------------------------------------------------


@dataclass
class SortOptions:
    """Options for ordering expression parts."""
    prefix_currencies: bool = True
    minus_last: bool = True


# ---------------------------------------------------------------------------
# Print options
# ---------------------------------------------------------------------------


@dataclass
class PrintOptions:
    """Options for formatting and display of mathematical structures/results."""
    min_exp: int = EXP_PRECISION
    base: int = BASE_DECIMAL
    base_display: BaseDisplay = BaseDisplay.NONE
    lower_case_numbers: bool = False
    lower_case_e: bool = False
    number_fraction_format: NumberFractionFormat = NumberFractionFormat.DECIMAL
    indicate_infinite_series: bool = False
    show_ending_zeroes: bool = False
    abbreviate_names: bool = True
    use_reference_names: bool = False
    place_units_separately: bool = True
    use_unit_prefixes: bool = True
    use_prefixes_for_all_units: bool = False
    use_prefixes_for_currencies: bool = False
    use_all_prefixes: bool = False
    use_denominator_prefix: bool = True
    negative_exponents: bool = False
    short_multiplication: bool = True
    limit_implicit_multiplication: bool = False
    allow_non_usable: bool = False
    use_unicode_signs: int = UnicodeSigns.OFF
    multiplication_sign: MultiplicationSign = MultiplicationSign.DOT
    division_sign: DivisionSign = DivisionSign.DIVISION_SLASH
    spacious: bool = True
    excessive_parenthesis: bool = False
    halfexp_to_sqrt: bool = True
    min_decimals: int = 0
    max_decimals: int = -1
    use_min_decimals: bool = True
    use_max_decimals: bool = True
    improve_division_multipliers: bool = True
    is_approximate: bool | None = None
    sort_options: SortOptions = field(default_factory=SortOptions)
    comma_sign: str = ""
    decimalpoint_sign: str = ""
    hide_underscore_spaces: bool = False
    preserve_format: bool = False
    allow_factorization: bool = False
    spell_out_logical_operators: bool = False
    restrict_to_parent_precision: bool = True
    restrict_fraction_length: bool = False
    exp_to_root: bool = False
    preserve_precision: bool = False
    interval_display: IntervalDisplay = IntervalDisplay.INTERVAL
    digit_grouping: DigitGrouping = DigitGrouping.NONE
    date_time_format: DateTimeFormat = DateTimeFormat.ISO
    time_zone: TimeZone = TimeZone.LOCAL
    custom_time_zone: int = 0
    twos_complement: bool = True
    hexadecimal_twos_complement: bool = False
    binary_bits: int = 0
    exp_display: ExpDisplay = ExpDisplay.DEFAULT
    duodecimal_symbols: bool = False
    rounding: RoundingMode = RoundingMode.HALF_AWAY_FROM_ZERO
    exact: bool = False
    approximate: bool = False
    precision: int = 0  # When > 0, evalf symbolic results to this many significant digits


# ---------------------------------------------------------------------------
# Parse options
# ---------------------------------------------------------------------------


@dataclass
class ParseOptions:
    """Options for parsing expressions."""
    variables_enabled: bool = True
    functions_enabled: bool = True
    unknowns_enabled: bool = True
    units_enabled: bool = True
    rpn: bool = False
    base: int = BASE_DECIMAL
    limit_implicit_multiplication: bool = False
    read_precision: ReadPrecisionMode = ReadPrecisionMode.DONT_READ
    dot_as_separator: bool = False
    comma_as_separator: bool = False
    brackets_as_parentheses: bool = False
    angle_unit: AngleUnit = AngleUnit.NONE
    preserve_format: bool = False
    parsing_mode: ParsingMode = ParsingMode.ADAPTIVE
    twos_complement: bool = False
    hexadecimal_twos_complement: bool = False
    binary_bits: int = 0


# ---------------------------------------------------------------------------
# Evaluation options
# ---------------------------------------------------------------------------


@dataclass
class EvaluationOptions:
    """Options for calculation."""
    approximation: ApproximationMode = ApproximationMode.TRY_EXACT
    sync_units: bool = True
    sync_nonlinear_unit_relations: bool = True
    keep_prefixes: bool = False
    calculate_variables: bool = True
    calculate_functions: bool = True
    test_comparisons: bool = True
    isolate_x: bool = True
    expand: bool = True
    combine_divisions: bool = False
    reduce_divisions: bool = True
    allow_complex: bool = True
    allow_infinite: bool = True
    assume_denominators_nonzero: bool = False
    warn_about_denominators_assumed_nonzero: bool = True
    split_squares: bool = True
    keep_zero_units: bool = True
    auto_post_conversion: AutoPostConversion = AutoPostConversion.OPTIMAL
    mixed_units_conversion: MixedUnitsConversion = MixedUnitsConversion.DEFAULT
    structuring: StructuringMode = StructuringMode.NONE
    parse_options: ParseOptions = field(default_factory=ParseOptions)
    do_polynomial_division: bool = True
    complex_number_form: ComplexNumberForm = ComplexNumberForm.RECTANGULAR
    local_currency_conversion: bool = True
    transform_trigonometric_functions: bool = True
    interval_calculation: IntervalCalculation = IntervalCalculation.VARIANCE_FORMULA


# ---------------------------------------------------------------------------
# Plot parameters
# ---------------------------------------------------------------------------


@dataclass
class PlotParameters:
    """Parameters for plotting functions."""
    title: str = ""
    y_label: str = ""
    x_label: str = ""
    filename: str = ""
    filetype: PlotFileType = PlotFileType.AUTO
    font: str = ""
    color: str = "blue"
    auto_y_min: bool = True
    auto_x_min: bool = True
    auto_y_max: bool = True
    auto_x_max: bool = True
    y_min: float = 0.0
    y_max: float = 0.0
    x_min: float = 0.0
    x_max: float = 0.0
    logarithmic_x: bool = False
    logarithmic_y: bool = False
    x_axis_with: bool = True
    grid: bool = True


@dataclass
class PlotDataParameters:
    """Parameters for a single data series in a plot."""
    title: str = ""
    style: PlotStyle = PlotStyle.LINES
    smoothing: PlotSmoothing = PlotSmoothing.NONE
    test_continuous: bool = False
    force_continuous: bool = False
    y_axis2: bool = False
    x_axis2: bool = False
    color: str = ""
    width: int = -1
    legend_placement: PlotLegendPlacement = PlotLegendPlacement.NONE

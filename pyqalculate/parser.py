"""Parser - expression parsing for PyQalculate.

Handles tokenization and parsing of mathematical expressions into
MathStructure trees.  Mirrors the C++ Calculator::parse() hierarchy
(Calculator-parse.cc) using a recursive-descent approach.

Operator precedence (lowest → highest):
  0  :=  assignment
  1  where
  2  ||
  3  &&
  4  |  OR           (bitwise or)
  5  XOR             (bitwise xor)
  6  &  AND          (bitwise and)
  7  == !=
  8  < > <= >=
  9  << >>
  10 + -
  11 * / % // mod \\   (multiply / divide / modulo / integer-div)
  12 ^ **             (power)
  13 unary - + NOT ~
  14 postfix ! % ‰ bp
  15 primary  (number | identifier | function-call | paren | bracket)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from pyqalculate.math_structure import MathStructure
from pyqalculate.number import Number
from pyqalculate.types import (
    ComparisonType,
    ParseOptions,
    StructureType,
)

if TYPE_CHECKING:
    from pyqalculate.calculator import Calculator


# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------

class TT(Enum):
    """Token type enumeration."""
    NUMBER = auto()
    IDENT = auto()        # identifier (variable / function / unit / keyword)
    STRING = auto()       # "quoted string"
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    DSLASH = auto()       # //
    BACKSLASH = auto()    # \  (integer division)
    PERCENT = auto()
    CARET = auto()        # ^
    DSTAR = auto()        # **
    BANG = auto()         # !
    AMP = auto()          # &
    PIPE = auto()         # |
    DPIPE = auto()        # ||
    DAMP = auto()         # &&
    LT = auto()
    GT = auto()
    LE = auto()           # <=
    GE = auto()           # >=
    EQ = auto()           # ==
    NE = auto()           # !=
    DLT = auto()          # <<
    DGT = auto()          # >>
    TILDE = auto()        # ~  (bitwise not)
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    ASSIGN = auto()       # :=
    TO = auto()           # to / ->
    PLUSMINUS = auto()    # ±  +/-
    AT = auto()           # @ (backslash variable prefix marker)
    WHERE = auto()        # where keyword
    DOT = auto()          # .  (dot product)
    DOT_STAR = auto()     # .* (Hadamard / element-wise product)
    EOF = auto()


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Token:
    type: TT
    value: str
    pos: int = 0


# ---------------------------------------------------------------------------
# Key-words that are recognised as operator-like tokens
# ---------------------------------------------------------------------------

_KEYWORD_MAP: dict[str, TT] = {
    "and": TT.AMP,      # bitwise AND
    "or": TT.PIPE,      # bitwise OR
    "xor": TT.CARET,    # bitwise xor
    "not": TT.TILDE,    # logical/bitwise not
    "mod": TT.DSLASH,   # modulo (distinct token so postfix % doesn't eat it)
    "to": TT.TO,
    "where": TT.WHERE,
}


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

class _Tokenizer:
    """Low-level tokenizer that converts an expression string into tokens."""

    __slots__ = ("src", "pos", "len")

    def __init__(self, src: str) -> None:
        # Strip comments
        comment_idx = src.find("#")
        if comment_idx >= 0:
            src = src[:comment_idx]
        self.src = src
        self.pos = 0
        self.len = len(src)

    # -- helpers --

    def _peek(self, offset: int = 0) -> str:
        p = self.pos + offset
        return self.src[p] if p < self.len else ""

    def _advance(self, n: int = 1) -> str:
        start = self.pos
        self.pos = min(self.pos + n, self.len)
        return self.src[start:self.pos]

    def _skip_ws(self) -> None:
        while self.pos < self.len and self.src[self.pos] in " \t\n\r":
            self.pos += 1

    # -- main --

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self.pos < self.len:
            self._skip_ws()
            if self.pos >= self.len:
                break
            ch = self.src[self.pos]

            # -- backslash: variable prefix (\x \a \b) or integer-division operator --
            if ch == "\\":
                start = self.pos
                self.pos += 1
                # If followed by letter or underscore → variable prefix
                if self.pos < self.len and (self.src[self.pos].isalpha() or self.src[self.pos] == "_"):
                    ident = ""
                    while self.pos < self.len and (self.src[self.pos].isalnum() or self.src[self.pos] == "_"):
                        ident += self.src[self.pos]
                        self.pos += 1
                    tokens.append(Token(TT.IDENT, "\\" + ident, start))
                else:
                    # integer-division operator (followed by digit, space, operator, etc.)
                    tokens.append(Token(TT.BACKSLASH, "\\", start))
                continue

            # -- numbers --
            if ch.isdigit() or (ch == "." and self.pos + 1 < self.len and self.src[self.pos + 1].isdigit()):
                tokens.append(self._read_number())
                continue

            # -- identifiers / keywords --
            if ch.isalpha() or ch == "_" or ch == '"':
                if ch == '"':
                    tokens.append(self._read_string())
                else:
                    tokens.append(self._read_ident())
                continue

            # -- two-char operators --
            two = self.src[self.pos:self.pos + 2]
            if two == ":=":
                tokens.append(Token(TT.ASSIGN, ":=", self.pos))
                self.pos += 2
                continue
            if two == "=:":
                tokens.append(Token(TT.ASSIGN, "=:", self.pos))
                self.pos += 2
                continue
            if two == "||":
                tokens.append(Token(TT.DPIPE, "||", self.pos))
                self.pos += 2
                continue
            if two == "&&":
                tokens.append(Token(TT.DAMP, "&&", self.pos))
                self.pos += 2
                continue
            if two == "<=":
                tokens.append(Token(TT.LE, "<=", self.pos))
                self.pos += 2
                continue
            if two == ">=":
                tokens.append(Token(TT.GE, ">=", self.pos))
                self.pos += 2
                continue
            if two == "==":
                tokens.append(Token(TT.EQ, "==", self.pos))
                self.pos += 2
                continue
            if two == "!=":
                tokens.append(Token(TT.NE, "!=", self.pos))
                self.pos += 2
                continue
            if two == "<<":
                tokens.append(Token(TT.DLT, "<<", self.pos))
                self.pos += 2
                continue
            if two == ">>":
                tokens.append(Token(TT.DGT, ">>", self.pos))
                self.pos += 2
                continue
            if two == "//":
                tokens.append(Token(TT.DSLASH, "//", self.pos))
                self.pos += 2
                continue
            if two == "**":
                tokens.append(Token(TT.DSTAR, "**", self.pos))
                self.pos += 2
                continue
            if two == "+-" or (self.pos + 2 < self.len and self.src[self.pos:self.pos + 3] == "+/-"):
                is_slash = self.src[self.pos:self.pos + 3] == "+/-"
                tokens.append(Token(TT.PLUSMINUS, "+/-", self.pos))
                self.pos += 3 if is_slash else 2
                continue
            if two == "->":
                tokens.append(Token(TT.TO, "->", self.pos))
                self.pos += 2
                continue
            if two == ".*":
                tokens.append(Token(TT.DOT_STAR, ".*", self.pos))
                self.pos += 2
                continue

            # -- single-char operators --
            op_map = {
                "+": TT.PLUS, "-": TT.MINUS, "*": TT.STAR, "/": TT.SLASH,
                "%": TT.PERCENT, "^": TT.CARET, "!": TT.BANG, "&": TT.AMP,
                "|": TT.PIPE, "<": TT.LT, ">": TT.GT, "~": TT.TILDE,
                "=": TT.EQ, ".": TT.DOT,
                "(": TT.LPAREN, ")": TT.RPAREN, "[": TT.LBRACKET,
                "]": TT.RBRACKET, ",": TT.COMMA, ";": TT.SEMICOLON,
            }
            if ch == "\u00b1":  # ±
                tokens.append(Token(TT.PLUSMINUS, "\u00b1", self.pos))
                self.pos += 1
                continue
            if ch == "\u2030":  # ‰
                tokens.append(Token(TT.PERCENT, "\u2030", self.pos))
                self.pos += 1
                continue
            if ch in op_map:
                tokens.append(Token(op_map[ch], ch, self.pos))
                self.pos += 1
                continue

            # unknown char – skip
            self.pos += 1

        tokens.append(Token(TT.EOF, "", self.pos))
        return self._postprocess_time_units(tokens)

    @staticmethod
    def _postprocess_time_units(tokens: list[Token]) -> list[Token]:
        """Insert '+' between time-unit expressions.

        Transforms e.g. ``10 h 31 min`` → ``10 h + 31 min`` so that
        time-unit juxtaposition is treated as addition, not multiplication.
        """
        _TIME_UNITS = frozenset({
            "h", "hr", "hour", "hours",
            "min", "minute", "minutes",
            "s", "sec", "second", "seconds",
        })
        result: list[Token] = []
        for i, tok in enumerate(tokens):
            result.append(tok)
            # Pattern: IDENT(time_unit) NUMBER IDENT(time_unit)
            # Insert '+' between IDENT(time_unit) and NUMBER
            if (tok.type == TT.IDENT and tok.value.lower() in _TIME_UNITS
                    and i + 1 < len(tokens) and tokens[i + 1].type == TT.NUMBER
                    and i + 2 < len(tokens) and tokens[i + 2].type == TT.IDENT
                    and tokens[i + 2].value.lower() in _TIME_UNITS):
                result.append(Token(TT.PLUS, "+", tok.pos))
        return result

    # -- sub-tokenizers --

    def _read_number(self) -> Token:
        start = self.pos
        num = ""
        # integer part
        while self.pos < self.len and self.src[self.pos].isdigit():
            num += self.src[self.pos]
            self.pos += 1
        # Check for hex literal: 0xABC or 0XABC
        if num == "0" and self.pos < self.len and self.src[self.pos] in "xX":
            self.pos += 1  # skip 'x'
            hex_digits = ""
            while self.pos < self.len and self.src[self.pos] in "0123456789abcdefABCDEF":
                hex_digits += self.src[self.pos]
                self.pos += 1
            if hex_digits:
                return Token(TT.NUMBER, str(int(hex_digits, 16)), start)
            # No hex digits after 0x — backtrack to just "0"
            self.pos = start + 1
            return Token(TT.NUMBER, "0", start)
        # Check for date pattern: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
        if (len(num) == 4 and self.pos < self.len and self.src[self.pos] == "-"
                and self.pos + 3 < self.len and self.src[self.pos + 1].isdigit()
                and self.src[self.pos + 2].isdigit() and self.src[self.pos + 3] == "-"):
            # Looks like a date: consume YYYY-MM-DD
            date_str = num  # year
            while self.pos < self.len and self.src[self.pos] in "-0123456789T:.":
                date_str += self.src[self.pos]
                self.pos += 1
            return Token(TT.STRING, date_str, start)
        # Check for time pattern: HH:MM or H:MM (1-2 digit hours)
        if (len(num) <= 2 and self.pos < self.len and self.src[self.pos] == ":"
                and self.pos + 1 < self.len and self.src[self.pos + 1].isdigit()):
            self.pos += 1  # skip ':'
            minutes_str = ""
            while self.pos < self.len and self.src[self.pos].isdigit():
                minutes_str += self.src[self.pos]
                self.pos += 1
            hours = int(num)
            minutes = int(minutes_str) if minutes_str else 0
            total_minutes = hours * 60 + minutes
            return Token(TT.NUMBER, str(total_minutes), start)
        # decimal part
        if self.pos < self.len and self.src[self.pos] == ".":
            # peek ahead: don't consume '.' if followed by identifier char (e.g. "3.pi")
            if self.pos + 1 < self.len and (self.src[self.pos + 1].isdigit()):
                num += "."
                self.pos += 1
                while self.pos < self.len and self.src[self.pos].isdigit():
                    num += self.src[self.pos]
                    self.pos += 1
        # scientific notation
        if self.pos < self.len and self.src[self.pos] in "eE":
            exp_ch = self.src[self.pos]
            # check that it's really an exponent (not an identifier start)
            after = self.pos + 1
            if after < self.len and (self.src[after].isdigit() or
                (self.src[after] in "+-" and after + 1 < self.len and self.src[after + 1].isdigit())):
                num += exp_ch
                self.pos += 1
                if self.pos < self.len and self.src[self.pos] in "+-":
                    num += self.src[self.pos]
                    self.pos += 1
                while self.pos < self.len and self.src[self.pos].isdigit():
                    num += self.src[self.pos]
                    self.pos += 1
        return Token(TT.NUMBER, num, start)

    def _read_ident(self) -> Token:
        start = self.pos
        ident = ""
        while self.pos < self.len and (self.src[self.pos].isalnum() or self.src[self.pos] == "_"):
            ident += self.src[self.pos]
            self.pos += 1
        # check for special suffixes attached to identifier: "bp" suffix for basis points
        if ident.lower() == "bp" and len(ident) == 2:
            return Token(TT.PERCENT, "bp", start)
        # check keyword map — but only if not followed by '(' (function call)
        lower = ident.lower()
        if lower in _KEYWORD_MAP:
            # If followed by '(', treat as function name (IDENT), not keyword
            if self.pos < self.len and self.src[self.pos] == '(':
                return Token(TT.IDENT, ident, start)
            return Token(_KEYWORD_MAP[lower], ident, start)
        return Token(TT.IDENT, ident, start)

    def _read_string(self) -> Token:
        start = self.pos
        self.pos += 1  # skip opening "
        content = ""
        while self.pos < self.len and self.src[self.pos] != '"':
            if self.src[self.pos] == "\\" and self.pos + 1 < self.len:
                self.pos += 1
            content += self.src[self.pos]
            self.pos += 1
        if self.pos < self.len:
            self.pos += 1  # skip closing "
        return Token(TT.STRING, content, start)


# ---------------------------------------------------------------------------
# Parser (recursive descent)
# ---------------------------------------------------------------------------

class Parser:
    """Expression parser.

    Tokenizes and parses mathematical expression strings into MathStructure
    trees.  Supports implicit multiplication, unit parsing, function calls,
    and various parsing modes.

    This is the Python equivalent of libqalculate's Calculator::parse() methods.
    """

    def __init__(self, calculator: Calculator | None = None) -> None:
        self._calculator = calculator

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(
        self,
        expression: str,
        po: ParseOptions | None = None,
    ) -> MathStructure:
        """Parse an expression string into a MathStructure."""
        if po is None:
            po = ParseOptions()

        expr = expression.strip()
        if not expr:
            return MathStructure.undefined()

        tok = _Tokenizer(expr)
        tokens = tok.tokenize()
        result, _pos = self._parse_assignment(tokens, 0, po)
        return result

    def parse_and_calculate(
        self,
        expression: str,
        po: ParseOptions | None = None,
    ) -> MathStructure:
        """Parse and immediately evaluate an expression."""
        mstruct = self.parse(expression, po)
        return mstruct.evaluate()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tok(tokens: list[Token], pos: int) -> Token:
        if pos < len(tokens):
            return tokens[pos]
        return Token(TT.EOF, "", -1)

    @staticmethod
    def _match(tokens: list[Token], pos: int, tt: TT | tuple[TT, ...]) -> bool:
        if pos >= len(tokens):
            return False
        if isinstance(tt, tuple):
            return tokens[pos].type in tt
        return tokens[pos].type == tt

    def _parse_timezone_target(
        self, tokens: list[Token], pos: int,
    ) -> tuple[MathStructure | None, int]:
        """Try to parse a timezone target after 'to': utc, gmt, utc+N, utc-N.

        Returns (MathStructure, new_pos) if successful, or (None, pos) if not
        a timezone pattern (let normal parsing proceed).
        """
        tok = self._tok(tokens, pos)
        if tok.type != TT.IDENT:
            return None, pos
        lower = tok.value.lower()
        if lower not in ("utc", "gmt"):
            return None, pos
        tz_name = lower
        pos += 1
        # Check for +N or -N offset
        next_tok = self._tok(tokens, pos)
        if next_tok.type in (TT.PLUS, TT.MINUS):
            sign = 1 if next_tok.type == TT.PLUS else -1
            pos += 1
            num_tok = self._tok(tokens, pos)
            if num_tok.type == TT.NUMBER:
                offset = int(num_tok.value) * sign
                pos += 1
                offset_str = f"+{offset}" if offset >= 0 else str(offset)
                return MathStructure.from_symbol(f"{tz_name}{offset_str}"), pos
            # Not a number after +/- — backtrack (not a timezone)
            return None, pos - 1
        return MathStructure.from_symbol(tz_name), pos

    # ------------------------------------------------------------------
    # Precedence climbing – each level calls the next higher one
    # ------------------------------------------------------------------

    # Level 0 – assignment  (:=)
    def _parse_assignment(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_where(tokens, pos, po)
        if self._match(tokens, pos, TT.ASSIGN):
            pos += 1
            right, pos = self._parse_where(tokens, pos, po)
            return MathStructure.assignment(left, right), pos
        # Handle "to" for unit conversion: expr to unit
        if self._match(tokens, pos, TT.TO):
            pos += 1
            # Check for timezone target: utc, gmt, utc+N, utc-N, etc.
            tz_struct, new_pos = self._parse_timezone_target(tokens, pos)
            if tz_struct is not None:
                return MathStructure.unit_conversion(left, tz_struct), new_pos
            right, pos = self._parse_where(tokens, pos, po)
            return MathStructure.unit_conversion(left, right), pos
        return left, pos

    # Level 1 – where clause
    def _parse_where(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_logical_or(tokens, pos, po)
        if self._match(tokens, pos, TT.WHERE):
            pos += 1
            conditions: list[MathStructure] = []
            cond, pos = self._parse_comparison(tokens, pos, po)
            conditions.append(cond)
            return MathStructure.where_clause(left, conditions), pos
        return left, pos

    # Level 2 – logical OR  ||
    def _parse_logical_or(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_logical_and(tokens, pos, po)
        while self._match(tokens, pos, TT.DPIPE):
            pos += 1
            right, pos = self._parse_logical_and(tokens, pos, po)
            m = MathStructure(struct_type=StructureType.LOGICAL_OR)
            m._children = [left, right]
            left = m
        return left, pos

    # Level 3 – logical AND  &&
    def _parse_logical_and(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_bitwise_or(tokens, pos, po)
        while self._match(tokens, pos, TT.DAMP):
            pos += 1
            right, pos = self._parse_bitwise_or(tokens, pos, po)
            m = MathStructure(struct_type=StructureType.LOGICAL_AND)
            m._children = [left, right]
            left = m
        return left, pos

    # Level 4 – bitwise OR  |  / OR keyword
    def _parse_bitwise_or(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_bitwise_xor(tokens, pos, po)
        while self._match(tokens, pos, TT.PIPE):
            pos += 1
            right, pos = self._parse_bitwise_xor(tokens, pos, po)
            m = MathStructure(struct_type=StructureType.BITWISE_OR)
            m._children = [left, right]
            left = m
        return left, pos

    # Level 5 – bitwise XOR  XOR / ^
    def _parse_bitwise_xor(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_bitwise_and(tokens, pos, po)
        # Note: ^ is normally power; we use 'xor' keyword for bitwise xor
        # If someone uses ^ with non-power intent, that's handled elsewhere
        return left, pos

    # Level 6 – bitwise AND  & / AND keyword
    def _parse_bitwise_and(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_comparison(tokens, pos, po)
        while self._match(tokens, pos, TT.AMP):
            pos += 1
            right, pos = self._parse_comparison(tokens, pos, po)
            m = MathStructure(struct_type=StructureType.BITWISE_AND)
            m._children = [left, right]
            left = m
        return left, pos

    # Level 7-8 – comparison  == != < > <= >=
    def _parse_comparison(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_shift(tokens, pos, po)
        comp_map: dict[TT, ComparisonType] = {
            TT.LT: ComparisonType.LESS,
            TT.GT: ComparisonType.GREATER,
            TT.LE: ComparisonType.EQUALS_LESS,
            TT.GE: ComparisonType.EQUALS_GREATER,
            TT.EQ: ComparisonType.EQUALS,
            TT.NE: ComparisonType.NOT_EQUALS,
        }
        while self._tok(tokens, pos).type in comp_map:
            ct = comp_map[tokens[pos].type]
            pos += 1
            right, pos = self._parse_shift(tokens, pos, po)
            left = MathStructure.comparison(left, right, ct)
        return left, pos

    # Level 9 – shift  << >>
    def _parse_shift(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_additive(tokens, pos, po)
        while self._match(tokens, pos, (TT.DLT, TT.DGT)):
            op = tokens[pos].type
            pos += 1
            right, pos = self._parse_additive(tokens, pos, po)
            # Represent shift as function call: shift(base, amount)
            m = MathStructure.from_symbol("shift")
            m = MathStructure(struct_type=StructureType.FUNCTION)
            m._symbol = "shift"
            m._children = [left, right, MathStructure(1 if op == TT.DLT else -1)]
            left = m
        return left, pos

    # Level 10 – additive  + -
    def _parse_additive(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_multiplicative(tokens, pos, po)
        while self._match(tokens, pos, (TT.PLUS, TT.MINUS)):
            op = tokens[pos].type
            pos += 1
            right, pos = self._parse_multiplicative(tokens, pos, po)
            if op == TT.PLUS:
                left = left + right
            else:
                left = left - right
        return left, pos

    # Level 11 – multiplicative  * / % // \ mod  + implicit multiplication
    def _parse_multiplicative(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        left, pos = self._parse_power(tokens, pos, po)
        while True:
            if self._match(tokens, pos, (TT.STAR, TT.SLASH, TT.PERCENT, TT.DSLASH, TT.BACKSLASH)):
                op = tokens[pos].type
                op_value = tokens[pos].value
                pos += 1
                right, pos = self._parse_power(tokens, pos, po)
                if op == TT.STAR:
                    left = left * right
                elif op == TT.SLASH:
                    # If both operands are integer numbers, fold into rational
                    if (left.is_number() and right.is_number()
                            and left.number is not None and right.number is not None
                            and left.number.is_integer() and right.number.is_integer()):
                        num = left.number.to_int()
                        den = right.number.to_int()
                        if den != 0:
                            left = MathStructure.from_number(Number.from_rational(num, den))
                        else:
                            left = left / right
                    else:
                        left = left / right
                elif op == TT.PERCENT:
                    # percentage: divide by 100
                    left = left / MathStructure(100)
                elif op == TT.DSLASH:
                    # Check if it's 'mod' keyword or '//' integer division
                    if op_value.lower() == "mod":
                        # modulo: build as mod(left, right) function
                        m = MathStructure(struct_type=StructureType.FUNCTION)
                        m._symbol = "mod"
                        m._children = [left, right]
                        left = m
                    else:
                        # integer division
                        m = MathStructure(struct_type=StructureType.FUNCTION)
                        m._symbol = "trunc"
                        m._children = [left / right]
                        left = m
                elif op == TT.BACKSLASH:
                    m = MathStructure(struct_type=StructureType.FUNCTION)
                    m._symbol = "trunc"
                    m._children = [left / right]
                    left = m
            # Dot product: vector . vector
            elif self._match(tokens, pos, TT.DOT):
                pos += 1
                right, pos = self._parse_power(tokens, pos, po)
                left = self._build_function("dot", [left, right])
            # Hadamard (element-wise) product: matrix .* matrix
            elif self._match(tokens, pos, TT.DOT_STAR):
                pos += 1
                right, pos = self._parse_power(tokens, pos, po)
                left = self._build_function("hadamard", [left, right])
            # Implicit multiplication: number followed by ident/number/lparen
            # e.g., "2x" → 2*x, "2(3+4)" → 2*(3+4), "2 3" → 2*3
            elif (not po.limit_implicit_multiplication
                    and left.is_number() and self._match(tokens, pos,
                    (TT.IDENT, TT.NUMBER, TT.LPAREN, TT.LBRACKET))):
                right, pos = self._parse_power(tokens, pos, po)
                left = left * right
            else:
                break
        return left, pos

    # Level 12 – power  ^ **
    def _parse_power(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        # Power is right-associative: 2^3^2 = 2^(3^2)
        base, pos = self._parse_unary(tokens, pos, po)
        if self._match(tokens, pos, (TT.CARET, TT.DSTAR)):
            pos += 1
            exponent, pos = self._parse_power(tokens, pos, po)  # right-associative recursion
            base = base ** exponent
        return base, pos

    # Level 13 – unary  - + NOT ~
    def _parse_unary(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        tok = self._tok(tokens, pos)
        if tok.type == TT.MINUS:
            pos += 1
            # Use _parse_power so exponentiation binds tighter:
            # -x^2  →  -(x^2), not (-x)^2
            operand, pos = self._parse_power(tokens, pos, po)
            return -operand, pos
        if tok.type == TT.PLUS:
            pos += 1
            return self._parse_power(tokens, pos, po)
        if tok.type == TT.TILDE:
            pos += 1
            operand, pos = self._parse_power(tokens, pos, po)
            m = MathStructure(struct_type=StructureType.BITWISE_NOT)
            m._children = [operand]
            return m, pos
        return self._parse_postfix(tokens, pos, po)

    # Level 14 – postfix  ! % ‰ bp
    def _parse_postfix(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        operand, pos = self._parse_primary(tokens, pos, po)
        while True:
            tok = self._tok(tokens, pos)
            if tok.type == TT.BANG:
                pos += 1
                operand = MathStructure.factorial(operand)
            elif tok.type == TT.PERCENT:
                # percentage: divide by 100
                pos += 1
                if tok.value == "\u2030":  # ‰ per-mille
                    operand = operand / MathStructure(1000)
                elif tok.value == "bp":  # basis points
                    operand = operand / MathStructure(10000)
                else:  # %
                    operand = operand / MathStructure(100)
            elif tok.type == TT.PLUSMINUS:
                # uncertainty: value ± unc  → interval [value - unc, value + unc]
                pos += 1
                if self._match(tokens, pos, TT.NUMBER):
                    unc_tok = tokens[pos]
                    pos += 1
                    if operand.is_number() and operand.number is not None:
                        val = operand.number.to_float()
                        unc_val = float(unc_tok.value)
                        from pyqalculate.number import Number as Num
                        interval_num = Num.from_plusminus(val, unc_val)
                        operand = MathStructure.from_number(interval_num)
                    else:
                        # Non-numeric operand with ± — create uncertainty() function
                        # This will be evaluated later when the operand is resolved
                        unc_num = MathStructure(float(unc_tok.value))
                        operand = self._build_function("uncertainty", [operand, unc_num])
                continue
            else:
                break
        return operand, pos

    # Level 15 – primary  (number | identifier | function-call | paren | bracket)
    def _parse_primary(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        tok = self._tok(tokens, pos)

        # -- Number --
        if tok.type == TT.NUMBER:
            pos += 1
            m = self._make_number(tok.value)
            # check for implicit multiplication with following identifier/number/paren
            return self._maybe_implicit_mul(m, tokens, pos, po)

        # -- PlusMinus number (standalone ± at start of expression) --
        if tok.type == TT.PLUSMINUS:
            pos += 1
            # Treat ± as a marker; the next number is the uncertainty
            if self._match(tokens, pos, TT.NUMBER):
                unc_tok = tokens[pos]
                pos += 1
                # ±0.1 at start → interval [-0.1, 0.1]
                from pyqalculate.number import Number as Num
                unc_val = float(unc_tok.value)
                interval_num = Num.from_plusminus(0.0, unc_val)
                return MathStructure.from_number(interval_num), pos
            return MathStructure.undefined(), pos

        # -- Parenthesized expression / column vector --
        if tok.type == TT.LPAREN:
            pos += 1
            # empty parens
            if self._match(tokens, pos, TT.RPAREN):
                pos += 1
                return MathStructure(0), pos
            # Check for column vector using semicolons: (1; 2; 3)
            result, pos = self._parse_assignment(tokens, pos, po)
            # Check if this is a vector: (a; b; c)
            if self._match(tokens, pos, TT.SEMICOLON):
                elems = [result]
                while self._match(tokens, pos, TT.SEMICOLON):
                    pos += 1
                    if self._match(tokens, pos, TT.RPAREN):
                        break
                    elem, pos = self._parse_assignment(tokens, pos, po)
                    elems.append(elem)
                if self._match(tokens, pos, TT.RPAREN):
                    pos += 1
                return MathStructure.vector(*elems), pos
            if self._match(tokens, pos, TT.RPAREN):
                pos += 1
                # Implicit multiplication after closing paren
                return self._maybe_implicit_mul(result, tokens, pos, po)
            # Missing closing paren
            return self._maybe_implicit_mul(result, tokens, pos, po)

        # -- Bracket  [ ... ]  (vector / matrix) --
        if tok.type == TT.LBRACKET:
            return self._parse_bracket(tokens, pos, po)

        # -- Identifier / function call --
        if tok.type == TT.IDENT:
            return self._parse_ident_or_func(tokens, pos, po)

        # -- String literal --
        if tok.type == TT.STRING:
            pos += 1
            m = MathStructure.from_symbol(tok.value)
            return m, pos

        # fallback
        pos += 1
        return MathStructure.undefined(), pos

    # ------------------------------------------------------------------
    # Bracket / matrix parsing
    # ------------------------------------------------------------------

    def _parse_bracket(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        """Parse [ ... ] as vector or matrix."""
        pos += 1  # skip [
        rows: list[MathStructure] = []
        current_row: list[MathStructure] = []

        # Create a copy of po with implicit multiplication disabled inside brackets
        po_inner = ParseOptions(
            variables_enabled=po.variables_enabled,
            functions_enabled=po.functions_enabled,
            unknowns_enabled=po.unknowns_enabled,
            units_enabled=po.units_enabled,
            rpn=po.rpn,
            base=po.base,
            limit_implicit_multiplication=True,  # disable inside brackets
            read_precision=po.read_precision,
            dot_as_separator=po.dot_as_separator,
            comma_as_separator=po.comma_as_separator,
            brackets_as_parentheses=po.brackets_as_parentheses,
            angle_unit=po.angle_unit,
            preserve_format=po.preserve_format,
            parsing_mode=po.parsing_mode,
            twos_complement=po.twos_complement,
            hexadecimal_twos_complement=po.hexadecimal_twos_complement,
            binary_bits=po.binary_bits,
        )

        while not self._match(tokens, pos, TT.RBRACKET) and not self._match(tokens, pos, TT.EOF):
            elem, pos = self._parse_assignment(tokens, pos, po_inner)
            current_row.append(elem)

            tok = self._tok(tokens, pos)
            if tok.type == TT.SEMICOLON:
                # semicolon separates rows
                pos += 1
                rows.append(MathStructure.vector(*current_row))
                current_row = []
            elif tok.type == TT.COMMA:
                # comma separates elements within a row
                pos += 1
            elif tok.type == TT.RBRACKET:
                break
            elif tok.type in (TT.NUMBER, TT.LPAREN, TT.LBRACKET, TT.IDENT, TT.MINUS, TT.PLUS):
                # implicit space separator: next token starts a new element
                continue
            else:
                break

        if current_row:
            rows.append(MathStructure.vector(*current_row))

        if self._match(tokens, pos, TT.RBRACKET):
            pos += 1

        if len(rows) == 0:
            m = MathStructure.vector()
        elif len(rows) == 1:
            row = rows[0]
            # Check if all elements in the single row are vectors → treat as matrix
            if (row.is_vector() and len(row) > 0
                    and all(c.is_vector() for c in row)):
                m = MathStructure.matrix(list(row))
            else:
                m = row
        else:
            m = MathStructure.matrix(rows)

        return self._maybe_implicit_mul(m, tokens, pos, po)

    # ------------------------------------------------------------------
    # Identifier / function call
    # ------------------------------------------------------------------

    def _parse_ident_or_func(self, tokens: list[Token], pos: int, po: ParseOptions) -> tuple[MathStructure, int]:
        """Parse an identifier, possibly followed by (args) as a function call."""
        tok = tokens[pos]
        name = tok.value
        pos += 1

        # Handle backslash variables: \x → symbolic
        if name.startswith("\\"):
            m = MathStructure.from_symbol(name)
            return self._maybe_implicit_mul(m, tokens, pos, po)

        # Check if this is a function call (next token is LPAREN)
        if self._match(tokens, pos, TT.LPAREN) and po.functions_enabled:
            return self._parse_function_call(name, tokens, pos, po)

        # Try to look up in calculator
        if self._calculator is not None:
            from pyqalculate.types import ExpressionItemType
            from pyqalculate.variable import Variable
            from pyqalculate.unit import Unit
            from pyqalculate.function import MathFunction
            item = self._calculator.get_item(name)
            if item is not None:
                if item.type() == ExpressionItemType.VARIABLE and isinstance(item, Variable):
                    m = MathStructure.from_variable(item)
                    return self._maybe_implicit_mul(m, tokens, pos, po)
                if item.type() == ExpressionItemType.UNIT and isinstance(item, Unit):
                    m = MathStructure.from_unit(item)
                    return self._maybe_implicit_mul(m, tokens, pos, po)
                # Handle 0-arg functions (e.g., now, today) without parentheses
                if item.type() == ExpressionItemType.FUNCTION and isinstance(item, MathFunction):
                    if item.min_args() == 0:
                        func_m = MathStructure(struct_type=StructureType.FUNCTION)
                        func_m._function = item
                        func_m._children = []
                        return self._maybe_implicit_mul(func_m, tokens, pos, po)

        # Check for known constants
        lower = name.lower()
        if lower == "pi":
            m = MathStructure.from_symbol("pi")
            return self._maybe_implicit_mul(m, tokens, pos, po)
        if lower in ("i",) and po.unknowns_enabled:
            m = MathStructure.from_symbol(name)
            return self._maybe_implicit_mul(m, tokens, pos, po)

        # Unknown identifier → symbolic
        m = MathStructure.from_symbol(name)
        return self._maybe_implicit_mul(m, tokens, pos, po)

    def _parse_function_call(
        self,
        name: str,
        tokens: list[Token],
        pos: int,
        po: ParseOptions,
    ) -> tuple[MathStructure, int]:
        """Parse function_name(arg1; arg2; ...)."""
        pos += 1  # skip (
        args: list[MathStructure] = []

        # empty args
        if self._match(tokens, pos, TT.RPAREN):
            pos += 1
            func_m = self._build_function(name, args)
            return self._maybe_implicit_mul(func_m, tokens, pos, po)

        # parse args (separated by ; or ,)
        arg, pos = self._parse_assignment(tokens, pos, po)
        args.append(arg)
        while self._match(tokens, pos, (TT.SEMICOLON, TT.COMMA)):
            pos += 1
            if self._match(tokens, pos, TT.RPAREN):
                break
            arg, pos = self._parse_assignment(tokens, pos, po)
            args.append(arg)

        if self._match(tokens, pos, TT.RPAREN):
            pos += 1

        func_m = self._build_function(name, args)
        return self._maybe_implicit_mul(func_m, tokens, pos, po)

    def _build_function(self, name: str, args: list[MathStructure]) -> MathStructure:
        """Build a function MathStructure, looking up in calculator if possible."""
        if self._calculator is not None:
            func = self._calculator.get_function(name)
            if func is not None:
                m = MathStructure(struct_type=StructureType.FUNCTION)
                m._function = func
                m._children = args
                return m
        # Unknown function – store as symbolic function
        m = MathStructure(struct_type=StructureType.FUNCTION)
        m._symbol = name
        m._children = args
        return m

    # ------------------------------------------------------------------
    # Implicit multiplication
    # ------------------------------------------------------------------

    def _maybe_implicit_mul(
        self,
        left: MathStructure,
        tokens: list[Token],
        pos: int,
        po: ParseOptions,
    ) -> tuple[MathStructure, int]:
        """If the next token can start a primary expression, insert implicit multiplication.

        Uses _parse_power (not _parse_primary) for the right operand so that
        exponentiation binds tighter: ``3x^3`` → ``3 * (x^3)``, not ``(3x)^3``.
        """
        if po.limit_implicit_multiplication:
            # Even with limit, allow "number * identifier" (e.g. 2x → 2*x)
            tok = self._tok(tokens, pos)
            if left.is_number() and tok.type == TT.IDENT and not tok.value.startswith("\\"):
                lower = tok.value.lower()
                if lower not in _KEYWORD_MAP:
                    right, pos = self._parse_power(tokens, pos, po)
                    return left * right, pos
            return left, pos
        tok = self._tok(tokens, pos)
        if tok.type in (TT.NUMBER, TT.LPAREN, TT.LBRACKET):
            # e.g. "2(", "2[", "2 3"
            right, pos = self._parse_power(tokens, pos, po)
            return left * right, pos
        if tok.type == TT.IDENT and not tok.value.startswith("\\"):
            # e.g. "2x", "2pi", "x y"
            # But only if it's not a keyword like "to", "where", "mod"
            lower = tok.value.lower()
            if lower not in _KEYWORD_MAP:
                right, pos = self._parse_power(tokens, pos, po)
                return left * right, pos
        return left, pos

    # ------------------------------------------------------------------
    # Number construction
    # ------------------------------------------------------------------

    def _make_number(self, value_str: str) -> MathStructure:
        """Create a MathStructure number from a string."""
        try:
            if "." in value_str or "e" in value_str.lower():
                return MathStructure(float(value_str))
            return MathStructure(int(value_str))
        except ValueError:
            return MathStructure.from_symbol(value_str)

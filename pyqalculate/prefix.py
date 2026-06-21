"""Prefix classes - decimal (metric), binary, and number prefixes.

Mirrors libqalculate's Prefix hierarchy. A prefix is prepended to a unit
to specify a quantity multiplier (e.g., kilo in kilometer = 1000).
"""

from __future__ import annotations

from pyqalculate.expression_item import ExpressionName
from pyqalculate.number import Number
from pyqalculate.types import PrefixType


class Prefix:
    """Abstract base class for prefixes.

    A prefix has up to three names: long (e.g., "kilo"), short (e.g., "k"),
    and unicode. The value depends on the exponent of the prefixed unit.
    """

    def __init__(
        self,
        long_name: str = "",
        short_name: str = "",
        unicode_name: str = "",
    ) -> None:
        self._names: list[ExpressionName] = []
        if long_name:
            en = ExpressionName(long_name)
            en.abbreviation = False
            self._names.append(en)
        if short_name:
            en = ExpressionName(short_name)
            en.abbreviation = True
            self._names.append(en)
        if unicode_name:
            en = ExpressionName(unicode_name)
            en.abbreviation = True
            en.unicode = True
            self._names.append(en)

    # -- Name access --

    def short_name(self, return_long_if_no_short: bool = True) -> str:
        """Return the short name."""
        for n in self._names:
            if n.abbreviation and not n.unicode:
                return n.name
        if return_long_if_no_short:
            return self.long_name()
        return ""

    def long_name(self) -> str:
        """Return the long name."""
        for n in self._names:
            if not n.abbreviation:
                return n.name
        if self._names:
            return self._names[0].name
        return ""

    def unicode_name(self) -> str:
        """Return the unicode name."""
        for n in self._names:
            if n.unicode:
                return n.name
        return self.short_name()

    def name(self, short: bool = True, use_unicode: bool = False) -> str:
        """Return a preferred name."""
        if use_unicode:
            u = self.unicode_name()
            if u:
                return u
        if short:
            return self.short_name()
        return self.long_name()

    def preferred_name(
        self,
        abbreviation: bool = False,
        use_unicode: bool = False,
        plural: bool = False,
        reference: bool = False,
    ) -> ExpressionName:
        """Return the best-matching name."""
        if use_unicode:
            for n in self._names:
                if n.unicode:
                    return n
        if abbreviation:
            for n in self._names:
                if n.abbreviation and not n.unicode:
                    return n
        if self._names:
            return self._names[0]
        return ExpressionName()

    def set_short_name(self, name: str) -> None:
        # Replace existing short name or add
        for i, n in enumerate(self._names):
            if n.abbreviation and not n.unicode:
                self._names[i] = ExpressionName(name)
                self._names[i].abbreviation = True
                return
        en = ExpressionName(name)
        en.abbreviation = True
        self._names.append(en)

    def set_long_name(self, name: str) -> None:
        for i, n in enumerate(self._names):
            if not n.abbreviation:
                self._names[i] = ExpressionName(name)
                return
        en = ExpressionName(name)
        en.abbreviation = False
        self._names.insert(0, en)

    def set_unicode_name(self, name: str) -> None:
        for i, n in enumerate(self._names):
            if n.unicode:
                self._names[i] = ExpressionName(name)
                self._names[i].unicode = True
                self._names[i].abbreviation = True
                return
        en = ExpressionName(name)
        en.unicode = True
        en.abbreviation = True
        self._names.append(en)

    def has_name(self, name: str, case_sensitive: bool = True) -> int:
        """Return 1-based index of name, or 0 if not found."""
        for i, n in enumerate(self._names, 1):
            if case_sensitive:
                if n.name == name:
                    return i
            else:
                if n.name.lower() == name.lower():
                    return i
        return 0

    def count_names(self) -> int:
        return len(self._names)

    # -- Value (abstract) --

    def value(self, exponent: int = 1) -> Number:
        """Return the value of the prefix for the given unit exponent."""
        raise NotImplementedError

    def type(self) -> PrefixType:
        """Return the type of this prefix."""
        raise NotImplementedError


class DecimalPrefix(Prefix):
    """A decimal (metric) prefix.

    Value = 10^exponent. For example, kilo has exponent 3 (value = 1000).
    """

    def __init__(
        self,
        exponent: int,
        long_name: str = "",
        short_name: str = "",
        unicode_name: str = "",
    ) -> None:
        super().__init__(long_name, short_name, unicode_name)
        self._exponent = exponent

    def exponent(self, unit_exponent: int = 1) -> int:
        """Return the prefix exponent, adjusted for unit exponent."""
        return self._exponent * unit_exponent

    def set_exponent(self, exponent: int) -> None:
        self._exponent = exponent

    def value(self, exponent: int = 1) -> Number:
        """Return 10^(exponent * unit_exponent)."""
        return Number(10) ** Number(self._exponent * exponent)

    def type(self) -> PrefixType:
        return PrefixType.DECIMAL


class BinaryPrefix(Prefix):
    """A binary prefix.

    Value = 2^exponent. For example, kibi has exponent 10 (value = 1024).
    """

    def __init__(
        self,
        exponent: int,
        long_name: str = "",
        short_name: str = "",
        unicode_name: str = "",
    ) -> None:
        super().__init__(long_name, short_name, unicode_name)
        self._exponent = exponent

    def exponent(self, unit_exponent: int = 1) -> int:
        return self._exponent * unit_exponent

    def set_exponent(self, exponent: int) -> None:
        self._exponent = exponent

    def value(self, exponent: int = 1) -> Number:
        """Return 2^(exponent * unit_exponent)."""
        return Number(2) ** Number(self._exponent * exponent)

    def type(self) -> PrefixType:
        return PrefixType.BINARY


class NumberPrefix(Prefix):
    """A prefix with a free numerical value.

    Can use any number as the prefix value.
    """

    def __init__(
        self,
        value: Number,
        long_name: str = "",
        short_name: str = "",
        unicode_name: str = "",
    ) -> None:
        super().__init__(long_name, short_name, unicode_name)
        self._value = value

    def set_value(self, value: Number) -> None:
        self._value = value

    def value(self, exponent: int = 1) -> Number:
        return self._value ** exponent

    def type(self) -> PrefixType:
        return PrefixType.NUMBER

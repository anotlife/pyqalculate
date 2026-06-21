"""ExpressionName and base class for expression items.

Mirrors libqalculate's ExpressionItem class hierarchy: the abstract base for
functions, variables, and units that can appear in mathematical expressions.
"""

from __future__ import annotations

from pyqalculate.types import ExpressionItemType


class ExpressionName:
    """A name for an expression item (function, variable or unit).

    Each name has a text string and boolean flags describing its properties:
    abbreviation, suffix, unicode, plural, reference, avoid_input, case_sensitive.
    """

    __slots__ = (
        "name", "abbreviation", "suffix", "unicode", "plural",
        "reference", "avoid_input", "case_sensitive", "completion_only",
    )

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.abbreviation = len(name) == 1
        self.suffix = False
        self.unicode = False
        self.plural = False
        self.reference = False
        self.avoid_input = False
        self.case_sensitive = len(name) == 1
        self.completion_only = False

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ExpressionName):
            return self.name == other.name
        return NotImplemented

    def __repr__(self) -> str:
        return f"ExpressionName({self.name!r})"


class ExpressionItem:
    """Abstract base class for functions, variables and units.

    Expression items have one or more names used to reference them in
    mathematical expressions. Each name must be fully unique (with the
    exception that functions can share names with other item types).

    Items have an optional title and description. The category property
    organizes items for end users (subcategories separated by '/').

    A local item is created/edited by the end user.
    A builtin item has defining properties that should not be edited.
    An inactive item cannot be used in expressions.
    """

    def __init__(
        self,
        category: str = "",
        name: str = "",
        title: str = "",
        description: str = "",
        is_local: bool = True,
        is_builtin: bool = False,
        is_active: bool = True,
    ) -> None:
        self._category = category
        self._title = title
        self._description = description
        self._is_local = is_local
        self._is_changed = False
        self._is_builtin = is_builtin
        self._is_approximate = False
        self._is_active = is_active
        self._is_registered = False
        self._is_hidden = False
        self._is_destroyed = False
        self._ref_count = 0
        self._precision = 0
        self._names: list[ExpressionName] = []

        if name:
            self.add_name(name)

    # -- Name management --

    def name(self) -> str:
        """Return the primary name."""
        if self._names:
            return self._names[0].name
        return ""

    def reference_name(self) -> str:
        """Return the reference name."""
        for n in self._names:
            if n.reference:
                return n.name
        return self.name()

    def preferred_name(
        self,
        abbreviation: bool = False,
        use_unicode: bool = False,
        plural: bool = False,
        reference: bool = False,
    ) -> ExpressionName:
        """Return the name that best matches the given criteria."""
        if not self._names:
            return ExpressionName()
        # Simple heuristic: return first matching, or first overall
        for n in self._names:
            if abbreviation and not n.abbreviation:
                continue
            if plural and not n.plural:
                continue
            if reference and not n.reference:
                continue
            return n
        return self._names[0]

    def preferred_input_name(self, **kwargs: bool) -> ExpressionName:
        """Return the preferred name suitable for user input."""
        return self.preferred_name(**kwargs)

    def preferred_display_name(self, **kwargs: bool) -> ExpressionName:
        """Return the preferred name suitable for display."""
        return self.preferred_name(**kwargs)

    def get_name(self, index: int) -> ExpressionName | None:
        """Return name at 1-based index, or None."""
        if 1 <= index <= len(self._names):
            return self._names[index - 1]
        return None

    def set_name(self, name: str | ExpressionName, index: int = 1) -> None:
        """Set a name at the given 1-based index."""
        if isinstance(name, str):
            ename = ExpressionName(name)
        else:
            ename = name
        if 1 <= index <= len(self._names):
            self._names[index - 1] = ename
        else:
            self._names.append(ename)

    def add_name(self, name: str | ExpressionName, index: int = 0) -> None:
        """Add a name at the given position (0 = append)."""
        if isinstance(name, str):
            ename = ExpressionName(name)
        else:
            ename = name
        if index == 0:
            self._names.append(ename)
        else:
            self._names.insert(index - 1, ename)

    def count_names(self) -> int:
        return len(self._names)

    def clear_names(self) -> None:
        self._names.clear()

    def remove_name(self, index: int) -> None:
        if 1 <= index <= len(self._names):
            del self._names[index - 1]

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

    # -- Title / description --

    def title(self) -> str:
        return self._title or self.name()

    def set_title(self, title: str) -> None:
        self._title = title

    def description(self) -> str:
        return self._description

    def set_description(self, description: str) -> None:
        self._description = description

    # -- Category --

    def category(self) -> str:
        return self._category

    def set_category(self, category: str) -> None:
        self._category = category

    # -- State flags --

    def is_registered(self) -> bool:
        return self._is_registered

    def set_registered(self, is_registered: bool) -> None:
        self._is_registered = is_registered

    def is_local(self) -> bool:
        return self._is_local

    def is_builtin(self) -> bool:
        return self._is_builtin

    def is_approximate(self) -> bool:
        return self._is_approximate

    def set_approximate(self, is_approx: bool = True) -> None:
        self._is_approximate = is_approx

    def precision(self) -> int:
        return self._precision

    def set_precision(self, prec: int) -> None:
        self._precision = prec

    def is_active(self) -> bool:
        return self._is_active

    def set_active(self, is_active: bool) -> None:
        self._is_active = is_active

    def is_hidden(self) -> bool:
        return self._is_hidden

    def set_hidden(self, is_hidden: bool) -> None:
        self._is_hidden = is_hidden

    def has_changed(self) -> bool:
        return self._is_changed

    def set_changed(self, has_changed: bool = True) -> None:
        self._is_changed = has_changed

    # -- Reference counting --

    def ref_count(self) -> int:
        return self._ref_count

    def ref(self) -> None:
        self._ref_count += 1

    def unref(self) -> None:
        self._ref_count = max(0, self._ref_count - 1)

    # -- Abstract --

    def type(self) -> ExpressionItemType:
        """Return the type of this expression item."""
        raise NotImplementedError

    def subtype(self) -> int:
        """Return the subtype of this expression item."""
        raise NotImplementedError

    def copy(self) -> ExpressionItem:
        """Return a copy of this item."""
        raise NotImplementedError

    def destroy(self) -> bool:
        """Destroy this item (remove from calculator if registered)."""
        self._is_destroyed = True
        return True

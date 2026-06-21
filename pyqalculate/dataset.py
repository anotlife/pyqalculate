"""DataSet and DataProperty classes for structured data storage.

Mirrors libqalculate's DataSet class. A DataSet is a simple database
for storage of grouped values (e.g., planets with mass, radius, etc.).
DataSet is also a mathematical function: dataset(object, property).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyqalculate.function import MathFunction, Argument
from pyqalculate.types import PropertyType, FunctionSubtype, EvaluationOptions

if TYPE_CHECKING:
    from pyqalculate.math_structure import MathStructure
    from pyqalculate.unit import Unit


class DataProperty:
    """A data set property definition.

    Properties define the schema for data objects: name, title, description,
    unit, type, and various flags.
    """

    def __init__(
        self,
        parent: DataSet | None = None,
        name: str = "",
        title: str = "",
        description: str = "",
    ) -> None:
        self._parent = parent
        self._names: list[str] = []
        self._name_is_ref: list[bool] = []
        self._title = title
        self._description = description
        self._unit = ""
        self._is_approximate = False
        self._uses_brackets = False
        self._is_key = False
        self._is_case_sensitive = False
        self._is_hidden = False
        self._property_type = PropertyType.EXPRESSION

        if name:
            self.set_name(name, is_ref=True)

    def set_name(self, name: str, is_ref: bool = False) -> None:
        """Set the primary name."""
        if self._names:
            self._names[0] = name
            self._name_is_ref[0] = is_ref
        else:
            self._names.append(name)
            self._name_is_ref.append(is_ref)

    def add_name(self, name: str, is_ref: bool = False) -> None:
        self._names.append(name)
        self._name_is_ref.append(is_ref)

    def has_name(self, name: str) -> int:
        """Return 1-based index of name, or 0 if not found."""
        for i, n in enumerate(self._names, 1):
            if n == name:
                return i
        return 0

    def count_names(self) -> int:
        return len(self._names)

    def get_name(self, index: int = 1) -> str:
        if 1 <= index <= len(self._names):
            return self._names[index - 1]
        return ""

    def get_reference_name(self) -> str:
        for i, is_ref in enumerate(self._name_is_ref):
            if is_ref:
                return self._names[i]
        return self.get_name(1)

    def title(self, return_name_if_no_title: bool = True) -> str:
        if self._title:
            return self._title
        if return_name_if_no_title:
            return self.get_name(1)
        return ""

    def set_title(self, title: str) -> None:
        self._title = title

    def description(self) -> str:
        return self._description

    def set_description(self, description: str) -> None:
        self._description = description

    def unit(self) -> str:
        return self._unit

    def set_unit(self, unit: str) -> None:
        self._unit = unit

    def is_key(self) -> bool:
        return self._is_key

    def set_key(self, is_key: bool = True) -> None:
        self._is_key = is_key

    def is_hidden(self) -> bool:
        return self._is_hidden

    def set_hidden(self, is_hidden: bool = True) -> None:
        self._is_hidden = is_hidden

    def is_case_sensitive(self) -> bool:
        return self._is_case_sensitive

    def set_case_sensitive(self, case_sensitive: bool = True) -> None:
        self._is_case_sensitive = case_sensitive

    def uses_brackets(self) -> bool:
        return self._uses_brackets

    def set_uses_brackets(self, uses_brackets: bool = True) -> None:
        self._uses_brackets = uses_brackets

    def is_approximate(self) -> bool:
        return self._is_approximate

    def set_approximate(self, is_approximate: bool = True) -> None:
        self._is_approximate = is_approximate

    def property_type(self) -> PropertyType:
        return self._property_type

    def set_property_type(self, ptype: PropertyType) -> None:
        self._property_type = ptype


class DataObject:
    """A data set object consisting of property-value pairs."""

    def __init__(self, parent: DataSet | None = None) -> None:
        self._parent = parent
        self._properties: dict[str, str] = {}
        self._user_modified = False

    @property
    def name(self) -> str:
        """Return the name property value, or empty string if not set."""
        return self._properties.get("name", "")

    def set_property(self, property_name: str, value: str) -> None:
        """Set value for a property."""
        self._properties[property_name] = value

    def get_property(self, property_name: str) -> str:
        """Return the value for a property, or empty string if not set."""
        return self._properties.get(property_name, "")

    def erase_property(self, property_name: str) -> None:
        """Unset a property."""
        self._properties.pop(property_name, None)

    def is_user_modified(self) -> bool:
        return self._user_modified

    def set_user_modified(self, modified: bool = True) -> None:
        self._user_modified = modified

    def parent_set(self) -> DataSet | None:
        return self._parent


class DataSet(MathFunction):
    """A data set - a simple database for grouped values.

    A data set consists of properties (schema) and objects (rows).
    It is also a mathematical function: dataset(object, property).

    Example: "Planets" dataset with properties mass, radius, density
    and an object for each planet.
    """

    def __init__(
        self,
        category: str = "",
        name: str = "",
        default_file: str = "",
        title: str = "",
        description: str = "",
        is_local: bool = True,
    ) -> None:
        super().__init__(name, 2, 2, category, title, description, True)
        self._is_local = is_local
        self._file = default_file
        self._copyright = ""
        self._loaded = False
        self._properties: list[DataProperty] = []
        self._objects: list[DataObject] = []
        self._default_property = ""
        self._calculator: object = None  # back-reference to Calculator

    def subtype(self) -> int:
        return FunctionSubtype.DATA_SET

    def copy(self) -> DataSet:
        ds = DataSet(self._category, self.name(), self._file, self._title,
                     self._description, self._is_local)
        return ds

    # -- File management --

    def set_default_data_file(self, file: str) -> None:
        self._file = file

    def default_data_file(self) -> str:
        return self._file

    def set_copyright(self, copyright: str) -> None:
        self._copyright = copyright

    def copyright(self) -> str:
        return self._copyright

    def objects_loaded(self) -> bool:
        return self._loaded

    def set_objects_loaded(self, loaded: bool = True) -> None:
        self._loaded = loaded

    def load_objects(self, file_name: str | None = None) -> bool:
        """Load data objects from file. Stub - to be implemented."""
        # TODO: implement XML loading
        self._loaded = True
        return True

    # -- Default property --

    def set_default_property(self, property: str) -> None:
        self._default_property = property

    def default_property(self) -> str:
        return self._default_property

    # -- Property management --

    def add_property(self, dp: DataProperty) -> None:
        self._properties.append(dp)

    def del_property(self, dp: DataProperty) -> None:
        self._properties.remove(dp)

    def get_property_by_name(self, name: str) -> DataProperty | None:
        for p in self._properties:
            if p.has_name(name):
                return p
        return None

    def get_primary_key_property(self) -> DataProperty | None:
        for p in self._properties:
            if p.is_key():
                return p
        return None

    def get_first_property(self) -> DataProperty | None:
        return self._properties[0] if self._properties else None

    def count_properties(self) -> int:
        return len(self._properties)

    # -- Object management --

    def add_object(self, obj: DataObject) -> None:
        self._objects.append(obj)

    def del_object(self, obj: DataObject) -> None:
        self._objects.remove(obj)

    def get_object(self, name: str) -> DataObject | None:
        """Find an object by its primary key value (case-insensitive)."""
        key_prop = self.get_primary_key_property()
        if key_prop is None:
            return None
        key_name = key_prop.get_reference_name()
        name_lower = name.lower()
        for obj in self._objects:
            if obj.get_property(key_name).lower() == name_lower:
                return obj
        return None

    def count_objects(self) -> int:
        return len(self._objects)

    def get_all_objects(self) -> list[DataObject]:
        """Return all objects in the dataset."""
        return list(self._objects)

    def find_objects(self, property_name: str, value: str) -> list[DataObject]:
        """Find all objects where a property matches a value.

        Args:
            property_name: The property to check.
            value: The value to match (case-insensitive).

        Returns:
            List of matching DataObjects.
        """
        results = []
        for obj in self._objects:
            prop_val = obj.get_property(property_name)
            if prop_val and prop_val.lower() == value.lower():
                results.append(obj)
        return results

    def __len__(self) -> int:
        return len(self._objects)

    def __getitem__(self, index: int) -> DataObject:
        return self._objects[index]

    def __iter__(self):
        return iter(self._objects)

    # -- Query --

    def get_object_property(self, property_name: str, object_name: str) -> str:
        """Return the value of a property for an object."""
        obj = self.get_object(object_name)
        if obj is None:
            return ""
        prop = self.get_property_by_name(property_name)
        if prop is None:
            return ""
        return obj.get_property(prop.get_reference_name())

    # -- Function interface --

    def calculate(
        self,
        vargs: list[MathStructure],
        eo: EvaluationOptions | None = None,
    ) -> MathStructure:
        """Calculate: dataset(object, property).

        Looks up the property value for the given object and returns it as
        a MathStructure (number, optionally multiplied by a unit).
        """
        from pyqalculate.math_structure import MathStructure
        from pyqalculate.number import Number

        if len(vargs) < 2:
            return MathStructure.undefined()

        # Extract object name from first argument
        arg0 = vargs[0]
        if arg0.is_symbolic():
            object_name = arg0.symbol
        elif arg0.is_number():
            object_name = str(arg0.float_value())
        else:
            return MathStructure.undefined()

        # Extract property name from second argument
        arg1 = vargs[1]
        if arg1.is_symbolic():
            property_name = arg1.symbol
        elif arg1.is_number():
            property_name = str(arg1.float_value())
        else:
            return MathStructure.undefined()

        # Look up the raw value string
        value_str = self.get_object_property(property_name, object_name)
        if not value_str:
            return MathStructure.undefined()

        # Try to parse as a number
        try:
            import re as _re
            # Strip uncertainty notation like "1.3030(30)E22" → "1.3030E22"
            clean = _re.sub(r'\(\d+\)', '', value_str)
            num = Number(float(clean))
            result: MathStructure = MathStructure.from_number(num)
        except (ValueError, ZeroDivisionError, OverflowError):
            return MathStructure.from_symbol(value_str)

        # Attach unit if the object stores a *_unit field for this property
        obj = self.get_object(object_name)
        if obj is not None:
            unit_name = obj.get_property(f"{property_name}_unit")
            if unit_name:
                # Look up the unit through the calculator (if available)
                unit = self._find_unit(unit_name)
                if unit is not None:
                    unit_ms = MathStructure.from_unit(unit)
                    result = MathStructure.multiplication(result, unit_ms)

        return result

    def _find_unit(self, unit_name: str) -> "Unit | None":
        """Find a unit by name, using the calculator's unit registry if available."""
        # Walk up to the calculator via the parent reference if set
        parent = getattr(self, '_calculator', None)
        if parent is not None:
            return parent.get_unit(unit_name)
        return None


class DataPropertyArgument(Argument):
    """Argument that accepts data property names."""

    def __init__(self, dataset: DataSet, name: str = "", does_test: bool = True, does_error: bool = True) -> None:
        super().__init__(name, does_test, does_error)
        self._dataset = dataset

    def data_set(self) -> DataSet:
        return self._dataset

    def set_data_set(self, dataset: DataSet) -> None:
        self._dataset = dataset


class DataObjectArgument(Argument):
    """Argument that accepts data object names."""

    def __init__(self, dataset: DataSet, name: str = "", does_test: bool = True, does_error: bool = True) -> None:
        super().__init__(name, does_test, does_error)
        self._dataset = dataset

    def data_set(self) -> DataSet:
        return self._dataset

    def set_data_set(self, dataset: DataSet) -> None:
        self._dataset = dataset

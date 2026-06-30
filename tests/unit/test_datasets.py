"""Tests for datasets (chemical elements and planets).

Verifies that:
- 118 chemical elements are loaded from elements.json
- 10 planets/solar system bodies are loaded from planets.json
- Properties can be accessed by name
- DataSet objects work as functions
"""

from __future__ import annotations

import pytest

from pyqalculate.calculator import Calculator
from pyqalculate.dataset import DataSet, DataObject, DataProperty


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def calc() -> Calculator:
    """Create a Calculator with all definitions loaded."""
    c = Calculator()
    c.load_definitions()
    c.load_global_definitions()
    # Set as global calculator for expression evaluation
    import pyqalculate.calculator as calc_module
    calc_module._calculator = c
    return c


@pytest.fixture
def elements(calc: Calculator) -> DataSet:
    """Get the elements dataset."""
    ds = calc.get_dataset("elements")
    assert ds is not None, "Elements dataset not found"
    return ds


@pytest.fixture
def planets(calc: Calculator) -> DataSet:
    """Get the planets dataset."""
    ds = calc.get_dataset("planet")
    assert ds is not None, "Planets dataset not found"
    return ds


# ---------------------------------------------------------------------------
# Elements Dataset
# ---------------------------------------------------------------------------


class TestElementsDataset:
    """Test chemical elements dataset."""

    def test_elements_loaded(self, elements: DataSet) -> None:
        """All 118 elements should be loaded."""
        assert elements.count_objects() == 118

    def test_elements_has_properties(self, elements: DataSet) -> None:
        """Elements dataset should have expected properties."""
        assert elements.count_properties() >= 5
        assert elements.get_property_by_name("name") is not None
        assert elements.get_property_by_name("symbol") is not None
        assert elements.get_property_by_name("number") is not None
        assert elements.get_property_by_name("weight") is not None

    def test_hydrogen(self, elements: DataSet) -> None:
        """Hydrogen should be element 1 with symbol H."""
        h = elements.get_object("Hydrogen")
        assert h is not None
        assert h.get_property("symbol") == "H"
        assert h.get_property("number") == "1"

    def test_helium(self, elements: DataSet) -> None:
        """Helium should be element 2 with symbol He."""
        he = elements.get_object("Helium")
        assert he is not None
        assert he.get_property("symbol") == "He"
        assert he.get_property("number") == "2"

    def test_carbon(self, elements: DataSet) -> None:
        """Carbon should be element 6."""
        c = elements.get_object("Carbon")
        assert c is not None
        assert c.get_property("symbol") == "C"
        assert c.get_property("number") == "6"

    def test_gold(self, elements: DataSet) -> None:
        """Gold should be element 79 with symbol Au."""
        au = elements.get_object("Gold")
        assert au is not None
        assert au.get_property("symbol") == "Au"
        assert au.get_property("number") == "79"

    def test_uranium(self, elements: DataSet) -> None:
        """Uranium should be element 92."""
        u = elements.get_object("Uranium")
        assert u is not None
        assert u.get_property("symbol") == "U"
        assert u.get_property("number") == "92"

    def test_oganesson(self, elements: DataSet) -> None:
        """Oganesson should be element 118 (last element)."""
        og = elements.get_object("Oganesson")
        assert og is not None
        assert og.get_property("symbol") == "Og"
        assert og.get_property("number") == "118"

    def test_first_element(self, elements: DataSet) -> None:
        """First element should be Hydrogen."""
        first = elements[0]
        assert first.name == "Hydrogen"

    def test_last_element(self, elements: DataSet) -> None:
        """Last element should be Oganesson."""
        last = elements[-1]
        assert last.name == "Oganesson"

    def test_element_properties_not_empty(self, elements: DataSet) -> None:
        """Most elements should have non-empty weight property."""
        count_with_weight = 0
        for elem in elements:
            weight = elem.get_property("weight")
            if weight:
                count_with_weight += 1
        assert count_with_weight >= 100, f"Only {count_with_weight} elements have weight"

    def test_element_by_index(self, elements: DataSet) -> None:
        """Should be able to access elements by index."""
        for i in range(min(10, len(elements))):
            elem = elements[i]
            assert elem.name
            assert elem.get_property("symbol")

    def test_element_iteration(self, elements: DataSet) -> None:
        """Should be able to iterate over all elements."""
        names = [e.name for e in elements]
        assert len(names) == 118
        assert "Hydrogen" in names
        assert "Oganesson" in names

    def test_element_find_by_number(self, elements: DataSet) -> None:
        """Should be able to find elements by their atomic number."""
        # Find by property
        results = elements.find_objects("number", "26")
        assert len(results) >= 1
        assert results[0].name == "Iron"


# ---------------------------------------------------------------------------
# Planets Dataset
# ---------------------------------------------------------------------------


class TestPlanetsDataset:
    """Test planets dataset."""

    def test_planets_loaded(self, planets: DataSet) -> None:
        """All 11 planets/solar system bodies should be loaded."""
        assert planets.count_objects() == 11

    def test_planets_has_properties(self, planets: DataSet) -> None:
        """Planets dataset should have expected properties."""
        assert planets.count_properties() >= 5
        assert planets.get_property_by_name("name") is not None
        assert planets.get_property_by_name("mass") is not None
        assert planets.get_property_by_name("radius") is not None

    def test_earth(self, planets: DataSet) -> None:
        """Earth should have correct properties."""
        earth = planets.get_object("Earth")
        assert earth is not None
        assert earth.get_property("name") == "Earth"
        mass = earth.get_property("mass")
        assert mass  # Should have mass
        assert "5.97" in mass or "24" in mass  # ~5.97E24 kg

    def test_mars(self, planets: DataSet) -> None:
        """Mars should be in the dataset."""
        mars = planets.get_object("Mars")
        assert mars is not None
        assert mars.get_property("name") == "Mars"

    def test_jupiter(self, planets: DataSet) -> None:
        """Jupiter should have the largest mass."""
        jupiter = planets.get_object("Jupiter")
        assert jupiter is not None
        mass = jupiter.get_property("mass")
        assert mass
        assert "1.898" in mass or "27" in mass  # ~1.898E27 kg

    def test_sun(self, planets: DataSet) -> None:
        """Sun should be in the dataset."""
        sun = planets.get_object("Sun")
        assert sun is not None
        assert sun.get_property("name") == "Sun"

    def test_pluto(self, planets: DataSet) -> None:
        """Pluto should be in the dataset."""
        pluto = planets.get_object("Pluto")
        assert pluto is not None
        assert pluto.get_property("name") == "Pluto"

    def test_all_planets_have_names(self, planets: DataSet) -> None:
        """All planets should have names."""
        for planet in planets:
            assert planet.name, f"Planet at index has no name"
            assert planet.get_property("name"), f"Planet {planet.name} has empty name property"

    def test_planet_iteration(self, planets: DataSet) -> None:
        """Should be able to iterate over all planets."""
        names = [p.name for p in planets]
        assert len(names) == 11
        assert "Earth" in names
        assert "Mars" in names
        assert "Jupiter" in names
        assert "Sun" in names

    def test_planet_find_by_name(self, planets: DataSet) -> None:
        """Should be able to find planets by name."""
        results = planets.find_objects("name", "Earth")
        assert len(results) >= 1
        assert results[0].get_property("mass")

    def test_planet_default_property(self, planets: DataSet) -> None:
        """Default property should be 'name'."""
        assert planets.default_property() == "name"


# ---------------------------------------------------------------------------
# Dataset Integration
# ---------------------------------------------------------------------------


class TestDatasetIntegration:
    """Test dataset integration with calculator."""

    def test_datasets_registered_as_functions(self, calc: Calculator) -> None:
        """Datasets should be registered as functions."""
        assert calc.has_function("elements")
        assert calc.has_function("planet")

    def test_dataset_object_access(self, calc: Calculator) -> None:
        """Should be able to access dataset objects."""
        elements = calc.get_dataset("elements")
        assert elements is not None

        oxygen = elements.get_object("Oxygen")
        assert oxygen is not None
        assert oxygen.get_property("symbol") == "O"

    def test_dataset_property_access(self, calc: Calculator) -> None:
        """Should be able to access specific properties."""
        planets = calc.get_dataset("planet")
        earth = planets.get_object("Earth")
        assert earth is not None

        # Earth's gravity should be approx 9.8 m/s²
        gravity = earth.get_property("gravity")
        assert gravity
        assert "9.8" in gravity

    def test_element_lookup_by_name(self, calc: Calculator) -> None:
        """Should be able to look up elements by name."""
        elements = calc.get_dataset("elements")

        # Test several elements
        test_elements = [
            ("Hydrogen", "H", "1"),
            ("Oxygen", "O", "8"),
            ("Iron", "Fe", "26"),
            ("Silver", "Ag", "47"),
            ("Gold", "Au", "79"),
            ("Uranium", "U", "92"),
        ]

        for name, symbol, number in test_elements:
            elem = elements.get_object(name)
            assert elem is not None, f"Element {name} not found"
            assert elem.get_property("symbol") == symbol, f"{name} symbol mismatch"
            assert elem.get_property("number") == number, f"{name} number mismatch"

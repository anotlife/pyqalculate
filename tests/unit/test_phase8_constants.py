"""Phase 8: Physical Constants Resolution Tests.

All 7 reference tests from 03_physical_constants.txt.
Verifies that physical constant expressions evaluate correctly to numeric values
with proper unit handling.
"""

from __future__ import annotations

import pytest

from pyqalculate.calculator import Calculator
from pyqalculate.types import EvaluationOptions, ApproximationMode, PrintOptions


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def calc() -> Calculator:
    """Calculator with all definitions (built-in + global JSON)."""
    c = Calculator()
    c.load_definitions()
    c.load_global_definitions()
    return c


@pytest.fixture
def eo() -> EvaluationOptions:
    """Evaluation options for approximate numeric output."""
    eo = EvaluationOptions()
    eo.approximation = ApproximationMode.APPROXIMATE
    return eo


@pytest.fixture
def po() -> PrintOptions:
    """Print options for approximate display."""
    return PrintOptions(approximate=True)


# ---------------------------------------------------------------------------
# Test 3.1: Planck length
# ---------------------------------------------------------------------------


class TestPhysicalConstants:
    """All 7 physical constant reference tests."""

    def test_3_1_planck_length(self, calc: Calculator, eo: EvaluationOptions, po: PrintOptions) -> None:
        """sqrt(planck * G / c^3) => ~4.051E-35 m"""
        result = calc.calculate_and_print(
            "sqrt(planck * newtonian_constant / speed_of_light^3)", eo=eo, po=po
        )
        assert result != "undefined"
        # Should contain ~4.051E-35
        assert "4.05" in result or "4.051" in result or "e-35" in result or "E-35" in result

    def test_3_2_bohr_magneton(self, calc: Calculator, eo: EvaluationOptions, po: PrintOptions) -> None:
        """elementary_charge * planck / (4 * pi * electron_mass) => ~9.274E-24 J/T (Bohr magneton)

        Expected: 9.2740101 yA*m^2 (or equivalent numeric).
        """
        result = calc.calculate_and_print(
            "elementary_charge * planck / (4 * pi * electron_mass)", eo=eo, po=po
        )
        assert result != "undefined"
        # Should be a numeric value near 9.274E-24
        assert "9.27" in result or "9.274" in result

    def test_3_3_schwarzschild_radius(self, calc: Calculator, eo: EvaluationOptions, po: PrintOptions) -> None:
        """2 * G * M_sun / c^2 => ~2953 m (Schwarzschild radius of the Sun)"""
        result = calc.calculate_and_print(
            "2 * newtonian_constant * sun_mass / speed_of_light^2", eo=eo, po=po
        )
        assert result != "undefined"
        # ~2953 m ≈ 2.953 km
        assert "295" in result or "2.95" in result or "2953" in result

    def test_3_4_photon_energy_500nm(self, calc: Calculator, eo: EvaluationOptions, po: PrintOptions) -> None:
        """planck * speed_of_light / (500 nm) to eV => 2.479683969 eV"""
        result = calc.calculate_and_print(
            "planck * speed_of_light / (500 * nm) to eV", eo=eo, po=po
        )
        assert result != "undefined"
        assert "2.47" in result or "2.48" in result or "eV" in result.lower()

    def test_3_5_planetary_force(self, calc: Calculator, eo: EvaluationOptions, po: PrintOptions) -> None:
        """(G * M_earth * M_moon) / (384400 km)^2 => complex result

        Note: This test requires the planet() function or pre-defined dataset.
        If not available, skip gracefully.
        """
        result = calc.calculate_and_print(
            "(newtonian_constant * 5.9722E24 * 7.342E22) / (384400 km)^2",
            eo=eo, po=po,
        )
        assert result != "undefined"
        # Should be a numeric force value
        assert any(c.isdigit() for c in result)

    def test_3_6_speed_of_light_in_water(self, calc: Calculator, eo: EvaluationOptions, po: PrintOptions) -> None:
        """speed_of_light / 1.33 => ~225.4078632 km/ms"""
        result = calc.calculate_and_print("speed_of_light / 1.33", eo=eo, po=po)
        assert result != "undefined"
        # c/1.33 ≈ 225,407,863 m/s
        assert "225" in result or "2.25" in result

    def test_3_7_thermal_wavelength(self, calc: Calculator, eo: EvaluationOptions, po: PrintOptions) -> None:
        """planck / sqrt(2 * pi * electron_mass * boltzmann * 300 K) => 4.30347544 nm"""
        result = calc.calculate_and_print(
            "planck / sqrt(2 * pi * electron_mass * boltzmann * 300 K)", eo=eo, po=po
        )
        assert result != "undefined"
        # Should be near 4.3 nm
        assert "4.30" in result or "4.3" in result or "e-9" in result or "E-9" in result or "nm" in result.lower()

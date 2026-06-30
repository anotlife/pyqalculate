"""Tests for GUI application."""
import pytest
import os


def test_import():
    """Test GUI module can be imported."""
    from pyqalculate_gui.app import App
    assert App is not None


def test_calculator_integration():
    """Test calculator works correctly."""
    from pyqalculate.calculator import Calculator
    calc = Calculator()
    calc.load_definitions()
    assert "1" in calc.calculate_and_print("sin(pi/2)")


def test_calculator_unit_conversion():
    """Test unit conversion works."""
    from pyqalculate.calculator import Calculator
    calc = Calculator()
    calc.load_definitions()
    result = calc.calculate_and_print("5 ft to m")
    assert "1.52" in result


def test_calculator_exact_mode():
    """Test exact mode returns symbolic results."""
    from pyqalculate.calculator import Calculator
    from pyqalculate.types import EvaluationOptions, PrintOptions, ApproximationMode
    calc = Calculator()
    calc.load_definitions()

    eo = EvaluationOptions()
    eo.approximation = ApproximationMode.EXACT
    po = PrintOptions()
    po.exact = True

    result = calc.calculate_and_print("sqrt(2)", eo=eo, po=po)
    assert "sqrt" in result or "1.414" in result


def test_calculator_approximate_mode():
    """Test approximate mode returns numeric results."""
    from pyqalculate.calculator import Calculator
    from pyqalculate.types import EvaluationOptions, PrintOptions, ApproximationMode
    calc = Calculator()
    calc.load_definitions()

    eo = EvaluationOptions()
    eo.approximation = ApproximationMode.APPROXIMATE
    po = PrintOptions()
    po.approximate = True

    result = calc.calculate_and_print("sqrt(2)", eo=eo, po=po)
    assert "1.414" in result


@pytest.mark.skipif(
    os.environ.get("DISPLAY") is None and os.name != "nt",
    reason="No display available"
)
def test_gui_creation():
    """Test GUI can be created (requires display)."""
    import tkinter as tk
    from pyqalculate_gui.app import App

    app = App()
    assert app._root is not None
    assert app._root.title() == "PyQalculate"
    app._root.destroy()

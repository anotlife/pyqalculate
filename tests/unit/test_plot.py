"""Tests for the plotting module.

Verifies that:
- Single function plotting works
- Multi-function plotting works
- Data plotting works
- File saving works in display-less mode
- Data generation works
"""

from __future__ import annotations

import os
import tempfile

import pytest

from pyqalculate.calculator import Calculator
from pyqalculate.plot import Plotter, PlotData
from pyqalculate.types import PlotParameters


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
def plotter(calc: Calculator) -> Plotter:
    """Create a Plotter with calculator."""
    return Plotter(calculator=calc)


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as d:
        yield d


# ---------------------------------------------------------------------------
# Matplotlib availability check
# ---------------------------------------------------------------------------


def matplotlib_available() -> bool:
    """Check if matplotlib is available."""
    try:
        import matplotlib
        return True
    except ImportError:
        return False


skip_no_matplotlib = pytest.mark.skipif(
    not matplotlib_available(),
    reason="matplotlib not installed"
)


# ---------------------------------------------------------------------------
# Plot Data Generation
# ---------------------------------------------------------------------------


class TestPlotDataGeneration:
    """Test plot data generation without rendering."""

    def test_generate_data_basic(self, plotter: Plotter) -> None:
        """Should generate x/y data for a simple expression."""
        data = plotter.generate_data("x^2", x_min=-2, x_max=2, num_points=5)
        assert len(data.x_values) == 5
        assert len(data.y_values) == 5
        assert data.title == "x^2"

    def test_generate_data_values(self, plotter: Plotter) -> None:
        """Generated data should have correct values."""
        data = plotter.generate_data("x^2", x_min=-2, x_max=2, num_points=5)
        # x = [-2, -1, 0, 1, 2], y = [4, 1, 0, 1, 4]
        assert data.y_values[0] == pytest.approx(4.0)
        assert data.y_values[1] == pytest.approx(1.0)
        assert data.y_values[2] == pytest.approx(0.0)
        assert data.y_values[3] == pytest.approx(1.0)
        assert data.y_values[4] == pytest.approx(4.0)

    def test_generate_data_linear(self, plotter: Plotter) -> None:
        """Linear function should produce linear data."""
        data = plotter.generate_data("2*x + 1", x_min=0, x_max=4, num_points=5)
        # x = [0, 1, 2, 3, 4], y = [1, 3, 5, 7, 9]
        assert data.y_values[0] == pytest.approx(1.0)
        assert data.y_values[2] == pytest.approx(5.0)
        assert data.y_values[4] == pytest.approx(9.0)

    def test_generate_data_trig(self, plotter: Plotter) -> None:
        """Trigonometric functions should work."""
        import math
        data = plotter.generate_data("sin(x)", x_min=0, x_max=math.pi, num_points=3)
        # x = [0, pi/2, pi], y = [0, 1, 0]
        assert data.y_values[0] == pytest.approx(0.0, abs=1e-10)
        assert data.y_values[1] == pytest.approx(1.0, abs=1e-10)
        assert data.y_values[2] == pytest.approx(0.0, abs=1e-3)

    def test_generate_data_sqrt(self, plotter: Plotter) -> None:
        """sqrt function should work."""
        data = plotter.generate_data("sqrt(x)", x_min=0, x_max=4, num_points=3)
        # linspace(0, 4, 3) = [0, 2, 4], so sqrt values = [0, sqrt(2), 2]
        assert data.y_values[0] == pytest.approx(0.0)
        assert data.y_values[1] == pytest.approx(1.4142135623730951)
        assert data.y_values[2] == pytest.approx(2.0)

    def test_generate_data_exponential(self, plotter: Plotter) -> None:
        """Exponential function should work."""
        data = plotter.generate_data("exp(x)", x_min=0, x_max=1, num_points=3)
        assert data.y_values[0] == pytest.approx(1.0)
        assert data.y_values[2] == pytest.approx(2.71828, rel=1e-3)

    def test_generate_data_invalid_expr(self, plotter: Plotter) -> None:
        """Invalid expressions should produce NaN."""
        data = plotter.generate_data("sqrt(-x^2)", x_min=1, x_max=2, num_points=3)
        import math
        for y in data.y_values:
            assert math.isnan(y)

    def test_generate_data_caret_exponent(self, plotter: Plotter) -> None:
        """Caret ^ should work as exponentiation."""
        data = plotter.generate_data("x^3", x_min=0, x_max=2, num_points=3)
        assert data.y_values[0] == pytest.approx(0.0)
        assert data.y_values[1] == pytest.approx(1.0)
        assert data.y_values[2] == pytest.approx(8.0)


# ---------------------------------------------------------------------------
# PlotData class
# ---------------------------------------------------------------------------


class TestPlotData:
    """Test PlotData class."""

    def test_plot_data_init(self) -> None:
        """PlotData should initialize with empty lists."""
        pd = PlotData()
        assert pd.x_values == []
        assert pd.y_values == []
        assert pd.title == ""

    def test_plot_data_attributes(self) -> None:
        """PlotData attributes should be settable."""
        pd = PlotData()
        pd.x_values = [1.0, 2.0, 3.0]
        pd.y_values = [4.0, 5.0, 6.0]
        pd.title = "test"
        assert len(pd.x_values) == 3
        assert len(pd.y_values) == 3
        assert pd.title == "test"


# ---------------------------------------------------------------------------
# Plotter class
# ---------------------------------------------------------------------------


class TestPlotter:
    """Test Plotter class."""

    def test_plotter_init(self) -> None:
        """Plotter should initialize with or without calculator."""
        p1 = Plotter()
        assert p1._calculator is None

        p2 = Plotter(calculator=Calculator())
        assert p2._calculator is not None

    @skip_no_matplotlib
    def test_plot_save_to_file(self, plotter: Plotter, tmp_dir: str) -> None:
        """Should save plot to file."""
        filepath = os.path.join(tmp_dir, "test_plot.png")
        result = plotter.plot("x^2", x_min=-5, x_max=5, filename=filepath)
        assert result == filepath
        assert os.path.exists(filepath)
        assert os.path.getsize(filepath) > 0

    @skip_no_matplotlib
    def test_plot_multi_save(self, plotter: Plotter, tmp_dir: str) -> None:
        """Should save multi-function plot to file."""
        filepath = os.path.join(tmp_dir, "multi_plot.png")
        result = plotter.plot_multi(
            ["sin(x)", "cos(x)"],
            x_min=0, x_max=6.28,
            filename=filepath,
            title="Trig Functions"
        )
        assert result == filepath
        assert os.path.exists(filepath)

    @skip_no_matplotlib
    def test_plot_data_save(self, plotter: Plotter, tmp_dir: str) -> None:
        """Should save data plot to file."""
        filepath = os.path.join(tmp_dir, "data_plot.png")
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 4.0, 9.0, 16.0, 25.0]
        result = plotter.plot_data(x, y, filename=filepath)
        assert result == filepath
        assert os.path.exists(filepath)

    @skip_no_matplotlib
    def test_plot_with_params(self, plotter: Plotter, tmp_dir: str) -> None:
        """Should respect PlotParameters."""
        filepath = os.path.join(tmp_dir, "params_plot.png")
        params = PlotParameters()
        params.title = "My Plot"
        params.x_label = "Time"
        params.y_label = "Value"
        params.grid = True
        params.filename = filepath

        result = plotter.plot("x^2", params=params, x_min=-3, x_max=3)
        assert result == filepath
        assert os.path.exists(filepath)

    @skip_no_matplotlib
    def test_plot_multiple_expressions(self, plotter: Plotter, tmp_dir: str) -> None:
        """Should plot multiple expressions on same axes."""
        filepath = os.path.join(tmp_dir, "multi_expr.png")
        result = plotter.plot_multi(
            ["x^2", "x^3", "x^4"],
            x_min=-2, x_max=2,
            filename=filepath
        )
        assert result == filepath
        assert os.path.exists(filepath)


# ---------------------------------------------------------------------------
# Expression Evaluation
# ---------------------------------------------------------------------------


class TestExpressionEvaluation:
    """Test the expression evaluation helper."""

    def test_basic_arithmetic(self, plotter: Plotter) -> None:
        """Basic arithmetic should work in expressions."""
        data = plotter.generate_data("x + 1", x_min=0, x_max=2, num_points=3)
        assert data.y_values[0] == pytest.approx(1.0)
        assert data.y_values[1] == pytest.approx(2.0)
        assert data.y_values[2] == pytest.approx(3.0)

    def test_power_operator(self, plotter: Plotter) -> None:
        """^ should work as exponentiation."""
        data = plotter.generate_data("2^x", x_min=0, x_max=3, num_points=4)
        assert data.y_values[0] == pytest.approx(1.0)
        assert data.y_values[1] == pytest.approx(2.0)
        assert data.y_values[2] == pytest.approx(4.0)
        assert data.y_values[3] == pytest.approx(8.0)

    def test_absolute_value(self, plotter: Plotter) -> None:
        """abs() should work."""
        data = plotter.generate_data("abs(x)", x_min=-2, x_max=2, num_points=5)
        assert data.y_values[0] == pytest.approx(2.0)
        assert data.y_values[2] == pytest.approx(0.0)
        assert data.y_values[4] == pytest.approx(2.0)

    def test_logarithm(self, plotter: Plotter) -> None:
        """log() should work."""
        import math
        data = plotter.generate_data("log(x)", x_min=1, x_max=math.e, num_points=3)
        assert data.y_values[0] == pytest.approx(0.0, abs=1e-10)
        assert data.y_values[2] == pytest.approx(1.0, abs=1e-3)

    def test_combined_functions(self, plotter: Plotter) -> None:
        """Multiple functions in one expression should work."""
        data = plotter.generate_data("sin(x) + cos(x)", x_min=0, x_max=1, num_points=3)
        # Just verify it produces valid numbers
        import math
        for y in data.y_values:
            assert not math.isnan(y)
            assert not math.isinf(y)


# ---------------------------------------------------------------------------
# PlotFunction Calculator Integration
# ---------------------------------------------------------------------------


class TestPlotFunctionIntegration:
    """Test PlotFunction integration via Calculator."""

    def test_plot_function_registered(self, calc: Calculator) -> None:
        """PlotFunction should be registered as 'plot' in the calculator."""
        func = calc.get_function("plot")
        assert func is not None
        assert func.name() == "plot"

    def test_plot_function_id(self, calc: Calculator) -> None:
        """PlotFunction should have id FUNCTION_ID_PLOT (2690)."""
        func = calc.get_function("plot")
        assert func is not None
        assert func.id() == 2690

    @skip_no_matplotlib
    def test_plot_from_calculator(self, calc: Calculator, tmp_dir: str) -> None:
        """calc.calculate('plot(x^2, -5, 5, ...)') should produce a file."""
        # Use forward slashes — Windows accepts them and parser doesn't eat them
        filepath = tmp_dir.replace("\\", "/") + "/calc_plot.png"
        result = calc.calculate_and_print(f'plot(x^2, -5, 5, "{filepath}")')
        assert result == filepath
        assert os.path.exists(filepath)
        assert os.path.getsize(filepath) > 0

    @skip_no_matplotlib
    def test_plot_from_calculator_trig(self, calc: Calculator, tmp_dir: str) -> None:
        """plot(sin(x), 0, 6.28, ...) should produce a file."""
        filepath = tmp_dir.replace("\\", "/") + "/trig_plot.png"
        result = calc.calculate_and_print(f'plot(sin(x), 0, 6.28, "{filepath}")')
        assert result == filepath
        assert os.path.exists(filepath)

    @skip_no_matplotlib
    def test_plot_no_filename_displays(self, calc: Calculator) -> None:
        """plot(x^2, -5, 5) without filename returns 'Plot displayed' or file path."""
        # Without a filename, matplotlib either displays interactively or returns empty
        result = calc.calculate_and_print("plot(x^2, -5, 5)")
        # Should return either "Plot displayed" or a file path (auto-generated)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_plot_function_copy(self, calc: Calculator) -> None:
        """PlotFunction.copy() should return an independent copy."""
        func = calc.get_function("plot")
        assert func is not None
        copy = func.copy()
        assert copy is not func
        assert copy.name() == "plot"
        assert copy.id() == 2690

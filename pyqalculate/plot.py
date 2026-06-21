"""Plot module - function plotting for PyQalculate.

Mirrors libqalculate's Calculator::plot() functionality using matplotlib.
Supports single/multiple function plotting, data plotting, and calculator integration.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Sequence

from pyqalculate.types import (
    PlotDataParameters,
    PlotFileType,
    PlotParameters,
    PlotSmoothing,
    PlotStyle,
)

if TYPE_CHECKING:
    from pyqalculate.calculator import Calculator


# Default safe namespace for expression evaluation
_SAFE_MATH_NS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "atan2": math.atan2,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "exp": math.exp, "log": math.log, "ln": math.log, "log2": math.log2, "log10": math.log10,
    "sqrt": math.sqrt, "cbrt": lambda x: math.copysign(abs(x) ** (1/3), x),
    "pi": math.pi, "e": math.e, "tau": math.tau,
    "abs": abs, "sign": lambda x: (x > 0) - (x < 0),
    "floor": math.floor, "ceil": math.ceil,
    "factorial": math.factorial,
    "gamma": math.gamma, "lgamma": math.lgamma,
}


class PlotData:
    """Data for a single plot series."""

    def __init__(self) -> None:
        self.x_values: list[float] = []
        self.y_values: list[float] = []
        self.title: str = ""
        self.style: PlotStyle = PlotStyle.LINES


def _eval_expression(expression: str, x_val: float) -> float:
    """Evaluate a mathematical expression at a given x value.

    Uses a safe namespace with common math functions.

    Args:
        expression: The expression string (e.g., "x^2 + sin(x)").
        x_val: The x value to evaluate at.

    Returns:
        The computed y value, or NaN on error.
    """
    ns = {**_SAFE_MATH_NS, "x": x_val}
    # Convert ^ to ** for Python exponentiation
    expr = expression.replace("^", "**")
    try:
        result = eval(expr, {"__builtins__": {}}, ns)
        return float(result)
    except Exception:
        return float("nan")


class Plotter:
    """Function plotter using matplotlib.

    Provides plotting capabilities for mathematical functions and data,
    equivalent to libqalculate's plot functionality.

    Usage:
        plotter = Plotter(calculator)
        plotter.plot("x^2", x_min=-5, x_max=5, filename="plot.png")
        plotter.plot_multi(["sin(x)", "cos(x)"], x_min=0, x_max=6.28)
    """

    def __init__(self, calculator: Calculator | None = None) -> None:
        self._calculator = calculator

    def plot(
        self,
        expression: str,
        params: PlotParameters | None = None,
        x_min: float = -10.0,
        x_max: float = 10.0,
        num_points: int = 1000,
        filename: str = "",
    ) -> str:
        """Plot a mathematical expression.

        Args:
            expression: The expression to plot (e.g., "sin(x)", "x^2 + 1").
            params: Plot parameters (title, labels, file, etc.).
            x_min: Minimum x value.
            x_max: Maximum x value.
            num_points: Number of points to evaluate.
            filename: If provided, save to this file instead of showing.

        Returns:
            Path to saved file, or empty string if displayed interactively.
        """
        if params is None:
            params = PlotParameters()

        # Allow filename override
        if filename:
            params.filename = filename

        try:
            import matplotlib
            if not params.filename:
                # Use non-interactive backend if no display
                try:
                    import os
                    if os.environ.get("DISPLAY") is None and os.name != "nt":
                        matplotlib.use("Agg")
                except Exception:
                    pass
            else:
                matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            raise ImportError(
                "matplotlib is required for plotting. "
                "Install with: pip install matplotlib"
            )

        x = np.linspace(x_min, x_max, num_points)
        y = np.array([_eval_expression(expression, xi) for xi in x])

        fig, ax = plt.subplots(figsize=(10, 6))
        color = params.color if isinstance(params.color, str) and params.color else "blue"
        ax.plot(x, y, linewidth=1.5, color=color, label=expression)

        self._apply_axes_settings(ax, params, expression)
        ax.legend()

        return self._save_or_show(fig, params.filename)

    def plot_multi(
        self,
        expressions: Sequence[str],
        params: PlotParameters | None = None,
        x_min: float = -10.0,
        x_max: float = 10.0,
        num_points: int = 1000,
        filename: str = "",
        title: str = "",
        colors: Sequence[str] | None = None,
    ) -> str:
        """Plot multiple mathematical expressions on the same axes.

        Args:
            expressions: List of expressions to plot.
            params: Plot parameters.
            x_min: Minimum x value.
            x_max: Maximum x value.
            num_points: Number of points to evaluate.
            filename: If provided, save to this file.
            title: Plot title.
            colors: Optional list of colors for each expression.

        Returns:
            Path to saved file, or empty string if displayed interactively.
        """
        if params is None:
            params = PlotParameters()
        if filename:
            params.filename = filename
        if title:
            params.title = title

        try:
            import matplotlib
            if params.filename:
                matplotlib.use("Agg")
            else:
                try:
                    import os
                    if os.environ.get("DISPLAY") is None and os.name != "nt":
                        matplotlib.use("Agg")
                except Exception:
                    pass
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            raise ImportError("matplotlib is required for plotting.")

        default_colors = ["blue", "red", "green", "orange", "purple",
                          "brown", "pink", "gray", "olive", "cyan"]
        if colors is None:
            colors = default_colors[:len(expressions)]

        x = np.linspace(x_min, x_max, num_points)
        fig, ax = plt.subplots(figsize=(10, 6))

        for i, expr in enumerate(expressions):
            y = np.array([_eval_expression(expr, xi) for xi in x])
            color = colors[i % len(colors)]
            ax.plot(x, y, linewidth=1.5, color=color, label=expr)

        self._apply_axes_settings(ax, params, ", ".join(expressions))
        ax.legend()

        return self._save_or_show(fig, params.filename)

    def plot_data(
        self,
        x_values: list[float],
        y_values: list[float],
        params: PlotParameters | None = None,
        filename: str = "",
    ) -> str:
        """Plot raw x/y data.

        Args:
            x_values: List of x values.
            y_values: List of y values.
            params: Plot parameters.
            filename: If provided, save to this file.

        Returns:
            Path to saved file, or empty string if displayed interactively.
        """
        if params is None:
            params = PlotParameters()
        if filename:
            params.filename = filename

        try:
            import matplotlib
            if params.filename:
                matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib is required for plotting.")

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x_values, y_values, linewidth=1.5)

        self._apply_axes_settings(ax, params, "Data")
        return self._save_or_show(fig, params.filename)

    def generate_data(
        self,
        expression: str,
        x_min: float = -10.0,
        x_max: float = 10.0,
        num_points: int = 1000,
    ) -> PlotData:
        """Generate plot data without rendering.

        Useful for accessing computed data points programmatically.

        Args:
            expression: The expression to evaluate.
            x_min: Minimum x value.
            x_max: Maximum x value.
            num_points: Number of points.

        Returns:
            PlotData with x and y values.
        """
        data = PlotData()
        data.title = expression

        try:
            import numpy as np
            x_arr = np.linspace(x_min, x_max, num_points)
            data.x_values = [float(v) for v in x_arr]
        except ImportError:
            step = (x_max - x_min) / (num_points - 1)
            data.x_values = [x_min + i * step for i in range(num_points)]
        data.y_values = [_eval_expression(expression, xi) for xi in data.x_values]

        return data

    def _apply_axes_settings(
        self,
        ax,
        params: PlotParameters,
        default_ylabel: str,
    ) -> None:
        """Apply common axes settings from PlotParameters."""
        if params.title:
            ax.set_title(params.title)
        ax.set_xlabel(params.x_label or "x")
        ax.set_ylabel(params.y_label or default_ylabel)

        if params.grid:
            ax.grid(True, alpha=0.3)

        if not params.auto_x_min:
            ax.set_xlim(left=params.x_min)
        if not params.auto_x_max:
            ax.set_xlim(right=params.x_max)
        if not params.auto_y_min:
            ax.set_ylim(bottom=params.y_min)
        if not params.auto_y_max:
            ax.set_ylim(top=params.y_max)

    @staticmethod
    def _save_or_show(fig, filename: str) -> str:
        """Save figure to file or show interactively."""
        import matplotlib.pyplot as plt

        if filename:
            try:
                fig.savefig(filename, dpi=150, bbox_inches="tight")
                return filename
            finally:
                plt.close(fig)
        else:
            plt.show()
            plt.close(fig)
            return ""

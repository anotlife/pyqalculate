"""Matplotlib plot widget embedded in tkinter.

Embeds a matplotlib FigureCanvasTkAgg into a tkinter frame for
displaying mathematical function plots inline.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class PlotWidget(ttk.Frame):
    """Embeds a matplotlib figure in a tkinter frame.

    Provides methods to plot expressions, clear, and manage the figure.
    """

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self._canvas = None
        self._figure = None
        self._ax = None
        self._has_plot = False
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the plot area UI."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Placeholder label
        self._placeholder = ttk.Label(
            self, text="Plot area - enter plot(...) to display",
            anchor=tk.CENTER, foreground="#999999"
        )
        self._placeholder.grid(row=0, column=0, sticky="nsew")

        # Clear button (hidden until plot is shown)
        self._btn_frame = ttk.Frame(self)
        self._btn_frame.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        self._clear_btn = ttk.Button(
            self._btn_frame, text="Clear Plot", command=self.clear_plot
        )
        # Don't pack initially - shown when plot exists

    def plot_expression(
        self,
        expression: str,
        x_min: float = -10.0,
        x_max: float = 10.0,
        num_points: int = 1000,
    ) -> bool:
        """Plot a mathematical expression.

        Args:
            expression: The expression to plot (e.g., "sin(x)", "x^2").
            x_min: Minimum x value.
            x_max: Maximum x value.
            num_points: Number of points to evaluate.

        Returns:
            True if plotting succeeded, False otherwise.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import numpy as np
        except ImportError:
            return False

        from pyqalculate.plot import _eval_expression

        # Generate data
        x = np.linspace(x_min, x_max, num_points)
        y = np.array([_eval_expression(expression, xi) for xi in x])

        # Clear previous plot
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()

        # Create figure
        self._figure, self._ax = plt.subplots(figsize=(6, 3), dpi=100)
        self._ax.plot(x, y, linewidth=1.5, color="blue", label=expression)
        self._ax.set_xlabel("x")
        self._ax.set_ylabel(expression)
        self._ax.grid(True, alpha=0.3)
        self._ax.legend()

        # Embed in tkinter
        self._canvas = FigureCanvasTkAgg(self._figure, master=self)
        self._canvas.draw()
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Hide placeholder, show clear button
        self._placeholder.grid_forget()
        self._clear_btn.pack(side=tk.RIGHT)
        self._has_plot = True

        return True

    def plot_multi(
        self,
        expressions: list[str],
        x_min: float = -10.0,
        x_max: float = 10.0,
        num_points: int = 1000,
        title: str = "",
    ) -> bool:
        """Plot multiple expressions on the same axes.

        Args:
            expressions: List of expression strings.
            x_min: Minimum x value.
            x_max: Maximum x value.
            num_points: Number of points per expression.
            title: Plot title.

        Returns:
            True if plotting succeeded, False otherwise.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import numpy as np
        except ImportError:
            return False

        from pyqalculate.plot import _eval_expression

        colors = ["blue", "red", "green", "orange", "purple",
                  "brown", "pink", "gray", "olive", "cyan"]

        x = np.linspace(x_min, x_max, num_points)

        # Clear previous plot
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()

        # Create figure
        self._figure, self._ax = plt.subplots(figsize=(6, 3), dpi=100)

        for i, expr in enumerate(expressions):
            y = np.array([_eval_expression(expr, xi) for xi in x])
            color = colors[i % len(colors)]
            self._ax.plot(x, y, linewidth=1.5, color=color, label=expr)

        if title:
            self._ax.set_title(title)
        self._ax.set_xlabel("x")
        self._ax.grid(True, alpha=0.3)
        self._ax.legend()

        # Embed in tkinter
        self._canvas = FigureCanvasTkAgg(self._figure, master=self)
        self._canvas.draw()
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Hide placeholder, show clear button
        self._placeholder.grid_forget()
        self._clear_btn.pack(side=tk.RIGHT)
        self._has_plot = True

        return True

    def clear_plot(self) -> None:
        """Clear the current plot and show placeholder."""
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None
            self._figure = None
            self._ax = None

        # Show placeholder
        self._placeholder.grid(row=0, column=0, sticky="nsew")
        self._clear_btn.pack_forget()
        self._has_plot = False

    def has_plot(self) -> bool:
        """Return True if a plot is currently displayed."""
        return self._has_plot

    def save_plot(self, filename: str) -> bool:
        """Save the current plot to a file.

        Args:
            filename: Path to save the figure.

        Returns:
            True if save succeeded, False otherwise.
        """
        if self._figure is None:
            return False
        try:
            self._figure.savefig(filename, dpi=150, bbox_inches="tight")
            return True
        except Exception:
            return False

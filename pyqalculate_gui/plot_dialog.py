"""Plot dialog for PyQalculate GUI.

Provides a tkinter dialog for plotting mathematical expressions using
matplotlib. Supports multiple expressions, x-range configuration, plot
style options, zoom/pan via NavigationToolbar, grid toggle, and saving
to PNG or SVG.

Uses the existing Plotter class from pyqalculate.plot for expression
evaluation and data generation.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyqalculate.calculator import Calculator


# ---------------------------------------------------------------------------
# Color palette for multi-expression plots
# ---------------------------------------------------------------------------
_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]


class PlotDialog:
    """Modal plot dialog for PyQalculate.

    Opens a top-level window with:
    - Expression list (add / remove multiple expressions)
    - X range controls (min / max / step count)
    - Plot style combo (lines, points, points+lines, dots, steps)
    - Grid toggle checkbox
    - Embedded matplotlib canvas with NavigationToolbar (zoom, pan, save)
    - Save-as button (PNG / SVG)
    """

    def __init__(self, parent: tk.Tk | tk.Toplevel, calculator: Calculator | None = None) -> None:
        self._parent = parent
        self._calculator = calculator
        self._dialog: tk.Toplevel | None = None
        self._canvas = None
        self._toolbar = None
        self._fig = None
        self._ax = None

        # Expression list model
        self._expressions: list[str] = []

        # Keep references for matplotlib imports (lazy)
        self._FigureCanvasTkAgg = None
        self._NavigationToolbar2Tk = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self, expression: str = "") -> None:
        """Open (or raise) the plot dialog.

        Args:
            expression: Optional expression to pre-fill.
        """
        if self._dialog is not None and self._dialog.winfo_exists():
            self._dialog.lift()
            if expression:
                self._add_expression(expression)
            return

        self._create_dialog()
        if expression:
            self._add_expression(expression)
        else:
            # Start with one empty entry
            self._add_expression("")

    # ------------------------------------------------------------------
    # Dialog construction
    # ------------------------------------------------------------------

    def _create_dialog(self) -> None:
        """Build the full dialog UI."""
        dlg = tk.Toplevel(self._parent)
        dlg.title("Plot")
        dlg.geometry("900x680")
        dlg.minsize(700, 500)
        dlg.transient(self._parent)
        dlg.grab_set()
        self._dialog = dlg

        dlg.protocol("WM_DELETE_WINDOW", self._on_close)

        # ---- Layout: left panel (controls) + right panel (canvas) ----
        dlg.columnconfigure(1, weight=1)
        dlg.rowconfigure(0, weight=1)

        # Left panel -- controls
        ctrl = ttk.Frame(dlg, padding=8)
        ctrl.grid(row=0, column=0, sticky="nsew")

        # Right panel -- plot canvas + toolbar
        plot_frame = ttk.Frame(dlg)
        plot_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(1, weight=1)

        self._build_controls(ctrl)
        self._build_canvas_area(plot_frame)
        self._build_buttons(dlg)

        # Import matplotlib classes lazily
        self._init_matplotlib(plot_frame)

    # ---- Controls (left panel) ----

    def _build_controls(self, parent: ttk.Frame) -> None:
        """Build the left-side control panel."""
        row = 0

        # -- Expression list --
        ttk.Label(parent, text="Expressions", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        row += 1

        list_frame = ttk.Frame(parent)
        list_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        list_frame.columnconfigure(0, weight=1)

        self._expr_listbox = tk.Listbox(list_frame, height=5, width=30)
        self._expr_listbox.grid(row=0, column=0, sticky="ew")
        sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._expr_listbox.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._expr_listbox.config(yscrollcommand=sb.set)
        row += 1

        # Add/Remove buttons
        btn_row = ttk.Frame(parent)
        btn_row.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ttk.Button(btn_row, text="Add", width=6, command=self._on_add).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_row, text="Remove", width=6, command=self._on_remove).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_row, text="Edit", width=6, command=self._on_edit).pack(side=tk.LEFT)
        row += 1

        # Separator
        ttk.Separator(parent, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # -- X Range --
        ttk.Label(parent, text="X Range", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        row += 1

        ttk.Label(parent, text="Min:").grid(row=row, column=0, sticky="w")
        self._x_min_var = tk.StringVar(value="-10")
        ttk.Entry(parent, textvariable=self._x_min_var, width=12).grid(
            row=row, column=1, sticky="ew", padx=(4, 0)
        )
        row += 1

        ttk.Label(parent, text="Max:").grid(row=row, column=0, sticky="w")
        self._x_max_var = tk.StringVar(value="10")
        ttk.Entry(parent, textvariable=self._x_max_var, width=12).grid(
            row=row, column=1, sticky="ew", padx=(4, 0)
        )
        row += 1

        ttk.Label(parent, text="Points:").grid(row=row, column=0, sticky="w")
        self._points_var = tk.StringVar(value="1000")
        ttk.Entry(parent, textvariable=self._points_var, width=12).grid(
            row=row, column=1, sticky="ew", padx=(4, 0)
        )
        row += 1

        # Separator
        ttk.Separator(parent, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # -- Style --
        ttk.Label(parent, text="Style", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        row += 1

        ttk.Label(parent, text="Line style:").grid(row=row, column=0, sticky="w")
        self._style_var = tk.StringVar(value="lines")
        style_combo = ttk.Combobox(
            parent,
            textvariable=self._style_var,
            values=["lines", "points", "points+lines", "dots", "steps"],
            state="readonly",
            width=14,
        )
        style_combo.grid(row=row, column=1, sticky="ew", padx=(4, 0))
        row += 1

        ttk.Label(parent, text="Line width:").grid(row=row, column=0, sticky="w")
        self._linewidth_var = tk.StringVar(value="1.5")
        ttk.Entry(parent, textvariable=self._linewidth_var, width=12).grid(
            row=row, column=1, sticky="ew", padx=(4, 0)
        )
        row += 1

        # Grid toggle
        self._grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Show grid", variable=self._grid_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        row += 1

        # Legend toggle
        self._legend_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Show legend", variable=self._legend_var).grid(
            row=row, column=0, columnspan=2, sticky="w"
        )
        row += 1

        # Plot title
        ttk.Label(parent, text="Title:").grid(row=row, column=0, sticky="w", pady=(4, 0))
        self._title_var = tk.StringVar(value="")
        ttk.Entry(parent, textvariable=self._title_var, width=16).grid(
            row=row, column=1, sticky="ew", padx=(4, 0), pady=(4, 0)
        )
        row += 1

        # ---- Plot button (primary action) ----
        ttk.Button(parent, text="Plot", command=self._on_plot).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(12, 0)
        )

    # ---- Canvas area (right panel) ----

    def _build_canvas_area(self, parent: ttk.Frame) -> None:
        """Reserve frames for the matplotlib canvas and toolbar."""
        self._toolbar_frame = ttk.Frame(parent)
        self._toolbar_frame.grid(row=0, column=0, sticky="ew")

        self._canvas_frame = ttk.Frame(parent)
        self._canvas_frame.grid(row=1, column=0, sticky="nsew")

        # Placeholder
        self._placeholder = ttk.Label(
            self._canvas_frame,
            text="Click Plot to draw",
            anchor=tk.CENTER,
            foreground="#999999",
        )
        self._placeholder.pack(expand=True)

    # ---- Bottom buttons ----

    def _build_buttons(self, parent: tk.Toplevel) -> None:
        """Build the bottom button row."""
        btn_frame = ttk.Frame(parent, padding=8)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        ttk.Button(btn_frame, text="Save as PNG", command=self._on_save_png).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(btn_frame, text="Save as SVG", command=self._on_save_svg).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(btn_frame, text="Close", command=self._on_close).pack(
            side=tk.RIGHT
        )

    # ------------------------------------------------------------------
    # Matplotlib integration
    # ------------------------------------------------------------------

    def _init_matplotlib(self, plot_frame: ttk.Frame) -> None:
        """Import and store matplotlib tkinter classes."""
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.backends._backend_tk import NavigationToolbar2Tk
            self._FigureCanvasTkAgg = FigureCanvasTkAgg
            self._NavigationToolbar2Tk = NavigationToolbar2Tk
        except ImportError:
            if self._dialog is not None:
                messagebox.showerror(
                    "Missing Dependency",
                    "matplotlib is required for plotting.\n"
                    "Install with:  pip install matplotlib",
                    parent=self._dialog,
                )

    def _render_plot(self) -> None:
        """Evaluate all expressions and render the matplotlib figure."""
        if self._FigureCanvasTkAgg is None or self._NavigationToolbar2Tk is None:
            return

        # Parse range
        try:
            x_min = float(self._x_min_var.get())
            x_max = float(self._x_max_var.get())
            num_points = max(100, int(self._points_var.get()))
        except ValueError:
            if self._dialog is not None:
                messagebox.showerror(
                    "Invalid Range",
                    "X min, max, and points must be valid numbers.",
                    parent=self._dialog,
                )
            return

        if x_min >= x_max:
            if self._dialog is not None:
                messagebox.showerror(
                    "Invalid Range",
                    "X min must be less than X max.",
                    parent=self._dialog,
                )
            return

        # Collect non-empty expressions
        exprs = [e for e in self._expressions if e.strip()]
        if not exprs:
            if self._dialog is not None:
                messagebox.showwarning(
                    "No Expressions",
                    "Add at least one expression to plot.",
                    parent=self._dialog,
                )
            return

        # Build plot style map
        style_map = {
            "lines": "-",
            "points": "o",
            "points+lines": "o-",
            "dots": ".",
            "steps": "steps-post",
        }
        draw_style = style_map.get(self._style_var.get(), "-")
        try:
            lw = float(self._linewidth_var.get())
        except ValueError:
            lw = 1.5

        # Evaluate expressions
        from pyqalculate.plot import _eval_expression
        import numpy as np

        x_arr = np.linspace(x_min, x_max, num_points)

        # Destroy old canvas / toolbar
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None
        if self._toolbar is not None:
            self._toolbar.destroy()
            self._toolbar = None
        self._placeholder.pack_forget()

        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor("#fafafa")

        for i, expr in enumerate(exprs):
            y = np.array([_eval_expression(expr, xi) for xi in x_arr])
            color = _COLORS[i % len(_COLORS)]
            if draw_style == "steps-post":
                ax.step(x_arr, y, where="post", linewidth=lw, color=color, label=expr)
            else:
                ax.plot(x_arr, y, draw_style, linewidth=lw, color=color, label=expr)

        title = self._title_var.get().strip()
        if title:
            ax.set_title(title, fontsize=11)
        ax.set_xlabel("x")
        ax.set_ylabel(", ".join(exprs) if len(exprs) == 1 else "y")

        if self._grid_var.get():
            ax.grid(True, alpha=0.3, linestyle="--")

        if self._legend_var.get():
            ax.legend(fontsize=9, loc="best")

        fig.tight_layout()

        # Embed in tkinter
        canvas = self._FigureCanvasTkAgg(fig, master=self._canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = self._NavigationToolbar2Tk(canvas, self._toolbar_frame)
        toolbar.update()

        self._fig = fig
        self._ax = ax
        self._canvas = canvas
        self._toolbar = toolbar

    # ------------------------------------------------------------------
    # Expression list management
    # ------------------------------------------------------------------

    def _add_expression(self, expr: str) -> None:
        """Add an expression to the list."""
        self._expressions.append(expr)
        self._expr_listbox.insert(tk.END, expr if expr else "(empty)")

    def _sync_listbox(self) -> None:
        """Rebuild the listbox from the internal expression list."""
        self._expr_listbox.delete(0, tk.END)
        for e in self._expressions:
            self._expr_listbox.insert(tk.END, e if e else "(empty)")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_plot(self) -> None:
        """Handle Plot button click."""
        self._sync_expressions_from_listbox()
        self._render_plot()

    def _on_add(self) -> None:
        """Open a simple entry popup to add an expression."""
        self._prompt_expression("Add Expression")

    def _on_remove(self) -> None:
        """Remove the selected expression."""
        sel = self._expr_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if 0 <= idx < len(self._expressions):
            del self._expressions[idx]
            self._sync_listbox()

    def _on_edit(self) -> None:
        """Edit the selected expression."""
        sel = self._expr_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if 0 <= idx < len(self._expressions):
            self._prompt_expression("Edit Expression", idx=idx)

    def _prompt_expression(self, title: str, idx: int | None = None) -> None:
        """Show a simple dialog to enter/edit an expression.

        Args:
            title: Dialog window title.
            idx: If provided, edit this index; otherwise add new.
        """
        if self._dialog is None:
            return

        popup = tk.Toplevel(self._dialog)
        popup.title(title)
        popup.geometry("360x100")
        popup.transient(self._dialog)
        popup.grab_set()
        popup.resizable(False, False)

        ttk.Label(popup, text="Expression:").grid(
            row=0, column=0, padx=8, pady=(12, 4), sticky="w"
        )
        init_val = self._expressions[idx] if idx is not None and 0 <= idx < len(self._expressions) else ""
        var = tk.StringVar(value=init_val)
        entry = ttk.Entry(popup, textvariable=var, width=30)
        entry.grid(row=0, column=1, padx=(0, 8), pady=(12, 4), sticky="ew")
        entry.select_range(0, tk.END)
        entry.focus_set()
        popup.columnconfigure(1, weight=1)

        def _confirm() -> None:
            val = var.get().strip()
            if idx is not None:
                self._expressions[idx] = val
            else:
                self._expressions.append(val)
            self._sync_listbox()
            popup.destroy()

        popup.bind("<Return>", lambda e: _confirm())

        ttk.Button(popup, text="OK", command=_confirm, width=8).grid(
            row=1, column=0, columnspan=2, pady=8
        )

    def _sync_expressions_from_listbox(self) -> None:
        """Update internal list from listbox (in case of inline editing)."""
        # We rely on explicit add/edit, but clear empties
        self._expressions = [e for e in self._expressions]

    # ---- Save ----

    def _on_save_png(self) -> None:
        """Save the current figure as PNG."""
        self._save_figure("png")

    def _on_save_svg(self) -> None:
        """Save the current figure as SVG."""
        self._save_figure("svg")

    def _save_figure(self, fmt: str) -> None:
        """Save figure to file via file dialog."""
        if self._fig is None:
            if self._dialog is not None:
                messagebox.showinfo(
                    "No Plot",
                    "Nothing to save. Click Plot first.",
                    parent=self._dialog,
                )
            return

        ftypes = {
            "png": [("PNG Image", "*.png"), ("All Files", "*.*")],
            "svg": [("SVG Vector", "*.svg"), ("All Files", "*.*")],
        }
        path = filedialog.asksaveasfilename(
            parent=self._dialog,
            title=f"Save Plot as {fmt.upper()}",
            defaultextension=f".{fmt}",
            filetypes=ftypes.get(fmt, [("All Files", "*.*")]),
        )
        if not path:
            return

        try:
            self._fig.savefig(path, dpi=150, bbox_inches="tight", format=fmt)
            if self._dialog is not None:
                messagebox.showinfo(
                    "Saved",
                    f"Plot saved to:\n{path}",
                    parent=self._dialog,
                )
        except Exception as exc:
            if self._dialog is not None:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save:\n{exc}",
                    parent=self._dialog,
                )

    # ---- Close ----

    def _on_close(self) -> None:
        """Clean up and close the dialog."""
        import matplotlib.pyplot as plt

        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
            self._ax = None
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None
        if self._toolbar is not None:
            self._toolbar.destroy()
            self._toolbar = None
        if self._dialog is not None:
            self._dialog.destroy()
            self._dialog = None

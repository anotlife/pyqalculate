"""Main window for PyQalculate GUI.

Provides a simple tkinter-based calculator interface with expression input,
result display, exact/approximate mode toggle, and a status bar.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import traceback

from pyqalculate.calculator import Calculator
from pyqalculate.types import ApproximationMode, EvaluationOptions, PrintOptions


class CalculatorApp:
    """Main calculator application window.

    Features:
        - Expression input with Enter key submission
        - Result area with auto-scroll
        - Exact/Approximate mode toggle
        - Copy result on double-click
        - Clear button to reset
        - Status bar with calculator info
    """

    def __init__(self) -> None:
        self._calc = Calculator()
        self._calc.load_definitions()
        self._exact_mode = True

        self._root = tk.Tk()
        self._root.title("PyQalculate")
        self._root.geometry("600x450")
        self._root.minsize(400, 300)

        self._build_ui()
        self._update_status()

    def _build_ui(self) -> None:
        """Build the main window UI."""
        main_frame = ttk.Frame(self._root, padding=8)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Input row: [Entry] [Calculate] ---
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 4))
        input_frame.columnconfigure(0, weight=1)

        self._entry = ttk.Entry(input_frame, font=("Consolas", 12))
        self._entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._entry.bind("<Return>", self._on_enter)
        self._entry.focus_set()

        self._calc_btn = ttk.Button(
            input_frame, text="Calculate", width=10, command=self._calculate
        )
        self._calc_btn.grid(row=0, column=1)

        # --- Mode row: [x] Exact mode  |  [Clear] ---
        mode_frame = ttk.Frame(main_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 4))

        self._exact_var = tk.BooleanVar(value=True)
        self._exact_cb = ttk.Checkbutton(
            mode_frame,
            text="Exact mode",
            variable=self._exact_var,
            command=self._on_mode_toggle,
        )
        self._exact_cb.pack(side=tk.LEFT)

        self._clear_btn = ttk.Button(
            mode_frame, text="Clear", command=self._clear
        )
        self._clear_btn.pack(side=tk.RIGHT)

        # --- Results area ---
        result_frame = ttk.LabelFrame(main_frame, text="Results", padding=4)
        result_frame.pack(fill=tk.BOTH, expand=True)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self._result_text = tk.Text(
            result_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            state=tk.DISABLED,
            bg="#f8f8f8",
            relief=tk.FLAT,
            padx=8,
            pady=4,
        )
        self._result_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            result_frame, orient=tk.VERTICAL, command=self._result_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._result_text.config(yscrollcommand=scrollbar.set)

        # Configure text tags
        self._result_text.tag_configure(
            "expression", foreground="#2060a0", font=("Consolas", 11, "bold")
        )
        self._result_text.tag_configure(
            "result", foreground="#006600", font=("Consolas", 12)
        )
        self._result_text.tag_configure(
            "error", foreground="#cc0000", font=("Consolas", 11)
        )

        # Double-click to copy last result
        self._result_text.bind("<Double-Button-1>", self._on_double_click)
        self._last_result: str = ""

        # --- Status bar ---
        self._status_var = tk.StringVar(value="")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self._status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            foreground="#555555",
        )
        status_bar.pack(fill=tk.X, pady=(4, 0))

    def _on_enter(self, event: tk.Event) -> None:
        """Handle Enter key press."""
        self._calculate()

    def _on_mode_toggle(self) -> None:
        """Handle exact/approximate mode toggle."""
        self._exact_mode = self._exact_var.get()

    def _calculate(self) -> None:
        """Calculate the expression in the input field."""
        expr = self._entry.get().strip()
        if not expr:
            return

        self._entry.delete(0, tk.END)

        try:
            eo = EvaluationOptions()
            po = PrintOptions()

            if self._exact_mode:
                eo.approximation = ApproximationMode.EXACT
                po.exact = True
            else:
                eo.approximation = ApproximationMode.APPROXIMATE
                po.approximate = True

            result = self._calc.calculate_and_print(expr, eo=eo, po=po)
            self._show_result(expr, result)
        except Exception:
            error_msg = traceback.format_exc()
            self._show_error(expr, error_msg)

    def _show_result(self, expression: str, result: str) -> None:
        """Display an expression and its result."""
        self._result_text.config(state=tk.NORMAL)

        # Add newline if there's existing content
        content = self._result_text.get("1.0", tk.END).strip()
        if content:
            self._result_text.insert(tk.END, "\n")

        self._result_text.insert(tk.END, f"> {expression}\n", "expression")
        self._result_text.insert(tk.END, f"= {result}\n", "result")

        self._result_text.config(state=tk.DISABLED)
        self._result_text.see(tk.END)

        self._last_result = result

    def _show_error(self, expression: str, error: str) -> None:
        """Display an expression and its error."""
        self._result_text.config(state=tk.NORMAL)

        content = self._result_text.get("1.0", tk.END).strip()
        if content:
            self._result_text.insert(tk.END, "\n")

        self._result_text.insert(tk.END, f"> {expression}\n", "expression")
        self._result_text.insert(tk.END, f"Error: {error}\n", "error")

        self._result_text.config(state=tk.DISABLED)
        self._result_text.see(tk.END)

        self._last_result = ""

    def _on_double_click(self, event: tk.Event) -> None:
        """Copy last result to clipboard on double-click."""
        if self._last_result:
            self._root.clipboard_clear()
            self._root.clipboard_append(self._last_result)

    def _clear(self) -> None:
        """Clear the results area."""
        self._result_text.config(state=tk.NORMAL)
        self._result_text.delete("1.0", tk.END)
        self._result_text.config(state=tk.DISABLED)
        self._last_result = ""

    def _update_status(self) -> None:
        """Update the status bar with calculator info."""
        n_funcs = self._calc.count_functions()
        n_units = self._calc.count_units()
        n_vars = self._calc.count_variables()
        self._status_var.set(
            f"Functions: {n_funcs} | Units: {n_units} | Vars: {n_vars}"
        )

    def run(self) -> None:
        """Start the main event loop."""
        self._root.mainloop()

    @property
    def root(self) -> tk.Tk:
        """Return the root Tk window."""
        return self._root


def main() -> None:
    """Launch the PyQalculate GUI."""
    app = CalculatorApp()
    app.run()


if __name__ == "__main__":
    main()

"""Main window for PyQalculate v2.2 GUI.

Modern tkinter-based calculator interface with:
- Menu bar (File, Edit, View, Help)
- Expression input with history, undo/redo
- Result display with copy support
- History view with answer(N) recall
- Status bar with calculator info
"""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
from typing import TYPE_CHECKING

from pyqalculate.calculator import Calculator
from pyqalculate.types import ApproximationMode, EvaluationOptions, PrintOptions

if TYPE_CHECKING:
    from pyqalculate.math_structure import MathStructure

from pyqalculate_gui.expression_edit import ExpressionEdit
from pyqalculate_gui.keypad import KeypadWidget
from pyqalculate_gui.result_view import ResultView
from pyqalculate_gui.history_view import HistoryView
from pyqalculate_gui.conversion_view import ConversionView
from pyqalculate_gui.plot_dialog import PlotDialog
from pyqalculate_gui.preferences_dialog import PreferencesDialog
from pyqalculate_gui.import_csv_dialog import ImportCsvDialog
from pyqalculate_gui.export_csv_dialog import ExportCsvDialog


class MainWindow:
    """Main calculator application window.

    Orchestrates the expression input, result display, history view,
    menu bar, and status bar into a cohesive calculator UI.
    """

    _ANSWER_RE = re.compile(r"answer\(\s*(-?\d+)\s*\)")

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("PyQalculate")
        self._root.geometry("860x820")
        self._root.minsize(600, 550)

        # Calculator engine
        self._calc = Calculator()
        self._calc.load_definitions()

        # Mode state
        self._exact_mode = True

        # Plot dialog (lazy -- created once, reused)
        self._plot_dialog = PlotDialog(self._root)

        # Preferences dialog (lazy -- created once, reused)
        self._prefs_dialog = PreferencesDialog(
            self._root, calculator=self._calc, on_apply=self._on_preferences_apply,
        )

        # CSV import/export dialogs (lazy -- created once, reused)
        self._import_csv_dialog = ImportCsvDialog(self._root, calculator=self._calc)
        self._export_csv_dialog = ExportCsvDialog(
            self._root, calculator=self._calc, get_last_result=self._get_last_result_for_export,
        )

        # Build UI
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()
        self._update_status()

        # Focus expression input on startup
        self._root.after(100, self._expr_edit.focus_input)

    # ==================================================================
    # Menu bar
    # ==================================================================

    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = tk.Menu(self._root)
        self._root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Clear All", command=self._clear_all)
        file_menu.add_separator()
        file_menu.add_command(label="Import CSV...", command=self._open_import_csv)
        file_menu.add_command(label="Export CSV...", command=self._open_export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(
            label="Copy Result", command=self._copy_result, accelerator="Ctrl+C"
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Clear Expression",
            command=lambda: self._expr_edit.clear(),
            accelerator="Escape",
        )
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # Mode menu
        mode_menu = tk.Menu(menubar, tearoff=0)
        self._exact_mode_var = tk.BooleanVar(value=True)
        mode_menu.add_checkbutton(
            label="Exact Mode",
            variable=self._exact_mode_var,
            command=self._on_mode_toggle,
        )
        mode_menu.add_separator()
        mode_menu.add_command(
            label="Preferences...",
            command=self._open_preferences,
            accelerator="Ctrl+Shift+P",
        )
        menubar.add_cascade(label="Mode", menu=mode_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        self._show_history_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(
            label="Show History",
            variable=self._show_history_var,
            command=self._toggle_history,
        )
        self._show_keypad_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(
            label="Show Keypad",
            variable=self._show_keypad_var,
            command=self._toggle_keypad,
        )
        self._show_conversion_var = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(
            label="Unit Conversion",
            variable=self._show_conversion_var,
            command=self._toggle_conversion,
        )
        view_menu.add_separator()
        view_menu.add_command(
            label="Plot...",
            command=self._open_plot_dialog,
            accelerator="Ctrl+P",
        )
        menubar.add_cascade(label="View", menu=view_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        # Global keyboard shortcuts
        self._root.bind("<Control-c>", lambda e: self._copy_result())
        self._root.bind("<Control-p>", lambda e: self._open_plot_dialog())
        self._root.bind("<Control-Shift-P>", lambda e: self._open_preferences())

    # ==================================================================
    # Main layout
    # ==================================================================

    def _create_main_layout(self) -> None:
        """Create the main window layout with panels."""
        main_frame = ttk.Frame(self._root, padding=8)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # result area expands

        # --- Expression input ---
        self._expr_edit = ExpressionEdit(main_frame, on_submit=self._on_submit)
        self._expr_edit.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        # --- Virtual keypad (togglable) ---
        self._keypad_frame = ttk.Frame(main_frame)
        self._keypad_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        self._keypad = KeypadWidget(
            self._keypad_frame,
            on_insert=self._on_keypad_insert,
            on_clear=self._on_keypad_clear,
            on_backspace=self._on_keypad_backspace,
            on_submit=self._on_keypad_submit,
        )
        self._keypad.pack(fill=tk.X, expand=False)
        self._keypad_visible = True

        # --- Paned window: result + history ---
        self._paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self._paned.grid(row=2, column=0, sticky="nsew")

        # Result view (left)
        self._result_view = ResultView(self._paned)
        self._paned.add(self._result_view, weight=3)

        # History view (right)
        self._history_frame = ttk.Frame(self._paned)
        self._history_view = HistoryView(
            self._history_frame, on_recall=self._on_history_recall
        )
        self._history_view.pack(fill=tk.BOTH, expand=True)
        self._paned.add(self._history_frame, weight=1)

        # Conversion panel (togglable, initially hidden)
        self._conversion_frame = ttk.Frame(self._paned)
        self._conversion_view = ConversionView(
            self._conversion_frame,
            calculator=self._calc,
            on_convert=self._on_conversion_result,
        )
        self._conversion_view.pack(fill=tk.BOTH, expand=True)
        self._conversion_visible = False

    # ==================================================================
    # Status bar
    # ==================================================================

    def _create_status_bar(self) -> None:
        """Create the bottom status bar."""
        self._status_var = tk.StringVar(value="")
        self._status_bar = ttk.Label(
            self._root,
            textvariable=self._status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(6, 2),
        )
        self._status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self._mode_var = tk.StringVar(value="Exact")
        self._mode_label = ttk.Label(
            self._root,
            textvariable=self._mode_var,
            relief=tk.SUNKEN,
            anchor=tk.E,
            padding=(6, 2),
            foreground="#1a5276",
            font=("TkDefaultFont", 9, "bold"),
        )
        self._mode_label.pack(fill=tk.X, side=tk.BOTTOM)

    def _update_status(self) -> None:
        """Update status bar with calculator statistics."""
        n_funcs = self._calc.count_functions()
        n_units = self._calc.count_units()
        n_vars = self._calc.count_variables()
        self._status_var.set(
            f"Functions: {n_funcs}  |  Units: {n_units}  |  Variables: {n_vars}"
        )

    # ==================================================================
    # Calculation flow
    # ==================================================================

    def _on_submit(self, expression: str) -> None:
        """Handle expression submission from the input widget."""
        # Resolve answer(N) references
        resolved = self._resolve_answer_refs(expression)

        # Record expression in history
        self._history_view.add_expression(expression)

        # Calculate using preferences dialog settings when available
        try:
            prefs = self._prefs_dialog
            if hasattr(prefs, "_current_eo") and prefs._current_eo is not None:
                eo = prefs._current_eo
            else:
                eo = EvaluationOptions()
            if hasattr(prefs, "_current_po") and prefs._current_po is not None:
                po = prefs._current_po
            else:
                po = PrintOptions()

            # Exact/approximate mode toggle (from mode menu or preferences)
            if self._exact_mode:
                eo.approximation = ApproximationMode.EXACT
                po.exact = True
                po.approximate = False
            else:
                eo.approximation = ApproximationMode.APPROXIMATE
                po.approximate = True
                po.exact = False

            result = self._calc.calculate_and_print(resolved, eo=eo, po=po)

            # Display result
            self._result_view.show_result(expression, result, exact=self._exact_mode)
            self._history_view.add_result(result, exact=self._exact_mode)

        except Exception:
            error_msg = traceback.format_exc()
            self._result_view.show_error(expression, error_msg)
            self._history_view.add_error(error_msg)

        # Return focus to input
        self._expr_edit.focus_input()

    def _resolve_answer_refs(self, expression: str) -> str:
        """Replace answer(N) references with actual result values.

        Args:
            expression: The raw expression text.

        Returns:
            The expression with answer(N) replaced by numeric values.
        """
        def _replace(match: re.Match) -> str:
            idx = int(match.group(1))
            value = self._history_view.get_answer(idx)
            if value is not None:
                return f"({value})"
            return match.group(0)  # leave unresolved

        return self._ANSWER_RE.sub(_replace, expression)

    def _on_history_recall(self, expression: str) -> None:
        """Handle expression recall from history view."""
        self._expr_edit.set_expression(expression)

    # ==================================================================
    # Mode toggle
    # ==================================================================

    def _on_mode_toggle(self) -> None:
        """Toggle exact/approximate mode."""
        self._exact_mode = self._exact_mode_var.get()
        self._mode_var.set("Exact" if self._exact_mode else "Approximate")
        self._mode_label.config(
            foreground="#1a5276" if self._exact_mode else "#7d6608"
        )

    # ==================================================================
    # View toggles
    # ==================================================================

    def _toggle_history(self) -> None:
        """Show or hide the history panel."""
        if self._show_history_var.get():
            self._history_frame.pack(fill=tk.BOTH, expand=True)
            # Re-add to paned if removed
            try:
                self._paned.add(self._history_frame, weight=1)
            except tk.TclError:
                pass  # already added
        else:
            self._paned.forget(self._history_frame)

    def _toggle_keypad(self) -> None:
        """Show or hide the virtual keypad."""
        if self._show_keypad_var.get():
            self._keypad_frame.grid(row=1, column=0, sticky="ew", pady=(0, 4))
            self._keypad_visible = True
        else:
            self._keypad_frame.grid_forget()
            self._keypad_visible = False

    def _toggle_conversion(self) -> None:
        """Show or hide the unit conversion panel."""
        if self._show_conversion_var.get():
            if not self._conversion_visible:
                self._paned.add(self._conversion_frame, weight=2)
                self._conversion_visible = True
        else:
            if self._conversion_visible:
                self._paned.forget(self._conversion_frame)
                self._conversion_visible = False

    def _on_conversion_result(self, expr: str, result: str) -> None:
        """Handle a successful conversion from the conversion panel."""
        self._result_view.show_result(expr, result, exact=True)
        self._history_view.add_expression(expr)
        self._history_view.add_result(result, exact=True)

    # ==================================================================
    # Keypad handlers
    # ==================================================================

    def _on_keypad_insert(self, text: str) -> None:
        """Insert text from keypad at the cursor position."""
        self._expr_edit.insert_at_cursor(text)

    def _on_keypad_clear(self) -> None:
        """Clear the expression via keypad."""
        self._expr_edit.clear()

    def _on_keypad_backspace(self) -> None:
        """Delete character before cursor via keypad."""
        entry_widget = self._expr_edit._entry
        try:
            pos = entry_widget.index(tk.INSERT)
            if pos > 0:
                entry_widget.delete(pos - 1)
        except tk.TclError:
            pass

    def _on_keypad_submit(self) -> None:
        """Submit expression via keypad equals button."""
        self._expr_edit._do_submit()

    # ==================================================================
    # Actions
    # ==================================================================

    def _open_plot_dialog(self) -> None:
        """Open the plot dialog, pre-filling with current expression if any."""
        expr = self._expr_edit.get_expression().strip()
        self._plot_dialog.show(expression=expr)

    def _open_import_csv(self) -> None:
        """Open the CSV import dialog."""
        self._import_csv_dialog.show()

    def _open_export_csv(self) -> None:
        """Open the CSV export dialog."""
        self._export_csv_dialog.show()

    def _get_last_result_for_export(self) -> "MathStructure | None":
        """Return the last calculation result as a MathStructure for CSV export."""
        try:
            last_expr = self._history_view.get_answer(0)
            if last_expr is not None:
                return self._calc.parse(str(last_expr))
        except Exception:
            pass
        return None

    def _open_preferences(self) -> None:
        """Open the preferences dialog."""
        self._prefs_dialog.show()

    def _on_preferences_apply(self) -> None:
        """Handle preferences being applied -- update mode display."""
        settings = self._prefs_dialog.get_settings()
        approx = settings.get("approximation", "exact")
        if approx == "exact":
            self._exact_mode = True
            self._exact_mode_var.set(True)
            self._mode_var.set("Exact")
            self._mode_label.config(foreground="#1a5276")
        else:
            self._exact_mode = False
            self._exact_mode_var.set(False)
            self._mode_var.set("Approximate")
            self._mode_label.config(foreground="#7d6608")

    def _copy_result(self) -> None:
        """Copy the last result to clipboard."""
        last = self._result_view.get_last_result()
        if last:
            self._root.clipboard_clear()
            self._root.clipboard_append(last)

    def _clear_all(self) -> None:
        """Clear expression, results, and history."""
        self._expr_edit.clear()
        self._result_view.clear()
        self._history_view.clear()

    def _show_about(self) -> None:
        """Show the About dialog."""
        messagebox.showinfo(
            "About PyQalculate",
            "PyQalculate v2.2\n\n"
            "A Python implementation of the Qalculate! calculator.\n\n"
            "Features:\n"
            "- Mathematical expression evaluation\n"
            "- Unit conversion\n"
            "- Built-in functions and variables\n"
            "- Expression history with answer(N) recall",
        )

    # ==================================================================
    # Run
    # ==================================================================

    def run(self) -> None:
        """Start the main event loop."""
        self._root.mainloop()

    @property
    def root(self) -> tk.Tk:
        """Return the root Tk window."""
        return self._root


def main() -> None:
    """Launch the PyQalculate GUI."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()

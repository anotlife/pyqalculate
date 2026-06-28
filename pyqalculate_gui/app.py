"""Application controller — owns root, state, services, and event wiring.

Replaces the old MainWindow god object.  All widget communication flows
through the EventBus; no widget holds a reference to another widget.
"""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk

from pyqalculate.types import ApproximationMode, EvaluationOptions
from pyqalculate_gui.autocomplete import AutoComplete
from pyqalculate_gui.calculator_service import CalculatorService
from pyqalculate_gui.dialogs.functions_list import FunctionsListDialog
from pyqalculate_gui.event_bus import (
    CLEAR_ALL,
    COPY_RESULT,
    EXPRESSION_SUBMITTED,
    EXPORT_CSV,
    HISTORY_RECALLED,
    IMPORT_CSV,
    OPEN_NUMBER_BASES,
    OPEN_PLOT,
    OPEN_PREFERENCES,
    PREFERENCE_APPLIED,
    RESULT_DISPLAYED,
    TOGGLE_CONVERSION,
    TOGGLE_HISTORY,
    TOGGLE_KEYPAD,
    EventBus,
)
from pyqalculate_gui.conversion_view import ConversionView
from pyqalculate_gui.expression_edit import ExpressionEdit
from pyqalculate_gui.expression_status import ExpressionStatusBar
from pyqalculate_gui.keyboard_shortcuts import (
    SHORTCUT_TYPE_ACTIVATE_FIRST_COMPLETION,
    SHORTCUT_TYPE_COPY_RESULT as KS_COPY_RESULT,
    SHORTCUT_TYPE_HELP,
    SHORTCUT_TYPE_HISTORY,
    SHORTCUT_TYPE_HISTORY_CLEAR,
    SHORTCUT_TYPE_KEYPAD,
    SHORTCUT_TYPE_MANAGE_FUNCTIONS,
    SHORTCUT_TYPE_MANAGE_UNITS,
    SHORTCUT_TYPE_MANAGE_VARIABLES,
    SHORTCUT_TYPE_MINIMAL,
    SHORTCUT_TYPE_NUMBER_BASES,
    SHORTCUT_TYPE_PARENTHESES,
    SHORTCUT_TYPE_PROGRAMMING,
    SHORTCUT_TYPE_QUIT,
    SHORTCUT_TYPE_RPN_CLEAR,
    SHORTCUT_TYPE_RPN_COPY,
    SHORTCUT_TYPE_RPN_DELETE,
    SHORTCUT_TYPE_RPN_DOWN,
    SHORTCUT_TYPE_RPN_LASTX,
    SHORTCUT_TYPE_RPN_SWAP,
    SHORTCUT_TYPE_RPN_UP,
    SHORTCUT_TYPE_STORE,
    KeyboardShortcutManager,
)
from pyqalculate_gui.keypad import KeypadWidget
from pyqalculate_gui.menu_bar import MenuBar
from pyqalculate_gui.plot_dialog import PlotDialog
from pyqalculate_gui.preferences_dialog import PreferencesDialog
from pyqalculate_gui.result_view import ResultView
from pyqalculate_gui.state import AppState
from pyqalculate_gui.status_bar import StatusBar
from pyqalculate_gui.theme import LIGHT, Theme, get_theme

_ANSWER_RE = re.compile(r"answer\(\s*(-?\d+)\s*\)")


class App:
    """Top-level application: root window + services + event wiring.

    Creates every widget and dialog, then delegates all inter-widget
    communication to the EventBus.  No widget references cross except
    through events.
    """

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("PyQalculate")
        self._root.geometry("800x600")
        self._root.minsize(600, 400)

        self._state = AppState()
        self._theme: Theme = LIGHT
        self._event_bus = EventBus()
        self._calculator = CalculatorService()
        self._eo = EvaluationOptions(approximation=ApproximationMode.TRY_EXACT)

        self._build_ui()
        self._wire_events()
        self._init_shortcuts()
        self._update_status()
        self._root.after(100, self._expr_edit.focus_input)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the widget tree.

        Layout matches original qalculate-gtk:
        - MenuBar (top)
        - ResultView (expandable middle)
        - ExpressionEdit
        - ExpressionStatusBar
        - KeypadWidget
        - PanedWindow (History + Conversion)
        - StatusBar (bottom)
        """
        self._menu_bar = MenuBar(
            self._root, theme=self._theme, event_bus=self._event_bus,
        )
        self._exact_var = self._menu_bar.get_exact_mode_var()
        self._exact_var.trace_add("write", self._on_exact_mode_toggle)

        main = ttk.Frame(self._root, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        # Status bar at bottom (packed first to anchor)
        self._status_bar = StatusBar(
            main, theme=self._theme, event_bus=self._event_bus,
        )
        self._status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(4, 0))

        # Keypad at bottom
        self._keypad = KeypadWidget(
            main, theme=self._theme, event_bus=self._event_bus,
        )
        self._keypad.pack(fill=tk.X, side=tk.BOTTOM, pady=(4, 0))

        # PanedWindow for conversion (bottom area)
        self._paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL, height=150)
        self._paned.pack(fill=tk.X, side=tk.BOTTOM, pady=(4, 0))

        self._conversion_view = ConversionView(
            self._paned, theme=self._theme, event_bus=self._event_bus,
            calculator=self._calculator,
        )
        self._paned.add(self._conversion_view, weight=1)

        # Expression status bar (below expression)
        self._expr_status = ExpressionStatusBar(
            main, theme=self._theme, event_bus=self._event_bus,
        )
        self._expr_status.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 4))

        # Expression edit (below result)
        self._expr_edit = ExpressionEdit(
            main,
            theme=self._theme,
            event_bus=self._event_bus,
            state=self._state,
        )
        self._expr_edit.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 0))
        self._expr_edit.pack_propagate(False)
        self._expr_edit.configure(height=40)

        # Autocomplete popup — wired to expression edit's text widget
        self._autocomplete = AutoComplete(
            self._expr_edit,
            theme=self._theme,
            calculator=self._calculator,
        )
        self._autocomplete.set_on_select(self._on_autocomplete_select)
        self._expr_edit.bind_key("<KeyRelease>", self._on_key_release)
        self._expr_edit.bind_key("<Up>", self._on_nav_key)
        self._expr_edit.bind_key("<Down>", self._on_nav_key)
        self._expr_edit.bind_key("<Escape>", self._on_escape_key)
        self._expr_edit.bind_key("<Tab>", self._on_tab_key)

        # Result view (expandable middle - fills remaining space)
        self._result_view = ResultView(
            main, theme=self._theme, event_bus=self._event_bus,
        )
        self._result_view.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    # ------------------------------------------------------------------
    # Event wiring
    # ------------------------------------------------------------------

    def _wire_events(self) -> None:
        """Subscribe App handlers to EventBus events."""
        bus = self._event_bus
        bus.subscribe(EXPRESSION_SUBMITTED, self._on_expression_submitted)
        bus.subscribe("keypad_insert", self._expr_edit.insert_at_cursor)
        bus.subscribe("keypad_clear", self._expr_edit.clear)
        bus.subscribe("keypad_backspace", self._on_backspace)
        bus.subscribe("keypad_negate", self._on_negate)
        bus.subscribe(CLEAR_ALL, self._on_clear_all)
        bus.subscribe(OPEN_NUMBER_BASES, self._open_number_bases)
        bus.subscribe(OPEN_PREFERENCES, self._on_open_preferences)
        bus.subscribe(OPEN_PLOT, self._on_open_plot)
        bus.subscribe(COPY_RESULT, self._on_copy_result)
        bus.subscribe(HISTORY_RECALLED, self._on_history_recalled)
        bus.subscribe(PREFERENCE_APPLIED, self._on_preference_applied)
        bus.subscribe(TOGGLE_KEYPAD, self._on_toggle_keypad)
        bus.subscribe(TOGGLE_HISTORY, self._on_toggle_history)
        bus.subscribe(TOGGLE_CONVERSION, self._on_toggle_conversion)
        bus.subscribe(RESULT_DISPLAYED, self._on_result_displayed)
        bus.subscribe(IMPORT_CSV, self._on_import_csv)
        bus.subscribe(EXPORT_CSV, self._on_export_csv)
        bus.subscribe("open_manage_functions", lambda: self._open_manage_functions())

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def _init_shortcuts(self) -> None:
        """Create shortcut manager and register handlers."""
        self._shortcut_mgr = KeyboardShortcutManager(
            self._root, event_bus=self._event_bus,
        )

        mgr = self._shortcut_mgr
        mgr.register_handler(SHORTCUT_TYPE_QUIT, lambda v: self._root.destroy())
        mgr.register_handler(SHORTCUT_TYPE_HELP, lambda v: self._show_help())
        mgr.register_handler(SHORTCUT_TYPE_NUMBER_BASES, lambda v: self._open_number_bases())
        mgr.register_handler(KS_COPY_RESULT, lambda v: self._on_copy_result())
        mgr.register_handler(SHORTCUT_TYPE_STORE, lambda v: self._store_result())
        mgr.register_handler(SHORTCUT_TYPE_MANAGE_VARIABLES, lambda v: self._open_manage_variables())
        mgr.register_handler(SHORTCUT_TYPE_MANAGE_FUNCTIONS, lambda v: self._open_manage_functions())
        mgr.register_handler(SHORTCUT_TYPE_MANAGE_UNITS, lambda v: self._open_manage_units())
        mgr.register_handler(SHORTCUT_TYPE_KEYPAD, lambda v: self._on_toggle_keypad())
        mgr.register_handler(SHORTCUT_TYPE_HISTORY, lambda v: self._on_toggle_history())
        mgr.register_handler(SHORTCUT_TYPE_MINIMAL, lambda v: self._toggle_minimal())
        mgr.register_handler(SHORTCUT_TYPE_PROGRAMMING, lambda v: self._toggle_programming())
        mgr.register_handler(SHORTCUT_TYPE_PARENTHESES, lambda v: self._insert_parentheses())
        mgr.register_handler(SHORTCUT_TYPE_RPN_UP, lambda v: self._rpn_up())
        mgr.register_handler(SHORTCUT_TYPE_RPN_DOWN, lambda v: self._rpn_down())
        mgr.register_handler(SHORTCUT_TYPE_RPN_SWAP, lambda v: self._rpn_swap())
        mgr.register_handler(SHORTCUT_TYPE_RPN_COPY, lambda v: self._rpn_copy())
        mgr.register_handler(SHORTCUT_TYPE_RPN_LASTX, lambda v: self._rpn_lastx())
        mgr.register_handler(SHORTCUT_TYPE_RPN_DELETE, lambda v: self._rpn_delete())
        mgr.register_handler(SHORTCUT_TYPE_RPN_CLEAR, lambda v: self._rpn_clear())
        mgr.register_handler(SHORTCUT_TYPE_ACTIVATE_FIRST_COMPLETION, lambda v: self._activate_completion())
        mgr.register_handler(SHORTCUT_TYPE_HISTORY_CLEAR, lambda v: self._result_view.clear())

    # ------------------------------------------------------------------
    # Handlers — calculation flow
    # ------------------------------------------------------------------

    def _on_expression_submitted(self, expression: str) -> None:
        """Evaluate *expression* (or the edit widget text if empty)."""
        expr = expression or self._expr_edit.get_expression()
        expr = self._resolve_answer_refs(expr.strip())
        if not expr:
            return

        result = self._calculator.calculate(expr, eo=self._eo)
        if result.error:
            self._result_view.show_error(result.error)
            self._expr_status.show_error(result.error)
        else:
            self._result_view.show_result(expr, result.result, result.exact)
            self._expr_status.show_autocalc_result(
                result.result, result.exact
            )

        self._expr_edit.clear()
        self._expr_edit.focus_input()

    def _resolve_answer_refs(self, expression: str) -> str:
        """Replace ``answer(N)`` tokens with past results."""

        def _replace(match: re.Match[str]) -> str:
            idx = int(match.group(1))
            value = self._result_view.get_answer(idx)
            return f"({value})" if value is not None else match.group(0)

        return _ANSWER_RE.sub(_replace, expression)

    # ------------------------------------------------------------------
    # Handlers — keypad helpers
    # ------------------------------------------------------------------

    def _on_backspace(self) -> None:
        """Delete the last character from the expression."""
        expr = self._expr_edit.get_expression()
        if expr:
            self._expr_edit.set_expression(expr[:-1])

    def _on_negate(self) -> None:
        """Toggle a leading minus sign."""
        expr = self._expr_edit.get_expression()
        if expr.startswith("-"):
            self._expr_edit.set_expression(expr[1:])
        elif expr:
            self._expr_edit.set_expression(f"-{expr}")

    # ------------------------------------------------------------------
    # Handlers — menu actions
    # ------------------------------------------------------------------

    def _on_clear_all(self) -> None:
        """Reset expression, results, and history."""
        self._expr_edit.clear()
        self._result_view.clear()
        self._expr_status.clear()

    def _on_open_preferences(self) -> None:
        """Show the preferences dialog modally."""
        PreferencesDialog(
            self._root, theme=self._theme, event_bus=self._event_bus,
        ).show()

    def _on_open_plot(self) -> None:
        """Show the plot dialog, pre-filling the current expression."""
        PlotDialog(self._root, theme=self._theme).show(
            expression=self._expr_edit.get_expression().strip(),
        )

    def _on_copy_result(self) -> None:
        """Copy the last result to the system clipboard."""
        result = self._result_view.get_last_result()
        if result:
            self._root.clipboard_clear()
            self._root.clipboard_append(result)

    def _on_import_csv(self) -> None:
        """Show the import CSV dialog."""
        from pyqalculate_gui.import_csv_dialog import ImportCsvDialog

        ImportCsvDialog(
            self._root, theme=self._theme, calculator=self._calculator,
        ).show()

    def _on_export_csv(self) -> None:
        """Show the export CSV dialog."""
        from pyqalculate_gui.export_csv_dialog import ExportCsvDialog

        ExportCsvDialog(
            self._root,
            theme=self._theme,
            calculator=self._calculator,
            get_last_result=self._result_view.get_last_result,
        ).show()

    def _on_history_recalled(self, expression: str) -> None:
        """Put a recalled expression back into the edit widget."""
        self._expr_edit.set_expression(expression)
        self._expr_edit.focus_input()

    def _on_preference_applied(self, settings: dict[str, object]) -> None:
        """React to preference changes (theme switch, approximation, etc.)."""
        theme_name = settings.get("theme", "light")
        if isinstance(theme_name, str):
            self._theme = get_theme(theme_name)
        # Push new theme to every child widget that supports it
        for widget in (
            self._menu_bar,
            self._status_bar,
            self._keypad,
            self._conversion_view,
            self._expr_status,
            self._expr_edit,
            self._result_view,
            self._autocomplete,
        ):
            set_theme_fn = getattr(widget, "set_theme", None)
            if set_theme_fn is not None:
                set_theme_fn(self._theme)

        # Wire approximation mode from preferences
        approx_map = {
            "exact": ApproximationMode.EXACT,
            "try_exact": ApproximationMode.TRY_EXACT,
            "approximate": ApproximationMode.APPROXIMATE,
        }
        approx_str = settings.get("approximation", "try_exact")
        approx_mode = approx_map.get(str(approx_str), ApproximationMode.TRY_EXACT)
        self._eo = EvaluationOptions(approximation=approx_mode)

        # Sync the Exact Mode checkbox to match
        self._exact_var.set(approx_mode == ApproximationMode.EXACT)

    def _on_exact_mode_toggle(self, *args: object) -> None:
        """React to the Exact Mode menu checkbox toggle."""
        is_exact = self._exact_var.get()
        self._eo = EvaluationOptions(
            approximation=ApproximationMode.EXACT
            if is_exact
            else ApproximationMode.TRY_EXACT,
        )

    def _on_result_displayed(self, expression: str, result: str, exact: bool) -> None:
        """Update expression status bar when a result is displayed."""
        self._expr_status.show_autocalc_result(result, exact)

    # ------------------------------------------------------------------
    # Handlers — view toggles
    # ------------------------------------------------------------------

    def _on_toggle_keypad(self) -> None:
        """Show or hide the virtual keypad."""
        if self._keypad.winfo_viewable():
            self._keypad.pack_forget()
        else:
            self._keypad.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 4), after=self._expr_edit)

    def _on_toggle_history(self) -> None:
        """History view removed — no-op for backward compat."""
        pass

    def _on_toggle_conversion(self) -> None:
        """Show or hide the conversion pane inside the PanedWindow."""
        try:
            self._paned.forget(self._conversion_view)
        except tk.TclError:
            self._paned.add(self._conversion_view, weight=1)

    # ------------------------------------------------------------------
    # Handlers — keyboard shortcut actions
    # ------------------------------------------------------------------

    def _show_help(self) -> None:
        """Open the help dialog."""
        from pyqalculate_gui.dialogs.help_dialog import HelpDialog

        HelpDialog(self._root, theme=self._theme).show()

    def _open_number_bases(self) -> None:
        """Open number base conversion dialog."""
        from pyqalculate_gui.dialogs.number_bases import NumberBasesDialog

        initial = self._result_view.get_last_result() or ""
        NumberBasesDialog(
            self._root,
            theme=self._theme,
            calculator=self._calculator,
            initial_value=initial,
        ).show()

    def _store_result(self) -> None:
        """Store the current result as a variable."""
        result = self._result_view.get_last_result()
        if result:
            self._event_bus.emit("store_result", result)

    def _open_manage_variables(self) -> None:
        """Open the manage variables dialog."""
        self._event_bus.emit("open_manage_variables")

    def _open_manage_functions(self) -> None:
        """Open the manage functions dialog."""
        FunctionsListDialog(
            self._root,
            theme=self._theme,
            event_bus=self._event_bus,
            calculator=self._calculator,
        ).show()

    def _open_manage_units(self) -> None:
        """Open the manage units dialog."""
        self._event_bus.emit("open_manage_units")

    def _toggle_minimal(self) -> None:
        """Toggle minimal window mode (hide keypad)."""
        self._on_toggle_keypad()

    def _toggle_programming(self) -> None:
        """Toggle programming keypad mode."""
        self._event_bus.emit("toggle_programming")

    def _insert_parentheses(self) -> None:
        """Insert a pair of parentheses at cursor."""
        self._expr_edit.insert_at_cursor("()")

    def _rpn_up(self) -> None:
        """RPN: move up in stack."""
        self._event_bus.emit("rpn_up")

    def _rpn_down(self) -> None:
        """RPN: move down in stack."""
        self._event_bus.emit("rpn_down")

    def _rpn_swap(self) -> None:
        """RPN: swap top two stack items."""
        self._event_bus.emit("rpn_swap")

    def _rpn_copy(self) -> None:
        """RPN: copy top of stack."""
        self._event_bus.emit("rpn_copy")

    def _rpn_lastx(self) -> None:
        """RPN: recall last x value."""
        self._event_bus.emit("rpn_lastx")

    def _rpn_delete(self) -> None:
        """RPN: delete top of stack."""
        self._event_bus.emit("rpn_delete")

    def _rpn_clear(self) -> None:
        """RPN: clear the entire stack."""
        self._event_bus.emit("rpn_clear")

    def _activate_completion(self) -> None:
        """Activate the first completion suggestion."""
        if self._autocomplete.is_visible():
            selected = self._autocomplete.get_selected()
            if selected:
                self._on_autocomplete_select(selected)
        else:
            # Trigger completion for the current word
            text = self._expr_edit.get_text_before_cursor()
            full_text = self._expr_edit.get_expression()
            self._autocomplete.update(full_text, len(text))

    # ------------------------------------------------------------------
    # Autocomplete integration
    # ------------------------------------------------------------------

    def _on_key_release(self, event: tk.Event) -> None:
        """Feed current text and cursor to the autocomplete system."""
        if event.keysym in ("Up", "Down", "Tab", "Escape", "Return"):
            return
        text = self._expr_edit.get_expression()
        cursor_text = self._expr_edit.get_text_before_cursor()
        self._autocomplete.update(text, len(cursor_text))

    def _on_nav_key(self, event: tk.Event) -> str | None:
        """Route Up/Down to autocomplete when popup is visible."""
        if self._autocomplete.is_visible():
            if event.keysym == "Up":
                self._autocomplete.select_previous()
            else:
                self._autocomplete.select_next()
            return "break"
        return None

    def _on_escape_key(self, event: tk.Event) -> str | None:
        """Hide autocomplete on Escape, or propagate if already hidden."""
        if self._autocomplete.is_visible():
            self._autocomplete.hide()
            return "break"
        return None

    def _on_tab_key(self, event: tk.Event) -> str | None:
        """Accept current autocomplete selection on Tab."""
        if self._autocomplete.is_visible():
            selected = self._autocomplete.get_selected()
            if selected:
                self._on_autocomplete_select(selected)
            return "break"
        return None

    def _on_autocomplete_select(self, name: str) -> None:
        """Insert the selected completion into the expression edit."""
        text = self._expr_edit.get_expression()
        cursor_pos = self._expr_edit.get_cursor_position()

        # Find word start (same break-char logic as AutoComplete)
        word_start = cursor_pos
        while word_start > 0 and text[word_start - 1] not in " \t+-*/^()=,;<>!|&%":
            word_start -= 1

        # Insert completion — append "(" for functions
        insert_text = name
        for func_name in self._calculator.get_functions():
            if func_name == name:
                insert_text = f"{name}("
                break
        self._expr_edit.replace_current_word(insert_text, word_start)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def _update_status(self) -> None:
        """Push calculator statistics into the status bar."""
        self._status_bar.update_stats(
            len(self._calculator.get_functions()),
            len(self._calculator.get_units()),
            len(self._calculator.get_variables()),
        )

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Enter the tkinter main loop."""
        self._root.mainloop()


def main() -> None:
    """Application entry point."""
    App().run()


if __name__ == "__main__":
    main()

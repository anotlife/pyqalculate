"""PyQalculate CLI - command-line calculator.

Entry point for the 'pyqalc' command.  Supports both single-expression
evaluation and an interactive REPL with readline history, tab completion,
colour output, and a set of built-in meta-commands.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Sequence

from pyqalculate.calculator import Calculator
from pyqalculate.types import (
    BASE_BINARY,
    BASE_DECIMAL,
    BASE_HEXADECIMAL,
    BASE_OCTAL,
    EvaluationOptions,
    ApproximationMode,
    PrintOptions,
)
from pyqalculate.variable import KnownVariable
from pyqalculate.math_structure import MathStructure

VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

_COLOR_SUPPORTED = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
_ENABLE_COLOR = _COLOR_SUPPORTED


def _c(text: str, code: str) -> str:  # pragma: no cover - cosmetic
    """Wrap *text* in an ANSI colour *code* if colour is enabled."""
    if not _ENABLE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _bold(text: str) -> str:
    return _c(text, "1")


def _green(text: str) -> str:
    return _c(text, "32")


def _yellow(text: str) -> str:
    return _c(text, "33")


def _cyan(text: str) -> str:
    return _c(text, "36")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for pyqalc."""
    parser = argparse.ArgumentParser(
        prog="pyqalc",
        description="PyQalculate! - the ultimate CLI calculator",
    )
    parser.add_argument(
        "expression",
        nargs="*",
        help="Expression to evaluate",
    )
    parser.add_argument(
        "-t",
        "--terse",
        action="store_true",
        default=False,
        help="Show only the result (no expression echo)",
    )
    parser.add_argument(
        "-b",
        "--base",
        type=int,
        default=None,
        metavar="BASE",
        help="Set the number base for output (e.g. 2, 8, 10, 16)",
    )
    parser.add_argument(
        "-s",
        "--set",
        type=str,
        default=None,
        metavar="OPTION",
        help='Set an option (e.g. "precision 20")',
    )
    parser.add_argument(
        "-e",
        "--exrates",
        action="store_true",
        default=False,
        help="Update exchange rates on start",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"pyqalc {VERSION}",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colour output",
    )
    return parser


# ---------------------------------------------------------------------------
# Readline setup (optional)
# ---------------------------------------------------------------------------


def _setup_readline() -> list[str]:
    """Try to import readline and configure history.  Returns completer words."""
    words: list[str] = []
    try:
        import readline  # noqa: F811

        # Attempt to load persistent history
        histfile = os.path.join(os.path.expanduser("~"), ".pyqalc_history")
        try:
            readline.read_history_file(histfile)
        except FileNotFoundError:
            pass
        readline.set_history_length(1000)

        import atexit

        atexit.register(lambda: readline.write_history_file(histfile))

        words = _COMPLETER_WORDS  # will be populated later
    except ImportError:
        pass
    return words


# Populated by interactive_mode once the calculator is ready
_COMPLETER_WORDS: list[str] = []


def _make_completer(calc: Calculator) -> list[str]:
    """Build a list of known names for tab completion."""
    words: list[str] = []
    words.extend(calc._functions.keys())
    words.extend(calc._variables.keys())
    words.extend(calc._units.keys())
    # Add built-in commands
    words.extend([
        "set", "save", "delete", "assume", "base", "mode",
        "help", "quit", "exit", "factorize", "simplify",
        "functions", "constants",
        "plot", "plot3d", "plot_implicit", "subplot",
    ])
    return words


def _get_completion_description(word: str, calc: Calculator) -> str:
    """Get a short description for a completion word."""
    # Check if it's a function
    func = calc.get_function(word)
    if func:
        title = func.title()
        args = func.min_args()
        max_args = func.max_args()
        if max_args > args:
            return f"{title} ({args}-{max_args} args)"
        elif args > 0:
            return f"{title} ({args} args)"
        else:
            return title

    # Check if it's a variable
    var = calc.get_variable(word)
    if var:
        return var.title() or "variable"

    # Check if it's a unit
    unit = calc.get_unit(word)
    if unit:
        return unit.title() or "unit"

    # Built-in commands
    cmd_descs = {
        "set": "Show/set options",
        "save": "Save a variable",
        "delete": "Delete a variable",
        "assume": "Set assumptions",
        "base": "Change output base",
        "mode": "Change calculation mode",
        "help": "Show help",
        "quit": "Exit program",
        "exit": "Exit program",
        "factorize": "Factorize last result",
        "simplify": "Simplify last result",
        "functions": "List all functions",
        "constants": "List all constants",
        "plot": "Plot expression (interactive or save to file)",
        "plot3d": "3D surface plot (not yet implemented)",
        "plot_implicit": "Plot implicit equation f(x,y)=0",
        "subplot": "Combine multiple plots in a grid layout",
    }
    return cmd_descs.get(word, "")


def _install_completer(words: list[str], calc: Calculator) -> None:
    """Install a readline tab-completer using *words*."""
    try:
        import readline  # noqa: F811

        def completer(text: str, state: int) -> str | None:
            options = [w for w in words if w.startswith(text.lower())]
            if state < len(options):
                word = options[state]
                # Show description on second tab press
                if state == 0 and len(options) == 1:
                    desc = _get_completion_description(word, calc)
                    if desc:
                        print(f"\n  {word} - {desc}")
                return options[state]
            return None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")
    except ImportError:
        pass


# ---------------------------------------------------------------------------
# Interactive commands
# ---------------------------------------------------------------------------

HELP_TEXT = """\
PyQalculate {version} - interactive calculator

Type any mathematical expression to evaluate it.
Special commands:
  set [option [value]]     Show/set options (precision, base, etc.)
  base <n>                 Change the output number base
  save <name> [value]      Save a variable
  delete <name>            Delete a user variable
  assume <assumptions>     Set assumptions for unknowns
  mode [mode_name]         Show/change calculation mode
  factorize                Factorize last result
  simplify                 Simplify last result
  help [function]          Show help for a function (e.g. help sin)
  functions                List all available functions
  constants                List all physical constants
  plot(expr)               Plot expression in interactive window
  plot_implicit(expr)      Plot implicit equation f(x,y)=0
  subplot(r,c,plots...)    Combine plots: subplot(1,2,plot(sin(x)),plot(cos(x)))
  quit / exit              Exit the program
"""


def _handle_help_function(func_name: str, calc: Calculator) -> str | None:
    """Show help for a specific function, variable, or unit."""
    # Try function first
    func = calc.get_function(func_name)
    if func is not None:
        lines = []
        lines.append(f"  {func.name()} - {func.title()}")
        lines.append(f"  Category: {func.category()}")

        # Build argument signature
        min_a = func.min_args()
        max_a = func.max_args()
        arg_parts = []
        for i in range(max_a if max_a > 0 else min_a):
            arg_def = func.get_argument_definition(i)
            if arg_def:
                arg_name = arg_def.name() or f"arg{i+1}"
                arg_type = arg_def.print_short()
                if i >= min_a:
                    arg_parts.append(f"[{arg_name}:{arg_type}]")
                else:
                    arg_parts.append(f"{arg_name}:{arg_type}")
            else:
                arg_parts.append(f"arg{i+1}")

        if arg_parts:
            lines.append(f"  Syntax: {func.name()}({', '.join(arg_parts)})")
        else:
            lines.append(f"  Syntax: {func.name()}()")

        if func.description():
            lines.append(f"  Description: {func.description()}")

        if func.example():
            lines.append(f"  Example: {func.example()}")

        return "\n".join(lines)

    # Try variable
    var = calc.get_variable(func_name)
    if var is not None:
        lines = []
        lines.append(f"  {var.name()} - {var.title()}")
        lines.append(f"  Category: {var.category()}")
        if var.description():
            lines.append(f"  Description: {var.description()}")
        return "\n".join(lines)

    # Try unit
    unit = calc.get_unit(func_name)
    if unit is not None:
        lines = []
        lines.append(f"  {unit.name()} - {unit.title()}")
        lines.append(f"  Category: {unit.category()}")
        if unit.description():
            lines.append(f"  Description: {unit.description()}")
        return "\n".join(lines)

    return f"Error: unknown function/unit '{func_name}'"


def _list_functions_by_category(calc: Calculator) -> str:
    """List all functions organized by category."""
    categories: dict[str, list[str]] = {}
    for name, func in calc._functions.items():
        cat = func.category() or "Other"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(name)

    lines = []
    for cat in sorted(categories.keys()):
        funcs = sorted(categories[cat])
        lines.append(f"\n  {cat}:")
        lines.append(f"    {', '.join(funcs)}")

    return "\n".join(lines)


def _list_constants(calc: Calculator) -> str:
    """List all physical constants."""
    from pyqalculate.variable import KnownVariable
    constants = []
    for name, var in calc._variables.items():
        if isinstance(var, KnownVariable):
            try:
                val = var.get()
                if val is not None:
                    constants.append((name, str(val)))
            except:
                pass

    lines = ["  Physical Constants:"]
    for name, val in sorted(constants)[:50]:  # Show first 50
        lines.append(f"    {name} = {val}")
    if len(constants) > 50:
        lines.append(f"    ... and {len(constants) - 50} more")
    return "\n".join(lines)


def _handle_set_command(
    args: list[str],
    po: PrintOptions,
    eo: EvaluationOptions,
    calc: Calculator,
) -> str | None:
    """Handle the 'set' command.  Returns a status message."""
    if not args:
        # Show current settings
        lines = [
            f"  precision = {calc.get_precision()}",
            f"  base = {po.base}",
            f"  terse = {po.spacious is False}",
            f"  approximation = {eo.approximation.name}",
        ]
        return "\n".join(lines)

    option = args[0].lower()
    value = args[1] if len(args) > 1 else None

    if option == "precision" and value is not None:
        try:
            n = int(value)
            calc.set_precision(n)
            return f"precision = {n}"
        except ValueError:
            return "Error: precision must be an integer"

    if option == "base" and value is not None:
        try:
            b = int(value)
            po.base = b
            return f"base = {b}"
        except ValueError:
            return "Error: base must be an integer"

    if option in ("approx", "approximation") and value is not None:
        v = value.lower()
        if v in ("exact",):
            eo.approximation = ApproximationMode.EXACT
            return "approximation = EXACT"
        if v in ("approx", "approximate"):
            eo.approximation = ApproximationMode.APPROXIMATE
            return "approximation = APPROXIMATE"
        if v in ("try", "try_exact"):
            eo.approximation = ApproximationMode.TRY_EXACT
            return "approximation = TRY_EXACT"
        return f"Error: unknown approximation mode '{value}'"

    return f"Error: unknown option '{option}'"


def _handle_base_command(
    args: list[str],
    po: PrintOptions,
) -> str | None:
    """Handle the 'base' command."""
    if not args:
        return f"Current base: {po.base}"

    base_str = args[0].lower().strip()
    base_map = {
        "bin": BASE_BINARY, "binary": BASE_BINARY, "2": BASE_BINARY,
        "oct": BASE_OCTAL, "octal": BASE_OCTAL, "8": BASE_OCTAL,
        "dec": BASE_DECIMAL, "decimal": BASE_DECIMAL, "10": BASE_DECIMAL,
        "hex": BASE_HEXADECIMAL, "hexadecimal": BASE_HEXADECIMAL, "16": BASE_HEXADECIMAL,
    }

    if base_str in base_map:
        po.base = base_map[base_str]
        return f"Base set to {po.base}"

    try:
        b = int(base_str)
        if 2 <= b <= 36:
            po.base = b
            return f"Base set to {b}"
        return "Error: base must be between 2 and 36"
    except ValueError:
        return f"Error: unknown base '{base_str}'"


def _handle_save_command(
    args: list[str],
    calc: Calculator,
    last_result: MathStructure | None,
) -> str | None:
    """Handle the 'save' command."""
    if not args:
        return "Usage: save <name> [value]"

    name = args[0]
    if len(args) > 1:
        value_str = " ".join(args[1:])
    elif last_result is not None:
        # Save the last result
        var = KnownVariable("User", name, last_result, f"User variable: {name}")
        calc.add_variable(var)
        return f"Saved '{name}' = {calc.print_result(last_result)}"
    else:
        return "Error: no result to save"

    # Parse the value expression
    try:
        result = calc.calculate(value_str)
        var = KnownVariable("User", name, result, f"User variable: {name}")
        calc.add_variable(var)
        return f"Saved '{name}' = {calc.print_result(result)}"
    except Exception as e:
        return f"Error: {e}"


def _handle_delete_command(
    args: list[str],
    calc: Calculator,
) -> str | None:
    """Handle the 'delete' command."""
    if not args:
        return "Usage: delete <name>"

    name = args[0].lower()
    if name in calc._variables:
        del calc._variables[name]
        return f"Deleted variable '{name}'"
    if name in calc._functions:
        del calc._functions[name]
        return f"Deleted function '{name}'"
    return f"Error: '{name}' not found"


def _handle_assume_command(
    args: list[str],
    calc: Calculator,
) -> str | None:
    """Handle the 'assume' command."""
    if not args:
        return "Usage: assume <assumptions>  (e.g. 'x > 0', 'y is integer')"
    # For now, just echo back - full assumption parsing would require
    # extending the parser
    return f"Assumptions noted: {' '.join(args)}"


def _handle_mode_command(
    args: list[str],
    po: PrintOptions,
    eo: EvaluationOptions,
) -> str | None:
    """Handle the 'mode' command."""
    if not args:
        modes = [
            f"  base = {po.base}",
            f"  approximation = {eo.approximation.name}",
            f"  exact = {po.exact}",
            f"  fraction = {po.number_fraction_format.name}",
        ]
        return "Current mode:\n" + "\n".join(modes)

    mode = args[0].lower()
    if mode == "exact":
        po.exact = True
        po.approximate = False
        eo.approximation = ApproximationMode.EXACT
        return "Mode: exact"
    if mode in ("approx", "approximate"):
        po.exact = False
        po.approximate = True
        eo.approximation = ApproximationMode.APPROXIMATE
        return "Mode: approximate"
    if mode == "fraction":
        from pyqalculate.types import NumberFractionFormat
        po.number_fraction_format = NumberFractionFormat.FRACTIONAL
        return "Mode: fraction"
    if mode == "decimal":
        from pyqalculate.types import NumberFractionFormat
        po.number_fraction_format = NumberFractionFormat.DECIMAL
        return "Mode: decimal"

    return f"Error: unknown mode '{mode}'"


def _handle_plot_command(args: list[str], full_line: str) -> None:
    """Handle: plot(expr) or plot(expr, file.png)"""
    import re
    from pyqalculate.plot import Plotter
    # Parse: plot(expr) or plot(expr, filename.png)
    m = re.match(r'^plot\((.+)\)$', full_line.strip())
    if not m:
        print("Usage: plot(expression) — opens interactive window")
        return
    inner = m.group(1)
    # Check if last arg is a filename
    parts = inner.rsplit(',', 1)
    if len(parts) == 2 and parts[1].strip().endswith('.png'):
        expr = parts[0].strip()
        filename = parts[1].strip()
    else:
        expr = inner.strip()
        filename = ""
    try:
        plotter = Plotter()
        result = plotter.plot(expr, filename=filename)
        if result:
            print(f"  Saved: {result}")
        else:
            print("  Plot window closed.")
    except Exception as e:
        print(f"  Plot error: {e}")


def _handle_plot3d_command(args: list[str]) -> None:
    """Handle: plot3d(expr, x_min, x_max, y_min, y_max) — 3D surface plot"""
    print("  3D plotting not yet implemented. Use plot() for 2D.")


def _handle_plot_implicit_command(args: list[str]) -> None:
    """Handle: plot_implicit(expr) or plot_implicit(expr, file.png)"""
    import re
    from pyqalculate.plot import Plotter
    # Build the original line from args
    line = "plot_implicit(" + " ".join(args) + ")"
    m = re.match(r'^plot_implicit\((.+)\)$', line.strip())
    if not m:
        print("Usage: plot_implicit(expression) — opens interactive window")
        return
    inner = m.group(1)
    parts = inner.rsplit(',', 1)
    if len(parts) == 2 and parts[1].strip().endswith('.png'):
        expr = parts[0].strip()
        filename = parts[1].strip()
    else:
        expr = inner.strip()
        filename = ""
    try:
        plotter = Plotter()
        result = plotter.plot_implicit(expr, filename=filename)
        if result:
            print(f"  Saved: {result}")
        else:
            print("  Plot window closed.")
    except Exception as e:
        print(f"  Plot error: {e}")


def _handle_subplot_command(full_line: str) -> None:
    """Handle: subplot(rows, cols, plot(...), plot_implicit(...), ...)"""
    import re
    from pyqalculate.plot import Plotter

    # Parse: subplot(rows, cols, spec1, spec2, ...)
    m = re.match(r"^subplot\((.+)\)$", full_line.strip(), re.DOTALL)
    if not m:
        print("Usage: subplot(rows, cols, plot(expr), plot_implicit(expr), ...)")
        return

    inner = m.group(1)
    # Split by top-level commas (not inside parentheses)
    parts: list[str] = []
    depth = 0
    current = ""
    for ch in inner:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current.strip())

    if len(parts) < 3:
        print("Usage: subplot(rows, cols, plot(expr), ...)")
        return

    try:
        rows = int(parts[0])
        cols = int(parts[1])
    except ValueError:
        print("  Error: rows and cols must be integers")
        return

    subplot_specs: list[dict] = []
    for spec_str in parts[2:]:
        spec_str = spec_str.strip()
        # Determine type
        if spec_str.startswith("plot(") and spec_str.endswith(")"):
            inner_arg = spec_str[5:-1]
            # Check for filename at end
            fname_parts = inner_arg.rsplit(",", 1)
            if len(fname_parts) == 2 and fname_parts[1].strip().endswith(".png"):
                expr = fname_parts[0].strip()
            else:
                expr = inner_arg.strip()
            subplot_specs.append({"type": "plot", "args": {"expression": expr}})

        elif spec_str.startswith("plot_parametric(") and spec_str.endswith(")"):
            inner_arg = spec_str[16:-1]
            pparts = inner_arg.split(",")
            if len(pparts) >= 2:
                subplot_specs.append({
                    "type": "parametric",
                    "args": {
                        "x_expr": pparts[0].strip(),
                        "y_expr": pparts[1].strip(),
                    },
                })

        elif spec_str.startswith("plot_implicit(") and spec_str.endswith(")"):
            inner_arg = spec_str[14:-1]
            fname_parts = inner_arg.rsplit(",", 1)
            if len(fname_parts) == 2 and fname_parts[1].strip().endswith(".png"):
                expr = fname_parts[0].strip()
            else:
                expr = inner_arg.strip()
            subplot_specs.append(
                {"type": "implicit", "args": {"expression": expr}}
            )

        else:
            print(f"  Warning: unrecognized subplot spec: {spec_str}")

    if not subplot_specs:
        print("  Error: no valid subplot specifications")
        return

    try:
        plotter = Plotter()
        result = plotter.plot_subplot(subplot_specs, rows=rows, cols=cols)
        if result:
            print(f"  Saved: {result}")
        else:
            print("  Plot window closed.")
    except Exception as e:
        print(f"  Subplot error: {e}")


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------


def _evaluate_expression(
    expr: str,
    calc: Calculator,
    po: PrintOptions,
    eo: EvaluationOptions,
    terse: bool = False,
) -> str:
    """Evaluate a single expression and return the formatted result."""
    result_str = calc.calculate_and_print(expr, eo=eo, po=po)
    if terse:
        return result_str
    return result_str


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------


def interactive_mode(
    calc: Calculator,
    po: PrintOptions,
    eo: EvaluationOptions,
) -> None:
    """Run the interactive REPL."""
    global _COMPLETER_WORDS

    _COMPLETER_WORDS = _make_completer(calc)
    _setup_readline()
    _install_completer(_COMPLETER_WORDS, calc)

    print(_bold(f"PyQalculate {VERSION}"))
    print("Type 'help' for help, 'quit' to exit.\n")

    last_result: MathStructure | None = None

    # Create / locate the 'ans' variable
    existing = calc.get_variable("ans")
    if existing is not None and isinstance(existing, KnownVariable):
        ans_var: KnownVariable = existing
    else:
        ans_var = KnownVariable("User", "ans", MathStructure(0), "Last result")
        calc.add_variable(ans_var)

    while True:
        try:
            line = input(_cyan("> ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        # ---- Meta-commands ------------------------------------------------
        lower = line.lower()

        if lower in ("quit", "exit", "q"):
            break

        if lower == "help":
            print(HELP_TEXT.format(version=VERSION))
            continue

        parts = line.split()
        cmd = parts[0].lower()
        cmd_args = parts[1:]

        if cmd == "help":
            if cmd_args:
                # Help for specific function
                func_name = cmd_args[0].lower()
                msg = _handle_help_function(func_name, calc)
                if msg:
                    print(msg)
            else:
                print(HELP_TEXT.format(version=VERSION))
            continue

        if cmd == "functions":
            print(_list_functions_by_category(calc))
            continue

        if cmd == "constants":
            print(_list_constants(calc))
            continue

        if cmd == "set":
            msg = _handle_set_command(cmd_args, po, eo, calc)
            if msg:
                print(msg)
            continue

        if cmd == "base":
            msg = _handle_base_command(cmd_args, po)
            if msg:
                print(msg)
            continue

        if cmd == "save":
            msg = _handle_save_command(cmd_args, calc, last_result)
            if msg:
                print(msg)
            continue

        if cmd == "delete":
            msg = _handle_delete_command(cmd_args, calc)
            if msg:
                print(msg)
            continue

        if cmd == "assume":
            msg = _handle_assume_command(cmd_args, calc)
            if msg:
                print(msg)
            continue

        if cmd == "mode":
            msg = _handle_mode_command(cmd_args, po, eo)
            if msg:
                print(msg)
            continue

        # ---- Plot commands ------------------------------------------------
        if cmd == "plot":
            _handle_plot_command(cmd_args, line)
            continue

        if cmd == "plot3d":
            _handle_plot3d_command(cmd_args)
            continue

        if cmd == "plot_implicit":
            _handle_plot_implicit_command(cmd_args)
            continue

        if cmd == "subplot":
            _handle_subplot_command(line)
            continue

        if cmd == "factorize" and last_result is not None:
            try:
                from pyqalculate.types import StructuringMode
                eo_local = EvaluationOptions(
                    approximation=eo.approximation,
                    structuring=StructuringMode.FACTORIZE,
                    parse_options=eo.parse_options,
                )
                evaluated = last_result.evaluate(eo_local)
                print(evaluated.print(po))
                last_result = evaluated
                ans_var.set(last_result)
            except Exception as e:
                print(f"Error: {e}")
            continue

        if cmd == "simplify" and last_result is not None:
            try:
                evaluated = last_result.evaluate(eo)
                print(evaluated.print(po))
                last_result = evaluated
                ans_var.set(last_result)
            except Exception as e:
                print(f"Error: {e}")
            continue

        # ---- Expression evaluation ----------------------------------------
        try:
            result = calc.calculate(line, eo=eo)
            result_str = result.print(po)
            print(_green(result_str))
            last_result = result
            # Update ans variable
            ans_var.set(last_result)
        except Exception as e:
            print(f"Error: {e}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for the pyqalc CLI."""
    global _ENABLE_COLOR

    parser = build_parser()
    args = parser.parse_args(argv)

    # Colour
    if args.no_color:
        _ENABLE_COLOR = False

    # Build calculator
    calc = Calculator()
    calc.load_definitions()

    # Load global definitions (units, currencies from JSON)
    try:
        calc.load_global_definitions()
    except Exception:
        pass  # non-fatal

    # Exchange rates
    if args.exrates:
        try:
            calc.load_exchange_rates()
        except Exception:
            print("Warning: could not update exchange rates", file=sys.stderr)

    # Build print/eval options
    po = PrintOptions()
    eo = EvaluationOptions()

    if args.base is not None:
        po.base = args.base

    # Apply --set option
    if args.set is not None:
        set_parts = args.set.split(None, 1)
        msg = _handle_set_command(set_parts, po, eo, calc)
        if msg and "Error" in msg:
            print(msg, file=sys.stderr)
            sys.exit(1)

    # ---- Single expression mode -------------------------------------------
    if args.expression:
        expr = " ".join(args.expression)
        try:
            result_str = _evaluate_expression(expr, calc, po, eo)
            if args.terse:
                print(result_str)
            else:
                print(f"{expr} = {result_str}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # ---- Interactive mode -------------------------------------------------
    interactive_mode(calc, po, eo)


if __name__ == "__main__":
    main()

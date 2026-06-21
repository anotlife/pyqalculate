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
    ])
    return words


def _install_completer(words: list[str]) -> None:
    """Install a readline tab-completer using *words*."""
    try:
        import readline  # noqa: F811

        def completer(text: str, state: int) -> str | None:
            options = [w for w in words if w.startswith(text.lower())]
            if state < len(options):
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
  help                     Show this help message
  quit / exit              Exit the program
"""


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
            return "approximation = APPROROXIMATE"
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
    _install_completer(_COMPLETER_WORDS)

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

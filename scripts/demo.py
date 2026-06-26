"""PyQalculate Demo - Calculator API-based command runner.

Scans demo/*.txt files, lets the user select one, then executes each
command via the Calculator API (for stateful settings).  Output goes
to demo/{name}/{name}_output.txt and plots to demo/{name}/.

Meta-commands (set, help, mode, base) are handled programmatically via
the CLI's handler functions.  Math expressions use calculate_and_print().
Plot commands use the Plotter API and save to file (no interactive windows).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import TextIO

from pyqalculate import Calculator
from pyqalculate.types import (
    AngleUnit,
    ApproximationMode,
    EvaluationOptions,
    PrintOptions,
)

# Import CLI meta-command handlers
from pyqalc.cli import (
    _handle_set_command,
    _handle_mode_command,
    _handle_base_command,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent
_DEMO_DIR = _PROJECT_DIR / "demo"


# ---------------------------------------------------------------------------
# Demo file scanning & selection
# ---------------------------------------------------------------------------


def scan_demo_files() -> list[tuple[str, Path]]:
    """Scan demo/*.txt and return sorted list of (stem, path) tuples."""
    if not _DEMO_DIR.is_dir():
        print(f"Error: demo directory not found: {_DEMO_DIR}")
        sys.exit(1)

    files = sorted(_DEMO_DIR.glob("*.txt"), key=lambda p: p.name)
    if not files:
        print(f"Error: no .txt files found in {_DEMO_DIR}")
        sys.exit(1)

    return [(f.stem, f) for f in files]


def show_selection_menu(files: list[tuple[str, Path]]) -> int:
    """Display numbered list and return the selected index (0-based)."""
    print("Demo files:")
    for i, (name, _) in enumerate(files, start=1):
        print(f"  [{i}] {name}.txt")
    print()

    while True:
        try:
            raw = input(f"Select demo (1-{len(files)}): ").strip()
            choice = int(raw)
            if 1 <= choice <= len(files):
                return choice - 1
            print(f"  Please enter a number between 1 and {len(files)}.")
        except ValueError:
            print("  Invalid input. Please enter a number.")
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            sys.exit(0)


# ---------------------------------------------------------------------------
# Meta-command detection
# ---------------------------------------------------------------------------

META_COMMANDS = frozenset({"set", "help", "mode", "base"})


def _is_meta_command(line: str) -> bool:
    """Check if line starts with a meta-command keyword."""
    parts = line.split()
    return bool(parts) and parts[0].lower() in META_COMMANDS


# ---------------------------------------------------------------------------
# Plot command parsing
# ---------------------------------------------------------------------------

# plot(expr, filename.png)
_RE_PLOT = re.compile(r"^plot\((.+),\s*(\S+\.png)\)$")

# plot_parametric(x_expr, y_expr, filename.png)
_RE_PARAMETRIC = re.compile(
    r"^plot_parametric\((.+?),\s*(.+?),\s*(\S+\.png)\)$"
)

# plot_implicit(expr, filename.png)
_RE_IMPLICIT = re.compile(r"^plot_implicit\((.+?),\s*(\S+\.png)\)$")


def _run_plot(expr: str, filename: str, plot_dir: Path, out: TextIO) -> None:
    """Plot a standard y=f(x) expression."""
    from pyqalculate.plot import Plotter

    path = str(plot_dir / filename)
    plotter = Plotter()
    result = plotter.plot(expr, filename=path)
    size = os.path.getsize(result) if result and os.path.exists(result) else 0
    out.write(f"  -> saved {filename} ({size} bytes)\n")
    print(f"  [PLOT] {filename} ({size} bytes)")


def _run_parametric(
    x_expr: str, y_expr: str, filename: str, plot_dir: Path, out: TextIO
) -> None:
    """Plot a parametric curve x(t), y(t)."""
    from pyqalculate.plot import Plotter

    path = str(plot_dir / filename)
    plotter = Plotter()
    result = plotter.plot_parametric(x_expr, y_expr, filename=path)
    size = os.path.getsize(result) if result and os.path.exists(result) else 0
    out.write(f"  -> saved {filename} ({size} bytes)\n")
    print(f"  [PARAMETRIC] {filename} ({size} bytes)")


def _run_implicit(expr: str, filename: str, plot_dir: Path, out: TextIO) -> None:
    """Plot an implicit equation f(x,y) = 0."""
    from pyqalculate.plot import Plotter

    path = str(plot_dir / filename)
    plotter = Plotter()
    result = plotter.plot_implicit(expr, filename=path)
    size = os.path.getsize(result) if result and os.path.exists(result) else 0
    out.write(f"  -> saved {filename} ({size} bytes)\n")
    print(f"  [IMPLICIT] {filename} ({size} bytes)")


# ---------------------------------------------------------------------------
# Meta-command handling
# ---------------------------------------------------------------------------


def _handle_help(out: TextIO) -> None:
    """Print demo help text."""
    lines = [
        "  PyQalculate Demo Help:",
        "  - Type expressions to evaluate (e.g., 2+2, sin(pi/2))",
        "  - Use 'set precision N' to set decimal precision",
        "  - Use 'set base N' to set number base (2-36)",
        "  - Use 'set angle degree|radian' to set angle unit",
        "  - Use 'set approx exact|approximate|try_exact' to set mode",
        "  - Use 'mode' to show current settings",
    ]
    for line in lines:
        out.write(f"{line}\n")
        print(line)


def _run_meta_command(
    line: str,
    calc: Calculator,
    po: PrintOptions,
    eo: EvaluationOptions,
    out: TextIO,
) -> None:
    """Handle a meta-command programmatically."""
    parts = line.split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "help":
        _handle_help(out)
        return

    if cmd == "set":
        # Intercept 'set angle' since CLI handler doesn't support it
        if len(args) >= 2 and args[0].lower() == "angle":
            angle_str = args[1].lower()
            if angle_str == "radian":
                eo.parse_options.angle_unit = AngleUnit.RADIANS
            elif angle_str == "degree":
                eo.parse_options.angle_unit = AngleUnit.DEGREES
            elif angle_str == "gradian":
                eo.parse_options.angle_unit = AngleUnit.GRADIANS
            else:
                eo.parse_options.angle_unit = AngleUnit.NONE
            msg = f"  angle unit = {angle_str}"
            out.write(f"{msg}\n")
            print(msg)
            return

        # Intercept 'set precision' to also set max_decimals for output
        if len(args) >= 2 and args[0].lower() == "precision":
            try:
                n = int(args[1])
                calc.set_precision(n)
                po.max_decimals = n
                msg = f"  precision = {n}"
                out.write(f"{msg}\n")
                print(msg)
            except ValueError:
                msg = "  Error: precision must be an integer"
                out.write(f"{msg}\n")
                print(msg)
            return

        # Delegate other set commands to CLI handler
        msg = _handle_set_command(args, po, eo, calc)
        if msg:
            out.write(f"  {msg}\n")
            print(f"  {msg}")
        return

    if cmd == "mode":
        msg = _handle_mode_command(args, po, eo)
        if msg:
            out.write(f"  {msg}\n")
            print(f"  {msg}")
        return

    if cmd == "base":
        msg = _handle_base_command(args, po)
        if msg:
            out.write(f"  {msg}\n")
            print(f"  {msg}")
        return


# ---------------------------------------------------------------------------
# Math expression evaluation
# ---------------------------------------------------------------------------


def _run_expression(
    expr: str,
    calc: Calculator,
    po: PrintOptions,
    eo: EvaluationOptions,
    out: TextIO,
) -> None:
    """Evaluate a math expression via the Calculator API."""
    try:
        result = calc.calculate_and_print(expr, eo=eo, po=po)
        if result:
            out.write(f"  {result}\n")
            print(f"  {result}")
    except Exception as e:
        out.write(f"  [ERROR] {e}\n")
        print(f"  [ERROR] {e}")


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------


def run_demo(file_path: Path) -> None:
    """Execute all commands in the selected demo file."""
    name = file_path.stem
    output_dir = _DEMO_DIR / name
    output_dir.mkdir(parents=True, exist_ok=True)

    results_file = output_dir / f"{name}_output.txt"

    lines = file_path.read_text(encoding="utf-8").splitlines()

    # Initialize Calculator with definitions
    calc = Calculator()
    calc.load_definitions()
    try:
        calc.load_global_definitions()
    except Exception:
        pass  # non-fatal

    # Shared print/eval options (stateful across commands)
    po = PrintOptions()
    eo = EvaluationOptions()

    total = 0
    plots = 0
    errors = 0

    print(f"\nRunning demo: {name}.txt")
    print(f"Output: {results_file}")
    print("=" * 60)

    with open(results_file, "w", encoding="utf-8") as out:
        out.write(f"PyQalculate Demo: {name}.txt\n")
        out.write("=" * 60 + "\n\n")

        for raw_line in lines:
            line = raw_line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                # Echo section headers
                if line.startswith("# =="):
                    out.write(f"\n{line}\n")
                    print(f"\n{line}")
                elif line.startswith("#"):
                    out.write(f"{line}\n")
                    print(line)
                continue

            total += 1
            out.write(f"\n>> {line}\n")
            print(f"\n>> {line}")

            # --- Meta-commands (set, help, mode, base) ---
            if _is_meta_command(line):
                try:
                    _run_meta_command(line, calc, po, eo, out)
                except Exception as e:
                    out.write(f"  [META ERROR] {e}\n")
                    print(f"  [META ERROR] {e}")
                    errors += 1
                continue

            # --- plot(expr, file.png) ---
            m = _RE_PLOT.match(line)
            if m:
                try:
                    _run_plot(m.group(1), m.group(2), output_dir, out)
                    plots += 1
                except Exception as e:
                    out.write(f"  [PLOT ERROR] {e}\n")
                    print(f"  [PLOT ERROR] {e}")
                    errors += 1
                continue

            # --- plot_parametric(x_expr, y_expr, file.png) ---
            m = _RE_PARAMETRIC.match(line)
            if m:
                try:
                    _run_parametric(
                        m.group(1), m.group(2), m.group(3), output_dir, out
                    )
                    plots += 1
                except Exception as e:
                    out.write(f"  [PARAMETRIC ERROR] {e}\n")
                    print(f"  [PARAMETRIC ERROR] {e}")
                    errors += 1
                continue

            # --- plot_implicit(expr, file.png) ---
            m = _RE_IMPLICIT.match(line)
            if m:
                try:
                    _run_implicit(m.group(1), m.group(2), output_dir, out)
                    plots += 1
                except Exception as e:
                    out.write(f"  [IMPLICIT ERROR] {e}\n")
                    print(f"  [IMPLICIT ERROR] {e}")
                    errors += 1
                continue

            # --- Regular math expression via Calculator API ---
            _run_expression(line, calc, po, eo, out)

        out.write(f"\n{'=' * 60}\n")
        out.write(f"Total commands: {total}\n")
        out.write(f"Plots generated: {plots}\n")
        out.write(f"Errors: {errors}\n")

    print(f"\n{'=' * 60}")
    print(f"Done! {total} commands, {plots} plots, {errors} errors")
    print(f"Results: {results_file}")
    if plots:
        print(f"Plots:   {output_dir}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    files = scan_demo_files()
    idx = show_selection_menu(files)
    name, path = files[idx]
    run_demo(path)


if __name__ == "__main__":
    main()

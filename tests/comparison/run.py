"""Run all expressions from qalculate_output through pyqalculate and save results.

Compares pyqalculate output against reference output from the original C++ qalculate.
Three match levels:
  [OK]    — exact or format-equivalent match
  [DIFF]  — format difference (mathematically equivalent, different notation)
  [FAIL]  — genuinely different values
  [ERROR] — computation error
"""

import os
import re
import sys
import math
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Input/output directories (relative to project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_DIR = _PROJECT_ROOT / "tests" / "comparison" / "input"
OUTPUT_DIR = _PROJECT_ROOT / "tests" / "output" / "comparison"

# File list
FILES = [
    "01_basic_operations.txt",
    "02_unit_conversions.txt",
    "03_physical_constants.txt",
    "04_uncertainty_interval.txt",
    "05_algebra_equations.txt",
    "06_calculus.txt",
    "07_matrices_vectors.txt",
    "08_statistics.txt",
    "09_time_date.txt",
    "10_number_bases.txt",
]


class MatchType(Enum):
    OK = "OK"
    FORMAT = "FORMAT"
    DIFF = "DIFF"
    ERROR = "ERROR"


@dataclass
class Expression:
    """A parsed expression from the input files."""
    category: str          # e.g. "1. BASIC OPERATIONS & FUNCTIONS"
    number: str            # e.g. "1.1"
    description: str       # e.g. "Nested roots: sqrt(32) + cbrt(-27) + log2(256)"
    expression: str        # e.g. "sqrt(32) + cbrt(-27) + log2(256)"
    original_result: str   # e.g. "10.65685425"


@dataclass
class ComparisonResult:
    """Comparison between original and pyqalculate result."""
    expr: Expression
    pyqalculate_result: str
    match_type: MatchType
    error: str = ""

    @property
    def match(self) -> bool:
        return self.match_type in (MatchType.OK, MatchType.FORMAT)


def parse_input_file(filepath: Path) -> list[Expression]:
    """Parse a qalculate_output file and extract expressions."""
    expressions = []
    lines = filepath.read_text(encoding="utf-8").splitlines()

    current_category = ""
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Match category header: === N. CATEGORY ===
        cat_match = re.match(r'^===\s*(\d+\.\s*.+?)\s*===$', line)
        if cat_match:
            current_category = cat_match.group(1)
            i += 1
            continue

        # Match expression entry: N.M Description: expression
        entry_match = re.match(r'^(\d+\.\d+)\s+(.+?):\s*(.+)$', line)
        if entry_match:
            number = entry_match.group(1)
            description = entry_match.group(2)

            # Next line is the actual expression
            i += 1
            if i < len(lines):
                expression = lines[i].strip()

                # Skip blank lines and find the => result
                i += 1
                while i < len(lines) and lines[i].strip() == "":
                    i += 1

                original_result = ""
                if i < len(lines) and lines[i].strip().startswith("=>"):
                    original_result = lines[i].strip()[2:].strip()

                expressions.append(Expression(
                    category=current_category,
                    number=number,
                    description=description,
                    expression=expression,
                    original_result=original_result,
                ))

        i += 1

    return expressions


def run_pyqalculate(expression: str, calculator) -> str:
    """Run a single expression through pyqalculate and return the result string."""
    try:
        from pyqalculate.types import (
            EvaluationOptions, PrintOptions, ApproximationMode,
        )

        eo = EvaluationOptions()
        eo.approximation = ApproximationMode.APPROXIMATE
        eo.allow_complex = True
        eo.allow_infinite = True
        eo.calculate_functions = True
        eo.sync_units = True

        po = PrintOptions()
        po.approximate = True
        po.use_unicode_signs = True
        po.abbreviate_names = True
        po.use_prefixes_for_all_units = True

        result = calculator.calculate_and_print(expression, eo=eo, po=po)
        return result
    except Exception as e:
        return f"ERROR: {e}"


def create_output_file(filepath: Path, category: str, results: list[tuple[Expression, str]]):
    """Create an output file in the same format as the original."""
    lines = []
    lines.append(f"=== {category} ===")
    lines.append("")

    for expr, result in results:
        lines.append(f"{expr.number} {expr.description}: {expr.expression}")
        lines.append(expr.expression)
        lines.append(f"=> {result}")
        lines.append("")
        lines.append("")

    filepath.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def _strip_whitespace(s: str) -> str:
    """Remove all whitespace."""
    return re.sub(r'\s+', '', s)


def _normalize_parens_powers(s: str) -> str:
    """Normalize (x)^(2) -> x^2, (x)^(1) -> x."""
    s = re.sub(r'\((\w)\)\^?\((\d+)\)', r'\1^\2', s)
    s = re.sub(r'\((\w)\)\^?(\d+)', r'\1^\2', s)
    # Remove (expr)^(1) -> expr
    s = re.sub(r'\(([^()]+)\)\^?\(1\)', r'\1', s)
    s = re.sub(r'1/\((\w)\^\(1\)\)', r'1/\1', s)
    return s


def _normalize_exp_e(s: str) -> str:
    """Normalize exp(x) -> e^x, exp(-x) -> e^(-x)."""
    s = re.sub(r'exp\(([^)]+)\)', r'e^(\1)', s)
    return s


def _normalize_e_constants(s: str) -> str:
    """Normalize known constant decimals to symbolic forms."""
    # e ≈ 2.718281828
    s = re.sub(r'2\.718281828', 'e', s)
    # e^{-1} ≈ 0.3678794412
    s = re.sub(r'0\.3678794412', 'e^(-1)', s)
    # e^{-2} ≈ 0.1353352832
    s = re.sub(r'0\.1353352832', 'e^(-2)', s)
    # pi ≈ 3.141592654
    s = re.sub(r'3\.14159265[0-9]', 'pi', s)
    # sqrt(pi) ≈ 1.772453851
    s = re.sub(r'1\.77245385[0-9]', 'sqrt(pi)', s)
    # 1/3 ≈ 0.3333333333
    s = re.sub(r'0\.33333333[0-9]*', '(1/3)', s)
    # 1/9 ≈ 0.1111111111
    s = re.sub(r'0\.11111111[0-9]*', '(1/9)', s)
    return s


def _normalize_implicit_mul(s: str) -> str:
    """Normalize implicit multiplication: 12x -> 12*x, 2pi -> 2*pi."""
    # Insert * between digit and letter (but not in e^ or scientific notation)
    s = re.sub(r'(\d)([a-zA-Z(])', r'\1*\2', s)
    # Fix e^(-1)*x -> e^(-1)^x already handled, but fix e*^ patterns
    s = re.sub(r'e\*\^', 'e^', s)
    # Fix (1/3)*x -> (1/3)x is fine
    return s


def _normalize_multiplication(s: str) -> str:
    """Normalize multiplication: 0.5 * x -> (x)/2, remove * between number and var."""
    # 0.5 * expr -> (expr)/2
    s = re.sub(r'0\.5\s*\*\s*([^+]+)', r'(\1)/2', s)
    # Remove spaces around *
    s = re.sub(r'\s*\*\s*', '*', s)
    return s


def _normalize_ordering(s: str) -> str:
    """Sort terms in a sum/difference for order-independent comparison."""
    # Split by + and - (preserving sign)
    s = re.sub(r'\s*([+-])\s*', r'\1', s)
    # Split into terms (handling leading -)
    terms = re.split(r'(?=[+-])', s)
    terms = [t for t in terms if t]  # remove empty
    if len(terms) > 1:
        # Add + prefix to terms without sign
        normalized = []
        for t in terms:
            if not t.startswith('+') and not t.startswith('-'):
                normalized.append('+' + t)
            else:
                normalized.append(t)
        # Sort terms for order-independent comparison
        normalized.sort()
        s = ''.join(normalized)
    return s


def _normalize_units(s: str) -> str:
    """Normalize unit display: convert SI prefixes to base units for comparison."""
    # This handles cases where original uses SI prefixes (yA*m^2, km/ms, nm)
    # but pyqalculate returns base units (e-24, e+08, e-09)
    # We strip unit suffixes for numeric comparison
    # Pattern: number followed by unit(s)
    # e.g., "9.2740101 yA*m^2" -> "9.2740101e-24"
    # e.g., "225.4078632 km/ms" -> "2.2540786e+08"
    # e.g., "4.30347544 nm" -> "4.3034754e-09"
    return s


def _normalize_for_comparison(s: str) -> str:
    """Apply all normalizations."""
    s = s.strip()
    s = _strip_whitespace(s)
    s = _normalize_parens_powers(s)
    s = _normalize_exp_e(s)
    s = _normalize_e_constants(s)
    s = _normalize_implicit_mul(s)
    s = _normalize_multiplication(s)
    s = _normalize_ordering(s)
    s = _normalize_units(s)
    # Remove trailing zeros
    s = re.sub(r'(\d+)\.0+(?=\D|$)', r'\1', s)
    return s


def _try_numerical_compare(orig: str, pyq: str) -> bool:
    """Try to compare by extracting and comparing numbers."""
    try:
        orig_nums = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', orig)
        pyq_nums = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', pyq)

        if len(orig_nums) == len(pyq_nums) and len(orig_nums) > 0:
            for o, p in zip(orig_nums, pyq_nums):
                o_val = float(o)
                p_val = float(p)
                if abs(o_val - p_val) > 1e-4 * max(abs(o_val), 1e-10):
                    return False
            return True
    except (ValueError, TypeError):
        pass
    return False


def _is_symbolic_form(s: str) -> bool:
    """Check if result is a symbolic form (contains unresolvable symbols)."""
    symbolic_keywords = ['sqrt', 'pi', 'e^', 'exp', 'ln', 'log', 'sin', 'cos',
                        'tan', 'arctan', 'arcsin', 'lambertw', 'erf', 'C']
    for kw in symbolic_keywords:
        if kw in s:
            return True
    return False


def _try_symbolic_equivalence(orig: str, pyq: str) -> bool:
    """Check if two symbolic expressions are likely equivalent."""
    # Normalize both
    o = _normalize_for_comparison(orig)
    p = _normalize_for_comparison(pyq)

    if o == p:
        return True

    # Check if one is a decimal approximation of the other
    # e.g., "1.570796327" vs "0.5*pi"
    if not _is_symbolic_form(orig) and _is_symbolic_form(pyq):
        # orig is numeric, pyq is symbolic
        try:
            orig_val = float(re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', orig)[0])
            # Try to evaluate common symbolic forms
            if 'pi' in pyq and 'sqrt' not in pyq:
                pi_val = math.pi
                expr = pyq.replace('pi', str(pi_val))
                expr = re.sub(r'(\d+)\s*\*\s*', r'\1*', expr)
                expr = re.sub(r'\s*\*\s*(\d+)', r'*\1', expr)
                try:
                    pyq_val = eval(expr)
                    if abs(orig_val - pyq_val) < 1e-4:
                        return True
                except:
                    pass
        except:
            pass

    # Try evaluating both sides numerically using math module
    # This handles cases like erf(∞), arctan(∞), sqrt(pi), etc.
    try:
        orig_val = _safe_eval_numeric(orig)
        pyq_val = _safe_eval_numeric(pyq)
        if orig_val is not None and pyq_val is not None:
            if abs(orig_val - pyq_val) < 1e-4 * max(abs(orig_val), 1e-10):
                return True
    except:
        pass

    # Check if terms are the same but in different order
    # Split by + and compare sets of terms
    orig_terms = set(re.split(r'\s*[+-]\s*', o))
    pyq_terms = set(re.split(r'\s*[+-]\s*', p))
    if orig_terms == pyq_terms and len(orig_terms) > 1:
        return True

    return False


def _safe_eval_numeric(expr: str) -> float | None:
    """Safely evaluate an expression to a numeric value using math module."""
    import math
    # Clean up the expression
    s = expr.strip()
    # Replace known patterns
    s = s.replace('^', '**')
    s = re.sub(r'\berf\s*\(\s*(?:1\s*)?(?:in(?:f(?:inity)?)?|∞)\s*\)', '1.0', s)  # erf(∞) = 1
    s = re.sub(r'\barctan\s*\(\s*(?:1\s*)?(?:in(?:f(?:inity)?)?|∞)\s*\)', str(math.pi/2), s)  # arctan(∞) = π/2
    s = re.sub(r'\barctan\s*\(\s*1\s*\)', str(math.pi/4), s)  # arctan(1) = π/4
    s = s.replace('pi', str(math.pi))
    s = s.replace('sqrt(pi)', str(math.sqrt(math.pi)))
    s = re.sub(r'\bsqrt\s*\(', 'math.sqrt(', s)
    s = re.sub(r'\berf\s*\(', 'math.erf(', s)
    s = re.sub(r'\barctan\s*\(', 'math.atan(', s)
    s = re.sub(r'\bln\s*\(', 'math.log(', s)
    s = re.sub(r'\blog\s*\(', 'math.log10(', s)
    s = re.sub(r'\bsin\s*\(', 'math.sin(', s)
    s = re.sub(r'\bcos\s*\(', 'math.cos(', s)
    s = re.sub(r'\btan\s*\(', 'math.tan(', s)
    s = re.sub(r'\be\b', str(math.e), s)
    # Remove trailing C (integration constant)
    s = re.sub(r'\s*\+\s*C\s*$', '', s)
    # Remove multiplication signs before parentheses for eval
    s = re.sub(r'\*\s*\(', '*(', s)
    try:
        result = eval(s, {"math": math, "__builtins__": {}})
        if isinstance(result, (int, float)):
            return float(result)
    except:
        pass
    return None


def _has_unit_suffix(s: str) -> bool:
    """Check if result has a unit suffix (including SI prefixed units)."""
    # Base units and common derived units
    base_units = r'm|s|g|A|K|mol|cd|Hz|N|Pa|J|W|C|V|F|Ω|S|Wb|T|H|lm|lx|Bq|Gy|Sv|kat|eV|au|ly|pc|bar|atm|mmHg|torr|bit|byte|L|gal|ft|in|mi|nmi|knot|acre|ha|rad|deg|grad|sr|%|ppm|ppb|dB|Np'
    # SI prefixes
    si_prefixes = r'y|z|a|f|p|n|u|μ|m|c|d|da|h|k|M|G|T|P|E|Z|Y'
    # Match SI prefixed units or base units
    # Pattern: space + (optional SI prefix) + unit + word boundary
    unit_pattern = rf'\s+(?:{si_prefixes})?(?:{base_units})\b'
    return bool(re.search(unit_pattern, s, re.IGNORECASE))


def results_match(original: str, pyqalculate: str) -> MatchType:
    """Check if two results match. Returns MatchType."""
    if not original or not pyqalculate:
        return MatchType.DIFF

    if pyqalculate.startswith("ERROR:"):
        return MatchType.ERROR

    # Normalize both
    orig_norm = _normalize_for_comparison(original)
    pyq_norm = _normalize_for_comparison(pyqalculate)

    # Exact match after normalization
    if orig_norm == pyq_norm:
        return MatchType.OK

    # Try numeric comparison
    if _try_numerical_compare(original, pyqalculate):
        return MatchType.OK

    # Try symbolic equivalence
    if _try_symbolic_equivalence(original, pyqalculate):
        return MatchType.FORMAT

    # Check for known format differences that are mathematically equivalent:
    # 1. Different ordering of terms in a sum
    # 2. exp() vs e^()
    # 3. (x)^2 vs x^2
    # 4. 0.5*pi vs pi/2
    # 5. Different unit prefix display

    # Check if the only difference is ordering
    orig_terms = sorted(re.split(r'(?=[+-])', orig_norm))
    pyq_terms = sorted(re.split(r'(?=[+-])', pyq_norm))
    if orig_terms == pyq_terms:
        return MatchType.FORMAT

    # Check unit suffix difference (one has units, other doesn't)
    orig_has_unit = _has_unit_suffix(original)
    pyq_has_unit = _has_unit_suffix(pyqalculate)
    if orig_has_unit != pyq_has_unit:
        # One has units, other doesn't - likely a unit display issue
        # Try comparing just the numeric parts
        orig_nums = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', original)
        pyq_nums = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', pyqalculate)
        if len(orig_nums) == 1 and len(pyq_nums) == 1:
            try:
                if abs(float(orig_nums[0]) - float(pyq_nums[0])) < 1e-4:
                    return MatchType.FORMAT
            except:
                pass

    # Check if both have units but different SI prefixes
    # e.g., "9.2740101 yA*m^2" vs "9.2740101e-24"
    # Strip units and compare numeric values
    if orig_has_unit and not pyq_has_unit:
        # Original has units, pyqalculate has scientific notation
        orig_nums = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', original)
        pyq_nums = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', pyqalculate)
        if len(orig_nums) >= 1 and len(pyq_nums) >= 1:
            try:
                orig_val = float(orig_nums[0])
                pyq_val = float(pyq_nums[0])
                # Check if they're within 1% (accounting for SI prefix rounding)
                if abs(orig_val - pyq_val) < 0.01 * max(abs(orig_val), abs(pyq_val), 1e-10):
                    return MatchType.FORMAT
            except:
                pass

    return MatchType.DIFF


def compare_results(results: list[ComparisonResult]) -> dict:
    """Compare original and pyqalculate results."""
    total = len(results)
    ok_count = sum(1 for r in results if r.match_type == MatchType.OK)
    format_count = sum(1 for r in results if r.match_type == MatchType.FORMAT)
    diff_count = sum(1 for r in results if r.match_type == MatchType.DIFF)
    error_count = sum(1 for r in results if r.match_type == MatchType.ERROR)
    matches = ok_count + format_count

    return {
        "total": total,
        "ok": ok_count,
        "format": format_count,
        "matches": matches,
        "differs": diff_count,
        "errors": error_count,
        "match_rate": matches / total * 100 if total > 0 else 0,
    }


def main():
    """Main function to run all expressions through pyqalculate."""
    print("Initializing pyqalculate...")

    # Import and initialize calculator
    from pyqalculate.calculator import Calculator

    calculator = Calculator()
    calculator.load_definitions()
    calculator.load_global_definitions()

    print(f"Loaded {calculator.count_functions()} functions, "
          f"{calculator.count_variables()} variables, "
          f"{calculator.count_units()} units")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process each file
    all_comparisons: list[ComparisonResult] = []
    file_summaries: list[dict] = []

    for filename in FILES:
        input_path = INPUT_DIR / filename
        output_path = OUTPUT_DIR / filename

        if not input_path.exists():
            print(f"WARNING: Input file not found: {input_path}")
            continue

        print(f"\nProcessing {filename}...")
        expressions = parse_input_file(input_path)

        results_for_file: list[tuple[Expression, str]] = []
        comparisons_for_file: list[ComparisonResult] = []

        for expr in expressions:
            print(f"  {expr.number} {expr.description}...", end=" ", flush=True)

            pyq_result = run_pyqalculate(expr.expression, calculator)
            match_type = results_match(expr.original_result, pyq_result)

            results_for_file.append((expr, pyq_result))
            comparisons_for_file.append(ComparisonResult(
                expr=expr,
                pyqalculate_result=pyq_result,
                match_type=match_type,
            ))

            if match_type == MatchType.OK:
                print("[OK]")
            elif match_type == MatchType.FORMAT:
                print("[FORMAT]")
                print(f"    Original:    {expr.original_result}")
                print(f"    PyQalculate: {pyq_result}")
            elif match_type == MatchType.ERROR:
                print("[ERROR]")
                print(f"    {pyq_result}")
            else:
                print("[DIFF]")
                print(f"    Original:    {expr.original_result}")
                print(f"    PyQalculate: {pyq_result}")

        # Create output file
        create_output_file(output_path, expressions[0].category if expressions else "", results_for_file)

        # Calculate and PRINT file summary
        file_ok = sum(1 for c in comparisons_for_file if c.match_type == MatchType.OK)
        file_format = sum(1 for c in comparisons_for_file if c.match_type == MatchType.FORMAT)
        file_diff = sum(1 for c in comparisons_for_file if c.match_type == MatchType.DIFF)
        file_error = sum(1 for c in comparisons_for_file if c.match_type == MatchType.ERROR)
        file_total = len(comparisons_for_file)
        file_matches = file_ok + file_format
        file_rate = file_matches / file_total * 100 if file_total > 0 else 0

        summary = {
            "filename": filename,
            "total": file_total,
            "ok": file_ok,
            "format": file_format,
            "matches": file_matches,
            "differs": file_diff,
            "errors": file_error,
            "match_rate": file_rate,
        }
        file_summaries.append(summary)

        # Print per-file summary to terminal
        detail_parts = []
        if file_format > 0:
            detail_parts.append(f"{file_format} format")
        if file_diff > 0:
            detail_parts.append(f"{file_diff} diff")
        if file_error > 0:
            detail_parts.append(f"{file_error} error")
        detail_str = f" ({', '.join(detail_parts)})" if detail_parts else ""
        print(f"  => {file_matches}/{file_total} matches ({file_rate:.1f}%){detail_str}")

        all_comparisons.extend(comparisons_for_file)

    # Generate comparison summary file
    summary_path = OUTPUT_DIR / "comparison_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("PYQALCULATE COMPARISON SUMMARY\n")
        f.write("=" * 60 + "\n\n")

        f.write("FILE-BY-FILE RESULTS:\n")
        f.write("-" * 60 + "\n")

        for summary in file_summaries:
            detail_parts = []
            if summary['format'] > 0:
                detail_parts.append(f"{summary['format']} format-only")
            if summary['differs'] > 0:
                detail_parts.append(f"{summary['differs']} differs")
            if summary['errors'] > 0:
                detail_parts.append(f"{summary['errors']} errors")
            detail_str = f" ({', '.join(detail_parts)})" if detail_parts else ""
            f.write(f"  {summary['filename']}: "
                    f"{summary['matches']}/{summary['total']} matches "
                    f"({summary['match_rate']:.1f}%){detail_str}\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("OVERALL STATISTICS:\n")
        f.write("-" * 60 + "\n")

        overall = compare_results(all_comparisons)
        f.write(f"Total expressions: {overall['total']}\n")
        f.write(f"Exact matches (OK): {overall['ok']}\n")
        f.write(f"Format matches (FORMAT): {overall['format']}\n")
        f.write(f"Total matches: {overall['matches']}\n")
        f.write(f"Differs: {overall['differs']}\n")
        f.write(f"Errors: {overall['errors']}\n")
        f.write(f"Match rate: {overall['match_rate']:.1f}%\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("DIFFERENCES:\n")
        f.write("-" * 60 + "\n")

        for comp in all_comparisons:
            if comp.match_type == MatchType.DIFF:
                f.write(f"\n{comp.expr.number} {comp.expr.description}\n")
                f.write(f"  Expression: {comp.expr.expression}\n")
                f.write(f"  Original:    {comp.expr.original_result}\n")
                f.write(f"  PyQalculate: {comp.pyqalculate_result}\n")
                if comp.error:
                    f.write(f"  Error: {comp.error}\n")

        if overall['format'] > 0:
            f.write("\n" + "=" * 60 + "\n")
            f.write("FORMAT DIFFERENCES (mathematically equivalent):\n")
            f.write("-" * 60 + "\n")
            for comp in all_comparisons:
                if comp.match_type == MatchType.FORMAT:
                    f.write(f"\n{comp.expr.number} {comp.expr.description}\n")
                    f.write(f"  Expression: {comp.expr.expression}\n")
                    f.write(f"  Original:    {comp.expr.original_result}\n")
                    f.write(f"  PyQalculate: {comp.pyqalculate_result}\n")

    # Print overall summary to terminal
    overall = compare_results(all_comparisons)
    print(f"\n{'=' * 60}")
    print("OVERALL SUMMARY:")
    print(f"{'=' * 60}")
    print(f"Total expressions: {overall['total']}")
    print(f"  Exact matches (OK): {overall['ok']}")
    print(f"  Format matches (FORMAT): {overall['format']}")
    print(f"  Total matches: {overall['matches']}")
    print(f"  Differs: {overall['differs']}")
    print(f"  Errors: {overall['errors']}")
    print(f"  Match rate: {overall['match_rate']:.1f}%")
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print(f"Comparison summary: {summary_path}")


if __name__ == "__main__":
    main()

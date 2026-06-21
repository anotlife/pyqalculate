# PyQalculate v2.1 — Development Plan

> **Project Goal**: Raise reference test pass rate from 89.9% (71/79) to 100% (79/79).
>
> **Scope**: 9 targeted fixes for 2 failed + 6 skipped tests, plus 1 weak-pass improvement.
>
> **This document is for execution by subsequent agents. Follow tasks in priority order.**

---

## 1. Project Overview

### 1.1 v2.1 Goal

v2.0 delivered a massive leap: from 29% (23/79) to 89.9% (71/79). Most feature domains are complete. The v2.1 milestone targets the remaining **8 tests** that still don't pass, plus hardening 1 weak pass. The end state: **79/79 tests passing, 0 failed, 0 skipped**.

Unlike v2.0's broad feature work, v2.1 is surgical. Every issue is a specific bug with a known root cause. No new feature domains to build. Just fixing edge cases, parser quirks, and missing data.

### 1.2 v2.0 Recap

| Metric | v1.0 | v2.0 | v2.1 Target |
|--------|------|------|-------------|
| Reference tests passing | 23/79 (29%) | 71/79 (89.9%) | 79/79 (100%) |
| Failed tests | 1 | 2 | 0 |
| Skipped tests | 55 | 6 | 0 |
| Unit tests | 869 | ~1,200+ | ~1,200+ (no regressions) |

**What v2.0 accomplished:**
- Calculus engine (diff, integrate, limit) via SymPy delegation
- Algebra equation solving (solve, multisolve, dsolve, factor, expand)
- Uncertainty/interval arithmetic with error propagation
- Advanced matrix operations (inverse, cross, dot, Hadamard, eigenvalues, trace)
- Statistics (quartile, normdist, correlation)
- Time/date functions (time arithmetic, now, days, timestamp, calendars)
- Number base extensions (float, arbitrary base, roman, bitwise, bin16)
- Physical constants with unit arithmetic
- 151+ built-in functions operational

### 1.3 What v2.1 Does Not Cover

- Performance optimization
- New built-in functions beyond reference test needs
- Web interface or API changes
- GUI enhancements
- Currency or real-time data integration

---

## 2. Current Status — Detailed Breakdown

### 2.1 Summary

| Metric | Count |
|--------|-------|
| Total reference tests | 79 |
| Passing | 71 (89.9%) |
| Failed | 2 |
| Skipped | 6 |
| Weak pass (needs improvement) | 1 |
| **v2.1 Target** | **79/79 (100%)** |

### 2.2 Per-File Breakdown

| File | Tests | Passed | Skipped | Failed | v2.1 Target |
|------|-------|--------|---------|--------|-------------|
| 01_basic_operations.txt | 9 | 8 | 1 | 0 | 9/9 |
| 02_unit_conversions.txt | 10 | 10 | 0 | 0 | 10/10 |
| 03_physical_constants.txt | 7 | 6 | 1 | 0 | 7/7 |
| 04_uncertainty_interval.txt | 5 | 5 | 0 | 0 | 5/5 |
| 05_algebra_equations.txt | 8 | 7 | 0 | 1 | 8/8 |
| 06_calculus.txt | 8 | 7 | 0 | 1 | 8/8 |
| 07_matrices_vectors.txt | 8 | 8 | 0 | 0 | 8/8 |
| 08_statistics.txt | 6 | 6 | 0 | 0 | 6/6 |
| 09_time_date.txt | 8 | 8 | 0 | 0 | 8/8 |
| 10_number_bases.txt | 10 | 6 | 4 | 0 | 10/10 |
| **Total** | **79** | **71** | **6** | **2** | **79/79** |

---

## 3. Remaining Issues — Root Cause Analysis

### 3.1 Failed Tests

#### FAIL-1: Test 5.3 — multisolve parser bug

**Expression**: `multisolve([x+y+z=6, 2*x-y+z=3, x+2*y-z=5]; [x, y, z])`

**Expected**: `[13/7, 17/7, 12/7]` (approximately `[1.857, 2.429, 1.714]`)

**Root Cause**: In `parser.py` line 856, the multisolve parser uses `limit_implicit_multiplication=True` when parsing bracket contents. This causes the tokenizer to split `2x` into separate tokens `2` and `x` instead of treating it as `2*x`. The resulting equations are malformed, and SymPy either errors or returns wrong results.

**File**: `parser.py:856`

**Fix**: Remove `limit_implicit_multiplication=True` from the multisolve bracket parsing path, or adjust space-separator logic so that `2x` inside brackets is still parsed as implicit multiplication.

**Verification**: `multisolve([x+y+z=6, 2*x-y+z=3, x+2*y-z=5]; [x, y, z])` → `[13/7, 17/7, 12/7]`

---

#### FAIL-2: Test 6.3 — Gaussian integral constant conversion

**Expression**: `integrate(e^(-x^2); -inf; inf)`

**Expected**: `sqrt(pi)`

**Root Cause**: In `math_structure.py`, the `_number_to_sympy()` function converts numbers to SymPy objects. When the expression `e^(-x^2)` is evaluated, the `e` constant gets converted to its float value `0.367879441171442` instead of the symbolic constant `sp.E`. SymPy then integrates `0.367879...^(-x^2)` which gives a numeric result involving `erf`, not the clean `sqrt(pi)`.

**File**: `math_structure.py`, `_number_to_sympy()` function

**Fix**: Add detection for floats close to known mathematical constants (e ≈ 2.71828..., pi ≈ 3.14159...) and return the symbolic constant instead of the float approximation. Use a relative tolerance check (e.g., `abs(val - math.e) / math.e < 1e-10`).

**Verification**: `integrate(e^(-x^2); -inf; inf)` → `sqrt(pi)`

---

### 3.2 Skipped Tests

#### SKIP-1: Test 1.1 — cbrt(-27)

**Expression**: `cbrt(-27)`

**Expected**: `-3`

**Root Cause**: `_SYMPY_FUNC_MAP` in `math_structure.py` line 525 maps `cbrt` to a custom `_cbrt` function. This custom function incorrectly handles negative inputs. SymPy's native `cbrt()` actually returns the correct real root `-3`, so the fix is to stop overriding it.

**File**: `math_structure.py:525`

**Fix**: Delete `"cbrt": _cbrt,` from `_SYMPY_FUNC_MAP`. Let SymPy's default handling produce the correct real cube root. Also remove the skip pattern from `test_qalculate_reference.py` line 61.

**Verification**: `cbrt(-27)` → `-3`

---

#### SKIP-2: Test 1.2 — sum()

**Expression**: `sum(sin(\i)^2+cos(\i)^2; 1; 20; \i)`

**Expected**: `20`

**Root Cause**: This test is skipped because the iteration variable `\i` was thought to be unsupported. However, the sum function already works with regular variable names (like `x`). The expression `sin(x)^2+cos(x)^2` simplifies to `1`, and `sum(1, 1, 20)` = `20`. The real question is whether the parser correctly handles `\i` as a variable name, or whether the test needs to use `x` instead.

**File**: `test_qalculate_reference.py` (skip pattern removal)

**Fix**: Verify that `sum(sin(x)^2+cos(x)^2, x, 1, 20)` returns `20`. If the `\i` syntax doesn't work but `x` does, update the test expression. If `\i` needs parser support, add it. Most likely, just removing the skip and testing with a standard variable works.

**Verification**: `sum(sin(x)^2+cos(x)^2, x, 1, 20)` → `20`

---

#### SKIP-3: Test 1.4 — `\` integer division

**Expression**: `137 \ 12`

**Expected**: `11` (floor division)

**Root Cause**: The tokenizer in `parser.py` lines 162-172 doesn't emit `TT.BACKSLASH` when it encounters a `\` character. Without the token, the expression can't be parsed as integer division. Additionally, the floor division handler at lines 667-676 uses `floor()` which may not be correct for negative numbers; `trunc()` (toward zero) is the standard behavior for `\` in qalculate.

**File**: `parser.py:162-172` (tokenizer), `parser.py:667-676` (division handler)

**Fix**:
1. In the tokenizer, when `\` is followed by a digit, space, or operator, emit `TT.BACKSLASH`.
2. In the division handler, use `trunc()` instead of `floor()` for both `//` and `\` operators.

**Verification**: `137 \ 12` → `11`

---

#### SKIP-4: Test 1.8 — (-27)^(1/3) complex root

**Expression**: `(-27)^(1/3)`

**Expected**: `1.5 + 2.598i` (principal complex cube root)

**Root Cause**: The `raise_()` method in `number.py` doesn't use the complex path when a negative number is raised to a fractional power with an odd denominator. It returns the real root `-3` instead of the principal complex root `1.5 + 2.598i`.

**File**: `number.py`, `raise_()` method

**Fix**: When `allow_complex=True` and the base is negative with a fractional exponent (odd denominator), use the complex number path: `(-27)^(1/3) = 27^(1/3) * e^(i*pi/3) = 3 * (cos(pi/3) + i*sin(pi/3)) = 1.5 + 2.598i`. Alternatively, in `MathStructure.evaluate()` for `POWER` nodes, force the float/complex path when `allow_complex=True`.

**Verification**: `(-27)^(1/3)` → `1.5 + 2.598i`

---

#### SKIP-5: Test 2.6 — Mixed unit conversion (ft)

**Expression**: `5280 ft to mi`

**Expected**: `1 mi`

**Root Cause**: The bare number fallback in `calculator.py` line 1547 uses `base_unit()` instead of `first_base_unit()`. When converting `5280 ft`, the system should find that feet's root base is meters, convert 5280 ft to meters, then convert meters to miles. But it's using `base_unit()` which may skip the intermediate step or pick the wrong base.

**File**: `calculator.py:1547`

**Fix**: Change `base_unit()` to `first_base_unit()` so the conversion chain correctly resolves through the root base unit.

**Verification**: `5280 ft to mi` → `1 mi`

---

#### SKIP-6: Test 3.5 — planet() function

**Expression**: `planet(earth; mass)`

**Expected**: `5.972E24 kg`

**Root Cause**: Two problems:
1. `DataSet.calculate()` in `dataset.py` lines 339-347 is a stub that returns `None`.
2. Moon is missing from `planets.json`.

**File**: `dataset.py:339-347`, `planets.json`

**Fix**:
1. Implement `DataSet.calculate()` to look up the object's property from the loaded dataset.
2. Add Moon data to `planets.json` (mass=7.342E22 kg, radius=1737.4 km, etc.).

**Verification**: `planet(earth; mass)` → `5.972E24 kg`

---

### 3.3 Weak Pass (Needs Improvement)

#### WEAK-1: Test 4.5 — Interval unit simplification

**Expression**: `2*pi*sqrt((1.5+/-0.05 m)/(9.81+/-0.01 m/s^2))`

**Expected**: `2.457±0.041 s`

**Root Cause**: The unit engine doesn't simplify `(m)^0.5 * (1/(m/s^2))^0.5` to `s`. The individual unit simplification for `(m)^0.5` and `(m/s^2)^-0.5` works in isolation, but combining them in a multiplication doesn't trigger the exponent-merging logic.

**File**: `math_structure.py`

**Fix**: Implement unit exponent combining in the multiplication path:
1. Add an `isUnit_exp()` predicate to detect unit-raised-to-power nodes.
2. When multiplying unit terms, merge exponents of matching base units.
3. Simplify power expressions: `m^0.5 * m^-0.5 = m^0 = 1`, `(s^-2)^-0.5 = s^1 = s`.

**Verification**: `2*pi*sqrt((1.5+/-0.05 m)/(9.81+/-0.01 m/s^2))` → `2.457±0.041 s`

---

## 4. Development Tasks — Ordered by Difficulty

### Task 1: Fix cbrt(-27) [EASY — 5 min]

**What**: Remove the custom `_cbrt` override from `_SYMPY_FUNC_MAP` so SymPy's native cube root handles negative numbers correctly.

**Files to modify**:
- `pyqalculate/math_structure.py` line 525: Delete `"cbrt": _cbrt,` from `_SYMPY_FUNC_MAP`
- `tests/test_qalculate_reference.py` line 61: Remove skip pattern for test 1.1

**Why**: SymPy's `cbrt(-27)` returns `-3` (real root). The custom `_cbrt` function incorrectly returns symbolic or complex output for negative inputs. Removing the override lets SymPy do its job.

**Verification**:
```python
from pyqalculate import Calculator
calc = Calculator()
assert calc.calculate("cbrt(-27)") == "-3"
```

**Risk**: Low. SymPy's native `cbrt` is well-tested. The only risk is if other code depends on the custom `_cbrt` behavior.

---

### Task 2: Fix `\` integer division [EASY — 15 min]

**What**: Add tokenizer support for `\` and fix the floor division logic.

**Files to modify**:
- `pyqalculate/parser.py` lines 162-172: Add `\` token emission
- `pyqalculate/parser.py` lines 667-676: Change `floor` to `trunc`

**Tokenizer fix** (lines 162-172):
```python
# In the character-by-character tokenizer loop:
if char == '\\':
    # Check if this is integer division (followed by digit/space/operator)
    # not an escape character
    if i + 1 < len(expr) and (expr[i+1].isdigit() or expr[i+1] in ' +-*/^'):
        tokens.append(Token(TT.BACKSLASH, '\\'))
    else:
        # escape character handling
        ...
```

**Division handler fix** (lines 667-676):
```python
# For both // and \ operators:
result = trunc(left / right)  # not floor(left / right)
```

**Why**: `137 \ 12` should be `11` (trunc toward zero). `floor` would give `11` for positive numbers but `-12` for `-23 \ 5` instead of `-4`. Using `trunc` matches qalculate's behavior.

**Verification**:
```python
calc = Calculator()
assert calc.calculate("137 \\ 12") == "11"
assert calc.calculate("-23 \\ 5") == "-4"  # trunc toward zero
```

**Risk**: Low. Adding a token is straightforward. The `trunc` vs `floor` difference only matters for negative numbers.

---

### Task 3: Fix bare number unit conversion [EASY — 5 min]

**What**: Change the base unit lookup method for bare number fallback conversion.

**Files to modify**:
- `pyqalculate/calculator.py` line 1547: `base_unit()` → `first_base_unit()`

**Change**:
```python
# Before:
base = unit.base_unit()
# After:
base = unit.first_base_unit()
```

**Why**: `base_unit()` may return a derived unit, causing the conversion chain to fail. `first_base_unit()` returns the fundamental SI base unit (meters for feet, kilograms for pounds), which is the correct starting point for unit conversion chains.

**Verification**:
```python
calc = Calculator()
assert calc.calculate("5280 ft to mi") == "1 mi"
```

**Risk**: Low. This is a one-line change. The only concern is if `first_base_unit()` returns something unexpected for edge-case units.

---

### Task 4: Verify sum() works [EASY — 5 min]

**What**: Test whether sum() already works, and remove the skip if it does.

**Files to modify**:
- `tests/test_qalculate_reference.py`: Remove skip pattern for test 1.2

**Why**: The sum function was implemented in v2.0. The `\i` iteration variable syntax might be the issue, but if `x` works as the variable, the test can use `x` instead.

**Verification**:
```python
calc = Calculator()
result = calc.calculate("sum(sin(x)^2+cos(x)^2, x, 1, 20)")
assert result == "20"
```

**If `\i` doesn't work**: Update the test expression to use `x` as the iteration variable. The mathematical identity `sin(x)^2 + cos(x)^2 = 1` holds regardless of variable name.

**Risk**: Very low. This is a verification task, not a code change (unless `\i` needs parser support).

---

### Task 5: Fix multisolve parser bug [EASY — 15 min]

**What**: Fix the implicit multiplication parsing inside multisolve brackets.

**Files to modify**:
- `pyqalculate/parser.py` line 856: Remove or adjust `limit_implicit_multiplication=True`

**The bug**: When parsing `multisolve([x+y+z=6, 2*x-y+z=3, ...])`, the parser sets `limit_implicit_multiplication=True` for the bracket contents. This tells the tokenizer to NOT merge adjacent number+variable tokens into implicit multiplication. So `2*x` becomes two separate tokens `2` and `x` instead of `2*x`.

**Fix options**:

Option A — Remove the flag:
```python
# Before (line 856):
parts = parse(bracket_content, limit_implicit_multiplication=True)
# After:
parts = parse(bracket_content)
```

Option B — Only limit when space-separated:
```python
# Keep implicit multiplication for 2x, but break on spaces
parts = parse(bracket_content, space_separates_tokens=True)
```

**Why**: The multisolve equations use standard math notation where `2x` means `2*x`. Removing the restriction lets the parser handle this correctly.

**Verification**:
```python
calc = Calculator()
result = calc.calculate("multisolve([x+y+z=6, 2*x-y+z=3, x+2*y-z=5]; [x, y, z])")
# Should return [13/7, 17/7, 12/7] or approximately [1.857, 2.429, 1.714]
```

**Risk**: Low. The change is localized to multisolve parsing. Other parsers that need `limit_implicit_multiplication` won't be affected.

---

### Task 6: Fix Gaussian integral constant conversion [MEDIUM — 30 min]

**What**: Make `_number_to_sympy()` recognize mathematical constants from their float values.

**Files to modify**:
- `pyqalculate/math_structure.py`, `_number_to_sympy()` function

**The bug**: When `e^(-x^2)` is parsed, `e` is stored as the float `2.718281828459045`. When `_number_to_sympy()` converts this to SymPy, it becomes `sp.Float(2.718...)` instead of `sp.E`. SymPy then integrates a numeric constant raised to a power, not the symbolic `e`.

**Fix**:
```python
import sympy as sp
import math

CONSTANT_TOLERANCE = 1e-10

KNOWN_CONSTANTS = [
    (sp.E, math.e, "e"),
    (sp.pi, math.pi, "pi"),
]

def _number_to_sympy(value):
    """Convert a number to a SymPy object, recognizing mathematical constants."""
    if isinstance(value, (int, float)):
        # Check if value is close to a known constant
        for sympy_const, float_val, name in KNOWN_CONSTANTS:
            if abs(value - float_val) / max(abs(float_val), 1e-15) < CONSTANT_TOLERANCE:
                return sympy_const
        # Fall through to regular conversion
        return sp.Float(value)
    # ... existing logic
```

**Why**: The Gaussian integral `integrate(e^(-x^2); -inf; inf)` requires `e` to be symbolic. When it's a float, SymPy can't apply the standard Gaussian integral formula and falls back to numeric evaluation with `erf`.

**Verification**:
```python
calc = Calculator()
result = calc.calculate("integrate(e^(-x^2); -inf; inf)")
assert "sqrt(pi)" in result or "√π" in result
```

**Risk**: Medium. The tolerance check must be tight enough to avoid false positives (e.g., a user entering `2.71828` shouldn't become `e`). Using relative tolerance with 1e-10 should be safe.

---

### Task 7: Implement planet() dataset [MEDIUM — 30 min]

**What**: Implement `DataSet.calculate()` and add Moon data to `planets.json`.

**Files to modify**:
- `pyqalculate/dataset.py` lines 339-347: Implement `DataSet.calculate()`
- `pyqalculate/data/planets.json`: Add Moon entry

**DataSet.calculate() implementation**:
```python
def calculate(self, object_name, property_name):
    """Look up a property of a celestial object."""
    if object_name not in self.data:
        return None
    obj = self.data[object_name]
    if property_name not in obj:
        return None
    value = obj[property_name]
    # Return as MathStructure with appropriate units
    return self._to_mathstructure(value, obj.get(f"{property_name}_unit", ""))
```

**Moon data for planets.json**:
```json
{
    "moon": {
        "mass": 7.342e22,
        "mass_unit": "kg",
        "radius": 1737.4,
        "radius_unit": "km",
        "distance_from_earth": 384400,
        "distance_unit": "km",
        "orbital_period": 27.3,
        "orbital_period_unit": "days"
    }
}
```

**Why**: Test 3.5 calls `planet(earth; mass)` and `planet(moon; mass)`. Without the calculate() implementation, the function returns None. Without Moon data, the second call fails.

**Verification**:
```python
calc = Calculator()
result = calc.calculate("planet(earth; mass)")
assert "5.972E24" in result or "5.972×10²⁴" in result
```

**Risk**: Medium. The dataset loading mechanism needs to handle units correctly. If the unit system doesn't match, the result could be off by orders of magnitude.

---

### Task 8: Fix complex cube root [MEDIUM — 45 min]

**What**: Make negative-number fractional powers return the principal complex root when appropriate.

**Files to modify**:
- `pyqalculate/number.py`, `raise_()` method

**The issue**: `(-27)^(1/3)` currently returns `-3` (real root). The reference test expects `1.5 + 2.598i` (principal complex root). In complex analysis, `z^(1/n)` has n roots, and the principal root is the one with the smallest positive argument. For `-27 = 27 * e^(i*pi)`, the principal cube root is `3 * e^(i*pi/3) = 1.5 + 2.598i`.

**Fix approach**:
```python
def raise_(self, exponent, allow_complex=False):
    if self.is_negative() and exponent.is_fraction():
        numerator = exponent.numerator()
        denominator = exponent.denominator()
        if denominator % 2 == 1 and allow_complex:
            # Odd root of negative number → complex principal root
            abs_result = abs(self).raise_(exponent)
            angle = sp.pi / denominator  # pi divided by odd root
            return ComplexNumber(
                abs_result * sp.cos(angle),
                abs_result * sp.sin(angle)
            )
    # ... existing real-number logic
```

**Why**: qalculate follows complex analysis convention: `(-27)^(1/3)` gives the principal cube root. The real root `-3` is one of the three cube roots, but not the principal one.

**Verification**:
```python
calc = Calculator()
result = calc.calculate("(-27)^(1/3)")
assert "1.5" in result and "2.598" in result
```

**Risk**: Medium. This changes behavior for ALL negative-number fractional powers. Need to verify that other tests (like `cbrt(-27) = -3`) still work. The key difference: `cbrt()` explicitly asks for the real root, while `^(1/3)` asks for the principal root.

---

### Task 9: Fix interval unit simplification [HARD — 2-4 hours]

**What**: Implement unit exponent combining so `(m)^0.5 * (1/(m/s^2))^0.5` simplifies to `s`.

**Files to modify**:
- `pyqalculate/math_structure.py`: Unit simplification engine

**The problem**: When evaluating `sqrt(m) * sqrt(s^2/m)`, the system creates two separate unit nodes:
- Node A: `m^0.5`
- Node B: `(m/s^2)^(-0.5) = m^(-0.5) * s^1`

The multiplication should combine these: `m^0.5 * m^(-0.5) * s^1 = m^0 * s^1 = s`. But the current engine doesn't merge exponents of matching base units during multiplication.

**Fix approach**:

1. **Add `isUnit_exp()` predicate**:
```python
def isUnit_exp(node):
    """Check if a MathStructure node is a unit raised to a power."""
    return (node.is_power() and
            node.base().is_unit() and
            node.exponent().is_number())
```

2. **Exponent merging in MULTIPLICATION**:
```python
def simplify_unit_multiplication(terms):
    """Merge exponents of matching base units."""
    unit_exps = {}  # base_unit -> total_exponent
    for term in terms:
        if isUnit_exp(term):
            base = term.base().unit_name()
            exp = term.exponent().value()
            unit_exps[base] = unit_exps.get(base, 0) + exp
        elif term.is_unit():
            unit_exps[term.unit_name()] = unit_exps.get(term.unit_name(), 0) + 1
    # Remove zero-exponent units
    return {u: e for u, e in unit_exps.items() if abs(e) > 1e-10}
```

3. **Power simplification**: After merging, simplify units with exponent 0 to 1 (dimensionless).

**Why**: This is the hardest fix because it touches the core unit arithmetic engine. The simplification must work for all unit combinations, not just this specific test case. Getting it wrong could break existing unit conversions.

**Verification**:
```python
calc = Calculator()
result = calc.calculate("2*pi*sqrt((1.5+/-0.05 m)/(9.81+/-0.01 m/s^2))")
assert "s" in result  # Must simplify to seconds
# Numeric check:
assert "2.457" in result
assert "0.041" in result
```

**Risk**: High. The unit engine is shared across all calculations. A bug here could break dozens of existing passing tests. Must run full regression suite after this change.

---

## 5. Test Strategy

### 5.1 Per-Task Verification

Each task has specific verification steps (see task descriptions above). The general pattern:

1. **Unit test**: Write a focused test for the specific fix
2. **Reference test**: Run the corresponding reference test from the `.txt` files
3. **Regression test**: Run the full 869+ unit test suite to catch side effects

### 5.2 Reference Test Integration

After all tasks, run the complete reference test suite:

```bash
pytest tests/test_qalculate_reference.py -v
```

Expected output:
```
79 passed, 0 failed, 0 skipped
```

### 5.3 Tolerance Guidelines

| Result Type | Tolerance | Example |
|-------------|-----------|---------|
| Exact integer | Exact match | `-3` = `-3` |
| Exact fraction | Exact match | `13/7` = `13/7` |
| Floating point | ±0.001 relative | `1.857` ≈ `1.857` |
| Uncertainty | ±0.01 absolute | `2.457±0.041` ≈ `2.457±0.041` |
| Symbolic | Canonical form match | `sqrt(pi)` = `sqrt(pi)` |
| Complex number | ±0.001 per component | `1.5 + 2.598i` ≈ `1.5 + 2.598i` |

### 5.4 Regression Testing

After each task, run the full unit test suite:

```bash
pytest tests/ -v --tb=short
```

**Critical**: If any task causes regressions, stop and investigate before proceeding. The goal is 79/79 without breaking existing passing tests.

---

## 6. Risk Assessment

### 6.1 Low-Risk Tasks (Tasks 1-5)

These are surgical fixes with clear root causes and minimal blast radius.

| Task | Risk | Mitigation |
|------|------|------------|
| 1. cbrt(-27) | Removing a function override | Verify SymPy's native cbrt works for all inputs |
| 2. `\` division | Adding a token + changing floor to trunc | Test positive and negative numbers |
| 3. bare number conversion | One-line method change | Test edge cases (dimensionless units) |
| 4. sum() verification | No code change expected | Just remove skip pattern |
| 5. multisolve parser | Removing a parser flag | Test all equation types in algebra suite |

### 6.2 Medium-Risk Tasks (Tasks 6-8)

These touch core systems but have isolated blast radius.

| Task | Risk | Mitigation |
|------|------|------------|
| 6. Gaussian integral | Float-to-constant detection | Tight tolerance to avoid false positives |
| 7. planet() dataset | Dataset loading + unit handling | Verify unit conversion chain for constants |
| 8. complex cube root | Changes power evaluation behavior | Verify cbrt() still returns real root |

### 6.3 High-Risk Tasks (Task 9)

| Task | Risk | Mitigation |
|------|------|------------|
| 9. interval unit simplification | Touches core unit arithmetic engine | Run full regression suite; implement incrementally; test each unit combination |

### 6.4 Worst-Case Scenarios

**Scenario A**: Task 9 causes regressions in existing unit conversions.
- **Impact**: Could drop passing tests from 71 to lower.
- **Mitigation**: Implement unit simplification as an opt-in path, not a replacement for existing logic.

**Scenario B**: Task 8 changes break other power evaluations.
- **Impact**: Tests relying on real roots of negative numbers could fail.
- **Mitigation**: Only use complex path when `allow_complex=True` is explicitly set.

**Scenario C**: Task 6's constant detection triggers on user input.
- **Impact**: User enters `2.71828` and gets `e` instead.
- **Mitigation**: Use very tight tolerance (1e-10 relative) and only check known constants.

---

## 7. Execution Order — Dependency-Aware

### 7.1 Recommended Order

The tasks are independent (no task depends on another), but some share files. Group by file to minimize context switching:

**Batch 1 — Parser fixes** (Tasks 2 + 5):
- Both modify `parser.py`
- Fix tokenizer for `\` (Task 2)
- Fix multisolve `limit_implicit_multiplication` (Task 5)
- Run parser tests after both changes

**Batch 2 — math_structure.py fixes** (Tasks 1 + 6):
- Task 1: Remove `_cbrt` from `_SYMPY_FUNC_MAP`
- Task 6: Add constant detection to `_number_to_sympy()`
- Run calculus and basic operations tests after both changes

**Batch 3 — Standalone fixes** (Tasks 3 + 4 + 7):
- Task 3: `calculator.py` one-liner
- Task 4: Skip pattern removal (test file only)
- Task 7: `dataset.py` + `planets.json`
- Run unit conversion and constants tests

**Batch 4 — Complex number fix** (Task 8):
- Task 8: `number.py` power evaluation
- Test both `(-27)^(1/3)` and `cbrt(-27)` to ensure no conflict

**Batch 5 — Unit simplification** (Task 9):
- Task 9: `math_structure.py` unit engine
- Run full regression suite before and after
- This is the riskiest change; isolate it last

### 7.2 Parallel Execution

Tasks 1-8 are safe to parallelize (different files or non-conflicting changes). Task 9 should be done sequentially after all others, since it touches the unit engine shared by many tests.

### 7.3 Quick Wins First

If time is limited, prioritize by expected impact:

| Priority | Task | Tests Gained | Time | ROI |
|----------|------|-------------|------|-----|
| 1 | Task 1: cbrt(-27) | +1 | 5 min | Highest |
| 2 | Task 4: sum() verification | +1 | 5 min | Highest |
| 3 | Task 3: bare number conversion | +1 | 5 min | Highest |
| 4 | Task 5: multisolve parser | +1 | 15 min | High |
| 5 | Task 2: `\` integer division | +1 | 15 min | High |
| 6 | Task 7: planet() dataset | +1 | 30 min | Medium |
| 7 | Task 6: Gaussian integral | +1 | 30 min | Medium |
| 8 | Task 8: complex cube root | +1 | 45 min | Medium |
| 9 | Task 9: interval unit simplification | 0 (hardens weak pass) | 2-4 hrs | Low |

**Minimum viable v2.1**: Tasks 1-7 give 78/79 (98.7%). Task 8 gets to 79/79 (100%). Task 9 improves quality but doesn't change pass count.

---

## 8. Test Case Reference

### 8.1 All 8 Tests to Fix

| # | Test | Current Status | Fix Task | Expected Result |
|---|------|---------------|----------|-----------------|
| 1.1 | `cbrt(-27)` | Skipped | Task 1 | `-3` |
| 1.2 | `sum(sin(\i)^2+cos(\i)^2; 1; 20; \i)` | Skipped | Task 4 | `20` |
| 1.4 | `137 \ 12` | Skipped | Task 2 | `11` |
| 1.8 | `(-27)^(1/3)` | Skipped | Task 8 | `1.5 + 2.598i` |
| 2.6 | `5280 ft to mi` | Skipped | Task 3 | `1 mi` |
| 3.5 | `planet(earth; mass)` | Skipped | Task 7 | `5.972E24 kg` |
| 5.3 | `multisolve([x+y+z=6, ...])` | Failed | Task 5 | `[13/7, 17/7, 12/7]` |
| 6.3 | `integrate(e^(-x^2); -inf; inf)` | Failed | Task 6 | `sqrt(pi)` |

### 8.2 Weak Pass to Harden

| # | Test | Current Status | Fix Task | Expected Result |
|---|------|---------------|----------|-----------------|
| 4.5 | `2*pi*sqrt((1.5+/-0.05 m)/(9.81+/-0.01 m/s^2))` | Weak pass | Task 9 | `2.457±0.041 s` |

---

## 9. Deliverables

### 9.1 Modified Files

| File | Tasks | Changes |
|------|-------|---------|
| `pyqalculate/math_structure.py` | 1, 6, 9 | Remove cbrt override; add constant detection; unit exponent combining |
| `pyqalculate/parser.py` | 2, 5 | Add `\` token; fix multisolve implicit multiplication |
| `pyqalculate/calculator.py` | 3 | Change base_unit to first_base_unit |
| `pyqalculate/number.py` | 8 | Complex path for negative fractional powers |
| `pyqalculate/dataset.py` | 7 | Implement DataSet.calculate() |
| `pyqalculate/data/planets.json` | 7 | Add Moon data |
| `tests/test_qalculate_reference.py` | 1, 4 | Remove skip patterns |

### 9.2 No New Files

Unlike v2.0, v2.1 doesn't require new modules. All fixes are within existing files.

---

## 10. Appendix: v2.0 → v2.1 Pass Rate Trajectory

```
v1.0:  23/79 =  29%  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
v2.0:  71/79 =  90%  ████████████████████████████████████████████░░░░░░░
v2.1:  79/79 = 100%  ████████████████████████████████████████████████████
                     ────────────────────────────────────────────────────
                     0%                    50%                       100%
```

### Gains Per Task

| Task | Tests Gained | Cumulative | Cumulative % |
|------|-------------|------------|-------------|
| Task 1: cbrt(-27) | +1 | 72 | 91.1% |
| Task 2: `\` division | +1 | 73 | 92.4% |
| Task 3: bare number conversion | +1 | 74 | 93.7% |
| Task 4: sum() verification | +1 | 75 | 94.9% |
| Task 5: multisolve parser | +1 | 76 | 96.2% |
| Task 6: Gaussian integral | +1 | 77 | 97.5% |
| Task 7: planet() dataset | +1 | 78 | 98.7% |
| Task 8: complex cube root | +1 | 79 | 100% |
| Task 9: interval unit hardening | 0 (quality) | 79 | 100% |

---

*Document created for PyQalculate v2.1 development. Execute tasks in batch order. Each batch is independently testable. Run full regression suite after each batch.*

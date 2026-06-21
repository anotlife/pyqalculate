# PyQalculate v2.0 — Development Plan

> **Project Goal**: Raise reference test pass rate from 29% (23/79) to 100% (79/79 passing).
>
> **Scope**: 8 development phases targeting the 55 skipped + 1 failed reference tests.
>
> **This document is for execution by subsequent agents. Follow phases in priority order.**

---

## 1. Project Overview

### 1.1 v2.0 Goal

The v1.0 release achieved a working core: 869 unit tests passing, basic math, unit conversion, 151 built-in functions, CLI, and GUI. However, only 23 of 79 reference tests pass (29%). The v2.0 milestone targets **100% reference test pass rate**, meaning all **79 of 79 tests must pass**.

This requires implementing 8 feature domains that are currently stubbed or missing entirely.

### 1.2 v1.0 Recap

| Component | Status |
|-----------|--------|
| Core number engine (gmpy2/mpmath) | Working |
| Expression parser | Working |
| MathStructure expression tree | Working |
| Calculator engine (calculate/evaluate) | Working |
| Unit conversion system (426+ units) | Working |
| 151 built-in functions (basic) | Working |
| CLI application (pyqalc) | Working |
| GUI application (PyQt6) | Working |
| 869 unit tests | All passing |

### 1.3 What v2.0 Does Not Cover

- Performance optimization (SymEngine backend, caching)
- Additional built-in functions beyond what's needed for reference tests
- Web interface or Jupyter integration
- Currency API integration (real-time rates)
- Plotting improvements

---

## 2. v1.0 Completion Status

| Module | Files | Unit Tests | Reference Tests | Status |
|--------|-------|-----------|----------------|--------|
| Number engine | `number.py` | ✅ Passing | 23/79 overall | Core working |
| Parser | `parser.py` | ✅ Passing | — | Core working |
| Expression tree | `math_structure.py` | ✅ Passing | — | Core working |
| Calculator | `calculator.py` | ✅ Passing | — | Core working |
| Units | `unit.py`, `prefix.py` | ✅ Passing | 10/10 in 02 | Mostly working |
| Basic functions | `builtin_functions.py` | ✅ Passing | 6/9 in 01 | Core trig/arithmetic OK |
| Physical constants | `variable.py` | Partial | 1/7 in 03 | Constants load, expressions fail |
| Matrices | `builtin_functions.py` | Partial | 2/8 in 07 | Basic ops work, advanced missing |
| Statistics | `builtin_functions.py` | Partial | 3/6 in 08 | mean/stdev OK, rest missing |
| Calculus | Stub only | ❌ | 0/8 in 06 | Not implemented |
| Algebra solving | Stub only | ❌ | 0/8 in 05 | Not implemented |
| Uncertainty/interval | Stub only | ❌ | 0/5 in 04 | Not implemented |
| Time/date | Stub only | ❌ | 0/8 in 09 | Not implemented |
| Number bases | Partial | ✅ Passing | 3/10 in 10 | bin/oct/hex OK, rest missing |

---

## 3. Reference Test Results — Detailed Breakdown

### Summary

| Metric | Count |
|--------|-------|
| Total reference tests | 79 |
| Passing | 23 (29%) |
| Skipped | 55 |
| Failed | 1 |
| **v2.0 Target** | **79/79 (100%)** |
| Already passing (no work needed) | 23 |
| Easy fixes (variable additions, simple functions) | ~30 |
| Medium difficulty (core engine extensions) | ~15 |
| Hard (unit chains, symbolic resolution) | ~11 |

### Per-File Breakdown

| File | Tests | Passed | Skipped | Failed | v2.0 Target |
|------|-------|--------|---------|--------|-------------|
| 01_basic_operations.txt | 9 | 6 | 3 | 0 | 9/9 |
| 02_unit_conversions.txt | 10 | 9 | 1 | 0 | 10/10 |
| 03_physical_constants.txt | 7 | 1 | 4 | 1 | 7/7 |
| 04_uncertainty_interval.txt | 5 | 0 | 5 | 0 | 5/5 |
| 05_algebra_equations.txt | 8 | 0 | 8 | 0 | 8/8 |
| 06_calculus.txt | 8 | 0 | 8 | 0 | 8/8 |
| 07_matrices_vectors.txt | 8 | 2 | 6 | 0 | 8/8 |
| 08_statistics.txt | 6 | 3 | 3 | 0 | 6/6 |
| 09_time_date.txt | 8 | 0 | 8 | 0 | 8/8 |
| 10_number_bases.txt | 10 | 3 | 6 | 1 | 10/10 |
| **Total** | **79** | **23** | **55** | **1** | **79/79** |

*Note: All 10 number base tests including 10.8 (bitwise) and 10.10 (base sqrt(2)) are included in the 100% target.*

---

## 4. v2.0 Target

### 4.1 Pass Rate Trajectory

```
v1.0:  23/79 = 29%  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
v2.0:  79/79 = 100% ████████████████████████████████████████████████
```

### 4.2 Gains Per Phase

| Phase | Tests Gained | Cumulative | Cumulative % |
|-------|-------------|------------|-------------|
| Phase 1: Calculus | +8 | 31 | 39% |
| Phase 2: Algebra | +8 | 39 | 49% |
| Phase 3: Uncertainty | +5 | 44 | 56% |
| Phase 4: Matrices | +6 | 50 | 63% |
| Phase 5: Statistics | +3 | 53 | 67% |
| Phase 6: Time/Date | +8 | 61 | 77% |
| Phase 7: Number Bases | +8 | 69 | 87% |
| Phase 8: Physical Constants | +10 | 79 | 100% |

---

## 5. Development Phases

### Phase 1: Calculus Engine (5-7 days)

**Target**: `06_calculus.txt` — all 8 tests (currently 0/8)

**Goal**: Implement symbolic differentiation, integration, and limits via SymPy delegation.

**Reference Tests to Pass**:

| # | Expression | Expected Output | Difficulty |
|---|-----------|----------------|------------|
| 6.1 | `diff(sin(x^2) * e^(-x))` | `2 * e^(-x) * cos(x^2) * x - e^(-x) * sin(x^2)` | Medium |
| 6.2 | `integrate(x^2 * ln(x))` | `1/3 * ln(x) * x^3 - 1/9 * x^3 + C` | Medium |
| 6.3 | `integrate(e^(-x^2); -inf; inf)` | `sqrt(pi)` (Gaussian integral) | Hard |
| 6.4 | `limit((1 + 1/n)^n; inf)` | `e` | Medium |
| 6.5 | `limit(sin(x)/x; 0)` | `1` | Easy |
| 6.6 | `diff(x^4 - 3x^3 + 2x^2 - x + 1; x; 2)` | `12x^2 - 18x + 4` | Easy |
| 6.7 | `integrate(sin(x)^2; 0; pi)` | `pi/2` | Medium |
| 6.8 | `integrate(1/(1+x^2); -inf; inf)` | `pi` | Hard |

**Implementation Plan**:

1. **diff() function** (`builtin_functions.py`):
   - Register `DiffFunction` class
   - Delegate to `sympy.diff(expr, var, order)`
   - Handle both `diff(expr)` (auto-detect variable) and `diff(expr, x, n)` (explicit)
   - Map SymPy output back to MathStructure

2. **integrate() function**:
   - Register `IntegrateFunction` class
   - Delegate to `sympy.integrate(expr, var)` for indefinite
   - Delegate to `sympy.integrate(expr, (var, a, b))` for definite
   - Handle `+C` constant for indefinite integrals
   - Handle `erf()` in output for Gaussian-type integrals

3. **limit() function**:
   - Register `LimitFunction` class
   - Delegate to `sympy.limit(expr, var, point)`
   - Handle `inf` / `oo` mapping

4. **Output formatting**:
   - Create `CalculusPrinter` extending SymPy's printer
   - Format `e^x` as `e^x` (not `exp(x)`)
   - Handle `erf(1 in)` output format
   - Handle `+ C` suffix for indefinite integrals

**Verification**: Run `tests/test_calculus.py` and compare all 8 outputs against `06_calculus.txt`.

---

### Phase 2: Algebra Equation Solving (5-7 days)

**Target**: `05_algebra_equations.txt` — all 8 tests (currently 0/8)

**Goal**: Implement symbolic equation solving, factoring, expansion, and GCD.

**Reference Tests to Pass**:

| # | Expression | Expected Output | Difficulty |
|---|-----------|----------------|------------|
| 5.1 | `x^6 - 1 to factors` | `(x-1)(x+1)(x^2-x+1)(x^2+x+1)` | Medium |
| 5.2 | `1/(x^3 - x) to partial fraction` | `1/(2x+2) + 1/(2x-2) - 1/x` | Medium |
| 5.3 | `multisolve([x+y+z=6, 2x-y+z=3, x+2y-z=5]; [x,y,z])` | `[1.857  2.429  1.714]` | Hard |
| 5.4 | `dsolve(diff(y;x) + 2y = 4x; 5)` | `2x + 6*e^(-2x) - 1` | Hard |
| 5.5 | `solve(x = y + ln(y); y)` | `lambertw(e^x)` | Hard |
| 5.6 | `x^2 + 5x + 6 = 0 where x > -3` | `x = -2` | Medium |
| 5.7 | `expand((x+1)^8)` | Polynomial expansion | Easy |
| 5.8 | `gcd(x^3 - 1; x^2 - 1)` | `x - 1` | Medium |

**Implementation Plan**:

1. **solve() function**:
   - Register `SolveFunction` class
   - Delegate to `sympy.solve(eq, var)`
   - Handle `where` clause for conditional solutions (filter results)
   - Handle Lambert W output format

2. **multisolve() function**:
   - Register `MultiSolveFunction` class
   - Delegate to `sympy.solve([eq1, eq2, ...], [x, y, z])`
   - Format vector output as `[val1  val2  val3]`

3. **dsolve() function**:
   - Register `DsolveFunction` class
   - Delegate to `sympy.dsolve(eq, func, ics={y(0): value})`
   - Handle initial condition parameter

4. **factor() / expand() / to factors / to partial fraction**:
   - Register `FactorFunction`, `ExpandFunction`
   - Parse `to factors` and `to partial fraction` as conversion targets
   - Delegate to `sympy.factor()`, `sympy.expand()`, `sympy.apart()`

5. **Polynomial GCD**:
   - Extend existing `gcd()` to handle symbolic polynomials
   - Delegate to `sympy.gcd(poly1, poly2)` for polynomial inputs

**Verification**: Run `tests/test_algebra.py` and compare all 8 outputs against `05_algebra_equations.txt`.

---

### Phase 3: Uncertainty & Interval Arithmetic (3-5 days)

**Target**: `04_uncertainty_interval.txt` — all 5 tests (currently 0/5)

**Goal**: Implement interval arithmetic with automatic error propagation.

**Reference Tests to Pass**:

| # | Expression | Expected Output | Difficulty |
|---|-----------|----------------|------------|
| 4.1 | `(5±0.1)*(3±0.2)^2/(2±0.05)` | `22.5±3.1` | Hard |
| 4.2 | `interval(-3; 7)^3` | `interval(-52, 68)` | Medium |
| 4.3 | `sin(pi/4 ± 0.01)^2` | `0.5000±0.0020` | Hard |
| 4.4 | `(2.5±0.3 m) / (1.2±0.1 s) to m/s` | `2.08±0.31 m/s` | Medium |
| 4.5 | `2*pi*sqrt((1.5±0.05 m)/(9.81±0.01 m/s^2))` | `2.457±0.041 s` | Hard |

**Implementation Plan**:

1. **Interval class** (new file `interval.py`):
   ```python
   class Interval:
       value: float      # center value
       uncertainty: float  # ± uncertainty
       unit: str | None
   ```

2. **± syntax parser support**:
   - Extend parser to recognize `value ± uncertainty` notation
   - Map to `Interval(value, uncertainty)`
   - Handle unit attachment: `(2.5±0.3 m)`

3. **Interval arithmetic operations**:
   - Addition/Subtraction: uncertainties add in quadrature
   - Multiplication: relative uncertainties add in quadrature
   - Division: relative uncertainties add in quadrature
   - Power: `relative_unc = |n| * relative_unc_base`
   - Trig functions: propagate through derivatives
   - Square root: `uncertainty / (2 * sqrt(value))`

4. **Error propagation engine**:
   - For `f(x1±u1, x2±u2, ...)`: `uf = sqrt((∂f/∂x1*u1)^2 + (∂f/∂x2*u2)^2)`
   - Use SymPy's `diff()` for partial derivatives
   - Numerical evaluation for final result

5. **interval() function**:
   - Register `IntervalFunction` class
   - Accept `interval(lower; upper)` syntax
   - Convert to center ± half-width for arithmetic
   - Output as `interval(lower, upper)` for interval results

6. **Output formatting**:
   - Format `22.5±3.1` (not `22.5 ± 3.1`)
   - Round uncertainty to 1-2 significant figures
   - Match value precision to uncertainty decimal place

**Verification**: Run `tests/test_interval.py` and compare all 5 outputs against `04_uncertainty_interval.txt`.

---

### Phase 4: Advanced Matrix Operations (3-5 days)

**Target**: `07_matrices_vectors.txt` — 6 additional tests (currently 2/8)

**Goal**: Implement matrix inverse, cross product, dot product, Hadamard product, eigenvalues, and trace.

**Reference Tests to Pass** (the 6 currently skipped):

| # | Expression | Expected Output | Difficulty |
|---|-----------|----------------|------------|
| 7.4 | `cross([1 2 3]; [4 5 6])` | `[-3  6  -3]` | Easy |
| 7.5 | `[1 2 3 4].[5 6 7 8]` | `70` | Easy |
| 7.6 | `[1 2; 3 4].*[5 6; 7 8]` | `[5  12; 21  32]` | Easy |
| 7.7 | `eigenvalues([4 1; 2 3])` | `[2, 5]` | Medium |
| 7.8 | `trace([1 2 3; 4 5 6; 7 8 9])` | `15` | Easy |
| 7.2 | `[2 1 0; 1 0 1; 0 1 2]^-1` | Inverse matrix | Medium |

**Implementation Plan**:

1. **cross() function**:
   - Register `CrossProductFunction` class
   - Validate both inputs are 3-element vectors
   - Delegate to `sympy.Matrix.cross()`
   - Format output as `[-3  6  -3]`

2. **Dot product** (`.` operator):
   - Parse `.` between vectors as dot product operator
   - Delegate to `sympy.Matrix.dot()`
   - Return scalar result

3. **Hadamard product** (`.*` operator):
   - Parse `.*` between matrices as element-wise multiplication
   - Implement as `(A .* B)[i,j] = A[i,j] * B[i,j]`
   - Format as matrix output

4. **eigenvalues() function**:
   - Register `EigenvaluesFunction` class
   - Delegate to `sympy.Matrix.eigenvals()`
   - Return eigenvalues as vector

5. **trace() function**:
   - Register `TraceFunction` class
   - Delegate to `sympy.Matrix.trace()`
   - Return scalar

6. **Matrix inverse** (`^-1` syntax):
   - Ensure `MathStructure` handles `matrix ^ -1` as inverse
   - Delegate to `sympy.Matrix.inv()`

**Verification**: Run `tests/test_matrix.py` and compare all 8 outputs against `07_matrices_vectors.txt`.

---

### Phase 5: Advanced Statistics (2-3 days)

**Target**: `08_statistics.txt` — 3 additional tests (currently 3/6)

**Goal**: Implement quartile, normdist, and correlation functions.

**Reference Tests to Pass** (the 3 currently skipped):

| # | Expression | Expected Output | Difficulty |
|---|-----------|----------------|------------|
| 8.3 | `quartile([12 15 18 22 25 30 35 40 42 48]; 1)` | `19` | Easy |
| 8.3b | `quartile([12 15 18 22 25 30 35 40 42 48]; 2)` | `27.5` | Easy |
| 8.3c | `quartile([12 15 18 22 25 30 35 40 42 48]; 3)` | `38.75` | Easy |
| 8.4 | `normdist(100; 100; 15)` | `0.02659615203` | Medium |
| 8.5 | `correlation([1..10]; [2,4,5,4,5,7,8,9,10,12])` | `-0.9719076166` | Medium |

**Implementation Plan**:

1. **quartile() function**:
   - Register `QuartileFunction` class
   - Accept array + quartile number (1, 2, 3)
   - Implement using numpy's percentile with linear interpolation
   - quartile(data, 1) = percentile(data, 25)
   - quartile(data, 2) = percentile(data, 50) = median
   - quartile(data, 3) = percentile(data, 75)

2. **normdist() function**:
   - Register `NormDistFunction` class
   - Delegate to `scipy.stats.norm.pdf(x, mu, sigma)`
   - Handle 2-arg form: `normdist(x; mu; sigma)`

3. **correlation() function**:
   - Register `CorrelationFunction` class
   - Delegate to `numpy.corrcoef(x, y)[0,1]`
   - Handle array inputs from vector syntax
   - Note: expected output shows negative correlation (`-0.9719`)

**Verification**: Run `tests/test_statistics.py` and compare all 6 outputs against `08_statistics.txt`.

---

### Phase 6: Time & Date Functions (3-5 days)

**Target**: `09_time_date.txt` — all 8 tests (currently 0/8)

**Goal**: Implement time arithmetic, date operations, timezone conversion, and timestamp.

**Reference Tests to Pass**:

| # | Expression | Expected Output | Difficulty |
|---|-----------|----------------|------------|
| 9.1 | `10:31 + 8:30 to time` | `19:01` | Easy |
| 9.2 | `10h 31min + 8h 30min to time` | `19:01` | Easy |
| 9.3 | `now to utc` | `"2026-06-19T11:54:21Z"` | Medium |
| 9.4 | `now to utc+8` | `"2026-06-19T19:54:21+08:00"` | Medium |
| 9.5 | `days(2024-01-01; 2024-12-25)` | `359` | Easy |
| 9.6 | `2024-06-15 + 100 days` | Date result | Medium |
| 9.7 | `timestamp(2024-01-01)` | `1704038400` | Easy |
| 9.8 | `2024-10-01 to calendars` | Calendar conversions | Hard |

**Implementation Plan**:

1. **Time arithmetic** (`to time`):
   - Parse `HH:MM` syntax as time values
   - Parse `Xh Ymin` syntax as alternative time format
   - Implement addition: `10:31 + 8:30 = 19:01`
   - Format result as `HH:MM` with `to time` conversion

2. **now function**:
   - Register `NowFunction` class
   - Return current datetime as `QalculateDateTime`
   - Support `to utc` conversion (ISO 8601 format)
   - Support `to utc+N` timezone offset

3. **days() function**:
   - Register `DaysFunction` class
   - Accept two date arguments
   - Calculate difference in days
   - Handle leap years correctly

4. **Date arithmetic** (`date + N days`):
   - Parse `YYYY-MM-DD` as date literal
   - Support `date + N days` addition
   - Format result back as `YYYY-MM-DD`

5. **timestamp() function**:
   - Register `TimestampFunction` class
   - Convert date to Unix timestamp (seconds since 1970-01-01)
   - Use `datetime.datetime.timestamp()` internally

6. **Calendar conversions** (`to calendars`):
   - Leverage `convertdate` library
   - Support Islamic, Hebrew, Julian, and other calendar systems
   - Format as list of calendar dates

**Verification**: Run `tests/test_datetime.py` and compare all 8 outputs against `09_time_date.txt`.

---

### Phase 7: Number Base Extensions (2-3 days)

**Target**: `10_number_bases.txt` — all 10 tests (currently 3/10)

**Goal**: Implement float representation, arbitrary base, roman numerals, extended binary, bitwise operations, and non-integer base conversion.

**Reference Tests to Pass** (the 7 currently skipped or failed):

| # | Expression | Expected Output | Difficulty |
|---|-----------|----------------|------------|
| 10.5 | `3.14159 to float` | IEEE 754 binary representation | Medium |
| 10.6 | `255 to base 7` | `513` | Easy |
| 10.7 | `2024 to roman` | `MMXXIV` | Easy |
| 10.8 | `(0xABCD AND 0xFF00) to hex` | `0xAB00` | Medium |
| 10.9 | `42 to bin16` | `0000 0000 0010 1010` | Easy |
| 10.10 | `16 to base sqrt(2)` | `100000000` | Hard |

**Implementation Plan**:

1. **`to float` (IEEE 754)**:
   - Implement binary32/binary64 encoding
   - Parse float → sign + exponent + mantissa
   - Format as 32-bit grouped binary string
   - Handle special cases: NaN, Inf, denormals

2. **`to base N` (arbitrary base)**:
   - Implement generic base conversion for bases 2-36
   - Support non-integer bases (like `sqrt(2)`) via representation algorithm
   - Format digits using 0-9, A-Z for values > 9

3. **`to roman`**:
   - Implement Roman numeral conversion
   - Standard subtractive notation (IV, IX, XL, XC, etc.)
   - Handle large numbers with overline notation if needed

4. **Bitwise AND**:
   - Ensure `AND` operator works on hex literals
   - Parse `0xABCD` as hexadecimal integer
   - Apply bitwise AND: `0xABCD & 0xFF00 = 0xAB00`

5. **`to bin16` (16-bit binary)**:
   - Extend existing `to bin` to support width parameter
   - `bin16` = 16-bit binary with leading zeros

**Verification**: Run `tests/test_bases.py` and compare all 10 outputs against `10_number_bases.txt`.

---

### Phase 8: Physical Constants (2-3 days)

**Target**: `03_physical_constants.txt` — all 7 tests (currently 1/7 passing, 1 failed)

**Goal**: Fix failing test and implement all remaining constant expressions including symbolic constant resolution, complex cube roots, and unit conversion with constants.

**Reference Tests to Pass** (6 currently skipped + 1 fix):

| # | Expression | Expected Output | Difficulty |
|---|-----------|----------------|------------|
| 3.1 | `sqrt(planck * newtonian_constant / speed_of_light^3)` | `4.051E-35 m` | Medium |
| 3.3 | `2 * newtonian_constant * sun_mass / speed_of_light^2` | Schwarzschild radius | Medium |
| 3.4 | `planck * speed_of_light / (500 nm) to eV` | `2.479683969 eV` | Medium |
| 3.6 | `speed_of_light / 1.33` | `225.4078632 km/ms` | Easy |
| 3.7 | `planck / sqrt(2 * pi * electron_mass * boltzmann * 300 K)` | `4.30347544 nm` | Hard |

**Implementation Plan**:

1. **Constant expression evaluation**:
   - Ensure constants return `MathStructure` with units attached
   - `planck` → `6.626E-34 J*s`
   - `newtonian_constant` → `6.674E-11 m^3/(kg*s^2)`
   - `speed_of_light` → `299792458 m/s`
   - `electron_mass` → `9.109E-31 kg`
   - `boltzmann` → `1.381E-23 J/K`

2. **Unit arithmetic with constants**:
   - Verify multiplication/division preserves unit chains
   - Ensure `J*s * m^3/(kg*s^2) / (m/s)^3` simplifies to `m`
   - Fix `kg*s*m^2/Pa` garbage output (test 3.3)

3. **Planck length expression** (test 3.1):
   - Chain: `planck * G / c^3` → take sqrt → result in meters
   - Verify unit cancellation produces `m`

4. **Photon energy** (test 3.4):
   - `planck * speed_of_light / (500 nm)` → Joules
   - Convert Joules to eV: `1 eV = 1.602E-19 J`
   - Verify result ≈ 2.48 eV

5. **Thermal de Broglie wavelength** (test 3.7):
   - `planck / sqrt(2 * pi * m_e * k_B * T)` with T = 300 K
   - Complex unit chain, verify result in nanometers

**Verification**: Run `tests/test_constants.py` and compare outputs against `03_physical_constants.txt`.

---

## 6. Test Strategy

### 6.1 Unit Tests Per Phase

Each phase creates or extends a dedicated test file:

| Phase | Test File | Tests | Strategy |
|-------|-----------|-------|----------|
| 1 | `tests/test_calculus.py` | 8 reference + N unit | SymPy delegation verification |
| 2 | `tests/test_algebra.py` | 8 reference + N unit | Symbolic output comparison |
| 3 | `tests/test_interval.py` | 5 reference + N unit | Numeric tolerance (±0.01) |
| 4 | `tests/test_matrix.py` | 8 reference + N unit | Matrix equality comparison |
| 5 | `tests/test_statistics.py` | 6 reference + N unit | Numeric tolerance (±0.001) |
| 6 | `tests/test_datetime.py` | 8 reference + N unit | String + numeric comparison |
| 7 | `tests/test_bases.py` | 10 reference + N unit | String comparison |
| 8 | `tests/test_constants.py` | 7 reference + N unit | Numeric tolerance + unit check |

### 6.2 Reference Test Integration

After each phase, run the full reference test suite:

```bash
pytest tests/test_integration.py -v --reference-output=qalculate_output/
```

This compares calculator output against the reference files line by line.

### 6.3 Tolerance Guidelines

| Result Type | Tolerance | Example |
|-------------|-----------|---------|
| Exact integer | Exact match | `15504` = `15504` |
| Exact fraction | Exact match | `11 + 5/12` = `11 + 5/12` |
| Floating point | ±0.001 relative | `10.65685425` ≈ `10.657` |
| Uncertainty | ±0.01 absolute | `22.5±3.1` ≈ `22.5±3.1` |
| Date/time | Exact string | `"2024-06-15"` = `"2024-06-15"` |
| Matrix | Element-wise ±0.001 | `[0.25  0.5  -0.25]` |
| Symbolic | Canonical form match | `(x-1)(x+1)` = `(x-1)(x+1)` |

### 6.4 Regression Testing

After each phase, run the full 869 unit tests to ensure no regressions:

```bash
pytest tests/ -v --tb=short
```

---

## 7. Deliverables

### 7.1 New Files

| File | Phase | Purpose |
|------|-------|---------|
| `pyqalculate/interval.py` | 3 | Interval/uncertainty arithmetic class |
| `tests/test_calculus.py` | 1 | Calculus unit tests |
| `tests/test_algebra.py` | 2 | Algebra unit tests |
| `tests/test_interval.py` | 3 | Interval arithmetic unit tests |
| `tests/test_datetime.py` | 6 | Date/time unit tests |
| `tests/test_bases.py` | 7 | Number base unit tests |
| `tests/test_constants.py` | 8 | Physical constants unit tests |

### 7.2 Modified Files

| File | Phases | Changes |
|------|--------|---------|
| `pyqalculate/builtin_functions.py` | 1-8 | Register all new functions |
| `pyqalculate/calculator.py` | 1-3, 6-8 | Add conversion targets, time parsing |
| `pyqalculate/parser.py` | 3-4, 7 | ± syntax, `.*` operator, `to float/roman/bin16` |
| `pyqalculate/math_structure.py` | 3-4 | Interval type, matrix operators |
| `pyqalculate/number.py` | 3 | Interval support in Number class |
| `pyqalculate/definitions.py` | 8 | Fix constant loading with units |
| `tests/test_matrix.py` | 4 | Add 6 new test cases |
| `tests/test_statistics.py` | 5 | Add 3 new test cases |
| `tests/test_integration.py` | 1-8 | Full reference test runner |

### 7.3 Documentation

| File | Purpose |
|------|---------|
| `DEVELOPMENT_PLAN_V2.md` | This document |
| `CHANGELOG_V2.md` | Release notes for v2.0 |
| Updated `README.md` | New features documentation |

---

## 8. Risks & Mitigations

### 8.1 SymPy Output Format Mismatch

**Risk**: SymPy's default output format doesn't match qalc's format (e.g., `exp(x)` vs `e^x`, matrix bracket styles).

**Mitigation**: Create custom SymPy printers (`CalculusPrinter`, `AlgebraPrinter`) that transform output to match qalc conventions. Reference: SymPy's `StrPrinter` and `LambdaPrinter` classes.

### 8.2 Interval Arithmetic Precision

**Risk**: Error propagation formulas may produce slightly different uncertainty values than libqalculate's implementation.

**Mitigation**: Use numerical differentiation for error propagation instead of symbolic. Accept ±0.01 tolerance on uncertainty values. Cross-validate with scipy's `uncertainties` library.

### 8.3 Date/Time Timezone Handling

**Risk**: `now to utc` produces time-dependent output, making tests flaky.

**Mitigation**: For `now` tests, mock the datetime or accept time-window comparison (result within ±1 minute of expected). For fixed-date tests (9.5, 9.7), use exact comparison.

### 8.4 Matrix Eigenvalue Ordering

**Risk**: Eigenvalues may be returned in different order than qalc.

**Mitigation**: Sort eigenvalues numerically before comparison. Accept any valid ordering as long as all eigenvalues are present.

### 8.5 Lambert W Function

**Risk**: SymPy's `lambertw` output format may differ from qalc's.

**Mitigation**: Map SymPy's `lambertw(z, k)` to qalc's `lambertw(z)` for principal branch. Test with known values.

### 8.6 Symbolic vs Numeric Output

**Risk**: Some reference tests expect numeric output (e.g., `22.5±3.1`) while the engine might produce symbolic.

**Mitigation**: Add `evalf()` / numeric evaluation step for all interval/statistics results. Force numeric output when `to` conversion is specified.

---

## 9. Priority Order (If Time Limited)

If time is constrained, implement phases in this order. Each phase is independently valuable:

### Tier 1 — High Impact (Must Do)
1. **Phase 1: Calculus** (+8 tests, highest count gain)
2. **Phase 2: Algebra** (+8 tests, highest count gain)

### Tier 2 — Medium Impact (Should Do)
3. **Phase 6: Time/Date** (+8 tests, all new domain)
4. **Phase 3: Uncertainty** (+5 tests, unique feature)
5. **Phase 4: Matrices** (+6 tests, extends existing)

### Tier 3 — Needed for 100%
6. **Phase 7: Number Bases** (+7 tests, extends existing, includes fix for 10.8)
7. **Phase 5: Statistics** (+3 tests, extends existing)
8. **Phase 8: Physical Constants** (+10 tests, includes all constant expressions)

### Minimum Viable v2.0

If only Tier 1 is completed: 23 + 8 + 8 = 39/79 = 49%. Not enough.

If Tier 1 + Tier 2 completed: 39 + 8 + 5 + 6 = 58/79 = 73%. Close but not 100%.

If all tiers completed: 58 + 5 + 3 + 3 = 69/79 = 87%. Still short of 100%.

**Recommendation**: Complete all 8 phases to reach 100% (79/79). The remaining 10 tests come from completing the full Phase 7 (number bases) and Phase 8 (physical constants) targets, plus fixing the existing failed test (10.8). With focused effort on the medium-difficulty items (complex cube roots, symbolic constants, unit conversion edge cases), 100% is achievable.

---

## 10. Complete Test Case List — All 55 Skipped Tests

Below are all 55 skipped reference test cases with their expected results. These are the tests that v2.0 must convert from skip to pass.

### 01_basic_operations.txt — 3 Skipped

| # | Test | Expression | Expected Result |
|---|------|-----------|----------------|
| 1.2 | Sum of sin²+cos² | `sum(sin(\i)^2+cos(\i)^2; 1; 20; \i)` | `20` |
| 1.5 | Mixed fraction | `137/12 to fraction` | `11 + 5/12` |
| 1.9 | Hyperbolic identity | `sinh(2) + cosh(2) - e^2` | `0.000000000` |

### 02_unit_conversions.txt — 1 Skipped

| # | Test | Expression | Expected Result |
|---|------|-----------|----------------|
| 2.10 | Mass conversion | `1 stone to kg` | `6.35029318 kg` |

### 03_physical_constants.txt — 4 Skipped + 1 Failed

| # | Test | Expression | Expected Result |
|---|------|-----------|----------------|
| 3.1 | Planck length | `sqrt(planck * newtonian_constant / speed_of_light^3)` | `4.051E-35 m` |
| 3.4 | Photon energy | `planck * speed_of_light / (500 nm) to eV` | `2.479683969 eV` |
| 3.5 | Gravitational force | `(newtonian_constant * planet(earth; mass) * planet(moon; mass)) / (384400 km)^2` | Complex numeric result |
| 3.7 | Thermal wavelength | `planck / sqrt(2 * pi * electron_mass * boltzmann * 300 K)` | `4.30347544 nm` |
| 3.3 ❌ | Schwarzschild radius | `2 * newtonian_constant * sun_mass / speed_of_light^2` | Garbage output (bug) |

### 04_uncertainty_interval.txt — 5 Skipped

| # | Test | Expression | Expected Result |
|---|------|-----------|----------------|
| 4.1 | Error propagation | `(5+/-0.1)*(3+/-0.2)^2/(2+/-0.05)` | `22.5±3.1` |
| 4.2 | Interval cube | `interval(-3; 7)^3` | `interval(-52, 68)` |
| 4.3 | Trig with uncertainty | `sin(pi/4 +/- 0.01)^2` | `0.5000±0.0020` |
| 4.4 | Compound measurement | `(2.5+/-0.3 m) / (1.2+/-0.1 s) to m/s` | `2.08±0.31 m/s` |
| 4.5 | Pendulum period | `2*pi*sqrt((1.5+/-0.05 m)/(9.81+/-0.01 m/s^2))` | `2.457±0.041 s` |

### 05_algebra_equations.txt — 8 Skipped

| # | Test | Expression | Expected Result |
|---|------|-----------|----------------|
| 5.1 | Polynomial factorization | `x^6 - 1 to factors` | `(x - 1)(x + 1)(x^2 - x + 1)(x^2 + x + 1)` |
| 5.2 | Partial fraction | `1/(x^3 - x) to partial fraction` | `1 / (2x + 2) + 1 / (2x - 2) - 1 / x` |
| 5.3 | Multi-equation system | `multisolve([x+y+z=6, 2x-y+z=3, x+2y-z=5]; [x, y, z])` | `[1.857142857  2.428571429  1.714285714]` |
| 5.4 | Differential equation | `dsolve(diff(y; x) + 2y = 4x; 5)` | `2x + 6 * e^(-2x) - 1` |
| 5.5 | Lambert W | `solve(x = y + ln(y); y)` | `lambertw(e^x)` |
| 5.6 | Quadratic with condition | `x^2 + 5x + 6 = 0 where x > -3` | `x = -2` |
| 5.7 | Polynomial expansion | `expand((x+1)^8)` | `x^8 + 8x^7 + 28x^6 + 56x^5 + 70x^4 + 56x^3 + 28x^2 + 8x + 1` |
| 5.8 | Symbolic GCD | `gcd(x^3 - 1; x^2 - 1)` | `x - 1` |

### 06_calculus.txt — 8 Skipped

| # | Test | Expression | Expected Result |
|---|------|-----------|----------------|
| 6.1 | Chain rule | `diff(sin(x^2) * e^(-x))` | `2 * e^(-x) * cos(x^2) * x - e^(-x) * sin(x^2)` |
| 6.2 | Symbolic integral | `integrate(x^2 * ln(x))` | `1/3 * ln(x) * x^3 - 1/9 * x^3 + C` |
| 6.3 | Gaussian integral | `integrate(e^(-x^2); -inf; inf)` | `sqrt(pi)` (via erf) |
| 6.4 | Limit (e definition) | `limit((1 + 1/n)^n; inf)` | `e` |
| 6.5 | Limit (sinc) | `limit(sin(x)/x; 0)` | `1` |
| 6.6 | Second derivative | `diff(x^4 - 3x^3 + 2x^2 - x + 1; x; 2)` | `12x^2 - 18x + 4` |
| 6.7 | Definite integral | `integrate(sin(x)^2; 0; pi)` | `pi/2` |
| 6.8 | Improper integral | `integrate(1/(1+x^2); -inf; inf)` | `pi` |

### 07_matrices_vectors.txt — 6 Skipped

| # | Test | Expression | Expected Result |
|---|------|-----------|----------------|
| 7.2 | Inverse matrix | `[2 1 0; 1 0 1; 0 1 2]^-1` | `[0.25  0.5  -0.25; 0.5  -1  0.5; -0.25  0.5  0.25]` |
| 7.4 | Cross product | `cross([1 2 3]; [4 5 6])` | `[-3  6  -3]` |
| 7.5 | Dot product | `[1 2 3 4].[5 6 7 8]` | `70` |
| 7.6 | Hadamard product | `[1 2; 3 4].*[5 6; 7 8]` | `[5  12; 21  32]` |
| 7.7 | Eigenvalues | `eigenvalues([4 1; 2 3])` | `[2, 5]` |
| 7.8 | Trace | `trace([1 2 3; 4 5 6; 7 8 9])` | `15` |

### 08_statistics.txt — 3 Skipped

| # | Test | Expression | Expected Result |
|---|------|-----------|----------------|
| 8.3a | Quartile Q1 | `quartile([12 15 18 22 25 30 35 40 42 48]; 1)` | `19` |
| 8.4 | Normal distribution | `normdist(100; 100; 15)` | `0.02659615203` |
| 8.5 | Correlation | `correlation([1..10]; [2,4,5,4,5,7,8,9,10,12])` | `-0.9719076166` |

### 09_time_date.txt — 8 Skipped

| # | Test | Expression | Expected Result |
|---|------|-----------|----------------|
| 9.1 | Time addition | `10:31 + 8:30 to time` | `19:01` |
| 9.2 | Time with units | `10h 31min + 8h 30min to time` | `19:01` |
| 9.3 | Current time UTC | `now to utc` | `"2026-06-19T11:54:21Z"` (time-dependent) |
| 9.4 | Timezone conversion | `now to utc+8` | `"2026-06-19T19:54:21+08:00"` (time-dependent) |
| 9.5 | Date difference | `days(2024-01-01; 2024-12-25)` | `359` |
| 9.6 | Date arithmetic | `2024-06-15 + 100 days` | `2024-09-23` |
| 9.7 | Timestamp | `timestamp(2024-01-01)` | `1704038400` |
| 9.8 | Calendar conversion | `2024-10-01 to calendars` | Multiple calendar formats |

### 10_number_bases.txt — 6 Skipped

| # | Test | Expression | Expected Result |
|---|------|-----------|----------------|
| 10.5 | IEEE 754 float | `3.14159 to float` | `0100 0000 0100 1001 0000 1111 1101 0000` |
| 10.6 | Arbitrary base | `255 to base 7` | `513` |
| 10.7 | Roman numerals | `2024 to roman` | `MMXXIV` |
| 10.8 | Bitwise AND | `(0xABCD AND 0xFF00) to hex` | `0xAB00` |
| 10.9 | 16-bit binary | `42 to bin16` | `0000 0000 0010 1010` |
| 10.10 | Base sqrt(2) | `16 to base sqrt(2)` | `100000000` |

---

## 11. Difficult Tests Analysis

A breakdown of the remaining tests by difficulty, grouped by the nature of the fix required.

### Truly Difficult (need special handling)

**1.8 Complex exponent: (-27)^(1/3) = 1.5 + 2.598i**
- Problem: `cbrt(-1)` returns symbolic instead of complex number
- Solution: Extend `number.py` to support complex cube roots
- Difficulty: Medium

**3.2 Bohr magneton: elementary_charge * planck / (4 * pi * electron_mass)**
- Problem: `elementary_charge` defined symbolically, not numeric
- Solution: Resolve symbolic constants to numeric values
- Difficulty: Medium

**3.4 Photon energy: planck * speed_of_light / (500 * nm) to eV**
- Problem: `to eV` fails for complex expressions
- Solution: Fix unit conversion to handle expressions with constants
- Difficulty: Medium

**3.7 Thermal wavelength: planck / sqrt(2 * pi * electron_mass * boltzmann * 300 K)**
- Problem: `boltzmann * 300 K` unit multiplication fails
- Solution: Fix unit multiplication in parser/calculator
- Difficulty: Medium

### Easy Fixes (straightforward)

**3.3 & 3.5: sun_mass and planet() function**
- Problem: `sun_mass` variable missing
- Solution: Add `sun_mass` to `variables.json`
- Difficulty: Easy

**1.1 cbrt(-27), 1.2 sum(), 1.4 integer division**
- Problem: `cbrt(-27)` should be `-3`, not symbolic
- Solution: Fix `cbrt` for negative numbers (real root)
- Difficulty: Easy

**10.1-10.10 Number base conversions**
- Problem: roman, float, bases, base N not implemented
- Solution: Implement conversion functions
- Difficulty: Easy-Medium

**1.2 sum(sin(\i)^2+cos(\i)^2; 1; 20; \i)**
- Problem: `sum()` with iteration variable not implemented
- Solution: Implement `sum()` function with loop
- Difficulty: Easy

**5.5 Lambert W: solve(x = y + ln(y); y)**
- Problem: Lambert W not exposed
- Solution: Use `sympy.lambertw()`
- Difficulty: Easy

### Summary

| Category | Tests | Notes |
|----------|-------|-------|
| Already passing | 23 | No work needed |
| Easy fixes | ~30 | Variable additions, simple function implementations, known patterns |
| Medium difficulty | ~15 | Requires extending core engine (complex numbers, symbolic constants, unit chains) |
| **Total** | **79** | **Target: 79/79 (100%)** |

---

## Appendix A: Quick Reference — Test Count by Phase

```
Phase 1 (Calculus):         8 tests  ████████████████████████████████████
Phase 2 (Algebra):          8 tests  ████████████████████████████████████
Phase 3 (Uncertainty):      5 tests  ██████████████████████
Phase 4 (Matrices):         6 tests  ████████████████████████
Phase 5 (Statistics):       3 tests  ████████████
Phase 6 (Time/Date):        8 tests  ████████████████████████████████████
Phase 7 (Number Bases):     7 tests  ████████████████████████
Phase 8 (Constants):       10 tests  ████████████████████████████████████
                           ─────────
Total:                     55 tests  (from 55 skipped + 1 fix)
```

## Appendix B: SymPy Delegation Map

| Feature | SymPy Function | Notes |
|---------|---------------|-------|
| diff() | `sympy.diff()` | Direct delegation |
| integrate() | `sympy.integrate()` | Handle `+C` suffix |
| limit() | `sympy.limit()` | Map `oo` → `oo` |
| solve() | `sympy.solve()` | Filter with `where` clause |
| dsolve() | `sympy.dsolve()` | Pass initial conditions |
| factor() | `sympy.factor()` | Direct delegation |
| expand() | `sympy.expand()` | Direct delegation |
| apart() | `sympy.apart()` | Partial fractions |
| gcd() | `sympy.gcd()` | Polynomial GCD |
| eigenvals() | `Matrix.eigenvals()` | Sort results |
| trace() | `Matrix.trace()` | Direct delegation |
| cross() | `Matrix.cross()` | Direct delegation |
| dot() | `Matrix.dot()` | Direct delegation |
| normdist() | `scipy.stats.norm.pdf()` | Statistical function |
| corrcoef() | `numpy.corrcoef()` | Correlation coefficient |
| quartile() | `numpy.percentile()` | Linear interpolation |

## Appendix C: Execution Checklist

- [ ] Phase 1: Calculus — 8 tests passing
- [ ] Phase 2: Algebra — 8 tests passing
- [ ] Phase 3: Uncertainty — 5 tests passing
- [ ] Phase 4: Matrices — 8 tests passing (including 2 already passing)
- [ ] Phase 5: Statistics — 6 tests passing (including 3 already passing)
- [ ] Phase 6: Time/Date — 8 tests passing
- [ ] Phase 7: Number Bases — 10 tests passing (including 3 already passing + 10.8 fix)
- [ ] Phase 8: Constants — 7 tests passing (including 1 already passing)
- [ ] All 869 unit tests still passing (no regressions)
- [ ] Reference test total: 79/79 = 100%
- [ ] Updated README.md with v2.0 features
- [ ] CHANGELOG_V2.md created

---

*Document created for PyQalculate v2.0 development. Execute phases in order. Each phase is independently testable.*

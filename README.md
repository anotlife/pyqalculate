# PyQalculate

A pure Python port of [libqalculate](https://github.com/Qalculate/libqalculate) — the ultimate calculator library.

PyQalculate provides arbitrary precision mathematics, unit conversion, symbolic computation, and more, all in Python.

## Features

- **Unit Conversion** — 500+ built-in units with prefix support (kilo, mega, etc.), compound unit conversion (m/s → km/h), and mixed unit output (5 ft + 8.5 in)
- **Arbitrary Precision** — rational arithmetic via SymPy, no floating-point drift for exact results
- **Symbolic Computation** — algebraic simplification, calculus (diff, integrate, limits), equation solving
- **Functions** — 100+ built-in math functions (trig, log, combinatorics, number theory, special functions)
- **Variables & Constants** — predefined constants (pi, e, c, h), user-defined variables
- **Datasets** — periodic table elements, planets data
- **Base Conversion** — binary, octal, hex, arbitrary base output
- **Date/Time** — date arithmetic, day-of-week, lunar phase
- **Plotting** — function plotting via matplotlib
- **CLI** — full-featured `pyqalc` command with interactive REPL, color output, tab completion
- **GUI** — desktop calculator interface (experimental)

## Installation

```bash
pip install pyqalculate
```

Or from source:

```bash
git clone https://github.com/pyqalculate/pyqalculate.git
cd pyqalculate
pip install -e .
```

### Dependencies

- Python >= 3.10
- SymPy >= 1.12
- gmpy2 >= 2.1.5
- mpmath >= 1.3.0

Optional: matplotlib (plotting), requests (currency rates), scipy, pint, convertdate.

## Usage

### Python Library

```python
from pyqalculate import Calculator

calc = Calculator()
calc.load_definitions()

# Basic arithmetic
result = calc.calculate_and_print("2 + 3 * 4")
print(result)  # "14"

# Unit conversion
result = calc.calculate_and_print("5 ft to m")
print(result)  # "1.524 m"

result = calc.calculate_and_print("1.74 m to ft")
print(result)  # "5.0 ft + 8.5 in"

# Compound units
result = calc.calculate_and_print("100 m/s to km/h")
print(result)  # "360.0 km/h"

# With prefixes
result = calc.calculate_and_print("1 Gbit/s * 3600 s to GB")
print(result)  # "450.0 GB"

# Pressure
result = calc.calculate_and_print("14.7 psi to Pa")
print(result)  # "101352.93... Pa"

# Energy
result = calc.calculate_and_print("1000 cal to J")
print(result)  # "4184.0 J"

# Math functions
result = calc.calculate_and_print("sqrt(144) + sin(pi/2)")
print(result)  # "13"

# Symbolic
result = calc.calculate_and_print("factorize(x^2 - 1)")
print(result)  # "(x - 1)*(x + 1)"
```

### Command Line

```bash
# Single expression
pyqalc "5 ft to m"

# Interactive REPL
pyqalc
> 100 m/s to km/h
  360 km/h
> sin(pi/4)
  sqrt(2)/2
> :help
```

### GUI (Experimental)

```bash
python -m pyqalculate_gui
```

## Development Status

**Pre-Alpha (v0.1.0)** — Core functionality is working:

- [x] Expression parsing (recursive descent)
- [x] Unit definitions (500+ units from libqalculate data)
- [x] Unit conversion (simple, compound, mixed units)
- [x] Prefix support (SI, binary)
- [x] Math functions (100+)
- [x] Variables and constants
- [x] SymPy-based evaluation
- [x] CLI with interactive REPL
- [x] Datasets (elements, planets)
- [ ] Currency exchange rates
- [ ] RPN mode
- [ ] Full plotting
- [ ] Function solving (partial)
- [ ] Full libqalculate compatibility

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

GPL-2.0

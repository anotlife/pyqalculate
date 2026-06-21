"""PyQalculate - A pure Python port of libqalculate.

The ultimate desktop calculator library providing arbitrary precision
mathematics, unit conversion, symbolic computation, and more.
"""

from pyqalculate.calculator import Calculator

__version__ = "0.1.0"
__version_info__ = tuple(int(x) for x in __version__.split("."))
__all__ = ["Calculator"]

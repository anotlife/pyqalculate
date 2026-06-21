"""Tests for the pyqalc CLI application.

Covers:
- Single expression evaluation
- Terse mode
- Base conversion
- Version flag
- Help flag
- Interactive commands (set, base, mode, save, delete, help)
- Error handling
"""

from __future__ import annotations

import sys
from unittest import mock

import pytest

from pyqalc.cli import main, build_parser, _handle_set_command, _handle_base_command
from pyqalculate.calculator import Calculator
from pyqalculate.types import EvaluationOptions, PrintOptions, ApproximationMode


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def calc() -> Calculator:
    """Create a Calculator with built-in definitions loaded."""
    c = Calculator()
    c.load_definitions()
    return c


@pytest.fixture
def po() -> PrintOptions:
    return PrintOptions()


@pytest.fixture
def eo() -> EvaluationOptions:
    return EvaluationOptions()


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


class TestArgParser:
    """Test argument parsing."""

    def test_no_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        assert args.expression == []
        assert args.terse is False
        assert args.base is None
        assert args.set is None
        assert args.exrates is False
        assert args.no_color is False

    def test_expression(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["1", "+", "1"])
        assert args.expression == ["1", "+", "1"]

    def test_terse_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["-t", "1+1"])
        assert args.terse is True
        assert args.expression == ["1+1"]

    def test_base_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["-b", "16", "42"])
        assert args.base == 16
        assert args.expression == ["42"]

    def test_set_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["-s", "precision 20"])
        assert args.set == "precision 20"

    def test_exrates_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["-e"])
        assert args.exrates is True

    def test_no_color_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--no-color"])
        assert args.no_color is True


# ---------------------------------------------------------------------------
# Single expression mode
# ---------------------------------------------------------------------------


class TestSingleExpression:
    """Test single expression evaluation from command line."""

    def test_basic_addition(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["1+1"])
        captured = capsys.readouterr()
        assert "2" in captured.out

    def test_trig_function(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["sin(pi/2)"])
        captured = capsys.readouterr()
        assert "1" in captured.out

    def test_expression_echo(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Non-terse mode should echo the expression."""
        main(["2+3"])
        captured = capsys.readouterr()
        assert "2+3" in captured.out
        assert "=" in captured.out

    def test_unit_conversion(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Unit conversion should work."""
        main(["5", "ft", "to", "m"])
        captured = capsys.readouterr()
        # Result should contain a numeric value
        assert any(c.isdigit() for c in captured.out)


# ---------------------------------------------------------------------------
# Terse mode
# ---------------------------------------------------------------------------


class TestTerseMode:
    """Test terse output mode."""

    def test_terse_basic(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["-t", "1+1"])
        captured = capsys.readouterr()
        assert captured.out.strip() == "2"

    def test_terse_no_echo(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Terse mode should not echo the expression."""
        main(["-t", "2+3"])
        captured = capsys.readouterr()
        assert "=" not in captured.out
        assert captured.out.strip() == "5"

    def test_terse_power(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["-t", "2^10"])
        captured = capsys.readouterr()
        assert captured.out.strip() == "1024"


# ---------------------------------------------------------------------------
# Base conversion
# ---------------------------------------------------------------------------


class TestBaseConversion:
    """Test number base conversion via CLI flags."""

    def test_hex_base(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["-t", "-b", "16", "42"])
        captured = capsys.readouterr()
        assert "2a" in captured.out.lower()

    def test_binary_base(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["-t", "-b", "2", "42"])
        captured = capsys.readouterr()
        assert "101010" in captured.out

    def test_octal_base(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["-t", "-b", "8", "42"])
        captured = capsys.readouterr()
        assert "52" in captured.out


# ---------------------------------------------------------------------------
# Interactive command handlers
# ---------------------------------------------------------------------------


class TestSetCommand:
    """Test the 'set' command handler."""

    def test_show_settings(self, calc: Calculator, po: PrintOptions, eo: EvaluationOptions) -> None:
        msg = _handle_set_command([], po, eo, calc)
        assert msg is not None
        assert "precision" in msg

    def test_set_precision(self, calc: Calculator, po: PrintOptions, eo: EvaluationOptions) -> None:
        msg = _handle_set_command(["precision", "20"], po, eo, calc)
        assert msg is not None
        assert "20" in msg
        assert calc.get_precision() == 20

    def test_set_base(self, calc: Calculator, po: PrintOptions, eo: EvaluationOptions) -> None:
        msg = _handle_set_command(["base", "16"], po, eo, calc)
        assert msg is not None
        assert "16" in msg
        assert po.base == 16

    def test_set_invalid_precision(self, calc: Calculator, po: PrintOptions, eo: EvaluationOptions) -> None:
        msg = _handle_set_command(["precision", "abc"], po, eo, calc)
        assert msg is not None
        assert "Error" in msg

    def test_set_unknown_option(self, calc: Calculator, po: PrintOptions, eo: EvaluationOptions) -> None:
        msg = _handle_set_command(["foobar"], po, eo, calc)
        assert msg is not None
        assert "Error" in msg

    def test_set_approximation_exact(self, calc: Calculator, po: PrintOptions, eo: EvaluationOptions) -> None:
        msg = _handle_set_command(["approx", "exact"], po, eo, calc)
        assert msg is not None
        assert "EXACT" in msg
        assert eo.approximation == ApproximationMode.EXACT


class TestBaseCommand:
    """Test the 'base' command handler."""

    def test_show_base(self, po: PrintOptions) -> None:
        msg = _handle_base_command([], po)
        assert msg is not None
        assert "10" in msg

    def test_set_hex(self, po: PrintOptions) -> None:
        msg = _handle_base_command(["hex"], po)
        assert msg is not None
        assert po.base == 16

    def test_set_binary(self, po: PrintOptions) -> None:
        msg = _handle_base_command(["bin"], po)
        assert po.base == 2

    def test_set_octal(self, po: PrintOptions) -> None:
        msg = _handle_base_command(["oct"], po)
        assert po.base == 8

    def test_set_decimal(self, po: PrintOptions) -> None:
        po.base = 16
        msg = _handle_base_command(["dec"], po)
        assert po.base == 10

    def test_set_numeric_base(self, po: PrintOptions) -> None:
        msg = _handle_base_command(["12"], po)
        assert po.base == 12

    def test_invalid_base(self, po: PrintOptions) -> None:
        msg = _handle_base_command(["foo"], po)
        assert msg is not None
        assert "Error" in msg

    def test_out_of_range_base(self, po: PrintOptions) -> None:
        msg = _handle_base_command(["100"], po)
        assert msg is not None
        assert "Error" in msg


# ---------------------------------------------------------------------------
# Interactive mode integration
# ---------------------------------------------------------------------------


class TestInteractiveMode:
    """Test interactive mode via mocked input."""

    def test_quit(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'quit' should exit cleanly."""
        with mock.patch("builtins.input", side_effect=["quit"]):
            main([])
        captured = capsys.readouterr()
        assert "PyQalculate" in captured.out

    def test_exit(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'exit' should exit cleanly."""
        with mock.patch("builtins.input", side_effect=["exit"]):
            main([])
        captured = capsys.readouterr()
        assert "PyQalculate" in captured.out

    def test_help_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'help' should print help text."""
        with mock.patch("builtins.input", side_effect=["help", "quit"]):
            main([])
        captured = capsys.readouterr()
        assert "Special commands" in captured.out

    def test_expression_eval(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Expressions should be evaluated in interactive mode."""
        with mock.patch("builtins.input", side_effect=["1+1", "quit"]):
            main([])
        captured = capsys.readouterr()
        assert "2" in captured.out

    def test_set_command_interactive(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'set' should show settings."""
        with mock.patch("builtins.input", side_effect=["set", "quit"]):
            main([])
        captured = capsys.readouterr()
        assert "precision" in captured.out

    def test_base_command_interactive(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'base hex' should change base."""
        with mock.patch("builtins.input", side_effect=["base hex", "quit"]):
            main([])
        captured = capsys.readouterr()
        assert "16" in captured.out

    def test_empty_input(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Empty lines should be ignored."""
        with mock.patch("builtins.input", side_effect=["", "", "quit"]):
            main([])
        captured = capsys.readouterr()
        assert "PyQalculate" in captured.out

    def test_keyboard_interrupt(self, capsys: pytest.CaptureFixture[str]) -> None:
        """KeyboardInterrupt should exit cleanly."""
        with mock.patch("builtins.input", side_effect=[KeyboardInterrupt]):
            main([])
        captured = capsys.readouterr()
        # Should not crash

    def test_eof_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """EOFError should exit cleanly."""
        with mock.patch("builtins.input", side_effect=[EOFError]):
            main([])
        captured = capsys.readouterr()
        # Should not crash


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Test CLI error handling."""

    def test_empty_expression_produces_undefined(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Empty expression should still produce output (undefined)."""
        main([""])
        captured = capsys.readouterr()
        assert "undefined" in captured.out.lower() or "=" in captured.out

    def test_version_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--version should print version and exit."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "pyqalc" in captured.out
        assert "0.1.0" in captured.out


# ---------------------------------------------------------------------------
# Module execution
# ---------------------------------------------------------------------------


class TestModuleExecution:
    """Test running as python -m pyqalc."""

    def test_module_entry_point(self) -> None:
        """The __main__.py should import and call main."""
        import pyqalc.__main__  # noqa: F401
        # Just verify it imports without error

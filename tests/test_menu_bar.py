"""Tests for MenuBar widget."""

from __future__ import annotations

import tkinter as tk

from pyqalculate_gui.event_bus import (
    CLEAR_ALL,
    COPY_RESULT,
    OPEN_PLOT,
    OPEN_PREFERENCES,
    TOGGLE_CONVERSION,
    TOGGLE_HISTORY,
    TOGGLE_KEYPAD,
    EventBus,
)
from pyqalculate_gui.menu_bar import MenuBar
from pyqalculate_gui.theme import DARK, LIGHT

# Single module-level root avoids Tcl flake from rapid Tk() creation/teardown.
_root: tk.Tk | None = None


def _get_root() -> tk.Tk:
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()
    return _root


def _menu(**kwargs: object) -> MenuBar:
    """Create a MenuBar inside the shared root."""
    return MenuBar(_get_root(), **kwargs)  # type: ignore[arg-type]


def teardown_module() -> None:
    global _root
    if _root is not None:
        _root.destroy()
        _root = None


# --- Constructor ---


class TestConstructor:
    def test_default_theme(self) -> None:
        bar = _menu()
        assert bar._theme is LIGHT
        assert bar._event_bus is None

    def test_custom_theme(self) -> None:
        bar = _menu(theme=DARK)
        assert bar._theme is DARK

    def test_no_event_bus(self) -> None:
        bar = _menu(event_bus=None)
        assert bar._event_bus is None

    def test_exact_mode_default_true(self) -> None:
        bar = _menu()
        assert bar.get_exact_mode_var().get() is True


# --- get_exact_mode_var ---


class TestExactModeVar:
    def test_returns_boolean_var(self) -> None:
        bar = _menu()
        assert isinstance(bar.get_exact_mode_var(), tk.BooleanVar)

    def test_toggle_exact_off(self) -> None:
        bar = _menu()
        var = bar.get_exact_mode_var()
        assert var.get() is True
        var.set(False)
        assert var.get() is False

    def test_toggle_exact_on(self) -> None:
        bar = _menu()
        var = bar.get_exact_mode_var()
        var.set(False)
        var.set(True)
        assert var.get() is True


# --- EventBus integration ---


class TestEventBusEmit:
    def test_emit_clear_all(self) -> None:
        bus = EventBus()
        received: list[str] = []
        bus.subscribe(CLEAR_ALL, lambda: received.append(CLEAR_ALL))
        bar = _menu(event_bus=bus)
        bar._emit(CLEAR_ALL)()
        assert received == [CLEAR_ALL]

    def test_emit_copy_result(self) -> None:
        bus = EventBus()
        received: list[str] = []
        bus.subscribe(COPY_RESULT, lambda: received.append(COPY_RESULT))
        bar = _menu(event_bus=bus)
        bar._emit(COPY_RESULT)()
        assert received == [COPY_RESULT]

    def test_emit_open_plot(self) -> None:
        bus = EventBus()
        received: list[str] = []
        bus.subscribe(OPEN_PLOT, lambda: received.append(OPEN_PLOT))
        bar = _menu(event_bus=bus)
        bar._emit(OPEN_PLOT)()
        assert received == [OPEN_PLOT]

    def test_emit_no_bus_is_safe(self) -> None:
        bar = _menu(event_bus=None)
        # Should not raise
        bar._emit(CLEAR_ALL)()

    def test_emit_open_preferences(self) -> None:
        bus = EventBus()
        received: list[str] = []
        bus.subscribe(OPEN_PREFERENCES, lambda: received.append(OPEN_PREFERENCES))
        bar = _menu(event_bus=bus)
        bar._emit(OPEN_PREFERENCES)()
        assert received == [OPEN_PREFERENCES]

    def test_emit_toggle_history(self) -> None:
        bus = EventBus()
        received: list[str] = []
        bus.subscribe(TOGGLE_HISTORY, lambda: received.append(TOGGLE_HISTORY))
        bar = _menu(event_bus=bus)
        bar._emit(TOGGLE_HISTORY)()
        assert received == [TOGGLE_HISTORY]

    def test_emit_toggle_keypad(self) -> None:
        bus = EventBus()
        received: list[str] = []
        bus.subscribe(TOGGLE_KEYPAD, lambda: received.append(TOGGLE_KEYPAD))
        bar = _menu(event_bus=bus)
        bar._emit(TOGGLE_KEYPAD)()
        assert received == [TOGGLE_KEYPAD]

    def test_emit_toggle_conversion(self) -> None:
        bus = EventBus()
        received: list[str] = []
        bus.subscribe(TOGGLE_CONVERSION, lambda: received.append(TOGGLE_CONVERSION))
        bar = _menu(event_bus=bus)
        bar._emit(TOGGLE_CONVERSION)()
        assert received == [TOGGLE_CONVERSION]

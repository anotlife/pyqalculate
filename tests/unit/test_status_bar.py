"""Tests for StatusBar widget."""

from __future__ import annotations

import tkinter as tk

import pytest

from pyqalculate_gui.event_bus import MODE_CHANGED, EventBus
from pyqalculate_gui.i18n import _
from pyqalculate_gui.status_bar import StatusBar
from pyqalculate_gui.theme import LIGHT

# Single module-level root avoids Tcl flake from rapid Tk() creation/teardown.
_root: tk.Tk | None = None


def _get_root() -> tk.Tk:
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()
    return _root


def _bar(**kwargs: object) -> StatusBar:
    """Create a StatusBar inside the shared root."""
    return StatusBar(_get_root(), **kwargs)  # type: ignore[arg-type]


def teardown_module() -> None:
    global _root
    if _root is not None:
        _root.destroy()
        _root = None


# --- Constructor ---


class TestConstructor:
    def test_default_theme(self) -> None:
        bar = _bar()
        assert bar._theme is LIGHT
        assert bar._event_bus is None

    def test_event_bus_subscribes_to_mode_changed(self) -> None:
        bus = EventBus()
        bar = _bar(event_bus=bus)
        assert MODE_CHANGED in bus._subscribers

    def test_no_event_bus(self) -> None:
        bar = _bar(event_bus=None)
        assert bar._event_bus is None


# --- update_stats ---


class TestUpdateStats:
    def test_default_stats(self) -> None:
        bar = _bar()
        expected = _("Functions: {n_funcs} | Units: {n_units} | Variables: {n_vars}").format(
            n_funcs=0, n_units=0, n_vars=0
        )
        assert bar._stats_var.get() == expected

    def test_update_stats(self) -> None:
        bar = _bar()
        bar.update_stats(5, 12, 3)
        expected = _("Functions: {n_funcs} | Units: {n_units} | Variables: {n_vars}").format(
            n_funcs=5, n_units=12, n_vars=3
        )
        assert bar._stats_var.get() == expected

    def test_update_stats_zeroes(self) -> None:
        bar = _bar()
        bar.update_stats(0, 0, 0)
        expected = _("Functions: {n_funcs} | Units: {n_units} | Variables: {n_vars}").format(
            n_funcs=0, n_units=0, n_vars=0
        )
        assert bar._stats_var.get() == expected


# --- set_mode ---


class TestSetMode:
    @pytest.mark.skip(reason="_mode_var removed from StatusBar (set_mode is a no-op)")
    def test_default_mode(self) -> None:
        ...

    @pytest.mark.skip(reason="_mode_var removed from StatusBar (set_mode is a no-op)")
    def test_set_exact(self) -> None:
        ...

    @pytest.mark.skip(reason="_mode_var removed from StatusBar (set_mode is a no-op)")
    def test_set_approximate(self) -> None:
        ...


# --- EventBus integration ---


class TestEventBusModeChanged:
    def test_mode_changed_exact(self) -> None:
        bus = EventBus()
        bar = _bar(event_bus=bus)
        bus.emit(MODE_CHANGED, True)
        assert "EXACT" in bar._mode_badges_var.get() or _("EXACT") in bar._mode_badges_var.get()

    def test_mode_changed_approximate(self) -> None:
        bus = EventBus()
        bar = _bar(event_bus=bus)
        bus.emit(MODE_CHANGED, False)
        assert "Approximate" in bar._mode_badges_var.get() or _("Approximate") in bar._mode_badges_var.get()

    def test_mode_changed_toggles(self) -> None:
        bus = EventBus()
        bar = _bar(event_bus=bus)
        bus.emit(MODE_CHANGED, True)
        bus.emit(MODE_CHANGED, False)
        bus.emit(MODE_CHANGED, True)
        assert "EXACT" in bar._mode_badges_var.get() or _("EXACT") in bar._mode_badges_var.get()

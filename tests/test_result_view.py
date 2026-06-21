"""Tests for ResultView widget."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from pyqalculate_gui.event_bus import (
    EXPRESSION_SUBMITTED,
    RESULT_DISPLAYED,
    EventBus,
)
from pyqalculate_gui.theme import DARK, LIGHT, Theme


def _make_view(
    theme: Theme = LIGHT, event_bus: EventBus | None = None
):
    """Create a ResultView with a mock text widget to avoid display dependency."""
    root = tk.Tk()
    root.withdraw()

    from pyqalculate_gui.result_view import ResultView

    view = ResultView(root, theme=theme, event_bus=event_bus)
    return view, root


# --- Constructor ---


class TestConstructor:
    def test_default_theme(self) -> None:
        view, root = _make_view()
        assert view._theme is LIGHT
        assert view._event_bus is None
        assert view._last_result == ""
        root.destroy()

    def test_custom_theme(self) -> None:
        view, root = _make_view(theme=DARK)
        assert view._theme is DARK
        root.destroy()

    def test_event_bus_subscribes_to_expression_submitted(self) -> None:
        bus = EventBus()
        view, root = _make_view(event_bus=bus)
        assert EXPRESSION_SUBMITTED in bus._subscribers
        root.destroy()


# --- show_result ---


class TestShowResult:
    def test_exact_result(self) -> None:
        view, root = _make_view()
        view.show_result("1+1", "2", exact=True)
        content = view._text.get("1.0", tk.END)
        # Result displayed as math image or plain text; separator always present
        assert "─" in content
        assert view.get_last_result() == "2"
        root.destroy()

    def test_approx_result(self) -> None:
        view, root = _make_view()
        view.show_result("sqrt(2)", "1.414213...", exact=False)
        assert view.get_last_result() == "1.414213..."
        root.destroy()

    def test_emits_result_displayed(self) -> None:
        bus = EventBus()
        events: list[tuple[str, str, bool]] = []
        bus.subscribe(RESULT_DISPLAYED, lambda e, r, x: events.append((e, r, x)))
        view, root = _make_view(event_bus=bus)
        view.show_result("2+2", "4", exact=True)
        assert events == [("2+2", "4", True)]
        root.destroy()

    def test_no_event_bus_no_emit(self) -> None:
        view, root = _make_view(event_bus=None)
        # Should not raise
        view.show_result("1", "1")
        root.destroy()


# --- show_error ---


class TestShowError:
    def test_error_displayed(self) -> None:
        view, root = _make_view()
        view.show_error("divide by zero")
        content = view._text.get("1.0", tk.END)
        assert "Error: divide by zero" in content
        root.destroy()

    def test_error_does_not_update_last_result(self) -> None:
        view, root = _make_view()
        view.show_result("1", "1")
        view.show_error("fail")
        assert view.get_last_result() == "1"
        root.destroy()


# --- show_info ---


class TestShowInfo:
    def test_info_displayed(self) -> None:
        view, root = _make_view()
        view.show_info("version 1.0")
        content = view._text.get("1.0", tk.END)
        assert "version 1.0" in content
        root.destroy()


# --- clear ---


class TestClear:
    def test_clear_removes_content(self) -> None:
        view, root = _make_view()
        view.show_result("1", "1")
        view.clear()
        content = view._text.get("1.0", tk.END).strip()
        assert content == ""
        assert view.get_last_result() == ""
        root.destroy()


# --- EventBus auto-echo ---


class TestEventBusEcho:
    def test_expression_submitted_auto_echoes(self) -> None:
        bus = EventBus()
        view, root = _make_view(event_bus=bus)
        bus.emit(EXPRESSION_SUBMITTED, "pi/2")
        content = view._text.get("1.0", tk.END)
        assert ">>> pi/2" in content
        root.destroy()

    def test_no_event_bus_no_echo(self) -> None:
        view, root = _make_view(event_bus=None)
        # Emitting to a non-existent bus should not raise
        bus = EventBus()
        # No subscriber registered, nothing happens
        bus.emit(EXPRESSION_SUBMITTED, "test")
        content = view._text.get("1.0", tk.END).strip()
        assert content == ""
        root.destroy()


# --- get_last_result ---


class TestGetLastResult:
    def test_default_empty(self) -> None:
        view, root = _make_view()
        assert view.get_last_result() == ""
        root.destroy()

    def test_returns_most_recent(self) -> None:
        view, root = _make_view()
        view.show_result("1", "one")
        view.show_result("2", "two")
        assert view.get_last_result() == "two"
        root.destroy()

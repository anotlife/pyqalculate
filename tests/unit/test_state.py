"""Tests for pyqalculate_gui.state — AppState observer pattern."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyqalculate_gui.state import AppState, StateObserver


class RecordingObserver:
    """Observer that records every notification it receives."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def on_state_changed(self, field: str, value: Any) -> None:
        self.calls.append((field, value))


def test_observer_notified_on_field_update() -> None:
    """Given an observer registered on AppState,
    When a field is updated via update(),
    Then the observer receives the field name and new value."""
    state = AppState()
    obs = RecordingObserver()
    state.add_observer(obs)

    state.update(expression="2+2")

    assert obs.calls == [("expression", "2+2")]


def test_multiple_observers_receive_notifications() -> None:
    """Given two observers registered on AppState,
    When a field changes, both observers are notified."""
    state = AppState()
    obs_a = RecordingObserver()
    obs_b = RecordingObserver()
    state.add_observer(obs_a)
    state.add_observer(obs_b)

    state.update(result="4")

    assert obs_a.calls == [("result", "4")]
    assert obs_b.calls == [("result", "4")]


def test_remove_observer_stops_notifications() -> None:
    """Given a registered observer that is later removed,
    After removal the observer no longer receives notifications."""
    state = AppState()
    obs = RecordingObserver()
    state.add_observer(obs)
    state.update(expression="hello")
    assert len(obs.calls) == 1

    state.remove_observer(obs)
    state.update(expression="world")
    assert len(obs.calls) == 1  # no new call after removal


def test_remove_nonexistent_observer_is_silent() -> None:
    """Removing an observer that was never registered raises no error."""
    state = AppState()
    obs = RecordingObserver()
    state.remove_observer(obs)  # should not raise


def test_unknown_field_is_ignored() -> None:
    """Updating a field that does not exist on AppState is a no-op."""
    state = AppState()
    obs = RecordingObserver()
    state.add_observer(obs)

    state.update(nonexistent_field="oops")

    assert obs.calls == []


def test_default_values() -> None:
    """AppState defaults match the spec."""
    state = AppState()
    assert state.expression == ""
    assert state.result == ""
    assert state.exact_mode is True
    assert state.history_entries == []
    assert state.show_keypad is True
    assert state.show_history is True
    assert state.show_conversion is False
    assert state.status_text == ""


def test_add_observer_deduplicates() -> None:
    """Adding the same observer twice does not cause double notifications."""
    state = AppState()
    obs = RecordingObserver()
    state.add_observer(obs)
    state.add_observer(obs)

    state.update(expression="x")

    assert len(obs.calls) == 1

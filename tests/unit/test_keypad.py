"""Tests for pyqalculate_gui.keypad."""

from __future__ import annotations

import os

import pytest

from pyqalculate_gui.event_bus import EXPRESSION_SUBMITTED, EventBus
from pyqalculate_gui.theme import LIGHT, ButtonStyle, Theme

from pyqalculate_gui.keypad import (
    BUTTON_DEFS,
    KeypadWidget,
    _style_for_button,
)

# ── Button definition shape ───────────────────────────────────────────

VALID_STYLE_KEYS = {"digit", "op", "func", "action", "equals"}

EXPECTED_ROWS = 6
EXPECTED_COLS = 5


class TestButtonDefs:
    """Verify BUTTON_DEFS is well-formed."""

    def test_row_count(self) -> None:
        assert len(BUTTON_DEFS) == EXPECTED_ROWS

    def test_col_count(self) -> None:
        for row_idx, row in enumerate(BUTTON_DEFS):
            assert len(row) == EXPECTED_COLS, f"Row {row_idx} has {len(row)} cols"

    def test_each_entry_is_4_tuple(self) -> None:
        for row_idx, row in enumerate(BUTTON_DEFS):
            for col_idx, entry in enumerate(row):
                assert len(entry) == 4, f"({row_idx},{col_idx}) len={len(entry)}"
                label, action, _value, style_key = entry
                assert isinstance(label, str)
                assert isinstance(action, str)
                assert isinstance(style_key, str)

    def test_action_types_are_valid(self) -> None:
        valid_actions = {"insert", "clear", "backspace", "negate", "submit"}
        for row in BUTTON_DEFS:
            for _, action, _, _ in row:
                assert action in valid_actions, f"Unknown action: {action}"

    def test_style_keys_are_valid(self) -> None:
        for row in BUTTON_DEFS:
            for _, _, _, style_key in row:
                assert style_key in VALID_STYLE_KEYS, f"Unknown style: {style_key}"

    def test_equals_button_exists(self) -> None:
        labels = [entry[0] for row in BUTTON_DEFS for entry in row]
        assert "=" in labels

    def test_clear_button_exists(self) -> None:
        labels = [entry[0] for row in BUTTON_DEFS for entry in row]
        assert "AC" in labels

    def test_digit_coverage(self) -> None:
        labels = [entry[0] for row in BUTTON_DEFS for entry in row]
        for d in "0123456789":
            assert d in labels, f"Digit {d} missing"


# ── _style_for_button ────────────────────────────────────────────────

class TestStyleForButton:
    def test_returns_button_style(self) -> None:
        result = _style_for_button(LIGHT, "digit")
        assert isinstance(result, ButtonStyle)

    def test_unknown_key_defaults_to_digit(self) -> None:
        result = _style_for_button(LIGHT, "nonexistent")
        assert result is LIGHT.keypad_digit

    def test_each_style_key_resolves(self) -> None:
        for key in VALID_STYLE_KEYS:
            result = _style_for_button(LIGHT, key)
            expected = getattr(LIGHT, f"keypad_{key}")
            assert result is expected


# ── Theme integration ────────────────────────────────────────────────

_NO_DISPLAY = os.environ.get("DISPLAY") is None and os.name != "nt"


@pytest.mark.skipif(_NO_DISPLAY, reason="No display available")
class TestKeypadTheme:
    def _make_keypad(self, theme: Theme = LIGHT) -> tuple:
        import tkinter as tk
        from pyqalculate_gui.event_bus import EventBus

        root = tk.Tk()
        root.withdraw()
        bus = EventBus()
        kp = KeypadWidget(root, theme=theme, event_bus=bus)
        return root, kp, bus

    def test_creates_with_light_theme(self) -> None:
        root, kp, _ = self._make_keypad(LIGHT)
        try:
            assert kp._theme is LIGHT
            assert len(kp._buttons) == EXPECTED_ROWS * EXPECTED_COLS
        finally:
            root.destroy()

    def test_all_buttons_have_hover_bindings(self) -> None:
        root, kp, _ = self._make_keypad()
        try:
            for btn in kp._buttons.values():
                bindings = btn.bind()
                assert "<Enter>" in bindings
                assert "<Leave>" in bindings
        finally:
            root.destroy()


# ── Event bus integration ────────────────────────────────────────────


@pytest.mark.skipif(_NO_DISPLAY, reason="No display available")
class TestKeypadEvents:
    def _make_keypad(self) -> tuple:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        bus = EventBus()
        kp = KeypadWidget(root, event_bus=bus)
        return root, kp, bus

    def test_insert_digit_emits_keypad_insert(self) -> None:
        root, kp, bus = self._make_keypad()
        try:
            received: list[str] = []
            bus.subscribe("keypad_insert", lambda v: received.append(v))
            kp._on_button("insert", "7")
            assert received == ["7"]
        finally:
            root.destroy()

    def test_clear_emits_keypad_clear(self) -> None:
        root, kp, bus = self._make_keypad()
        try:
            called: list[bool] = []
            bus.subscribe("keypad_clear", lambda: called.append(True))
            kp._on_button("clear", "")
            assert called == [True]
        finally:
            root.destroy()

    def test_backspace_emits_keypad_backspace(self) -> None:
        root, kp, bus = self._make_keypad()
        try:
            called: list[bool] = []
            bus.subscribe("keypad_backspace", lambda: called.append(True))
            kp._on_button("backspace", "")
            assert called == [True]
        finally:
            root.destroy()

    def test_negate_emits_keypad_negate(self) -> None:
        root, kp, bus = self._make_keypad()
        try:
            called: list[bool] = []
            bus.subscribe("keypad_negate", lambda: called.append(True))
            kp._on_button("negate", "")
            assert called == [True]
        finally:
            root.destroy()

    def test_submit_emits_expression_submitted(self) -> None:
        root, kp, bus = self._make_keypad()
        try:
            called: list[bool] = []
            bus.subscribe(EXPRESSION_SUBMITTED, lambda *_: called.append(True))
            kp._on_button("submit", "")
            assert called == [True]
        finally:
            root.destroy()

    def test_no_bus_does_not_raise(self) -> None:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            kp = KeypadWidget(root, event_bus=None)
            kp._on_button("insert", "5")
            kp._on_button("clear", "")
            kp._on_button("backspace", "")
            kp._on_button("negate", "")
            kp._on_button("submit", "")
        finally:
            root.destroy()

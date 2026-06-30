"""Tests for the KeyboardShortcutManager."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from pyqalculate_gui.event_bus import EventBus
from pyqalculate_gui.keyboard_shortcuts import (
    SHORTCUT_TYPE_ACTIVATE_FIRST_COMPLETION,
    SHORTCUT_TYPE_COPY_RESULT,
    SHORTCUT_TYPE_HELP,
    SHORTCUT_TYPE_HISTORY,
    SHORTCUT_TYPE_KEYPAD,
    SHORTCUT_TYPE_MANAGE_FUNCTIONS,
    SHORTCUT_TYPE_MANAGE_UNITS,
    SHORTCUT_TYPE_MANAGE_VARIABLES,
    SHORTCUT_TYPE_MINIMAL,
    SHORTCUT_TYPE_NUMBER_BASES,
    SHORTCUT_TYPE_PROGRAMMING,
    SHORTCUT_TYPE_QUIT,
    SHORTCUT_TYPE_RPN_COPY,
    SHORTCUT_TYPE_RPN_DELETE,
    SHORTCUT_TYPE_RPN_DOWN,
    SHORTCUT_TYPE_RPN_LASTX,
    SHORTCUT_TYPE_RPN_MODE,
    SHORTCUT_TYPE_RPN_SWAP,
    SHORTCUT_TYPE_RPN_UP,
    SHORTCUT_TYPE_STORE,
    KeyboardShortcut,
    KeyboardShortcutManager,
)


@pytest.fixture(scope="module")
def root():  # type: ignore[no-untyped-def]
    """Share a single Tk root across all tests in this module."""
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()


class TestAddShortcut:
    """Tests for KeyboardShortcutManager.add_shortcut."""

    def test_add_new_shortcut(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        mgr.clear_all()

        mgr.add_shortcut("x", frozenset({"Alt"}), 99, "test")
        shortcuts = mgr.get_all_shortcuts()
        assert len(shortcuts) == 1
        s = shortcuts[0]
        assert s.key == "x"
        assert s.modifiers == frozenset({"Alt"})
        assert s.types == [99]
        assert s.values == ["test"]

    def test_add_second_type_to_existing_binding(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        mgr.clear_all()

        mgr.add_shortcut("a", frozenset({"Control"}), 1, "first")
        mgr.add_shortcut("a", frozenset({"Control"}), 2, "second")

        shortcuts = mgr.get_all_shortcuts()
        assert len(shortcuts) == 1
        s = shortcuts[0]
        assert s.types == [1, 2]
        assert s.values == ["first", "second"]

    def test_add_duplicate_type_is_noop(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        mgr.clear_all()

        mgr.add_shortcut("a", frozenset({"Control"}), 1, "first")
        mgr.add_shortcut("a", frozenset({"Control"}), 1, "duplicate")

        shortcuts = mgr.get_all_shortcuts()
        assert len(shortcuts) == 1
        assert shortcuts[0].types == [1]
        assert shortcuts[0].values == ["first"]


class TestRemoveShortcut:
    """Tests for KeyboardShortcutManager.remove_shortcut."""

    def test_remove_entire_binding(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        mgr.clear_all()

        mgr.add_shortcut("z", frozenset(), 5, "")
        mgr.remove_shortcut("z", frozenset())
        assert mgr.get_all_shortcuts() == []

    def test_remove_specific_type(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        mgr.clear_all()

        mgr.add_shortcut("z", frozenset(), 1, "a")
        mgr.add_shortcut("z", frozenset(), 2, "b")
        mgr.remove_shortcut("z", frozenset(), type_=1)

        shortcuts = mgr.get_all_shortcuts()
        assert len(shortcuts) == 1
        assert shortcuts[0].types == [2]
        assert shortcuts[0].values == ["b"]

    def test_remove_last_type_removes_binding(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        mgr.clear_all()

        mgr.add_shortcut("z", frozenset(), 1, "")
        mgr.remove_shortcut("z", frozenset(), type_=1)
        assert mgr.get_all_shortcuts() == []

    def test_remove_nonexistent_is_noop(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        mgr.clear_all()

        # Should not raise
        mgr.remove_shortcut("nope", frozenset())
        mgr.remove_shortcut("nope", frozenset(), type_=42)


class TestRegisterHandler:
    """Tests for KeyboardShortcutManager.register_handler."""

    def test_handler_called_on_shortcut(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        mgr.clear_all()

        handler = MagicMock()
        mgr.register_handler(SHORTCUT_TYPE_HELP, handler)
        mgr.add_shortcut("F1", frozenset(), SHORTCUT_TYPE_HELP, "")

        # Simulate key press
        event = MagicMock()
        event.keysym = "F1"
        event.state = 0
        result = mgr._on_key_press(event)

        assert result == "break"
        handler.assert_called_once_with("")

    def test_unhandled_action_emits_event_bus(self, root: tk.Tk) -> None:
        bus = EventBus()
        mgr = KeyboardShortcutManager(root, event_bus=bus)
        mgr.clear_all()

        emitted: list[tuple] = []
        bus.subscribe("shortcut_action", lambda t, v: emitted.append((t, v)))

        mgr.add_shortcut("F9", frozenset(), 99, "val")

        event = MagicMock()
        event.keysym = "F9"
        event.state = 0
        mgr._on_key_press(event)

        assert emitted == [(99, "val")]

    def test_no_match_returns_none(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        mgr.clear_all()

        event = MagicMock()
        event.keysym = "z"
        event.state = 0
        result = mgr._on_key_press(event)

        assert result is None


class TestGetShortcutText:
    """Tests for KeyboardShortcutManager.get_shortcut_text."""

    def test_known_type(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        assert mgr.get_shortcut_text(SHORTCUT_TYPE_HELP) == "Help"
        assert mgr.get_shortcut_text(SHORTCUT_TYPE_QUIT) == "Quit"
        assert mgr.get_shortcut_text(SHORTCUT_TYPE_RPN_MODE) == "Toggle RPN mode"

    def test_unknown_type(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        assert mgr.get_shortcut_text(999) == "Action 999"


class TestGetAllShortcuts:
    """Tests for KeyboardShortcutManager.get_all_shortcuts."""

    def test_defaults_loaded(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        shortcuts = mgr.get_all_shortcuts()
        # Should have the 28 default bindings
        assert len(shortcuts) == 28

    def test_after_clear(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        mgr.clear_all()
        assert mgr.get_all_shortcuts() == []


class TestClearAll:
    """Tests for KeyboardShortcutManager.clear_all."""

    def test_clear_removes_all(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        assert len(mgr.get_all_shortcuts()) > 0
        mgr.clear_all()
        assert mgr.get_all_shortcuts() == []


class TestDefaultBindings:
    """Verify that default shortcuts are loaded correctly."""

    def test_ctrl_b_is_number_bases(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        shortcuts = mgr.get_all_shortcuts()

        ctrl_b = [s for s in shortcuts if s.key == "b" and s.modifiers == frozenset({"Control"})]
        assert len(ctrl_b) == 1
        assert ctrl_b[0].types == [SHORTCUT_TYPE_NUMBER_BASES]

    def test_f1_is_help(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        shortcuts = mgr.get_all_shortcuts()

        f1 = [s for s in shortcuts if s.key == "F1"]
        assert len(f1) == 1
        assert f1[0].types == [SHORTCUT_TYPE_HELP]
        assert f1[0].modifiers == frozenset()

    def test_tab_is_activate_first_completion(self, root: tk.Tk) -> None:
        mgr = KeyboardShortcutManager(root)
        shortcuts = mgr.get_all_shortcuts()

        tab = [s for s in shortcuts if s.key == "Tab"]
        assert len(tab) == 1
        assert tab[0].types == [SHORTCUT_TYPE_ACTIVATE_FIRST_COMPLETION]

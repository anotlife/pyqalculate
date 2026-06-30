"""Keyboard shortcut manager for PyQalculate GUI.

Maps key combinations to calculator actions, matching qalculate-gtk's
shortcut type system.  Supports default bindings, custom rebinding,
multi-action shortcuts, and event-bus integration.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple

from pyqalculate_gui.event_bus import EventBus
from pyqalculate_gui.i18n import _

# ── Shortcut type constants (matching qalculate-gtk) ──────────────────

SHORTCUT_TYPE_FUNCTION = 0
SHORTCUT_TYPE_VARIABLE = 2
SHORTCUT_TYPE_UNIT = 3
SHORTCUT_TYPE_TEXT = 4
SHORTCUT_TYPE_CONVERT = 9
SHORTCUT_TYPE_TO_NUMBER_BASE = 14
SHORTCUT_TYPE_FACTORIZE = 15
SHORTCUT_TYPE_EXPAND = 16
SHORTCUT_TYPE_RPN_UP = 19
SHORTCUT_TYPE_RPN_DOWN = 20
SHORTCUT_TYPE_RPN_SWAP = 21
SHORTCUT_TYPE_RPN_COPY = 22
SHORTCUT_TYPE_RPN_LASTX = 23
SHORTCUT_TYPE_RPN_DELETE = 24
SHORTCUT_TYPE_RPN_CLEAR = 25
SHORTCUT_TYPE_META_MODE = 26
SHORTCUT_TYPE_OUTPUT_BASE = 27
SHORTCUT_TYPE_INPUT_BASE = 28
SHORTCUT_TYPE_EXACT_MODE = 29
SHORTCUT_TYPE_DEGREES = 30
SHORTCUT_TYPE_RADIANS = 31
SHORTCUT_TYPE_GRADIANS = 32
SHORTCUT_TYPE_FRACTIONS = 33
SHORTCUT_TYPE_MIXED_FRACTIONS = 34
SHORTCUT_TYPE_SCIENTIFIC_NOTATION = 35
SHORTCUT_TYPE_SIMPLE_NOTATION = 36
SHORTCUT_TYPE_RPN_MODE = 37
SHORTCUT_TYPE_AUTOCALC = 38
SHORTCUT_TYPE_PROGRAMMING = 39
SHORTCUT_TYPE_KEYPAD = 40
SHORTCUT_TYPE_HISTORY = 41
SHORTCUT_TYPE_HISTORY_SEARCH = 42
SHORTCUT_TYPE_CONVERSION = 43
SHORTCUT_TYPE_STACK = 44
SHORTCUT_TYPE_MINIMAL = 45
SHORTCUT_TYPE_MANAGE_VARIABLES = 46
SHORTCUT_TYPE_MANAGE_FUNCTIONS = 47
SHORTCUT_TYPE_MANAGE_UNITS = 48
SHORTCUT_TYPE_STORE = 50
SHORTCUT_TYPE_MEMORY_CLEAR = 51
SHORTCUT_TYPE_MEMORY_RECALL = 52
SHORTCUT_TYPE_MEMORY_STORE = 53
SHORTCUT_TYPE_MEMORY_ADD = 54
SHORTCUT_TYPE_MEMORY_SUBTRACT = 55
SHORTCUT_TYPE_PLOT = 58
SHORTCUT_TYPE_NUMBER_BASES = 59
SHORTCUT_TYPE_COPY_RESULT = 65
SHORTCUT_TYPE_HELP = 67
SHORTCUT_TYPE_QUIT = 68
SHORTCUT_TYPE_CHAIN_MODE = 69
SHORTCUT_TYPE_DO_COMPLETION = 71
SHORTCUT_TYPE_ACTIVATE_FIRST_COMPLETION = 72
SHORTCUT_TYPE_INSERT_RESULT = 73
SHORTCUT_TYPE_HISTORY_CLEAR = 74
SHORTCUT_TYPE_PARENTHESES = 79


# ── Data class ────────────────────────────────────────────────────────


@dataclass
class KeyboardShortcut:
    """A single shortcut binding: one key + modifiers → one or more actions."""

    key: str
    modifiers: frozenset[str]
    types: List[int] = field(default_factory=list)
    values: List[str] = field(default_factory=list)


# ── Type-name mapping (for human-readable labels) ─────────────────────

_TYPE_NAMES: Dict[int, str] = {
    SHORTCUT_TYPE_FUNCTION: _("Insert function"),
    SHORTCUT_TYPE_VARIABLE: _("Insert variable"),
    SHORTCUT_TYPE_UNIT: _("Insert unit"),
    SHORTCUT_TYPE_TEXT: _("Insert text"),
    SHORTCUT_TYPE_CONVERT: _("Convert to unit"),
    SHORTCUT_TYPE_TO_NUMBER_BASE: _("Convert to number base"),
    SHORTCUT_TYPE_FACTORIZE: _("Factorize result"),
    SHORTCUT_TYPE_EXPAND: _("Expand result"),
    SHORTCUT_TYPE_RPN_UP: _("RPN: up"),
    SHORTCUT_TYPE_RPN_DOWN: _("RPN: down"),
    SHORTCUT_TYPE_RPN_SWAP: _("RPN: swap"),
    SHORTCUT_TYPE_RPN_COPY: _("RPN: copy"),
    SHORTCUT_TYPE_RPN_LASTX: _("RPN: lastx"),
    SHORTCUT_TYPE_RPN_DELETE: _("RPN: delete register"),
    SHORTCUT_TYPE_RPN_CLEAR: _("RPN: clear stack"),
    SHORTCUT_TYPE_META_MODE: _("Load meta mode"),
    SHORTCUT_TYPE_OUTPUT_BASE: _("Set result base"),
    SHORTCUT_TYPE_INPUT_BASE: _("Set expression base"),
    SHORTCUT_TYPE_EXACT_MODE: _("Toggle exact mode"),
    SHORTCUT_TYPE_DEGREES: _("Set angle unit to degrees"),
    SHORTCUT_TYPE_RADIANS: _("Set angle unit to radians"),
    SHORTCUT_TYPE_GRADIANS: _("Set angle unit to gradians"),
    SHORTCUT_TYPE_FRACTIONS: _("Toggle simple fractions"),
    SHORTCUT_TYPE_MIXED_FRACTIONS: _("Toggle mixed fractions"),
    SHORTCUT_TYPE_SCIENTIFIC_NOTATION: _("Toggle scientific notation"),
    SHORTCUT_TYPE_SIMPLE_NOTATION: _("Toggle simple notation"),
    SHORTCUT_TYPE_RPN_MODE: _("Toggle RPN mode"),
    SHORTCUT_TYPE_AUTOCALC: _("Toggle calculate as you type"),
    SHORTCUT_TYPE_PROGRAMMING: _("Toggle programming keypad"),
    SHORTCUT_TYPE_KEYPAD: _("Show keypad"),
    SHORTCUT_TYPE_HISTORY: _("Show history"),
    SHORTCUT_TYPE_HISTORY_SEARCH: _("Search history"),
    SHORTCUT_TYPE_CONVERSION: _("Show conversion"),
    SHORTCUT_TYPE_STACK: _("Show RPN stack"),
    SHORTCUT_TYPE_MINIMAL: _("Toggle minimal window"),
    SHORTCUT_TYPE_MANAGE_VARIABLES: _("Manage variables"),
    SHORTCUT_TYPE_MANAGE_FUNCTIONS: _("Manage functions"),
    SHORTCUT_TYPE_MANAGE_UNITS: _("Manage units"),
    SHORTCUT_TYPE_STORE: _("Store result"),
    SHORTCUT_TYPE_MEMORY_CLEAR: _("MC (memory clear)"),
    SHORTCUT_TYPE_MEMORY_RECALL: _("MR (memory recall)"),
    SHORTCUT_TYPE_MEMORY_STORE: _("MS (memory store)"),
    SHORTCUT_TYPE_MEMORY_ADD: _("M+ (memory plus)"),
    SHORTCUT_TYPE_MEMORY_SUBTRACT: _("M- (memory minus)"),
    SHORTCUT_TYPE_PLOT: _("Open plot functions/data"),
    SHORTCUT_TYPE_NUMBER_BASES: _("Open convert number bases"),
    SHORTCUT_TYPE_COPY_RESULT: _("Copy result"),
    SHORTCUT_TYPE_HELP: _("Help"),
    SHORTCUT_TYPE_QUIT: _("Quit"),
    SHORTCUT_TYPE_CHAIN_MODE: _("Toggle chain mode"),
    SHORTCUT_TYPE_DO_COMPLETION: _("Show/hide completion"),
    SHORTCUT_TYPE_ACTIVATE_FIRST_COMPLETION: _("Perform completion"),
    SHORTCUT_TYPE_INSERT_RESULT: _("Insert result"),
    SHORTCUT_TYPE_HISTORY_CLEAR: _("Clear history"),
    SHORTCUT_TYPE_PARENTHESES: _("Insert parentheses"),
}


# ── Manager ───────────────────────────────────────────────────────────


class KeyboardShortcutManager:
    """Manages keyboard shortcuts for the application."""

    def __init__(self, root: tk.Tk, event_bus: EventBus | None = None) -> None:
        self._root = root
        self._event_bus = event_bus
        self._shortcuts: Dict[Tuple[str, frozenset[str]], KeyboardShortcut] = {}
        self._action_handlers: Dict[int, Callable[[str], None]] = {}

        # Load default shortcuts
        self._load_defaults()

        # Bind key handler
        self._root.bind("<KeyPress>", self._on_key_press)

    # ── Defaults ──────────────────────────────────────────────────────

    def _load_defaults(self) -> None:
        """Load default keyboard shortcuts matching qalculate-gtk."""
        defaults: list[Tuple[str, frozenset[str], int, str]] = [
            ("b", frozenset({"Control"}), SHORTCUT_TYPE_NUMBER_BASES, ""),
            ("q", frozenset({"Control"}), SHORTCUT_TYPE_QUIT, ""),
            ("F1", frozenset(), SHORTCUT_TYPE_HELP, ""),
            ("c", frozenset({"Control", "Alt"}), SHORTCUT_TYPE_COPY_RESULT, ""),
            ("s", frozenset({"Control"}), SHORTCUT_TYPE_STORE, ""),
            ("m", frozenset({"Control"}), SHORTCUT_TYPE_MANAGE_VARIABLES, ""),
            ("f", frozenset({"Control"}), SHORTCUT_TYPE_MANAGE_FUNCTIONS, ""),
            ("u", frozenset({"Control"}), SHORTCUT_TYPE_MANAGE_UNITS, ""),
            ("k", frozenset({"Control"}), SHORTCUT_TYPE_KEYPAD, ""),
            ("k", frozenset({"Alt"}), SHORTCUT_TYPE_KEYPAD, ""),
            ("h", frozenset({"Control"}), SHORTCUT_TYPE_HISTORY, ""),
            ("h", frozenset({"Alt"}), SHORTCUT_TYPE_HISTORY, ""),
            ("space", frozenset({"Control"}), SHORTCUT_TYPE_MINIMAL, ""),
            ("o", frozenset({"Control"}), SHORTCUT_TYPE_CONVERSION, ""),
            ("o", frozenset({"Alt"}), SHORTCUT_TYPE_CONVERSION, ""),
            ("t", frozenset({"Control"}), SHORTCUT_TYPE_CONVERT, ""),
            ("p", frozenset({"Control"}), SHORTCUT_TYPE_PROGRAMMING, ""),
            ("r", frozenset({"Control"}), SHORTCUT_TYPE_RPN_MODE, ""),
            (
                "parenright",
                frozenset({"Control", "Shift"}),
                SHORTCUT_TYPE_PARENTHESES,
                "",
            ),
            (
                "parenleft",
                frozenset({"Control", "Shift"}),
                SHORTCUT_TYPE_PARENTHESES,
                "",
            ),
            ("Up", frozenset({"Control"}), SHORTCUT_TYPE_RPN_UP, ""),
            ("Down", frozenset({"Control"}), SHORTCUT_TYPE_RPN_DOWN, ""),
            ("Right", frozenset({"Control"}), SHORTCUT_TYPE_RPN_SWAP, ""),
            ("Left", frozenset({"Control"}), SHORTCUT_TYPE_RPN_LASTX, ""),
            ("c", frozenset({"Control", "Shift"}), SHORTCUT_TYPE_RPN_COPY, ""),
            ("Delete", frozenset({"Control"}), SHORTCUT_TYPE_RPN_DELETE, ""),
            (
                "Delete",
                frozenset({"Control", "Shift"}),
                SHORTCUT_TYPE_RPN_CLEAR,
                "",
            ),
            ("Tab", frozenset(), SHORTCUT_TYPE_ACTIVATE_FIRST_COMPLETION, ""),
        ]

        for key, modifiers, type_, value in defaults:
            self.add_shortcut(key, modifiers, type_, value)

    # ── Key-press handler ─────────────────────────────────────────────

    def _on_key_press(self, event: tk.Event) -> str | None:  # type: ignore[type-arg]
        """Handle key press events and dispatch to registered handlers."""
        modifiers = self._extract_modifiers(event)

        key = event.keysym
        shortcut = self._shortcuts.get((key, modifiers))

        if shortcut is not None:
            for type_, value in zip(shortcut.types, shortcut.values):
                self._execute_action(type_, value)
            return "break"  # Prevent default handling

        return None  # Allow default handling

    @staticmethod
    def _extract_modifiers(event: tk.Event) -> frozenset[str]:  # type: ignore[type-arg]
        """Build a modifier frozenset from a Tk event state bitmask."""
        state = int(event.state)
        modifiers: set[str] = set()
        if state & 0x0001:  # Shift
            modifiers.add("Shift")
        if state & 0x0004:  # Control
            modifiers.add("Control")
        if state & 0x0008:  # Alt
            modifiers.add("Alt")

        # AltGr fix: Ctrl+Alt together with NumLock → drop Control
        if "Alt" in modifiers and "Control" in modifiers:
            if state & 0x2000:  # Mod2 (NumLock)
                modifiers.discard("Control")

        return frozenset(modifiers)

    def _execute_action(self, action_type: int, value: str) -> None:
        """Execute a shortcut action via handler or event bus."""
        handler = self._action_handlers.get(action_type)
        if handler is not None:
            handler(value)
        elif self._event_bus is not None:
            self._event_bus.emit("shortcut_action", action_type, value)

    # ── Public API ────────────────────────────────────────────────────

    def add_shortcut(
        self, key: str, modifiers: frozenset[str], type_: int, value: str = ""
    ) -> None:
        """Add or update a keyboard shortcut."""
        shortcut_key = (key, modifiers)
        existing = self._shortcuts.get(shortcut_key)
        if existing is not None:
            if type_ not in existing.types:
                existing.types.append(type_)
                existing.values.append(value)
        else:
            self._shortcuts[shortcut_key] = KeyboardShortcut(
                key=key,
                modifiers=modifiers,
                types=[type_],
                values=[value],
            )

    def remove_shortcut(
        self, key: str, modifiers: frozenset[str], type_: int | None = None
    ) -> None:
        """Remove a keyboard shortcut.

        If *type_* is given, remove only that action from the binding.
        If it was the last action, remove the binding entirely.
        If *type_* is ``None``, remove the whole binding.
        """
        shortcut_key = (key, modifiers)
        shortcut = self._shortcuts.get(shortcut_key)
        if shortcut is None:
            return

        if type_ is None:
            del self._shortcuts[shortcut_key]
            return

        if type_ in shortcut.types:
            idx = shortcut.types.index(type_)
            shortcut.types.pop(idx)
            shortcut.values.pop(idx)
            if not shortcut.types:
                del self._shortcuts[shortcut_key]

    def register_handler(
        self, action_type: int, handler: Callable[[str], None]
    ) -> None:
        """Register a handler for a shortcut action type."""
        self._action_handlers[action_type] = handler

    def get_shortcut_text(self, type_: int) -> str:
        """Get human-readable text for a shortcut type."""
        return _TYPE_NAMES.get(type_, _("Action {}").format(type_))

    def get_all_shortcuts(self) -> List[KeyboardShortcut]:
        """Get all registered shortcuts."""
        return list(self._shortcuts.values())

    def clear_all(self) -> None:
        """Remove all shortcuts."""
        self._shortcuts.clear()

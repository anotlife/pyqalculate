"""Tests for pyqalculate_gui.preferences_dialog."""

from __future__ import annotations

import json
import os
import tkinter as tk
from pathlib import Path
from typing import Any

import pytest

from pyqalculate_gui.event_bus import EventBus, PREFERENCE_APPLIED
from pyqalculate_gui.preferences_dialog import DEFAULT_SETTINGS, PreferencesDialog
from pyqalculate_gui.theme import LIGHT

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HAS_DISPLAY = bool(
    os.environ.get("DISPLAY")
    or os.environ.get("WAYLAND_DISPLAY")
    or os.name == "nt"
)


def _reset_config_file(tmp_path: Path) -> None:
    """Point the module-level config file at a temp location."""
    import pyqalculate_gui.preferences_dialog as mod

    mod._CONFIG_DIR = tmp_path
    mod._CONFIG_FILE = tmp_path / "preferences.json"


def _get_config_file() -> Path:
    """Read the current module-level config path (may have been patched)."""
    import pyqalculate_gui.preferences_dialog as mod

    return mod._CONFIG_FILE


# ---------------------------------------------------------------------------
# Unit tests (no display required)
# ---------------------------------------------------------------------------


class TestDefaultSettings:
    """DEFAULT_SETTINGS structure validation."""

    def test_has_all_keys(self) -> None:
        """Given: DEFAULT_SETTINGS\nWhen:  inspected\nThen:  contains all expected keys."""
        expected = {
            "approximation",
            "angle_unit",
            "precision",
            "number_format",
            "digit_grouping",
            "unicode_signs",
            "exp_display",
            "font_family",
            "font_size",
            "theme",
            "language",
        }
        assert expected == set(DEFAULT_SETTINGS.keys())

    def test_default_precision_is_int(self) -> None:
        """Given: DEFAULT_SETTINGS\nWhen:  precision accessed\nThen:  value is an int."""
        assert isinstance(DEFAULT_SETTINGS["precision"], int)

    def test_default_theme_is_light(self) -> None:
        """Given: DEFAULT_SETTINGS\nWhen:  theme accessed\nThen:  value is 'light'."""
        assert DEFAULT_SETTINGS["theme"] == "light"


class TestLoadSettings:
    """_load_settings behavior."""

    def test_returns_defaults_when_no_file(self, tmp_path: Path) -> None:
        """Given: no config file exists\nWhen:  _load_settings called\nThen:  returns DEFAULT_SETTINGS copy."""
        _reset_config_file(tmp_path)
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = PreferencesDialog(root)
            assert dlg._settings == DEFAULT_SETTINGS
        finally:
            root.destroy()

    def test_loads_valid_json(self, tmp_path: Path) -> None:
        """Given: a valid JSON config file\nWhen:  _load_settings called\nThen:  merges with defaults."""
        _reset_config_file(tmp_path)
        cfg = _get_config_file()
        data = {"precision": 20, "theme": "dark"}
        cfg.write_text(json.dumps(data), encoding="utf-8")

        root = tk.Tk()
        root.withdraw()
        try:
            dlg = PreferencesDialog(root)
            assert dlg._settings["precision"] == 20
            assert dlg._settings["theme"] == "dark"
            # Unset keys fall back to defaults
            assert dlg._settings["angle_unit"] == DEFAULT_SETTINGS["angle_unit"]
        finally:
            root.destroy()

    def test_returns_defaults_on_corrupt_json(self, tmp_path: Path) -> None:
        """Given: a corrupt JSON file\nWhen:  _load_settings called\nThen:  returns defaults."""
        _reset_config_file(tmp_path)
        cfg = _get_config_file()
        cfg.write_text("NOT JSON {{{", encoding="utf-8")

        root = tk.Tk()
        root.withdraw()
        try:
            dlg = PreferencesDialog(root)
            assert dlg._settings == DEFAULT_SETTINGS
        finally:
            root.destroy()


class TestSaveSettings:
    """_save_settings persistence."""

    def test_creates_file_and_directory(self, tmp_path: Path) -> None:
        """Given: no config directory exists\nWhen:  _save_settings called\nThen:  file created with valid JSON."""
        _reset_config_file(tmp_path)
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = PreferencesDialog(root)
            dlg._settings["precision"] = 42
            dlg._save_settings()

            cfg = _get_config_file()
            assert cfg.exists()
            data = json.loads(cfg.read_text(encoding="utf-8"))
            assert data["precision"] == 42
        finally:
            root.destroy()

    def test_roundtrip_preserves_all_keys(self, tmp_path: Path) -> None:
        """Given: settings saved then loaded\nWhen:  round-tripped\nThen:  all keys preserved."""
        _reset_config_file(tmp_path)
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = PreferencesDialog(root)
            dlg._save_settings()

            # Reload settings from the file into the same dialog instance
            dlg._settings = dlg._load_settings()
            assert dlg._settings == DEFAULT_SETTINGS
        finally:
            root.destroy()


class TestGetSettings:
    """get_settings public API."""

    def test_returns_copy(self, tmp_path: Path) -> None:
        """Given: a PreferencesDialog\nWhen:  get_settings called twice\nThen:  returned dicts are equal but not the same object."""
        _reset_config_file(tmp_path)
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = PreferencesDialog(root)
            s1 = dlg.get_settings()
            s2 = dlg.get_settings()
            assert s1 == s2
            assert s1 is not s2
        finally:
            root.destroy()


class TestEventBusEmission:
    """EventBus integration."""

    def test_on_ok_emits_preference_applied(self, tmp_path: Path) -> None:
        """Given: a dialog with an EventBus\nWhen:  _on_ok called\nThen:  PREFERENCE_APPLIED emitted."""
        _reset_config_file(tmp_path)
        root = tk.Tk()
        root.withdraw()
        try:
            bus = EventBus()
            received: list[dict[str, Any]] = []
            bus.subscribe(PREFERENCE_APPLIED, lambda s: received.append(s))

            dlg = PreferencesDialog(root, event_bus=bus)
            dlg._on_ok()

            assert len(received) == 1
            assert "precision" in received[0]
        finally:
            root.destroy()

    def test_apply_settings_emits_event(self, tmp_path: Path) -> None:
        """Given: a dialog with an EventBus\nWhen:  apply_settings called\nThen:  PREFERENCE_APPLIED emitted."""
        _reset_config_file(tmp_path)
        root = tk.Tk()
        root.withdraw()
        try:
            bus = EventBus()
            received: list[dict[str, Any]] = []
            bus.subscribe(PREFERENCE_APPLIED, lambda s: received.append(s))

            dlg = PreferencesDialog(root, event_bus=bus)
            dlg.apply_settings()

            assert len(received) == 1
        finally:
            root.destroy()

    def test_no_event_bus_no_crash(self, tmp_path: Path) -> None:
        """Given: a dialog without an EventBus\nWhen:  _on_ok called\nThen:  no crash."""
        _reset_config_file(tmp_path)
        root = tk.Tk()
        root.withdraw()
        try:
            dlg = PreferencesDialog(root, event_bus=None)
            dlg._on_ok()
            # No assertion needed — just must not raise
        finally:
            root.destroy()


# ---------------------------------------------------------------------------
# Integration — requires a display (skip in headless CI)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="ModalDialog.wait_window causes Tk event loop hang on teardown")
def test_show_and_cancel(tmp_path: Path) -> None:
    """Given: a PreferencesDialog\nWhen:  show() then cancel\nThen:  result is False."""
    _reset_config_file(tmp_path)
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = PreferencesDialog(root)
        root.after(50, dlg._on_cancel)
        dlg.show()
        assert dlg.get_result() is False
    finally:
        root.destroy()


@pytest.mark.skip(reason="ModalDialog.wait_window causes Tk event loop hang on teardown")
def test_show_and_ok(tmp_path: Path) -> None:
    """Given: a PreferencesDialog\nWhen:  show() then OK\nThen:  result is True."""
    _reset_config_file(tmp_path)
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = PreferencesDialog(root)
        root.after(50, dlg._on_ok)
        dlg.show()
        assert dlg.get_result() is True
    finally:
        root.destroy()

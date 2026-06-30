"""Tests for pyqalculate_gui.theme."""

import pytest

from pyqalculate_gui.theme import DARK, LIGHT, ButtonStyle, Theme, get_theme


REQUIRED_THEME_FIELDS = {
    "bg",
    "fg",
    "entry_bg",
    "select_bg",
    "expression_fg",
    "result_fg",
    "result_approx_fg",
    "error_fg",
    "separator_fg",
    "info_fg",
    "expression_font",
    "result_font",
    "info_font",
    "keypad_digit",
    "keypad_op",
    "keypad_func",
    "keypad_const",
    "keypad_var",
    "keypad_action",
    "keypad_equals",
}


class TestLightTheme:
    def test_has_all_required_fields(self):
        fields = {f.name for f in Theme.__dataclass_fields__.values()}
        assert REQUIRED_THEME_FIELDS.issubset(fields)

    def test_is_frozen(self):
        with pytest.raises(AttributeError):
            LIGHT.bg = "#000000"  # type: ignore[misc]

    def test_colors_are_valid_hex(self):
        color_fields = [
            "bg",
            "fg",
            "entry_bg",
            "select_bg",
            "expression_fg",
            "result_fg",
            "result_approx_fg",
            "error_fg",
            "separator_fg",
            "info_fg",
        ]
        for field in color_fields:
            value = getattr(LIGHT, field)
            assert isinstance(value, str)
            assert value.startswith("#")
            assert len(value) == 7

    def test_keypad_styles_are_button_style(self):
        button_fields = [
            "keypad_digit",
            "keypad_op",
            "keypad_func",
            "keypad_const",
            "keypad_var",
            "keypad_action",
            "keypad_equals",
        ]
        for field in button_fields:
            value = getattr(LIGHT, field)
            assert isinstance(value, ButtonStyle)

    def test_fonts_are_tuples(self):
        for field in ("expression_font", "result_font", "info_font"):
            value = getattr(LIGHT, field)
            assert isinstance(value, tuple)


class TestDarkTheme:
    def test_has_all_required_fields(self):
        fields = {f.name for f in Theme.__dataclass_fields__.values()}
        assert REQUIRED_THEME_FIELDS.issubset(fields)

    def test_is_frozen(self):
        with pytest.raises(AttributeError):
            DARK.bg = "#000000"  # type: ignore[misc]

    def test_colors_are_valid_hex(self):
        color_fields = [
            "bg",
            "fg",
            "entry_bg",
            "select_bg",
            "expression_fg",
            "result_fg",
            "result_approx_fg",
            "error_fg",
            "separator_fg",
            "info_fg",
        ]
        for field in color_fields:
            value = getattr(DARK, field)
            assert isinstance(value, str)
            assert value.startswith("#")
            assert len(value) == 7

    def test_dark_differs_from_light(self):
        assert DARK.bg != LIGHT.bg
        assert DARK.fg != LIGHT.fg


class TestGetTheme:
    def test_returns_light_for_light(self):
        assert get_theme("light") is LIGHT

    def test_returns_dark_for_dark(self):
        assert get_theme("dark") is DARK

    def test_case_insensitive(self):
        assert get_theme("LIGHT") is LIGHT
        assert get_theme("Dark") is DARK

    def test_unknown_defaults_to_light(self):
        assert get_theme("unknown") is LIGHT

    def test_empty_string_defaults_to_light(self):
        assert get_theme("") is LIGHT

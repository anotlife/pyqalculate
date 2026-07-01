"""Tests for pyqalculate_gui.theme."""

import pytest

from pyqalculate_gui.theme import LIGHT, ButtonStyle, Theme


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




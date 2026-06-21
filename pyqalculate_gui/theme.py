"""Centralized theme with design tokens for the pyQalculate GUI."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ButtonStyle:
    """Style for a keypad button."""

    bg: str
    fg: str
    hover_bg: str
    font: tuple  # (family, size, weight)


@dataclass(frozen=True)
class Theme:
    """Complete application theme with colors, fonts, and button styles."""

    # Colors
    bg: str
    fg: str
    entry_bg: str
    select_bg: str

    # Text tags
    expression_fg: str
    result_fg: str
    result_approx_fg: str
    error_fg: str
    separator_fg: str
    info_fg: str

    # Fonts
    expression_font: tuple
    result_font: tuple
    info_font: tuple

    # Keypad button styles
    keypad_digit: ButtonStyle
    keypad_op: ButtonStyle
    keypad_func: ButtonStyle
    keypad_const: ButtonStyle
    keypad_var: ButtonStyle
    keypad_action: ButtonStyle
    keypad_equals: ButtonStyle


LIGHT = Theme(
    bg="#ffffff",
    fg="#000000",
    entry_bg="#f8f8f8",
    select_bg="#0078d4",
    expression_fg="#000000",
    result_fg="#1a5276",
    result_approx_fg="#7d6608",
    error_fg="#c0392b",
    separator_fg="#95a5a6",
    info_fg="#27ae60",
    expression_font=("Consolas", 11),
    result_font=("Consolas", 12, "bold"),
    info_font=("Consolas", 9),
    keypad_digit=ButtonStyle("#f0f0f0", "#000000", "#e0e0e0", ("Arial", 11)),
    keypad_op=ButtonStyle("#d4e6f1", "#1a5276", "#aed6f1", ("Arial", 11, "bold")),
    keypad_func=ButtonStyle("#d5f5e3", "#1e8449", "#abebc6", ("Arial", 10)),
    keypad_const=ButtonStyle("#fdebd0", "#7d6608", "#f9e79f", ("Arial", 10)),
    keypad_var=ButtonStyle("#f5eef8", "#6c3483", "#e8daef", ("Arial", 10)),
    keypad_action=ButtonStyle("#fadbd8", "#c0392b", "#f1948a", ("Arial", 10)),
    keypad_equals=ButtonStyle("#2e86c1", "#ffffff", "#1a5276", ("Arial", 12, "bold")),
)

DARK = Theme(
    bg="#1e1e1e",
    fg="#d4d4d4",
    entry_bg="#2d2d2d",
    select_bg="#264f78",
    expression_fg="#d4d4d4",
    result_fg="#569cd6",
    result_approx_fg="#ce9178",
    error_fg="#f44747",
    separator_fg="#808080",
    info_fg="#4ec9b0",
    expression_font=("Consolas", 11),
    result_font=("Consolas", 12, "bold"),
    info_font=("Consolas", 9),
    keypad_digit=ButtonStyle("#333333", "#d4d4d4", "#444444", ("Arial", 11)),
    keypad_op=ButtonStyle("#264f78", "#569cd6", "#37699e", ("Arial", 11, "bold")),
    keypad_func=ButtonStyle("#1e3a2d", "#4ec9b0", "#2d5a47", ("Arial", 10)),
    keypad_const=ButtonStyle("#3d2e1e", "#ce9178", "#5a4530", ("Arial", 10)),
    keypad_var=ButtonStyle("#2d1e3d", "#c586c0", "#45305a", ("Arial", 10)),
    keypad_action=ButtonStyle("#3d1e1e", "#f44747", "#5a3030", ("Arial", 10)),
    keypad_equals=ButtonStyle("#0e639c", "#ffffff", "#1177bb", ("Arial", 12, "bold")),
)


def get_theme(name: str) -> Theme:
    """Get theme by name."""
    themes = {"light": LIGHT, "dark": DARK}
    return themes.get(name.lower(), LIGHT)

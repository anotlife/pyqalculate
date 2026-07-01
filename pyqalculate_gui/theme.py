"""Centralized theme with design tokens for the pyQalculate GUI."""

from dataclasses import dataclass, replace


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
    warning_fg: str
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

    def with_scaled_fonts(self, scale: float) -> "Theme":
        """Return a new Theme with all font sizes scaled by *scale*."""
        def _scale_font(font: tuple) -> tuple:
            if len(font) == 3:
                return (font[0], int(round(font[1] * scale)), font[2])
            return (font[0], int(round(font[1] * scale)))

        def _scale_button(bs: ButtonStyle) -> ButtonStyle:
            return ButtonStyle(bs.bg, bs.fg, bs.hover_bg, _scale_font(bs.font))

        return replace(
            self,
            expression_font=_scale_font(self.expression_font),
            result_font=_scale_font(self.result_font),
            info_font=_scale_font(self.info_font),
            keypad_digit=_scale_button(self.keypad_digit),
            keypad_op=_scale_button(self.keypad_op),
            keypad_func=_scale_button(self.keypad_func),
            keypad_const=_scale_button(self.keypad_const),
            keypad_var=_scale_button(self.keypad_var),
            keypad_action=_scale_button(self.keypad_action),
            keypad_equals=_scale_button(self.keypad_equals),
        )


LIGHT = Theme(
    bg="#ffffff",
    fg="#000000",
    entry_bg="#f8f8f8",
    select_bg="#0078d4",
    expression_fg="#000000",
    result_fg="#1a5276",
    result_approx_fg="#7d6608",
    error_fg="#c0392b",
    warning_fg="#e67e22",
    separator_fg="#95a5a6",
    info_fg="#27ae60",
    expression_font=("Consolas", 18),
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


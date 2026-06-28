"""Mathematical expression renderer using matplotlib.

Converts calculator output strings to properly rendered mathematical
notation using matplotlib's mathtext engine. Supports fractions,
superscripts, subscripts, radicals, Greek letters, and more.
"""

from __future__ import annotations

import re
from typing import Any, Final, Optional

import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from PIL import Image, ImageTk

# Unicode superscript and subscript digit mappings
_SUPERSCRIPTS: Final = "⁰¹²³⁴⁵⁶⁷⁸⁹"
_SUBSCRIPTS: Final = "₀₁₂₃₄₅₆₇₈₉"

# Operator replacements: Unicode → mathtext command
_OPERATOR_MAP: Final[dict[str, str]] = {
    "×": r"\times ",
    "÷": r"\div ",
    "·": r"\cdot ",
    "π": r"\pi ",
    "∞": r"\infty ",
    "±": r"\pm ",
    "≤": r"\leq ",
    "≥": r"\geq ",
    "≠": r"\neq ",
    "≈": r"\approx ",
}


class MathRenderer:
    """Renders mathematical expressions as images using matplotlib.

    Uses matplotlib's mathtext engine to typeset expressions with proper
    mathematical notation (fractions, radicals, superscripts, etc.).
    Caches rendered images keyed by (text, font_size, color).
    """

    def __init__(self, dpi: int = 100) -> None:
        self._dpi = dpi
        self._cache: dict[str, ImageTk.PhotoImage] = {}

    def _convert_to_mathtext(self, text: str) -> str:
        """Convert calculator output to matplotlib mathtext format.

        Handles Unicode math symbols, superscript/subscript digits,
        square root notation, division (fractions), negative numbers,
        parenthesized exponents, comparison operators, infinity,
        and sum/product functions.
        """
        # ── Phase 1: Unicode → mathtext operators ──
        for old, new in _OPERATOR_MAP.items():
            text = text.replace(old, new)

        # ── Phase 2: Unicode superscript/subscript digits ──
        for i, ch in enumerate(_SUPERSCRIPTS):
            text = text.replace(ch, f"^{{{i}}}")

        for i, ch in enumerate(_SUBSCRIPTS):
            text = text.replace(ch, f"_{{{i}}}")

        # ── Phase 3: Square root ──
        # √2 → \sqrt{2}, √(x+1) → \sqrt{x+1}
        text = re.sub(r"√(\d+)", r"\\sqrt{\1}", text)
        text = re.sub(r"√\(([^)]+)\)", r"\\sqrt{\1}", text)

        # ── Phase 4: Text functions → mathtext (before other transforms) ──
        text = self._convert_text_functions(text)

        # ── Phase 5: Division (fractions) ──
        text = self._convert_division(text)

        # ── Phase 6: Parenthesized exponents ──
        # 2^(1/3) → 2^{\frac{1}{3}}, x^(n+1) → x^{n+1}
        text = re.sub(r"\^\(([^)]+)\)", r"^{\1}", text)

        # ── Phase 7: Negative numbers ──
        # Wrap negative literals in braces for proper mathtext rendering.
        # Only match when a minus sign is actually present, and the minus is
        # unary (at start, after =, (, [, ,) — NOT after +, *, /, etc.
        text = re.sub(
            r"(^|(?<=[=\(,\[]))\s*(-\d+\.?\d*)",
            r"\1{\2}",
            text,
        )

        # ── Phase 8: Comparison operators (ASCII) ──
        # Order matters: multi-char before single-char to avoid partial matches
        text = text.replace("!=", r"\neq ")
        text = text.replace("<=", r"\leq ")
        text = text.replace(">=", r"\geq ")
        # Single < and > are valid mathtext as-is — no conversion needed

        # ── Phase 9: Infinity ──
        text = re.sub(r"\binf(?:inity)?\b", r"\\infty ", text)

        # ── Phase 10: Sum and Product ──
        text = re.sub(r"\bsum\b", r"\\sum ", text)
        text = re.sub(r"\bproduct\b", r"\\prod ", text)

        return text

    @staticmethod
    def _convert_text_functions(text: str) -> str:
        """Convert text function names to mathtext (e.g. sin → \\sin)."""
        funcs = (
            "sin", "cos", "tan", "sec", "csc", "cot",
            "asin", "acos", "atan", "sinh", "cosh", "tanh",
            "log", "ln", "exp", "sqrt",
        )
        for fn in funcs:
            # Only match whole-word function calls, not part of variable names
            text = re.sub(rf"\b{fn}\b", rf"\\{fn}", text)
        return text

    @staticmethod
    def _convert_division(text: str) -> str:
        """Convert a/b to \\frac{a}{b}, handling nested parens and avoiding URLs.

        Rules:
        - Skip if already a mathtext command (\\div, \\frac)
        - Skip protocol prefixes like ://
        - Match simple: 1/3, x/2, 2.5/3
        - Match parenthesized: (a+b)/c, a/(b+c), (a+b)/(c+d)
        """
        def _is_in_cmd(s: str, pos: int) -> bool:
            """Check if pos is inside a \\command (after backslash, before space/brace)."""
            i = pos - 1
            if i >= 0 and s[i] == "\\":
                return True
            return False

        def _replace_frac(m: re.Match) -> str:
            numerator, denominator = m.group(1), m.group(2)
            # Strip redundant outer parens from denominator — the fraction
            # bar already provides grouping.
            if denominator.startswith("(") and denominator.endswith(")"):
                denominator = denominator[1:-1]
            return f"\\frac{{{numerator}}}{{{denominator}}}"

        # Parenthesized numerator: (a+b)/c
        text = re.sub(
            r"(?<!\\)\(([^()]+)\)/((?:\d+\.?\d*|[a-zA-Z]\w*|\([^()]+\)))",
            _replace_frac,
            text,
        )
        # Parenthesized denominator: a/(b+c)
        text = re.sub(
            r"(?<!\\)([\w.]+)/\(([^()]+)\)",
            _replace_frac,
            text,
        )
        # Simple: a/b where a,b are plain tokens (no parens involved)
        def _simple_frac(m: re.Match) -> str:
            full = m.group(0)
            if _is_in_cmd(text, m.start()):
                return full
            numerator, denominator = m.group(1), m.group(2)
            return f"\\frac{{{numerator}}}{{{denominator}}}"

        text = re.sub(
            r"(?<!\\)(\d+\.?\d*|[a-zA-Z]\w*)\s*/\s*(\d+\.?\d*|[a-zA-Z]\w*)",
            _simple_frac,
            text,
        )
        return text

    def render(
        self,
        text: str,
        font_size: int = 14,
        color: str = "black",
        master: Any | None = None,
    ) -> Optional[ImageTk.PhotoImage]:
        """Render a mathematical expression as a tkinter-compatible image.

        Args:
            text: Expression string to render.
            font_size: Font size in points.
            color: Text color.
            master: Tk widget to associate the image with (ensures correct
                interpreter in test environments with multiple Tk roots).

        Returns None if rendering fails (caller should fall back to plain text).
        """
        cache_key = f"{text}_{font_size}_{color}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            mathtext = self._convert_to_mathtext(text)
        except Exception:  # noqa: BLE001
            mathtext = None

        # Attempt 1: full mathtext conversion
        if mathtext is not None:
            try:
                photo = self._to_photo(f"${mathtext}$", font_size, color, master)
                if photo is not None:
                    self._cache[cache_key] = photo
                    return photo
            except Exception:  # noqa: BLE001
                pass

        # Attempt 2: literal text in math mode (escape backslashes for safety)
        try:
            safe_text = text.replace("\\", "\\\\")
            photo = self._to_photo(f"$\\mathrm{{{safe_text}}}$", font_size, color, master)
            if photo is not None:
                self._cache[cache_key] = photo
                return photo
        except Exception:  # noqa: BLE001
            pass

        # Attempt 3: plain text fallback (no math mode)
        try:
            photo = self._to_photo(text, font_size, color, master)
            if photo is not None:
                self._cache[cache_key] = photo
                return photo
        except Exception:  # noqa: BLE001
            pass

        return None

    def render_plain(
        self,
        text: str,
        font_size: int = 14,
        color: str = "black",
        master: Any | None = None,
    ) -> Optional[ImageTk.PhotoImage]:
        """Render plain text as an image (fallback when mathtext fails)."""
        try:
            return self._to_photo(text, font_size, color, master)
        except Exception:  # noqa: BLE001
            return None

    def _to_photo(
        self, display_text: str, font_size: int, color: str, master: Any | None
    ) -> Optional[ImageTk.PhotoImage]:
        """Render display_text to an ImageTk.PhotoImage with tight sizing."""
        fig = Figure(dpi=self._dpi)
        fig.patch.set_facecolor("none")
        fig.patch.set_edgecolor("none")

        text_obj = fig.text(
            0.0, 0.5, display_text,
            fontsize=font_size, color=color,
            ha="left", va="center",
        )

        # First pass: measure bounding box
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        bbox = text_obj.get_window_extent(canvas.get_renderer())

        # Resize figure to tightly fit text
        w_inch = bbox.width / self._dpi + 0.1
        h_inch = bbox.height / self._dpi + 0.2
        fig.set_size_inches(w_inch, h_inch)

        # Second pass: render at final size
        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        # Copy buffer to own the pixel data before clearing the figure
        buf = canvas.buffer_rgba()
        image = Image.frombytes("RGBA", canvas.get_width_height(), bytes(buf))
        photo = ImageTk.PhotoImage(image, master=master)

        fig.clear()
        return photo

    def clear_cache(self) -> None:
        """Clear the image cache."""
        self._cache.clear()

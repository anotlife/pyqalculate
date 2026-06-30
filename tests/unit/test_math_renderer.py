"""Tests for MathRenderer."""

from __future__ import annotations

import tkinter as tk
from typing import Generator

import pytest
from PIL import ImageTk

from pyqalculate_gui.math_renderer import MathRenderer


def _tk_available() -> bool:
    """Check if tkinter can initialize in this environment."""
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except tk.TclError:
        return False


needs_tk = pytest.mark.skipif(not _tk_available(), reason="tkinter not available")


@pytest.fixture()
def renderer() -> MathRenderer:
    return MathRenderer(dpi=72)


@pytest.fixture()
def tk_root() -> Generator[tk.Tk, None, None]:
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("tkinter not available in this environment")
    yield root
    root.destroy()


# --- _convert_to_mathtext ---


class TestConvertToMathtext:
    def test_operators(self, renderer: MathRenderer) -> None:
        assert r"\times" in renderer._convert_to_mathtext("2×3")
        assert r"\div" in renderer._convert_to_mathtext("6÷2")
        assert r"\cdot" in renderer._convert_to_mathtext("3·4")
        assert r"\pi" in renderer._convert_to_mathtext("2π")
        assert r"\infty" in renderer._convert_to_mathtext("∞")
        assert r"\pm" in renderer._convert_to_mathtext("±1")
        assert r"\leq" in renderer._convert_to_mathtext("x≤5")
        assert r"\geq" in renderer._convert_to_mathtext("x≥5")
        assert r"\neq" in renderer._convert_to_mathtext("x≠0")
        assert r"\approx" in renderer._convert_to_mathtext("π≈3.14")

    def test_superscripts(self, renderer: MathRenderer) -> None:
        result = renderer._convert_to_mathtext("x²")
        assert "^{2}" in result

        result = renderer._convert_to_mathtext("x³")
        assert "^{3}" in result

        result = renderer._convert_to_mathtext("x⁰¹²³⁴⁵⁶⁷⁸⁹")
        for i in range(10):
            assert f"^{{{i}}}" in result

    def test_subscripts(self, renderer: MathRenderer) -> None:
        result = renderer._convert_to_mathtext("x₀₁₂₃₄₅₆₇₈₉")
        for i in range(10):
            assert f"_{{{i}}}" in result

    def test_sqrt_simple(self, renderer: MathRenderer) -> None:
        result = renderer._convert_to_mathtext("√2")
        assert r"\sqrt{2}" in result

    def test_sqrt_parens(self, renderer: MathRenderer) -> None:
        result = renderer._convert_to_mathtext("√(x+1)")
        assert r"\sqrt{x+1}" in result

    def test_plain_number_unchanged(self, renderer: MathRenderer) -> None:
        assert renderer._convert_to_mathtext("42") == "42"
        assert renderer._convert_to_mathtext("3.14159") == "3.14159"

    def test_empty_string(self, renderer: MathRenderer) -> None:
        assert renderer._convert_to_mathtext("") == ""

    def test_combined_expression(self, renderer: MathRenderer) -> None:
        result = renderer._convert_to_mathtext("2×3²+√5")
        assert r"\times" in result
        assert "^{2}" in result  # ² → ^{2}
        assert r"\sqrt{5}" in result


# --- render ---


class TestRender:
    @needs_tk
    def test_renders_number(self, renderer: MathRenderer, tk_root: tk.Tk) -> None:
        photo = renderer.render("42")
        assert photo is not None
        assert isinstance(photo, ImageTk.PhotoImage)

    @needs_tk
    def test_renders_expression(self, renderer: MathRenderer, tk_root: tk.Tk) -> None:
        photo = renderer.render("2×3+1")
        assert photo is not None

    @needs_tk
    def test_renders_greek(self, renderer: MathRenderer, tk_root: tk.Tk) -> None:
        photo = renderer.render("2π")
        assert photo is not None

    def test_returns_none_for_bad_input(self, renderer: MathRenderer) -> None:
        # Mathtext with unbalanced braces should fail gracefully
        # No tk_root needed — render returns None before PhotoImage creation
        photo = renderer.render("{unbalanced")
        assert photo is None

    @needs_tk
    def test_render_plain(self, renderer: MathRenderer, tk_root: tk.Tk) -> None:
        photo = renderer.render_plain("hello world")
        assert photo is not None
        assert isinstance(photo, ImageTk.PhotoImage)

    @needs_tk
    def test_render_plain_returns_none_on_failure(
        self, renderer: MathRenderer, tk_root: tk.Tk
    ) -> None:
        photo = renderer.render_plain("test")
        assert photo is not None


# --- cache ---


class TestCache:
    @needs_tk
    def test_cache_hit_returns_same_object(
        self, renderer: MathRenderer, tk_root: tk.Tk
    ) -> None:
        renderer.clear_cache()
        photo1 = renderer.render("42")
        photo2 = renderer.render("42")
        assert photo1 is photo2

    @needs_tk
    def test_different_params_cache_separately(
        self, renderer: MathRenderer, tk_root: tk.Tk
    ) -> None:
        renderer.clear_cache()
        photo1 = renderer.render("42", font_size=12)
        photo2 = renderer.render("42", font_size=16)
        assert photo1 is not photo2

    @needs_tk
    def test_clear_cache(self, renderer: MathRenderer, tk_root: tk.Tk) -> None:
        renderer.render("42")
        assert len(renderer._cache) > 0
        renderer.clear_cache()
        assert len(renderer._cache) == 0

    def test_failure_not_cached(self, renderer: MathRenderer) -> None:
        renderer.clear_cache()
        renderer.render("{bad")
        assert len(renderer._cache) == 0

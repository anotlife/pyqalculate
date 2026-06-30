"""Internationalization support for pyqalculate GUI.

Provides a lightweight gettext wrapper.  Call ``init(language)`` early
in the application startup (before any widget is constructed) and then
import ``_()`` into every widget module that needs translations.

Language-change detection is done in ``app.py``; this module does not
subscribe to preferences directly — it simply sets up the gettext
machinery that the rest of the UI consumes.
"""

from __future__ import annotations

import builtins
import gettext
import os
from typing import Callable

try:
    import tkinter.font as tkfont
    _TKFONT_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    tkfont = None  # type: ignore
    _TKFONT_AVAILABLE = False

_LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")

_translator: gettext.NullTranslations | None = None
_current_language: str = "en"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init(language: str = "en") -> None:
    """Initialise gettext for *language* (e.g. ``"en"``, ``"zh_CN"``).

    Must be called before any GUI widgets are built so that ``_()``
    calls inside widget constructors pick up the correct translations.
    """
    global _translator, _current_language

    _current_language = language

    try:
        _translator = gettext.translation(
            "pyqalculate",
            localedir=_LOCALES_DIR,
            languages=[language],
            fallback=True,
        )
    except Exception:
        _translator = gettext.NullTranslations()

    _translator.install()


def gettext_(message: str) -> str:
    """Return the translation for *message*.

    Falls back gracefully to the untranslated string.
    """
    if _translator is None:
        return message
    return _translator.gettext(message)


def ngettext_(singular: str, plural: str, n: int) -> str:
    """Return the plural form for *n*."""
    if _translator is None:
        return singular if n == 1 else plural
    return _translator.ngettext(singular, plural, n)


def get_current_language() -> str:
    """Return the currently active language code."""
    return _current_language


# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------

_CJK_FONTS = [
    "Noto Sans CJK SC",
    "Microsoft YaHei",
    "Noto Sans SC",
    "WenQuanYi Micro Hei",
    "Noto Sans CJK TC",
]


def get_cjk_font_family() -> str:
    """Return the best available CJK font family name for the current system.

    Falls back to ``"sans-serif"`` if no CJK font is installed or if
    tkinter is not available.
    """
    if not _TKFONT_AVAILABLE:
        return "Noto Sans CJK SC"
    available = set(tkfont.families())
    for name in _CJK_FONTS:
        if name in available:
            return name
    return "sans-serif"


def get_default_font_family() -> str:
    """Return the default font family appropriate for the current language.

    For CJK locales this returns a CJK-capable font; otherwise the
    Monospace font set in preferences is used.
    """
    if _current_language == "zh_CN":
        return get_cjk_font_family()
    return "Consolas"


# Convenience aliases — these are the functions other modules import
_ = gettext_
n_ = ngettext_

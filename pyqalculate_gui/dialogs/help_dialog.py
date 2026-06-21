"""Help/About dialog for PyQalculate.

Shows version info, credits, license, and links.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pyqalculate_gui.dialogs.base import ModalDialog
from pyqalculate_gui.theme import LIGHT, Theme


class HelpDialog(ModalDialog):
    """About/Help dialog with version info and credits."""

    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme = LIGHT,
    ) -> None:
        super().__init__(
            parent,
            title="About PyQalculate",
            size=(400, 350),
            resizable=(False, False),
            theme=theme,
        )

    def _build_content(self, parent: ttk.Frame) -> None:
        """Build the help dialog content."""
        ttk.Label(
            parent,
            text="PyQalculate",
            font=("Arial", 18, "bold"),
        ).pack(pady=(10, 5))

        from pyqalculate_gui import __version__

        ttk.Label(
            parent,
            text=f"Version {__version__}",
            font=self._theme.info_font,
        ).pack(pady=(0, 15))

        desc_text = (
            "A pure Python port of the Qalculate! library.\n"
            "Features a complete calculator with unit conversion,\n"
            "function plotting, and mathematical expression evaluation."
        )
        ttk.Label(
            parent,
            text=desc_text,
            font=self._theme.info_font,
            justify=tk.CENTER,
        ).pack(pady=(0, 15))

        ttk.Label(
            parent,
            text="Credits:",
            font=("Arial", 11, "bold"),
        ).pack(anchor=tk.W, padx=20)

        for credit in (
            "Original Qalculate! by Hanna Knutsson",
            "Python port by anotlife",
            "Built with tkinter and matplotlib",
        ):
            ttk.Label(
                parent,
                text=f"  • {credit}",
                font=self._theme.info_font,
            ).pack(anchor=tk.W, padx=30)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(
            fill=tk.X, pady=10, padx=20,
        )

        links_frame = ttk.Frame(parent)
        links_frame.pack(fill=tk.X, padx=20)

        github_label = ttk.Label(
            links_frame,
            text="GitHub: github.com/anotlife/pyqalculate",
            font=self._theme.info_font,
            foreground="blue",
            cursor="hand2",
        )
        github_label.pack(anchor=tk.W)
        github_label.bind(
            "<Button-1>",
            lambda _e: self._open_url("https://github.com/anotlife/pyqalculate"),
        )

        ttk.Label(
            links_frame,
            text="License: MIT",
            font=self._theme.info_font,
        ).pack(anchor=tk.W, pady=(5, 0))

    def _open_url(self, url: str) -> None:
        """Open a URL in the default browser."""
        import webbrowser

        webbrowser.open(url)

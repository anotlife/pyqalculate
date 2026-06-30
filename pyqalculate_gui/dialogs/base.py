"""Base class for all modal dialogs."""

from __future__ import annotations

import tkinter as tk
from abc import ABC, abstractmethod
from typing import Any

from tkinter import ttk

from pyqalculate_gui.i18n import _
from pyqalculate_gui.theme import LIGHT, Theme


class ModalDialog(ABC):
    """Base class for all modal dialogs.

    Subclasses must implement ``_build_content`` to populate the dialog body.
    OK / Cancel buttons are provided automatically.
    """

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        size: tuple[int, int] = (400, 300),
        resizable: tuple[bool, bool] = (False, False),
        theme: Theme = LIGHT,
    ) -> None:
        self._parent = parent
        self._title = title
        self._size = size
        self._resizable = resizable
        self._theme = theme
        self._result: Any = None
        self._dialog: tk.Toplevel | None = None

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _build_content(self, parent: ttk.Frame) -> None:
        """Build dialog content inside *parent* frame.

        Subclasses must override this method.
        """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Show the dialog modally and block until closed."""
        self._dialog = tk.Toplevel(self._parent)
        self._dialog.title(self._title)
        self._dialog.geometry(f"{self._size[0]}x{self._size[1]}")
        self._dialog.resizable(*self._resizable)
        self._dialog.transient(self._parent)
        self._dialog.grab_set()

        # Apply theme background
        self._dialog.configure(bg=self._theme.bg)

        # Content area
        content = ttk.Frame(self._dialog, padding=10)
        content.pack(fill=tk.BOTH, expand=True)
        self._build_content(content)

        # Button row
        btn_frame = ttk.Frame(self._dialog, padding=(10, 0, 10, 10))
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text=_("OK"), command=self._on_ok).pack(
            side=tk.RIGHT, padx=5,
        )
        ttk.Button(btn_frame, text=_("Cancel"), command=self._on_cancel).pack(
            side=tk.RIGHT,
        )

        # Handle window-manager close button
        self._dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Centre on parent
        self._dialog.update_idletasks()
        x = (
            self._parent.winfo_x()
            + (self._parent.winfo_width() - self._dialog.winfo_width()) // 2
        )
        y = (
            self._parent.winfo_y()
            + (self._parent.winfo_height() - self._dialog.winfo_height()) // 2
        )
        self._dialog.geometry(f"+{x}+{y}")

        # Block until the dialog is destroyed
        self._parent.wait_window(self._dialog)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_ok(self) -> None:
        """Handle OK button press."""
        self._result = True
        self._close()

    def _on_cancel(self) -> None:
        """Handle Cancel button press or window close."""
        self._result = False
        self._close()

    def _close(self) -> None:
        """Destroy the dialog window."""
        if self._dialog is not None:
            self._dialog.destroy()
            self._dialog = None

    def get_result(self) -> Any:
        """Return the dialog result after ``show()`` has returned."""
        return self._result

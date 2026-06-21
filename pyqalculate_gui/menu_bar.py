"""Menu bar widget for the PyQalculate GUI."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from pyqalculate_gui.event_bus import (
    CLEAR_ALL,
    COPY_RESULT,
    OPEN_PLOT,
    OPEN_PREFERENCES,
    TOGGLE_CONVERSION,
    TOGGLE_HISTORY,
    TOGGLE_KEYPAD,
    EventBus,
)
from pyqalculate_gui.theme import LIGHT, Theme


class MenuBar:
    """Application menu bar wired to the event bus."""

    def __init__(
        self,
        parent: tk.Tk,
        theme: Theme = LIGHT,
        event_bus: EventBus | None = None,
    ) -> None:
        self._parent = parent
        self._theme = theme
        self._event_bus = event_bus
        self._exact_var = tk.BooleanVar(value=True)
        self._build_menu()

    # -- construction --------------------------------------------------------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self._parent)
        self._parent.config(menu=menubar)

        self._build_file_menu(menubar)
        self._build_edit_menu(menubar)
        self._build_mode_menu(menubar)
        self._build_view_menu(menubar)
        self._build_help_menu(menubar)
        self._bind_shortcuts()

    def _build_file_menu(self, menubar: tk.Menu) -> None:
        menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=menu)
        menu.add_command(
            label="Clear All", command=self._emit(CLEAR_ALL), accelerator="Ctrl+L"
        )
        menu.add_separator()
        menu.add_command(label="Import CSV...", command=lambda: None)
        menu.add_command(label="Export CSV...", command=lambda: None)
        menu.add_separator()
        menu.add_command(label="Exit", command=self._parent.quit)

    def _build_edit_menu(self, menubar: tk.Menu) -> None:
        menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=menu)
        menu.add_command(
            label="Copy Result", command=self._emit(COPY_RESULT), accelerator="Ctrl+C"
        )
        menu.add_command(label="Clear Expression", command=self._emit(CLEAR_ALL))

    def _build_mode_menu(self, menubar: tk.Menu) -> None:
        menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Mode", menu=menu)
        menu.add_checkbutton(label="Exact Mode", variable=self._exact_var)
        menu.add_separator()
        menu.add_command(label="Preferences...", command=self._emit(OPEN_PREFERENCES))

    def _build_view_menu(self, menubar: tk.Menu) -> None:
        menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=menu)
        menu.add_command(label="Toggle History", command=self._emit(TOGGLE_HISTORY))
        menu.add_command(label="Toggle Keypad", command=self._emit(TOGGLE_KEYPAD))
        menu.add_command(
            label="Toggle Conversion", command=self._emit(TOGGLE_CONVERSION)
        )
        menu.add_separator()
        menu.add_command(label="Plot...", command=self._emit(OPEN_PLOT))

    def _build_help_menu(self, menubar: tk.Menu) -> None:
        menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=menu)
        menu.add_command(label="About", command=self._show_about)

    def _bind_shortcuts(self) -> None:
        self._parent.bind("<Control-l>", lambda _: self._emit(CLEAR_ALL)())
        self._parent.bind("<Control-c>", lambda _: self._emit(COPY_RESULT)())
        self._parent.bind("<Control-p>", lambda _: self._emit(OPEN_PLOT)())

    # -- helpers -------------------------------------------------------------

    def _emit(self, event: str):  # noqa: ANN202
        """Return a callable that emits *event* on the bus."""

        def handler() -> None:
            if self._event_bus is not None:
                self._event_bus.emit(event)

        return handler

    def _show_about(self) -> None:
        messagebox.showinfo("About", "PyQalculate v3.0\nPure Python calculator")

    # -- public API ----------------------------------------------------------

    def get_exact_mode_var(self) -> tk.BooleanVar:
        """Return the BooleanVar backing the exact-mode checkbutton."""
        return self._exact_var

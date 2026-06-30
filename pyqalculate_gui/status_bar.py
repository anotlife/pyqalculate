"""Status bar widget showing calculator stats and mode."""

import tkinter as tk
from tkinter import ttk

from pyqalculate_gui.event_bus import MODE_CHANGED, EventBus
from pyqalculate_gui.i18n import _
from pyqalculate_gui.theme import LIGHT, Theme


class StatusBar(ttk.Frame):
    """Status bar displaying statistics and current calculation mode."""

    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme = LIGHT,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._event_bus = event_bus

        if self._event_bus:
            self._event_bus.subscribe(MODE_CHANGED, self._on_mode_changed)

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the status bar."""
        self._stats_var = tk.StringVar(
            value=_("Functions: {n_funcs} | Units: {n_units} | Variables: {n_vars}").format(
                n_funcs=0, n_units=0, n_vars=0
            )
        )
        self._stats_label = ttk.Label(
            self, textvariable=self._stats_var, font=self._theme.info_font
        )
        self._stats_label.pack(side=tk.LEFT, padx=10)

        self._mode_var = tk.StringVar(value=_("Approximate"))
        self._mode_label = ttk.Label(
            self, textvariable=self._mode_var, font=self._theme.info_font
        )
        self._mode_label.pack(side=tk.RIGHT, padx=10)

    def _on_mode_changed(self, exact: bool) -> None:
        """Handle mode change."""
        self.set_mode(exact)

    def update_stats(self, n_funcs: int, n_units: int, n_vars: int) -> None:
        """Update statistics display."""
        self._stats_var.set(
            _("Functions: {n_funcs} | Units: {n_units} | Variables: {n_vars}").format(
                n_funcs=n_funcs, n_units=n_units, n_vars=n_vars
            )
        )

    def set_mode(self, exact: bool) -> None:
        """Set mode display."""
        self._mode_var.set(_("Exact") if exact else _("Approximate"))

    def set_theme(self, theme: Theme) -> None:
        """Update the widget's theme."""
        self._theme = theme
        self._stats_label.config(font=theme.info_font)
        self._mode_label.config(font=theme.info_font)

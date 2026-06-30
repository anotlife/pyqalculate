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

        # Mode indicators (from expression status bar)
        self._mode_badges_var = tk.StringVar(value="")
        self._mode_badges_label = ttk.Label(
            self, textvariable=self._mode_badges_var, font=self._theme.info_font
        )
        self._mode_badges_label.pack(side=tk.RIGHT, padx=10)

    def _on_mode_changed(self, mode_info) -> None:
        """Update mode indicator badges."""
        indicators: list[str] = []
        if isinstance(mode_info, dict):
            if mode_info.get("exact", False):
                indicators.append(_("EXACT"))
            else:
                indicators.append(_("Approximate"))
            angle = mode_info.get("angle", "degrees")
            angle_map = {"degrees": _("DEG"), "radians": _("RAD"), "gradians": _("GRA")}
            if angle in angle_map:
                indicators.append(angle_map[angle])
        elif isinstance(mode_info, bool):
            indicators.append(_("EXACT") if mode_info else _("Approximate"))
        self._mode_badges_var.set("  ".join(indicators))

    def update_stats(self, n_funcs: int, n_units: int, n_vars: int) -> None:
        """Update statistics display."""
        self._stats_var.set(
            _("Functions: {n_funcs} | Units: {n_units} | Variables: {n_vars}").format(
                n_funcs=n_funcs, n_units=n_units, n_vars=n_vars
            )
        )

    def set_mode(self, exact: bool) -> None:
        """Set mode display."""  # no-op: mode display removed
        pass

    def set_theme(self, theme: Theme) -> None:
        """Update the widget's theme."""
        self._theme = theme
        self._stats_label.config(font=theme.info_font)
        self._mode_badges_label.config(font=theme.info_font)

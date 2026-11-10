"""Janela Repeat: número de repetições (ou até parar) e intervalo entre cliques."""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import customtkinter as ctk

import config
from ..widgets import NumberEntry, label, radio_button
from .base import ToolWindow

_INTERVAL_FIELDS = (("hours", "hours"), ("mins", "mins"), ("secs", "secs"), ("ms", "milliseconds"))


class RepeatWindow(ToolWindow):
    def __init__(self, master, on_change: Callable[[], None]) -> None:
        super().__init__(master, "Repeat", config.REPEAT_WIDTH)

        self._mode = ctk.StringVar(value="times")
        self._mode.trace_add("write", lambda *_: on_change())

        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 6))
        radio_button(row, "Repeat", self._mode, "times").pack(side="left")
        self._count = NumberEntry(row, width=64, default=config.DEFAULT_REPEAT_COUNT, on_change=on_change)
        self._count.pack(side="left", padx=8)
        label(row, "times").pack(side="left")

        radio_button(self.body, "Repeat until stopped", self._mode, "until").pack(anchor="w", pady=(0, 12))

        label(self.body, "Interval", muted=True).pack(anchor="w", pady=(0, 4))
        fields = ctk.CTkFrame(self.body, fg_color="transparent")
        fields.pack(fill="x")
        self._interval = {}
        for key, caption in _INTERVAL_FIELDS:
            cell = ctk.CTkFrame(fields, fg_color="transparent")
            cell.pack(side="left", padx=(0, 8))
            entry = NumberEntry(cell, width=56, on_change=on_change)
            entry.pack()
            label(cell, caption, muted=True).pack()
            self._interval[key] = entry

    @property
    def repeat_count(self) -> Optional[int]:
        """None = repetir até parar."""
        if self._mode.get() == "until":
            return None
        return max(1, self._count.value)

    @property
    def interval(self) -> float:
        """Intervalo total em segundos."""
        v = self._interval
        return (v["hours"].value * 3600 + v["mins"].value * 60
                + v["secs"].value + v["ms"].value / 1000)

    def get_state(self) -> Dict[str, Any]:
        return {
            "mode": self._mode.get(),
            "count": max(1, self._count.value),
            "interval": {key: entry.value for key, entry in self._interval.items()},
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        self._mode.set(state["mode"])
        self._count.set_value(state["count"])
        for key, entry in self._interval.items():
            entry.set_value(state["interval"][key])

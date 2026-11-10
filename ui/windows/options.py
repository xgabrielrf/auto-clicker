"""Janela Options: botão do mouse, tipo de clique e Freeze the pointer."""
from __future__ import annotations

from typing import Any, Callable, Dict

import customtkinter as ctk

import config
from ..widgets import check_box, label, segmented
from .base import ToolWindow


class OptionsWindow(ToolWindow):
    def __init__(self, master, on_change: Callable[[], None]) -> None:
        super().__init__(master, "Options", config.OPTIONS_WIDTH)

        self._mouse = ctk.StringVar(value=config.DEFAULT_MOUSE_BUTTON)
        self._click = ctk.StringVar(value=config.DEFAULT_CLICK_TYPE)
        self._freeze = ctk.BooleanVar(value=False)
        for var in (self._mouse, self._click, self._freeze):
            var.trace_add("write", lambda *_: on_change())

        grid = ctk.CTkFrame(self.body, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure(1, weight=1)

        label(grid, "Mouse", muted=True).grid(row=0, column=0, sticky="w", pady=4)
        segmented(grid, config.MOUSE_BUTTONS, self._mouse).grid(row=0, column=1, sticky="e", pady=4)

        label(grid, "Click", muted=True).grid(row=1, column=0, sticky="w", pady=4)
        segmented(grid, config.CLICK_TYPES, self._click).grid(row=1, column=1, sticky="e", pady=4)

        check_box(self.body, "Freeze the pointer", self._freeze).pack(anchor="w", pady=(10, 0))

    @property
    def button(self) -> str:
        return self._mouse.get()

    @property
    def double(self) -> bool:
        return self._click.get() == "Double"

    @property
    def freeze(self) -> bool:
        return self._freeze.get()

    def get_state(self) -> Dict[str, Any]:
        return {"button": self.button, "double": self.double, "freeze": self.freeze}

    def set_state(self, state: Dict[str, Any]) -> None:
        self._mouse.set(state["button"])
        self._click.set("Double" if state["double"] else "Single")
        self._freeze.set(state["freeze"])

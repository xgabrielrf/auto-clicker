"""Janela Hotkey Setting: escolhe a tecla que inicia/para o clicker."""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

import config
from core.capture import KeyCapture
from core.hotkey import HotkeyManager
from core.keys import display_name
from .. import theme
from ..widgets import ghost_button, label, red_button
from .base import ToolWindow


class HotkeyWindow(ToolWindow):
    """Modal. Enquanto aberta, qualquer tecla pressionada vira a candidata (captura global
    via pynput) e a hotkey atual fica suspensa. Ok aplica; Cancel/fechar descarta."""

    def __init__(self, master, hotkey: HotkeyManager, post: Callable[..., None],
                 on_apply: Callable[[str], None]) -> None:
        super().__init__(master, "Hotkey Setting", config.HOTKEY_WIDTH)
        self._hotkey = hotkey
        self._on_apply = on_apply
        self._pending = hotkey.hotkey
        self._capture = KeyCapture(lambda name: post(self._key_pressed, name), once=False)

        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=(8, 4))
        row.grid_columnconfigure((0, 1), weight=1, uniform="cols")
        ctk.CTkLabel(row, text="Click / Stop", height=44, corner_radius=6, fg_color=theme.ELEVATED,
                     text_color=theme.TEXT, font=theme.font()).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._box = ctk.CTkLabel(row, text="", height=44, corner_radius=6, fg_color=theme.ELEVATED,
                                 text_color=theme.TEXT, font=theme.font(20, "bold"))
        self._box.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        label(self.body, "Press the key you want to use", muted=True).pack(pady=(4, 12))

        buttons = ctk.CTkFrame(self.body, fg_color="transparent")
        buttons.pack()
        red_button(buttons, "Ok", self._ok, width=90).pack(side="left", padx=6)
        ghost_button(buttons, "Cancel", self.hide, width=90).pack(side="left", padx=6)

    def open(self) -> None:
        self._pending = self._hotkey.hotkey
        self._box.configure(text=display_name(self._pending))
        self._hotkey.suspended = True
        self._capture.start()
        self.show()
        self.after(60, self._grab)

    def hide(self) -> None:
        self._capture.cancel()
        self._hotkey.suspended = False
        try:
            self.grab_release()
        except Exception:  # noqa: BLE001 - sem grab ativo
            pass
        super().hide()

    def _grab(self) -> None:
        try:
            if self.visible:
                self.grab_set()
        except Exception:  # noqa: BLE001 - janela ainda não visível; segue sem modal
            pass

    def _key_pressed(self, name: str) -> None:
        if not self.visible:
            return
        self._pending = name
        self._box.configure(text=display_name(name))

    def _ok(self) -> None:
        self._on_apply(self._pending)
        self.hide()

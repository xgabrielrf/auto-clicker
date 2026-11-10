"""Barra de menu superior (estilo VS Code). Customizada porque a barra nativa do Windows
não aceita tema dark."""
from __future__ import annotations

from typing import Callable, Sequence, Tuple

import customtkinter as ctk

from . import theme


class MenuBar(ctk.CTkFrame):
    """Botões planos; cada um chama seu comando (aqui, abre uma janela).
    `trailing` é um texto discreto alinhado à direita (ex.: a versão)."""

    def __init__(self, master, items: Sequence[Tuple[str, Callable[[], None]]], trailing: str = "") -> None:
        super().__init__(master, fg_color=theme.BG, corner_radius=0)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=4, pady=2)
        self._buttons = []
        for text, command in items:
            button = ctk.CTkButton(
                row, text=text, command=command, width=0, height=24, corner_radius=4,
                fg_color="transparent", hover_color=theme.ELEVATED,
                text_color=theme.TEXT_MUTED, text_color_disabled=theme.TEXT_DISABLED,
                font=theme.font(theme.FONT_SIZE),
            )
            button.pack(side="left", padx=1)
            self._buttons.append(button)
        if trailing:
            ctk.CTkLabel(row, text=trailing, text_color=theme.TEXT_FAINT,
                         font=theme.font(theme.FONT_SMALL)).pack(side="right", padx=(0, 8))

        ctk.CTkFrame(self, height=1, fg_color=theme.BORDER, corner_radius=0).pack(fill="x")

    def set_enabled(self, enabled: bool) -> None:
        for button in self._buttons:
            button.configure(state="normal" if enabled else "disabled")

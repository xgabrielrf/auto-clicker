"""Widgets reutilizáveis com o tema do app."""
from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from . import theme


class NumberEntry(ctk.CTkEntry):
    """Entrada numérica inteira (aceita só dígitos); `value` devolve int com fallback.

    `on_change` é chamado a cada alteração do conteúdo.
    """

    def __init__(self, master, width: int = 54, default: int = 0,
                 on_change: Optional[Callable[[], None]] = None, **kwargs) -> None:
        self._default = default
        self._on_change = on_change
        self._var = ctk.StringVar(value=str(default))
        super().__init__(
            master, width=width, height=28, justify="center", textvariable=self._var,
            fg_color=theme.ELEVATED, border_color=theme.BORDER, text_color=theme.TEXT,
            font=theme.font(), **kwargs,
        )
        self._var.trace_add("write", self._changed)
        self.bind("<FocusOut>", self._normalize)

    def _changed(self, *_) -> None:
        text = self._var.get()
        clean = "".join(ch for ch in text if ch.isdigit())[:9]
        if clean != text:
            self._var.set(clean)            # dispara de novo; o on_change roda na 2ª passada
            return
        if self._on_change:
            self._on_change()

    def _normalize(self, _event=None) -> None:
        if not self._var.get():
            self._var.set(str(self._default))

    @property
    def value(self) -> int:
        try:
            return int(self._var.get())
        except ValueError:
            return self._default

    def set_value(self, value: int) -> None:
        self._var.set(str(value))


def red_button(master, text: str, command, width: int = 110, height: int = 30, **kwargs) -> ctk.CTkButton:
    return ctk.CTkButton(
        master, text=text, command=command, width=width, height=height,
        fg_color=theme.RED, hover_color=theme.RED_HOVER, text_color="#ffffff",
        text_color_disabled=theme.TEXT_DISABLED, font=theme.font(theme.FONT_SIZE, "bold"),
        corner_radius=6, **kwargs,
    )


def ghost_button(master, text: str, command, width: int = 90, height: int = 30, **kwargs) -> ctk.CTkButton:
    return ctk.CTkButton(
        master, text=text, command=command, width=width, height=height,
        fg_color=theme.ELEVATED, hover_color=theme.RED_DARK, text_color=theme.TEXT,
        text_color_disabled=theme.TEXT_DISABLED, border_width=1, border_color=theme.BORDER,
        font=theme.font(), corner_radius=6, **kwargs,
    )


def label(master, text: str, muted: bool = False, **kwargs) -> ctk.CTkLabel:
    return ctk.CTkLabel(master, text=text, font=theme.font(),
                        text_color=theme.TEXT_MUTED if muted else theme.TEXT, **kwargs)


def check_box(master, text: str, variable=None, command=None) -> ctk.CTkCheckBox:
    return ctk.CTkCheckBox(
        master, text=text, variable=variable, command=command, font=theme.font(),
        text_color=theme.TEXT, text_color_disabled=theme.TEXT_DISABLED,
        fg_color=theme.RED, hover_color=theme.RED_HOVER, border_color=theme.BORDER,
        checkmark_color="#ffffff", corner_radius=4, border_width=2,
        checkbox_width=18, checkbox_height=18,
    )


def radio_button(master, text: str, variable, value, command=None) -> ctk.CTkRadioButton:
    return ctk.CTkRadioButton(
        master, text=text, variable=variable, value=value, command=command, font=theme.font(),
        text_color=theme.TEXT, text_color_disabled=theme.TEXT_DISABLED,
        fg_color=theme.RED, hover_color=theme.RED_HOVER, border_color=theme.BORDER,
        radiobutton_width=18, radiobutton_height=18, border_width_checked=5,
    )


def segmented(master, values, variable, command=None) -> ctk.CTkSegmentedButton:
    return ctk.CTkSegmentedButton(
        master, values=list(values), variable=variable, command=command, font=theme.font(),
        fg_color=theme.ELEVATED, selected_color=theme.RED, selected_hover_color=theme.RED_HOVER,
        unselected_color=theme.ELEVATED, unselected_hover_color=theme.RED_DARK,
        text_color=theme.TEXT, height=28, border_width=2,
    )

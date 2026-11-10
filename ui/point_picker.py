"""Overlay de tela cheia para escolher um ponto com o próximo clique."""
from __future__ import annotations

import ctypes
import tkinter as tk
from typing import Callable

from . import theme

_SM_XVIRTUALSCREEN, _SM_YVIRTUALSCREEN, _SM_CXVIRTUALSCREEN, _SM_CYVIRTUALSCREEN = 76, 77, 78, 79


def _virtual_screen() -> tuple:
    metrics = ctypes.windll.user32.GetSystemMetrics
    return (metrics(_SM_XVIRTUALSCREEN), metrics(_SM_YVIRTUALSCREEN),
            metrics(_SM_CXVIRTUALSCREEN), metrics(_SM_CYVIRTUALSCREEN))


class PointPicker:
    """Cobre todos os monitores com uma camada translúcida.

    O clique é engolido pelo overlay (não atinge o app embaixo). A posição é lida do
    backend de entrada, o mesmo sistema de coordenadas usado no replay. Esc / botão
    direito cancelam.
    """

    def __init__(self, root: tk.Misc, backend, on_pick: Callable[[int, int], None],
                 on_cancel: Callable[[], None]) -> None:
        self._root = root
        self._backend = backend
        self._on_pick = on_pick
        self._on_cancel = on_cancel
        self._top: tk.Toplevel | None = None

    def start(self) -> None:
        x, y, w, h = _virtual_screen()
        top = tk.Toplevel(self._root, bg=theme.RED_DARK, cursor="crosshair")
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.attributes("-alpha", 0.25)
        top.geometry(f"{w}x{h}+{x}+{y}")
        tk.Label(top, text="Click anywhere to pick a point   ·   Esc to cancel",
                 bg=theme.RED_DARK, fg=theme.TEXT, font=theme.font(16, "bold")).place(relx=0.5, rely=0.08, anchor="center")
        top.bind("<ButtonRelease-1>", self._picked)
        top.bind("<Button-3>", lambda _e: self._finish(None))
        top.bind("<Escape>", lambda _e: self._finish(None))
        top.focus_force()
        self._top = top

    def _picked(self, _event) -> None:
        self._finish(tuple(self._backend.position))

    def _finish(self, point) -> None:
        if self._top is None:
            return
        self._top.destroy()
        self._top = None
        if point is None:
            self._on_cancel()
        else:
            self._on_pick(*point)

"""Base das janelas secundárias (Options, Repeat, Recording, Hotkey)."""
from __future__ import annotations

import tkinter
from typing import Callable, Optional

import customtkinter as ctk

from .. import theme
from ..icon import apply_icon


class ToolWindow(ctk.CTkToplevel):
    """Janela de largura fixa e altura automática.

    Fechar apenas esconde (`withdraw`): os widgets e seus valores continuam existindo,
    então o app pode ler/gravar o estado mesmo com a janela fechada.
    """

    def __init__(self, master, title: str, width: int) -> None:
        super().__init__(master, fg_color=theme.BG)
        self.withdraw()
        self.on_hide: Optional[Callable[[], None]] = None   # o app usa para reabilitar o clicker
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self.bind("<Escape>", lambda _e: self.hide())

        # "Strut" que fixa a largura; a altura segue o conteúdo.
        ctk.CTkFrame(self, width=width, height=0, fg_color="transparent").pack()
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=16, pady=(4, 16))

    def _windows_set_titlebar_icon(self) -> None:
        """O CTk aplicaria o ícone azul padrão ~200 ms após abrir; mantemos o nosso."""
        apply_icon(self)

    @property
    def visible(self) -> bool:
        return self.state() != "withdrawn"

    def show(self) -> None:
        """Abre ao lado da janela principal (ou só traz para frente se já estiver aberta)."""
        if not self.visible:
            self._place_beside_master()
            self.deiconify()
        self.lift()
        self.focus_force()

    def hide(self) -> None:
        was_visible = self.visible
        self.withdraw()
        if was_visible and self.on_hide:
            self.on_hide()

    def _place_beside_master(self) -> None:
        main = self.master
        main.update_idletasks()
        self.update_idletasks()
        width = self.winfo_reqwidth()
        x = main.winfo_rootx() + main.winfo_width() + 12
        if x + width > self.winfo_screenwidth():
            x = max(0, main.winfo_rootx() - width - 12)
        y = max(0, main.winfo_rooty() - 31)           # alinha com o topo da barra de título
        tkinter.Wm.wm_geometry(self, f"+{x}+{y}")     # CTk.geometry escalaria x/y

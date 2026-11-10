"""Ícone do app (embutido em base64) para janela e barra de tarefas."""
from __future__ import annotations

import ctypes
import tkinter as tk

import config
from assets.icon_data import ICON_B64


def set_app_id() -> None:
    """Evita que o Windows agrupe o app com o python.exe (ícone correto na barra de tarefas)."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(config.APP_ID)
    except (AttributeError, OSError):
        pass


def apply_icon(window: tk.Misc) -> None:
    """Aplica o ícone na janela (e, por consequência, na barra de tarefas)."""
    image = tk.PhotoImage(master=window, data=ICON_B64)
    window._icon_image = image          # referência: sem ela o Tk descarta a imagem
    window.iconphoto(True, image)

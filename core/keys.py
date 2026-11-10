"""Conversão entre teclas do pynput e nomes simples (strings)."""
from __future__ import annotations

from typing import Optional

from pynput.keyboard import Key, KeyCode


def key_to_str(key) -> Optional[str]:
    """Key/KeyCode do pynput -> 'f8', 'enter', 'a'. None se não for representável."""
    if isinstance(key, Key):
        return key.name
    if isinstance(key, KeyCode):
        if key.char:
            return key.char.lower()
        if key.vk is not None:
            return f"vk{key.vk}"
    return None


def str_to_key(name: str):
    """Inverso de key_to_str."""
    if name.startswith("vk") and name[2:].isdigit():
        return KeyCode.from_vk(int(name[2:]))
    try:
        return Key[name]
    except KeyError:
        return KeyCode.from_char(name)


def display_name(name: str) -> str:
    """Nome amigável para a UI: F8, A, Enter, Space."""
    if name.startswith("vk"):
        return name.upper()
    if len(name) == 1 or (name[0] == "f" and name[1:].isdigit()):
        return name.upper()
    return name.replace("_", " ").title()

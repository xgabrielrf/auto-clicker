"""Camada fina sobre o pynput. O engine só depende desta interface (fácil de trocar em testes)."""
from __future__ import annotations

from typing import Tuple

from pynput import keyboard, mouse

from .keys import str_to_key

_BUTTONS = {
    "Left": mouse.Button.left,
    "Right": mouse.Button.right,
    "Middle": mouse.Button.middle,
}


class InputBackend:
    def __init__(self) -> None:
        self._mouse = mouse.Controller()
        self._keyboard = keyboard.Controller()

    @property
    def position(self) -> Tuple[int, int]:
        return self._mouse.position

    def move(self, x: int, y: int) -> None:
        self._mouse.position = (x, y)

    def click(self, button: str, double: bool = False) -> None:
        self._mouse.click(_BUTTONS[button], 2 if double else 1)

    def press_key(self, name: str) -> None:
        key = str_to_key(name)
        self._keyboard.press(key)
        self._keyboard.release(key)

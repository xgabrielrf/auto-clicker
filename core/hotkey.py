"""Hotkey global (liga/desliga) via listener do pynput."""
from __future__ import annotations

from typing import Callable

from pynput import keyboard

from .keys import key_to_str


class HotkeyManager:
    def __init__(self, hotkey: str, on_toggle: Callable[[], None]) -> None:
        self.hotkey = hotkey
        self.suspended = False          # True enquanto outra captura de tecla está ativa
        self._on_toggle = on_toggle
        self._down = False              # evita repetição automática enquanto a tecla está pressionada
        self._listener = keyboard.Listener(on_press=self._pressed, on_release=self._released)

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()

    def _pressed(self, key) -> None:
        if self.suspended or key_to_str(key) != self.hotkey or self._down:
            return
        self._down = True
        self._on_toggle()

    def _released(self, key) -> None:
        if key_to_str(key) == self.hotkey:
            self._down = False

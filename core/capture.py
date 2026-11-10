"""Captura de teclas (usada em 'Add Key' e na janela Hotkey Setting)."""
from __future__ import annotations

from typing import Callable, Optional

from pynput import keyboard

from .keys import key_to_str


class KeyCapture:
    """Escuta globalmente e entrega as teclas pressionadas.

    once=True  -> entrega só a primeira tecla e encerra (Add Key).
    once=False -> continua escutando até `cancel()` (Hotkey Setting).

    `on_key(name)` roda na thread do listener — a UI deve reencaminhar com `after`.
    """

    def __init__(self, on_key: Callable[[str], None], once: bool = True) -> None:
        self._on_key = on_key
        self._once = once
        self._listener: Optional[keyboard.Listener] = None

    def start(self) -> None:
        self.cancel()
        self._listener = keyboard.Listener(on_press=self._pressed)
        self._listener.start()

    def cancel(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _pressed(self, key):
        name = key_to_str(key)
        if name is None:
            return None                 # ignora e continua escutando
        self._on_key(name)
        return False if self._once else None   # False encerra o listener

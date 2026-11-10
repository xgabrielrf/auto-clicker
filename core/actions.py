"""Passos gravados no modo Recording."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Union

import config


@dataclass(frozen=True)
class ClickAction:
    x: int
    y: int
    button: str = "Left"      # Left | Right | Middle
    double: bool = False

    def label(self) -> str:
        kind = "Double" if self.double else "Single"
        return f"{self.button} · {kind} @ ({self.x}, {self.y})"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "click", "x": self.x, "y": self.y, "button": self.button, "double": self.double}


@dataclass(frozen=True)
class KeyAction:
    key: str                  # nome serializado, ex.: "enter", "a", "f5"

    def label(self) -> str:
        return f"Key: {self.key}"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "key", "key": self.key}


Action = Union[ClickAction, KeyAction]


def action_from_dict(data: Any) -> Action:
    """Reconstrói um passo a partir de um dict; levanta ValueError se for inválido."""
    if not isinstance(data, dict):
        raise ValueError("step is not an object")
    kind = data.get("type")
    if kind == "click":
        x, y = data.get("x"), data.get("y")
        button = data.get("button", "Left")
        double = data.get("double", False)
        if (type(x) is not int or type(y) is not int or button not in config.MOUSE_BUTTONS
                or not isinstance(double, bool)):
            raise ValueError("invalid click step")
        return ClickAction(x, y, button, double)
    if kind == "key":
        key = data.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError("invalid key step")
        return KeyAction(key)
    raise ValueError(f"unknown step type: {kind!r}")

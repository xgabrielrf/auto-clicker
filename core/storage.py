"""Persistência: estado automático (arquivo local) e arquivos de sequência (.acseq)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import config
from .actions import Action, action_from_dict


class SequenceError(Exception):
    """Arquivo de sequência ilegível ou inválido (a mensagem é exibida ao usuário)."""


# ----------------------------------------------------------------------------- local
def app_dir() -> Path:
    """Pasta onde o programa foi iniciado: a do .exe (empacotado) ou a raiz do projeto."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


# ----------------------------------------------------------------------------- estado
def default_state() -> Dict[str, Any]:
    return {
        "version": config.STATE_VERSION,
        "hotkey": config.DEFAULT_HOTKEY,
        "options": {"button": config.DEFAULT_MOUSE_BUTTON, "double": False, "freeze": False},
        "repeat": {
            "mode": "times",
            "count": config.DEFAULT_REPEAT_COUNT,
            "interval": {"hours": 0, "mins": 0, "secs": 0, "ms": 0},
        },
    }


def _nonneg_int(value: Any, default: int) -> int:
    return value if type(value) is int and 0 <= value <= 999_999_999 else default


def normalize_state(raw: Any) -> Dict[str, Any]:
    """Valida cada campo do estado lido do disco; o que for inválido volta ao padrão."""
    state = default_state()
    if not isinstance(raw, dict):
        return state

    hotkey = raw.get("hotkey")
    if isinstance(hotkey, str) and hotkey:
        state["hotkey"] = hotkey

    options = raw.get("options")
    if isinstance(options, dict):
        if options.get("button") in config.MOUSE_BUTTONS:
            state["options"]["button"] = options["button"]
        for key in ("double", "freeze"):
            if isinstance(options.get(key), bool):
                state["options"][key] = options[key]

    repeat = raw.get("repeat")
    if isinstance(repeat, dict):
        if repeat.get("mode") in ("times", "until"):
            state["repeat"]["mode"] = repeat["mode"]
        state["repeat"]["count"] = max(1, _nonneg_int(repeat.get("count"), config.DEFAULT_REPEAT_COUNT))
        interval = repeat.get("interval")
        if isinstance(interval, dict):
            for key in ("hours", "mins", "secs", "ms"):
                state["repeat"]["interval"][key] = _nonneg_int(interval.get(key), 0)

    recording = raw.get("recording")
    if isinstance(recording, dict):
        steps = []
        for item in recording.get("steps", []) if isinstance(recording.get("steps"), list) else []:
            try:
                steps.append(action_from_dict(item).to_dict())
            except ValueError:
                continue                       # passo inválido é descartado
        enabled = recording.get("enabled")
        state["recording"] = {"enabled": enabled if isinstance(enabled, bool) else False, "steps": steps}
    return state


class StateStore:
    """Lê/grava o estado em `auto-clicker-state.json` (junto ao programa)."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else app_dir() / config.STATE_FILE
        self._recording_used = False
        self.warning: Optional[str] = None      # mensagem se o arquivo existente estava corrompido

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return default_state()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("root is not an object")
        except (OSError, ValueError):
            self._quarantine()
            return default_state()
        state = normalize_state(raw)
        self._recording_used = "recording" in state
        return state

    def save(self, state: Dict[str, Any]) -> None:
        """Grava de forma atômica. O bloco `recording` só entra depois que o Recording
        foi selecionado alguma vez (ou já existia no arquivo carregado)."""
        out = dict(state)
        recording = out.get("recording")
        if isinstance(recording, dict) and recording.get("enabled"):
            self._recording_used = True
        if not self._recording_used:
            out.pop("recording", None)
        tmp = self.path.with_name(self.path.name + ".tmp")
        try:
            tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError as exc:
            self.warning = f"Could not save settings: {exc}"

    def _quarantine(self) -> None:
        backup = self.path.with_name(self.path.name + ".corrupt")
        try:
            os.replace(self.path, backup)
            self.warning = f"Settings file was unreadable; moved to {backup.name}"
        except OSError:
            self.warning = "Settings file was unreadable; using defaults"


# ----------------------------------------------------------------------------- sequência (.acseq)
def save_sequence(path: str, steps: Sequence[Action]) -> None:
    payload = {
        "format": config.SEQUENCE_FORMAT,
        "version": config.SEQUENCE_VERSION,
        "steps": [step.to_dict() for step in steps],
    }
    try:
        Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        raise SequenceError(f"Could not write file: {exc}") from exc


def load_sequence(path: str) -> List[Action]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise SequenceError(f"Could not read file: {exc}") from exc
    except ValueError as exc:
        raise SequenceError("Not a valid Auto Clicker sequence file.") from exc

    if not isinstance(raw, dict) or raw.get("format") != config.SEQUENCE_FORMAT:
        raise SequenceError("Not an Auto Clicker sequence file.")
    version = raw.get("version")
    if version != config.SEQUENCE_VERSION:
        raise SequenceError(f"Unsupported sequence file version: {version!r}.")
    steps = raw.get("steps")
    if not isinstance(steps, list):
        raise SequenceError("Sequence file has no step list.")

    result: List[Action] = []
    for index, item in enumerate(steps, start=1):
        try:
            result.append(action_from_dict(item))
        except ValueError as exc:
            raise SequenceError(f"Step {index} is invalid ({exc}).") from exc
    return result

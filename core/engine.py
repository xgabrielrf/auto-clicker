"""Motor de cliques: roda numa thread própria e não conhece a UI."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import config
from .actions import Action, ClickAction, KeyAction


@dataclass
class ClickerConfig:
    button: str = config.DEFAULT_MOUSE_BUTTON
    double: bool = False
    freeze: bool = False
    repeat_count: Optional[int] = config.DEFAULT_REPEAT_COUNT   # None = até parar
    interval: float = 0.0                                       # segundos
    steps: List[Action] = field(default_factory=list)           # vazio = clique simples


class ClickEngine:
    """Executa a configuração numa thread daemon.

    Callbacks (chamados na thread do engine — a UI deve reencaminhá-los com `after`):
      on_count(n)          a cada ação executada
      on_finish(error)     ao terminar (error = None se encerrou normalmente)
    """

    def __init__(
        self,
        backend,
        on_count: Optional[Callable[[int], None]] = None,
        on_finish: Optional[Callable[[Optional[str]], None]] = None,
    ) -> None:
        self._backend = backend
        self._on_count = on_count or (lambda n: None)
        self._on_finish = on_finish or (lambda err: None)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.count = 0

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, cfg: ClickerConfig) -> bool:
        if self.running:
            return False
        self._stop.clear()
        self.count = 0
        self._thread = threading.Thread(target=self._run, args=(cfg,), daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()

    def join(self, timeout: Optional[float] = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout)

    # ------------------------------------------------------------------ interno
    def _run(self, cfg: ClickerConfig) -> None:
        error: Optional[str] = None
        try:
            self._loop(cfg)
        except Exception as exc:  # noqa: BLE001 - qualquer falha do backend vira mensagem na UI
            error = str(exc) or exc.__class__.__name__
        finally:
            self._on_finish(error)

    def _loop(self, cfg: ClickerConfig) -> None:
        interval = max(cfg.interval, config.MIN_INTERVAL)
        simple = not cfg.steps
        steps = list(cfg.steps) or [ClickAction(-1, -1, cfg.button, cfg.double)]
        anchor: Tuple[int, int] = tuple(self._backend.position)
        cycles = 0

        while not self._stop.is_set():
            for index, action in enumerate(steps):
                if self._stop.is_set():
                    return
                anchor = self._perform(action, anchor, cfg.freeze, simple)
                self.count += 1
                self._on_count(self.count)

                last_of_run = (
                    cfg.repeat_count is not None
                    and cycles + 1 >= cfg.repeat_count
                    and index == len(steps) - 1
                )
                if last_of_run:
                    return
                self._wait(interval, anchor if cfg.freeze else None)
            cycles += 1

    def _perform(self, action: Action, anchor: Tuple[int, int], freeze: bool, simple: bool) -> Tuple[int, int]:
        if isinstance(action, ClickAction):
            if simple:
                if freeze:
                    self._hold(anchor)          # clica sempre no ponto em que começou
            else:
                self._backend.move(action.x, action.y)
                anchor = (action.x, action.y)
            self._backend.click(action.button, action.double)
        elif isinstance(action, KeyAction):
            if freeze:
                self._hold(anchor)
            self._backend.press_key(action.key)
        return anchor

    def _hold(self, anchor: Tuple[int, int]) -> None:
        if tuple(self._backend.position) != anchor:
            self._backend.move(*anchor)

    def _wait(self, seconds: float, hold_at: Optional[Tuple[int, int]]) -> None:
        """Espera interrompível; com `hold_at`, reposiciona o ponteiro a cada fatia."""
        if hold_at is None:
            self._stop.wait(seconds)
            return
        end = time.monotonic() + seconds
        while not self._stop.is_set():
            remaining = end - time.monotonic()
            if remaining <= 0:
                break
            self._hold(hold_at)
            self._stop.wait(min(config.WAIT_SLICE, remaining))

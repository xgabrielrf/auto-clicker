"""Janela principal: menu superior, botão da hotkey, status; liga a UI ao engine e ao estado salvo."""
from __future__ import annotations

import queue
import tkinter
from typing import Any, Callable, Dict, Optional

import customtkinter as ctk

import config
from core.actions import ClickAction, KeyAction
from core.capture import KeyCapture
from core.engine import ClickEngine, ClickerConfig
from core.hotkey import HotkeyManager
from core.input_backend import InputBackend
from core.keys import display_name
from core.storage import StateStore
from . import theme
from .icon import apply_icon, set_app_id
from .menubar import MenuBar
from .point_picker import PointPicker
from .widgets import red_button
from .windows.hotkey import HotkeyWindow
from .windows.options import OptionsWindow
from .windows.recording import RecordingWindow
from .windows.repeat import RepeatWindow

_POLL_MS = 40


class App(ctk.CTk):
    def __init__(self, store: Optional[StateStore] = None) -> None:
        set_app_id()
        ctk.set_appearance_mode("dark")
        super().__init__(fg_color=theme.BG)

        self.title(config.APP_NAME)
        self.resizable(False, False)
        apply_icon(self)

        # Threads do pynput/engine nunca mexem no Tk: entregam eventos nesta fila,
        # drenada na thread principal.
        self._events: "queue.SimpleQueue[Callable[[], None]]" = queue.SimpleQueue()

        self._store = store or StateStore()
        state = self._store.load()

        self._backend = InputBackend()
        self._engine = ClickEngine(
            self._backend,
            on_count=lambda n: self._post(self._on_count, n),
            on_finish=lambda err: self._post(self._on_finish, err),
        )
        self._hotkey = HotkeyManager(state["hotkey"], lambda: self._post(self._toggle))
        self._capture: Optional[KeyCapture] = None       # Add Key (uma tecla)
        self._counting_label = "clicks"
        self._picking = False
        self._recording_was_open = False
        self._restoring = True                           # evita regravar enquanto restaura o estado
        self._save_job: Optional[str] = None

        self._build()
        self._apply_state(state)
        self._restoring = False
        self._center_on_screen()

        self._hotkey.start()
        self._poll()
        self.protocol("WM_DELETE_WINDOW", self._close)
        if self._store.warning:
            self._set_status(self._store.warning, error=True)

    def _windows_set_titlebar_icon(self) -> None:
        """O CTk aplicaria o ícone azul padrão ~200 ms após abrir; mantemos o nosso."""
        apply_icon(self)

    # ---------------------------------------------------------------- layout
    def _build(self) -> None:
        # "Strut" que fixa a largura; a altura segue o conteúdo.
        ctk.CTkFrame(self, width=config.WINDOW_WIDTH, height=0, fg_color="transparent").pack()

        self._options = OptionsWindow(self, on_change=self._changed_soon)
        self._repeat = RepeatWindow(self, on_change=self._changed_soon)
        self._recording = RecordingWindow(
            self, on_pick=self._pick_point, on_add_key=self._on_add_key,
            on_change=self._changed_now, on_message=self._set_status,
        )
        self._hotkey_window = HotkeyWindow(self, self._hotkey, self._post, self._apply_hotkey)

        MenuBar(self, [
            ("Options", self._options.show),
            ("Repeat", self._repeat.show),
            ("Recording", self._recording.show),
        ], trailing=f"v{config.APP_VERSION}").pack(fill="x")

        self._main_button = red_button(self, "", self._hotkey_window.open, height=56)
        self._main_button.pack(fill="x", padx=14, pady=(14, 8))

        self._status = ctk.CTkLabel(self, text="", anchor="w", font=theme.font(theme.FONT_SMALL),
                                    text_color=theme.TEXT_MUTED, wraplength=config.WINDOW_WIDTH - 32,
                                    justify="left")
        self._status.pack(fill="x", padx=16, pady=(0, 10))
        self._set_status("Idle")

    def _center_on_screen(self) -> None:
        """Abre sempre no centro da tela (Wm.wm_geometry: o CTk.geometry escalaria x/y)."""
        self.withdraw()                      # evita piscar em outro lugar enquanto mede
        self.update()
        border = self.winfo_rootx() - self.winfo_x()          # borda lateral/inferior
        titlebar = self.winfo_rooty() - self.winfo_y()        # barra de título (+ borda superior)
        outer_w = self.winfo_reqwidth() + 2 * border
        outer_h = self.winfo_reqheight() + titlebar + border
        x = max((self.winfo_screenwidth() - outer_w) // 2, 0)
        y = max((self.winfo_screenheight() - outer_h) // 2, 0)
        tkinter.Wm.wm_geometry(self, f"+{x}+{y}")
        self.deiconify()

    def _refresh_main_button(self) -> None:
        verb = "stop" if self._engine.running else "click"
        self._main_button.configure(text=f"Press {display_name(self._hotkey.hotkey)} to {verb}")

    def _set_status(self, text: str, error: bool = False) -> None:
        self._status.configure(text=text, text_color=theme.RED_HOVER if error else theme.TEXT_MUTED)

    # ---------------------------------------------------------------- estado salvo
    def _apply_state(self, state: Dict[str, Any]) -> None:
        self._options.set_state(state["options"])
        self._repeat.set_state(state["repeat"])
        if "recording" in state:
            self._recording.set_state(state["recording"])
        self._refresh_main_button()

    def _collect_state(self) -> Dict[str, Any]:
        return {
            "version": config.STATE_VERSION,
            "hotkey": self._hotkey.hotkey,
            "options": self._options.get_state(),
            "repeat": self._repeat.get_state(),
            "recording": self._recording.get_state(),
        }

    def _changed_now(self) -> None:
        """Mudança discreta (passos, checkbox): grava na hora."""
        if not self._restoring:
            self._save_now()

    def _changed_soon(self) -> None:
        """Mudança em campo de texto/opção: grava após uma pausa curta."""
        if self._restoring:
            return
        if self._save_job is not None:
            self.after_cancel(self._save_job)
        self._save_job = self.after(config.SAVE_DEBOUNCE_MS, self._save_now)

    def _save_now(self) -> None:
        if self._save_job is not None:
            self.after_cancel(self._save_job)
            self._save_job = None
        self._store.save(self._collect_state())
        if self._store.warning:
            self._set_status(self._store.warning, error=True)
            self._store.warning = None

    # ---------------------------------------------------------------- fila de eventos
    def _post(self, fn: Callable, *args) -> None:
        self._events.put(lambda: fn(*args))

    def _poll(self) -> None:
        try:
            while True:
                self._events.get_nowait()()
        except queue.Empty:
            pass
        self.after(_POLL_MS, self._poll)

    # ---------------------------------------------------------------- Start / Stop (hotkey)
    def _toggle(self) -> None:
        if self._picking:
            return
        if self._engine.running:
            self._engine.stop()
            return
        cfg = self._build_config()
        if cfg is None:
            return
        self._counting_label = "actions" if cfg.steps else "clicks"
        if self._engine.start(cfg):
            self._refresh_main_button()
            self._set_status(f"Running · 0 {self._counting_label}")

    def _build_config(self) -> Optional[ClickerConfig]:
        steps = []
        if self._recording.enabled:
            steps = self._recording.steps
            if not steps:
                self._set_status("Add at least one step in Recording (Pick point / Add Key).", error=True)
                return None
        return ClickerConfig(
            button=self._options.button,
            double=self._options.double,
            freeze=self._options.freeze,
            repeat_count=self._repeat.repeat_count,
            interval=self._repeat.interval,
            steps=steps,
        )

    def _on_count(self, n: int) -> None:
        if self._engine.running:
            self._set_status(f"Running · {n} {self._counting_label}")

    def _on_finish(self, error: Optional[str]) -> None:
        self._refresh_main_button()
        total = self._engine.count
        if error:
            self._set_status(f"Stopped on error: {error}", error=True)
        else:
            self._set_status(f"Idle · last run: {total} {self._counting_label}")

    # ---------------------------------------------------------------- hotkey
    def _apply_hotkey(self, name: str) -> None:
        self._hotkey.hotkey = name
        self._refresh_main_button()
        self._set_status(f"Hotkey set to {display_name(name)}")
        self._changed_now()

    # ---------------------------------------------------------------- Add Key
    def _on_add_key(self) -> None:
        if self._capture is not None:                    # segundo clique = Cancel
            self._cancel_add_key()
            self._set_status("Idle")
            return
        self._hotkey.suspended = True
        self._capture = KeyCapture(lambda name: self._post(self._key_captured, name))
        self._capture.start()
        self._recording.set_add_key_capturing(True)
        self._set_status("Press the key to add…")

    def _cancel_add_key(self) -> None:
        if self._capture is not None:
            self._capture.cancel()
            self._capture = None
        self._hotkey.suspended = False
        self._recording.set_add_key_capturing(False)

    def _key_captured(self, name: str) -> None:
        if self._capture is None:                        # cancelado enquanto a tecla estava a caminho
            return
        self._cancel_add_key()
        if name == self._hotkey.hotkey:
            self._set_status(f"{display_name(name)} is the Start/Stop hotkey — pick another key.", error=True)
            return
        self._recording.add_step(KeyAction(name))
        self._set_status(f"Added key {display_name(name)}")

    # ---------------------------------------------------------------- Pick point
    def _pick_point(self) -> None:
        if self._engine.running:
            self._set_status("Stop the clicker before picking a point.", error=True)
            return
        self._cancel_add_key()
        self._picking = True
        self._recording_was_open = self._recording.visible
        self._recording.withdraw()
        self.withdraw()
        PointPicker(self, self._backend, self._point_picked, self._pick_cancelled).start()

    def _end_pick(self) -> None:
        self._picking = False
        self.deiconify()
        if self._recording_was_open:
            self._recording.deiconify()
            self._recording.lift()

    def _point_picked(self, x: int, y: int) -> None:
        self._end_pick()
        action = ClickAction(x, y, self._options.button, self._options.double)
        self._recording.add_step(action)
        self._set_status(f"Added {action.label()}")

    def _pick_cancelled(self) -> None:
        self._end_pick()
        self._set_status("Pick cancelled")

    # ---------------------------------------------------------------- encerramento
    def _close(self) -> None:
        self._save_now()
        self._engine.stop()
        self._cancel_add_key()
        self._hotkey_window.hide()
        self._hotkey.stop()
        self.destroy()

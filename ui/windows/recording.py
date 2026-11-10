"""Janela Recording: sequência de cliques (pontos) e teclas, reproduzida em ordem."""
from __future__ import annotations

from tkinter import filedialog
from typing import Any, Callable, Dict, List

import customtkinter as ctk

import config
from core import storage
from core.actions import Action, action_from_dict
from .. import theme
from ..widgets import check_box, ghost_button, label
from .base import ToolWindow

_FILETYPES = [("Auto Clicker sequence", f"*{config.SEQUENCE_EXT}")]


class RecordingWindow(ToolWindow):
    def __init__(self, master, on_pick: Callable[[], None], on_add_key: Callable[[], None],
                 on_change: Callable[[], None], on_message: Callable[[str, bool], None]) -> None:
        super().__init__(master, "Recording", config.RECORDING_WIDTH)

        self._steps: List[Action] = []
        self._on_change = on_change
        self._on_message = on_message
        self._enabled = ctk.BooleanVar(value=False)

        check_box(self.body, "Record and replay multiple clicks", self._enabled,
                  command=self._toggled).pack(anchor="w", pady=(0, 10))

        label(self.body, "Click records", muted=True).pack(anchor="w", pady=(0, 4))
        self._list = ctk.CTkScrollableFrame(
            self.body, height=130, fg_color=theme.ELEVATED, corner_radius=6,
            scrollbar_button_color=theme.BORDER, scrollbar_button_hover_color=theme.RED_DARK,
        )
        self._list.pack(fill="x")

        edit = ctk.CTkFrame(self.body, fg_color="transparent")
        edit.pack(fill="x", pady=(10, 0))
        self._pick = ghost_button(edit, "Pick point", on_pick, width=100)
        self._pick.pack(side="left")
        self._add_key = ghost_button(edit, "Add Key", on_add_key, width=90)
        self._add_key.pack(side="left", padx=6)
        self._clear = ghost_button(edit, "Clear", self.clear, width=70)
        self._clear.pack(side="right")

        files = ctk.CTkFrame(self.body, fg_color="transparent")
        files.pack(fill="x", pady=(8, 0))
        ghost_button(files, "Save…", self._save, width=90).pack(side="left")
        ghost_button(files, "Load…", self._load, width=90).pack(side="left", padx=6)

        self._render()
        self._refresh_state()

    # ---------------------------------------------------------------- API
    @property
    def enabled(self) -> bool:
        return self._enabled.get()

    @property
    def steps(self) -> List[Action]:
        return list(self._steps)

    def add_step(self, action: Action) -> None:
        self._steps.append(action)
        self._render()
        self._on_change()

    def clear(self) -> None:
        self._steps.clear()
        self._render()
        self._on_change()

    def set_add_key_capturing(self, capturing: bool) -> None:
        self._add_key.configure(text="Cancel" if capturing else "Add Key")

    def get_state(self) -> Dict[str, Any]:
        return {"enabled": self.enabled, "steps": [step.to_dict() for step in self._steps]}

    def set_state(self, state: Dict[str, Any]) -> None:
        self._enabled.set(state["enabled"])
        self._steps = [action_from_dict(item) for item in state["steps"]]
        self._refresh_state()

    # ---------------------------------------------------------------- Save / Load
    def _save(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self, title="Save sequence", defaultextension=config.SEQUENCE_EXT,
            filetypes=_FILETYPES, initialfile=f"sequence{config.SEQUENCE_EXT}",
        )
        if not path:
            return
        try:
            storage.save_sequence(path, self._steps)
        except storage.SequenceError as exc:
            self._on_message(str(exc), True)
            return
        self._on_message(f"Saved {len(self._steps)} step(s) to {path}", False)

    def _load(self) -> None:
        path = filedialog.askopenfilename(parent=self, title="Load sequence", filetypes=_FILETYPES)
        if not path:
            return
        try:
            steps = storage.load_sequence(path)
        except storage.SequenceError as exc:
            self._on_message(str(exc), True)
            return
        self._steps = steps                 # substitui a lista atual
        self._enabled.set(True)             # carregar uma sequência = querer reproduzi-la
        self._refresh_state()
        self._on_change()
        self._on_message(f"Loaded {len(steps)} step(s) from {path}", False)

    # ---------------------------------------------------------------- interno
    def _toggled(self) -> None:
        self._refresh_state()
        self._on_change()

    def _remove(self, index: int) -> None:
        del self._steps[index]
        self._render()
        self._on_change()

    def _render(self) -> None:
        for child in self._list.winfo_children():
            child.destroy()
        if not self._steps:
            label(self._list, "No steps yet — use Pick point or Add Key.", muted=True).pack(pady=24)
            return
        state = "normal" if self.enabled else "disabled"
        for i, action in enumerate(self._steps):
            row = ctk.CTkFrame(self._list, fg_color="transparent")
            row.pack(fill="x")
            ctk.CTkLabel(row, text=f"{i + 1}.  {action.label()}", anchor="w", font=theme.font(),
                         text_color=theme.TEXT if self.enabled else theme.TEXT_DISABLED
                         ).pack(side="left", fill="x", expand=True, padx=(4, 0))
            ctk.CTkButton(row, text="✕", width=24, height=24, fg_color="transparent",
                          hover_color=theme.RED_DARK, text_color=theme.TEXT_MUTED,
                          text_color_disabled=theme.TEXT_DISABLED, state=state,
                          command=lambda idx=i: self._remove(idx)).pack(side="right")

    def _refresh_state(self) -> None:
        state = "normal" if self.enabled else "disabled"
        for button in (self._pick, self._add_key, self._clear):
            button.configure(state=state)
        self._render()

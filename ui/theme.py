"""Paleta (dark com detalhes vermelhos) e fontes."""

BG = "#1e1e22"            # fundo da janela
SURFACE = "#27272c"       # cartões / seções
ELEVATED = "#31313a"      # campos de entrada, itens de lista
BORDER = "#3d3d46"
TEXT = "#e8e8ec"
TEXT_MUTED = "#9d9da8"
TEXT_DISABLED = "#5d5d68"
TEXT_FAINT = "#74747f"    # detalhes discretos (ex.: versão)

RED = "#c4282d"
RED_HOVER = "#d83c41"
RED_DARK = "#7a1a1e"

FONT_FAMILY = "Segoe UI"
FONT_SIZE = 13
FONT_SMALL = 11


def font(size: int = FONT_SIZE, weight: str = "normal") -> tuple:
    return (FONT_FAMILY, size, weight)

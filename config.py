"""Constantes e valores padrão do aplicativo."""

APP_NAME = "Auto Clicker"
APP_VERSION = "1.0.0"                 # única fonte da versão (build, nome do .exe e tag do git)
APP_ID = "xgabr.autoclicker"          # AppUserModelID (agrupamento na barra de tarefas)

# Larguras das janelas (a altura de todas segue o conteúdo)
WINDOW_WIDTH = 300
OPTIONS_WIDTH = 380
REPEAT_WIDTH = 420
RECORDING_WIDTH = 480
HOTKEY_WIDTH = 320

DEFAULT_HOTKEY = "f8"

# Persistência
STATE_FILE = "auto-clicker-state.json"      # gravado junto ao programa (ver core/storage.py)
STATE_VERSION = 1
SEQUENCE_FORMAT = "auto-clicker-sequence"   # marcador dentro dos arquivos salvos pelo usuário
SEQUENCE_EXT = ".acseq"
SEQUENCE_VERSION = 1
SAVE_DEBOUNCE_MS = 300                      # espera ao digitar em campos antes de gravar

MOUSE_BUTTONS = ("Left", "Right", "Middle")
CLICK_TYPES = ("Single", "Double")

DEFAULT_MOUSE_BUTTON = "Left"
DEFAULT_CLICK_TYPE = "Single"
DEFAULT_REPEAT_COUNT = 1

# Piso do intervalo (segundos): evita laço apertado que trava CPU e janela.
MIN_INTERVAL = 0.001
# Fatia da espera (segundos): permite parar rápido e reposicionar o ponteiro (freeze).
WAIT_SLICE = 0.01

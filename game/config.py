from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SAVES_DIR = ROOT / "saves"
DEFAULT_WORLD = DATA_DIR / "cenithael_default.json"
CUSTOM_WORLD = DATA_DIR / "cenithael_custom.json"
SAVE_FILE = SAVES_DIR / "partida.json"

MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
MODEL_SAFE = "meta-llama/Llama-Guard-4-12B"

INVENTARIO_BASE = {
    "uniforme de trinchera": 1,
    "cuchillo de campaña": 1,
    "ración de hierro": 2,
    "monedas de sacramento": 5,
}

ATRIBUTOS_BASE = {
    "fuerza": 10,
    "destreza": 12,
    "constitucion": 11,
    "inteligencia": 13,
    "sabiduria": 14,
    "carisma": 10,
}

ARQUETIPOS = [
    "Cruzado de Trinchera",
    "Médico de Campaña",
    "Explorador de Reliquias",
    "Hereje Penitente",
    "Artillero del Hierro Santo",
]

MAX_HISTORIAL = 40

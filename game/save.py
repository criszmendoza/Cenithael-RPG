import json
from datetime import datetime, timezone
from pathlib import Path

from game.config import MAX_HISTORIAL, SAVE_FILE, SAVES_DIR
from game.engine import normalizar_historial


def existe_partida() -> bool:
    return SAVE_FILE.exists()


def guardar_partida(estado: dict, historial: list, modo_inicio: str, mundo_archivo: str) -> None:
    SAVES_DIR.mkdir(parents=True, exist_ok=True)
    hist = normalizar_historial(historial)[-MAX_HISTORIAL:]
    data = {
        "version": 1,
        "guardado_en": datetime.now(timezone.utc).isoformat(),
        "modo_inicio": modo_inicio,
        "mundo_archivo": mundo_archivo,
        "estado": estado,
        "historial": hist,
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cargar_partida() -> dict | None:
    if not existe_partida():
        return None
    with open(SAVE_FILE, encoding="utf-8") as f:
        return json.load(f)


def borrar_partida() -> None:
    if SAVE_FILE.exists():
        SAVE_FILE.unlink()

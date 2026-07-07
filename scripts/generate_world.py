#!/usr/bin/env python3
"""Genera un mundo Cenithael nuevo vía API y lo guarda en data/cenithael_custom.json."""

from game.config import CUSTOM_WORLD
from game.world_gen import generar_mundo_completo

if __name__ == "__main__":
    print("Generando mundo Cenithael (varias llamadas API, ~2 min)...")
    mundo = generar_mundo_completo(str(CUSTOM_WORLD))
    print(f"Listo: {CUSTOM_WORLD}")
    print(f"Mundo: {mundo['nombre']} — {len(mundo['reinos'])} facciones")

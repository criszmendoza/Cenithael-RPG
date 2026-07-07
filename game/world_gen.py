import random

from game.config import CUSTOM_WORLD, DEFAULT_WORLD
from game.llm import ask_json
from game.world import guardar_mundo

WORLD_SYSTEM = """
Creas mundos grimdark de guerra perpetua inspirados en cruzadas industriales y trincheras.
Responde SIEMPRE con JSON válido en español. Descripciones de 3-5 frases, tono oscuro y épico.
No copies IP de Warhammer ni Trench Crusade; inspírate en el tono solamente.
"""

PROMPT_MUNDO = """
Genera el mundo de fantasía oscura Cenithael: fortalezas sobre titanos caídos, frentes de trinchera,
fe y pólvora, herejía y reliquias. Responde: {"nombre": "...", "descripcion": "...", "gancho": "..."}
"""

PROMPT_REINOS = """
Crea 3 facciones en guerra para el mundo {mundo_nombre}: {mundo_desc}
Facciones sugeridas: Orden del Hierro Santo, Legión de Ceniza, Culto de la Grieta.
Responde: {{"reinos": [{{"nombre": "...", "descripcion": "..."}}, ...]}}
"""

PROMPT_PUEBLOS = """
Crea 3 frentes de trinchera para la facción {reino_nombre}: {reino_desc}
Mundo: {mundo_nombre}
Responde: {{"pueblos": [{{"nombre": "...", "descripcion": "...", "gancho": "..."}}, ...]}}
"""

PROMPT_PERSONAJES = """
Crea 3 héroes jugables para el frente {pueblo_nombre}: {pueblo_desc}
Facción: {reino_nombre}. Mundo: {mundo_nombre}
Cada héroe debe tener nombre único, descripción con dolor y deseo, y gancho personal.
Responde: {{"personajes": [{{"nombre": "...", "descripcion": "...", "gancho": "..."}}, ...]}}
"""


def _msg(prompt: str) -> list:
    return [
        {"role": "system", "content": WORLD_SYSTEM},
        {"role": "user", "content": prompt},
    ]


def generar_mundo_completo(destino: str | None = None) -> dict:
    mundo_data = ask_json(_msg(PROMPT_MUNDO), temperature=0.8)
    mundo = {
        "nombre": mundo_data.get("nombre", "Cenithael"),
        "descripcion": mundo_data["descripcion"],
        "gancho": mundo_data.get("gancho", ""),
        "reinos": {},
    }

    reinos_data = ask_json(
        _msg(PROMPT_REINOS.format(
            mundo_nombre=mundo["nombre"],
            mundo_desc=mundo["descripcion"],
        )),
        temperature=0.8,
    )

    for reino_raw in reinos_data.get("reinos", [])[:3]:
        reino_key = reino_raw["nombre"]
        if not reino_key.startswith("Orden") and not reino_key.startswith("Legión") and not reino_key.startswith("Culto"):
            reino_key = f"Facción de {reino_raw['nombre']}"
        mundo["reinos"][reino_key] = {
            "nombre": reino_raw["nombre"],
            "descripcion": reino_raw["descripcion"],
            "mundo": mundo["nombre"],
            "pueblos": {},
        }

        pueblos_data = ask_json(
            _msg(PROMPT_PUEBLOS.format(
                reino_nombre=reino_raw["nombre"],
                reino_desc=reino_raw["descripcion"],
                mundo_nombre=mundo["nombre"],
            )),
            temperature=0.8,
        )

        for pueblo_raw in pueblos_data.get("pueblos", [])[:3]:
            pueblo_key = pueblo_raw["nombre"]
            mundo["reinos"][reino_key]["pueblos"][pueblo_key] = {
                "nombre": pueblo_key,
                "descripcion": pueblo_raw["descripcion"],
                "gancho": pueblo_raw.get("gancho", ""),
                "mundo": mundo["nombre"],
                "reino": reino_raw["nombre"],
                "personajes": {},
            }

            chars_data = ask_json(
                _msg(PROMPT_PERSONAJES.format(
                    pueblo_nombre=pueblo_key,
                    pueblo_desc=pueblo_raw["descripcion"],
                    reino_nombre=reino_raw["nombre"],
                    mundo_nombre=mundo["nombre"],
                )),
                temperature=0.8,
            )

            for char in chars_data.get("personajes", [])[:3]:
                nombre = char["nombre"]
                mundo["reinos"][reino_key]["pueblos"][pueblo_key]["personajes"][nombre] = {
                    "nombre": nombre,
                    "descripcion": char["descripcion"],
                    "gancho": char.get("gancho", ""),
                    "mundo": mundo["nombre"],
                    "reino": reino_raw["nombre"],
                    "pueblo": pueblo_key,
                }

    path = destino or str(CUSTOM_WORLD)
    guardar_mundo(mundo, path)
    return mundo

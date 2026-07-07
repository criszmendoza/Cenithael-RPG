import random

from game.config import INVENTARIO_BASE
from game.llm import ask_json
from game.world import cargar_mundo, crear_estado_base

FORGE_SYSTEM = """
Creas fichas de personajes para un RPG grimdark de trincheras y cruzadas en Cenithael.
Responde SOLO JSON en español con esta estructura:
{
  "descripcion": "3-4 frases en segunda persona",
  "atributos": {"fuerza": 10, "destreza": 12, "constitucion": 11, "inteligencia": 13, "sabiduria": 14, "carisma": 10},
  "inventario": {"objeto": cantidad},
  "gancho_apertura": "2-3 frases con conflicto inmediato en el frente"
}
Atributos entre 8 y 16. Inventario temático de guerra (3-5 objetos). gancho_apertura debe tener acción urgente.
"""

OPENING_SYSTEM = """
Eres narrador de un RPG grimdark. Genera una escena de apertura con conflicto inmediato.
Responde SOLO JSON: {"gancho": "2-4 frases en segunda persona, tiempo presente, con incidente de guerra"}
"""


def forjar_personaje(
    nombre: str,
    arquetipo: str,
    motivacion: str,
    cicatriz: str,
    mundo_archivo: str,
) -> dict:
    prompt = f"""
Nombre: {nombre}
Arquetipo: {arquetipo}
Motivación: {motivacion}
Cicatriz / trauma: {cicatriz}
Universo: Cenithael — trincheras, fe, hierro y herejía.
"""
    data = ask_json(
        [{"role": "system", "content": FORGE_SYSTEM}, {"role": "user", "content": prompt}],
        temperature=0.8,
    )
    mundo = cargar_mundo(mundo_archivo)
    reino = random.choice(list(mundo["reinos"].keys()))
    pueblo = random.choice(list(mundo["reinos"][reino]["pueblos"].keys()))

    return crear_estado_base(
        mundo_archivo,
        reino,
        pueblo,
        nombre,
        data["descripcion"],
        inventario=data.get("inventario", INVENTARIO_BASE),
        atributos=data.get("atributos"),
        gancho=data.get("gancho_apertura", ""),
    )


def generar_apertura_heroe(estado: dict) -> str:
    prompt = f"""
Personaje: {estado['nombre_personaje']}
Descripción: {estado['personaje']}
Frente: {estado['nombre_pueblo']} — {estado['pueblo']}
Facción: {estado['nombre_reino']}
Mundo: {estado.get('mundo_nombre', 'Cenithael')}
Genera un incidente de apertura con alarma, combate cercano o misión urgente.
"""
    data = ask_json(
        [{"role": "system", "content": OPENING_SYSTEM}, {"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return data.get("gancho", estado.get("inicio", "El frente arde. Debes actuar ya."))

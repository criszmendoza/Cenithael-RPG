import json
import random
from pathlib import Path

from game.config import ATRIBUTOS_BASE, DEFAULT_WORLD, INVENTARIO_BASE, ROOT


from game.engine import modificador_atributo


def cargar_mundo(archivo: Path | str | None = None) -> dict:
    path = Path(archivo) if archivo else DEFAULT_WORLD
    if not path.is_absolute():
        path = ROOT / path
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def guardar_mundo(mundo: dict, archivo: Path | str) -> None:
    path = Path(archivo)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mundo, f, ensure_ascii=False, indent=2)


def listar_personajes(archivo: Path | str | None = None) -> list[dict]:
    mundo = cargar_mundo(archivo)
    personajes: dict[str, str] = {}
    for reino_data in mundo["reinos"].values():
        for pueblo_data in reino_data["pueblos"].values():
            for nombre, datos in pueblo_data["personajes"].items():
                if nombre not in personajes:
                    personajes[nombre] = datos["descripcion"]
    return [{"nombre": n, "descripcion": d} for n, d in sorted(personajes.items())]


def ubicaciones_personaje(nombre: str, archivo: Path | str | None = None) -> list[tuple[str, str]]:
    mundo = cargar_mundo(archivo)
    ubicaciones = []
    for reino_key, reino_data in mundo["reinos"].items():
        for pueblo_key, pueblo_data in reino_data["pueblos"].items():
            if nombre in pueblo_data["personajes"]:
                ubicaciones.append((reino_key, pueblo_key))
    return ubicaciones


def elegir_pueblo_aleatorio(nombre: str, archivo: Path | str | None = None) -> tuple[str, str]:
    ubicaciones = ubicaciones_personaje(nombre, archivo)
    if not ubicaciones:
        raise ValueError(f"Personaje '{nombre}' no encontrado.")
    return random.choice(ubicaciones)


def modificador_atributo(valor: int) -> int:
    return (valor - 10) // 2


def pv_maximo(constitucion: int) -> int:
    return max(8, 10 + modificador_atributo(constitucion))


def crear_estado_base(
    archivo: Path | str,
    reino: str,
    pueblo: str,
    personaje_nombre: str,
    personaje_desc: str,
    inventario: dict | None = None,
    atributos: dict | None = None,
    gancho: str = "",
) -> dict:
    mundo = cargar_mundo(archivo)
    reino_data = mundo["reinos"][reino]
    pueblo_data = reino_data["pueblos"][pueblo]
    attrs = dict(atributos or ATRIBUTOS_BASE)
    pv_max = pv_maximo(attrs["constitucion"])
    return {
        "mundo": mundo["descripcion"],
        "mundo_nombre": mundo["nombre"],
        "reino": reino_data["descripcion"],
        "pueblo": pueblo_data["descripcion"],
        "personaje": personaje_desc,
        "inicio": gancho or pueblo_data.get("gancho", mundo.get("gancho", "")),
        "nombre_personaje": personaje_nombre,
        "nombre_pueblo": pueblo,
        "nombre_reino": reino,
        "atributos": attrs,
        "inventario": dict(inventario if inventario is not None else INVENTARIO_BASE),
        "pv": pv_max,
        "pv_max": pv_max,
        "mision_activa": "Sobrevive al frente y cumple tu juramento.",
        "puede_comerciar": False,
        "opciones": [],
        "turno": 0,
        "en_combate": False,
        "enemigo": None,
    }


def crear_partida_heroe(personaje: str, archivo: Path | str | None = None) -> dict:
    path = archivo or DEFAULT_WORLD
    reino, pueblo = elegir_pueblo_aleatorio(personaje, path)
    mundo = cargar_mundo(path)
    desc = mundo["reinos"][reino]["pueblos"][pueblo]["personajes"][personaje]["descripcion"]
    estado = crear_estado_base(path, reino, pueblo, personaje, desc)
    pueblo_data = cargar_mundo(path)["reinos"][reino]["pueblos"][pueblo]
    personaje_data = pueblo_data["personajes"][personaje]
    gancho = personaje_data.get("gancho") or pueblo_data.get("gancho") or ""
    estado["inicio"] = gancho
    return estado

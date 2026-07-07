import json
import random

from game.engine import (
    aplicar_dano,
    es_transaccion,
    expand_opcion,
    format_tirada,
    modificador_atributo,
    modificador_habilidad,
    normalizar_historial,
    roll_dice,
    tirada_ataque,
)
from game.inventory import detect_inventory_changes, update_inventory
from game.llm import ask_json

EVENTOS = [
    "Una patrulla enemiga aparece en la niebla.",
    "Un mercader de reliquias ofrece suministros en la trinchera.",
    "Una emboscada desde las trincheras enemigas.",
    "Un mensajero herido trae órdenes urgentes del mando.",
    "Artillería enemiga impacta cerca; debes reaccionar.",
]

DND_GM_SYSTEM = """
Eres Maestro de Juego de Calabozos y Dragones en el universo grimdark Cenithael (trincheras, cruzadas, hierro y ceniza).
Responde SIEMPRE con JSON válido (sin markdown):
{
  "narrativa": "2-4 frases urgentes en segunda persona, tiempo presente",
  "requiere_prueba": false,
  "cd": 12,
  "habilidad": "destreza",
  "contexto_prueba": "",
  "opciones": ["[Combate] ...", "[Sigilo — dificultad 14] ...", "[Fe — dificultad 12] ...", "..."],
  "comercio_disponible": false,
  "transaccion_completada": false,
  "inicia_combate": false,
  "enemigo_nombre": "",
  "enemigo_pv": 0,
  "nueva_mision": ""
}

Reglas:
- Tono grimdark: acción constante, consecuencias reales, poca paz.
- SIEMPRE 3-4 opciones; al menos una agresiva [Combate] y una cautelosa.
- Etiqueta riesgo en opciones: [Combate], [Sigilo — dificultad X], [Fe — dificultad X], [Fuerza — dificultad X]. No uses abreviaturas como CD o d20.
- requiere_prueba=true para acciones arriesgadas. Dificultad: 8=fácil, 12=normal, 15=difícil, 18=muy difícil.
- inicia_combate=true cuando aparece un enemigo claro; enemigo_pv entre 8 y 20.
- comercio_disponible=true solo con mercaderes o puestos de suministro.
- transaccion_completada=true solo si el jugador cerró compra/venta.
- nueva_mision: solo si cambia la misión activa (cada 4-6 turnos aprox).
- No listes inventario en narrativa. No completes transacciones sin orden explícita del jugador.
"""


def _contexto_mundo(estado: dict) -> str:
    attrs = ", ".join(
        f"{k} {v} ({modificador_atributo(v):+d})" for k, v in estado["atributos"].items()
    )
    enemigo = ""
    if estado.get("en_combate") and estado.get("enemigo"):
        e = estado["enemigo"]
        enemigo = f"\nEn combate contra: {e['nombre']} (PV {e['pv']})"
    return f"""Mundo: {estado['mundo']}
Facción: {estado['reino']}
Frente: {estado['pueblo']}
Personaje: {estado['personaje']}
PV: {estado['pv']}/{estado['pv_max']}
Misión activa: {estado.get('mision_activa', '—')}
Turno: {estado.get('turno', 0)}
Atributos: {attrs}
Inventario: {json.dumps(estado['inventario'], ensure_ascii=False)}
Comercio disponible: {'sí' if estado.get('puede_comerciar') else 'no'}{enemigo}"""


def _mensajes_gm(estado: dict, historial: list, instruccion: str) -> list:
    mensajes = [
        {"role": "system", "content": DND_GM_SYSTEM},
        {"role": "user", "content": _contexto_mundo(estado)},
    ]
    for msg in normalizar_historial(historial):
        mensajes.append(msg)
    mensajes.append({"role": "user", "content": instruccion})
    return mensajes


def format_opciones(opciones: list) -> str:
    if not opciones:
        return ""
    lineas = ["\n**¿Qué haces?**"]
    for i, op in enumerate(opciones, 1):
        lineas.append(f"{i}. {op}")
    lineas.append("\n_Escribe el número o describe tu acción. Las pruebas usan un dado de 20 caras; cuanto mayor el número, mejor._")
    return "\n".join(lineas)


def format_turno(data: dict, extras: list | None = None) -> str:
    partes = list(extras or [])
    if data.get("narrativa"):
        partes.append(data["narrativa"])
    texto = "\n\n".join(partes)
    texto += format_opciones(data.get("opciones", []))
    return texto


def _resolver_prueba(accion: str, historial: list, estado: dict, plan: dict, roll: dict) -> dict:
    exito = roll["total"] >= plan.get("cd", 12)
    if roll["natural"] == 20:
        exito = True
    elif roll["natural"] == 1:
        exito = False
    instruccion = f"""Acción: {accion}
Contexto: {plan.get('contexto_prueba', '')}
Tirada: d20={roll['natural']}, mod={roll['modifier']}, total={roll['total']}, CD={plan.get('cd', 12)}
Resultado: {'éxito' if exito else 'fallo'}
Narra consecuencias dramáticas. requiere_prueba=false. 3-4 opciones etiquetadas."""
    return ask_json(_mensajes_gm(estado, historial, instruccion))


def _aplicar_post_turno(estado: dict, data: dict, accion: str) -> str:
    extra = ""
    if data.get("nueva_mision"):
        estado["mision_activa"] = data["nueva_mision"]
        extra += f"\n\n📜 **Nueva misión:** {data['nueva_mision']}"

    if data.get("inicia_combate") and not estado.get("en_combate"):
        nombre = data.get("enemigo_nombre") or "Soldado enemigo"
        pv = data.get("enemigo_pv") or random.randint(8, 16)
        estado["en_combate"] = True
        estado["enemigo"] = {"nombre": nombre, "pv": pv, "pv_max": pv}
        extra += f"\n\n⚔️ **¡Combate!** {nombre} (PV {pv})"

    if estado.get("en_combate") and ("[combate]" in accion.lower() or "atac" in accion.lower()):
        roll, exito, dano = tirada_ataque(estado)
        extra += "\n" + format_tirada(roll, 12, "fuerza")
        if exito and estado.get("enemigo"):
            estado["enemigo"]["pv"] -= dano
            extra += f"\n💥 Infliges {dano} de daño a {estado['enemigo']['nombre']}."
            if estado["enemigo"]["pv"] <= 0:
                estado["en_combate"] = False
                estado["enemigo"] = None
                extra += "\n✅ Enemigo derrotado."
        elif not exito:
            contra = random.randint(1, 4)
            extra += aplicar_dano(estado, contra)

    if data.get("transaccion_completada") or (estado["puede_comerciar"] and es_transaccion(accion)):
        extra += update_inventory(
            estado["inventario"],
            detect_inventory_changes(estado, accion, data.get("narrativa", "")),
        )

    if estado["puede_comerciar"] and not data.get("transaccion_completada"):
        extra += "\n\n🏪 Puedes comprar o vender. Di qué intercambias."

    return extra


def run_turn(mensaje: str, historial: list, estado: dict) -> str:
    accion = expand_opcion(mensaje, estado.get("opciones", []))
    estado["turno"] = estado.get("turno", 0) + 1

    if estado["pv"] <= 0:
        return "💀 Has caído. Pulsa **Comenzar de 0** para reiniciar."

    extras_evento = []
    if estado["turno"] > 1 and estado["turno"] % 3 == 0:
        extras_evento.append(f"⚡ **Evento:** {random.choice(EVENTOS)}")

    if accion.strip().lower() == "iniciar juego":
        gancho = estado.get("inicio", "El frente estalla en combate.")
        instruccion = f"""El jugador inicia. Escena base:
{gancho}
Amplía con incidente urgente (alarma, asalto, gas, reliquia). requiere_prueba=false.
Ofrece 3-4 opciones etiquetadas con riesgo."""
        data = ask_json(_mensajes_gm(estado, [], instruccion))
    else:
        instruccion = f"Acción del jugador: {accion}"
        if estado["turno"] % 5 == 0:
            instruccion += f"\nActualiza o refuerza la misión activa: {estado.get('mision_activa', '')}"
        data = ask_json(_mensajes_gm(estado, historial, instruccion))

        if data.get("requiere_prueba"):
            habilidad = data.get("habilidad", "destreza")
            mod = modificador_habilidad(estado["atributos"], habilidad)
            cd = data.get("cd", 12)
            roll = roll_dice(20, mod)
            tirada = format_tirada(roll, cd, habilidad)
            data = _resolver_prueba(accion, historial, estado, data, roll)
            extras_evento.insert(0, tirada)
            if data.get("contexto_prueba"):
                extras_evento.insert(0, data["contexto_prueba"])

    estado["puede_comerciar"] = data.get("comercio_disponible", False)
    estado["opciones"] = data.get("opciones", [])
    texto = format_turno(data, extras_evento)
    texto += _aplicar_post_turno(estado, data, accion)
    return texto

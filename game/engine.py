import random


def modificador_atributo(valor: int) -> int:
    return (valor - 10) // 2


def roll_dice(sides: int = 20, modifier: int = 0) -> dict:
    natural = random.randint(1, sides)
    return {"natural": natural, "modifier": modifier, "total": natural + modifier}


def modificador_habilidad(atributos: dict, habilidad: str) -> int:
    return modificador_atributo(atributos.get(habilidad.lower(), 10))


def format_tirada(roll: dict, cd: int, habilidad: str) -> str:
    hab = habilidad.lower()
    mod = roll["modifier"]
    natural = roll["natural"]
    total = roll["total"]

    if natural == 20:
        resultado = "ÉXITO CRÍTICO"
        dado = "¡**20** en el dado (¡crítico!)"
    elif natural == 1:
        resultado = "FALLO CRÍTICO"
        dado = "¡**1** en el dado (¡fallo crítico!)"
    elif total >= cd:
        resultado = "ÉXITO"
        dado = f"**{natural}** en el dado"
    else:
        resultado = "FALLO"
        dado = f"**{natural}** en el dado"

    if mod > 0:
        calculo = f"{dado} + **{mod}** por tu {hab} = **{total}**"
    elif mod < 0:
        calculo = f"{dado} − **{abs(mod)}** por tu {hab} = **{total}**"
    else:
        calculo = f"{dado} (sin bonificación de {hab}) = **{total}**"

    return (
        f"🎲 **Prueba de {hab}:** Tiras un dado de 20 caras y sacas {calculo}. "
        f"Para tener éxito necesitabas **{cd}** o más → **{resultado}**"
    )


def expand_opcion(mensaje: str, opciones: list) -> str:
    texto = mensaje.strip()
    if texto.isdigit():
        idx = int(texto) - 1
        if 0 <= idx < len(opciones):
            return opciones[idx]
    return mensaje


def es_transaccion(mensaje: str) -> bool:
    claves = ("compro", "comprar", "vendo", "vender", "intercambio", "trueque", "pago", "cuesto")
    return any(c in mensaje.lower() for c in claves)


def aplicar_dano(estado: dict, dano: int) -> str:
    estado["pv"] = max(0, estado["pv"] - dano)
    if estado["pv"] == 0:
        return f"\n\n💀 **Has caído en combate.** Escribe *iniciar juego* para un nuevo intento en el frente."
    return f"\n\n❤️ PV: {estado['pv']}/{estado['pv_max']}"


def tirada_ataque(estado: dict, cd: int = 12) -> tuple[dict, bool, int]:
    mod = modificador_habilidad(estado["atributos"], "fuerza")
    roll = roll_dice(20, mod)
    exito = roll["total"] >= cd
    if roll["natural"] == 20:
        exito = True
    elif roll["natural"] == 1:
        exito = False
    dano = 0
    if exito:
        dano_roll = roll_dice(6, modificador_habilidad(estado["atributos"], "fuerza"))
        dano = max(1, dano_roll["total"])
    return roll, exito, dano


def normalizar_historial(historial: list) -> list:
    mensajes = []
    for msg in historial or []:
        if isinstance(msg, dict):
            mensajes.append({"role": msg["role"], "content": msg["content"]})
        elif isinstance(msg, (list, tuple)) and len(msg) == 2:
            if msg[0]:
                mensajes.append({"role": "user", "content": msg[0]})
            if msg[1]:
                mensajes.append({"role": "assistant", "content": msg[1]})
    return mensajes


def format_panel(estado: dict) -> str:
    inv = ", ".join(f"{k} x{v}" if v > 1 else k for k, v in estado["inventario"].items())
    attrs = " | ".join(f"{k[:3].upper()} {v}" for k, v in estado["atributos"].items())
    enemigo = ""
    if estado.get("en_combate") and estado.get("enemigo"):
        enemigo = f"\n**Enemigo:** {estado['enemigo']['nombre']} (PV {estado['enemigo']['pv']})"
    return (
        f"**{estado['nombre_personaje']}** — {estado['nombre_pueblo']}\n"
        f"❤️ {estado['pv']}/{estado['pv_max']} | Turno {estado.get('turno', 0)}"
        f"{enemigo}\n"
        f"**Misión:** {estado.get('mision_activa', '—')}\n"
        f"**Atributos:** {attrs}\n"
        f"**Inventario:** {inv}"
    )

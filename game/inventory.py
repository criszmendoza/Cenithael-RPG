import json

from game.llm import ask_json

INVENTORY_SYSTEM = """
Detecta cambios REALES y COMPLETADOS en el inventario de un soldado en guerra.
Un cambio SOLO ocurre con acción ya realizada: comprar, vender, entregar, recibir, tirar, recoger, usar.
NO hay cambio si solo se mencionan objetos o hay intención sin trato cerrado.
Responde SOLO JSON: {"itemUpdates": [{"name": "...", "change_amount": N}]}
Usa los mismos nombres del inventario actual. Si no hay cambios: {"itemUpdates": []}
"""


def detect_inventory_changes(estado: dict, accion: str, narrativa: str) -> list:
    messages = [
        {"role": "system", "content": INVENTORY_SYSTEM},
        {"role": "user", "content": f"Inventario: {json.dumps(estado['inventario'], ensure_ascii=False)}"},
        {"role": "user", "content": f"Acción: {accion}"},
        {"role": "user", "content": f"Historia: {narrativa}"},
    ]
    result = ask_json(messages, temperature=0.0)
    return result.get("itemUpdates", [])


def update_inventory(inventario: dict, item_updates: list) -> str:
    update_msg = ""
    for update in item_updates:
        if "name" not in update or "change_amount" not in update:
            continue
        name = update["name"]
        change = update["change_amount"]
        if change > 0:
            inventario[name] = inventario.get(name, 0) + change
            update_msg += f"\nInventario: {name} +{change}"
        elif name in inventario and change < 0:
            inventario[name] += change
            update_msg += f"\nInventario: {name} {change}"
        if name in inventario and inventario[name] <= 0:
            del inventario[name]
    return update_msg

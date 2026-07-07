"""Interfaz Gradio para Cenithael RPG."""

from __future__ import annotations

import gradio as gr

from game.character import forjar_personaje, generar_apertura_heroe
from game.config import ARQUETIPOS, CUSTOM_WORLD, DEFAULT_WORLD, ROOT
from game.engine import format_panel, normalizar_historial
from game.gm import run_turn
from game.save import borrar_partida, cargar_partida, existe_partida, guardar_partida
from game.safety import is_safe
from game.world import crear_partida_heroe, listar_personajes
from game.world_gen import generar_mundo_completo


class Session:
    def __init__(self):
        self.estado: dict | None = None
        self.modo: str = ""
        self.mundo_archivo: str = str(DEFAULT_WORLD.relative_to(ROOT))
        self.historial: list = []

    def reset(self):
        self.estado = None
        self.modo = ""
        self.historial = []


def _hist_to_gradio(historial: list) -> list:
    return normalizar_historial(historial)


def _gradio_to_hist(chat: list) -> list:
    if not chat:
        return []
    if isinstance(chat[0], dict):
        return [{"role": m["role"], "content": m["content"]} for m in chat if m.get("content")]
    return normalizar_historial(chat)


def _append_turn(chat: list, usuario: str, asistente: str) -> list:
    return list(chat or []) + [
        {"role": "user", "content": usuario},
        {"role": "assistant", "content": asistente},
    ]


def _es_accion_rapida(mensaje: str) -> bool:
    t = mensaje.strip().lower()
    return t.isdigit() or t in ("iniciar juego", "iniciar", "start")


def launch(share: bool = False):
    session = Session()
    personajes = listar_personajes()
    nombres = [p["nombre"] for p in personajes]

    def descripcion_personaje(nombre: str | None) -> str:
        if not nombre:
            return ""
        archivo = ROOT / session.mundo_archivo
        for p in listar_personajes(archivo):
            if p["nombre"] == nombre:
                return p["descripcion"]
        return ""

    def panel_md():
        if session.estado is None:
            return "Selecciona o crea un personaje para comenzar."
        return format_panel(session.estado)

    def show_chat():
        return gr.update(visible=True), gr.update(visible=True)

    def hide_chat():
        return gr.update(visible=False), gr.update(visible=False)

    def _selector_mundo():
        archivo = ROOT / session.mundo_archivo
        heroes = listar_personajes(archivo)
        nombres_mundo = [p["nombre"] for p in heroes]
        primero = nombres_mundo[0] if nombres_mundo else None
        return (
            gr.update(choices=nombres_mundo, value=primero),
            descripcion_personaje(primero),
        )

    def on_chat(mensaje: str, chat: list):
        if not mensaje.strip():
            yield chat, panel_md(), mensaje
            return

        usuario = mensaje.strip()
        chat_base = list(chat or [])
        # Mostrar mensaje del jugador y vaciar caja al instante
        yield chat_base + [{"role": "user", "content": usuario}], panel_md(), ""

        if session.estado is None:
            yield _append_turn(chat_base, usuario, "Elige modo de partida y pulsa **Comenzar aventura**."), panel_md(), ""
            return

        if not _es_accion_rapida(usuario) and not is_safe(usuario):
            yield _append_turn(chat_base, usuario, "Acción no válida."), panel_md(), ""
            return

        hist = _gradio_to_hist(chat_base)
        try:
            salida = run_turn(usuario, hist, session.estado)
        except Exception as e:
            yield _append_turn(chat_base, usuario, f"Error del motor: {e}"), panel_md(), ""
            return

        session.historial = hist + [
            {"role": "user", "content": usuario},
            {"role": "assistant", "content": salida},
        ]
        guardar_partida(session.estado, session.historial, session.modo, session.mundo_archivo)
        yield _append_turn(chat_base, usuario, salida), panel_md(), ""

    def start_hero(nombre: str):
        if not nombre:
            return "Selecciona un personaje.", *hide_chat(), [], panel_md()
        try:
            estado = crear_partida_heroe(nombre, ROOT / session.mundo_archivo)
        except (ValueError, KeyError, FileNotFoundError) as e:
            return (
                f"No se pudo iniciar con **{nombre}**: {e}\n\n"
                "Si generaste una campaña nueva, elige un héroe de esa lista. "
                "Si volviste al mundo base, pulsa **Comenzar de 0**.",
                *hide_chat(),
                [],
                panel_md(),
            )
        session.reset()
        session.modo = "heroe"
        session.estado = estado
        try:
            estado["inicio"] = generar_apertura_heroe(estado)
        except Exception:
            pass
        session.estado = estado
        resumen = (
            f"### {nombre}\n"
            f"**Frente (aleatorio):** {estado['nombre_pueblo']}\n"
            f"**Facción:** {estado['nombre_reino']}\n\n"
            f"{estado['personaje']}\n\n"
            "Escribe **iniciar juego** en el chat."
        )
        return resumen, *show_chat(), [], panel_md()

    def start_forge(nombre, arquetipo, motivacion, cicatriz):
        if not nombre or not arquetipo:
            return "Completa nombre y arquetipo.", *hide_chat(), [], panel_md()
        try:
            estado = forjar_personaje(
                nombre, arquetipo, motivacion or "Sobrevivir", cicatriz or "Una guerra sin fin",
                str(ROOT / session.mundo_archivo),
            )
        except Exception as e:
            return f"Error al forjar: {e}", *hide_chat(), [], panel_md()
        session.reset()
        session.modo = "forjado"
        session.estado = estado
        resumen = (
            f"### {nombre} — {arquetipo}\n"
            f"**Frente:** {estado['nombre_pueblo']}\n\n"
            f"{estado['personaje']}\n\n"
            "Escribe **iniciar juego** en el chat."
        )
        return resumen, *show_chat(), [], panel_md()

    def start_new_world():
        session.reset()
        session.modo = "nuevo_mundo"
        try:
            generar_mundo_completo(str(CUSTOM_WORLD))
            session.mundo_archivo = str(CUSTOM_WORLD.relative_to(ROOT))
            nuevos = listar_personajes(CUSTOM_WORLD)
            nuevos_nombres = [p["nombre"] for p in nuevos]
            primero = nuevos_nombres[0] if nuevos_nombres else None
            return (
                "✅ Campaña nueva generada. Ve a **Héroe del mundo**, elige personaje y pulsa **Comenzar aventura**.",
                *hide_chat(),
                [],
                panel_md(),
                gr.update(choices=nuevos_nombres, value=primero),
                descripcion_personaje(primero),
            )
        except Exception as e:
            return f"Error generando mundo: {e}", *hide_chat(), [], panel_md(), gr.update(), ""

    def continue_save():
        data = cargar_partida()
        if not data:
            return "No hay partida guardada.", *hide_chat(), [], panel_md()
        session.estado = data["estado"]
        session.modo = data.get("modo_inicio", "heroe")
        session.mundo_archivo = data.get("mundo_archivo", str(DEFAULT_WORLD.relative_to(ROOT)))
        session.historial = data.get("historial", [])
        chat = _hist_to_gradio(session.historial)
        return (
            f"Partida restaurada — **{session.estado['nombre_personaje']}** (turno {session.estado.get('turno', 0)})",
            *show_chat(),
            chat,
            panel_md(),
        )

    def reset_all():
        borrar_partida()
        session.reset()
        session.mundo_archivo = str(DEFAULT_WORLD.relative_to(ROOT))
        sel, desc = _selector_mundo()
        return (
            "Partida borrada. Elige un modo para comenzar de 0.",
            *hide_chat(),
            [],
            panel_md(),
            "",
            sel,
            desc,
        )

    def manual_save(chat):
        if session.estado:
            session.historial = _gradio_to_hist(chat)
            guardar_partida(session.estado, session.historial, session.modo, session.mundo_archivo)
            return "💾 Partida guardada."
        return "No hay partida activa."

    has_save = existe_partida()

    with gr.Blocks(title="Cenithael RPG") as demo:
        gr.Markdown("# Cenithael RPG\nRPG de texto con IA. Elige tu héroe y sobrevive al frente.")

        if has_save:
            gr.Markdown("📂 **Tienes una partida guardada.**")
            with gr.Row():
                btn_continue = gr.Button("Continuar aventura", variant="primary")
                btn_reset_launch = gr.Button("Comenzar de 0", variant="secondary")

        with gr.Tabs():
            with gr.Tab("Héroe del mundo"):
                with gr.Row():
                    selector = gr.Dropdown(
                        choices=nombres, value=nombres[0] if nombres else None, label="Personaje"
                    )
                    desc_box = gr.Textbox(
                        label="Descripción",
                        lines=4,
                        interactive=False,
                        value=descripcion_personaje(nombres[0]) if nombres else "",
                    )
                selector.change(descripcion_personaje, selector, desc_box)
                btn_hero = gr.Button("Comenzar aventura", variant="primary")

            with gr.Tab("Forjar personaje"):
                forge_name = gr.Textbox(label="Nombre", placeholder="Ej: Veyl Ashford")
                forge_arch = gr.Dropdown(choices=ARQUETIPOS, label="Arquetipo", value=ARQUETIPOS[0])
                forge_mot = gr.Textbox(label="Motivación", placeholder="¿Por qué luchas?")
                forge_cic = gr.Textbox(label="Cicatriz / trauma", placeholder="Tu herida del pasado")
                btn_forge = gr.Button("Forjar y comenzar", variant="primary")

            with gr.Tab("Nueva campaña"):
                gr.Markdown("Genera un mundo nuevo vía API (~2 min). Requiere `TOGETHER_API_KEY`.")
                btn_world = gr.Button("Generar campaña nueva", variant="primary")

        resumen = gr.Markdown()
        panel = gr.Markdown(value="Selecciona o crea un personaje para comenzar.")

        with gr.Row():
            btn_save = gr.Button("Guardar partida")
            btn_reset = gr.Button("Comenzar de 0", variant="stop")
            save_msg = gr.Markdown()

        chatbot = gr.Chatbot(height=420, visible=False)
        caja = gr.Textbox(
            placeholder="Escribe 'iniciar juego' o el número de una opción...",
            visible=False,
            label="Tu acción",
        )
        caja.submit(on_chat, [caja, chatbot], [chatbot, panel, caja])

        chat_outs = [resumen, chatbot, caja, chatbot, panel]
        world_outs = [resumen, chatbot, caja, chatbot, panel, selector, desc_box]
        btn_hero.click(start_hero, selector, chat_outs)
        btn_forge.click(start_forge, [forge_name, forge_arch, forge_mot, forge_cic], chat_outs)
        btn_world.click(start_new_world, outputs=world_outs)
        btn_save.click(manual_save, chatbot, save_msg)
        reset_outs = [resumen, chatbot, caja, chatbot, panel, save_msg, selector, desc_box]
        btn_reset.click(reset_all, outputs=reset_outs)

        if has_save:
            btn_continue.click(continue_save, outputs=[resumen, chatbot, caja, chatbot, panel])
            btn_reset_launch.click(reset_all, outputs=reset_outs)

    demo.queue(default_concurrency_limit=1)
    demo.launch(share=share, server_name="0.0.0.0", theme="soft")

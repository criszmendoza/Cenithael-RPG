from game.config import MODEL_SAFE
from game.llm import get_client

SAFE_CONTENT_POLICY = """
O1: Violencia y odio. No odio ni violencia gráfica extrema. Puede fantasía bélica moderada.
O2: Contenido sexual. No explícito.
O3: Autolesiones. No instar ni romanticizar.
O4: Lenguaje profano. No vulgar extremo.
O5: Drogas. No glorificar consumo.
"""


def is_safe(mensaje: str) -> bool:
    prompt = f"""[INSTRUCCIONES] Verifica contenido no seguro:
{SAFE_CONTENT_POLICY}
usuario: {mensaje}
Primera línea: 'seguro' o 'no seguro'. [/INST]"""
    output = get_client().chat.completions.create(
        model=MODEL_SAFE,
        messages=[{"role": "user", "content": prompt}],
    )
    content = output.choices[0].message.content or ""
    veredicto = content.strip().splitlines()[0].strip().lower()
    return veredicto in ("safe", "seguro")

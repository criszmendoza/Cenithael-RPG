"""Genera data/cenithael_default.json sin llamadas a la API."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

mundo = {
    "nombre": "Cenithael",
    "descripcion": (
        "Cenithael es un mundo devastado por cruzadas perpetuas. Las fortalezas se alzan "
        "sobre los huesos de titanos caídos mientras millones luchan en trincheras de barro, "
        "hierro y fe. La Orden del Hierro Santo, la Legión de Ceniza y el Culto de la Grieta "
        "se desangran en un frente que no conoce la paz."
    ),
    "gancho": "Las campanas de alarma repican. Algo se mueve en la niebla del frente.",
    "reinos": {},
}

data = [
    (
        "Orden del Hierro Santo",
        "Cruzada industrial de clérigos-guerreros y artilleros bajo el Arzobispo Martel.",
        [
            ("Trinchera del Juicio", "Frente principal. Barro, alambre y rezos bajo fuego de mortero."),
            ("Bastión del Sacramento", "Fortín de reliquias y hospitales de campaña."),
            ("Línea del Hierro", "Trinchera avanzada donde caen cien soldados al día."),
        ],
        [
            ("Marcus Veyl", "Cruzado con armadura abollada. Juró salvar a su hermana del frente sur."),
            ("Sor Corvina Ash", "Médica de campaña que ve visiones en la niebla."),
            ("Artillero Thane", "Operador de mortero bendito. Cuenta cada disparo como un rezo."),
        ],
    ),
    (
        "Legión de Ceniza",
        "Veteranos que usan gas sagrado y bayonetas bajo la general Veyra.",
        [
            ("Foso de Ascuas", "Línea donde el suelo aún arde por bombardeos."),
            ("Línea de los Mártires", "Trinchera convertida en matadero sin fin."),
            ("Puente de los Condenados", "Paso estratégico sobre un titán en descomposición."),
        ],
        [
            ("Kael Riven", "Explorador con rostro quemado por gas. Busca su batallón perdido."),
            ("Lira Ember", "Sargento de bayoneta. Mata con eficiencia y llora en silencio."),
            ("Dorn el Silencioso", "Francotirador que no habla desde la Caída de Veyl."),
        ],
    ),
    (
        "Culto de la Grieta",
        "Profetas y flagelantes que veneran la herida abierta del mundo.",
        [
            ("Grieta Sangrienta", "Frente donde la tierra sangra y los susurros no cesan."),
            ("Cámara del Eco", "Túneles bajo el titán caído. La locura acecha."),
            ("Altar de la Ceniza", "Santuario profanado convertido en nido de herejes."),
        ],
        [
            ("Eira Grieta", "Penitente que duda de sus profetas. Su mano sangra sin herida."),
            ("Morth the Whisper", "Profeta que cree que la guerra es un sueño."),
            ("Sable Nyx", "Asesina de reliquias. Vende secretos a ambos bandos."),
        ],
    ),
]

for fk, fd, frentes, heroes in data:
    mundo["reinos"][fk] = {"nombre": fk, "descripcion": fd, "mundo": "Cenithael", "pueblos": {}}
    for pi, (pn, pd) in enumerate(frentes):
        pueblo = {
            "nombre": pn,
            "descripcion": pd,
            "gancho": f"En {pn} suenan las alarmas. El enemigo avanza.",
            "mundo": "Cenithael",
            "reino": fk,
            "personajes": {},
        }
        for hi, (hn, hd) in enumerate(heroes):
            pueblo["personajes"][hn] = {
                "nombre": hn,
                "descripcion": hd,
                "gancho": f"{hn} corre hacia el frente mientras el cielo arde.",
                "mundo": "Cenithael",
                "reino": fk,
                "pueblo": pn,
            }
        mundo["reinos"][fk]["pueblos"][pn] = pueblo

path = ROOT / "data" / "cenithael_default.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(mundo, f, ensure_ascii=False, indent=2)
print(f"Generado: {path}")

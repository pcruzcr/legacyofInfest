"""AUD-256 — desbloquear un logro era mudo.

Qué era falso y qué no
======================
La primera lectura de esta auditoría dijo que un logro «no se ve ni se oye».
**La mitad era falsa:** `AchievementSystem._unlock` encola un aviso y
`stage_scene.py` lo dibuja, así que el logro sí se ve.

Lo que sí faltaba: el desbloqueo **no suena**, y `ACHIEVEMENT_UNLOCKED` se
emitía sin un solo suscriptor —el propio código lo llama «reservado»—. Un
logro que aparece en una esquina sin sonido se pierde entre el combate que lo
acaba de provocar, que es justo cuando se desbloquean casi todos.

El alcance, dicho en voz alta
-----------------------------
El sonido se cablea en la tabla de `senales.py`, que es la que ya traduce
treinta y ocho eventos a muestras. Eso significa **dentro de un escenario**:
es la limitación que `docs/52` §6 lleva anotada para todos los SFX y no se
arregla aquí. En la práctica cubre casi todo, porque los diez logros se
desbloquean jugando (matar, combo, checkpoint, salud baja, tiempo).
"""
from __future__ import annotations

from src.engine.core.events import Events


class TestElEventoTieneQuienLoEscuche:
    def test_el_desbloqueo_esta_en_la_tabla_de_sonidos(self) -> None:
        from pathlib import Path

        # AUD-290 movió la tabla de sonidos de `senales.py` a `sonido.py`.
        senales = (Path(__file__).resolve().parents[1]
                   / "src" / "framework" / "scenes" / "stage_parts" / "sonido.py")
        texto = senales.read_text(encoding="utf-8")

        assert "Events.ACHIEVEMENT_UNLOCKED:" in texto, (
            "ACHIEVEMENT_UNLOCKED se emite y nadie lo escucha: el logro se "
            "desbloquea en silencio."
        )

    def test_la_muestra_que_usa_existe_en_disco(self) -> None:
        """Cablear a un fichero que no está es cablear de mentira."""
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1]
        assert (raiz / "assets" / "sfx" / "ui" / "sfx_ui_stage_complete.wav").is_file()


class TestElAvisoSigueApareciendo:
    """La mitad que ya funcionaba no se rompe al añadir la otra."""

    def test_desbloquear_encola_un_aviso(self, event_bus) -> None:
        from src.engine.core.achievements import AchievementSystem

        sistema = AchievementSystem.get_instance()
        sistema.bind_bus(event_bus)
        sistema._progress["first_blood"].unlocked = False
        sistema._notifications.clear()

        sistema._unlock("first_blood")

        assert len(sistema._notifications) == 1
        assert sistema._notifications[0]["id"] == "first_blood"

    def test_desbloquear_emite_el_evento(self, event_bus) -> None:
        recibidos: list[str] = []

        def _anotar(**data: object) -> None:
            recibidos.append(str(data.get("achievement_id", "")))

        event_bus.subscribe(Events.ACHIEVEMENT_UNLOCKED, _anotar)

        from src.engine.core.achievements import AchievementSystem

        sistema = AchievementSystem.get_instance()
        sistema.bind_bus(event_bus)
        sistema._progress["first_blood"].unlocked = False

        sistema._unlock("first_blood")
        event_bus.dispatch()

        assert recibidos == ["first_blood"]

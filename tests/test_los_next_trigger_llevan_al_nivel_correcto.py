"""AUD-552 — auditoría pedida: "que todos los stage esté con el NextTrigger
hacia el nivel que corresponde".

Lo que hay que entender primero, porque cambia qué se prueba
==============================================================
`NextTrigger` no lleva ningún dato de destino. Es sólo un rectángulo: quien lo
toca dispara `ProgressionSystem.check_next_trigger` (`progression_system.py`),
que marca `stage_complete = True`. El destino real lo decide
`SceneManager._enter_next_stage` (`scene_manager.py`) incrementando
`_stage_index` sobre la cola construida una sola vez a partir de
`STAGE_ORDER` (`stage_registry.py`) al arrancar la partida — no hay ninguna
propiedad "va hacia stage2_1" en el TMX que pudiera estar mal apuntada.

Así que "el NextTrigger que corresponde" no es una pregunta de *a dónde
apunta cada uno* (no apuntan a ningún sitio) sino de dos cosas objetivas y
verificables:

1. **Todo escenario que se completa por trigger lo declara.** Sin él, ese
   nivel es imposible de terminar — la partida se queda ahí para siempre. Los
   escenarios de jefe son la excepción a propósito: se completan por
   `check_boss_defeat`, no por trigger.
2. **`STAGE_ORDER` está en el orden narrativo correcto.** Esto sí podría
   "apuntar mal" — un jefe antes que su propia zona, una fase 2 antes que su
   fase 1 — y como es una lista de módulo, se audita leyéndola, no jugándola.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from src.engine.core.stage_registry import STAGE_ORDER, ruta_del_mapa

#: Convención ya usada en `stage_registry.py` y en los nombres de módulo: un
#: id que contiene "boss" termina por derrota, no por trigger.
_ES_JEFE = re.compile(r"boss")

#: Las variantes sorteadas de la Fase 4 (`selector.py`) no tienen su propio
#: slot en STAGE_ORDER — comparten el de "stage4_1" — así que se verifican
#: aparte, por ruta directa.
_VARIANTES_STAGE4_1: tuple[str, ...] = (
    "assets/maps/stage4_1/stage4_1.tmx",
    "assets/maps/stage4_1b/stage4_1b.tmx",
    "assets/maps/stage4_1c/stage4_1c_a.tmx",
    "assets/maps/stage4_1c/stage4_1c_b.tmx",
    "assets/maps/stage4_1c/stage4_1c_c.tmx",
)


def _tiene_next_trigger(ruta) -> bool:
    return 'type="NextTrigger"' in ruta.read_text(encoding="utf-8")


class TestTodoEscenarioNoJefeDeclaraSuNextTrigger:
    """Sin él, `ProgressionSystem.check_next_trigger` nunca dispara y la
    partida no puede avanzar de ese escenario — un softlock silencioso."""

    def test_cada_escenario_de_stage_order(self) -> None:
        faltantes = []
        for stage_id in STAGE_ORDER:
            if _ES_JEFE.search(stage_id):
                continue
            ruta = ruta_del_mapa(stage_id)
            assert ruta is not None and ruta.exists(), (
                f"{stage_id}: STAGE_ORDER lo declara pero no se le pudo "
                f"resolver un TMX"
            )
            if not _tiene_next_trigger(ruta):
                faltantes.append(f"{stage_id} ({ruta.name})")
        assert not faltantes, (
            "escenarios sin NextTrigger — imposibles de completar: "
            + ", ".join(faltantes)
        )

    def test_las_variantes_de_la_fase_4_tambien(self) -> None:
        """`stage4_1`, `stage4_1b` y las tres cinemáticas de `stage4_1c` —
        cualquiera que le toque en el sorteo debe poder terminarse."""
        faltantes = [
            ruta for ruta in _VARIANTES_STAGE4_1
            if not _tiene_next_trigger(Path(ruta))
        ]
        assert not faltantes, f"variantes de la Fase 4 sin NextTrigger: {faltantes}"


class TestLosEscenariosDeJefeCompletanPorDerrota:
    """Un jefe sin `NextTrigger` no es un softlock **si** su módulo instancia
    un `BossBase` — `check_boss_defeat` lo completa al morir. Comprobarlo de
    verdad exigiría cargar la escena entera (contexto, assets); más barato y
    suficiente aquí: el código fuente del módulo resuelto debe referenciar
    `BossBase`, o de lo contrario no tiene ninguna vía de salida."""

    def test_cada_jefe_referencia_bossbase_en_su_paquete(self) -> None:
        import importlib.util

        from src.engine.core.stage_registry import (
            _STAGE_FACTORY_MAP,
            _STAGE_MODULE_MAP,
        )

        sin_salida = []
        for stage_id in STAGE_ORDER:
            if not _ES_JEFE.search(stage_id):
                continue
            ruta_tmx = ruta_del_mapa(stage_id)
            tiene_trigger = ruta_tmx is not None and _tiene_next_trigger(ruta_tmx)

            ruta_modulo = _STAGE_MODULE_MAP.get(stage_id)
            if ruta_modulo is None and stage_id in _STAGE_FACTORY_MAP:
                ruta_modulo = _STAGE_FACTORY_MAP[stage_id].rsplit(".", 1)[0]
            if ruta_modulo is None:
                # Convención por defecto de `discover_stages`: mismo nombre
                # de paquete y de módulo.
                ruta_modulo = f"src.stages.{stage_id}.{stage_id}"

            spec = importlib.util.find_spec(ruta_modulo)
            referencia_bossbase = False
            if spec is not None and spec.origin is not None:
                # `BossBase` a veces vive en un módulo hermano (la entidad
                # del jefe) que la escena importa, no en el propio archivo
                # de la escena — se busca en todo el paquete, no en un solo
                # fichero.
                paquete = Path(spec.origin).parent
                for py in paquete.glob("*.py"):
                    if "BossBase" in py.read_text(encoding="utf-8"):
                        referencia_bossbase = True
                        break

            if not tiene_trigger and not referencia_bossbase:
                sin_salida.append(f"{stage_id} ({ruta_modulo})")
        assert not sin_salida, (
            "escenarios de jefe sin NextTrigger NI referencia a BossBase — "
            "sin ninguna vía de completado conocida: " + ", ".join(sin_salida)
        )


class TestElOrdenNarrativoDeStageOrder:
    """`STAGE_ORDER` es la única fuente del "siguiente nivel" — si esta
    lista está mal ordenada, no hay ningún NextTrigger que lo arregle."""

    def test_cada_zona_agrupa_sus_propios_niveles_en_bloque(self) -> None:
        """0, 1_1..1_4, 2_1..2_4, 3_1..3_4, 4_1..4_2 — sin entrelazar zonas."""
        zonas = []
        for stage_id in STAGE_ORDER:
            m = re.match(r"stage(\d)", stage_id)
            zonas.append(int(m.group(1)) if m else -1)  # stage0/mecánicas → -1
        # Una vez que aparece la zona N, no debe reaparecer una zona < N
        # (salvo los -1 iniciales, que son prólogo/laboratorio).
        vistas_reales = [z for z in zonas if z > 0]
        assert vistas_reales == sorted(vistas_reales), (
            f"STAGE_ORDER entrelaza zonas fuera de orden: {vistas_reales}"
        )

    def test_cada_jefe_cierra_su_propia_zona(self) -> None:
        """El jefe de la zona N debe ser el último elemento de esa zona,
        no uno intermedio — si no, "completarlo" no te saca de la zona."""
        for i, stage_id in enumerate(STAGE_ORDER):
            if not _ES_JEFE.search(stage_id):
                continue
            m = re.match(r"stage(\d)", stage_id)
            if m is None:
                continue
            zona = int(m.group(1))
            siguiente = STAGE_ORDER[i + 1] if i + 1 < len(STAGE_ORDER) else None
            if siguiente is not None:
                m_sig = re.match(r"stage(\d)", siguiente)
                zona_siguiente = int(m_sig.group(1)) if m_sig else None
                assert zona_siguiente != zona, (
                    f"{stage_id} (jefe de la zona {zona}) no es el último "
                    f"escenario de su zona: le sigue {siguiente}, todavía "
                    f"en la misma zona"
                )

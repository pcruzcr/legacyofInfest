"""
Module: boss_rush_entry
System: engine.scenes
Academic Unit: N/A

AUD-191 — la puerta de entrada al modo Boss Rush.

`framework/stage/boss_rush_mode.py` estaba completo y probado desde AUD-022, y
su propia cabecera avisaba de que **nada del juego lo construía**: sin opción
de menú, sin escena, sin enganche. Estaba escrito, mantenido y era inalcanzable
para el jugador. La tabla de récords incluso le reservaba una columna, «BOSS
RUSH», que sólo podía mostrar `--:--.--`.

Esto es lo mínimo que lo convierte en una función del juego: componer el
combate con los jefes que el registro ya conoce y meterlos en la cola de
escenarios. La cola es la misma maquinaria que encadena la partida normal, así
que derrotar a un jefe lleva al siguiente sin código nuevo.

Lo que este módulo **no** hace, y conviene saberlo antes de anunciar la función
como terminada: `BossRushMode` sabe arrastrar la vida entre combates y llevar
la puntuación, pero para que eso se note hay que leerlo desde `StageScene` al
entrar y al salir de cada jefe. Aquí se deja el modo construido y activo en el
contexto, listo para que esa integración lo encuentre.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.framework.stage.boss_rush_mode import BossRushMode, BossRushStage

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.engine.scene.base_scene import BaseScene

#: Cómo se reconoce a un jefe dentro de `STAGE_ORDER`.
#:
#: Por el identificador y no por una lista escrita a mano: los cuatro jefes se
#: llaman `stage1_4_boss_venado`, `stage2_4_boss_rey`… y un quinto seguiría la
#: misma convención. Una lista fija se olvidaría de él en silencio, que es
#: justo el modo de fallo que este repositorio persigue.
MARCA_DE_JEFE = "boss"


def escenarios_de_jefe() -> list[tuple[str, type[BaseScene]]]:
    """Los jefes del juego, en el orden en que aparecen en la campaña."""
    from src.engine.core.stage_registry import STAGE_ORDER, discover_stages

    return [
        (stage_id, clase)
        for stage_id, clase in zip(STAGE_ORDER, discover_stages(), strict=False)
        if MARCA_DE_JEFE in stage_id
    ]


def construir_modo(jefes: list[tuple[str, type[BaseScene]]]) -> BossRushMode:
    """El modo con sus combates declarados, aún sin arrancar."""
    modo = BossRushMode()
    for stage_id, clase in jefes:
        # `scene_builder` recibe la clase misma: el modo queda sabiendo
        # construir cada combate, que es lo que le hará falta el día que
        # gestione la vida arrastrada sin pasar por la cola de escenarios.
        modo.add_stage(BossRushStage(
            boss_id=stage_id,
            boss_name=clase.__name__,
            scene_builder=clase,
        ))
    return modo


def empezar_boss_rush(context: GameContext) -> BossRushMode | None:
    """Arranca el combate seguido. Devuelve el modo, o `None` si no hay jefes.

    Devolver `None` en vez de reventar es deliberado: en un curso donde alguien
    esté reescribiendo los escenarios puede no quedar ninguno que case con la
    marca, y quedarse sin modo no debe impedir arrancar el juego.
    """
    jefes = escenarios_de_jefe()
    if not jefes:
        return None

    modo = construir_modo(jefes)
    modo.start()
    # El modo vive en el contexto para que `StageScene` pueda encontrarlo al
    # entrar en cada jefe sin que nadie tenga que pasárselo por parámetro.
    context.boss_rush = modo

    gestor = context.scene_manager
    gestor.set_stage_queue([clase for _, clase in jefes])
    gestor.set_stage_index(0)
    gestor._enter_next_stage()
    return modo

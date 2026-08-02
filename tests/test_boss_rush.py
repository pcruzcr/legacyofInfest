"""
Module: test_boss_rush
System: tests
Academic Unit: N/A

AUD-191 — el modo Boss Rush ya se puede jugar.

`framework/stage/boss_rush_mode.py` estaba completo y probado desde AUD-022, y
su propia cabecera avisaba: «NOT WIRED … nothing in the shipping game
constructs or calls it — there is no menu entry, scene or hook that reaches
it». Código mantenido, cubierto por pruebas, y **inalcanzable para el
jugador**. La tabla de récords incluso le reservaba una columna que sólo sabía
mostrar `--:--.--`.

Estas pruebas cubren lo que faltaba: que exista la puerta, que la atraviese, y
que el combate encadene los cuatro jefes.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.events import Events


@pytest.fixture
def contexto():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    from src.engine.core.app import App
    from src.engine.utils.asset_loader import AssetLoader
    from src.framework.stage.stage_loader import StageLoader

    registro = dict(StageLoader._entity_registry)
    app = App()
    try:
        yield app.context
    finally:
        gestor = app.context.scene_manager
        if hasattr(gestor, "cleanup"):
            gestor.cleanup()
        AssetLoader.clear_cache()
        StageLoader.clear_tmx_cache()
        StageLoader._entity_registry.clear()
        StageLoader._entity_registry.update(registro)


class TestLaPuertaDeEntrada:
    def test_el_menu_principal_ofrece_boss_rush(self, contexto) -> None:
        """Lo que faltaba literalmente: una fila en el menú."""
        from src.engine.scenes.title_scene import TitleScene

        titulo = TitleScene(contexto)
        contexto.scene_manager.push(titulo)
        titulo.on_enter()

        opciones = [str(i.value) for i in titulo._menu.items]
        assert "BOSS RUSH" in opciones, f"no está en el menú: {opciones}"

    def test_los_cuatro_jefes_se_reconocen_por_su_identificador(self) -> None:
        """Y no por una lista escrita a mano, que se olvidaría del quinto."""
        from src.engine.scenes.boss_rush_entry import escenarios_de_jefe

        jefes = [stage_id for stage_id, _ in escenarios_de_jefe()]
        assert len(jefes) == 4, f"jefes detectados: {jefes}"
        assert all("boss" in j for j in jefes)

    def test_elegirlo_lleva_al_primer_jefe(self, contexto) -> None:
        from src.engine.scenes.title_scene import TitleScene

        titulo = TitleScene(contexto)
        contexto.scene_manager.push(titulo)
        titulo.on_enter()

        titulo._activate_option("BOSS RUSH")

        assert type(contexto.scene_manager.current).__name__ == "BossVenadoScene"
        assert contexto.boss_rush.active
        assert contexto.boss_rush.progress == "1/4"


class TestElCombateEncadenado:
    def test_derrotar_a_los_cuatro_lleva_a_los_creditos(self, contexto) -> None:
        """El combate entero, sin pasar por ningún nivel normal."""
        from src.engine.scenes.boss_rush_entry import empezar_boss_rush

        gestor = contexto.scene_manager
        empezar_boss_rush(contexto)

        recorrido = [type(gestor.current).__name__]
        for _ in range(4):
            contexto.event_bus.emit(Events.STAGE_COMPLETE, stage_id="jefe")
            contexto.event_bus.dispatch()
            recorrido.append(type(gestor.current).__name__)

        assert recorrido[-1] == "EndCreditsScene", (
            f"el combate no termina en los créditos: {recorrido}"
        )
        assert not any("Stage1_1" in n or "Stage0" in n for n in recorrido), (
            f"se ha colado un nivel normal en el combate: {recorrido}"
        )

    def test_el_modo_arranca_con_los_marcadores_a_cero(self, contexto) -> None:
        """`start()` reinicia derrotados, tiempos y golpes: si no, la segunda
        partida heredaría los jefes ya vencidos de la primera."""
        from src.engine.scenes.boss_rush_entry import empezar_boss_rush

        modo = empezar_boss_rush(contexto)

        assert modo is not None
        assert modo.score == 0
        assert modo.progress == "1/4"
        assert not modo.is_complete()

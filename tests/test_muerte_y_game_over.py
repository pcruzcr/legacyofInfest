"""
Module: test_muerte_y_game_over
System: tests
Academic Unit: N/A

AUD-186 — caer en un foso mandaba al título, no a la pantalla de game over.

Qué se veía jugando
-------------------
En `stage0`, caer al `DeathPit` no mostraba el game over: el juego volvía a la
pantalla de título. Lo mismo con cualquier `HazardZone` mortal.

Por qué pasaba
--------------
`HazardSystem` —y `StageScene._kill_player`— hacen dos cosas seguidas::

    self._context.event_bus.emit(Events.PLAYER_DIED)      # 1. ENCOLA
    self._context.scene_manager.push(GameOverScene(...))  # 2. inmediato

`emit` no invoca a nadie: encola para el `dispatch()` del siguiente fotograma.
Así que cuando `_on_player_died` corre por fin, el game over **ya está encima
de la pila**. El manejador miraba sólo la cima, no encontraba `respawn()` ahí
—`GameOverScene` no lo tiene—, daba por hecho que ninguna escena sabía
gestionar la muerte y aplicaba su rama de reserva: volver al título.

El game over llegaba a mostrarse durante un fotograma y el título se lo comía.

La corrección
-------------
`_on_player_died` busca una escena con `respawn()` **en toda la pila**, no sólo
en la cima. Que alguien haya empujado el game over encima no cambia que el
escenario siga vivo debajo y sepa reaparecer.
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
        manager = app.context.scene_manager
        if hasattr(manager, "cleanup"):
            manager.cleanup()
        AssetLoader.clear_cache()
        StageLoader.clear_tmx_cache()
        StageLoader._entity_registry.clear()
        StageLoader._entity_registry.update(registro)


@pytest.fixture
def stage0(contexto):
    from src.stages.stage0.stage0 import Stage0

    escena = Stage0(contexto)
    contexto.scene_manager.push(escena)
    escena.on_enter()
    return escena


class TestMorirEnUnFoso:
    def test_caer_al_foso_lleva_al_game_over_y_no_al_titulo(
        self, contexto, stage0,
    ) -> None:
        """El caso que se vio jugando, reproducido entero."""
        gestor = contexto.scene_manager
        foso = stage0._stage_data.death_pits[0].rect
        jugador = stage0._player
        jugador.rect.midbottom = (foso.centerx, foso.top + 4)

        vistas = []
        for _ in range(120):
            stage0.update(1 / 60)
            contexto.event_bus.dispatch()
            vistas.append(type(gestor.current).__name__)
            if vistas[-1] == "GameOverScene":
                break

        assert "TitleScene" not in vistas, (
            f"morir en el foso devolvió al título en vez de mostrar el game "
            f"over; escenas vistas: {vistas[-6:]}"
        )
        assert type(gestor.current).__name__ == "GameOverScene", (
            f"tras caer al foso la escena es {type(gestor.current).__name__}"
        )

    def test_el_game_over_sigue_teniendo_el_escenario_debajo(
        self, contexto, stage0,
    ) -> None:
        """El game over necesita el escenario vivo debajo: su opción
        «continue» llama a `respawn()` sobre él. Si el manejador de muerte lo
        hubiera reemplazado, no habría a qué volver."""
        gestor = contexto.scene_manager
        foso = stage0._stage_data.death_pits[0].rect
        stage0._player.rect.midbottom = (foso.centerx, foso.top + 4)

        for _ in range(120):
            stage0.update(1 / 60)
            contexto.event_bus.dispatch()
            if type(gestor.current).__name__ == "GameOverScene":
                break

        assert gestor.stack_size >= 2, (
            "el game over quedó solo en la pila: al continuar no habría "
            "escenario al que volver"
        )


class TestElManejadorDeMuerte:
    def test_encuentra_el_escenario_aunque_no_este_en_la_cima(
        self, contexto,
    ) -> None:
        """El contrato que faltaba, aislado de los escenarios reales.

        `emit` encola y `push` es inmediato, así que cuando el manejador corre
        la cima puede ser cualquier cosa. Lo que importa es si queda alguien
        en la pila que sepa reaparecer.
        """
        from src.engine.scenes.game_over_scene import GameOverScene
        from src.stages.stage0.stage0 import Stage0

        gestor = contexto.scene_manager
        escenario = Stage0(contexto)
        gestor.push(escenario)

        contexto.event_bus.emit(Events.PLAYER_DIED)
        gestor.push(GameOverScene(contexto, escenario))
        contexto.event_bus.dispatch()

        assert type(gestor.current).__name__ == "GameOverScene", (
            "el manejador de muerte se llevó por delante el game over que "
            "acababan de empujar"
        )

    def test_sin_escenario_en_la_pila_sigue_yendo_al_titulo(
        self, contexto,
    ) -> None:
        """La rama de reserva no se pierde: morir en algo que no es un
        escenario —una demo, un laboratorio— sigue devolviendo al título."""
        from src.engine.scenes.bestiary_scene import BestiaryScene

        gestor = contexto.scene_manager
        gestor.push(BestiaryScene(contexto))

        contexto.event_bus.emit(Events.PLAYER_DIED)
        contexto.event_bus.dispatch()

        assert type(gestor.current).__name__ == "TitleScene"

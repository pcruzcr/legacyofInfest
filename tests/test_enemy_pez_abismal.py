"""AUD-519 — el pez abismal de 4.1b: aparece de la nada, persigue, no
puede tocar al jugador ni ser tocado por él.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.framework.entities.enemy_pez_abismal import EnemyPezAbismal


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class TestNoPuedeDanarAlJugador:
    def test_damage_on_contact_es_cero(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        assert pez.damage_on_contact == 0.0


class TestNoSePuedeDanar:
    """Pedido explícito: que el jugador tampoco pueda hacerle nada — una
    criatura a la que se puede golpear deja de sentirse ineludible."""

    def test_apply_hit_no_cambia_la_vida(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        vida_antes = pez.current_health
        pez.apply_hit(999.0, (0, 0))
        assert pez.current_health == vida_antes
        assert pez.is_alive is True

    def test_apply_hit_repetido_sigue_sin_matarlo(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        for _ in range(50):
            pez.apply_hit(999.0, (0, 0))
        assert pez.is_alive is True


class TestPersigueConInercia:
    def test_sin_jugador_deriva_sin_reventar(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(100, 100))
        for _ in range(60):
            pez.update(1 / 60)
        # No hay excepción, y sigue vivo y sin objetivo.
        assert pez.is_alive is True

    def test_con_jugador_se_acerca(self, _video) -> None:
        # Dentro del alcance de detección (`EnemyFlying` fija 180 px en
        # X) — más lejos, el pez sigue en patrulla y el resultado no
        # dice nada sobre la persecución.
        pez = EnemyPezAbismal(pygame.Vector2(0, 100))
        pez.set_player_ref(pygame.Rect(120, 100, 16, 32))
        distancia_inicial = abs(pez.position.x - 120)
        for _ in range(180):  # 3 s
            pez.update(1 / 60)
        distancia_final = abs(pez.position.x - 120)
        assert distancia_final < distancia_inicial

    def test_entra_en_estado_de_persecucion(self, _video) -> None:
        from src.framework.entities.enemy_base import EnemyState

        pez = EnemyPezAbismal(pygame.Vector2(0, 100))
        pez.set_player_ref(pygame.Rect(50, 100, 16, 32))
        for _ in range(30):
            pez.update(1 / 60)
        assert pez.state in (EnemyState.ALERT, EnemyState.CHASE)


class TestSeDejaVerAlAparecer:
    """AUD-526 — `Stage4_1B._invocar_pez` lo aparece a propósito justo más
    allá del borde de la cámara ("nunca dentro del cuadro"), que en una
    pantalla de 800 px es muchísimo más que los 180/96 px de
    `detection_range_x/y` que `EnemyFlying` fija para todos sus subtipos.
    Con esos valores el pez nacía fuera de su propio rango de detección,
    nunca entraba en ALERT/CHASE, y se retiraba en silencio sin que el
    jugador llegara a verlo — «no se ve el pez» reportado jugando.
    """

    def test_el_rango_de_deteccion_supera_la_distancia_real_de_aparicion(
        self, _video,
    ) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        # Media pantalla (800 px de ancho interno) más el margen de
        # aparición (60 px, `Stage4_1B.MARGEN_DE_APARICION_PX`) es la peor
        # distancia real entre el spawn y un jugador centrado en cámara.
        distancia_real_de_aparicion = 800 / 2 + 60
        assert pez.detection_range_x > distancia_real_de_aparicion, (
            f"detection_range_x={pez.detection_range_x} no cubre la "
            f"distancia real de aparición ({distancia_real_de_aparicion} "
            f"px) — el pez nacería fuera de su propio rango otra vez"
        )

    def test_aparecido_a_la_distancia_real_entra_en_persecucion(
        self, _video,
    ) -> None:
        from src.framework.entities.enemy_base import EnemyState

        # Reproduce el peor caso de `Stage4_1B._invocar_pez`: el jugador en
        # el centro de una cámara de 800 px, el pez 60 px más allá del
        # borde.
        pez = EnemyPezAbismal(pygame.Vector2(460.0, 100.0))
        pez.set_player_ref(pygame.Rect(0, 100, 20, 32))
        for _ in range(60):
            pez.update(1 / 60)
        assert pez.state in (EnemyState.ALERT, EnemyState.CHASE), (
            "a la distancia real de aparición, el pez sigue en PATROL: "
            "nunca detecta al jugador y nunca se deja ver"
        )


class TestDibujaSinReventar:
    def test_draw_no_revienta(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(50, 50))
        surface = pygame.Surface((320, 240))
        pez.draw(surface, pygame.Vector2(0, 0))

    def test_carga_su_propio_sprite_no_el_de_zona(self, _video) -> None:
        """No existe un volador de "zone4" y, de existir, sería un
        halcón/cuervo — no una criatura abisal."""
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        assert "fly" in pez._sprite_frames
        assert len(pez._sprite_frames["fly"]) > 0


class TestEsMasGrandeYAmenazador:
    """AUD-529 — pedido tras jugarlo: «debe ser mucho más grande y
    amenazador». Antes compartía el 14×10 que `EnemyFlying` fija para
    todos sus subtipos — el mismo tamaño que un pájaro de zona1, no una
    amenaza abisal."""

    def test_el_sprite_es_el_doble_del_generico_de_volador(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        assert pez._sprite_fw == 28
        assert pez._sprite_fh == 20

    def test_el_rect_de_colision_crecio_con_el_sprite(self, _video) -> None:
        pez = EnemyPezAbismal(pygame.Vector2(0, 0))
        assert pez.rect.width >= pez._sprite_fw
        assert pez.rect.height >= pez._sprite_fh

    def test_el_fichero_de_sprite_tiene_el_tamano_declarado(self, _video) -> None:
        """`_sprite_fw/_sprite_fh` describen cómo se recorta la hoja — si
        el archivo no mide un múltiplo exacto, el recorte sale mal aunque
        la carga no reviente."""
        from src.engine.utils.asset_loader import AssetLoader
        from src.framework.entities.enemy_pez_abismal import SPRITE_PATH

        surf = AssetLoader.load_image(SPRITE_PATH)
        assert surf.get_width() % EnemyPezAbismal.SPRITE_ANCHO == 0
        assert surf.get_height() == EnemyPezAbismal.SPRITE_ALTO


class TestSeOyeAntesDeVerse:
    """AUD-529 — pedido explícito: el pez «no hará daño físico... su
    función es generar pánico... el jugador debe sentirlo y escucharlo
    antes de poder verlo»."""

    def test_aparecer_emite_el_sonido_de_aviso(self, _video) -> None:
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.events import Events
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.stage4_1b.stage4_1b import Stage4_1B

        entity_factory.ensure_registered()
        bus = EventBus()
        vistos: list[str] = []

        def _al_sonido(**_data: object) -> None:
            vistos.append("sonó")

        bus.subscribe(Events.SFX_ENEMIES_PEZ_ABISMAL_ACERCARSE, _al_sonido)

        ctx = GameContext(input_manager=InputManager(), audio_manager=AudioManager(),
                           scene_manager=None, event_bus=bus, clock=None,
                           save_manager=SaveManager())
        ctx.scene_manager = SceneManager(ctx)
        sc = Stage4_1B(ctx)
        ctx.scene_manager.push(sc)
        sc._invocar_pez()
        bus.dispatch()

        assert vistos, (
            "aparecer al pez no emite el sonido de aviso — el jugador ya "
            "no lo escucha antes de verlo"
        )

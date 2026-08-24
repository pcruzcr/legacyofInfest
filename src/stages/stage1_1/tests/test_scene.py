"""
Module: test_scene
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: IV (Escena y Z-order)
Description: Scroll del tilemap e interruptor de enemigos.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

import pygame
import pytest

from src.stages.stage1_1.entities.canopy_bird import CanopyBird
from src.stages.stage1_1.entities.jungle_frog import JungleFrog
from src.stages.stage1_1.stage1_1 import Stage1_1_LaEntrada

CTRL = [(100.0, 80.0), (140.0, 40.0), (180.0, 120.0), (220.0, 60.0)]


def _ave(**kw) -> CanopyBird:
    kw.setdefault("waypoints", list(CTRL))
    return CanopyBird(pygame.Vector2(CTRL[0]), **kw)


def _lienzo(color=(128, 128, 128), tam=(64, 48)) -> pygame.Surface:
    s = pygame.Surface(tam)
    s.fill(color)
    return s

# ════════════════════════════════════════════════════════════════════
# Interruptor de enemigos — para probar el recorrido sin combate
# ════════════════════════════════════════════════════════════════════

def test_el_filtro_quita_todos_los_enemigos() -> None:
    """Quita cualquier EnemyBase y conserva lo demás, para poder recorrer
    el nivel sin combate mientras se ajusta la geometría."""
    from src.framework.entities.enemy_walker import EnemyWalker

    entidades = [
        EnemyWalker(pygame.Vector2(10.0, 10.0)),
        JungleFrog(pygame.Vector2(20.0, 20.0)),
        _ave(),
        "no-soy-enemigo",
    ]

    quedan = Stage1_1_LaEntrada.filtrar_enemigos(entidades)

    assert quedan == ["no-soy-enemigo"]


def test_el_filtro_con_lista_vacia_devuelve_vacia() -> None:
    assert Stage1_1_LaEntrada.filtrar_enemigos([]) == []


def test_por_defecto_los_enemigos_estan_activos() -> None:
    """El interruptor es una ayuda temporal: el valor por defecto del
    entregable debe ser CON enemigos."""
    assert Stage1_1_LaEntrada.ENEMIGOS_ACTIVOS is True


# ════════════════════════════════════════════════════════════════════
# Scroll del tilemap — Unidad IV
# ════════════════════════════════════════════════════════════════════

def test_sincronizar_scroll_mueve_de_verdad_el_tilemap() -> None:
    """El mapa de tiles TIENE que desplazarse con la cámara.

    `StageScene.update()` mueve la cámara asignando
    `map_layer._map_layer.view_rect` directamente (stage_scene.py:268).
    En pyscroll eso cambia el valor pero NO reposiciona el búfer interno
    de tiles: el dibujo sale idéntico y el fondo se queda clavado
    mientras las entidades sí se mueven.

    El scroll real solo ocurre llamando `center()`, que recalcula el
    desplazamiento del búfer. Verificado con pyscroll 2.30 y reproducible
    también en el stage0 del profesor.
    """
    from src.engine.core import settings
    from src.framework.entities.entity_factory import ensure_registered
    from src.framework.stage.stage_loader import StageLoader

    ensure_registered()
    # AUD-591: aquí vivían dos register_entity ("Skitter"/"Bat") que quedaron
    # huérfanos cuando el TMX pasó a usar "ShooterFrog"/"FlyingBird": ningún
    # objeto del mapa lleva ya esos tipos, y el validador los llevaba años
    # avisando como «registro dentro de una función». Las sustituciones reales
    # ahora las hace el propio módulo de la escena al importarse.
    datos = StageLoader.load(
        "assets/maps/stage1_1/stage1_1.tmx",
    )

    def pintar() -> bytes:
        s = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        s.fill((0, 0, 0))
        datos.map_layer.draw(s)
        return pygame.image.tobytes(s, "RGB")

    Stage1_1_LaEntrada.sincronizar_scroll(datos.map_layer, pygame.Vector2(0, 0))
    inicio = pintar()

    Stage1_1_LaEntrada.sincronizar_scroll(datos.map_layer, pygame.Vector2(1200, 100))
    lejos = pintar()

    assert inicio != lejos, "el tilemap no se desplazó con la cámara"


def test_sincronizar_scroll_centra_donde_corresponde() -> None:
    """center() recibe el CENTRO de la vista; camera.offset es la esquina
    superior izquierda. La conversión debe sumar media pantalla.

    Se elige un offset dentro del rango NO acotado: el renderer se crea con
    `clamp_camera=True` (stage_loader.py:298), así que nunca deja ver fuera
    del mapa. Con vista de 800x600 sobre un mapa de 3840x640, el centro
    válido va de (400, 300) a (3440, 340) — pedir más se acota, y con razón.
    """
    from src.engine.core import settings
    from src.framework.stage.stage_loader import StageLoader

    datos = StageLoader.load(
        "assets/maps/stage1_1/stage1_1.tmx",
    )
    off = pygame.Vector2(800, 20)
    Stage1_1_LaEntrada.sincronizar_scroll(datos.map_layer, off)

    vista = datos.map_layer._map_layer.view_rect
    assert vista.centerx == pytest.approx(
        off.x + settings.INTERNAL_WIDTH // 2, abs=1)
    assert vista.centery == pytest.approx(
        off.y + settings.INTERNAL_HEIGHT // 2, abs=1)


def test_el_mapa_es_mas_alto_que_la_pantalla() -> None:
    """El motor corre a 800x600 (settings.py:11-12), NO a 320x224 como dice
    el enunciado. Un mapa más bajo que la pantalla se ve entero de golpe y
    deja vacío alrededor — que fue justo lo que pasó con 448 px de alto."""
    from src.engine.core import settings
    from src.framework.stage.stage_loader import StageLoader

    datos = StageLoader.load(
        "assets/maps/stage1_1/stage1_1.tmx",
    )
    ancho, alto = datos.map_pixel_size

    assert alto >= settings.INTERNAL_HEIGHT
    assert ancho >= settings.INTERNAL_WIDTH * 2   # varias pantallas de recorrido

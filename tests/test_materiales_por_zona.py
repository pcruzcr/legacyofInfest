"""
Module: test_materiales_por_zona
System: tests
Description: AUD-490 — GAP-039 dejaba la restitución como un dato de todo el
`PhysicsProfile` (un material para el nivel entero), no por región. Esta
prueba fija el puente que le falta: una `ZonaDeFriccion` puede declarar
`material`, `sistema_friccion` lo escribe en el dueño del `Transform` que
solapa (mismo patrón que ya usa `facing`), y el jugador lo usa en vez del
material del perfil mientras está dentro.

Fuera de alcance a propósito, como ya documentó GAP-039 en su día: leer
`material` de un tileset en vez de una `ZonaDeFriccion` — nadie lo pide desde
un mapa real todavía.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.ecs import Transform, Velocidad, World, ZonaDeFriccion
from src.framework.ecs import systems as S
from src.framework.physics.perfil import GOMA, MATERIALES, ROCA


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class TestElComponenteDeclaraMaterial:
    def test_roca_por_defecto(self) -> None:
        """Ningún mapa entregado declara `material`: debe seguir siendo roca."""
        zona = ZonaDeFriccion(pygame.Rect(0, 0, 10, 10))
        assert zona.material == "roca"

    def test_se_puede_declarar_otro(self) -> None:
        zona = ZonaDeFriccion(pygame.Rect(0, 0, 10, 10), material="goma")
        assert zona.material == "goma"


class TestElTmxLeeElMaterial:
    def test_friction_zone_con_material(self) -> None:
        from src.framework.stage.stage_data import StageData
        from src.framework.stage.stage_loader import StageLoader

        class _Obj:
            type = "FrictionZone"
            name = ""
            x, y, width, height = 0, 0, 32, 32

        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        StageLoader._handle_componente(stage, _Obj(), {"material": "goma"}, "FrictionZone")
        zonas = [c for grupo in stage.componentes for c in grupo
                 if isinstance(c, ZonaDeFriccion)]
        assert zonas and zonas[0].material == "goma"

    def test_friction_zone_sin_material_es_roca(self) -> None:
        from src.framework.stage.stage_data import StageData
        from src.framework.stage.stage_loader import StageLoader

        class _Obj:
            type = "FrictionZone"
            name = ""
            x, y, width, height = 0, 0, 32, 32

        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        StageLoader._handle_componente(stage, _Obj(), {}, "FrictionZone")
        zonas = [c for grupo in stage.componentes for c in grupo
                 if isinstance(c, ZonaDeFriccion)]
        assert zonas and zonas[0].material == "roca"


class TestElSistemaEscribeElMaterialEnElDueno:
    """Mismo patrón que `Transform.facing`: sólo escribe si el dueño lo pide."""

    class _Dueno:
        def __init__(self) -> None:
            self.position = pygame.Vector2(10, 10)
            self.rect = pygame.Rect(10, 10, 8, 8)
            self.velocity = pygame.Vector2(0, 0)
            self._material_de_zona = None

    def test_entra_en_una_zona_de_goma(self) -> None:
        mundo = World()
        mundo.crear(ZonaDeFriccion(pygame.Rect(0, 0, 200, 200), material="goma"))
        dueno = self._Dueno()
        transform = Transform(dueno.position, dueno.rect, duenio=dueno)
        mundo.crear(transform, Velocidad(dueno.velocity))

        S.sistema_friccion(mundo, 1 / 60)

        assert dueno._material_de_zona is MATERIALES["goma"]

    def test_al_salir_vuelve_a_ninguno(self) -> None:
        mundo = World()
        mundo.crear(ZonaDeFriccion(pygame.Rect(0, 0, 20, 20), material="goma"))
        dueno = self._Dueno()
        dueno.position.update(500, 500)  # fuera de la zona
        dueno.rect.topleft = (500, 500)
        dueno._material_de_zona = MATERIALES["goma"]  # como si viniera de dentro
        transform = Transform(dueno.position, dueno.rect, duenio=dueno)
        mundo.crear(transform, Velocidad(dueno.velocity))

        S.sistema_friccion(mundo, 1 / 60)

        assert dueno._material_de_zona is None

    def test_una_entidad_propia_sin_dueno_no_revienta(self) -> None:
        """Las entidades ECS puras (plataformas, bloques) no tienen `_material_de_zona`."""
        mundo = World()
        mundo.crear(ZonaDeFriccion(pygame.Rect(0, 0, 200, 200), material="goma"))
        mundo.crear(
            Transform(pygame.Vector2(10, 10), pygame.Rect(10, 10, 8, 8)),
            Velocidad(pygame.Vector2(0, 0)),
        )
        S.sistema_friccion(mundo, 1 / 60)  # no debe lanzar


class TestElJugadorRebotaConElMaterialDeLaZona:
    def test_restitucion_de_la_zona_gana_a_la_del_perfil(self) -> None:
        from src.framework.entities.player import Player

        jugador = Player(pygame.Vector2(0, 0))
        assert jugador.perfil.material is ROCA  # el de siempre, sin tocar nada
        jugador._material_de_zona = GOMA

        estado = jugador._estado_de_movimiento_para_resolver()
        assert estado.restitucion == GOMA.restitucion
        assert estado.restitucion != ROCA.restitucion

    def test_sin_zona_usa_el_material_del_perfil(self) -> None:
        from src.framework.entities.player import Player

        jugador = Player(pygame.Vector2(0, 0))
        jugador._material_de_zona = None

        estado = jugador._estado_de_movimiento_para_resolver()
        assert estado.restitucion == jugador.perfil.material.restitucion

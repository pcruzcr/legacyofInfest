"""
La guía del motor dice la verdad sobre el motor.

Por qué existe esta suite
=========================
`docs/07_STAGE0_DESIGN.md` describía, hasta hoy, un escenario de 240 × 14
baldosas con 27 mensajes y 12 enemigos que **no existe**: el mapa real mide
100 × 38. Nadie mintió; el documento se escribió antes que el mapa y nunca se
volvió a leer con el mapa delante. De esa ficción salió un generador que
llevaba meses listo para borrar el escenario de referencia del curso.

`docs/60_GUIA_COMPLETA_DEL_MOTOR.md` es el documento que más gente va a leer
—es el manual del diseñador— y por tanto el que más caro sale que envejezca.
Sus cifras se comprueban aquí contra el código.

Qué NO comprueba esto
---------------------
La prosa. Una guía puede tener todas las cifras bien y seguir explicando mal
las cosas. Esto sólo garantiza que los números no mientan; que se entienda
sigue siendo trabajo de quien la escribe.
"""
from __future__ import annotations

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GUIA = RAIZ / "docs" / "60_GUIA_COMPLETA_DEL_MOTOR.md"


@pytest.fixture(scope="module")
def guia() -> str:
    assert GUIA.exists(), f"falta {GUIA.name}: es el manual del diseñador"
    return GUIA.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def _motor():
    """Todo lo que la guía afirma, leído del motor de una sola vez."""
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame

    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((8, 8))

    from src.engine.core import settings
    from src.engine.core.achievements import AchievementSystem
    from src.engine.core.inventory import _ITEM_DEFS
    from src.framework.entities import entity_factory
    from src.framework.entities.enemy_base import EnemyState
    from src.framework.entities.player import PlayerState
    from src.framework.stage.stage_loader import StageLoader
    from src.framework.stage.tmx_diagnostics import (
        BUILTIN_OBJECT_TYPES,
        COLLISION_OBJECT_TYPES,
    )

    entity_factory.ensure_registered()
    logros = AchievementSystem.init_instance()

    return {
        "registrados": set(StageLoader._entity_registry),
        "integrados": set(BUILTIN_OBJECT_TYPES),
        "colision": set(COLLISION_OBJECT_TYPES),
        "estados_jugador": list(PlayerState),
        "estados_enemigo": list(EnemyState),
        "logros": set(logros._defs),
        "objetos": set(_ITEM_DEFS),
        "colores_luz": set(StageLoader.LIGHT_COLORS),
        "settings": settings,
    }


class TestLasCifrasDelIndice:
    """Los números que la guía pone en sus propios títulos."""

    def test_los_tipos_de_objeto(self, guia, _motor) -> None:
        total = (len(_motor["integrados"]) + len(_motor["registrados"])
                 + len(_motor["colision"]))
        assert f"**{total} tipos**" in guia, (
            f"la guía no dice que hay {total} tipos de objeto"
        )

    def test_los_estados_del_jugador(self, guia, _motor) -> None:
        n = len(_motor["estados_jugador"])
        assert f"El jugador: {n} estados" in guia, (
            f"la guía no dice que el jugador tiene {n} estados"
        )

    def test_los_estados_de_enemigo(self, guia, _motor) -> None:
        n = len(_motor["estados_enemigo"])
        assert f"{n} estados" in guia

    def test_los_tipos_de_enemigo(self, guia, _motor) -> None:
        n = len(_motor["registrados"])
        assert f"Enemigos: {n} tipos" in guia


class TestLasListasEstanCompletas:
    """Una guía a la que le falta la mitad del catálogo es peor que ninguna.

    El estudiante que no encuentra `Zipline` aquí concluye que no existe.
    """

    def test_menciona_cada_tipo_integrado(self, guia, _motor) -> None:
        faltan = sorted(t for t in _motor["integrados"] if f"`{t}`" not in guia)
        assert not faltan, (
            f"la guía no menciona estos tipos del motor: {faltan}"
        )

    def test_menciona_cada_tipo_de_enemigo(self, guia, _motor) -> None:
        faltan = sorted(t for t in _motor["registrados"] if t not in guia)
        assert not faltan, (
            f"la guía no menciona estos enemigos registrados: {faltan}"
        )

    def test_menciona_cada_estado_del_jugador(self, guia, _motor) -> None:
        faltan = sorted(s.name for s in _motor["estados_jugador"]
                        if f"`{s.name}`" not in guia)
        assert not faltan, f"estados del jugador sin documentar: {faltan}"

    def test_menciona_cada_estado_de_enemigo(self, guia, _motor) -> None:
        faltan = sorted(s.name for s in _motor["estados_enemigo"]
                        if f"`{s.name}`" not in guia)
        assert not faltan, f"estados de enemigo sin documentar: {faltan}"

    def test_menciona_cada_logro(self, guia, _motor) -> None:
        faltan = sorted(i for i in _motor["logros"] if f"`{i}`" not in guia)
        assert not faltan, f"logros sin documentar: {faltan}"

    def test_menciona_cada_objeto_del_inventario(self, guia, _motor) -> None:
        faltan = sorted(i for i in _motor["objetos"] if f"`{i}`" not in guia)
        assert not faltan, f"objetos de inventario sin documentar: {faltan}"

    def test_menciona_cada_color_de_luz(self, guia, _motor) -> None:
        faltan = sorted(c for c in _motor["colores_luz"] if f"`{c}`" not in guia)
        assert not faltan, f"colores de `Light` sin documentar: {faltan}"


class TestLosNumerosDelJugador:
    """La tabla de constantes: es la que se usa para decidir si un salto cabe."""

    @pytest.mark.parametrize("constante", [
        "PLAYER_MAX_HEALTH", "GRAVITY", "PLAYER_WALK_SPEED",
        "PLAYER_JUMP_FORCE", "PLAYER_MAX_FALL_SPEED", "PLAYER_COYOTE_FRAMES",
        "PLAYER_DASH_SPEED", "COMBO_MAX",
    ])
    def test_el_valor_publicado_es_el_valor_real(
        self, guia, _motor, constante,
    ) -> None:
        valor = getattr(_motor["settings"], constante)
        # Se busca el número tal cual, con coma decimal o sin decimales: la
        # guía está en español y escribe «0,5», no «0.5».
        # También sin signo: la guía escribe «−380 px/s» con el menos
        # tipográfico U+2212, que no es el mismo carácter que `-`.
        crudos = {valor, abs(valor)}
        candidatos: set[str] = set()
        for v in crudos:
            candidatos.add(str(v))
            candidatos.add(str(v).replace(".", ","))
            if float(v) == int(v):
                candidatos.add(str(int(v)))
        assert any(c in guia for c in candidatos), (
            f"{constante} vale {valor} y la guía no lo dice en ninguna forma"
        )

    def test_la_resolucion_interna(self, guia, _motor) -> None:
        s = _motor["settings"]
        assert f"{s.INTERNAL_WIDTH} × {s.INTERNAL_HEIGHT}" in guia
        assert f"{s.TARGET_FPS} FPS" in guia


class TestLaGuiaNoPrometeLoQueNoHay:
    """El fallo de `07_STAGE0_DESIGN.md`, al revés: inventar cosas.

    Se revisan los tipos que la guía presenta como propios del motor —los que
    aparecen en una tabla con `type` en Tiled— contra lo que el cargador
    acepta de verdad.
    """

    def test_no_documenta_tipos_inexistentes(self, guia, _motor) -> None:
        conocidos = (_motor["integrados"] | _motor["registrados"]
                     | _motor["colision"])
        # Los encabezados `#### \`Algo\`` de la sección 4 son declaraciones de
        # que ese tipo existe.
        declarados = set(re.findall(r"^#### `([A-Za-z_]+)`", guia, re.M))
        inventados = sorted(declarados - conocidos)
        assert not inventados, (
            f"la guía documenta tipos que el motor no acepta: {inventados}"
        )

    def test_los_comandos_que_recomienda_existen(self, guia) -> None:
        scripts = set(re.findall(r"python (scripts/[a-z_]+\.py)", guia))
        assert scripts, "la guía no recomienda ninguna herramienta"
        faltan = sorted(s for s in scripts if not (RAIZ / s).exists())
        assert not faltan, f"la guía manda ejecutar scripts que no existen: {faltan}"

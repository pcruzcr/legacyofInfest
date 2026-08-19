"""AUD-396 — materiales de superficie con restitución. Cierra GAP-039.

El defecto
==========
La fricción por superficie existía desde AUD-236 (`ZonaDeFriccion` +
`sistema_friccion`) y el perfil declaraba `friccion` desde AUD-336. Lo que no
existía era el **material** como cosa nombrada que agrupe las dos propiedades,
y por eso faltaba la segunda: sin restitución no hay rebote, así que el hielo y
el musgo se podían expresar y la goma no.

Dónde estaba el hueco exactamente: `resolver_eje_y` ponía
`estado.velocidad.y = 0.0` al aterrizar. Una línea, sin manera de decir «este
suelo devuelve parte del golpe».

Lo que importa de estas pruebas
===============================
Dos cosas, y la segunda es la que se olvida:

1. Que la goma rebote.
2. Que la roca **siga sin rebotar**, y que nada vibre. La restitución mal
   terminada no falla: hace que el personaje nunca acabe de posarse, con botes
   cada vez más pequeños que no llegan a cero, `en_el_suelo` parpadeando y la
   máquina de estados entrando y saliendo de «en el aire» para siempre. Por eso
   hay umbral, y por eso hay una prueba del umbral.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.physics.perfil import (
    GOMA,
    HIELO,
    LODO,
    MATERIALES,
    MUSGO,
    ROCA,
    Material,
    PhysicsProfile,
)
from src.framework.physics.resolucion import EstadoDeMovimiento, resolver_eje_y

SUELO = [pygame.Rect(0, 200, 400, 40)]


def _estado(restitucion: float, vy: float = 400.0) -> EstadoDeMovimiento:
    """Un cuerpo cayendo justo encima del suelo."""
    return EstadoDeMovimiento(
        posicion=pygame.Vector2(100, 168),
        velocidad=pygame.Vector2(0, vy),
        ancho=16,
        alto=32,
        en_el_suelo=False,
        restitucion=restitucion,
    )


class TestElCatalogo:
    def test_la_roca_no_rebota(self) -> None:
        assert ROCA.restitucion == 0.0

    def test_la_goma_rebota(self) -> None:
        assert GOMA.restitucion > 0.0

    def test_el_hielo_resbala_y_el_musgo_frena(self) -> None:
        assert HIELO.friccion < ROCA.friccion < MUSGO.friccion

    def test_los_materiales_son_inmutables(self) -> None:
        """Dos plataformas de goma comparten instancia: nadie debe poder
        ablandar una desde otro sitio."""
        with pytest.raises(AttributeError):
            GOMA.restitucion = 0.9  # type: ignore[misc]

    def test_se_pueden_buscar_por_nombre(self) -> None:
        """Es lo que permitirá declararlos desde un TMX o un tileset."""
        assert MATERIALES["goma"] is GOMA
        assert set(MATERIALES) == {"roca", "hielo", "musgo", "goma", "lodo"}

    def test_el_lodo_no_cambia_la_fisica_solo_se_nombra(self) -> None:
        """AUD-551 — GAP-070 punto 1: el lodo ya frenaba de verdad por
        `ZonaDeFriccion.multiplicador` (AUD-522); este material existe sólo
        para que la pisada distinga lodo de tierra firme
        (`states/grounded.py`), no para tocar la física — mismo criterio
        que ya usa `musgo` con su `friccion` sin consumidor."""
        assert LODO.restitucion == 0.0
        assert MATERIALES["lodo"] is LODO


class TestElRebote:
    def test_con_roca_el_aterrizaje_es_el_de_siempre(self) -> None:
        """La prueba de que los dieciséis mapas no cambian."""
        estado = _estado(ROCA.restitucion)
        resolver_eje_y(estado, 1 / 60, SUELO)
        assert estado.velocidad.y == 0.0
        assert estado.en_el_suelo is True

    def test_con_goma_sale_despedido_hacia_arriba(self) -> None:
        estado = _estado(GOMA.restitucion)
        resolver_eje_y(estado, 1 / 60, SUELO)
        assert estado.velocidad.y < 0, (
            "la goma no devolvió nada: sigue sin poder expresarse un suelo "
            "que rebote, que es el hueco entero"
        )
        assert estado.en_el_suelo is False

    def test_devuelve_la_fraccion_que_dice_el_material(self) -> None:
        estado = _estado(0.5, vy=400.0)
        resolver_eje_y(estado, 1 / 60, SUELO)
        assert estado.velocidad.y == pytest.approx(-200.0)

    def test_un_impacto_flojo_no_rebota_y_se_queda_apoyado(self) -> None:
        """El umbral. Sin él, el personaje vibra sobre la goma para siempre."""
        estado = _estado(GOMA.restitucion, vy=10.0)
        resolver_eje_y(estado, 1 / 60, SUELO)
        assert estado.velocidad.y == 0.0
        assert estado.en_el_suelo is True, (
            "un impacto por debajo del umbral dejó al cuerpo sin apoyar: "
            "`en_el_suelo` parpadeará cada fotograma"
        )

    def test_los_botes_se_amortiguan_hasta_pararse(self) -> None:
        """La propiedad que de verdad importa: que la cosa termine.

        Se deja caer sobre goma y se simula; el cuerpo tiene que acabar
        apoyado y quieto. Si el umbral no funcionara, esto no terminaría.
        """
        estado = _estado(GOMA.restitucion, vy=600.0)
        for _ in range(600):
            estado.velocidad.y += 980.0 * (1 / 60)
            resolver_eje_y(estado, 1 / 60, SUELO)
        assert estado.en_el_suelo is True
        assert estado.velocidad.y == 0.0, (
            f"tras diez segundos sigue botando a {estado.velocidad.y:.1f} px/s"
        )


class TestElPerfil:
    def test_el_perfil_por_defecto_es_roca(self) -> None:
        assert PhysicsProfile().material is ROCA

    def test_un_perfil_puede_declarar_otro_material(self) -> None:
        assert PhysicsProfile(material=GOMA).material.restitucion == GOMA.restitucion

    def test_cada_perfil_trae_el_suyo(self) -> None:
        """`field(default_factory=...)`, no un valor compartido mutable."""
        assert PhysicsProfile().material is PhysicsProfile().material


def test_el_jugador_lleva_la_restitucion_de_su_perfil() -> None:
    """El cable trampa del cableado: sin esto el material sería un dato que
    nadie consulta — el modo de fallo de esta casa."""
    from src.framework.entities.player import Player

    jugador = Player(pygame.Vector2(100, 100))
    jugador.perfil = PhysicsProfile(material=Material("prueba", restitucion=0.5))
    suelo = [pygame.Rect(0, 160, 400, 40)]
    jugador.velocity.y = 400.0
    jugador.is_grounded = False
    jugador.position.y = 120

    for _ in range(30):
        jugador.update(1 / 60, suelo, None)
        if jugador.velocity.y < 0:
            break
    assert jugador.velocity.y < 0, (
        "el jugador aterrizó sin rebotar aunque su perfil declara un material "
        "con restitución: el material no llega al resolutor"
    )

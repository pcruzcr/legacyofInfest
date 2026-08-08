"""
AUD-334 — el resolutor de mundo compartido, probado como función pura.

Antes la resolución de colisión vivía como métodos del jugador y cada
contexto de juego nuevo tenía que copiarlos. Ahora vive en
`framework/physics/resolucion.py`, como pasos puros sobre un
`EstadoDeMovimiento` que devuelven hechos (`Contacto`) sin tocar entidades.

Estas pruebas fijan los comportamientos auditados —AUD-130 (integrar
siempre), el umbral `v_overlap <= 2`, el ledge grab, AUD-297/323/324/326
(cuestas), AUD-328 (cenital), AUD-255 (repisas)— sin construir un jugador:
si el resolutor puro cumple los hechos, cualquier entidad que lo consuma
hereda los mismos contratos.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.physics import resolucion as r
from src.framework.physics.perfil import CENITAL, VUELO, Cuestas, PhysicsProfile
from src.framework.stage.pendientes import Pendiente

DT = 1.0 / 60.0


def _estado(
    x: float,
    y: float,
    vx: float = 0.0,
    vy: float = 0.0,
    w: float = 20.0,
    h: float = 32.0,
    grounded: bool = False,
    prev_foot_y: float | None = None,
) -> r.EstadoDeMovimiento:
    return r.EstadoDeMovimiento(
        posicion=pygame.Vector2(x, y),
        velocidad=pygame.Vector2(vx, vy),
        ancho=w,
        alto=h,
        en_el_suelo=grounded,
        prev_foot_y=prev_foot_y if prev_foot_y is not None else y + h,
    )


class TestElEjeX:
    def test_integra_siempre_aunque_no_haya_solidos(self) -> None:
        """AUD-130 — «integrar siempre, resolver sólo si hay contra qué»."""
        estado = _estado(100.0, 100.0, vx=120.0)
        r.resolver_eje_x(estado, DT, [])
        assert estado.posicion.x == pytest.approx(102.0)

    def test_el_umbral_de_dos_pixeles_deja_andar_sobre_el_borde(self) -> None:
        """El `v_overlap <= 2` separa «de pie encima» de «contra ello»."""
        suelo = pygame.Rect(0, 300, 400, 200)
        estado = _estado(100.0, 269.0, vx=120.0, grounded=True)
        r.resolver_eje_x(estado, DT, [suelo])
        assert estado.posicion.x == pytest.approx(102.0)
        assert estado.velocidad.x == pytest.approx(120.0)

    def test_andar_contra_el_muro_frena_y_reporta_el_lado(self) -> None:
        suelo = pygame.Rect(0, 300, 400, 200)
        muro = pygame.Rect(300, 100, 32, 200)
        estado = _estado(290.0, 268.0, vx=120.0, grounded=True)
        contacto = r.resolver_eje_x(estado, DT, [suelo, muro])
        assert estado.posicion.x == pytest.approx(280.0)
        assert estado.velocidad.x == pytest.approx(0.0)
        assert contacto.lado_de_pared == 1

    def test_en_el_aire_la_pared_se_reporta_como_pared_de_salto(self) -> None:
        muro = pygame.Rect(300, 0, 32, 200)
        estado = _estado(290.0, 50.0, vx=120.0)
        contacto = r.resolver_eje_x(estado, DT, [muro])
        assert contacto.pared_en_el_aire is True

    def test_pisando_suelo_no_hay_pared_de_salto(self) -> None:
        muro = pygame.Rect(300, 0, 32, 200)
        estado = _estado(290.0, 50.0, vx=120.0, grounded=True)
        contacto = r.resolver_eje_x(estado, DT, [muro])
        assert contacto.pared_en_el_aire is False

    def test_el_borde_con_hueco_permite_agarrarse(self) -> None:
        """El ledge grab: borde de pared libre por encima y cabeza a la altura."""
        muro = pygame.Rect(300, 100, 32, 200)
        estado = _estado(290.0, 100.0, vx=120.0)
        contacto = r.resolver_eje_x(estado, DT, [muro])
        assert contacto.repisa_libre is True

    def test_el_borde_tapado_no_permite_agarrarse(self) -> None:
        muro = pygame.Rect(300, 100, 32, 200)
        tapa = pygame.Rect(300, 84, 32, 16)
        estado = _estado(290.0, 100.0, vx=120.0)
        contacto = r.resolver_eje_x(estado, DT, [muro, tapa])
        assert contacto.repisa_libre is False


class TestElEjeY:
    def test_caer_y_aterrizar_en_suelo_solido(self) -> None:
        suelo = pygame.Rect(0, 300, 400, 200)
        estado = _estado(100.0, 266.0, vy=300.0)
        contacto = r.resolver_eje_y(estado, DT, [suelo])
        assert contacto.aterrizo is True
        assert contacto.aterrizo_en == "suelo"
        assert estado.en_el_suelo is True
        assert estado.velocidad.y == pytest.approx(0.0)
        assert estado.posicion.y == pytest.approx(268.0)

    def test_golpear_el_techo_frena_y_marca_topo(self) -> None:
        techo = pygame.Rect(0, 100, 400, 32)
        estado = _estado(100.0, 136.0, vy=-300.0)
        contacto = r.resolver_eje_y(estado, DT, [techo])
        assert contacto.topo is True
        assert estado.velocidad.y == pytest.approx(0.0)
        assert estado.posicion.y == pytest.approx(132.0)
        assert estado.en_el_suelo is False

    def test_venia_del_suelo_recuerda_el_estado_de_entrada(self) -> None:
        """AUD-297 — el dato que el paso de cuestas necesita después."""
        estado = _estado(100.0, 100.0, vy=0.0, grounded=True)
        contacto = r.resolver_eje_y(estado, DT, [])
        assert estado.venia_del_suelo is True
        assert contacto.venia_del_suelo is True
        assert estado.en_el_suelo is False

    def test_sin_solidos_la_caida_no_aterriza(self) -> None:
        estado = _estado(100.0, 100.0, vy=300.0)
        contacto = r.resolver_eje_y(estado, DT, [])
        assert contacto.aterrizo is False
        assert estado.en_el_suelo is False
        assert estado.posicion.y == pytest.approx(105.0)


class TestLasParedesDeLasCuestas:
    def test_la_cara_empinada_frena_la_entrada(self) -> None:
        """AUD-323 — el extremo alto de la rampa es un muro en toda su altura."""
        rampa = Pendiente(pygame.Rect(64, 100, 64, 32))
        estado = _estado(125.0, 78.0, vx=60.0)
        r.resolver_paredes_de_pendientes(estado, [rampa])
        assert estado.posicion.x == pytest.approx(128.0)
        assert estado.velocidad.x == pytest.approx(0.0)


class TestLasCuestas:
    RAMPA = Pendiente(pygame.Rect(0, 200, 64, 32))

    def test_aterrizar_en_cuesta_aterriza_y_proyecta(self) -> None:
        """AUD-324 — caer en vertical sobre la cuesta la reporta como suelo."""
        estado = _estado(16.0, 187.0, vy=300.0)
        contacto = r.resolver_cuestas(
            estado, DT, [self.RAMPA], Cuestas())
        assert contacto.aterrizo is True
        assert contacto.aterrizo_en == "cuesta"
        assert estado.en_el_suelo is True
        assert estado.velocidad.y == pytest.approx(0.0)
        assert estado.posicion.y == pytest.approx(187.0)

    def test_subiendo_la_cuesta_no_pega(self) -> None:
        estado = _estado(16.0, 187.0, vy=-300.0)
        contacto = r.resolver_cuestas(
            estado, DT, [self.RAMPA], Cuestas())
        assert contacto.aterrizo is False
        assert estado.en_el_suelo is False
        assert estado.posicion.y == pytest.approx(187.0)

    def test_el_margen_de_pegado_evita_el_traqueteo(self) -> None:
        """Bajar la cuesta: el margen pega al jugador que va un poco por encima."""
        estado = _estado(16.0, 186.0, grounded=True)
        r.resolver_cuestas(estado, DT, [self.RAMPA], Cuestas())
        assert estado.posicion.y == pytest.approx(187.0)

    def test_sin_margen_el_traqueteo_vuelve(self) -> None:
        """AUD-333 — el margen es del perfil: cero lo desactiva para el contexto."""
        estado = _estado(16.0, 186.0, grounded=True)
        r.resolver_cuestas(
            estado, DT, [self.RAMPA], Cuestas(margen_pegado=0.0))
        assert estado.posicion.y == pytest.approx(186.0)

    def test_quieto_en_la_cuesta_se_desliza(self) -> None:
        """AUD-326 — el deslizamiento sostenido, sin entrada horizontal."""
        estado = _estado(16.0, 187.0, grounded=True)
        r.resolver_cuestas(
            estado, DT, [self.RAMPA],
            Cuestas(velocidad_deslizamiento=90.0))
        assert estado.velocidad.x == pytest.approx(-36.0)
        assert estado.posicion.x == pytest.approx(16.0 - 36.0 * DT)
        assert estado.en_el_suelo is True


class TestLasRepisasDeUnSentido:
    PLAT = pygame.Rect(100, 200, 64, 16)

    def test_caer_encima_aterriza_y_reporta_el_aire(self) -> None:
        """La posición ya viene integrada (la integró el eje Y): los pies
        del fotograma anterior estaban a la altura del borde."""
        estado = _estado(120.0, 171.0, vy=0.0, prev_foot_y=198.0)
        contacto = r.resolver_repisas(estado, [self.PLAT])
        assert contacto.aterrizo is True
        assert contacto.aterrizo_en == "repisa"
        assert contacto.aterrizo_desde_el_aire is True
        assert estado.en_el_suelo is True
        assert estado.velocidad.y == pytest.approx(0.0)
        assert estado.posicion.y == pytest.approx(168.0)

    def test_subiendo_atraviesa(self) -> None:
        estado = _estado(120.0, 165.0, vy=-300.0)
        contacto = r.resolver_repisas(estado, [self.PLAT])
        assert contacto.aterrizo is False
        assert estado.posicion.y == pytest.approx(165.0)

    def test_venido_de_abajo_no_se_apoya(self) -> None:
        estado = _estado(
            120.0, self.PLAT.bottom + 2.0, vy=60.0,
            prev_foot_y=self.PLAT.bottom + 34.0)
        r.resolver_repisas(estado, [self.PLAT])
        assert estado.en_el_suelo is False

    def test_de_pie_encima_no_viene_del_aire(self) -> None:
        """Aterriza cada fotograma de pie — pero no «desde el aire»: el
        sonido de AUD-255 es responsabilidad de la entidad con este dato."""
        estado = _estado(120.0, 168.0, grounded=True, prev_foot_y=200.0)
        contacto = r.resolver_repisas(estado, [self.PLAT])
        assert contacto.aterrizo is True
        assert contacto.aterrizo_desde_el_aire is False
        assert estado.en_el_suelo is True


class TestElResolutorCompuesto:
    def test_cae_y_aterriza_consolidando_hechos(self) -> None:
        suelo = pygame.Rect(0, 300, 400, 200)
        estado = _estado(100.0, 266.0, vy=300.0)
        contacto = r.resolver_movimiento(estado, DT, [suelo])
        assert contacto.en_el_suelo is True
        assert contacto.aterrizo is True
        assert contacto.aterrizo_en == "suelo"
        assert estado.posicion.y == pytest.approx(268.0)

    def test_el_perfil_plataformas_pega_a_la_cuesta(self) -> None:
        rampa = Pendiente(pygame.Rect(0, 200, 64, 32))
        estado = _estado(16.0, 186.0, grounded=True)
        contacto = r.resolver_movimiento(
            estado, DT, [], pendientes=[rampa],
            perfil=PhysicsProfile.plataformas())
        assert contacto.en_el_suelo is True
        assert estado.posicion.y == pytest.approx(187.0)

    def test_el_perfil_cenital_no_pega_a_la_cuesta(self) -> None:
        """AUD-328 — en planta la rampa es terreno pintado: ni glue ni repisas."""
        rampa = Pendiente(pygame.Rect(0, 200, 64, 32))
        estado = _estado(16.0, 186.0, grounded=True)
        perfil = PhysicsProfile(modo=CENITAL)
        contacto = r.resolver_movimiento(
            estado, DT, [], pendientes=[rampa], perfil=perfil)
        assert contacto.en_el_suelo is False
        assert estado.posicion.y == pytest.approx(186.0)

    def test_el_perfil_vuelo_no_pega_a_la_cuesta(self) -> None:
        """AUD-335 — en vuelo la rampa tampoco es suelo: son semánticas de
        plataformas, y el resolutor las reserva para ese modo."""
        rampa = Pendiente(pygame.Rect(0, 200, 64, 32))
        estado = _estado(16.0, 186.0, grounded=True)
        perfil = PhysicsProfile(modo=VUELO)
        contacto = r.resolver_movimiento(
            estado, DT, [], pendientes=[rampa], perfil=perfil)
        assert contacto.en_el_suelo is False
        assert estado.posicion.y == pytest.approx(186.0)

    def test_el_compuesto_reporta_la_pared(self) -> None:
        suelo = pygame.Rect(0, 300, 400, 200)
        muro = pygame.Rect(300, 100, 32, 200)
        estado = _estado(290.0, 268.0, vx=120.0, grounded=True)
        contacto = r.resolver_movimiento(estado, DT, [suelo, muro])
        assert contacto.lado_de_pared == 1
        assert contacto.pared_en_el_aire is False
        assert estado.posicion.x == pytest.approx(280.0)

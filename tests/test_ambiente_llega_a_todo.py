"""AUD-402/403 — audio y sombras del ambiente. Cierran GAP-051.

Qué quedaba
===========
`GAP-051` decía que el estado ambiental «llega a la luz y se para ahí», y
marcaba tres consumidores en rojo. AUD-399 hizo el campo que los tres
necesitaban (`azimut_solar`) y AUD-401 el color grading. Estos son los otros
dos:

* **Audio ambiental** — `stage_parts/sonido.py` es despacho de efectos por
  eventos, y nada leía `viento` ni `precipitacion`. El canal de ambiente y su
  bus existían desde AUD-149: sonaban igual en calma que en tormenta.
* **Sombras dirigidas por el sol** — `vfx/sombras_proyectadas.py` proyecta
  desde un `foco`, de forma **radial**, porque una antorcha está a dos metros.
  El sol manda rayos paralelos, y eso es otra proyección, no la misma con el
  foco lejos: para acercarse al límite habría que poner el foco a millones de
  píxeles, y la coma flotante se rompe mucho antes.

Las dos decisiones que estas pruebas fijan
==========================================
* El audio **modula** el volumen del bus, no lo fija. Fijarlo pisaría la
  preferencia del jugador, que es justo lo que ese bus existe para respetar.
* Sin sol —de noche, o con él justo encima— no hay sombra que pintar, y ése es
  el valor por defecto: un escenario que no publique ambiente se ve igual que
  antes de este lote.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.vfx.sombras_proyectadas import sombra_direccional
from src.framework.world.environment import EnvironmentState


class TestElAudioDelAmbiente:
    def test_la_calma_no_es_silencio(self) -> None:
        """Callar el ambiente del todo se oye como un fallo de audio."""
        calma = EnvironmentState(precipitacion=0.0, viento=0.0)
        assert calma.intensidad_sonora > 0.0

    def test_la_tormenta_suena_mas_que_la_calma(self) -> None:
        calma = EnvironmentState(precipitacion=0.0, viento=0.0)
        tormenta = EnvironmentState(precipitacion=1.0, viento=1.0)
        assert tormenta.intensidad_sonora > calma.intensidad_sonora

    def test_la_lluvia_pesa_mas_que_el_viento(self) -> None:
        """Una tormenta sin lluvia suena a poco; un vendaval sin agua no llena
        el espectro."""
        lluvia = EnvironmentState(precipitacion=1.0, viento=0.0)
        viento = EnvironmentState(precipitacion=0.0, viento=1.0)
        assert lluvia.intensidad_sonora > viento.intensidad_sonora

    def test_el_viento_cuenta_en_valor_absoluto(self) -> None:
        """Una racha hacia el oeste no suena más floja que una hacia el este."""
        oeste = EnvironmentState(viento=-0.8)
        este = EnvironmentState(viento=0.8)
        assert oeste.intensidad_sonora == pytest.approx(este.intensidad_sonora)

    def test_nunca_se_pasa_de_uno(self) -> None:
        """Es un multiplicador de volumen: por encima de 1 satura."""
        bestia = EnvironmentState(precipitacion=5.0, viento=9.0)
        assert bestia.intensidad_sonora <= 1.0


class TestLaSombraDelSol:
    def _rect(self) -> pygame.Rect:
        return pygame.Rect(100, 100, 20, 40)

    def test_de_noche_no_hay_sombra(self) -> None:
        assert sombra_direccional(self._rect(), 0.0, 0.0) == ()

    def test_con_el_sol_encima_tampoco(self) -> None:
        """Dirección 0 es sombra a plomo: no hay nada que alargar."""
        assert sombra_direccional(self._rect(), 0.0, 2.0) == ()

    def test_da_un_cuadrilatero(self) -> None:
        assert len(sombra_direccional(self._rect(), 1.0, 1.0)) == 4

    def test_se_alarga_hacia_donde_dice_la_direccion(self) -> None:
        rect = self._rect()
        derecha = sombra_direccional(rect, 1.0, 1.0)
        izquierda = sombra_direccional(rect, -1.0, 1.0)
        assert derecha[2].x > rect.right
        assert izquierda[2].x < rect.right

    def test_un_objeto_mas_alto_proyecta_mas_sombra(self) -> None:
        """Lo que hace que una columna se distinga de un escalón."""
        bajo = sombra_direccional(pygame.Rect(0, 0, 20, 10), 1.0, 1.0)
        alto = sombra_direccional(pygame.Rect(0, 0, 20, 80), 1.0, 1.0)
        assert alto[2].x > bajo[2].x

    def test_el_sol_bajo_alarga_mas_que_el_alto(self) -> None:
        rect = self._rect()
        mediodia = sombra_direccional(rect, 0.3, 1.0)
        atardecer = sombra_direccional(rect, 0.3, 3.5)
        assert atardecer[2].x > mediodia[2].x


class TestElCableado:
    """Que los dos lleguen a alguien. Sin esto son derivados que nadie pide."""

    def test_el_sistema_de_luz_arranca_sin_sol(self) -> None:
        from src.framework.vfx.lighting import LightSystem

        assert LightSystem().sombra_solar == (0.0, 0.0)

    def test_el_sistema_de_luz_acepta_la_direccion(self) -> None:
        from src.framework.vfx.lighting import LightSystem

        luz = LightSystem()
        luz.set_sombra_solar((0.5, 2.0))
        assert luz.sombra_solar == (0.5, 2.0)

    @pytest.mark.parametrize("metodo", [
        "_aplicar_audio_ambiental", "set_sombra_solar", "publish_color_matrix",
    ])
    def test_la_simulacion_llama_a_los_tres(self, metodo: str) -> None:
        """Por AST y mirando **llamadas**, no texto.

        Los tres consumidores de GAP-051 tienen que salir de `_aplicar_hora`,
        que es el único sitio que consume el estado. Un derivado que nadie pide
        es justo lo que este hueco registra que pasó con la mitad productora de
        `world/`.
        """
        import ast
        import inspect

        from src.framework.scenes.stage_parts import simulacion

        arbol = ast.parse(inspect.getsource(simulacion))
        llamadas = {
            n.func.attr for n in ast.walk(arbol)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        }
        assert metodo in llamadas

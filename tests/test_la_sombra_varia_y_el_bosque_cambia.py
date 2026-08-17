"""AUD-513 — tres puntos de GAP-062 que quedaban pendientes tras AUD-481/492.

* Punto 10 — la sombra del Gavilán era siempre el mismo `_gavilan`
  reconocible, a la misma altura, siempre de izquierda a derecha: *«no
  debería aparecer como un sprite claramente identificable cada vez...
  queremos presencia, no exposición»*.
* Punto 13 — nada del escenario cambiaba tras el silencio súbito: *«un
  árbol que antes estaba en pie ahora está caído... el jugador reconstruye
  que algo ocurrió sin que se le muestre qué»*.
* Puntos 21-22 — la lluvia y la audibilidad del grito del Gavilán eran dos
  canales completamente independientes: *«un sonido tenue que la lluvia
  esconde y luego deja oír»*.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from tests.ayudantes_stage4_1 import construir_escena, preparar_video
from tests.test_stage4_1 import _llevar_a


@pytest.fixture(scope="module")
def _video():
    preparar_video()


@pytest.fixture
def escena(_video):
    sc = construir_escena()
    yield sc
    sc.on_exit()


def _tras_el_silencio(escena):
    from src.stages.stage4_1 import trazado
    from src.stages.stage4_1.fases import FASES

    fase4 = FASES[3]
    objetivo = fase4.desde_columna + int(0.6 * trazado.ANCHO_SECCION)
    _llevar_a(escena, objetivo)
    assert escena._shake_disparado is True
    return escena


class TestLaSombraVariaDeCruceEnCruce:
    def test_no_siempre_es_la_silueta_reconocible(self, escena) -> None:
        _tras_el_silencio(escena)
        variantes = set()
        for _ in range(60):
            escena._iniciar_cruce_de_sombra()
            variantes.add(escena._sombra_es_identificable)
        assert variantes == {True, False}, (
            "60 cruces y sólo salió una variante: la sombra sigue siendo "
            "siempre la misma silueta"
        )

    def test_la_reconocible_es_minoria(self, escena) -> None:
        """*"Queremos presencia, no exposición"*: la silueta identificable
        no puede ser la norma."""
        _tras_el_silencio(escena)
        identificables = 0
        for _ in range(200):
            escena._iniciar_cruce_de_sombra()
            if escena._sombra_es_identificable:
                identificables += 1
        assert identificables < 100, (
            f"{identificables}/200 cruces reconocibles: sigue siendo la "
            "norma, no la excepción"
        )

    def test_la_altura_varia(self, escena) -> None:
        _tras_el_silencio(escena)
        alturas = set()
        for _ in range(40):
            escena._iniciar_cruce_de_sombra()
            alturas.add(escena._sombra_altura)
        assert len(alturas) > 1, "la sombra cruza siempre a la misma altura"

    def test_las_dos_direcciones_ocurren(self, escena) -> None:
        _tras_el_silencio(escena)
        direcciones = set()
        for _ in range(60):
            escena._iniciar_cruce_de_sombra()
            direcciones.add(escena._sombra_izquierda_a_derecha)
        assert direcciones == {True, False}


class TestElBosqueCambiaTrasElSilencio:
    def test_un_arbol_cae_tras_el_silencio(self, escena) -> None:
        import unittest.mock as mock

        import pygame

        from src.stages.stage4_1 import siluetas, trazado

        _tras_el_silencio(escena)
        # Centrar la cámara sobre el último árbol (el que cae, por
        # `INDICE_ARBOL_QUE_CAE = -1`): con offset (0, 0) todo el bosque
        # queda fuera de pantalla y `_dibujar_siluetas_de_fondo` no llama a
        # nadie (mismo ajuste que ya hizo falta para las osamentas de la
        # Fase 3 en test_el_horizonte_y_la_despedida.py).
        ultimo_arbol = trazado.ARBOLES_FASE4[-1]
        offset = pygame.Vector2((ultimo_arbol * 16 - 400) / 0.85, 0)
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_decoracion(pygame.Surface((800, 600)), offset)
        formas = [c.args[1] for c in espia.call_args_list]
        assert siluetas._arbol_caido in formas, (
            "ningún árbol usó la silueta caída tras el silencio"
        )

    def test_ningun_arbol_cae_antes_del_silencio(self, escena) -> None:
        import unittest.mock as mock

        import pygame

        from src.stages.stage4_1 import siluetas, trazado
        from src.stages.stage4_1.fases import FASES

        fase4 = FASES[3]
        _llevar_a(escena, fase4.desde_columna + int(0.1 * trazado.ANCHO_SECCION))
        assert escena._shake_disparado is False
        ultimo_arbol = trazado.ARBOLES_FASE4[-1]
        offset = pygame.Vector2((ultimo_arbol * 16 - 400) / 0.85, 0)
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_decoracion(pygame.Surface((800, 600)), offset)
        assert espia.called, "sanity: los árboles deben pintarse (sólo sin caída todavía)"
        formas = [c.args[1] for c in espia.call_args_list]
        assert siluetas._arbol_caido not in formas


class TestLaLluviaEscondeYDejaOirElGrito:
    def test_el_volumen_varia_con_la_marea_de_lluvia(self, escena) -> None:
        _tras_el_silencio(escena)
        volumenes = []
        for t in (0.0, escena.PERIODO_DE_LLUVIA_FASE4 * 0.25,
                  escena.PERIODO_DE_LLUVIA_FASE4 * 0.5,
                  escena.PERIODO_DE_LLUVIA_FASE4 * 0.75):
            escena._tiempo = t
            claro = escena._intensidad_de_lluvia_fase4()
            volumen = (escena.VOLUMEN_GRITO[0]
                       + claro * (escena.VOLUMEN_GRITO[1] - escena.VOLUMEN_GRITO[0]))
            volumenes.append(volumen)
        assert len(set(round(v, 3) for v in volumenes)) > 1, (
            "el volumen del grito no cambia con el tiempo: sigue siendo "
            "un canal independiente de la lluvia"
        )
        assert all(
            escena.VOLUMEN_GRITO[0] <= v <= escena.VOLUMEN_GRITO[1]
            for v in volumenes
        )

    def test_el_grito_de_verdad_usa_el_volumen_calculado(self, escena, monkeypatch) -> None:
        _tras_el_silencio(escena)
        escena._tiempo = escena.PERIODO_DE_LLUVIA_FASE4 * 0.25  # un claro
        llamadas = []
        monkeypatch.setattr(
            escena, "_play_sfx_spatial",
            lambda *a, **kw: llamadas.append(kw.get("volume")),
        )
        escena._proximo_grito = 0.0
        escena._actualizar_grito_del_gavilan(1 / 60)
        assert len(llamadas) == 1
        esperado = (escena.VOLUMEN_GRITO[0] + escena._intensidad_de_lluvia_fase4()
                    * (escena.VOLUMEN_GRITO[1] - escena.VOLUMEN_GRITO[0]))
        assert llamadas[0] == pytest.approx(esperado, abs=1e-6)

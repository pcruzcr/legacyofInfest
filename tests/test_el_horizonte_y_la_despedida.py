"""AUD-513 — el hueco sistémico de GAP-058/059/065 y dos piezas de GAP-061/064.

`BG_Far`/`BG_Mid`/`BG_Near` seguían vacías en las seis fases del 4-1
(GAP-058, GAP-059, GAP-065 §12): el mapa trae las tres capas de parallax
declaradas y ninguna con contenido. Pintar tiles de un tileset que el
proyecto no tiene sería el mismo «arte falso» que `siluetas.py` ya evita
para los espíritus — así que el horizonte se pinta igual que ellos: un
contorno procedural, no un PNG.

Aprovecha la misma técnica para cerrar dos puntos más, ya con ganchos
listos en el código:

* GAP-061 punto 15 — las osamentas de la Fase 3 dejan de ser una sola
  calavera repetida y ganan una columna vertebral gigante de fondo (la
  mitad **visual** de «arquitectura»; la mitad **navegable** —una
  plataforma sólida de verdad— exige geometría nueva en el generador,
  fuera de este lote).
* GAP-064 puntos 7-8, 22-23 y 15-16 — la silueta de Paburu que crece con
  el avance de la Fase 6, y los tres espíritus liberados reapareciendo un
  instante como despedida.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from tests.ayudantes_stage4_1 import construir_escena, preparar_video
from tests.test_stage4_1 import _dentro_de_la_fase, _posicionar_sin_fisica


@pytest.fixture(scope="module")
def _video():
    preparar_video()


@pytest.fixture
def escena(_video):
    sc = construir_escena()
    yield sc
    sc.on_exit()


class TestElHorizontePintaEnLasSeisFases:
    def test_no_revienta_en_ninguna_fase(self, escena) -> None:
        """Sanity: `HORIZONTE_POR_FASE` cubre las seis, no cinco."""
        lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
        for numero in range(1, 7):
            _posicionar_sin_fisica(escena, _dentro_de_la_fase(numero))
            escena._dibujar_horizonte(lienzo, pygame.Vector2(0, 0))

    def test_cada_fase_tiene_su_propio_perfil(self, escena) -> None:
        """Las seis crestas no deben leerse como la misma silueta
        repintada: color, altura base, amplitud y frecuencia distintos."""
        perfiles = escena.HORIZONTE_POR_FASE
        assert len(perfiles) == 6
        assert len(set(perfiles.values())) == 6, (
            "dos fases comparten exactamente el mismo perfil de horizonte"
        )

    def test_el_paralaje_es_el_mas_lento_del_escenario(self, escena) -> None:
        """`BG_Far` es el plano más lejano: debe moverse menos que la
        decoración de primer plano (paralaje 0,85) al desplazar la cámara."""
        import unittest.mock as mock

        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_horizonte",
        ) as espia:
            escena._dibujar_horizonte(
                pygame.Surface((800, 600)), pygame.Vector2(1000.0, 0.0))
        desplazamiento_x = espia.call_args.args[3]
        assert desplazamiento_x == pytest.approx(1000.0 * 0.15)


class TestElVientoEscalaEnLaFase3:
    """GAP-061 punto 5: *"leve → fuerte → intermitente → combinado con
    pendientes → combinado con salto"* — antes una sola intensidad para
    todo el tramo."""

    def test_es_mas_debil_al_entrar_que_mas_adelante(self, escena) -> None:
        factor_temprano = escena._factor_de_viento(0.02)
        factor_tardio = escena._factor_de_viento(0.8)
        assert factor_temprano < factor_tardio, (
            "el viento no escala: la misma fuerza al entrar que cerca del final"
        )
        assert factor_temprano == pytest.approx(escena.VIENTO_FACTOR_LEVE, abs=0.05)

    def test_se_queda_en_su_tope_pasado_el_avance_de_plena_fuerza(self, escena) -> None:
        assert escena._factor_de_viento(0.6) == pytest.approx(
            escena.VIENTO_FACTOR_FUERTE)
        assert escena._factor_de_viento(1.0) == pytest.approx(
            escena.VIENTO_FACTOR_FUERTE), (
            "el viento debe seguir fuerte, no volver a caer cerca del final"
        )


class TestElRayoRevelaLasOsamentas:
    """GAP-061: *"el rayo sube el brillo, no revela nada"* — antes sólo
    escalaba `ambient_brightness`; ahora las osamentas gigantes saltan de
    apenas visibles a plena visibilidad durante el relámpago."""

    def test_las_osamentas_son_tenues_sin_rayo(self, escena) -> None:
        assert escena.ALFA_HUESOS_NORMAL < escena.ALFA_HUESOS_CON_RAYO

    def test_el_rayo_las_saca_a_plena_visibilidad(self, escena) -> None:
        import unittest.mock as mock

        columna_hueso = escena.COLUMNAS_DE_HUESOS_FASE3[0]
        _posicionar_sin_fisica(escena, columna_hueso)
        offset = pygame.Vector2((columna_hueso * 16 - 400) / 0.4, 0)

        escena._rayo = escena.DURACION_DEL_RAYO  # el relámpago, en su pico
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_columna_de_huesos(pygame.Surface((800, 600)), offset)
        assert espia.called
        alfa_con_rayo = espia.call_args.args[7]

        escena._rayo = 0.0
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia2:
            escena._dibujar_columna_de_huesos(pygame.Surface((800, 600)), offset)
        alfa_sin_rayo = espia2.call_args.args[7]

        assert alfa_con_rayo > alfa_sin_rayo, (
            "el relámpago no aumentó la visibilidad de las osamentas"
        )


class TestLaColumnaDeHuesosSoloEnLaFase3:
    def test_se_pinta_en_fase_3(self, escena) -> None:
        """Con la cámara centrada sobre la primera vértebra (columna 320,
        `COLUMNAS_DE_HUESOS_FASE3`), no fuera de pantalla."""
        import unittest.mock as mock

        columna_hueso = escena.COLUMNAS_DE_HUESOS_FASE3[0]
        _posicionar_sin_fisica(escena, columna_hueso)
        # `_dibujar_columna_de_huesos` aplica paralaje 0,4 al offset: para
        # que la vértebra caiga cerca del centro de una pantalla de 800 px,
        # el offset tiene que deshacer ese factor, no ser 1:1 con la cámara.
        offset = pygame.Vector2((columna_hueso * 16 - 400) / 0.4, 0)
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_columna_de_huesos(pygame.Surface((800, 600)), offset)
        assert espia.called, "ninguna vértebra gigante se pintó en la Fase 3"

    def test_no_se_pinta_fuera_de_la_fase_3(self, escena) -> None:
        import unittest.mock as mock

        _posicionar_sin_fisica(escena, _dentro_de_la_fase(4))
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_columna_de_huesos(
                pygame.Surface((800, 600)), pygame.Vector2(0, 0))
        assert not espia.called


class TestLaSiluetaDePaburuCrece:
    """GAP-064 puntos 7-8, 22-23: se insinúa, no se muestra completa, y
    sólo dentro de la Fase 6."""

    def test_no_aparece_al_entrar_a_la_fase_6(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        fase6 = FASES[5]
        _posicionar_sin_fisica(escena, fase6.desde_columna + 2)
        import unittest.mock as mock

        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_paburu(pygame.Surface((800, 600)), pygame.Vector2(0, 0))
        assert not espia.called, "Paburu se ve desde el primer paso: no crece"

    def test_aparece_pasado_el_umbral_y_crece_con_el_avance(self, escena) -> None:
        import unittest.mock as mock

        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase6 = FASES[5]

        def _ancho_en(avance: float) -> int:
            columna = fase6.desde_columna + int(avance * trazado.ANCHO_SECCION)
            _posicionar_sin_fisica(escena, columna)
            with mock.patch(
                "src.stages.stage4_1.siluetas.dibujar_contorno",
            ) as espia:
                escena._dibujar_paburu(
                    pygame.Surface((800, 600)), pygame.Vector2(0, 0))
            if not espia.called:
                return 0
            return espia.call_args.kwargs.get("ancho", espia.call_args.args[4])

        ancho_temprano = _ancho_en(escena.AVANCE_PARA_PABURU + 0.02)
        ancho_tardio = _ancho_en(0.95)
        assert ancho_temprano > 0
        assert ancho_tardio > ancho_temprano, (
            "la silueta de Paburu no crece con el avance de la Fase 6"
        )

    def test_no_aparece_en_otras_fases(self, escena) -> None:
        import unittest.mock as mock

        _posicionar_sin_fisica(escena, _dentro_de_la_fase(5))
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_paburu(pygame.Surface((800, 600)), pygame.Vector2(0, 0))
        assert not espia.called


class TestLaDespedidaDeLosEspiritus:
    """GAP-064 puntos 15-16: sólo los espíritus liberados de verdad
    (AUD-474) se despiden — a quien no se liberó no le queda nada."""

    def _liberar(self, escena, numero_de_fase: int) -> None:
        from src.stages.stage4_1 import trazado

        evento = trazado.evento_de_liberacion(numero_de_fase)
        for d in escena._stage_data.disparadores:
            if d.evento == evento:
                d.disparado = True
                return
        pytest.fail(f"no se encontró el disparador de liberación de la fase {numero_de_fase}")

    def test_un_espiritu_no_liberado_no_se_despide(self, escena) -> None:
        import unittest.mock as mock

        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase6 = FASES[5]
        columna = fase6.desde_columna + int(
            escena.AVANCES_DESPEDIDA[0] * trazado.ANCHO_SECCION)
        _posicionar_sin_fisica(escena, columna)
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_despedida_de_los_espiritus(
                pygame.Surface((800, 600)), pygame.Vector2(0, 0))
        assert not espia.called, (
            "el Venado se despidió sin que el jugador lo liberara nunca"
        )

    def test_un_espiritu_liberado_si_se_despide(self, escena) -> None:
        import unittest.mock as mock

        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        self._liberar(escena, 2)  # el Venado es fase.numero == 2 (espiritu=0)
        fase6 = FASES[5]
        columna = fase6.desde_columna + int(
            escena.AVANCES_DESPEDIDA[0] * trazado.ANCHO_SECCION)
        _posicionar_sin_fisica(escena, columna)
        with mock.patch(
            "src.stages.stage4_1.siluetas.dibujar_contorno",
        ) as espia:
            escena._dibujar_despedida_de_los_espiritus(
                pygame.Surface((800, 600)), pygame.Vector2(0, 0))
        assert espia.called

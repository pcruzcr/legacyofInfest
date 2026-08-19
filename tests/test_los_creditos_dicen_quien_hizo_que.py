"""AUD-548 — los créditos eran una lista inventada: "Student A: Stage
1-1", "Student B: Stage 1-2"… nombres de relleno que no correspondían a
quién entregó qué escenario. Los `.tmx` reales ya declaran `author`
desde que se entregaron (`César Ubáu Calvo`, `Fabrizio E`, `Jose Pablo
Monestel Cruz`, `Saul`, `Yariel`); nadie los leía.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    yield


class TestLaCarpetaDelMapaResuelveLosQuinceEscenarios:
    def test_cada_stage_id_de_stage_order_resuelve_un_tmx_real(self, _video) -> None:
        from src.engine.core.stage_registry import STAGE_ORDER, ruta_del_mapa

        sin_mapa = [sid for sid in STAGE_ORDER if ruta_del_mapa(sid) is None]
        assert sin_mapa == [], (
            f"stage_id sin `.tmx` localizable: {sin_mapa} — los créditos no "
            f"podrán leer su autor"
        )

    def test_la_ruta_resuelta_existe_de_verdad(self, _video) -> None:
        from src.engine.core.stage_registry import STAGE_ORDER, ruta_del_mapa

        for stage_id in STAGE_ORDER:
            ruta = ruta_del_mapa(stage_id)
            assert ruta is not None and ruta.exists(), (
                f"{stage_id}: {ruta} no existe en disco"
            )


class TestLosCreditosLeenElAutorReal:
    def test_ningun_credito_dice_student_a(self, _video) -> None:
        """El síntoma exacto que se reporta: nombres de relleno en vez
        de autores reales."""
        from src.engine.scenes.end_credits_scene import _creditos_por_escenario

        creditos = _creditos_por_escenario()
        autores_de_relleno = [
            (nombre, autor) for nombre, autor in creditos
            if autor.strip().lower().startswith("student ")
        ]
        assert autores_de_relleno == [], (
            f"quedan créditos de relleno: {autores_de_relleno}"
        )

    def test_hay_un_credito_por_cada_stage_order(self, _video) -> None:
        from src.engine.core.stage_registry import STAGE_ORDER
        from src.engine.scenes.end_credits_scene import _creditos_por_escenario

        assert len(_creditos_por_escenario()) == len(STAGE_ORDER)

    def test_los_autores_de_estudiante_conocidos_aparecen(self, _video) -> None:
        """Verificado contra el `.tmx` real, no inventado: estos cinco
        nombres están escritos hoy en `assets/maps/*/*.tmx`."""
        from src.engine.scenes.end_credits_scene import _creditos_por_escenario

        autores = {autor for _, autor in _creditos_por_escenario()}
        esperados = {
            "César Ubáu Calvo", "Fabrizio E", "Jose Pablo Monestel Cruz",
            "Saul", "Yariel",
        }
        faltan = esperados - autores
        assert faltan == set(), f"autores reales que no aparecen: {faltan}"

    def test_el_equipo_docente_no_se_confunde_con_un_estudiante(self, _video) -> None:
        from src.engine.scenes.end_credits_scene import (
            _AUTOR_DOCENTE,
            _creditos_por_escenario,
        )

        for _, autor in _creditos_por_escenario():
            if "docente" in autor.lower() or "legacy" in autor.lower():
                assert autor in _AUTOR_DOCENTE, (
                    f"variante de 'equipo docente' no reconocida: {autor!r} — "
                    f"aparecería listada como si fuera un estudiante"
                )


class TestLaPantallaDeCreditosSeArmaConDatosReales:
    def test_las_lineas_de_estudiante_llevan_el_autor_real(self, _video) -> None:
        from src.engine.scenes.end_credits_scene import EndCreditsScene

        lineas = [t for t, _ in EndCreditsScene._armar_lineas()]
        texto = "\n".join(lineas)
        assert "Fabrizio E" in texto
        assert "Yariel" in texto
        assert "Student A" not in texto and "Student B" not in texto

    def test_no_hay_lineas_vacias_de_autor(self, _video) -> None:
        """Un escenario sin `author` en su TMX cae al respaldo del
        equipo docente, no a una línea "None: Nivel X"."""
        from src.engine.scenes.end_credits_scene import EndCreditsScene

        for texto, _ in EndCreditsScene._armar_lineas():
            assert "None:" not in texto
            assert not texto.strip().endswith(": ")

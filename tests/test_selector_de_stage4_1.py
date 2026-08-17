"""AUD-518 — el sorteo entre variantes de 4-1 (cementerio, y más adelante
acuático/aéreo). Todas las pruebas de selección usan un catálogo de
mentira: no dependen de que 4.1b/4.1c existan (ver `docstring` de
`src/stages/stage4_1/selector.py`).
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from src.engine.core import azar
from src.engine.core.save_data import SaveData
from src.engine.core.save_manager import SaveManager
from src.stages.stage4_1 import selector


@pytest.fixture
def gestor(tmp_path: Path) -> SaveManager:
    sm = SaveManager()
    sm.SAVES_DIR = tmp_path / "saves"
    sm.SAVES_DIR.mkdir(parents=True, exist_ok=True)
    return sm


class _ContextoDeMentira:
    """Lo único que `crear_stage4_1` toca de `GameContext` es
    `.save_manager` — no hace falta un contexto real ni pygame."""

    def __init__(self, save_manager: SaveManager) -> None:
        self.save_manager = save_manager


class _EscenaDeMentira:
    """Reemplaza a `Stage4_1`/`Stage4_1B`/`Stage4_1C` en las pruebas de
    selección: sólo hace falta que acepte `(context)`, para poder
    comprobar cuál se eligió sin construir una escena de pygame de
    verdad. `VARIANTES_DISPONIBLES` guarda rutas punteadas, así que las
    variantes de mentira tienen que ser importables por nombre —de ahí
    que vivan a nivel de módulo y no dentro de una función o clase."""

    def __init__(self, context: object) -> None:
        self.context = context


class _OtraEscenaDeMentira(_EscenaDeMentira):
    """Una segunda clase distinta, para las pruebas que necesitan más de
    una variante entre la que elegir."""


class TestElegirVariante:
    def test_una_sola_opcion_siempre_la_misma(self) -> None:
        assert selector.elegir_variante({"unica": "algo"}) == "unica"

    def test_catalogo_vacio_cae_al_por_defecto(self) -> None:
        assert selector.elegir_variante({}) == selector.VARIANTE_POR_DEFECTO

    def test_la_variante_por_defecto_esta_en_el_catalogo_real(self) -> None:
        """Si el catálogo real alguna vez se queda vacío por error, el
        respaldo tiene que ser una clave que exista — si no, `crear_stage4_1`
        revienta con `KeyError` en vez de degradar con gracia."""
        assert selector.VARIANTE_POR_DEFECTO in selector.VARIANTES_DISPONIBLES

    def test_es_reproducible_con_la_misma_semilla(self) -> None:
        catalogo = {"a": "x", "b": "y", "c": "z"}
        azar.sembrar(12345)
        primera = selector.elegir_variante(catalogo)
        azar.sembrar(12345)
        segunda = selector.elegir_variante(catalogo)
        assert primera == segunda

    def test_elige_entre_las_disponibles_no_otra_cosa(self) -> None:
        catalogo = {"a": "x", "b": "y"}
        for _ in range(20):
            assert selector.elegir_variante(catalogo) in catalogo


class TestCrearStage4_1:
    def test_sin_partida_activa_construye_igual_sin_reventar(self, gestor: SaveManager) -> None:
        """`--stage stage4_1` para probar, o cualquier arranque sin save:
        no hay dónde persistir, así que se juega la variante elegida sin
        guardarla (ver docstring de `_persistir_variante`)."""
        ctx = _ContextoDeMentira(gestor)
        original = dict(selector.VARIANTES_DISPONIBLES)
        selector.VARIANTES_DISPONIBLES.clear()
        selector.VARIANTES_DISPONIBLES["sola"] = f"{__name__}._EscenaDeMentira"
        try:
            escena = selector.crear_stage4_1(ctx)  # type: ignore[arg-type]
        finally:
            selector.VARIANTES_DISPONIBLES.clear()
            selector.VARIANTES_DISPONIBLES.update(original)
        assert isinstance(escena, _EscenaDeMentira)
        # No se creó ningún fichero: sin partida no hay dónde guardar.
        assert list(gestor.SAVES_DIR.glob("slot_*.json")) == []

    def test_primera_entrada_sortea_y_persiste(self, gestor: SaveManager) -> None:
        gestor.save(1, SaveData(slot_id=1, stage_id="stage3_4_boss_gavilan"))
        gestor.ranura_activa = 1
        ctx = _ContextoDeMentira(gestor)

        original = dict(selector.VARIANTES_DISPONIBLES)
        selector.VARIANTES_DISPONIBLES.clear()
        selector.VARIANTES_DISPONIBLES["sola"] = f"{__name__}._EscenaDeMentira"
        try:
            selector.crear_stage4_1(ctx)  # type: ignore[arg-type]
            guardado = gestor.load(1)
        finally:
            selector.VARIANTES_DISPONIBLES.clear()
            selector.VARIANTES_DISPONIBLES.update(original)

        assert guardado is not None
        assert guardado.stage4_1_variante == "sola"
        # El resto del progreso no se tocó (read-modify-write, no un
        # `SaveData()` nuevo encima).
        assert guardado.stage_id == "stage3_4_boss_gavilan"

    def test_segunda_entrada_no_vuelve_a_sortear(self, gestor: SaveManager, monkeypatch: pytest.MonkeyPatch) -> None:
        """Morir y reaparecer en un checkpoint no debe cambiar la
        variante — la decisión confirmada con el dueño (2026-08-17): un
        sorteo por partida, no por intento."""
        gestor.save(1, SaveData(slot_id=1))
        gestor.ranura_activa = 1
        ctx = _ContextoDeMentira(gestor)

        original = dict(selector.VARIANTES_DISPONIBLES)
        selector.VARIANTES_DISPONIBLES.clear()
        selector.VARIANTES_DISPONIBLES["a"] = f"{__name__}._EscenaDeMentira"
        selector.VARIANTES_DISPONIBLES["b"] = f"{__name__}._OtraEscenaDeMentira"
        try:
            selector.crear_stage4_1(ctx)  # type: ignore[arg-type]
            variante_primera_vez = gestor.load(1).stage4_1_variante  # type: ignore[union-attr]

            llamadas = []
            original_elegir = selector.elegir_variante

            def _elegir_espia(disponibles=None):
                llamadas.append(1)
                return original_elegir(disponibles)

            monkeypatch.setattr(selector, "elegir_variante", _elegir_espia)
            selector.crear_stage4_1(ctx)  # type: ignore[arg-type]
            variante_segunda_vez = gestor.load(1).stage4_1_variante  # type: ignore[union-attr]
        finally:
            selector.VARIANTES_DISPONIBLES.clear()
            selector.VARIANTES_DISPONIBLES.update(original)

        assert variante_primera_vez == variante_segunda_vez
        assert llamadas == [], "no debía volver a sortear en la segunda entrada"

    def test_variante_guardada_que_ya_no_existe_vuelve_a_sortear(self, gestor: SaveManager) -> None:
        """Una variante retirada entre versiones (GAP futuro) no debe
        romper la carga: se sortea de nuevo entre las que sí existen."""
        gestor.save(1, SaveData(slot_id=1, stage4_1_variante="variante_retirada"))
        gestor.ranura_activa = 1
        ctx = _ContextoDeMentira(gestor)

        original = dict(selector.VARIANTES_DISPONIBLES)
        selector.VARIANTES_DISPONIBLES.clear()
        selector.VARIANTES_DISPONIBLES["sola"] = f"{__name__}._EscenaDeMentira"
        try:
            escena = selector.crear_stage4_1(ctx)  # type: ignore[arg-type]
            guardado = gestor.load(1)
        finally:
            selector.VARIANTES_DISPONIBLES.clear()
            selector.VARIANTES_DISPONIBLES.update(original)

        assert isinstance(escena, _EscenaDeMentira)
        assert guardado is not None
        assert guardado.stage4_1_variante == "sola"


class TestElRegistroUsaLaFabrica:
    def test_el_slot_stage4_1_resuelve_a_la_fabrica(self) -> None:
        from src.engine.core.stage_registry import STAGE_ORDER, discover_stages

        stages = discover_stages()
        indice = STAGE_ORDER.index("stage4_1")
        assert stages[indice] is selector.crear_stage4_1

    def test_la_fabrica_expone_stage_id_y_stage_name(self) -> None:
        """`world_map_scene.py::construir_nodos` los lee con `getattr()`
        esperando una clase — tienen que existir también en la función."""
        assert selector.crear_stage4_1.STAGE_ID == "stage4_1"
        assert "CEMENTERIO" in selector.crear_stage4_1.STAGE_NAME

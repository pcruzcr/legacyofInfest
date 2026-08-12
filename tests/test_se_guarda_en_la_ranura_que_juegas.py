"""AUD-441 — el autoguardado escribía en la ranura equivocada.

Lo medido
---------
`auto_save` elegía destino con `newest_slot()`: la ranura cuya marca de tiempo
es más reciente. Eso funciona mientras haya una sola partida y deja de
funcionar en cuanto hay dos, que es exactamente lo que SYS-001 viene a montar.

La secuencia que destruye datos:

1. Juegas la ranura 2 hoy. Queda con la marca más reciente.
2. Mañana cargas la ranura 1 y sigues por donde ibas.
3. Tocas un punto de control. `auto_save` busca la más reciente —la 2— y
   escribe ahí el progreso de la 1.

El resultado no es que no se guarde: es que **se guarda encima de otra
partida**. La 2 queda con la posición, la vida y el escenario de la 1.

La causa de fondo
-----------------
Nadie era dueño de la pregunta «¿qué partida se está jugando?». Se deducía
del disco cada vez, y una deducción no es una decisión: en cuanto dos ranuras
existen a la vez, la heurística acierta por casualidad. El `SaveManager` pasa
a recordarlo, y quien carga o crea una partida lo declara.

Se conserva el respaldo a `newest_slot()` cuando nadie lo ha declarado: una
partida arrancada por un camino que todavía no pasa por la pantalla de
ranuras tiene que seguir guardando en algún sitio razonable.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from src.engine.core.save_data import SaveData
from src.engine.core.save_manager import SaveManager


@pytest.fixture
def gestor(tmp_path, monkeypatch):
    """Un `SaveManager` con su propio directorio, para no tocar el del usuario."""
    monkeypatch.setattr(SaveManager, "SAVES_DIR", tmp_path)
    return SaveManager()


def _partida(slot: int, stage: str, marca: str) -> SaveData:
    return SaveData(slot_id=slot, stage_id=stage, timestamp=marca,
                    checkpoint_x=float(slot * 100))


def test_el_autoguardado_va_a_la_ranura_activa(gestor) -> None:
    """El defecto exacto: jugar la 1 escribía en la 2."""
    gestor.save(1, _partida(1, "stage1_1", "2026-01-01T00:00:00+00:00"))
    gestor.save(2, _partida(2, "stage3_3", "2026-06-01T00:00:00+00:00"))
    assert gestor.newest_slot() == 2, "el escenario de partida exige que la 2 sea la reciente"

    gestor.ranura_activa = 1
    gestor.auto_save(
        stage_id="stage1_2", stage_index=3,
        checkpoint_x=777.0, checkpoint_y=0.0, health=4.0, max_health=5.0,
    )

    uno = gestor.load(1)
    dos = gestor.load(2)
    assert uno is not None and dos is not None
    assert uno.stage_id == "stage1_2", "no se guardó en la ranura que se juega"
    assert uno.checkpoint_x == pytest.approx(777.0)
    assert dos.stage_id == "stage3_3", (
        f"la ranura 2 quedó con el progreso de la 1: {dos.stage_id!r}. "
        f"Guardar en una partida ha destruido otra."
    )
    assert dos.checkpoint_x == pytest.approx(200.0)


def test_sin_ranura_declarada_se_conserva_el_comportamiento_anterior(gestor) -> None:
    """El control que evita romper el arranque que todavía no la declara."""
    gestor.save(1, _partida(1, "stage1_1", "2026-01-01T00:00:00+00:00"))
    gestor.save(2, _partida(2, "stage3_3", "2026-06-01T00:00:00+00:00"))

    assert gestor.ranura_activa is None
    gestor.auto_save(
        stage_id="stage4_1", stage_index=9,
        checkpoint_x=1.0, checkpoint_y=0.0, health=5.0, max_health=5.0,
    )

    dos = gestor.load(2)
    assert dos is not None and dos.stage_id == "stage4_1", (
        "sin ranura activa debía seguir escribiendo en la más reciente"
    )


def test_cargar_una_partida_la_declara_activa(gestor) -> None:
    """Quien carga es quien sabe qué se está jugando."""
    gestor.save(3, _partida(3, "stage2_2", "2026-02-02T00:00:00+00:00"))

    gestor.load(3, activar=True)

    assert gestor.ranura_activa == 3


def test_cargar_para_mirar_no_cambia_la_partida_activa(gestor) -> None:
    """La pantalla de ranuras lee las cinco para pintarlas.

    Si leer activara, pintar la lista dejaría como activa la última fila
    dibujada — y el autoguardado siguiente iría ahí. Activar es una decisión
    explícita, no un efecto de mirar.
    """
    gestor.save(1, _partida(1, "stage1_1", "2026-01-01T00:00:00+00:00"))
    gestor.save(2, _partida(2, "stage3_3", "2026-06-01T00:00:00+00:00"))
    gestor.ranura_activa = 1

    gestor.load(2)

    assert gestor.ranura_activa == 1


def test_una_ranura_activa_fuera_de_rango_no_se_acepta(gestor) -> None:
    """Un número imposible tiene que fallar donde se pone, no al guardar."""
    with pytest.raises(ValueError):
        gestor.ranura_activa = 99
    with pytest.raises(ValueError):
        gestor.ranura_activa = 0

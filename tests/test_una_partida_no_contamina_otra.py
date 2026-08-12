"""AUD-438 — cargar una ranura arrastraba el progreso de la anterior.

Lo medido
---------
Se ensucia el estado como si se hubiera jugado la ranura 1 (monedas, un
objeto), se carga la ranura 2 —vacía— y el inventario sigue siendo el de la 1.

La causa está en `aplicar_estado_de`: restaura **sólo si hay algo que
restaurar**::

    if data.inventory_items or data.inventory_equipped:
        get_inventory().restaurar(...)

Esa guarda existe por un motivo bueno y documentado en AUD-292: una partida de
la versión 2 llega con esos campos vacíos porque entonces no se guardaban, y
vaciarle la cartera a quien carga una partida antigua sería cobrarle la
migración. El problema es que «vacío porque es antiguo» y «vacío porque está
recién empezado» se escriben igual, y la guarda no puede distinguirlos.

Sí puede distinguirlos el número de versión, que la partida ya trae. De la
versión actual hacia arriba, vacío significa vacío: se aplica tal cual. Por
debajo, se conserva la indulgencia de AUD-292.

Los logros iban aparte y no se tocaban en absoluto: `AchievementSystem`
persiste en su propio fichero global, fuera del sistema de partidas, así que
lo desbloqueado en una ranura aparecía desbloqueado en todas.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core.save_data import SAVE_VERSION, SaveData


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((64, 64))
    yield


@pytest.fixture
def inventario(_video):
    from src.engine.core.inventory import get_inventory

    inv = get_inventory()
    inv.restaurar({}, {})
    return inv


def _partida_de_la_ranura_1() -> SaveData:
    return SaveData(
        slot_id=1, stage_id="stage1_1",
        inventory_items={"coin": 250, "hollow_eye": 1},
        inventory_equipped={},
    )


def _partida_nueva_en_la_ranura_2() -> SaveData:
    """Una ranura recién creada: sin objetos, sin monedas, versión actual."""
    return SaveData(slot_id=2, stage_id="stage0")


def test_cargar_una_partida_nueva_no_hereda_el_inventario_de_la_anterior(
    inventario,
) -> None:
    """El defecto exacto que se midió."""
    from src.engine.core.save_manager import aplicar_estado_de

    aplicar_estado_de(_partida_de_la_ranura_1())
    assert inventario.coins == 250, "no se pudo montar el escenario de partida"

    aplicar_estado_de(_partida_nueva_en_la_ranura_2())

    assert inventario.coins == 0, (
        f"la ranura 2 arranca con {inventario.coins} monedas de la ranura 1"
    )
    assert not inventario.has("hollow_eye"), (
        "la ranura 2 hereda un objeto que se consiguió en la ranura 1"
    )


def test_una_partida_antigua_conserva_la_indulgencia_de_aud_292(
    inventario,
) -> None:
    """El control que impide que el arreglo cobre la migración.

    Sin esta prueba, la corrección obvia —quitar la guarda— vaciaría el
    inventario de cualquiera que cargue una partida de la versión 2, que es
    justo lo que AUD-292 decidió no hacer.
    """
    from src.engine.core.save_manager import aplicar_estado_de

    aplicar_estado_de(_partida_de_la_ranura_1())
    # Por `from_dict`, que es como llega una partida de verdad: pasa por
    # `migrate()`, y ahí está el matiz que casi se me escapa — la migración
    # reescribe `version` a la actual, así que la indulgencia no puede
    # apoyarse en ella. Se apoya en `version_original`, que la migración
    # anota antes de tocar nada.
    antigua = SaveData.from_dict({"version": 2, "stage_id": "stage1_1"})
    assert antigua.version_original == 2
    assert antigua.version == SAVE_VERSION, "migrate() sube la versión, como debe"

    aplicar_estado_de(antigua)

    assert inventario.coins == 250, (
        "se le vació la cartera a una partida de la versión 2, que no pudo "
        "guardar su inventario porque entonces no se guardaba"
    )


def test_la_version_actual_con_inventario_vacio_significa_vacio(
    inventario,
) -> None:
    """La distinción que la guarda anterior no podía hacer."""
    from src.engine.core.save_manager import aplicar_estado_de

    aplicar_estado_de(_partida_de_la_ranura_1())
    vacia = SaveData(slot_id=4)
    assert vacia.version == SAVE_VERSION

    aplicar_estado_de(vacia)
    assert inventario.coins == 0
    assert dict(inventario.all_items()) == {}


def test_los_logros_tambien_se_reinician_al_cambiar_de_ranura(_video) -> None:
    """Iban por libre, en un fichero global fuera del sistema de partidas."""
    from src.engine.core.achievements import AchievementSystem
    from src.engine.core.save_manager import aplicar_estado_de

    logros = AchievementSystem.get_instance()
    logros.progress("first_blood")

    desbloqueados = lambda: [          # noqa: E731
        d.id for d, p in AchievementSystem.get_instance().get_all_achievements()
        if getattr(p, "unlocked", False)
    ]
    assert desbloqueados(), "no se pudo desbloquear ningún logro de partida"

    aplicar_estado_de(_partida_nueva_en_la_ranura_2())

    assert not desbloqueados(), (
        f"la ranura 2 arranca con {desbloqueados()} desbloqueado(s) en la 1"
    )


def test_el_progreso_de_la_ranura_se_restaura_de_verdad(inventario) -> None:
    """Reiniciar sin rehidratar convertiría el defecto en pérdida de progreso.

    Es el fallo que un arreglo apresurado introduce: dejar todo a cero al
    cargar y no volver a poner lo que la partida guardaba.
    """
    from src.engine.core.save_manager import aplicar_estado_de

    aplicar_estado_de(_partida_nueva_en_la_ranura_2())
    aplicar_estado_de(_partida_de_la_ranura_1())

    assert inventario.coins == 250
    assert inventario.has("hollow_eye")

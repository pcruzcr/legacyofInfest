"""AUD-545 — una notificación de recogida sobrevivía a la prueba que la generó.

El defecto
==========
`Inventory` es singleton de **proceso** (`_instance` de clase), no de
partida: `collect()` encola una notificación («ITEM: …», tres segundos de
temporizador) en `_collect_notifications`/`_current_notify`. `conftest.py`
resetea `AssetLoader`, `StageLoader`, `AchievementSystem` y las preferencias
de usuario entre pruebas — pero no `Inventory` —, así que cualquier prueba
que llamara a `collect()` dejaba esa notificación pendiente para la
siguiente prueba del proceso que construyera una escena y la dibujara.

Cómo se encontró
=================
`test_reported_ui_bugs.py::test_el_hud_conserva_su_brillo` (AUD-090: el HUD
no debe perder brillo bajo la luz del mundo) fallaba **sólo** dentro de la
suite completa, con la misma razón de brillo exacta en ejecuciones
separadas (0,7463648122122662). Esa repetibilidad bit a bit —no un número
distinto cada vez, que es la firma de una máquina cargada— apuntaba a
estado compartido, no a inestabilidad. Comparando pixel a pixel el HUD
aislado contra el compuesto completo, la diferencia no estaba en la luz ni
en las partículas —idénticas en ambas ejecuciones— sino en un aviso rojo de
«ITEM: Vasija de corazón» dibujado sobre el reloj del HUD por
`Inventory.draw_notifications`, ajeno a esa prueba: lo dejó recogiendo algo
una prueba muy anterior en el mismo proceso.

Esta prueba fija el contrato con dos funciones en orden de declaración —el
que pytest usa por defecto y del que ya depende el resto de la suite (no hay
`pytest-randomly` ni reordenado configurado)—: la primera ensucia el
inventario a propósito, la segunda comprueba que no hereda nada.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from src.engine.core.inventory import get_inventory


def test_1_recoger_algo_deja_una_notificacion_en_cola():
    """Ensucia el inventario a propósito — la prueba siguiente comprueba que
    no arrastra nada de esto."""
    inv = get_inventory()
    inv.collect("heart_vessel")
    assert inv._collect_notifications or inv._current_notify is not None, (
        "la propia recogida no dejó nada en cola: esta prueba no está "
        "probando lo que dice probar"
    )


def test_2_la_siguiente_prueba_no_hereda_la_notificacion_ajena():
    """AUD-545 — sin `Inventory._reset_instance()` en `conftest.py`, aquí
    `_collect_notifications`/`_current_notify` seguirían con lo que dejó
    `test_1_recoger_algo_deja_una_notificacion_en_cola`: `Inventory` es
    singleton de proceso y nada lo reseteaba entre pruebas.
    """
    inv = get_inventory()
    assert inv._collect_notifications == [], (
        "una notificación de una prueba anterior sigue en cola: el "
        "singleton de Inventory no se resetea entre pruebas"
    )
    assert inv._current_notify is None, (
        "una notificación de una prueba anterior sigue visible: el "
        "singleton de Inventory no se resetea entre pruebas"
    )

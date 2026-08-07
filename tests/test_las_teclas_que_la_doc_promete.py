"""
Module: test_las_teclas_que_la_doc_promete
System: tests
Academic Unit: N/A

AUD-310 — seis documentos decían que la consola de depuración se abre con F3.

Se abre con **F11**. `debug_overlay.TECLA_CONSOLA` es `pygame.K_F11`, y F3 está
ocupada por `Action.LEARN_PHYSICS` en el mapa de acciones.

Por qué estaba mal en seis sitios a la vez
===========================================
Porque era verdad cuando se escribió. AUD-283 movió la consola a F11 —F3 ya
tenía dueño— y arregló el código; los dos README, el manual de usuario, la
arquitectura, los contratos de API y las escenas académicas siguieron diciendo
F3. El propio reporte 87 lo dejó anotado («es **F11**, no F3») y aun así los
otros seis documentos no se enteraron.

Es el modo de fallo más caro de este repositorio y el más difícil de ver: nada
falla, nada avisa, y el estudiante pulsa una tecla que no hace nada y concluye
que la función no existe.

Qué fija esta prueba
====================
Que la tecla que documentan los ficheros que el usuario lee sea la que el
código usa de verdad. Se lee del código, no se escribe a mano aquí: si mañana
la consola se mueve a F12, esta prueba señala los seis documentos que hay que
tocar, uno por uno y con su nombre.
"""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

RAIZ = Path(__file__).resolve().parent.parent

#: Los ficheros que un humano lee para saber qué tecla pulsar.
DOCUMENTOS = (
    "README.md",
    "README.en.md",
    "docs/35_USER_MANUAL.md",
    "docs/03_ARCHITECTURE.md",
    "docs/22_API_CONTRACTS.md",
    "docs/15_ACADEMIC_DEMO_SCENES.md",
)


@pytest.fixture(scope="module")
def tecla_real() -> str:
    """El nombre de la tecla, sacado del código."""
    from src.engine.scenes.debug_overlay import TECLA_CONSOLA

    return pygame.key.name(TECLA_CONSOLA).upper()


def test_la_consola_no_esta_en_una_tecla_ya_ocupada(tecla_real: str) -> None:
    """La causa de AUD-283: la consola estaba asignada a una tecla con dueño,
    así que no la abría nadie."""
    from src.engine.input.action_map import DEFAULT_KEY_BINDINGS
    from src.engine.scenes.debug_overlay import TECLA_CONSOLA

    ocupadas = {t for teclas in DEFAULT_KEY_BINDINGS.values() for t in teclas}

    assert TECLA_CONSOLA not in ocupadas, (
        f"la consola de depuración usa {tecla_real}, que ya está asignada a "
        f"una acción del juego: volvería a no abrirse"
    )


@pytest.mark.parametrize("ruta", DOCUMENTOS)
def test_ningun_documento_anuncia_otra_tecla(ruta: str, tecla_real: str) -> None:
    """Busca líneas que hablen de la consola y prometan una tecla distinta."""
    texto = (RAIZ / ruta).read_text(encoding="utf-8", errors="replace")

    culpables = []
    for numero, linea in enumerate(texto.splitlines(), 1):
        bajo = linea.lower()
        # Cualquier línea que hable de depuración, no sólo las que usan la
        # frase completa: la primera versión de esta prueba buscaba «debug
        # console» y «consola de depuración», y se le escapó un titular que
        # decía sólo «Debug (F3)» — comprobado mutando el manual.
        if "debug" not in bajo and "depurac" not in bajo:
            continue
        # ¿Menciona alguna tecla de función que no sea la buena?
        otras = {f"F{n}" for n in range(1, 13)} - {tecla_real}
        mencionadas = {t for t in otras
                       if f"{t} " in linea or f"{t})" in linea
                       or f"`{t}`" in linea or f"{t}-" in linea or f"{t}:" in linea}
        if mencionadas and tecla_real not in linea:
            culpables.append(f"    {ruta}:{numero}  {linea.strip()[:110]}")

    assert not culpables, (
        f"la consola de depuración se abre con {tecla_real}, y estas líneas "
        f"anuncian otra tecla:\n" + "\n".join(culpables)
    )

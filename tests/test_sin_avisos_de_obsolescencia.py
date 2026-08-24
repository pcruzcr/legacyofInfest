"""AUD-357: la suite dejaba 20 avisos de obsolescencia por ejecución.

El hallazgo
===========

Cada `pytest tests/` terminaba con este bloque::

    tests/test_aberracion_cromatica.py: 14 warnings
    tests/test_refraccion_bajo_el_agua.py: 6 warnings
      gl_pipeline.py:552: DeprecationWarning: pygame.image.tostring
      deprecated since 2.3.0

Veinte avisos en verde son peores que uno en rojo. Un resumen de avisos que
sale siempre y siempre dice lo mismo enseña a no leerlo, y el día que aparezca
el aviso número veintiuno —el que sí importa— va a pasar entre estos veinte
sin que nadie lo vea. Es la misma razón por la que AUD-106 mantiene el lint de
las entregas fuera del CI: un canal ruidoso deja de ser un canal.

`pygame.image.tostring` / `fromstring` están obsoletas desde pygame 2.3 en
favor de `tobytes` / `frombytes` (mismo argumento, mismo retorno, sólo cambia
el nombre: lo que devolvía ya eran `bytes`, no `str`, desde Python 3). El
proyecto declara `pygame-ce>=2.5` en `pyproject.toml` y en `requirements.txt`,
así que `tobytes` existe en cualquier instalación soportada y no hace falta
ningún camino de compatibilidad.

Lo que fija este test
=====================

1. Que la subida de una superficie a la tarjeta —el camino lento, el que usa
   la conversión— **no emita ningún `DeprecationWarning`**. Es la prueba de
   comportamiento: se mide lo que hace la función, no lo que dice el fichero.
2. Que no vuelva a colarse una llamada a la API obsoleta en `src/` ni en
   `scripts/`. Es la prueba de regresión: sin ella, el aviso vuelve con el
   siguiente que copie una línea de un tutorial viejo.

La segunda mira **llamadas**, no menciones: varios docstrings y comentarios
del repositorio citan `tostring` a propósito, contando la historia de la
medición de AUD-229 (3,458 ms), y un guardián que los marcara obligaría a
falsear la historia para callarlo.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import ast
import pathlib
import warnings
from unittest.mock import MagicMock

import pygame

from src.engine.render.gl_pipeline import GLRenderer

RAIZ = pathlib.Path(__file__).resolve().parent.parent

#: Las dos funciones obsoletas y su reemplazo, para que el mensaje del fallo
#: diga qué poner en vez de sólo qué quitar.
OBSOLETAS = {"tostring": "tobytes", "fromstring": "frombytes"}


class TestLaSubidaNoAvisa:

    def test_subir_una_superficie_no_emite_deprecation(self) -> None:
        """El camino lento de `_subir`, que es el que convertía.

        Sin contexto GL real: `ctx` es un doble. Lo que se ejercita es la
        conversión de la superficie, que es donde vivía la llamada obsoleta,
        y ésa no necesita tarjeta.
        """
        renderer = GLRenderer()
        renderer.ctx = MagicMock()
        # `_swizzle` a None fuerza el camino de conversión (el rápido escribe
        # el `memoryview` tal cual y nunca tocó la API obsoleta).
        renderer._swizzle = None
        superficie = pygame.Surface((8, 8), pygame.SRCALPHA)

        with warnings.catch_warnings(record=True) as capturados:
            warnings.simplefilter("always")
            renderer._subir(superficie, None)

        deprecaciones = [
            str(w.message) for w in capturados
            if issubclass(w.category, DeprecationWarning)
        ]
        assert not deprecaciones, deprecaciones


class TestNadieVuelveALlamarla:

    @staticmethod
    def _llamadas_obsoletas(ruta: pathlib.Path) -> list[str]:
        """Nombres obsoletos **llamados** en el fichero. Comentarios no cuentan."""
        try:
            arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            return []
        encontradas = []
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call):
                continue
            f = nodo.func
            if isinstance(f, ast.Attribute) and f.attr in OBSOLETAS:
                # `pygame.image.tostring(...)`, no `unittest.mock.tostring`.
                origen = ast.unparse(f)
                if "image" in origen:
                    encontradas.append(f"{ruta.name}:{nodo.lineno} {origen}")
        return encontradas

    def test_ni_src_ni_scripts_llaman_a_la_api_obsoleta(self) -> None:
        objetivo = [
            *(RAIZ / "src" / "engine").rglob("*.py"),
            *(RAIZ / "src" / "framework").rglob("*.py"),
            *(RAIZ / "scripts").rglob("*.py"),
            *(RAIZ / "tools").rglob("*.py"),
        ]
        hallazgos = [h for ruta in objetivo for h in self._llamadas_obsoletas(ruta)]
        assert not hallazgos, (
            "API obsoleta de pygame en uso; el reemplazo es "
            f"{OBSOLETAS}:\n" + "\n".join(hallazgos)
        )

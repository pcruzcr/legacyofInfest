"""AUD-447 — la pantalla de Opciones estaba en inglés.

«MUSIC VOLUME», «SFX VOLUME», «DIFFICULTY», «COLORBLIND MODE», «SUBTITLES
(audio captions)», «KEY BINDINGS». Y dos filas a medias, «IDIOMA / LANGUAGE»
y «ACCESIBILIDAD / ACCESSIBILITY», que son de cuando el proyecto era bilingüe
— una política que AUD-428 retiró: el español es la lengua del proyecto y no
hay parejas que mantener.

Es la misma clase de defecto que AUD-440 encontró en el catálogo de objetos:
el marco de la pantalla en español y el contenido en inglés. Y se le escapa
al mismo guardián, `check_translations.py`, que mira los catálogos de
`locale/` y no los literales que una escena pasa a `pygame_gui`.

Qué comprueba esto
------------------
Lo mismo que el guardián del catálogo de objetos, y con el mismo límite
declarado: no demuestra que el castellano esté bien escrito, detecta las
palabras que sólo aparecen si alguien dejó el texto en inglés. Es el caso que
de verdad ocurre — copiar la fila de al lado al añadir un ajuste.
"""
from __future__ import annotations

import os
import re

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pathlib

import pytest

RUTA = (pathlib.Path(__file__).resolve().parent.parent
        / "src" / "engine" / "scenes" / "options_scene.py")

#: Palabras que no existen en español y que delatan un rótulo sin traducir.
_DELATORES = (
    "volume", "difficulty", "colorblind", "subtitles", "captions",
    "key bindings", "language", "accessibility", "back", "apply",
    "music", "text size", "reduced motion",
)


def _rotulos() -> list[str]:
    """Los textos que la pantalla dibuja, leídos del fuente.

    Se leen del fichero y no construyendo la escena porque `pygame_gui`
    necesita un gestor vivo y un tema cargado: para comprobar que un rótulo
    está en español no hace falta levantar media interfaz.
    """
    fuente = RUTA.read_text(encoding="utf-8")
    encontrados: list[str] = []
    # `self._fila(y, "TEXTO", ...)` y `text="TEXTO"`.
    encontrados += re.findall(r'_fila\(\s*[^,]+,\s*"([^"]+)"', fuente)
    encontrados += re.findall(r'text="([^"]+)"', fuente)
    encontrados += re.findall(r'titulo = "([^"]+)"', fuente)
    return encontrados


def test_la_pantalla_declara_rotulos() -> None:
    """Sin esto, un cambio de forma dejaría la prueba comprobando una lista
    vacía y pasando siempre."""
    assert len(_rotulos()) >= 8, f"sólo se encontraron {len(_rotulos())} rótulos"


@pytest.mark.parametrize("rotulo", _rotulos())
def test_el_rotulo_esta_en_espanol(rotulo: str) -> None:
    bajo = rotulo.lower()
    encontrados = [p for p in _DELATORES if re.search(rf"\b{re.escape(p)}\b", bajo)]
    assert not encontrados, (
        f"el rótulo {rotulo!r} está en inglés ({', '.join(encontrados)}). "
        f"Lo lee el jugador cada vez que abre Opciones."
    )


def test_no_quedan_filas_bilingues() -> None:
    """AUD-428 retiró la política bilingüe: no hay parejas que mantener.

    «IDIOMA / LANGUAGE» era de cuando sí las había. Dejarlas es enseñar dos
    idiomas a quien eligió uno, y ocupar el doble de ancho para decir lo mismo.
    """
    con_barra = [r for r in _rotulos() if "/" in r and len(r.split("/")) == 2]
    assert not con_barra, f"rótulos a medio traducir: {con_barra}"

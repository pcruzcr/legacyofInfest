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
    """Los textos que la pantalla enseña: etiquetas y valores.

    AUD-452 — se leen de la tabla de ajustes y no del fuente con expresiones
    regulares. Aquellas buscaban `_fila(...)` y `text="..."`, que eran la
    forma que tenía la pantalla cuando la dibujaba `pygame_gui`; al migrarla
    al kit del juego dejaron de encontrar nada y la prueba habría pasado en
    verde sobre una lista vacía.

    Preguntar por la estructura en vez de por el texto del fichero también
    cubre más: ahora entran los **valores** —«SÍ», «FÁCIL», «NINGUNO»—, que
    son la mitad de lo que se lee en esta pantalla y que las expresiones
    regulares no veían.
    """
    from src.engine.scenes.options_scene import OptionsScene

    # La pantalla sólo necesita el contexto para navegar; construirla para
    # leer sus rótulos no requiere ni gestor de escenas ni audio.
    escena = OptionsScene(None)          # type: ignore[arg-type]
    textos: list[str] = ["OPCIONES"]
    for ajuste in escena.ajustes:
        textos.append(ajuste.etiqueta)
        textos.extend(ajuste.mostrar(valor) for valor in ajuste.valores)
    textos += [str(item.label) for item in escena._menu.items]
    return textos


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

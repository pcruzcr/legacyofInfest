"""AUD-589 — los PNG de assets no llevan perfiles de color incrustados.

El problema que esto cubre
==========================
Quince tilesets del 4-1 (los que llegó el arte de autor en AUD-546) traían un
chunk `iCCP` con el perfil sRGB roto que libpng lleva años reconociendo. Cada
vez que algo los cargaba —`validate_assets`, `grade_stage`, el juego— la
consola escupía:

    libpng warning: iCCP: known incorrect sRGB profile

Un aviso por carga parece ruido, pero en este repositorio la consola es
contrato: los validadores dicen en voz alta lo que ven, y un aviso constante
entrena a quien lee a ignorar la salida (el mismo efecto que AUD-016 cazó con
los `filterwarnings`).

Por qué se quita el chunk y no se «arregla» el perfil
=====================================================
El motor no gestiona color: SDL_image decodifica píxeles y el perfil nunca se
usa para nada. Un PNG sin `iCCP` es sRGB por definición de la especificación,
as que quitarlo no cambia ni un píxel — sólo deja de avisar. Recalibrar el
perfil sería tocar arte de autor sin necesidad.

La prueba recorre los PNG con un parser de chunks mínimo (cabecera + longitud
+ tipo), sin dependencias: si mañana un generador o una herramienta externa
vuelve a meter un perfil, se sabrá aquí y no por la consola.
"""
from __future__ import annotations

import struct
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"


def _chunks(datos: bytes) -> list[str]:
    """Tipos de chunk de un PNG, en orden. Devuelve [] si no es un PNG."""
    if datos[:8] != b"\x89PNG\r\n\x1a\n":
        return []
    tipos: list[str] = []
    pos = 8
    while pos + 8 <= len(datos):
        longitud = struct.unpack(">I", datos[pos:pos + 4])[0]
        tipos.append(datos[pos + 4:pos + 8].decode("latin-1"))
        pos += 12 + longitud
    return tipos


def test_ningun_png_de_assets_lleva_iccp() -> None:
    con_perfil: list[str] = []
    for png in sorted(ASSETS.rglob("*.png")):
        if "iCCP" in _chunks(png.read_bytes()):
            con_perfil.append(png.relative_to(RAIZ).as_posix())
    assert not con_perfil, (
        "estos PNG llevan un perfil de color incrustado (iCCP): el motor no "
        "gestiona color y libpng avisa en cada carga. Quita el chunk — no "
        "cambia un píxel:\n" + "\n".join(con_perfil)
    )

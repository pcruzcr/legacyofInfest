"""
Module: i18n
System: engine.core
Academic Unit: N/A

Traducción de la interfaz. Español por defecto.

F3.1 — por qué no se usa `gettext`
----------------------------------
La biblioteca estándar trae `gettext`, y es lo primero que uno considera. Se
descartó por tres razones concretas, no por gusto:

1. **El flujo de trabajo exige herramientas externas.** `gettext` se apoya en
   archivos `.po` compilados a `.mo` con `msgfmt`. Añadir a los requisitos de
   un curso «instala las herramientas GNU gettext» es una barrera real, y en
   Windows —donde están la mayoría de los estudiantes— no es trivial.

2. **Los `.mo` son binarios.** Un catálogo compilado no se revisa en una
   petición de cambios ni se resuelve un conflicto de fusión a mano. En un
   repositorio donde treinta estudiantes tocan texto, eso importa.

3. **El caso de uso es diminuto.** Dos idiomas y unos cientos de cadenas. La
   maquinaria de `gettext` —dominios, `bindtextdomain`, resolución por
   `LC_MESSAGES`— resuelve problemas que este proyecto no tiene.

Lo que hay aquí es un diccionario en un `.json` por idioma y una función `_`.
Se lee, se edita en cualquier sitio y se revisa en texto plano.

Cómo se usa
-----------
::

    from src.engine.core.i18n import _

    titulo = _("INVENTARIO")

La clave **es el literal que hay en el código**, no un identificador
abstracto: `_("INVENTARIO")`, no `_("menu.inventory.title")`. Así una cadena
sin traducir sigue mostrando algo legible en vez de un identificador o un
hueco, y el `grep` para encontrar dónde sale un texto sigue funcionando.

Los dos idiomas tienen catálogo, y ésa es una decisión que conviene explicar:
lo natural sería que el idioma de las claves no necesitara ninguno. Pero el
código heredado mezcla literales en español (`"INVENTARIO"`, `"Objetos
recogidos"`) con literales en inglés (`"COLLISION LAB"`, `"GAME OVER"`), y
renombrar los segundos exigiría tocar treinta archivos de escena de golpe.
Con catálogo para el español, un literal inglés se traduce sin mover el
código, y uno ya español simplemente no tiene entrada y pasa tal cual.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

#: Idiomas con catálogo. El primero es el de las claves.
IDIOMAS: tuple[str, ...] = ("es", "en")
IDIOMA_POR_DEFECTO = "es"

_DIRECTORIO = Path(__file__).resolve().parent.parent.parent.parent / "locale"

_catalogo: dict[str, str] = {}
_idioma_actual: str = IDIOMA_POR_DEFECTO
_faltantes: set[str] = set()


def idioma_actual() -> str:
    return _idioma_actual


def set_idioma(codigo: str) -> str:
    """Carga el catálogo del idioma pedido. Devuelve el idioma efectivo.

    Un código desconocido no es un error: se avisa y se usa el idioma por
    defecto. Cambiar de idioma nunca debe impedir jugar.
    """
    global _catalogo, _idioma_actual

    codigo = (codigo or "").strip().lower()
    if codigo not in IDIOMAS:
        if codigo:
            logger.warning(
                "i18n: idioma '%s' desconocido. Disponibles: %s",
                codigo, ", ".join(IDIOMAS),
            )
        codigo = IDIOMA_POR_DEFECTO

    _idioma_actual = codigo
    _faltantes.clear()

    ruta = _DIRECTORIO / f"{codigo}.json"
    try:
        _catalogo = json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("i18n: no existe el catálogo %s; se usa español", ruta)
        _catalogo = {}
    except json.JSONDecodeError as e:
        logger.warning("i18n: catálogo %s mal formado (%s); se usa español", ruta, e)
        _catalogo = {}
    return codigo


def _(texto: str) -> str:
    """Traduce una cadena al idioma actual.

    Si no hay traducción se devuelve el original. Es deliberado y es la razón
    de que las claves sean el texto en español: una cadena sin traducir se ve
    en español, que es correcto para este curso, en lugar de mostrar un
    identificador o un hueco.

    Las cadenas sin traducir se anotan para que
    `scripts/check_translations.py` pueda listarlas.
    """
    if not _catalogo:
        return texto
    traducido = _catalogo.get(texto)
    if traducido is None:
        _faltantes.add(texto)
        return texto
    return traducido


def faltantes() -> set[str]:
    """Cadenas que se han pedido y no estaban en el catálogo."""
    return set(_faltantes)


def cargar_del_disco(codigo: str) -> dict[str, str]:
    """Devuelve el catálogo de un idioma sin cambiar el estado global.

    Lo usan las herramientas de verificación; el juego no lo necesita.
    """
    ruta = _DIRECTORIO / f"{codigo}.json"
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

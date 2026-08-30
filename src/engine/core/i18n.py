"""
Module: i18n
System: engine.core
Academic Unit: N/A

Traducción de la interfaz con claves canónicas. Español por defecto.

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

    titulo = _("ui.inventory_title")  # → "INVENTARIO" (es) / "INVENTORY" (en)

La clave es un **identificador canónico** (p.ej. `ui.cancel`, `menu.start`),
no el texto visible. Esto permite:
- Round-trip fiable entre idiomas (AUD-307)
- Cambiar el texto visible sin romper claves
- `grep` fiable para encontrar dónde se usa una cadena

Convención de claves:
- `ui.*` — elementos de interfaz (menús, botones, HUD)
- `ui.nav.*` — navegación y pistas
- `ui.hints.*` — ayudas contextuales
- `ui.vector_lab.*` — laboratorio de vectores
- `ui.color_theory.*` — teoría del color
- `ui.pattern_demo.*` — demo de patrones
- `ui.vision_demo.*` — demo de visión
- `ui.combo.*` — sistema de combos
- `ui.quiz.*` — cuestionarios
- `ui.units.*` — unidades académicas
- `ui.demo_modes.*` — modos de demo
- `ui.color_theory_modes.*` — modos de teoría del color
- `ui.vector_lab.modes.*` — modos del laboratorio de vectores
- etc.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

#: Idiomas con catálogo. El primero es el de las claves (fallback).
IDIOMAS: tuple[str, ...] = ("es", "en")
IDIOMA_POR_DEFECTO = "es"

_DIRECTORIO = Path(__file__).resolve().parent.parent.parent.parent / "locale"

_catalogo: dict[str, str] = {}
_idioma_actual: str = IDIOMA_POR_DEFECTO
_faltantes: set[str] = set()
_candado = threading.RLock()


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

    with _candado:
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


def _(clave: str) -> str:
    """Traduce una clave canónica al idioma actual.

    Si no hay traducción se devuelve la clave. Es deliberado: una clave
    sin traducir se ve como `ui.cancel` en lugar de un hueco, y el
    `scripts/check_translations.py` la listará como faltante.

    La clave **debe ser canónica** (p.ej. `ui.cancel`), no el texto visible.
    """
    with _candado:
        if not _catalogo:
            return clave
        traducido = _catalogo.get(clave)
        if traducido is None:
            _faltantes.add(clave)
            return clave
        return traducido


def faltantes() -> set[str]:
    """Claves que se han pedido y no estaban en el catálogo."""
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


def aplanar_catalogo(catalogo: dict) -> dict[str, str]:
    """Aplana un catálogo anidado a claves planas con notación de punto.

    Ejemplo: {"ui": {"cancel": "Cancelar"}} → {"ui.cancel": "Cancelar"}
    """
    resultado: dict[str, str] = {}

    def _aplanar(obj: dict, prefijo: str = "") -> None:
        for k, v in obj.items():
            clave = f"{prefijo}{k}"
            if isinstance(v, dict):
                _aplanar(v, f"{clave}.")
            else:
                resultado[clave] = v

    _aplanar(catalogo)
    return resultado
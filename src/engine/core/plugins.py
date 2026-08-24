"""
Module: plugins
System: engine.core
Academic Unit: N/A
Description: AUD-296 — extender el motor sin tocar el núcleo.

Qué añade esto sobre el bus de eventos, que es la pregunta justa
================================================================
El bus ya existe y es excelente para **enterarse** de que algo pasó. Lo que no
da es lo otro dos cosas que hacen falta para extender un motor:

* **Descubrimiento.** Un manejador del bus hay que suscribirlo desde algún
  sitio, y ese sitio es código del motor o de una escena. Un plugin se deja
  caer en `plugins/` y aparece solo. Sin eso, «extender sin tocar el núcleo» es
  falso: siempre hay que tocar algo para engancharse.
* **Puntos que el bus no publica.** Dibujar, por ejemplo. Nadie emite un evento
  por fotograma con la superficie dentro —sería un evento por fotograma con un
  objeto mutable de carga útil, que es justo lo que un bus no debe llevar—, así
  que un `overlay` propio no se podía escribir sin editar `DrawingSystem`.

Cómo se escribe un plugin
=========================
Un fichero `.py` en `plugins/` con una función `registrar(gestor)`::

    def registrar(gestor):
        def mi_overlay(superficie, escena, **_):
            ...  # pinta lo que quieras encima
        gestor.enganchar("escenario_dibujado", mi_overlay)

Los ganchos que existen están en `GANCHOS`, con su firma. La lista es corta a
propósito: cada gancho es una promesa de estabilidad hacia veintiséis personas,
y una API grande que hay que mantener compatible es peor regalo que una pequeña.

Lo que pasa cuando un plugin falla
==================================
Se retira y el juego sigue, con su traza en el registro — la misma decisión que
AUD-289 tomó para las entidades y por el mismo motivo: esto ejecuta código de
estudiantes, y un `IndexError` en el overlay de alguien no puede llevarse por
delante la clase entera. Un plugin que falla **dos veces** se desengancha para
no llenar el registro de la misma línea sesenta veces por segundo.
"""
from __future__ import annotations

import importlib.util
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

#: Los puntos de extensión, con lo que recibe cada uno.
#:
#: Todos los ganchos se llaman con argumentos **por nombre**, nunca
#: posicionales, y todos deben aceptar `**_`. Así se pueden añadir datos a un
#: gancho sin romper los plugins ya escritos, que es la única forma de que una
#: API que consumen veintiséis personas pueda evolucionar.
GANCHOS: dict[str, str] = {
    "juego_arrancado": "app — una vez, con el motor ya montado",
    "escenario_cargado": "escena, stage — al entrar en un nivel, ya cargado",
    "escenario_actualizado": "escena, dt — una vez por fotograma, tras el juego",
    "escenario_dibujado": "superficie, escena — encima de todo lo demás",
}

#: Dónde se buscan. Fuera de `src/` a propósito: lo que un estudiante añade no
#: se mezcla con el motor, y así `ruff`, `mypy` y el barrido de huérfanos no
#: tratan su código como si fuera del núcleo.
DIRECTORIO_POR_DEFECTO: str = "plugins"

#: Fallos seguidos que se le toleran a un gancho antes de desengancharlo.
FALLOS_TOLERADOS: int = 2


class GestorDePlugins:
    """Carga plugins y dispara los ganchos."""

    def __init__(self) -> None:
        self._ganchos: dict[str, list[Callable[..., Any]]] = {}
        self._fallos: dict[Callable[..., Any], int] = {}
        self._cargados: list[str] = []

    # ── registro ──────────────────────────────────────────────────
    def enganchar(self, nombre: str, funcion: Callable[..., Any]) -> bool:
        """Engancha una función a un punto de extensión.

        Devuelve `False` —y lo registra— si el gancho no existe. Es el error
        más probable de un plugin recién escrito: una errata en el nombre. Sin
        el aviso, el plugin se carga, no hace nada y no dice por qué.
        """
        if nombre not in GANCHOS:
            logger.warning(
                "plugins: no existe el gancho %r. Los que hay: %s",
                nombre, ", ".join(sorted(GANCHOS)))
            return False
        self._ganchos.setdefault(nombre, []).append(funcion)
        return True

    def desenganchar(self, nombre: str, funcion: Callable[..., Any]) -> None:
        if funcion in self._ganchos.get(nombre, []):
            self._ganchos[nombre].remove(funcion)

    @property
    def cargados(self) -> list[str]:
        return list(self._cargados)

    def enganchados(self, nombre: str) -> int:
        return len(self._ganchos.get(nombre, []))

    # ── descubrimiento ────────────────────────────────────────────
    def descubrir(self, directorio: Path | str = DIRECTORIO_POR_DEFECTO) -> int:
        """Carga todos los `.py` de `directorio` y les pide que se registren.

        Devuelve cuántos se cargaron. Un directorio que no existe **no es un
        error**: lo normal es no tener plugins, y avisar de ello en cada
        arranque enseñaría a ignorar los avisos.

        Los ficheros que empiezan por `_` se saltan, para que un plugin pueda
        tener módulos auxiliares sin que se carguen solos.
        """
        raiz = Path(directorio)
        if not raiz.is_dir():
            return 0
        cargados = 0
        for ruta in sorted(raiz.glob("*.py")):
            if ruta.name.startswith("_"):
                continue
            if self._cargar_uno(ruta):
                cargados += 1
        return cargados

    def _cargar_uno(self, ruta: Path) -> bool:
        """Importa un plugin y llama a su `registrar`. Nunca lanza."""
        try:
            spec = importlib.util.spec_from_file_location(
                f"loi_plugin_{ruta.stem}", ruta)
            if spec is None or spec.loader is None:
                return False
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
        except Exception:
            logger.exception("plugins: %s no se pudo importar; se ignora", ruta.name)
            return False

        registrar = getattr(modulo, "registrar", None)
        if not callable(registrar):
            logger.warning(
                "plugins: %s no define `registrar(gestor)`, así que no puede "
                "engancharse a nada. Se ignora.", ruta.name)
            return False
        try:
            registrar(self)
        except Exception:
            logger.exception("plugins: `registrar` de %s falló; se ignora",
                             ruta.name)
            return False
        self._cargados.append(ruta.stem)
        logger.info("plugins: cargado %s", ruta.stem)
        return True

    # ── disparo ───────────────────────────────────────────────────
    def disparar(self, nombre: str, **datos: Any) -> None:
        """Llama a todo lo enganchado a `nombre`. **Nunca lanza.**

        Un plugin que revienta se cuenta, y al segundo fallo se desengancha:
        esto corre por fotograma, y sesenta trazas por segundo del mismo error
        entierran el registro donde estaría la causa.
        """
        for funcion in list(self._ganchos.get(nombre, ())):
            try:
                funcion(**datos)
            except Exception:
                fallos = self._fallos.get(funcion, 0) + 1
                self._fallos[funcion] = fallos
                logger.exception(
                    "plugins: el gancho %r de %s falló (%d de %d)",
                    nombre, getattr(funcion, "__module__", "?"),
                    fallos, FALLOS_TOLERADOS)
                if fallos >= FALLOS_TOLERADOS:
                    self.desenganchar(nombre, funcion)
                    logger.warning(
                        "plugins: %r desenganchado de %r tras fallar %d veces",
                        getattr(funcion, "__qualname__", funcion), nombre, fallos)


_gestor: GestorDePlugins | None = None


def get_gestor() -> GestorDePlugins:
    """El gestor del proceso.

    Global, como el resto de lo que `App` monta una vez: los ganchos se
    disparan desde la escena, desde el sistema de dibujado y desde el bucle
    principal, y enhebrar el gestor por los tres constructores no compraría
    nada — no hay dos juegos vivos a la vez.
    """
    global _gestor
    if _gestor is None:
        _gestor = GestorDePlugins()
    return _gestor


def _reset_gestor() -> None:
    """Para las pruebas."""
    global _gestor
    _gestor = None

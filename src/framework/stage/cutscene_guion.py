"""
Module: cutscene_guion
System: framework.stage
Academic Unit: N/A
Description: AUD-136 (D3) — guiones de escena escritos en texto, para que una
cutscene se pueda montar desde Tiled sin escribir Python.

Por qué un lenguaje de texto y no una API
==========================================
El sistema de escenas funcionaba, pero sólo desde código: había que importar
tres clases, construir acciones y llamar a `start()`. En este proyecto eso
significa que **sólo el profesor puede hacer una escena narrativa**, porque el
estudiante trabaja en Tiled y toca Python lo justo.

Es la misma barrera que ya se quitó dos veces este mes: el disparador que no
abría nada hasta que la puerta pudo declarar `abre_con` (AUD-132), y el
sistema de diálogo entero, que estaba escrito, probado y era inalcanzable
porque nadie podía nombrarlo desde el mapa (AUD-127).

El guion se escribe en una propiedad `guion` del objeto `Cutscene`:

.. code-block:: text

    camara 320 100 1.0
    + mover jugador 340 . 1.0
    temblor 0.4 6
    dialogo intro_narrador
    evento ABRIR_COMPUERTA

Reglas del lenguaje, todas por el mismo motivo —que un error de escritura no
se lleve por delante la partida del estudiante—:

* una orden por línea, en español, sin puntuación;
* `#` empieza un comentario;
* `+` al principio de una línea la ejecuta **a la vez** que la anterior;
* `.` como coordenada significa «déjala como está»;
* una línea que no se entiende **no rompe la escena**: se anota en la lista de
  errores, se registra un aviso y el resto del guion sigue. Un guion es
  contenido, no código: fallar en caliente y dejar al jugador sin control por
  una coma es peor que ignorar una línea.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.framework.stage.cutscene_system import (
    AccionParalela,
    CameraMoveAction,
    CutsceneAction,
    CutsceneScript,
    DialogoArbolAction,
    DialogueAction,
    EsperarEventoAction,
    EventoAction,
    FadeAction,
    MoverEntidadAction,
    SonidoAction,
    TemblorAction,
    WaitAction,
)

logger = logging.getLogger(__name__)


@dataclass
class ContextoDeGuion:
    """Lo que el guion puede tocar. Nada más.

    Es deliberadamente corto: el guion mueve entidades, la cámara, el diálogo
    y el bus. Todo lo demás se hace **a través del bus**, con `evento`, para
    que añadir una mecánica no obligue a añadir una orden al lenguaje.
    """

    camara: Any = None
    jugador: Any = None
    bus: Any = None
    dialogo: Any = None
    #: Entidades por nombre, para `mover Guardia1 ...`.
    entidades: dict[str, Any] = field(default_factory=dict)

    def buscar(self, nombre: str) -> Any:
        if nombre.lower() in ("jugador", "player"):
            return self.jugador
        return self.entidades.get(nombre)


def _numero(texto: str) -> float | None:
    try:
        return float(texto)
    except (TypeError, ValueError):
        return None


class _Analizador:
    def __init__(self, contexto: ContextoDeGuion) -> None:
        self.ctx = contexto
        self.errores: list[str] = []

    def _fallo(self, linea: int, mensaje: str) -> None:
        self.errores.append(f"línea {linea}: {mensaje}")
        logger.warning("guion de escena, línea %d: %s", linea, mensaje)

    # -- órdenes ---------------------------------------------------
    def orden(self, linea: int, partes: list[str]) -> CutsceneAction | None:
        orden = partes[0].lower()
        args = partes[1:]
        metodo = getattr(self, f"_orden_{orden}", None)
        if metodo is None:
            self._fallo(linea, f"no entiendo «{orden}»")
            return None
        return metodo(linea, args)

    def _orden_esperar(self, linea: int, args: list[str]) -> CutsceneAction | None:
        segundos = _numero(args[0]) if args else None
        if segundos is None:
            self._fallo(linea, "esperar necesita segundos: «esperar 0.5»")
            return None
        return WaitAction(max(0.0, segundos))

    def _orden_camara(self, linea: int, args: list[str]) -> CutsceneAction | None:
        if len(args) < 3:
            self._fallo(linea, "camara necesita x, y y duración")
            return None
        x, y, dur = (_numero(a) for a in args[:3])
        if None in (x, y, dur):
            self._fallo(linea, "camara: x, y y duración tienen que ser números")
            return None
        return CameraMoveAction(x, y, max(0.001, dur), self.ctx.camara)

    def _orden_mover(self, linea: int, args: list[str]) -> CutsceneAction | None:
        if len(args) < 4:
            self._fallo(linea, "mover necesita: quién, x, y, duración")
            return None
        quien = self.ctx.buscar(args[0])
        if quien is None:
            self._fallo(linea, f"no hay ninguna entidad llamada «{args[0]}»")
            return None
        x, dur = _numero(args[1]), _numero(args[3])
        # El punto significa «esta coordenada no la toques». Sin él, mover a
        # alguien en horizontal obligaría a copiar su y a mano en el guion, y
        # un número copiado mal deja al personaje flotando.
        y = None if args[2] == "." else _numero(args[2])
        if x is None or dur is None or (args[2] != "." and y is None):
            self._fallo(linea, "mover: x, y y duración tienen que ser números")
            return None
        return MoverEntidadAction(quien, x, y, max(0.001, dur))

    def _orden_dialogo(self, linea: int, args: list[str]) -> CutsceneAction | None:
        if not args:
            self._fallo(linea, "dialogo necesita el nombre de un árbol")
            return None
        return DialogoArbolAction(self.ctx.dialogo, args[0])

    def _orden_evento(self, linea: int, args: list[str]) -> CutsceneAction | None:
        if not args:
            self._fallo(linea, "evento necesita un nombre")
            return None
        return EventoAction(self.ctx.bus, args[0])

    def _orden_sonido(self, linea: int, args: list[str]) -> CutsceneAction | None:
        if not args:
            self._fallo(linea, "sonido necesita un nombre de evento")
            return None
        return SonidoAction(self.ctx.bus, args[0])

    def _orden_temblor(self, linea: int, args: list[str]) -> CutsceneAction | None:
        dur = _numero(args[0]) if args else 0.4
        fuerza = _numero(args[1]) if len(args) > 1 else 6.0
        return TemblorAction(self.ctx.camara, dur or 0.4, fuerza or 6.0)

    def _orden_fundido(self, linea: int, args: list[str]) -> CutsceneAction | None:
        if not args or args[0].lower() not in ("entra", "sale"):
            self._fallo(linea, "fundido necesita «entra» o «sale»")
            return None
        dur = _numero(args[1]) if len(args) > 1 else 0.5
        return FadeAction(dur or 0.5, fade_in=args[0].lower() == "entra")

    def _orden_esperar_evento(self, linea: int, args: list[str]) -> CutsceneAction | None:
        if not args:
            self._fallo(linea, "esperar_evento necesita un nombre")
            return None
        tope = _numero(args[1]) if len(args) > 1 else 10.0
        return EsperarEventoAction(self.ctx.bus, args[0], tope or 10.0)


def analizar_guion(
    texto: str, contexto: ContextoDeGuion, *,
    bloquea: bool = True, saltable: bool = True, bandas: bool | None = None,
) -> tuple[CutsceneScript, list[str]]:
    """Convierte el texto de un guion en un `CutsceneScript`.

    Devuelve el guion y la lista de errores. Los errores **no** impiden que la
    escena se reproduzca: se avisa y se sigue con lo que sí se entendió.
    """
    analizador = _Analizador(contexto)
    acciones: list[CutsceneAction] = []

    for numero, cruda in enumerate(str(texto or "").splitlines(), start=1):
        linea = cruda.split("#", 1)[0].strip()
        if not linea:
            continue

        en_paralelo = linea.startswith("+")
        if en_paralelo:
            linea = linea[1:].strip()

        # «texto Narrador: hola» lleva la frase entera detrás de los dos
        # puntos, así que no se puede partir por espacios como las demás.
        if linea.lower().startswith("texto "):
            resto = linea[6:]
            hablante, _, frase = resto.partition(":")
            if not frase.strip():
                hablante, frase = "", resto
            accion: CutsceneAction | None = DialogueAction(
                frase.strip(), speaker=hablante.strip())
        else:
            accion = analizador.orden(numero, linea.split())

        if accion is None:
            continue

        if en_paralelo and acciones:
            anterior = acciones[-1]
            if isinstance(anterior, AccionParalela):
                anterior._acciones.append(accion)
            else:
                acciones[-1] = AccionParalela([anterior, accion])
        else:
            if en_paralelo:
                analizador.errores.append(
                    "línea 1: «+» en la primera orden; no hay nada anterior "
                    "con lo que ir en paralelo",
                )
            acciones.append(accion)

    if bandas is None:
        bandas = bloquea
    guion = CutsceneScript(acciones, bloquea=bloquea, saltable=saltable,
                           bandas=bool(bandas))
    return guion, analizador.errores

"""
Module: azar
System: engine.core
Academic Unit: N/A

AUD-375 — quién fija la semilla del proceso.

El defecto
==========
No había **una sola** llamada a `random.seed()` en `src/engine` ni en
`src/framework`. Las 46 llamadas a `random.*` del motor —partículas, sacudida
de cámara, clima, rayos, decisiones de enemigo— tiraban del generador global
sin sembrarlo nunca, así que dos ejecuciones del mismo escenario no coinciden
y no hay forma de pedir que coincidan.

Lo que costaba, con nombres propios:

* **AUD-359** — «la prueba de presupuesto del 4-1 fallaba por el azar de una
  sola muestra». Sin poder fijar el azar, una prueba se escribe tolerante, y
  una prueba tolerante deja pasar las regresiones pequeñas.
* **Un informe de fallo no se puede reproducir.** «Se me cayó en el acto IV»
  no basta cuando la disposición de las partículas, el instante del rayo y la
  decisión del enemigo eran otras esa vez.
* **El fantasma del speedrun** no se puede validar contra una repetición.

Qué hace este módulo, y qué no
==============================
Hace **una** cosa: fijar la semilla del generador global una vez, al arrancar,
y dejarla escrita en el registro.

Hace **una** cosa con dos generadores: el de `random` y el de NumPy. Son
globales distintos y `random.seed()` no toca el segundo — AUD-375 sembró sólo
el primero y dio la partida por reproducible cuando no lo era, porque los doce
usos de `np.random` de `vfx/particle_system.py` seguían saliendo distintos cada
vez (AUD-385).

No convierte los 66 usos para que cada sistema reciba su generador. Eso es
auditar uso por uso y va por lotes (GAP-042). Pero es el paso que hace
verificable todo lo demás: con los dos globales sembrados, un sistema que
todavía tira de `random.random()` o de `np.random.uniform()` **ya es
reproducible**, y el trabajo de darle su propio generador pasa a ser una mejora
de aislamiento en vez del arreglo del que todo depende.

Por qué se siembra aunque no se pida
------------------------------------
Porque no ser determinista y no saber qué pasó son cosas distintas. La partida
de un jugador **no debe** salir siempre igual —un juego que reparte siempre el
mismo rayo en el mismo segundo se lee como roto—, y aun así su informe de
fallo tiene que poder repetirse. La respuesta es sembrar con una semilla
inventada y **anotarla**: azar de verdad, y reproducible a posteriori.

Por eso `sembrar()` la escribe en el registro con `INFO`. El registro va a un
fichero junto a las partidas (AUD-268), así que la semilla viaja en cualquier
informe sin que el jugador sepa qué es una semilla.
"""
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)

#: Rango de la semilla inventada. 2^32 es lo que aceptan los generadores de
#: cualquier lenguaje al que alguien quiera portar una repetición, y entra en
#: un entero de 32 bits sin sorpresas al serializarla en una partida.
_TOPE: int = 2 ** 32

#: La del proceso. `None` hasta que alguien siembra: leerla antes de sembrar
#: tiene que devolver «ninguna», no un número inventado que nadie usó.
_semilla: int | None = None


def sembrar(semilla: int | None = None) -> int:
    """Fija la semilla del generador global. Devuelve la que quedó puesta.

    Con `None` se inventa una y se anota, que es el caso normal de una partida:
    azar de verdad, y repetible después si algo va mal.

    Se llama **una vez**, al arrancar. Volver a llamar en mitad de la partida
    rebobina el generador, y dos sistemas que compartan el global verían
    repetirse valores que ya habían salido.
    """
    global _semilla
    if semilla is None:
        semilla = random.randrange(_TOPE)
    semilla = int(semilla)
    random.seed(semilla)
    # AUD-385 — NumPy tiene **su propio** generador global, ajeno a
    # `random.seed()`. Sembrar sólo el de Python dejaba fuera 20 usos, y doce
    # están en `vfx/particle_system.py`, que es quien dibuja todas las
    # partículas del juego: chispas, sangre, polvo, lluvia. O sea que la
    # partida seguía sin poder repetirse justo en lo más visible, mientras
    # AUD-375 daba el asunto por cerrado.
    #
    # Se descubrió mirando de qué generador tira cada módulo en vez de fiarse
    # del recuento de `random.*`, que sólo contaba la mitad de la historia.
    #
    # `np.random.seed` y no un `Generator` nuevo a propósito: el código que hay
    # llama a `np.random.uniform` directamente, y cambiar eso es el trabajo de
    # aislamiento de GAP-042b. Esto es lo que hace reproducible lo que YA hay.
    import numpy as np

    np.random.seed(semilla % 2**32)
    _semilla = semilla
    # INFO y no DEBUG: esto tiene que estar en el registro de una partida
    # normal, porque el informe que lo necesita se escribe después del fallo,
    # cuando ya no se puede volver a arrancar con más verbosidad.
    logger.info("semilla del azar: %d", semilla)
    return semilla


def semilla_actual() -> int | None:
    """La semilla del proceso, o `None` si nadie ha sembrado todavía."""
    return _semilla


def generador_numpy(semilla: int | None = None) -> np.random.Generator:
    """Un generador de NumPy propio, aislado del global — AUD-386.

    El hermano de `generador()` para los módulos que sortean con NumPy, que en
    este motor son los que mueven arreglos: partículas, ruido, patrones.

    Devuelve un `Generator` moderno y no el `RandomState` heredado: es el
    camino que NumPy recomienda desde 1.17, es más rápido, y sobre todo **no
    comparte estado con `np.random`**, que es justamente el punto. Cuidado con
    una diferencia de nombre al migrar: `Generator` tiene `integers`, no
    `randint`.

    Sin semilla, se deriva del global —que `sembrar()` ya fijó—, así que hereda
    la reproducibilidad del proceso sin necesidad de un número propio y sin que
    quien lo pide tenga que saber nada de semillas.
    """
    import numpy as np

    if semilla is None:
        semilla = int(np.random.randint(0, 2**32, dtype=np.int64))
    return np.random.default_rng(int(semilla))


def generador(semilla: int | None = None) -> random.Random:
    """Un generador propio, aislado del global.

    Es el camino por el que van las conversiones de GAP-042: un sistema que
    recibe el suyo se puede fijar en una prueba sin tocar el azar de nadie más,
    y deja de competir por el estado global con los otros catorce módulos que
    tiran de `random`. `WorldSimulation` fue el primero (AUD-374).

    Sin semilla, el generador nace del global — que ya está sembrado, así que
    hereda la reproducibilidad del proceso sin necesidad de un número propio.
    """
    if semilla is None:
        return random.Random(random.randrange(_TOPE))
    return random.Random(int(semilla))

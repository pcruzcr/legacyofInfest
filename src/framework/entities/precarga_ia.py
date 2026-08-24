"""Módulo: precarga_ia
Sistema: framework.entities
Unidad Académica: Unidad IX — Reconocimiento de patrones

Carga de scikit-learn ANTES de que el primer enemigo lo pida.

Por qué existe (AUD-088 + AUD-456 + AUD-457)
--------------------------------------------
`ai_predictor` importa scikit-learn entero en su cabecera (medido: 2,3-3,3 s).
AUD-088 movió esa carga a la pantalla de inicio, pero el flujo `--stage` /
`--boss` de `main.py` entierra la splash sin actualizarla, así que en ese
camino el import volvía a caer en el primer lote de `SquadBrain`, a medio
segundo de partida — justo cuando un enemigo está encima. El jugador lo veía
como un congelamiento del juego al recibir el primer golpe.

AUD-456 intentó resolverlo con un hilo daemon que importaba desde
`App.__init__`. Se retira en AUD-457: **la importación concurrente de
scipy 1.9.0 en CPython 3.14 deadlockea**. Medido en el arranque real del
juego, dos importadores en paralelo hacen que importlib lance
`_DeadlockError: deadlock detected by _ModuleLock('scipy.linalg.cython_blas')`
(que mata el hilo y pierde la precarga) o que se quede bloqueado para
siempre (el juego se congela). Ese es el cuelgue que el dueño veía.

La alternativa síncrona no tiene ese problema porque **nunca hay dos
importadores en vuelo**:

- Flujo normal: la splash paga la carga (AUD-088) con su mensaje visible.
- Flujo `--stage` / `--boss`: `main.py` la paga antes del bucle, en la
  arrancada del escenario — sin enemigos cerca, porque la partida aún no
  empieza.

Si sklearn no está instalado, la carga falla con ImportError (silencioso) y
la IA es la heurística de `tactica_por_reglas` — exactamente la reserva que
el README promete. `ia_lista()` existe para que `squad_brain` decida sin
llamar al predictor cuando la carga no se hizo.
"""

from __future__ import annotations

import logging
import sys
import threading

logger = logging.getLogger(__name__)

_MODULO = "src.framework.entities.ai_predictor"

#: `True` cuando la carga ya se intentó (la haya hecho o haya fallado).
_arrancada: bool = False
#: Señal de «la carga terminó». Sin hilo desde AUD-457, pero `squad_brain`
#: sigue consultándola; el objeto Event la conserva entre llamadas.
_terminado: threading.Event = threading.Event()


def precargar_ia() -> None:
    """Importa `ai_predictor` al momento, bloqueando hasta terminar.

    Una sola vez por proceso: la segunda llamada no vuelve a importar. El
    bloqueo es la garantía de AUD-457: la splash (o la arrancada de
    `main.py --stage`) es el ÚNICO importador del árbol scipy en ese momento,
    y dos importadores en paralelo son lo que deadlockea en Python 3.14.

    `ImportError` es silencioso: scikit-learn es opcional y sin él la IA es
    la heurística. Cualquier otro error sí se anota — un import roto en el
    flujo de arranque no es un modo de funcionamiento.
    """
    global _arrancada
    if _arrancada:
        return
    _arrancada = True
    try:
        import src.framework.entities.ai_predictor  # noqa: F401
    except ImportError:
        pass
    except Exception:
        logger.warning("precarga_ia: la carga de la IA falló", exc_info=True)
    finally:
        _terminado.set()


def esperar() -> None:
    """Bloquea hasta que la carga terminó. En el diseño síncrono (AUD-457)
    sólo hace falta como contrato para quien llegue aquí por otro camino."""
    _terminado.wait()


def importada() -> bool:
    """`True` si `ai_predictor` quedó publicado en `sys.modules`.

    Un import fallido deja una entrada `None` en `sys.modules`; publicada de
    verdad es el objeto módulo.
    """
    return sys.modules.get(_MODULO) is not None


def ia_lista() -> bool:
    """`True` cuando la carga ya se intentó (con o sin scikit-learn).

    Se consulta desde `squad_brain._decide_batch` ANTES de llamar al
    predictor: si la respuesta es `False`, la carga aún no se hizo y pedirlo
    aquí bloquearía el fotograma — exactamente el tirón que esto evita.
    """
    return _terminado.is_set()

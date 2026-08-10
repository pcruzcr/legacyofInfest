"""Cuantiles de una serie de tiempos de fotograma, puros y verificables.

AUD-346 — el promedio esconde la varianza
=========================================
El motor medía cada fotograma con un promedio móvil de pygame y un banco de
50 ms de fotograma en algún test, pero nadie tenía la pregunta correcta:
«¿el juego va estable o va a trompicones?». 59 fotogramas a 16 ms y uno a
250 ms dan 20 ms de media: un promedio que no cuenta la historia de cómo se
siente el juego.

Aquí se calcula sin estado —una lista de milisegundos dentro, cinco números
fuera— y se enseña en la consola de F11 y en los benches. Rango de los
cuantiles: P50 (el fotograma típico), P95 (el fotograma agónico), P99 y el
peor absoluto. La regla es el **nearest-rank**: el elemento en la posición
`ceil(q * n)` de la lista ordenada; es la que no necesita interpolar y la
que un lector de un archivo de tiempos puede reproducir con lápiz.
"""
from __future__ import annotations

import math
from collections.abc import Iterable

#: Los cuantiles que se reportan, en el orden en que se muestran.
CUANTILES: tuple[tuple[str, float], ...] = (
    ("p50", 0.50),
    ("p95", 0.95),
    ("p99", 0.99),
)


def cuantiles(muestras: Iterable[float]) -> dict[str, float]:
    """P50, P95, P99, media y peor fotograma de una serie (en milisegundos).

    Devuelve un diccionario vacío para una serie vacía, para que quien lo
    muestre decida si omite la línea; una serie de un solo dato reporta ese
    dato en todos los huecos.
    """
    ordenada = sorted(float(m) for m in muestras)
    if not ordenada:
        return {}
    n = len(ordenada)
    peor = ordenada[-1]
    resultado: dict[str, float] = {
        "media": sum(ordenada) / n,
        "peor": peor,
    }
    for nombre, q in CUANTILES:
        idx = min(n - 1, math.ceil(q * n) - 1)
        resultado[nombre] = ordenada[idx]
    return resultado
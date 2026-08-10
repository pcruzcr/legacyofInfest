"""AUD-379 — el cable trampa de una decisión medida en contra (GAP-037).

Qué se decidió, y con qué número
================================
`RejillaEspacial` (AUD-276) da fase amplia, trazado de rayos y línea de visión,
y su único consumidor de producción es `vfx/sombras_proyectadas.py`. GAP-037
proponía cablearla también al camino de colisión, y lo llamaba «el candidato
con mejor relación coste/ganancia de toda la lista».

Medido, es al revés. El mapa más grande del repositorio —`stage4_1`— trae **51
rectángulos de colisión**, de los que 4 caen cerca del cuerpo:

    lista completa : 0,0419 ms/fotograma
    con rejilla    : 0,0310 ms/fotograma   (1,35x)

Ahorra **0,011 ms** sobre un presupuesto de 16,67: un 0,07%. Cablearla añadiría
una estructura que mantener, un sitio más donde los sólidos y su índice pueden
desincronizarse —las plataformas móviles y los bloques se recomponen cada
fotograma— y una ruta nueva que probar, a cambio de nada medible.

La premisa era falsa
====================
`rejilla.py` justificaba su existencia diciendo que «`stage4_1` trae miles de
rectángulos y la inmensa mayoría están a pantallas de distancia». Son 51. El
número nunca se verificó, y explica de paso por qué el propio módulo de sombras
dice, medido, que la rejilla «no cambia el resultado»: no había nada que
acelerar.

Esto **no invalida** `RejillaEspacial`. Sus otras dos operaciones —`rayo()` y
`hay_vision()`— siguen siendo la respuesta correcta a «¿qué hay entre este
punto y aquel otro?», que ninguna lista de rectángulos contesta por barrido. Lo
que se cae es sólo el argumento de la fase amplia.

Por qué esta prueba no falla antes y pasa después
=================================================
Porque no arregla nada: **vigila la premisa de una decisión**. Es la misma
especie que `test_calibracion_del_salto`, que no arregla el salto sino que grita
si alguien cambia la gravedad. Si algún día un mapa trae miles de rectángulos
de verdad, esto se pone rojo y obliga a re-medir antes de dar por buena una
decisión que se tomó con 51.
"""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

_RAIZ = Path(__file__).resolve().parent.parent

#: Por encima de esto, la decisión de GAP-037 deja de estar respaldada por su
#: medición y hay que rehacerla. No es un límite de diseño —nadie prohíbe un
#: mapa grande—: es el punto donde el barrido lineal empieza a costar lo
#: bastante como para que una fase amplia se pague. Con 51 rectángulos el
#: ahorro medido fue de 0,011 ms; diez veces más rectángulos es donde conviene
#: volver a mirar.
TOPE_ANTES_DE_REMEDIR: int = 500


@pytest.fixture(scope="module")
def _display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield


def _mapas() -> list[Path]:
    return sorted((_RAIZ / "assets" / "maps").rglob("*.tmx"))


def test_ningun_mapa_justifica_todavia_una_fase_amplia(_display) -> None:
    from src.framework.stage.stage_loader import StageLoader

    peores: list[tuple[int, str]] = []
    for ruta in _mapas():
        try:
            datos = StageLoader.load(str(ruta))
        except Exception:
            # Un mapa que no carga es problema de otras pruebas, no de ésta.
            continue
        peores.append((len(datos.collision_rects), ruta.parent.name))

    assert peores, "no se pudo cargar ningún mapa"
    peores.sort(reverse=True)
    cuantos, nombre = peores[0]
    assert cuantos <= TOPE_ANTES_DE_REMEDIR, (
        f"«{nombre}» trae {cuantos} rectángulos de colisión, por encima de "
        f"{TOPE_ANTES_DE_REMEDIR}. GAP-037 —no cablear `RejillaEspacial` al "
        "camino de colisión— se decidió midiendo sobre 51, donde ahorraba "
        "0,011 ms de 16,67. Con este mapa esa medición ya no vale: hay que "
        "rehacerla antes de mantener la decisión."
    )


def test_la_rejilla_sigue_teniendo_su_consumidor(_display) -> None:
    """Lo que la decisión NO dice: que la rejilla sobre.

    Se cayó el argumento de la fase amplia, no el módulo. Si alguien la borra
    leyendo mal la decisión, las sombras proyectadas se quedan sin la
    estructura que resuelve «¿qué hay entre el foco y este punto?».
    """
    from src.framework.vfx import sombras_proyectadas

    assert hasattr(sombras_proyectadas, "RejillaEspacial"), (
        "`sombras_proyectadas` ya no usa `RejillaEspacial`: si se retiró, "
        "revisa GAP-037 — allí se decidió no cablearla a las colisiones, no "
        "prescindir de ella"
    )

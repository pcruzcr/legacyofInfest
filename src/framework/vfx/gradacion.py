"""La matriz de color 3x3, aplicada píxel a píxel (Unidad V).

Por qué está aquí y no dentro de `post_processing.py` (AUD-496)
================================================================
Porque es el único punto caliente medido del dibujo, y aislarlo permite
medirlo, probarlo y precalentarlo por separado.

La medida que motivó esto
-------------------------
`tests/test_stage4_1.py::TestCabeEnElPresupuestoDeFotograma` llevaba tiempo
en rojo: el dibujo del 4-1 costaba unos 47 ms contra un presupuesto de 15.
Un perfil del fotograma completo dijo dónde:

    post_processing.apply   ~28-30 ms   <- la gradación, aquí
    drawing_system.draw       ~4,4 ms
    _apply_bloom              ~2,9 ms
    resto                       ~7 ms

Y el desglose de esos 30 ms fue la sorpresa: la multiplicación de matrices
cuesta 5,4 ms; los otros ~25 son **mover los datos**, tres `astype(int32)`
sobre una vista no contigua de la superficie y tres escrituras de vuelta.
Optimizar la aritmética no servía de nada; había que dejar de copiar.

Por qué numba, si AUD-006 lo quitó del proyecto
-----------------------------------------------
AUD-006 midió que numba hacía **más lentas** las funciones escalares de
`math_utils` (cruzar la frontera Python→nopython cuesta más que dos sumas) y
lo revirtió. Ese mismo docstring deja escrita la condición para volver a
usarlo, y describe este caso con esas palabras: *«numba se gana el sueldo en
bucles apretados sobre arrays grandes... Si aparece un punto caliente real a
nivel de array (un núcleo de filtro por píxel...), compila **eso**, y mídelo
antes y después.»*

Medido, 800x600, matriz sepia de la Fase 4:

    numpy (lo que había)     30,58 ms
    numba njit                8,77 ms   (3,5x)
    salida                    idéntica píxel a píxel

La igualdad exacta no es un detalle: es la condición para poder sustituir
una por otra sin cambiar cómo se ve el juego. La comprueba
`tests/test_la_gradacion_no_copia_la_pantalla.py`.

El coste de compilar, y qué se hace con él
------------------------------------------
La primera llamada compila y cuesta ~1,1 s. Por eso existe `precalentar()`:
la pantalla de carga ya tiene un sistema de pasos anunciados (AUD-449) y ahí
el segundo se paga una vez y a la vista, en vez de como un tirón al entrar
al primer escenario con gradación.

numba es un extra opcional (`pip install -e ".[accel]"`). Sin él, esto usa
la ruta de numpy de siempre y el juego funciona igual, sólo que más despacio
— la misma regla que la invariante 7 aplica a scikit-learn.

AUD-530 — un hilo no bastaba, ocho sí
--------------------------------------
`TestCabeEnElPresupuestoDeFotograma::test_el_dibujo_cabe` seguía fallando
después de AUD-496 pese a que la ruta acelerada estaba activa
(`gradacion.acelerada()` daba `True`): un perfil del dibujo completo de la
Fase 4 repartía así los ~13-14 ms típicos, con picos por encima de 15 ms bajo
la más mínima carga del sistema —

    aplicar_gradacion (serie)   ~5-7 ms   <- seguía siendo el mayor bloque
    resto del dibujo            ~7-8 ms

El núcleo ya no copiaba nada (AUD-496 lo resolvió); lo que quedaba era la
propia pasada por 480 000 píxeles en un hilo. La medida, aislada, 800x600,
matriz sepia:

    njit en serie          11,96 ms
    njit + parallel/prange   3,86 ms   (~3,1x, no 8x: el límite es el ancho
                                         de banda de memoria del array, no
                                         los núcleos)
    salida                  idéntica píxel a píxel

Repartir por `y` (fila) con `numba.prange` es seguro sin bloqueo ni sección
crítica porque cada hilo escribe filas que ningún otro hilo toca — no hay
dato compartido en escritura. La igualdad de salida la sigue comprobando
`tests/test_la_gradacion_no_copia_la_pantalla.py`, que no cambió: si el
paralelismo alterase un solo píxel, esa prueba lo vería.

Esto baja el dibujo típico de la Fase 4 a ~13 ms, con margen real bajo el
presupuesto de 15 en vez de pisarlo. No lo hace inmune al ruido de máquina
— sigue siendo una medida de milisegundos, y una carga suficiente (otro
proceso, otra sesión) puede seguir empujarla por encima alguna vez, igual
que a `test_con_la_vision_puesta_tambien` en el mismo archivo. La diferencia
es que antes el dibujo *no cabía* casi nunca; ahora cabe casi siempre y sólo
el ruido del sistema, no el código, explica una falla ocasional.
"""
from __future__ import annotations

from typing import Any, Final

import numpy as np

#: Cada canal de salida es el mismo canal de entrada, escalado a 255.
#: Aplicarla es una pasada completa por la pantalla para no cambiar nada, así
#: que `PostProcessing.set_color_grading` la trata como «sin gradación».
MATRIZ_IDENTIDAD: Final[tuple[int, ...]] = (255, 0, 0, 0, 255, 0, 0, 0, 255)

_nucleo: Any = None
_numba_intentado = False


def _compilar() -> Any:
    """El núcleo JIT, o `None` si numba no está instalado.

    Se importa aquí dentro y no arriba a propósito: `import numba` costaba
    419 ms de los 450 que tardaba en importarse `math_utils` (AUD-006), y
    quien juegue sin el extra `accel` no debe pagar nada por él.
    """
    global _nucleo, _numba_intentado
    if _numba_intentado:
        return _nucleo
    _numba_intentado = True
    try:
        import numba
    except ImportError:
        return None

    @numba.njit(cache=True, nogil=True, parallel=True)
    def _kernel(px, m):  # pragma: no cover — lo ejecuta LLVM, no CPython
        # El orden de los bucles no es indiferente: `pixels3d` entrega la
        # pantalla con forma (ancho, alto, 3) pero strides (4, 3200, -1), o
        # sea que los píxeles consecutivos en **x** son los contiguos en
        # memoria y avanzar en `y` salta una fila entera. Recorrerlo con `x`
        # por fuera lee a saltos de 3200 bytes y desperdicia cada línea de
        # caché: medido, 8,42 ms así contra 5,70 ms con `x` por dentro, sin
        # cambiar una sola operación aritmética.
        #
        # AUD-530 — `parallel=True` + `prange` sobre `y`: cada hilo escribe
        # filas propias (no hay dos hilos tocando el mismo píxel), así que
        # repartir por fila es seguro sin bloqueo ni reducción. Medido en
        # 800x600 con `nogil=True` ya puesto: 11,96 ms en serie contra 3,86 ms
        # con 8 hilos (~3,1x, no 8x — la banda de memoria del array, no la
        # CPU, es el límite; ver `tests/test_stage4_1.py` para el presupuesto
        # de fotograma completo que motivó medir esto).
        ancho, alto, _ = px.shape
        for y in numba.prange(alto):
            for x in range(ancho):
                r = np.int32(px[x, y, 0])
                g = np.int32(px[x, y, 1])
                b = np.int32(px[x, y, 2])
                px[x, y, 0] = min(255, max(0, (r * m[0] + g * m[1] + b * m[2]) // 255))
                px[x, y, 1] = min(255, max(0, (r * m[3] + g * m[4] + b * m[5]) // 255))
                px[x, y, 2] = min(255, max(0, (r * m[6] + g * m[7] + b * m[8]) // 255))

    _nucleo = _kernel
    return _nucleo


def acelerada() -> bool:
    """¿Está disponible la ruta rápida? Para que lo diga el diagnóstico."""
    return _compilar() is not None


def precalentar() -> bool:
    """Compila el núcleo con una imagen mínima. Devuelve si quedó acelerada.

    Se llama desde la pantalla de carga: compilar cuesta ~1,1 s la primera
    vez, y ese segundo se paga mejor donde el jugador ya está esperando que
    como un tirón al entrar al primer escenario con gradación.
    """
    nucleo = _compilar()
    if nucleo is None:
        return False
    minimo = np.zeros((2, 2, 3), dtype=np.uint8)
    nucleo(minimo, np.array(MATRIZ_IDENTIDAD, dtype=np.int32))
    return True


def _con_numpy(px: np.ndarray, m: tuple[int, ...]) -> None:
    """La ruta de siempre. Es la definición de lo que tiene que dar la otra.

    Se conserva tal cual estaba —incluida la división entera `// 255`, que
    trunca— porque cualquier «mejora» aquí cambiaría el color de un píxel y
    con él la referencia contra la que se compara el núcleo rápido.
    """
    cr, cg, cb, crr, cgg, cbb, crrr, cggg, cbbb = m
    pr = px[:, :, 0].astype(np.int32)
    pg = px[:, :, 1].astype(np.int32)
    pb = px[:, :, 2].astype(np.int32)
    px[:, :, 0] = np.clip((pr * cr + pg * cg + pb * cb) // 255, 0, 255).astype(np.uint8)
    px[:, :, 1] = np.clip((pr * crr + pg * cgg + pb * cbb) // 255, 0, 255).astype(np.uint8)
    px[:, :, 2] = np.clip((pr * crrr + pg * cggg + pb * cbbb) // 255, 0, 255).astype(np.uint8)


def aplicar_gradacion(px: np.ndarray, matriz: tuple[int, ...]) -> None:
    """Aplica la matriz sobre los píxeles, **en el sitio**.

    `px` es la vista de la superficie (`pygame.surfarray.pixels3d`), así que
    escribir aquí es escribir en la pantalla; no se devuelve nada.
    """
    if matriz == MATRIZ_IDENTIDAD:
        return
    nucleo = _compilar()
    if nucleo is None:
        _con_numpy(px, matriz)
        return
    nucleo(px, np.asarray(matriz, dtype=np.int32))

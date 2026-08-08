"""
bench_sprite_batch.py — ¿compensa dibujar los sprites por GPU?

AUD-301. La pregunta que AUD-148 dejó abierta y que `docs/87` §15.4 arrastraba
desde entonces: `SpriteBatch` estaba en la lista de pendientes con la nota
«medir primero en la máquina destino». Esto es esa medición.

Las tres rutas que se comparan, y por qué son tres
==================================================
1. **Blits sueltos** — lo que hace el motor hoy: un `surface.blit` por sprite,
   con el bucle en Python.
2. **`Surface.blits()`** — el mismo trabajo con el bucle en C. Es lo que ya
   mide `sprite_atlas` (2,06 → 1,74 ms con 2.000) y lo que un `SpriteBatch` de
   CPU puede dar sin tocar nada más.
3. **Una llamada de dibujado instanciada en OpenGL** — un cuádruple por
   sprite, todos en un `render(instances=N)` contra el atlas subido una vez.

Y la cuarta columna, que es la que decide
=========================================
**GPU + lectura de vuelta.** Si el juego dibuja por CPU, los píxeles que la
tarjeta produce hay que bajarlos otra vez a una `Surface`, y `glReadPixels` es
lento. Una ruta de GPU que gane en la tarjeta y pierda en el trayecto de vuelta
no sirve de nada mientras el resto del fotograma siga en CPU — y eso sólo se ve
midiendo las dos cosas por separado.

Con qué tarjeta mide
====================
Con la que le dé Windows, y lo dice al terminar. En este equipo hay dos —una
Intel HD 530 integrada y una Quadro M2200— y **ni SDL ni ModernGL eligen la
Quadro por su cuenta**: ni con contexto standalone, ni con ventana OpenGL real.
No es cosa del motor; en Windows la ruta OpenGL de un proceso la decide una
preferencia por aplicación que hay que dar de alta.

Para medir con la dedicada, una de estas dos, y volver a ejecutar esto:

* Panel de control de NVIDIA → Administrar configuración 3D → Configuración de
  programa → añadir `python.exe` → «Procesador NVIDIA de alto rendimiento».
* Configuración de Windows → Sistema → Pantalla → Gráficos → añadir
  `python.exe` → Alto rendimiento.

**Y lo que la tarjeta dedicada no va a cambiar.** La columna `GPU` mejorará; la
de `GPU+bajar`, probablemente **empeore**: bajar píxeles de una tarjeta discreta
cruza el bus PCIe, mientras que la integrada comparte la memoria del sistema. La
conclusión —que no compensa mover los sprites a la tarjeta mientras el fotograma
se componga en CPU— se refuerza, no se debilita. Lo que sí bajará es el umbral a
partir del cual la GPU gana dibujando.

Uso::

    python scripts/bench_sprite_batch.py            # 500, 2.000 y 8.000
    python scripts/bench_sprite_batch.py --sprites 20000

La columna `lote GPU` (AUD-340) es el `SpriteBatchGPU` del motor, con su
atlas y sus órdenes reales; la columna `GPU` es la misma ruta de dibujado
con el mínimo de plomería. La diferencia entre las dos es la de clase: la
segunda entra a medir el algoritmo, la primera a medir el componente.
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path

# AUD-177: esto imprime «→» y «×», y la consola de Windows usa cp1252.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

ANCHO, ALTO = 800, 600
LADO = 32
REPETICIONES = 30


def _sprites_de_prueba(cantidad: int) -> tuple[pygame.Surface, list[tuple[int, int]]]:
    """Un atlas de 4×4 recortes y las posiciones donde van."""
    import random

    hoja = pygame.Surface((LADO * 4, LADO * 4), pygame.SRCALPHA)
    for i in range(16):
        color = (40 + i * 12, 200 - i * 8, 90 + i * 9, 255)
        hoja.fill(color, pygame.Rect((i % 4) * LADO, (i // 4) * LADO, LADO, LADO))
    rng = random.Random(1234)
    posiciones = [(rng.randrange(0, ANCHO - LADO), rng.randrange(0, ALTO - LADO))
                  for _ in range(cantidad)]
    return hoja, posiciones


def _mediana(fn) -> float:
    """Mediana de `REPETICIONES` pasadas, en milisegundos."""
    for _ in range(3):
        fn()
    tiempos = []
    for _ in range(REPETICIONES):
        t = time.perf_counter()
        fn()
        tiempos.append((time.perf_counter() - t) * 1000.0)
    return statistics.median(tiempos)


def medir_cpu(cantidad: int) -> tuple[float, float]:
    hoja, posiciones = _sprites_de_prueba(cantidad)
    destino = pygame.Surface((ANCHO, ALTO))
    recortes = [pygame.Rect((i % 4) * LADO, (i // 4) * LADO, LADO, LADO)
                for i in range(16)]

    def sueltos() -> None:
        for n, pos in enumerate(posiciones):
            destino.blit(hoja, pos, recortes[n % 16])

    secuencia = [(hoja, pos, recortes[n % 16])
                 for n, pos in enumerate(posiciones)]

    def en_lote() -> None:
        destino.blits(secuencia, doreturn=False)

    return _mediana(sueltos), _mediana(en_lote)


_VERTEX = """
#version 330
in vec2 en_esquina;
in vec2 en_pos;
in vec4 en_uv;
out vec2 uv;
uniform vec2 pantalla;
uniform float lado;
void main() {
    vec2 px = en_pos + en_esquina * lado;
    vec2 ndc = vec2(px.x / pantalla.x * 2.0 - 1.0,
                    1.0 - px.y / pantalla.y * 2.0);
    uv = en_uv.xy + en_esquina * en_uv.zw;
    gl_Position = vec4(ndc, 0.0, 1.0);
}
"""

_FRAGMENT = """
#version 330
in vec2 uv;
out vec4 color;
uniform sampler2D atlas;
void main() { color = texture(atlas, uv); }
"""


def medir_gpu(cantidad: int) -> tuple[float, float, str]:
    """(dibujar, dibujar + bajar los píxeles, nombre de la tarjeta)."""
    import moderngl
    import numpy as np

    ctx = moderngl.create_standalone_context()
    hoja, posiciones = _sprites_de_prueba(cantidad)
    ancho_hoja, alto_hoja = hoja.get_size()
    textura = ctx.texture((ancho_hoja, alto_hoja), 4,
                          pygame.image.tostring(hoja, "RGBA", False))
    textura.filter = (moderngl.NEAREST, moderngl.NEAREST)
    textura.use(0)

    programa = ctx.program(vertex_shader=_VERTEX, fragment_shader=_FRAGMENT)
    programa["pantalla"].value = (float(ANCHO), float(ALTO))
    programa["lado"].value = float(LADO)
    programa["atlas"].value = 0

    esquinas = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype="f4")
    vbo_esquinas = ctx.buffer(esquinas.tobytes())

    # Una fila por sprite: posición en píxeles y su recorte en coordenadas de
    # textura. Es lo único que cambia entre fotogramas en un juego real.
    instancias = np.zeros((cantidad, 6), dtype="f4")
    paso_u, paso_v = LADO / ancho_hoja, LADO / alto_hoja
    for n, (x, y) in enumerate(posiciones):
        i = n % 16
        instancias[n] = (x, y, (i % 4) * paso_u, (i // 4) * paso_v, paso_u, paso_v)
    vbo_inst = ctx.buffer(instancias.tobytes())

    vao = ctx.vertex_array(programa, [
        (vbo_esquinas, "2f", "en_esquina"),
        (vbo_inst, "2f 4f/i", "en_pos", "en_uv"),
    ])
    fbo = ctx.simple_framebuffer((ANCHO, ALTO))
    fbo.use()

    def dibujar() -> None:
        fbo.clear(0.0, 0.0, 0.0, 1.0)
        vao.render(moderngl.TRIANGLE_STRIP, instances=cantidad)
        # Sin esto se mide encolar, no dibujar: el controlador devuelve el
        # control antes de que la tarjeta haya terminado.
        ctx.finish()

    def dibujar_y_bajar() -> None:
        dibujar()
        fbo.read(components=4)

    tarjeta = str(ctx.info.get("GL_RENDERER", "?"))
    resultado = (_mediana(dibujar), _mediana(dibujar_y_bajar), tarjeta)
    ctx.release()
    return resultado


def medir_lote_gpu(cantidad: int) -> float:
    """El `SpriteBatchGPU` del motor (AUD-340): atlas real + órdenes reales.

    Mide lo mismo que la columna `GPU` de arriba —el dibujado instanciado
    contra el atlas— pero con la clase que usa el juego, sin duplicar el
    algoritmo de la medición: registra el atlas, encola `cantidad` órdenes
    con su recorte y suelta el lote. La subida del atlas no se mide: ocurre
    una vez, no por fotograma.
    """
    import moderngl

    from src.engine.render.gpu_sprite_batch import SpriteBatchGPU

    ctx = moderngl.create_standalone_context()
    hoja, posiciones = _sprites_de_prueba(cantidad)
    fbo = ctx.simple_framebuffer((ANCHO, ALTO))
    lote = SpriteBatchGPU(ctx, ANCHO, ALTO)
    atlas = lote.registrar_atlas(hoja)
    recortes = [pygame.Rect((i % 4) * LADO, (i // 4) * LADO, LADO, LADO)
                for i in range(16)]
    for n, pos in enumerate(posiciones):
        lote.dibujar(atlas, pos, recortes[n % 16])
    fbo.use()

    def volcar() -> None:
        fbo.clear(0.0, 0.0, 0.0, 1.0)
        lote.volcar()
        ctx.finish()

    resultado = _mediana(volcar)
    lote.destruir()
    ctx.release()
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sprites", type=int, nargs="*",
                        default=[500, 2000, 8000])
    args = parser.parse_args()

    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))

    print(f"{'sprites':>8}  {'blits':>8}  {'blits()':>8}  {'GPU':>8}  "
          f"{'GPU+bajar':>10}  {'lote GPU':>9}")
    tarjeta = "?"
    for cantidad in args.sprites:
        sueltos, lote = medir_cpu(cantidad)
        try:
            gpu, gpu_bajada, tarjeta = medir_gpu(cantidad)
            gpu_txt, bajada_txt = f"{gpu:8.3f}", f"{gpu_bajada:10.3f}"
        except Exception as e:  # pragma: no cover - sin tarjeta utilizable
            gpu_txt, bajada_txt = f"{'n/d':>8}", f"{'n/d':>10}"
            tarjeta = f"sin GPU utilizable ({type(e).__name__}: {e})"
        try:
            lote_txt = f"{medir_lote_gpu(cantidad):9.3f}"
        except Exception as e:  # pragma: no cover - sin tarjeta utilizable
            lote_txt = f"{'n/d':>9}"
            tarjeta = f"sin GPU utilizable ({type(e).__name__}: {e})"
        print(f"{cantidad:8d}  {sueltos:8.3f}  {lote:8.3f}  {gpu_txt}  "
              f"{bajada_txt}  {lote_txt}")

    print(f"\ntarjeta: {tarjeta}")
    # La Quadro de este equipo se presenta sin el prefijo "NVIDIA":
    # ("Quadro M2200/PCIe/SSE2"), así que hay que aceptar ambas marcas.
    if not any(marca in tarjeta.lower() for marca in ("nvidia", "quadro")):
        print(
            "AVISO: no corre en una tarjeta NVIDIA. Asigna python.exe a la "
            "Quadro (Panel de control de NVIDIA o Windows → Pantalla → "
            "Gráficos → Alto rendimiento) o esta medición no vale como "
            "referencia."
        )
    print("Milisegundos, mediana de", REPETICIONES, "pasadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

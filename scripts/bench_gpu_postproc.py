"""
bench_gpu_postproc.py — ¿compensa mover el post-procesado a la GPU?

AUD-148. La respuesta depende de la máquina, así que aquí está la máquina
midiéndose a sí misma.

En el equipo donde se escribió esto —sin GPU, con `SDL_VIDEODRIVER=dummy`— el
bloom en GPU salió **cinco veces más lento** que el de numpy: el renderizador
«acelerado» de SDL cae a software y entonces son los mismos píxeles por CPU
más el coste de subirlos. En un portátil con tarjeta el resultado puede ser el
contrario, y ésa es exactamente la razón de que esto sea un banco de pruebas y
no una afirmación en un documento.

Uso::

    python scripts/bench_gpu_postproc.py

Cómo leerlo
-----------
* **presentar** es lo que costaría enseñar el fotograma por GPU. Si es bajo,
  el camino está abierto.
* **bloom** compara la implementación actual con la de GPU. Si la de GPU gana
  por mucho en tu máquina, merece la pena plantearse el cambio; si no, el
  post-procesado se queda donde está y no pasa nada.

Lo que este banco NO mide, porque no se puede: el filtro de daltonismo mezcla
canales entre sí y el renderizador de SDL2 no tiene shaders. Eso seguirá por
CPU pase lo que pase aquí.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import numpy as np  # noqa: E402
import pygame  # noqa: E402

# AUD-177: imprime `→` y la consola de Windows usa cp1252, que no lo tiene.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ANCHO, ALTO = 800, 600
REPETICIONES = 12


def _medir(funcion, repeticiones: int = REPETICIONES) -> float:
    funcion()
    inicio = time.perf_counter()
    for _ in range(repeticiones):
        funcion()
    return (time.perf_counter() - inicio) / repeticiones * 1000.0


def main() -> int:
    pygame.init()
    from src.engine.render.gpu_present import hay_soporte

    if not hay_soporte():
        print("Esta instalación de pygame no trae `_sdl2`. Nada que medir.")
        return 0

    from pygame._sdl2 import video as sdl2

    ventana = sdl2.Window("banco", size=(ANCHO, ALTO))
    render = sdl2.Renderer(ventana)

    rng = np.random.default_rng(7)
    lienzo = pygame.Surface((ANCHO, ALTO))
    pygame.surfarray.blit_array(
        lienzo, rng.integers(0, 255, (ANCHO, ALTO, 3), dtype=np.uint8))
    textura = sdl2.Texture.from_surface(render, lienzo)

    def subir_y_presentar() -> None:
        t = sdl2.Texture.from_surface(render, lienzo)
        render.clear()
        t.draw()
        render.present()

    def solo_presentar() -> None:
        render.clear()
        textura.draw()
        render.present()

    def bloom_gpu() -> None:
        t = sdl2.Texture.from_surface(render, lienzo)
        render.clear()
        t.draw()
        t.blend_mode = pygame.BLENDMODE_ADD
        t.alpha = 60
        for d in (2, 5, 9):
            t.draw(dstrect=pygame.Rect(-d, -d, ANCHO + 2 * d, ALTO + 2 * d))
        render.present()

    from src.framework.vfx.post_processing import PostProcessing

    post = PostProcessing()

    def bloom_numpy() -> None:
        copia = lienzo.copy()
        post._apply_bloom(copia, ANCHO, ALTO, 0.6)

    print(f"Banco de post-procesado — {ANCHO}×{ALTO}, "
          f"{REPETICIONES} repeticiones\n")
    print(f"  subir textura + presentar   {_medir(subir_y_presentar):6.2f} ms")
    print(f"  presentar ya subida         {_medir(solo_presentar):6.2f} ms")
    numpy_ms = _medir(bloom_numpy)
    gpu_ms = _medir(bloom_gpu)
    print(f"  bloom con numpy (actual)    {numpy_ms:6.2f} ms")
    print(f"  bloom en GPU                {gpu_ms:6.2f} ms")

    print()
    if gpu_ms < numpy_ms * 0.75:
        print("  → En esta máquina la GPU gana con holgura. Merece la pena")
        print("    plantearse mover el post-procesado.")
    elif gpu_ms > numpy_ms:
        print("  → En esta máquina la GPU sale PEOR. Casi seguro que no hay")
        print("    aceleración real: SDL está cayendo a software.")
    else:
        print("  → Empate. Cambiar el motor entero por esto no compensa.")
    print("\n  El filtro de daltonismo seguirá por CPU en cualquier caso:")
    print("  mezcla canales entre sí y el renderizador no tiene shaders.")

    ventana.destroy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

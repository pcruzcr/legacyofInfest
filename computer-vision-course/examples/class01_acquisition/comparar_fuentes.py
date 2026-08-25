#!/usr/bin/env python3
"""
Clase 1 · Demostración del profesor — ¿de dónde sale una imagen?

Cuatro procedencias distintas, el mismo código de proceso detrás. La idea que
tiene que quedar es que **el pipeline no debería enterarse de dónde vino la
imagen**: si tu función de análisis necesita saber si el origen fue una cámara
o un fichero, está mal escrita.

Lo que sí cambia entre fuentes, y hay que mirar:

* el **tamaño** — una webcam da 640×480, un sprite del juego 32×32;
* el **rango dinámico** — un fichero PNG suele venir bien expuesto, una cámara
  no;
* la **transparencia** — sólo la tienen los sprites, y rompe el histograma;
* la **repetibilidad** — un fichero da siempre lo mismo, una cámara nunca.

Ejecutar:
    python examples/class01_acquisition/comparar_fuentes.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Dos rutas, no una: `cvcourse` vive en el curso y `src.*` en la raíz del
# repositorio. Este preámbulo se repite en todos los ejemplos porque no puede
# ir en un módulo importable — es justo lo que hace que los imports funcionen.
CURSO = Path(__file__).resolve().parents[2]
REPO = CURSO.parent
for _ruta in (CURSO, REPO):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import numpy as np

from cvcourse import acquisition, viz

SALIDA = CURSO / "outputs" / "clase01"


def describir(imagen: np.ndarray, nombre: str) -> dict[str, object]:
    """Las cinco cifras con las que se juzga una toma.

    Ninguna es un juicio por sí sola. Juntas dicen si la imagen sirve:

    * `saturados` — píxeles en 255. Información **perdida**: nada distingue un
      blanco de otro más blanco. No se recupera con ningún realce.
    * `negros` — píxeles en 0. Lo mismo por el otro extremo.
    * `rango` — cuánto del [0, 255] se está usando de verdad. Un rango de 40
      significa que toda la imagen cabe en el 16 % de la escala.
    * `media` — dónde está centrada. Ni oscura ni quemada.
    """
    gris = imagen.mean(axis=2) if imagen.ndim == 3 else imagen
    return {
        "fuente": nombre,
        "forma": imagen.shape,
        "tipo": str(imagen.dtype),
        "media": float(gris.mean()),
        "rango": float(gris.max() - gris.min()),
        "saturados_%": float((gris >= 254).mean() * 100),
        "negros_%": float((gris <= 1).mean() * 100),
    }


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)

    # Se pide una de cada tipo. Las que no existan en esta máquina se saltan y
    # se dice cuál faltó: una demostración que finge tener cámara cuando no la
    # hay enseña algo falso.
    candidatas: list[tuple[str, object]] = [
        ("Cámara (webcam)", lambda: acquisition.FuenteCamara(0)),
        ("Motor — sprites del juego", lambda: acquisition.FuenteMotor("sprites")),
        ("Motor — fotograma de escena", lambda: acquisition.FuenteMotor(escena="filter", maximo=1)),
        ("Sintética — pieza industrial", lambda: acquisition.FuenteSintetica(n=1, tamano=128)),
    ]

    imagenes: list[np.ndarray] = []
    titulos: list[str] = []
    informes: list[dict[str, object]] = []

    for nombre, constructor in candidatas:
        try:
            fuente = constructor()  # type: ignore[operator]
        except (OSError, RuntimeError, ImportError) as error:
            print(f"  [no disponible] {nombre}: {error}")
            continue

        with fuente:
            imagen = fuente.leer()
        if imagen is None:
            print(f"  [vacía] {nombre}")
            continue

        imagenes.append(imagen)
        titulos.append(f"{nombre}\n{imagen.shape[1]}×{imagen.shape[0]}")
        informes.append(describir(imagen, nombre))

    if not imagenes:
        print("Ninguna fuente disponible. Algo va muy mal: la sintética no depende de nada.")
        return 1

    print(f"\n{'fuente':32s} {'forma':>18s} {'media':>7s} {'rango':>6s} {'sat%':>6s} {'neg%':>6s}")
    print("-" * 80)
    for inf in informes:
        print(
            f"{inf['fuente']!s:32s} {inf['forma']!s:>18s} "
            f"{inf['media']:>7.1f} {inf['rango']:>6.0f} "
            f"{inf['saturados_%']:>6.2f} {inf['negros_%']:>6.2f}"
        )

    ruta = viz.guardar(
        viz.rejilla(imagenes, titulos, columnas=2,
                    titulo_general="Clase 1 — la misma pregunta, cuatro procedencias"),
        SALIDA / "comparar_fuentes.png",
    )
    print(f"\nFigura: {ruta}")

    # La observación que abre el laboratorio. El fotograma de escena y el
    # sprite salen del mismo motor y no se parecen en nada: uno es una captura
    # de pantalla de 800×600 con texto de interfaz, el otro un dibujo de 32×32
    # con transparencia. «Del motor» no describe una imagen.
    print(
        "\nPara discutir: ¿cuál de estas cuatro imágenes NO se puede volver a\n"
        "obtener idéntica mañana, y qué consecuencia tiene eso para un\n"
        "laboratorio que hay que corregir?"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

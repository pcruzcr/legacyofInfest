#!/usr/bin/env python3
"""
Clase 1 · Mecatrónica — el histograma como criterio de aceptación de la toma.

La idea que hay detrás
-----------------------
En un laboratorio, el histograma se dibuja y se mira. En una célula robotizada
**nadie lo mira**: la cámara toma una imagen cada 200 ms y el robot decide.
Así que el histograma tiene que dejar de ser un gráfico y convertirse en un
número con un umbral, es decir, en una **decisión automática**.

La pregunta operativa es: *¿esta toma sirve para localizar la pieza, o hay que
volver a tomarla?* Rechazar una imagen mala cuesta 200 ms. Procesarla y darle
al robot una coordenada equivocada cuesta una pieza, y a veces una pinza.

Los cuatro criterios que se implementan aquí son los del ejemplo anterior,
ahora con umbral:

| Criterio | Rechaza porque |
|---|---|
| saturación | los píxeles en 255 han perdido la información: no se recupera |
| subexposición | lo mismo por el extremo negro |
| rango dinámico | toda la escena cabe en una franja estrecha: no hay contraste que segmentar |
| media | la escena está globalmente oscura o quemada |

El orden importa: **primero se decide si la imagen sirve, después se procesa**.
Al revés se gasta el presupuesto de tiempo en imágenes que había que tirar.

Ejecutar:
    python examples/class01_acquisition/mechatronics/aceptacion_de_toma.py
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
REPO = CURSO.parent
for _ruta in (CURSO, REPO):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import numpy as np

from cvcourse import synthetic, viz

SALIDA = CURSO / "outputs" / "clase01"


@dataclass(frozen=True)
class Criterios:
    """Los umbrales de aceptación. Son parámetros de la célula, no constantes.

    Van en una dataclase y no como números sueltos en el código por una razón
    práctica: cuando cambia la iluminación de la planta hay que reajustarlos, y
    lo que se reajusta tiene que estar en un sitio, no repartido por seis
    funciones.
    """

    max_saturados_pct: float = 2.0
    max_negros_pct: float = 5.0
    min_rango: float = 60.0
    media_valida: tuple[float, float] = (40.0, 215.0)


@dataclass(frozen=True)
class Veredicto:
    aceptada: bool
    motivos: tuple[str, ...]
    medidas: dict[str, float]


def evaluar(imagen: np.ndarray, criterios: Criterios | None = None) -> Veredicto:
    """Decide si la toma sirve. Devuelve **por qué**, no sólo sí o no.

    Devolver los motivos no es cortesía: en producción, «rechazada» a secas no
    permite corregir nada. «Rechazada por saturación» manda a bajar la
    exposición; «rechazada por rango» manda a revisar la iluminación. Son dos
    acciones distintas del operario.

    El valor por defecto es `None` y no `Criterios()` porque un objeto en la
    firma se construye **una sola vez**, al definir la función, y queda
    compartido por todas las llamadas. Con una dataclase congelada como esta no
    haría daño, pero es un hábito que con una lista o un diccionario produce
    uno de los errores más difíciles de ver en Python.
    """
    criterios = criterios or Criterios()
    gris = imagen.mean(axis=2) if imagen.ndim == 3 else imagen.astype(float)

    medidas = {
        "saturados_pct": float((gris >= 254).mean() * 100),
        "negros_pct": float((gris <= 1).mean() * 100),
        "rango": float(gris.max() - gris.min()),
        "media": float(gris.mean()),
    }

    motivos: list[str] = []
    if medidas["saturados_pct"] > criterios.max_saturados_pct:
        motivos.append(f"saturación {medidas['saturados_pct']:.1f}% > {criterios.max_saturados_pct}%")
    if medidas["negros_pct"] > criterios.max_negros_pct:
        motivos.append(f"subexposición {medidas['negros_pct']:.1f}% > {criterios.max_negros_pct}%")
    if medidas["rango"] < criterios.min_rango:
        motivos.append(f"rango {medidas['rango']:.0f} < {criterios.min_rango:.0f}")
    bajo, alto = criterios.media_valida
    if not bajo <= medidas["media"] <= alto:
        motivos.append(f"media {medidas['media']:.0f} fuera de [{bajo:.0f}, {alto:.0f}]")

    return Veredicto(aceptada=not motivos, motivos=tuple(motivos), medidas=medidas)


# ── Simulación de la mesa de trabajo ──────────────────────────────────────

def tomas_de_la_celula() -> list[tuple[str, np.ndarray]]:
    """Seis tomas de la misma escena con seis problemas distintos.

    Se simulan a partir de una imagen buena en vez de buscar fotos reales
    porque así **sabemos** qué le pasa a cada una, y el estudiante puede
    comprobar si el criterio detectó lo que se le metió a propósito.
    """
    base, _ = synthetic.pieza_individual(tamano=192, clase="OK", forma="rectangulo", semilla=1)
    base = base.astype(float)
    rng = np.random.default_rng(1)

    return [
        ("correcta", base),
        # Exposición al alza: se recorta arriba y se pierde el borde de la pieza.
        ("sobreexpuesta", base * 2.4),
        ("subexpuesta", base * 0.25),
        # Diafragma cerrado + poca luz: la imagen es toda gris medio.
        ("sin contraste", base * 0.25 + 100),
        # La lámpara del techo entra directa en el sensor.
        ("reflejo especular", _con_reflejo(base, rng)),
        # Ganancia del sensor subida para compensar poca luz. La sigma está
        # elegida para que la imagen quede claramente sucia **sin** llegar a
        # saturar: es el contraejemplo del cierre, y si saturara lo cazaría el
        # primer criterio y dejaría de demostrar nada.
        ("ruido de ganancia", base + rng.normal(0, 18, base.shape)),
    ]


def _con_reflejo(base: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Un brillo saturado en una esquina, como el de una lámpara."""
    imagen = base.copy()
    alto, ancho = imagen.shape
    filas, columnas = np.ogrid[:alto, :ancho]
    centro = (alto * 0.28, ancho * 0.30)
    radio = min(alto, ancho) * 0.20
    mancha = ((filas - centro[0]) ** 2 + (columnas - centro[1]) ** 2) <= radio**2
    imagen[mancha] = 255.0
    return imagen + rng.normal(0, 1.0, imagen.shape)


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    criterios = Criterios()

    imagenes: list[np.ndarray] = []
    titulos: list[str] = []

    print(f"\n{'toma':20s} {'sat%':>6s} {'neg%':>6s} {'rango':>6s} {'media':>6s}  veredicto")
    print("-" * 78)
    for nombre, cruda in tomas_de_la_celula():
        imagen = np.clip(cruda, 0, 255).astype(np.uint8)
        v = evaluar(imagen, criterios)
        m = v.medidas
        estado = "ACEPTA" if v.aceptada else "RECHAZA"
        print(
            f"{nombre:20s} {m['saturados_pct']:>6.1f} {m['negros_pct']:>6.1f} "
            f"{m['rango']:>6.0f} {m['media']:>6.0f}  {estado}"
            + (f" — {v.motivos[0]}" if v.motivos else "")
        )
        for motivo in v.motivos[1:]:
            print(f"{'':52s}   y {motivo}")

        imagenes.append(imagen)
        titulos.append(f"{nombre}\n{estado}")

    ruta = viz.guardar(
        viz.rejilla(imagenes, titulos, columnas=3,
                    titulo_general="Aceptación de toma — decidir antes de procesar"),
        SALIDA / "aceptacion_de_toma.png",
    )
    print(f"\nFigura: {ruta}")

    print(
        "\nPara discutir: la toma con 'ruido de ganancia' pasa los cuatro\n"
        "criterios y sin embargo es mala. ¿Qué mide un histograma y qué NO\n"
        "puede medir? ¿Qué haría falta para detectar ese caso — y de qué\n"
        "clase de este curso saldrá la herramienta?"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

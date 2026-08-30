"""
De una máscara a una tabla de números: el `features.csv` de la Clase 3.

Qué problema resuelve
---------------------
La Clase 3 termina con un fichero de características y **sin entrenar nada**.
Ese orden es deliberado: si el modelo llega antes de que el estudiante haya
mirado las columnas, el aprendizaje automático se vuelve una caja negra que
escupe un número. Primero se mira qué información hay; en la Clase 4 se ve qué
puede hacer un modelo con ella.

Relación con `VisionTools` del motor
------------------------------------
`VisionTools.analyze_regions` ya devuelve `RegionInfo` con `label`, `area`,
`centroid`, `bounding_rect`, `eccentricity`, `solidity` y `perimeter`. Le
faltan las cuatro que pide el temario: `width`, `height`, `aspect_ratio` y
`circularity`. Las cuatro se derivan de lo que ya hay, así que este módulo las
calcula en vez de tocar el motor.

Hay dos caminos de entrada, a propósito:

* `caracteristicas_de_etiquetas(...)` — desde una máscara etiquetada (NumPy +
  scikit-image). Funciona en Colab sin el repositorio del motor.
* `desde_region_info(...)` — desde el `RegionInfo` del motor, para el
  laboratorio que trabaja dentro del juego.

Los dos producen exactamente la misma fila. Si dieran resultados distintos, el
estudiante que compara su cuaderno con el laboratorio del motor tendría razón
al desconfiar de los dos.
"""
from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import numpy as np

__all__ = [
    "COLUMNAS",
    "Caracteristicas",
    "a_matriz",
    "caracteristicas_de_etiquetas",
    "caracteristicas_de_mascara",
    "desde_region_info",
    "guardar_csv",
]


@dataclass(frozen=True)
class Caracteristicas:
    """Una fila de `features.csv`: un objeto medido.

    El orden de los campos es el del temario (§Clase 3), no el alfabético: la
    tabla se lee de izquierda a derecha como se explicó en la pizarra.
    """

    object_id: int
    area: float
    perimeter: float
    width: float
    height: float
    aspect_ratio: float
    circularity: float
    # Las tres siguientes no las pide el guion pero salen gratis de
    # `regionprops` y son las que mejor separan la deformación de una pieza
    # sana (ver `synthetic._deformar`). Dejarlas fuera obligaría a recalcular
    # todo el CSV en la Clase 4.
    eccentricity: float
    solidity: float
    extent: float
    centroid_x: float
    centroid_y: float
    label: str = ""


#: Cabecera del CSV, derivada de la dataclase para que no puedan divergir.
COLUMNAS: tuple[str, ...] = tuple(f.name for f in fields(Caracteristicas))


def _circularidad(area: float, perimetro: float) -> float:
    """4πA / P². Vale 1 en un círculo perfecto y baja al alejarse de él.

    Con perímetro 0 —una región de un solo píxel— la fórmula divide por cero.
    Devolver 0.0 en ese caso no es «tapar el error»: una región de un píxel no
    tiene forma que medir, y propagar un `inf` o un `nan` a la tabla rompe el
    entrenamiento de la Clase 4 muy lejos de aquí, donde ya no hay forma de
    saber de dónde salió.
    """
    if perimetro <= 0.0:
        return 0.0
    return float(4.0 * math.pi * area / (perimetro**2))


def _fila(
    object_id: int,
    area: float,
    perimetro: float,
    alto: float,
    ancho: float,
    excentricidad: float,
    solidez: float,
    extension: float,
    centroide: tuple[float, float],
    etiqueta: str,
) -> Caracteristicas:
    return Caracteristicas(
        object_id=int(object_id),
        area=float(area),
        perimeter=float(perimetro),
        width=float(ancho),
        height=float(alto),
        aspect_ratio=float(ancho / alto) if alto > 0 else 0.0,
        circularity=_circularidad(area, perimetro),
        eccentricity=float(excentricidad),
        solidity=float(solidez),
        extent=float(extension),
        centroid_x=float(centroide[1]),
        centroid_y=float(centroide[0]),
        label=str(etiqueta),
    )


def caracteristicas_de_etiquetas(
    etiquetas: np.ndarray,
    etiqueta_de_clase: str = "",
    area_minima: int = 20,
) -> list[Caracteristicas]:
    """Mide cada región de una máscara **etiquetada** (salida de `label`).

    `area_minima` descarta el picoteo que deja cualquier umbral: motas de dos
    o tres píxeles que no son objetos sino ruido que sobrevivió. Sin este
    filtro, una imagen normal produce cientos de filas basura y la tabla de la
    Clase 3 deja de poder leerse a ojo, que es justo para lo que sirve.
    """
    from skimage.measure import regionprops

    etiquetas = np.asarray(etiquetas)
    if etiquetas.ndim != 2:
        raise ValueError(f"se esperaba una imagen 2D de etiquetas, no {etiquetas.shape}")

    filas: list[Caracteristicas] = []
    for region in regionprops(etiquetas.astype(np.int32)):
        if region.area < area_minima:
            continue
        f0, c0, f1, c1 = region.bbox
        filas.append(
            _fila(
                object_id=int(region.label),
                area=float(region.area),
                perimetro=float(region.perimeter),
                alto=float(f1 - f0),
                ancho=float(c1 - c0),
                excentricidad=float(region.eccentricity),
                solidez=float(region.solidity),
                extension=float(region.extent),
                centroide=(float(region.centroid[0]), float(region.centroid[1])),
                etiqueta=etiqueta_de_clase,
            )
        )
    return filas


def caracteristicas_de_mascara(
    mascara: np.ndarray,
    etiqueta_de_clase: str = "",
    area_minima: int = 20,
) -> list[Caracteristicas]:
    """Igual que la anterior, pero partiendo de una máscara binaria.

    Etiqueta primero con `skimage.measure.label` (conectividad 2, es decir
    incluyendo diagonales) y luego mide. Es el camino corto para el 90 % de los
    laboratorios, que llegan aquí con una máscara de Otsu.
    """
    from skimage.measure import label

    mascara = np.asarray(mascara)
    binaria = mascara > 0 if mascara.dtype != bool else mascara
    return caracteristicas_de_etiquetas(
        label(binaria, connectivity=2), etiqueta_de_clase, area_minima
    )


def desde_region_info(region, etiqueta_de_clase: str = "") -> Caracteristicas:
    """Convierte un `RegionInfo` del motor en la misma fila.

    Se accede por atributos y no se importa el tipo para no arrastrar pygame a
    un módulo que tiene que funcionar en Colab sin el repositorio. El motor no
    expone `extent`, así que se deriva: área entre el área de su caja.
    """
    rect = region.bounding_rect
    ancho, alto = float(rect.width), float(rect.height)
    area = float(region.area)
    area_caja = ancho * alto
    return _fila(
        object_id=int(region.label),
        area=area,
        perimetro=float(region.perimeter),
        alto=alto,
        ancho=ancho,
        excentricidad=float(region.eccentricity),
        solidez=float(region.solidity),
        extension=area / area_caja if area_caja > 0 else 0.0,
        centroide=(float(region.centroid[1]), float(region.centroid[0])),
        etiqueta=etiqueta_de_clase,
    )


def guardar_csv(filas: list[Caracteristicas], ruta: str | Path) -> Path:
    """Escribe `features.csv`. Devuelve la ruta escrita.

    Usa el módulo `csv` de la biblioteca estándar y no pandas a propósito: el
    curso recomienda pandas, pero un aula sin permisos de instalación tiene que
    poder terminar la Clase 3 igualmente. Leerlo con pandas después funciona
    exactamente igual.

    `newline=""` no es adorno: sin él, en Windows el módulo `csv` escribe
    `\\r\\r\\n` y el fichero sale con una línea en blanco entre cada dos filas.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=list(COLUMNAS))
        escritor.writeheader()
        for fila in filas:
            escritor.writerow(asdict(fila))
    return ruta


def a_matriz(
    filas: list[Caracteristicas],
    columnas: tuple[str, ...] | None = None,
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    """`list[Caracteristicas]` → `(X, y, nombres_de_columna)` para scikit-learn.

    Es el puente exacto entre la Clase 3 y la Clase 4: lo que sale de aquí es
    lo que entra en `PatternRecognitionTools.train`.

    Por defecto se excluyen `object_id`, `centroid_x` y `centroid_y`. El
    identificador no es una medida del objeto, y **el centroide es dónde está
    la pieza, no cómo es**: un modelo entrenado con él aprende que «las piezas
    de la izquierda son defectuosas» si el generador las puso ahí. Es fuga de
    información, y es uno de los errores que la Clase 4 enseña a detectar —
    quitarlo por defecto y explicarlo vale más que descubrirlo con una
    *accuracy* del 100 % que no significa nada.
    """
    if not filas:
        raise ValueError("no hay filas de las que construir la matriz")

    if columnas is None:
        columnas = tuple(
            c for c in COLUMNAS
            if c not in ("object_id", "label", "centroid_x", "centroid_y")
        )

    desconocidas = set(columnas) - set(COLUMNAS)
    if desconocidas:
        raise ValueError(f"columnas desconocidas: {sorted(desconocidas)}")

    X = np.array(
        [[float(getattr(fila, c)) for c in columnas] for fila in filas],
        dtype=np.float32,
    )
    y = np.array([fila.label for fila in filas], dtype=object)
    return X, y, tuple(columnas)

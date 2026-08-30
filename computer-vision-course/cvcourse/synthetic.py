"""
Piezas industriales sintéticas, deterministas y con verdad-terreno exacta.

Por qué sintético y no un dataset descargado
--------------------------------------------
Tres cosas que ninguna descarga da:

1. **Verdad-terreno exacta.** Sabemos dónde pusimos el defecto porque lo
   pusimos nosotros. La métrica del estudiante se compara contra la realidad,
   no contra la etiqueta de otro que quizá se equivocó.
2. **Reproducibilidad.** Semilla fija ⇒ las 30 máquinas del aula generan los
   mismos píxeles. Un laboratorio cuyos números cambian de un portátil a otro
   no se puede corregir ni discutir.
3. **Control del eje de dificultad.** Se sube el ruido y se ve caer la
   *accuracy*. Ese es el experimento de la Clase 4, y con imágenes reales sólo
   se puede observar, no provocar.

Lo que hay que decirle al estudiante, y el material se lo dice
--------------------------------------------------------------
Un dataset sintético **no sustituye** a imágenes reales. Aquí el ruido es
gaussiano y homogéneo, la iluminación es uniforme y los defectos tienen tres
formas. Un sistema entrenado sólo con esto se estrella el primer día en una
planta. Sirve para aprender el método, no para desplegar.

Sin dependencias más allá de NumPy: estos generadores tienen que funcionar en
Colab sin el repositorio del motor clonado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

__all__ = [
    "CLASES",
    "DEFECTOS",
    "Pieza",
    "lote_de_piezas",
    "pieza_individual",
    "piezas_en_contacto",
]

#: Las dos clases del problema de inspección. Deliberadamente binario: la
#: Clase 4 mide el coste de un falso negativo, y eso se ve mucho mejor con dos
#: clases que con siete.
CLASES: tuple[str, ...] = ("OK", "NO_OK")

#: Los tres modos de fallo. Se eligieron porque cada uno se ve mejor con una
#: técnica distinta: la grieta con detección de bordes, la mota con umbral, y
#: la deformación con características geométricas (circularidad, solidez).
DEFECTOS: tuple[str, ...] = ("grieta", "mota", "deformacion")

_GRIS_BANDA = 70      # la banda transportadora, oscura
_GRIS_PIEZA = 185     # el metal, claro
_GRIS_DEFECTO = 45    # el defecto, más oscuro que la pieza


@dataclass(frozen=True)
class Pieza:
    """Una pieza y su verdad-terreno.

    `bbox` va en (fila_min, columna_min, fila_max, columna_max), el mismo
    convenio que `skimage.measure.regionprops`, para que comparar la detección
    con la verdad no exija traducir entre dos formatos.
    """

    id: int
    bbox: tuple[int, int, int, int]
    clase: Literal["OK", "NO_OK"]
    defecto: str | None
    forma: str
    centro: tuple[float, float]
    radio: float = 0.0
    metadatos: dict[str, float] = field(default_factory=dict)


# ── Primitivas de dibujo ──────────────────────────────────────────────────

def _rejilla(alto: int, ancho: int) -> tuple[np.ndarray, np.ndarray]:
    filas = np.arange(alto)[:, None]
    columnas = np.arange(ancho)[None, :]
    return filas, columnas


def _mascara_circulo(alto: int, ancho: int, centro: tuple[float, float], radio: float) -> np.ndarray:
    filas, columnas = _rejilla(alto, ancho)
    cf, cc = centro
    return ((filas - cf) ** 2 + (columnas - cc) ** 2) <= radio**2


def _mascara_rectangulo(alto: int, ancho: int, bbox: tuple[int, int, int, int]) -> np.ndarray:
    f0, c0, f1, c1 = bbox
    mascara = np.zeros((alto, ancho), dtype=bool)
    mascara[max(f0, 0):max(f1, 0), max(c0, 0):max(c1, 0)] = True
    return mascara


def _fondo_de_banda(alto: int, ancho: int, rng: np.random.Generator) -> np.ndarray:
    """Banda transportadora: gris con un degradado suave de iluminación.

    El degradado no es decorativo. Es lo que hace que un **umbral fijo** falle
    en un extremo de la imagen y Otsu no: sin él, la Clase 3 no tendría forma
    de enseñar por qué existe Otsu.
    """
    _, columnas = _rejilla(alto, ancho)
    degradado = 12.0 * (columnas / max(ancho - 1, 1)) - 6.0
    fondo = np.full((alto, ancho), float(_GRIS_BANDA)) + degradado
    fondo += rng.normal(0.0, 2.0, size=(alto, ancho))
    return fondo


def _aplicar_ruido(imagen: np.ndarray, sigma: float, rng: np.random.Generator) -> np.ndarray:
    if sigma <= 0:
        return imagen
    return imagen + rng.normal(0.0, sigma, size=imagen.shape)


def _a_uint8(imagen: np.ndarray) -> np.ndarray:
    return np.clip(imagen, 0, 255).astype(np.uint8)


# ── Defectos ──────────────────────────────────────────────────────────────

def _dibujar_grieta(
    imagen: np.ndarray, mascara_pieza: np.ndarray, rng: np.random.Generator
) -> None:
    """Una línea fina y oscura: se detecta por gradiente, no por umbral.

    Se dibuja como una polilínea de pocos puntos y no como un segmento recto
    porque una grieta recta la encuentra cualquier cosa; el objetivo es que el
    estudiante tenga que suavizar antes de derivar.
    """
    filas, columnas = np.nonzero(mascara_pieza)
    if filas.size == 0:
        return
    f0, f1 = int(filas.min()), int(filas.max())
    c0, c1 = int(columnas.min()), int(columnas.max())

    n = 5
    puntos_f = np.linspace(f0 + 2, f1 - 2, n) + rng.normal(0, (f1 - f0) * 0.06, n)
    puntos_c = np.linspace(c0 + 2, c1 - 2, n) + rng.normal(0, (c1 - c0) * 0.06, n)

    for i in range(n - 1):
        pasos = 60
        ff = np.linspace(puntos_f[i], puntos_f[i + 1], pasos).round().astype(int)
        cc = np.linspace(puntos_c[i], puntos_c[i + 1], pasos).round().astype(int)
        for df in (-1, 0, 1):  # grosor de 3 px: por debajo desaparece al suavizar
            f = np.clip(ff + df, 0, imagen.shape[0] - 1)
            c = np.clip(cc, 0, imagen.shape[1] - 1)
            dentro = mascara_pieza[f, c]
            imagen[f[dentro], c[dentro]] = _GRIS_DEFECTO


def _dibujar_mota(
    imagen: np.ndarray, mascara_pieza: np.ndarray, rng: np.random.Generator
) -> None:
    """Un disco oscuro: cae con un umbral simple, y por eso es el defecto fácil."""
    filas, columnas = np.nonzero(mascara_pieza)
    if filas.size == 0:
        return
    i = int(rng.integers(filas.size))
    radio = float(rng.uniform(3.0, 6.0))
    disco = _mascara_circulo(*imagen.shape[:2], (float(filas[i]), float(columnas[i])), radio)
    imagen[disco & mascara_pieza] = _GRIS_DEFECTO


def _deformar(mascara_pieza: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Muerde una esquina de la pieza.

    Este defecto no cambia el histograma: la pieza sigue siendo igual de clara.
    Sólo se detecta **midiendo la forma** —solidez, circularidad—, que es
    exactamente lo que la Clase 3 extrae y la Clase 4 usa. Es el defecto que
    justifica todo el bloque de características geométricas.
    """
    filas, columnas = np.nonzero(mascara_pieza)
    if filas.size == 0:
        return mascara_pieza
    f0, f1 = int(filas.min()), int(filas.max())
    c0, c1 = int(columnas.min()), int(columnas.max())
    alto, ancho = mascara_pieza.shape

    lado = max(int(min(f1 - f0, c1 - c0) * rng.uniform(0.30, 0.45)), 4)
    esquina = int(rng.integers(4))
    if esquina == 0:
        bbox = (f0, c0, f0 + lado, c0 + lado)
    elif esquina == 1:
        bbox = (f0, c1 - lado, f0 + lado, c1)
    elif esquina == 2:
        bbox = (f1 - lado, c0, f1, c0 + lado)
    else:
        bbox = (f1 - lado, c1 - lado, f1, c1)

    return mascara_pieza & ~_mascara_rectangulo(alto, ancho, bbox)


# ── Generadores públicos ──────────────────────────────────────────────────

def pieza_individual(
    tamano: int = 128,
    clase: str = "OK",
    defecto: str | None = None,
    forma: str = "rectangulo",
    ruido: float = 3.0,
    semilla: int = 0,
) -> tuple[np.ndarray, Pieza]:
    """Una pieza centrada sobre la banda, en gris (alto, ancho) uint8.

    Devuelve la imagen y su verdad-terreno. Si `clase` es ``"NO_OK"`` y no se
    da `defecto`, se elige uno de los tres al azar (con la semilla dada, así
    que sigue siendo reproducible).
    """
    if clase not in CLASES:
        raise ValueError(f"clase debe ser una de {CLASES}, no {clase!r}")
    if defecto is not None and defecto not in DEFECTOS:
        raise ValueError(f"defecto debe ser uno de {DEFECTOS} o None, no {defecto!r}")
    if forma not in ("rectangulo", "circulo"):
        raise ValueError(f"forma debe ser 'rectangulo' o 'circulo', no {forma!r}")

    rng = np.random.default_rng(semilla)
    imagen = _fondo_de_banda(tamano, tamano, rng)

    margen = int(tamano * 0.18)
    centro = (tamano / 2.0, tamano / 2.0)
    if forma == "circulo":
        radio = (tamano - 2 * margen) / 2.0
        mascara = _mascara_circulo(tamano, tamano, centro, radio)
    else:
        radio = 0.0
        mascara = _mascara_rectangulo(
            tamano, tamano, (margen, margen, tamano - margen, tamano - margen)
        )

    if clase == "NO_OK" and defecto is None:
        defecto = str(rng.choice(DEFECTOS))
    if clase == "OK":
        defecto = None

    if defecto == "deformacion":
        mascara = _deformar(mascara, rng)

    imagen[mascara] = float(_GRIS_PIEZA)

    if defecto == "grieta":
        _dibujar_grieta(imagen, mascara, rng)
    elif defecto == "mota":
        _dibujar_mota(imagen, mascara, rng)

    imagen = _a_uint8(_aplicar_ruido(imagen, ruido, rng))

    filas, columnas = np.nonzero(mascara)
    bbox = (int(filas.min()), int(columnas.min()), int(filas.max()) + 1, int(columnas.max()) + 1)
    verdad = Pieza(
        id=0,
        bbox=bbox,
        clase=clase,  # type: ignore[arg-type]
        defecto=defecto,
        forma=forma,
        centro=centro,
        radio=radio,
        metadatos={"area_verdadera": float(mascara.sum()), "ruido": float(ruido)},
    )
    return imagen, verdad


def lote_de_piezas(
    n: int = 30,
    tamano: int = 128,
    proporcion_defectuosas: float = 0.4,
    ruido: float = 3.0,
    semilla: int = 0,
) -> tuple[list[np.ndarray], list[Pieza]]:
    """Un lote de inspección: `n` imágenes con su verdad-terreno.

    Es el dataset de las Clases 3 y 4 en el contexto industrial. La proporción
    de defectuosas es un parámetro y no una constante porque el desbalanceo de
    clases es parte del temario: con un 5 % de defectos, un clasificador que
    diga siempre «OK» acierta el 95 % y no sirve para nada. Eso se enseña
    bajándole el valor a este argumento.
    """
    if n < 1:
        raise ValueError(f"n debe ser >= 1, no {n}")
    if not 0.0 <= proporcion_defectuosas <= 1.0:
        raise ValueError(
            f"proporcion_defectuosas debe estar en [0, 1], no {proporcion_defectuosas}"
        )

    rng = np.random.default_rng(semilla)
    n_malas = round(n * proporcion_defectuosas)
    clases = ["NO_OK"] * n_malas + ["OK"] * (n - n_malas)
    rng.shuffle(clases)

    imagenes: list[np.ndarray] = []
    verdades: list[Pieza] = []
    for i, clase in enumerate(clases):
        forma = "circulo" if rng.random() < 0.35 else "rectangulo"
        # Semilla derivada: cada pieza es reproducible por separado, y aun así
        # el lote entero depende de una sola semilla.
        imagen, verdad = pieza_individual(
            tamano=tamano,
            clase=clase,
            forma=forma,
            ruido=ruido,
            semilla=int(semilla) * 10_000 + i,
        )
        imagenes.append(imagen)
        verdades.append(
            Pieza(
                id=i,
                bbox=verdad.bbox,
                clase=verdad.clase,
                defecto=verdad.defecto,
                forma=verdad.forma,
                centro=verdad.centro,
                radio=verdad.radio,
                metadatos=verdad.metadatos,
            )
        )
    return imagenes, verdades


def piezas_en_contacto(
    n: int = 5,
    tamano: int = 256,
    ruido: float = 3.0,
    semilla: int = 0,
) -> tuple[np.ndarray, list[Pieza]]:
    """Piezas circulares que **se tocan**: el caso que obliga a usar watershed.

    Es el ejemplo central de la Clase 3. Un umbral —por bueno que sea— produce
    aquí una sola mancha conexa, así que `connected_components` cuenta 1 donde
    hay `n`. No es un fallo del umbral: es que contar objetos y separarlos son
    dos problemas distintos, y esta imagen lo demuestra en vez de contarlo.

    Los círculos se colocan en fila con solape garantizado; devolvemos el
    centro y el radio de cada uno para poder medir si el watershed acertó.
    """
    if n < 2:
        raise ValueError(f"hacen falta al menos 2 piezas para que se toquen, no {n}")

    rng = np.random.default_rng(semilla)
    imagen = _fondo_de_banda(tamano, tamano, rng)

    radio = tamano / (n + 1.4) / 2.0 * 1.35
    paso = 2.0 * radio * 0.82          # < 2r ⇒ solape asegurado
    ancho_total = paso * (n - 1)
    c0 = (tamano - ancho_total) / 2.0

    verdades: list[Pieza] = []
    for i in range(n):
        cf = tamano / 2.0 + float(rng.uniform(-radio * 0.15, radio * 0.15))
        cc = c0 + i * paso
        mascara = _mascara_circulo(tamano, tamano, (cf, cc), radio)
        imagen[mascara] = float(_GRIS_PIEZA)
        verdades.append(
            Pieza(
                id=i,
                bbox=(
                    int(max(cf - radio, 0)),
                    int(max(cc - radio, 0)),
                    int(min(cf + radio, tamano - 1)) + 1,
                    int(min(cc + radio, tamano - 1)) + 1,
                ),
                clase="OK",
                defecto=None,
                forma="circulo",
                centro=(float(cf), float(cc)),
                radio=float(radio),
            )
        )

    return _a_uint8(_aplicar_ruido(imagen, ruido, rng)), verdades

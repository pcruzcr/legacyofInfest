"""
Module: edge_detection
System: framework.processing
Academic Unit: Unidad VII — Detección de bordes

Sobel y Canny escritos paso a paso, para leerlos.

F2.3 — por qué existe este módulo
---------------------------------
`FilterTools.sobel_edge` llamaba a `cv2.Sobel` y `FilterTools.canny_edge` a
`cv2.Canny`. Funcionan, son rápidos y son lo que se usa en la industria. Pero
en las Unidades VII y VIII **Sobel y Canny son el contenido**, no una
herramienta: un estudiante que abre el laboratorio ve el efecto y aprende la
API, no el algoritmo. La distancia entre "sé que existe `cv2.Canny`" y "sé por
qué la supresión no máxima adelgaza el borde" es la asignatura entera.

Aquí está cada paso separado, con nombre y con su propia función, para que se
pueda leer, probar y romper por partes:

  Sobel   ->  gris, dos convoluciones, magnitud
  Canny   ->  suavizado, gradiente, supresión no máxima, doble umbral,
              histéresis

La versión de OpenCV **no se elimina**. Sigue en `FilterTools` y el laboratorio
muestra las dos, lado a lado, con sus tiempos: comparar tu implementación con
la de referencia es parte de aprender, y descubrir que la tuya es veinte veces
más lenta también.

Todo está vectorizado con numpy. Un bucle de Python sobre 57.600 píxeles cuesta
cientos de milisegundos —está medido en `noise_lab_scene`, donde tumbó la
escena a 3,4 FPS— y una lección que no se puede ejecutar en vivo no se ve.
"""
from __future__ import annotations

import numpy as np

#: Núcleos de Sobel. `KERNEL_X` responde a bordes verticales porque deriva en
#: horizontal; es el error de signo más frecuente al implementarlo.
KERNEL_X: np.ndarray = np.array(
    [[-1, 0, 1],
     [-2, 0, 2],
     [-1, 0, 1]], dtype=np.float32,
)
KERNEL_Y: np.ndarray = np.array(
    [[-1, -2, -1],
     [0,  0,  0],
     [1,  2,  1]], dtype=np.float32,
)

#: Coeficientes de luma ITU-R BT.601. Son los mismos que usa el bloom del
#: post-procesado, y no es casualidad: los dos preguntan "cuánta luz hay aquí".
LUMA = (0.299, 0.587, 0.114)


def a_gris(rgb: np.ndarray) -> np.ndarray:
    """Convierte una imagen RGB a luminancia, en float32.

    Se devuelve float y no uint8 a propósito: los pasos siguientes restan y
    dividen, y hacerlo en enteros de 8 bits desborda en silencio. Ése fue
    exactamente el defecto AUD-086 del sistema de iluminación, donde
    `216 * 255` daba 40 y todos los focos salían negros.
    """
    arr = rgb.astype(np.float32)
    return LUMA[0] * arr[..., 0] + LUMA[1] * arr[..., 1] + LUMA[2] * arr[..., 2]


def convolucionar(imagen: np.ndarray, nucleo: np.ndarray) -> np.ndarray:
    """Convolución 2D con bordes replicados, sin dependencias externas.

    Es la operación de la Unidad VII. Se implementa desplazando la imagen una
    vez por cada peso del núcleo y acumulando: para un núcleo de 3x3 son nueve
    sumas de matrices completas, que numpy hace a velocidad de C.

    El borde se replica (`edge`) en vez de rellenarse con ceros porque un
    relleno de ceros inventa un borde artificial en el marco de la imagen, y
    entonces Sobel detecta el marco.
    """
    k = nucleo.shape[0]
    r = k // 2
    relleno = np.pad(imagen, r, mode="edge")
    salida = np.zeros_like(imagen, dtype=np.float32)
    alto, ancho = imagen.shape
    for i in range(k):
        for j in range(k):
            peso = nucleo[i, j]
            if peso == 0.0:
                continue
            salida += peso * relleno[i:i + alto, j:j + ancho]
    return salida


def gradiente(gris: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Magnitud y dirección del gradiente. La dirección va en radianes."""
    gx = convolucionar(gris, KERNEL_X)
    gy = convolucionar(gris, KERNEL_Y)
    return np.hypot(gx, gy), np.arctan2(gy, gx)


def sobel(rgb: np.ndarray) -> np.ndarray:
    """Bordes por Sobel. Devuelve una imagen de un canal en uint8.

    Tres pasos: pasar a gris, derivar en las dos direcciones, y quedarse con
    la magnitud. Eso es todo lo que hace `cv2.Sobel` seguido de
    `cv2.magnitude`.
    """
    magnitud, _ = gradiente(a_gris(rgb))
    return np.clip(magnitud, 0, 255).astype(np.uint8)


def _gauss_1d(sigma: float) -> np.ndarray:
    radio = max(1, round(3 * sigma))
    x = np.arange(-radio, radio + 1, dtype=np.float32)
    nucleo = np.exp(-(x ** 2) / (2.0 * sigma ** 2))
    return nucleo / nucleo.sum()


def suavizar(gris: np.ndarray, sigma: float) -> np.ndarray:
    """Desenfoque gaussiano separable.

    Separable significa que una gaussiana 2D es el producto de dos 1D, así que
    en vez de un núcleo de NxN se pasan dos de N. Para sigma 1,4 eso son 18
    multiplicaciones por píxel en lugar de 81.

    Canny empieza suavizando porque el gradiente amplifica el ruido: derivar
    una imagen ruidosa da bordes por todas partes.
    """
    nucleo = _gauss_1d(sigma)
    r = len(nucleo) // 2
    horizontal = np.zeros_like(gris)
    relleno = np.pad(gris, ((0, 0), (r, r)), mode="edge")
    for i, peso in enumerate(nucleo):
        horizontal += peso * relleno[:, i:i + gris.shape[1]]
    salida = np.zeros_like(gris)
    relleno = np.pad(horizontal, ((r, r), (0, 0)), mode="edge")
    for i, peso in enumerate(nucleo):
        salida += peso * relleno[i:i + gris.shape[0], :]
    return salida


def supresion_no_maxima(magnitud: np.ndarray, angulo: np.ndarray) -> np.ndarray:
    """Adelgaza los bordes a un píxel de ancho.

    Un borde detectado por gradiente sale grueso: la derivada es alta en toda
    la pendiente, no sólo en la cresta. Aquí cada píxel se compara con sus dos
    vecinos **en la dirección del gradiente** —es decir, perpendicular al
    borde— y sobrevive sólo si es el máximo local. Es el paso que hace que
    Canny dé líneas y no manchas.

    La dirección se cuantiza a cuatro: horizontal, vertical y las dos
    diagonales. Con ocho vecinos no hay más opciones posibles.
    """
    grados = np.rad2deg(angulo) % 180.0
    salida = np.zeros_like(magnitud)

    # Se rellena para poder comparar los bordes de la imagen sin salirse.
    m = np.pad(magnitud, 1, mode="constant", constant_values=0.0)
    centro = m[1:-1, 1:-1]

    vecinos = {
        # (sector) -> (vecino A, vecino B) en la dirección del gradiente
        0: (m[1:-1, 2:], m[1:-1, :-2]),      # 0 grados: izquierda / derecha
        1: (m[:-2, 2:], m[2:, :-2]),         # 45 grados: diagonales
        2: (m[:-2, 1:-1], m[2:, 1:-1]),      # 90 grados: arriba / abajo
        3: (m[:-2, :-2], m[2:, 2:]),         # 135 grados: la otra diagonal
    }
    sector = np.zeros_like(grados, dtype=np.int8)
    sector[(grados >= 22.5) & (grados < 67.5)] = 1
    sector[(grados >= 67.5) & (grados < 112.5)] = 2
    sector[(grados >= 112.5) & (grados < 157.5)] = 3

    for s, (a, b) in vecinos.items():
        mascara = (sector == s) & (centro >= a) & (centro >= b)
        salida[mascara] = centro[mascara]
    return salida


def histeresis(
    delgado: np.ndarray, umbral_bajo: float, umbral_alto: float,
) -> np.ndarray:
    """Doble umbral con seguimiento de bordes.

    La idea de Canny: un solo umbral obliga a elegir entre perder bordes
    tenues (umbral alto) o aceptar ruido (umbral bajo). Con dos, los píxeles
    por encima del alto son bordes seguros, los que están entre los dos son
    candidatos, y un candidato se acepta **sólo si toca a un borde seguro**.

    La propagación se hace por dilatación iterativa: se marca lo seguro y se
    expande a los candidatos vecinos hasta que deja de crecer. Es la versión
    vectorizada del recorrido en profundidad que suele explicarse.
    """
    fuertes = delgado >= umbral_alto
    candidatos = (delgado >= umbral_bajo) & ~fuertes

    aceptados = fuertes.copy()
    for _ in range(delgado.shape[0] + delgado.shape[1]):
        # Vecindad de ocho: se desplaza la máscara en las ocho direcciones.
        vecino = np.zeros_like(aceptados)
        vecino[1:, :] |= aceptados[:-1, :]
        vecino[:-1, :] |= aceptados[1:, :]
        vecino[:, 1:] |= aceptados[:, :-1]
        vecino[:, :-1] |= aceptados[:, 1:]
        vecino[1:, 1:] |= aceptados[:-1, :-1]
        vecino[:-1, :-1] |= aceptados[1:, 1:]
        vecino[1:, :-1] |= aceptados[:-1, 1:]
        vecino[:-1, 1:] |= aceptados[1:, :-1]

        nuevos = candidatos & vecino & ~aceptados
        if not nuevos.any():
            break
        aceptados |= nuevos
    return (aceptados * 255).astype(np.uint8)


def canny(
    rgb: np.ndarray,
    umbral_bajo: float = 50.0,
    umbral_alto: float = 150.0,
    sigma: float = 1.4,
) -> np.ndarray:
    """Canny completo, en sus cinco pasos.

    Cada paso está en su propia función y se puede llamar por separado; el
    laboratorio los muestra uno a uno. Los valores por defecto de sigma y de
    los umbrales son los del artículo original de Canny (1986).
    """
    gris = suavizar(a_gris(rgb), sigma)
    magnitud, angulo = gradiente(gris)
    delgado = supresion_no_maxima(magnitud, angulo)
    return histeresis(delgado, umbral_bajo, umbral_alto)

"""
Figuras del curso: rejillas antes/después, histogramas y matrices de confusión.

Por qué un módulo y no Matplotlib suelto en cada ejemplo
--------------------------------------------------------
Porque el 80 % del código de un laboratorio de visión acaba siendo `subplots`,
`imshow`, `axis("off")` y `tight_layout`. Con eso repetido veinte veces, la
idea que se quería enseñar queda enterrada bajo la fontanería del dibujo. Aquí
la fontanería se escribe una vez y el ejemplo se queda con lo suyo.

Además fija dos cosas que, mal puestas, arruinan una figura docente:

* **Las imágenes en gris se dibujan con `vmin=0, vmax=255`.** Sin fijarlo,
  Matplotlib normaliza cada imagen a su propio rango, así que una imagen
  oscura y una clara salen idénticas en pantalla y la comparación
  «antes/después» —que es el ejercicio entero— no muestra nada.
* **El título dice de dónde salió la imagen.** Con fuentes que degradan
  (`acquisition.mejor_fuente_disponible`), saber si se está mirando una webcam
  o una pieza sintética es parte del resultado.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

__all__ = [
    "comparar",
    "guardar",
    "histograma",
    "matriz_de_confusion",
    "nube_de_caracteristicas",
    "rejilla",
]


def _preparar_matplotlib():
    """Importa pyplot eligiendo un backend que no requiera pantalla.

    En CI y en un `pytest` headless, el backend interactivo por defecto puede
    fallar al importar o intentar abrir una ventana. Se fuerza «Agg» sólo
    cuando no hay indicios de sesión gráfica ni de cuaderno, para no pisarle la
    elección a quien esté trabajando en Jupyter —donde Agg dejaría todas las
    figuras invisibles, que es un fallo mucho más desconcertante que un error.
    """
    import matplotlib

    en_cuaderno = "ipykernel" in sys.modules
    backend_elegido = bool(os.environ.get("MPLBACKEND"))
    sin_pantalla = (
        os.environ.get("SDL_VIDEODRIVER") == "dummy"
        or (sys.platform not in ("win32", "darwin") and not os.environ.get("DISPLAY"))
    )
    if sin_pantalla and not en_cuaderno and not backend_elegido:
        matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    return plt


def _mostrar(eje, imagen: np.ndarray, titulo: str = "") -> None:
    imagen = np.asarray(imagen)
    if imagen.ndim == 2:
        eje.imshow(imagen, cmap="gray", vmin=0, vmax=255)
    elif imagen.dtype == bool:
        eje.imshow(imagen.astype(np.uint8) * 255, cmap="gray", vmin=0, vmax=255)
    else:
        eje.imshow(np.clip(imagen, 0, 255).astype(np.uint8))
    if titulo:
        eje.set_title(titulo, fontsize=9)
    eje.axis("off")


def rejilla(
    imagenes: list[np.ndarray],
    titulos: list[str] | None = None,
    columnas: int = 4,
    titulo_general: str = "",
    ancho_por_celda: float = 3.0,
):
    """Varias imágenes en una rejilla. Devuelve la figura de Matplotlib."""
    if not imagenes:
        raise ValueError("no hay imágenes que dibujar")
    if titulos is not None and len(titulos) != len(imagenes):
        raise ValueError(
            f"{len(titulos)} títulos para {len(imagenes)} imágenes: tienen que coincidir"
        )

    plt = _preparar_matplotlib()
    columnas = max(1, min(columnas, len(imagenes)))
    filas = (len(imagenes) + columnas - 1) // columnas

    figura, ejes = plt.subplots(
        filas, columnas,
        figsize=(ancho_por_celda * columnas, ancho_por_celda * filas),
        squeeze=False,
    )
    for i, eje in enumerate(ejes.ravel()):
        if i < len(imagenes):
            _mostrar(eje, imagenes[i], titulos[i] if titulos else "")
        else:
            eje.axis("off")   # celdas sobrantes de la última fila
    if titulo_general:
        figura.suptitle(titulo_general, fontsize=12)
    figura.tight_layout()
    return figura


def comparar(
    antes: np.ndarray,
    despues: np.ndarray,
    titulo_antes: str = "Original",
    titulo_despues: str = "Procesada",
    titulo_general: str = "",
):
    """Dos imágenes lado a lado. El gesto más repetido de todo el curso."""
    return rejilla(
        [antes, despues], [titulo_antes, titulo_despues],
        columnas=2, titulo_general=titulo_general,
    )


def histograma(
    imagen: np.ndarray,
    titulo: str = "Histograma",
    bins: int = 256,
    con_imagen: bool = True,
):
    """Histograma de una imagen, con la imagen al lado si se pide.

    En color dibuja los tres canales por separado en vez de la luminancia
    combinada: la Clase 1 necesita que se vea que un canal puede estar saturado
    mientras los otros dos no, y una sola curva promedio esconde justo eso.
    """
    plt = _preparar_matplotlib()
    imagen = np.asarray(imagen)

    if con_imagen:
        figura, (eje_img, eje_hist) = plt.subplots(1, 2, figsize=(10, 4))
        _mostrar(eje_img, imagen, "Imagen")
    else:
        figura, eje_hist = plt.subplots(figsize=(6, 4))

    if imagen.ndim == 3 and imagen.shape[2] >= 3:
        for canal, color in enumerate(("red", "green", "blue")):
            eje_hist.hist(
                imagen[:, :, canal].ravel(), bins=bins, range=(0, 255),
                color=color, alpha=0.5, label=color,
            )
        eje_hist.legend(fontsize=8)
    else:
        eje_hist.hist(imagen.ravel(), bins=bins, range=(0, 255), color="gray")

    eje_hist.set_title(titulo, fontsize=10)
    eje_hist.set_xlabel("Valor de píxel")
    eje_hist.set_ylabel("Número de píxeles")
    eje_hist.set_xlim(0, 255)
    figura.tight_layout()
    return figura


def matriz_de_confusion(
    matriz: np.ndarray,
    clases: list[str],
    titulo: str = "Matriz de confusión",
    normalizar: bool = False,
):
    """Matriz de confusión con los números escritos dentro.

    Escritos dentro a propósito: una matriz de confusión sólo como mapa de
    color se interpreta mal —el ojo compara intensidades, no cantidades— y lo
    que la Clase 4 tiene que discutir es cuántos falsos negativos hubo, no si
    la celda estaba más o menos azul.
    """
    plt = _preparar_matplotlib()
    matriz = np.asarray(matriz, dtype=float)
    if matriz.shape[0] != matriz.shape[1]:
        raise ValueError(f"la matriz debe ser cuadrada, no {matriz.shape}")
    if len(clases) != matriz.shape[0]:
        raise ValueError(f"{len(clases)} clases para una matriz {matriz.shape}")

    if normalizar:
        totales = matriz.sum(axis=1, keepdims=True)
        # Una clase sin ejemplos en el test daría 0/0. Se deja en 0 en vez de
        # propagar un nan que luego se dibuja como un hueco sin explicación.
        matriz = np.divide(matriz, totales, out=np.zeros_like(matriz), where=totales > 0)

    figura, eje = plt.subplots(figsize=(1.6 * len(clases) + 2, 1.4 * len(clases) + 2))
    imagen = eje.imshow(matriz, cmap="Blues", vmin=0, vmax=matriz.max() or 1)
    figura.colorbar(imagen, ax=eje, fraction=0.046)

    eje.set_xticks(range(len(clases)), clases, rotation=45, ha="right")
    eje.set_yticks(range(len(clases)), clases)
    eje.set_xlabel("Predicho")
    eje.set_ylabel("Real")
    eje.set_title(titulo)

    umbral = (matriz.max() or 1) / 2.0
    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            texto = f"{matriz[i, j]:.2f}" if normalizar else f"{int(matriz[i, j])}"
            eje.text(
                j, i, texto, ha="center", va="center",
                color="white" if matriz[i, j] > umbral else "black",
            )
    figura.tight_layout()
    return figura


def nube_de_caracteristicas(
    X: np.ndarray,
    y: np.ndarray,
    nombres: tuple[str, ...],
    eje_x: str,
    eje_y: str,
    titulo: str = "",
):
    """Dos características enfrentadas, coloreadas por clase.

    Es la figura con la que termina la Clase 3 y empieza la Clase 4: si las
    clases se separan a ojo en este gráfico, casi cualquier modelo funcionará;
    si no se separan, ninguno lo hará y el problema está en las
    características, no en el algoritmo. Enseñar eso **antes** de entrenar es
    lo que evita que el aprendizaje automático parezca magia.
    """
    plt = _preparar_matplotlib()
    if eje_x not in nombres or eje_y not in nombres:
        raise ValueError(f"ejes {eje_x!r}/{eje_y!r} no están en {nombres}")

    ix, iy = nombres.index(eje_x), nombres.index(eje_y)
    figura, eje = plt.subplots(figsize=(6, 5))
    for clase in sorted(set(np.asarray(y).tolist())):
        seleccion = np.asarray(y) == clase
        eje.scatter(X[seleccion, ix], X[seleccion, iy], label=str(clase), alpha=0.75, s=36)
    eje.set_xlabel(eje_x)
    eje.set_ylabel(eje_y)
    eje.set_title(titulo or f"{eje_y} frente a {eje_x}")
    eje.legend()
    figura.tight_layout()
    return figura


def guardar(figura, ruta: str | Path, dpi: int = 120) -> Path:
    """Guarda una figura y **la cierra**.

    Cerrarla no es opcional: un notebook que genera cuarenta figuras sin cerrar
    ninguna acaba con el aviso de Matplotlib sobre figuras abiertas y, en un
    portátil justo de memoria, se lo come entero.
    """
    plt = _preparar_matplotlib()
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(ruta, dpi=dpi, bbox_inches="tight")
    plt.close(figura)
    return ruta

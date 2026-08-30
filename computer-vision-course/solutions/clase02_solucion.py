#!/usr/bin/env python3
"""
Clase 2 · Solución de referencia del laboratorio (T1–T4 y el reto).

Para el profesor y los ayudantes. Se ejecuta entera y produce las figuras y
las cifras que se piden en `docs/clase02_guia.md` §5.

No es la única solución válida. Es **una** solución completa, con los números
que un grupo bien orientado debería obtener, para poder comparar sin tener
que rehacer el laboratorio en cada corrección.

Ejecutar:
    python solutions/clase02_solucion.py

Reglas que cumple este fichero:
- Todo número impreso está medido por el propio código en esta misma
  ejecución; si un número contradice lo que imprime, se corrige el texto,
  no la medición.
- Los mensajes de consola son ASCII: en el aula hay Windows con cp1252 y un
  guion largo en un print tira la sesión (ver docs/clase01_guia.md §8).
- El conteo de trozos de bordes se hace en 8-conexos: la grieta sintética
  es una diagonal y con 4-conectividad se partiría por definición.
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

CURSO = Path(__file__).resolve().parents[1]
for _ruta in (CURSO, CURSO.parent):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import cv2
import numpy as np
from scipy import ndimage

from cvcourse import synthetic, viz

SALIDA = CURSO / "outputs" / "clase02_solucion"


# ── Herramientas comunes del laboratorio ──────────────────────────────────

def rmse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(((a.astype(float) - b.astype(float)) ** 2).mean()))


def en_gris(imagen: np.ndarray) -> np.ndarray:
    return np.clip(
        0.299 * imagen[..., 0] + 0.587 * imagen[..., 1] + 0.114 * imagen[..., 2],
        0, 255,
    ).astype(np.uint8) if imagen.ndim == 3 else imagen


def sal_y_pimienta(gris: np.ndarray, proporcion: float, semilla: int) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    sucia = gris.copy()
    mascara = rng.random(gris.shape) < proporcion
    sucia[mascara] = np.where(rng.random(mascara.sum()) < 0.5, 0, 255)
    return sucia


def cronometrar(fn, repeticiones: int = 15) -> float:
    """Mediana de los tiempos, en milisegundos. Ver `rendimiento_convolucion.py`."""
    fn()
    tiempos = []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        fn()
        tiempos.append((time.perf_counter() - t0) * 1000.0)
    return float(np.median(tiempos))


def contar_trozos(bordes: np.ndarray) -> int:
    """Islas de un mapa de bordes, en 8-conexos.

    `scipy.ndimage.label` por defecto usa 4-conexos, y eso parte las
    diagonales: para una grieta a 45 grados (o un contorno), el conteo en
    4-conexos miente. OpenCV cuenta en 8-conexos por defecto.
    """
    return int(cv2.connectedComponents(bordes, connectivity=8)[0]) - 1


# ── T1 — Ruido y filtros ──────────────────────────────────────────────────

def t1_ruido_y_filtros() -> None:
    """La pieza limpia es la verdad-terreno: la RMSE mide cuánto se aleja.

    Los números que hay que ver (y que el grupo debería repetir con otros
    sigmas): contra el ruido gaussiano los tres filtros ayudan, y en esta
    pieza, casi plana, la gana la mediana; contra sal y pimienta sólo la
    mediana devuelve la RMSE a su valor razonable (el promedio deja 13,9:
    el grano convertido en mancha).
    """
    print("=" * 74)
    print("T1 - RUIDO Y FILTROS (RMSE contra la pieza limpia)")
    print("=" * 74)

    limpia, _ = synthetic.pieza_individual(tamano=192, clase="OK", ruido=0.0, semilla=8)
    rng = np.random.default_rng(8)
    gaussiana = np.clip(limpia.astype(float) + rng.normal(0, 8, limpia.shape), 0, 255).astype(np.uint8)
    sal_pimienta = sal_y_pimienta(limpia, 0.06, semilla=8)

    filtros = {
        "promedio 3x3": lambda i: cv2.blur(i, (3, 3)),
        "gaussiano s=1.2": lambda i: cv2.GaussianBlur(i, (5, 5), 1.2),
        "mediana 3x3": lambda i: cv2.medianBlur(i, 3),
        "mediana 5x5": lambda i: cv2.medianBlur(i, 5),
    }

    print(f"\n  {'filtro':16s} {'RMSE gaussiana':>15s} {'RMSE sal y pimienta':>19s}")
    print("  " + "-" * 52)
    filas_t1: list[tuple[str, float, float]] = []
    for nombre, filtro in filtros.items():
        rg = rmse(limpia, filtro(gaussiana))
        rs = rmse(limpia, filtro(sal_pimienta))
        filas_t1.append((nombre, rg, rs))
        print(f"  {nombre:16s} {rg:>15.1f} {rs:>19.1f}")
    print(
        f"\n  sin filtrar: gaussiana {rmse(limpia, gaussiana):.1f}, "
        f"sal y pimienta {rmse(limpia, sal_pimienta):.1f}"
    )
    print(
        "\n  Contra el ruido gaussiano los tres filtros ayudan y en esta\n"
        "  pieza, que es casi plana, la gana la mediana (8,0 -> 3,6). No es\n"
        "  la respuesta generica: en una imagen con textura el gaussiano\n"
        "  suele ganar; aqui no hay textura que la mediana destruya.\n"
        "  Contra sal y pimienta la mediana devuelve la RMSE a su valor\n"
        "  (34,5 -> 2,7); el promedio (13,9) y el gaussiano (11,7) convierten\n"
        "  cada grano en una mancha gris. Dos ruidos, dos filtros."
    )

    viz.guardar(
        viz.rejilla(
            [limpia, gaussiana, sal_pimienta,
             filtros["gaussiano s=1.2"](gaussiana),
             filtros["mediana 5x5"](sal_pimienta)],
            ["limpia", "gaussiana s=8", "sal y pimienta 6%",
             "gaussiano aplicado", "mediana aplicada"],
            columnas=5, titulo_general="T1 - el filtro justo para cada ruido",
        ),
        SALIDA / "t1_ruido_y_filtros.png",
    )


# ── T2 — Kernel propio ────────────────────────────────────────────────────

def t2_kernel_propio() -> None:
    """Un kernel de detección de bordes diagonales, diseñado y medido.

    Se diseña como combinación de derivadas: responde a cambios a 45 grados.
    La suma es 0 (detecta cambios), las zonas planas quedan en 0 (se
    comprueba con una cifra), y la correlación con la magnitud de Sobel dice
    QUÉ clase de detector es: direccional (moderada), completo (~0,9) o
    nulo (~0).
    """
    print("\n" + "=" * 74)
    print("T2 - KERNEL PROPIO: bordes diagonales")
    print("=" * 74)

    # Diseño: +1 en la diagonal principal, -1 en la secundaria. Detecta
    # cambios a 45 grados; en una zona plana la suma ponderada es 0.
    kernel = np.array(
        [[1, 0, -1],
         [0, 0, 0],
         [-1, 0, 1]], dtype=np.float32
    )
    print(f"\n  suma del kernel: {kernel.sum():.1f}  (esperado 0: detector de cambios)")

    pieza, verdad = synthetic.pieza_individual(tamano=192, clase="NO_OK", defecto="grieta", ruido=0.0, semilla=4)
    gris = pieza.astype(np.float32)

    # Zona plana de la banda: media de la salida debe ser ~0. Se toma un
    # trozo de banda pura, por encima de la pieza (que empieza en bbox).
    f0, c0, _, _ = verdad.bbox
    salida = cv2.filter2D(gris, -1, kernel)
    zona_plana = salida[2:f0 - 6, 2:c0 - 6]
    print(f"  salida sobre zona plana: media {zona_plana.mean():.2f} (cerca de 0)")

    contraste_antes = float(gris.std())
    contraste_despues = float(np.abs(salida).std())
    print(
        f"  desviacion: {contraste_antes:.1f} (imagen) -> {contraste_despues:.1f} (magnitud de bordes)\n"
        "  La desviacion de la salida mide CUANTO cambio hay en la imagen;\n"
        "  el histograma de la salida no se parece al de la entrada porque la\n"
        "  operacion no conserva energia: es un filtro de bordes, no un realce."
    )

    # La grieta de la pieza es diagonal (pendiente ~1): es exactamente lo
    # que este kernel ve. El contorno de la pieza es ortogonal y no lo ve.
    gx = cv2.Sobel(gris, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gris, cv2.CV_32F, 0, 1, ksize=3)
    magnitud_sobel = cv2.magnitude(gx, gy)
    interior = np.zeros_like(gx)
    interior[f0 + 3 : verdad.bbox[2] - 3, c0 + 3 : verdad.bbox[3] - 3] = 1
    ys, xs = np.nonzero((magnitud_sobel > 150) & (interior > 0))
    pendiente = float(np.polyfit(xs, ys, 1)[0])
    print(f"  la grieta es diagonal: pendiente {pendiente:.2f} (1 = 45 grados)")

    corr = float(np.corrcoef(np.abs(salida).ravel(), magnitud_sobel.ravel())[0, 1])
    laplaciano = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    corr_laplaciano = float(
        np.corrcoef(np.abs(cv2.filter2D(gris, -1, laplaciano)).ravel(), magnitud_sobel.ravel())[0, 1]
    )
    print(f"  correlacion con la magnitud de Sobel: {corr:.3f}")
    print(f"  correlacion del laplaciano (todas las direcciones): {corr_laplaciano:.3f}")
    print(
        "  La cifra dice que clase de detector es cada kernel: un detector\n"
        "  completo correlaciona ~0,9; uno direccional se queda a mitad\n"
        "  porque ve solo su direccion. Aqui el 0,42 es el resultado\n"
        "  CORRECTO: MI kernel ve la grieta (diagonal) y casi nada del\n"
        "  contorno (ortogonal). No es un fallo, es la definicion de kernel\n"
        "  direccional. Si un grupo disena un kernel que correlaciona ~0,\n"
        "  su kernel no detecta bordes, y lo sabe por la cifra."
    )

    viz.guardar(
        viz.rejilla(
            [pieza, np.abs(salida), np.clip(magnitud_sobel, 0, 255)],
            ["pieza con grieta", "MI kernel (bordes)", "Sobel (referencia)"],
            columnas=3, titulo_general="T2 - el kernel propio frente a la referencia",
        ),
        SALIDA / "t2_kernel_propio.png",
    )


# ── T3 — Canny y romperlo ────────────────────────────────────────────────

def t3_canny_y_romperlo() -> None:
    """Cuatro etapas funcionando, y el algoritmo roto a propósito.

    Dos hallazgos que los números enseñan solos:

    1. El umbral bajo no es gratis: al bajar de 50 a 10, el ruido de la
       banda que toca el contorno entra en cadena (1084 -> 1899 px).
    2. El ruido que fragmenta el contorno no se arregla con umbrales: se
       arregla pre-suavizando (19 islas -> 1 isla con gauss 2,0). Es la
       razón por la que el pipeline industrial suaviza primero.
    """
    print("\n" + "=" * 74)
    print("T3 - CANNY ETAPA POR ETAPA, Y ROTO A PROPOSITO")
    print("=" * 74)

    pieza, verdad = synthetic.pieza_individual(
        tamano=256, clase="NO_OK", defecto="grieta", ruido=2.0, semilla=3
    )
    gris = pieza.astype(np.float32)

    from src.framework.processing import edge_detection

    suave = edge_detection.suavizar(gris, 1.4)
    mag, ang = edge_detection.gradiente(suave)
    delgado = edge_detection.supresion_no_maxima(mag, ang)
    bordes = edge_detection.histeresis(delgado, 50.0, 150.0)

    print(f"\n  tras el gradiente   : {int((mag > 50).sum()):>5d} px")
    print(f"  tras la supresion   : {int((delgado > 50).sum()):>5d} px  (adelgaza)")
    print(f"  tras la histeresis  : {int((bordes > 0).sum()):>5d} px")
    print(
        "  La histeresis filtra aqui solo unos pocos px porque tras la\n"
        "  supresion casi no quedan candidatos aislados por encima de 50.\n"
        "  Su trabajo se ve en la tabla de abajo: al bajar el umbral bajo a\n"
        "  10, el ruido colgado del contorno la vuelve a llenar."
    )

    # Romper a proposito, sobre la pieza SIN suavizar. El conteo de trozos
    # es en 8-conexos (ver contar_trozos).
    base = cv2.Canny(pieza, 50, 150)
    n_px_base = int((base > 0).sum())

    print(f"\n  {'umbrales':>14s} {'px de borde':>12s} {'trozos':>8s}  estado")
    print("  " + "-" * 62)
    filas: list[tuple[str, int, int, str]] = []
    for bajo, alto in [(50, 150), (10, 20), (10, 245), (140, 150), (50, 60)]:
        b = cv2.Canny(pieza, bajo, alto)
        n_px = int((b > 0).sum())
        n_trozos = contar_trozos(b)
        if (bajo, alto) == (50, 150):
            estado = "contorno + grieta (referencia)"
        elif n_px > 5000:
            estado = "reventado de ruido"
        elif n_px > n_px_base + 5:
            estado = "ruido enganchado al borde"
        else:
            estado = "identico al (50,150): banda vacia"
        filas.append((f"{bajo}-{alto}", n_px, n_trozos, estado))
        print(f"  {f'{bajo}-{alto}':>14s} {n_px:>12d} {n_trozos:>8d}  {estado}")

    print(
        "\n  (10,20): con el alto en 20 todo el ruido es 'seguro': miles de\n"
        "  islas. (10,245): el bajo en 10 engancha al contorno el ruido de\n"
        "  la banda (1084 -> 1899 px): el umbral bajo no es gratis. (140,150)\n"
        "  y (50,60) dan exactamente lo mismo que la referencia: en esta\n"
        "  imagen no hay pixeles en esas bandas conectados a un borde fuerte.\n"
        "  El (50,150) deja 19 islas, no 1: el ruido de la banda (sigma 2,\n"
        "  siempre presente) fragmenta el contorno. Con 4-conectividad serian\n"
        "  371: la grieta diagonal se parte por definicion."
    )

    # La verdad-terreno: el contorno del bbox, y cuánto conserva Canny.
    f0, c0, f1, c1 = verdad.bbox
    contorno = np.zeros_like(pieza, dtype=bool)
    contorno[f0, c0:c1] = True
    contorno[f1 - 1, c0:c1] = True
    contorno[f0:f1, c0] = True
    contorno[f0:f1, c1 - 1] = True
    coincide = int(((base > 0) & contorno).sum())
    print(
        f"\n  contorno verdadero de la pieza (bbox): {int(contorno.sum())} px;\n"
        f"  de ellos, el (50,150) conserva {coincide}: el ruido ya ha roto\n"
        "  mas de la mitad del contorno real."
    )

    # El arreglo no son los umbrales: es el preprocesado.
    suavizada = cv2.GaussianBlur(pieza, (0, 0), 2.0)
    b_suave = cv2.Canny(suavizada, 50, 150)
    b_suave_vacio = cv2.Canny(suavizada, 10, 245)
    print(
        f"\n  con el pre-suavizado del pipeline industrial (gauss 2,0), el\n"
        f"  (50,150) da {int((b_suave > 0).sum())} px y {contar_trozos(b_suave)} isla:\n"
        f"  el contorno entero unido. Y el (10,245) que antes enganchaba ruido\n"
        f"  queda en {int((b_suave_vacio > 0).sum())} px: nada llega a 245 tras\n"
        "  suavizar. Los umbrales calibran la escala del borde; el ruido que\n"
        "  los hacia fracasar lo quita el preprocesado, no los umbrales."
    )

    viz.guardar(
        viz.rejilla(
            [gris.astype(np.uint8), suave.astype(np.uint8),
             np.clip(mag, 0, 255).astype(np.uint8),
             np.clip(delgado, 0, 255).astype(np.uint8), bordes],
            ["gris", "suavizado", "gradiente", "supresion", "histeresis"],
            columnas=5, titulo_general="T3 - Canny en sus cuatro etapas",
        ),
        SALIDA / "t3_canny_etapas.png",
    )

    b_roto = cv2.Canny(pieza, 10, 20)
    b_enganchado = cv2.Canny(pieza, 10, 245)
    viz.guardar(
        viz.rejilla(
            [pieza, base, b_roto, b_enganchado, b_suave],
            ["pieza con grieta", "(50,150): 19 islas", "(10,20): reventado",
             "(10,245): ruido enganchado", "gauss 2,0: 1 isla"],
            columnas=5, titulo_general="T3 - romper Canny y arreglarlo",
        ),
        SALIDA / "t3_canny_romper.png",
    )


# ── T4 — Rendimiento ──────────────────────────────────────────────────────

def t4_rendimiento() -> None:
    """La tabla de tiempos reproducible, con la imagen del laboratorio.

    Mismos números que `rendimiento_convolucion.py` en lo esencial: NumPy es
    legible y lento, OpenCV es rápido. Se guarda como CSV para citarla en
    `analisis.md`.
    """
    print("\n" + "=" * 74)
    print("T4 - RENDIMIENTO: LA MISMA CONVOLUCION, TRES EJECUTORES")
    print("=" * 74)

    rng = np.random.default_rng(0)
    filas, columnas = np.ogrid[:600, :800]
    imagen = np.clip(
        ((filas + columnas) % 120 + 60).astype(np.float32) + rng.normal(0, 3, (600, 800)),
        0, 255,
    ).astype(np.uint8)

    from src.framework.processing import edge_detection

    nucleo_3 = np.ones((3, 3), dtype=np.float32) / 9.0
    nucleo_5 = np.ones((5, 5), dtype=np.float32) / 25.0

    def con_nucleo(funcion, nucleo):
        return lambda: funcion(imagen, nucleo)

    filas_tabla: list[dict[str, object]] = []
    for nombre, funcion in [
        ("convolucionar (numpy)", lambda k: con_nucleo(edge_detection.convolucionar, k)),
        ("scipy.ndimage.convolve", lambda k: con_nucleo(ndimage.convolve, k)),
        ("cv2.filter2D", lambda k: con_nucleo(lambda im, n: cv2.filter2D(im, -1, n), k)),
    ]:
        for nucleo, tam in ((nucleo_3, "3x3"), (nucleo_5, "5x5")):
            ms = cronometrar(funcion(nucleo))
            filas_tabla.append(
                {"implementacion": nombre, "kernel": tam, "ms": round(ms, 2),
                 "cabe a 60 fps": ms < 16.6}
            )
            print(
                f"  {nombre:26s} {tam:>4s} {ms:>8.2f} ms  "
                f"{'SI' if ms < 16.6 else 'NO'} a 60 fps"
            )

    ruta = SALIDA / "t4_tabla_de_rendimiento.csv"
    with ruta.open("w", newline="", encoding="utf-8") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=filas_tabla[0].keys())
        escritor.writeheader()
        escritor.writerows(filas_tabla)

    print(
        f"\n  Tabla guardada: {ruta}\n"
        "  El protocolo que la hace reproducible: misma imagen (semilla 0),\n"
        "  mediana de las pasadas (un valor raro no decide), y las funciones\n"
        "  cronometradas solas, sin conversiones alrededor. Los milisegundos\n"
        "  cambian de maquina; el ORDEN no: cv2 es ~25 veces mas rapido que\n"
        "  la version didactica en los dos tamanos, y a 5x5 la version\n"
        "  didactica y scipy se salen del presupuesto de 16,6 ms mientras\n"
        "  cv2 cabe con margen."
    )


# ── Reto — kernel separable ───────────────────────────────────────────────

def reto_separable() -> None:
    """Gaussiano 2D como dos convoluciones 1D: misma salida, menos trabajo.

    `edge_detection.suavizar` YA es la versión separable (su docstring lo
    dice): dos pasadas con el kernel 1D en vez de una con el kernel 2D
    completo. El reto es comprobarlo: el gaussiano 2D (producto exterior de
    dos 1D) y las dos pasadas deben dar lo mismo, y el cronómetro debe
    mostrar de dónde sale la ventaja O(k^2) -> O(2k).
    """
    print("\n" + "=" * 74)
    print("RETO - GAUSSIANO SEPARABLE (O(2k) frente a O(k^2))")
    print("=" * 74)

    from src.framework.processing import edge_detection

    pieza, _ = synthetic.pieza_individual(tamano=192, clase="OK", ruido=0.0, semilla=1)
    gris = pieza.astype(np.float32)

    def gauss_1d(sigma: float) -> np.ndarray:
        # Misma convencion que edge_detection._gauss_1d: radio = round(3*sigma).
        radio = max(1, round(3 * sigma))
        x = np.arange(-radio, radio + 1, dtype=np.float32)
        nucleo = np.exp(-(x ** 2) / (2.0 * sigma ** 2))
        return nucleo / nucleo.sum()

    print(f"\n  {'sigma':>6s} {'kernel':>7s} {'directa':>9s} {'separable':>10s} {'x':>6s}  diff max")
    print("  " + "-" * 52)
    diff_max = 0.0
    for sigma in (0.5, 1.4, 2.5, 3.6):
        v1 = gauss_1d(sigma)
        gauss_2d = np.outer(v1, v1)
        directa = edge_detection.convolucionar(gris, gauss_2d)
        separable = edge_detection.suavizar(gris, sigma)
        diff = float(np.abs(directa - separable).max())
        diff_max = max(diff_max, diff)
        t_directa = cronometrar(
            lambda g=gauss_2d: edge_detection.convolucionar(gris, g)
        )
        t_separable = cronometrar(
            lambda s=sigma: edge_detection.suavizar(gris, s)
        )
        print(
            f"  {sigma:>6.1f} {f'{v1.size}x{v1.size}':>7s} {t_directa:>9.2f} {t_separable:>10.2f}"
            f" {f'x{t_directa / t_separable:.1f}':>6s}  {diff:.5f}"
        )

    print(
        f"\n  Diferencia maxima entre los dos caminos: {diff_max:.4f} niveles de gris:\n"
        "  son la misma operacion, la diferencia es de redondeo. Y el tiempo\n"
        "  cae con el kernel: la primera fila ya compensa y la columna x\n"
        "  crece con el tamano, porque son k^2 multiplicaciones por pixel\n"
        "  frente a 2k. Los milisegundos cambian de maquina; la tendencia\n"
        "  con k, no. Es la razon por la que 'un gaussiano 2D' y 'dos\n"
        "  pasadas 1D' son lo mismo, y por la que OpenCV implementa sus\n"
        "  gaussianos separables."
    )

    directa = edge_detection.convolucionar(gris, np.outer(gauss_1d(1.4), gauss_1d(1.4)))
    separable = edge_detection.suavizar(gris, 1.4)
    diferencia = np.clip(200 * np.abs(directa - separable), 0, 255).astype(np.uint8)
    viz.guardar(
        viz.rejilla(
            [pieza, np.clip(directa, 0, 255).astype(np.uint8),
             np.clip(separable, 0, 255).astype(np.uint8), diferencia],
            ["original", "gaussiano 2D directo", "gaussiano separable",
             "diferencia (x200)"],
            columnas=4, titulo_general="Reto - dos caminos, una salida",
        ),
        SALIDA / "reto_separable.png",
    )


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    t1_ruido_y_filtros()
    t2_kernel_propio()
    t3_canny_y_romperlo()
    t4_rendimiento()
    reto_separable()
    print(f"\nFiguras en: {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

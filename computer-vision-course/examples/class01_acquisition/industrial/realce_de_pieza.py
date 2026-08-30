#!/usr/bin/env python3
"""
Clase 1 · Industrial — realzar una pieza subexpuesta, y medir si sirvió de algo.

El error que este ejemplo evita
--------------------------------
«Mejorar una imagen» suele evaluarse mirándola. Eso vale para una foto de
vacaciones y no vale para una estación de inspección: lo que importa no es que
se vea mejor, sino que **la siguiente etapa del pipeline funcione**.

Así que aquí cada realce se juzga con dos varas:

1. una medida del histograma —rango dinámico, desviación típica—, que es la
   que suele darse por buena;
2. una medida **de la tarea**: ¿se puede separar la pieza del fondo con un
   umbral, y con qué error respecto a la verdad-terreno?

La segunda es la que manda, y a veces contradice a la primera. Ese desacuerdo
es el contenido del ejemplo.

Los cuatro realces son los de la Unidad VII: subir brillo, subir contraste,
estirar el contraste al rango completo, y ecualizar el histograma.

Ejecutar:
    python examples/class01_acquisition/industrial/realce_de_pieza.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CURSO = Path(__file__).resolve().parents[3]
REPO = CURSO.parent
for _ruta in (CURSO, REPO):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import numpy as np

from cvcourse import synthetic, viz

SALIDA = CURSO / "outputs" / "clase01"


# ── Los cuatro realces, en NumPy puro y legibles ──────────────────────────

def subir_brillo(imagen: np.ndarray, delta: float = 60.0) -> np.ndarray:
    """Suma una constante. Desplaza el histograma; **no lo ensancha**.

    Es el realce que más se intenta y el que menos resuelve: si el problema era
    falta de contraste, sumar no lo arregla — mueve el mismo montón de valores
    un poco más a la derecha, y de paso satura por arriba lo que ya estaba alto.
    """
    return np.clip(imagen.astype(float) + delta, 0, 255).astype(np.uint8)


def subir_contraste(imagen: np.ndarray, factor: float = 2.0) -> np.ndarray:
    """Multiplica la distancia a la media. Ensancha alrededor del centro."""
    media = imagen.mean()
    return np.clip((imagen.astype(float) - media) * factor + media, 0, 255).astype(np.uint8)


def estirar_contraste(imagen: np.ndarray) -> np.ndarray:
    """Lleva el mínimo a 0 y el máximo a 255. Lineal, reversible, sin sorpresas.

    Es casi siempre la primera opción en inspección industrial: no inventa
    contraste donde no lo hay, sólo usa toda la escala. Su punto débil es que
    **un solo píxel extremo** —un reflejo, un píxel muerto del sensor— fija el
    máximo y anula el estiramiento para todos los demás.
    """
    minimo, maximo = float(imagen.min()), float(imagen.max())
    if maximo <= minimo:
        return imagen.copy()
    return (((imagen.astype(float) - minimo) / (maximo - minimo)) * 255).astype(np.uint8)


def ecualizar(imagen: np.ndarray) -> np.ndarray:
    """Redistribuye los valores para que el histograma quede plano.

    Es no lineal: dos píxeles que se diferenciaban en 1 pueden acabar
    diferenciándose en 30, o al revés. Saca detalle donde había mucha
    población, y **amplifica el ruido** donde había poca. En una pieza sobre
    fondo uniforme, ese fondo uniforme es justo donde vive el ruido.
    """
    histograma = np.bincount(imagen.ravel(), minlength=256)
    acumulado = histograma.cumsum().astype(float)
    acumulado = (acumulado - acumulado.min()) / max(acumulado.max() - acumulado.min(), 1)
    return (acumulado[imagen] * 255).astype(np.uint8)


# ── Medidas ───────────────────────────────────────────────────────────────

def calidad_del_histograma(imagen: np.ndarray) -> dict[str, float]:
    return {
        "rango": float(imagen.max() - imagen.min()),
        "desv": float(imagen.std()),
        "ocupacion_%": float((np.bincount(imagen.ravel(), minlength=256) > 0).mean() * 100),
    }


def calidad_de_la_tarea(imagen: np.ndarray, verdad: np.ndarray) -> dict[str, float]:
    """Umbraliza con Otsu y compara con la verdad-terreno.

    El IoU (intersección sobre unión) es la medida honesta aquí: la exactitud
    píxel a píxel engaña mucho cuando la pieza ocupa el 40 % de la imagen — un
    detector que diga «todo es fondo» acertaría el 60 %.
    """
    from skimage.filters import threshold_otsu

    umbral = float(threshold_otsu(imagen))
    mascara = imagen > umbral
    interseccion = float((mascara & verdad).sum())
    union = float((mascara | verdad).sum())
    return {
        "umbral_otsu": umbral,
        "iou": interseccion / union if union else 0.0,
    }


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)

    # Pieza bien expuesta y su verdad-terreno; después se subexpone a propósito
    # para tener la imagen «de planta» y saber a la vez cuál era la respuesta.
    buena, verdad_pieza = synthetic.pieza_individual(
        tamano=192, clase="NO_OK", defecto="mota", forma="rectangulo", semilla=4
    )
    f0, c0, f1, c1 = verdad_pieza.bbox
    verdad = np.zeros(buena.shape, dtype=bool)
    verdad[f0:f1, c0:c1] = True

    # Subexposición: se comprime todo el rango contra el extremo oscuro. Es lo
    # que da una nave mal iluminada con el tiempo de exposición corto que exige
    # una línea en movimiento.
    subexpuesta = np.clip(buena.astype(float) * 0.32 + 8, 0, 255).astype(np.uint8)

    realces = {
        "original (subexpuesta)": subexpuesta,
        "brillo +60": subir_brillo(subexpuesta),
        "contraste ×2": subir_contraste(subexpuesta),
        "estirado a [0,255]": estirar_contraste(subexpuesta),
        "ecualizado": ecualizar(subexpuesta),
    }

    print("\nESCENARIO A — la imagen que llega ya está limpia")
    print(f"{'realce':24s} {'rango':>6s} {'desv':>6s} {'ocup%':>6s} {'Otsu':>6s} {'IoU':>6s}")
    print("-" * 62)
    for nombre, imagen in realces.items():
        h = calidad_del_histograma(imagen)
        t = calidad_de_la_tarea(imagen, verdad)
        print(
            f"{nombre:24s} {h['rango']:>6.0f} {h['desv']:>6.1f} {h['ocupacion_%']:>6.1f} "
            f"{t['umbral_otsu']:>6.0f} {t['iou']:>6.3f}"
        )

    # ── Escenario B ──────────────────────────────────────────────────────
    # El anterior es demasiado limpio para ser una planta. Aquí el sensor mete
    # ruido **antes** de que nadie realce nada, que es el orden real de los
    # acontecimientos: el ruido entra en la captura, no en el post-proceso.
    rng = np.random.default_rng(4)
    ruido = rng.normal(0, 14, buena.shape)
    bien_con_ruido = np.clip(buena.astype(float) + ruido, 0, 255).astype(np.uint8)
    mal_con_ruido = np.clip((buena.astype(float) + ruido) * 0.32 + 8, 0, 255).astype(np.uint8)

    escenario_b = {
        "bien expuesta + ruido": bien_con_ruido,
        "subexpuesta + ruido": mal_con_ruido,
        # Sin caracteres fuera de cp1252 (nada de flechas Unicode): la consola
        # de Windows del aula usa esa página de códigos y un `UnicodeEncodeError`
        # a mitad de una demostración no lo entiende nadie.
        "  -> estirada despues": estirar_contraste(mal_con_ruido),
        "  -> ecualizada despues": ecualizar(mal_con_ruido),
    }

    print("\nESCENARIO B — el sensor mete ruido en la captura")
    print(f"{'realce':24s} {'rango':>6s} {'desv':>6s} {'ocup%':>6s} {'Otsu':>6s} {'IoU':>6s}")
    print("-" * 62)
    for nombre, imagen in escenario_b.items():
        h = calidad_del_histograma(imagen)
        t = calidad_de_la_tarea(imagen, verdad)
        print(
            f"{nombre:24s} {h['rango']:>6.0f} {h['desv']:>6.1f} {h['ocupacion_%']:>6.1f} "
            f"{t['umbral_otsu']:>6.0f} {t['iou']:>6.3f}"
        )

    ruta = viz.guardar(
        viz.rejilla(list(realces.values()), list(realces), columnas=5,
                    titulo_general="Realce de una pieza subexpuesta"),
        SALIDA / "realce_de_pieza.png",
    )
    print(f"\nFigura: {ruta}")

    ruta = viz.guardar(
        viz.rejilla(
            [subexpuesta, estirar_contraste(subexpuesta), ecualizar(subexpuesta)],
            ["subexpuesta", "estirado", "ecualizado"],
            columnas=3, titulo_general="Los dos realces que de verdad cambian el histograma",
        ),
        SALIDA / "realce_comparativa.png",
    )
    print(f"Figura: {ruta}")

    ious = [calidad_de_la_tarea(i, verdad)["iou"] for i in realces.values()]
    desvs = [calidad_del_histograma(i)["desv"] for i in realces.values()]
    print(
        f"\nEl histograma cambia muchísimo:  desviación de {min(desvs):.1f} a {max(desvs):.1f}"
        f"\nLa tarea, casi nada:             IoU de {min(ious):.3f} a {max(ious):.3f}"
    )

    print(
        "\nY eso NO es un fallo del ejemplo: es un teorema pequeño.\n"
        "\n"
        "  Umbralizar es comparar cada píxel con un número. Los cuatro realces\n"
        "  son funciones monótonas crecientes, y una función monótona no puede\n"
        "  cambiar el ORDEN de dos píxeles. Así que la partición que produce el\n"
        "  umbral es la misma; lo único que cambia es en qué valor cae. Mírese\n"
        "  la columna Otsu: 37, 97, 28, 85 — y el IoU quieto.\n"
        "\n"
        "  La ecualización sí pierde un poco (IoU 0.976). También tiene\n"
        "  explicación: es monótona pero no inyectiva. Al redondear a 8 bits\n"
        "  colapsa niveles vecinos, y ahí sí se destruye información. Se ve en\n"
        "  'ocup%', que baja de 10.2 a 6.6.\n"
        "\n"
        "  Y con ruido de sensor eso deja de ser 'un poco': en el escenario B,\n"
        "  ecualizar hunde el IoU de 0.997 a 0.834. Ecualizar reparte la escala\n"
        "  según cuántos píxeles hay en cada nivel, y en una imagen ruidosa\n"
        "  quien manda en ese reparto es el ruido del fondo. El único realce de\n"
        "  los cuatro que puede EMPEORAR la tarea es justo el más agresivo.\n"
        "\n"
        "Entonces, ¿para qué sirve realzar? Para que un humano lea la imagen, y\n"
        "para lo que venga después que no sea un umbral global — filtros,\n"
        "gradientes, umbral adaptativo (Clases 2 y 3). Lo que arregla una toma\n"
        "subexpuesta es la EXPOSICIÓN, no el post-proceso: el realce estira lo\n"
        "que hay, no añade lo que falta."
    )
    print(
        "\nPara discutir: en el escenario B, la bien expuesta y la subexpuesta\n"
        "dan el mismo IoU. ¿Significa eso que da igual exponer bien? ¿Qué\n"
        "columna de la tabla dice que no, y qué pasaría si el defecto a\n"
        "detectar fuese 20 veces más pequeño que la pieza?"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

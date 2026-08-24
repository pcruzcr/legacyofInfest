"""Convierte una hoja de referencia dibujada a un atlas que Tiled pueda cortar.

Por qué existe (AUD-494)
========================
Los modelos de imagen no producen atlas: producen ilustraciones. La hoja de
la Fase 1 salió con el contenido y el estilo correctos —superficie, relleno,
muro, cuatro variantes, esquinas, escalones, tierras y la decoración— pero
con las piezas flotando a tamaños distintos sobre fondo blanco, sin rejilla.
Tiled necesita lo contrario: celdas idénticas de 16x16, margen 0, espaciado
0, fondo transparente.

El paso intermedio es mecánico y es justo el que come el tiempo a mano: hay
que recortar cada pieza, escalarla a su huella real en baldosas, cuantizar
la paleta y montarlo todo en una rejilla. Eso hace esta herramienta.

Qué NO hace, a propósito
------------------------
No repasa los bordes de las baldosas repetibles. Reducir una ilustración a
16x16 siempre deja costura en los cantos, y eso se arregla mirando, en
Aseprite, no con una heurística. La herramienta deja el atlas listo para ese
repaso, no en su lugar.

Por qué reduce con área y no con vecino más cercano
---------------------------------------------------
La regla habitual —«pixel art se reduce con nearest, nunca con bilineal»—
vale cuando el origen *ya* es pixel art alineado a la rejilla. Aquí no lo
es: es una ilustración con estética de pixel art, cuyos «píxeles» no caen en
múltiplos exactos. Tomar una muestra por celda (nearest) elige un píxel
arbitrario de cada bloque y produce ruido; promediar el área y luego
cuantizar la paleta da un resultado mucho más limpio. La cuantización
posterior es la que devuelve los colores planos.

Uso
---
    python tools/hoja_a_tileset.py HOJA.png --salida assets/tilesets/x.png
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

#: Lado de la baldosa. El mismo que `src/engine/core/settings.py::TILE_SIZE`
#: y que declara el TMX del 4-1; no es configurable por capricho.
TS = 16

#: Columnas del atlas resultante. Ocho es lo que ya usa
#: `tools/generate_stage4_1.py::TS_COLUMNAS`, así que un atlas nuevo se lee
#: igual que el que hay.
COLUMNAS = 8

#: Cuánto tiene que separarse un píxel del blanco para contar como dibujo.
#: La hoja viene sobre blanco puro, pero el borde de cada pieza está
#: suavizado: con un umbral de 0 se recortarían las siluetas por dentro y
#: cada pieza perdería su contorno.
UMBRAL_DE_FONDO = 24


@dataclass(frozen=True)
class Pieza:
    """Una entrada de la hoja y qué ocupa en el mapa."""

    nombre: str
    #: Huella en baldosas, `(ancho, alto)`. La mayoría son 1x1; la lápida
    #: alta, la verja o el árbol no lo son, y escalarlas a una sola baldosa
    #: las volvería ilegibles.
    huella: tuple[int, int] = (1, 1)


#: El orden de la hoja de la Fase 1, leído de izquierda a derecha y de
#: arriba a abajo. Es el mismo orden que se pidió en el prompt: si la hoja
#: se regenera con otro contenido, esta tabla es lo único que hay que
#: reescribir.
FASE1: tuple[Pieza, ...] = (
    Pieza("cripta"), Pieza("cripta_relleno"), Pieza("muro"),
    Pieza("cripta_grieta"), Pieza("cripta_musgo"),
    Pieza("cripta_clara"), Pieza("cripta_partida"),
    Pieza("borde_izquierdo"), Pieza("borde_derecho"),
    Pieza("escalon_sube"), Pieza("escalon_baja"),
    Pieza("tierra_1"), Pieza("tierra_2"), Pieza("tierra_3"), Pieza("tierra_4"),
    Pieza("lapida_alta", (1, 2)), Pieza("lapida_baja"),
    Pieza("cruz_hierro", (1, 2)), Pieza("calavera"),
    Pieza("verja", (1, 2)), Pieza("porton", (2, 2)),
    Pieza("arbusto"), Pieza("macetero"),
    Pieza("angel", (1, 2)), Pieza("banco", (2, 1)),
    Pieza("farol", (1, 2)), Pieza("tronco", (1, 2)),
    Pieza("copa", (2, 2)), Pieza("zarza"),
    Pieza("charco"), Pieza("hojas"),
)


def quitar_el_fondo(hoja: Image.Image, umbral: int = UMBRAL_DE_FONDO) -> Image.Image:
    """Blanco de fondo a alfa 0, conservando el blanco *del dibujo*.

    Sólo se vacía el blanco conectado al borde de la imagen. Un relleno por
    inundación desde las cuatro esquinas distingue el fondo de, por ejemplo,
    la calavera o las flores blancas del arbusto, que también son casi
    blancas pero están rodeadas de dibujo. Umbralizar sin más las agujerearía.
    """
    rgba = hoja.convert("RGBA")
    ancho, alto = rgba.size
    px = rgba.load()
    assert px is not None

    def es_fondo(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        return a > 0 and min(r, g, b) >= 255 - umbral

    pila = [(x, y) for x in range(ancho) for y in (0, alto - 1) if es_fondo(x, y)]
    pila += [(x, y) for y in range(alto) for x in (0, ancho - 1) if es_fondo(x, y)]
    vistos = set(pila)
    while pila:
        x, y = pila.pop()
        r, g, b, _a = px[x, y]
        px[x, y] = (r, g, b, 0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < ancho and 0 <= ny < alto and (nx, ny) not in vistos:
                if es_fondo(nx, ny):
                    vistos.add((nx, ny))
                    pila.append((nx, ny))
    return rgba


def recortar_piezas(hoja: Image.Image) -> list[tuple[int, int, int, int]]:
    """Las cajas de cada pieza suelta, en orden de lectura.

    Se agrupan por filas antes de ordenar por x: ordenar sólo por `y` mezcla
    piezas de la misma fila que estén a alturas distintas —el ángel y el
    banco lo están— y el orden dejaría de corresponderse con la tabla.
    """
    cajas = _componentes(hoja)
    if not cajas:
        return []
    alto_tipico = sorted(y1 - y0 for _x0, y0, _x1, y1 in cajas)[len(cajas) // 2]
    filas: list[list[tuple[int, int, int, int]]] = []
    for caja in sorted(cajas, key=lambda c: c[1]):
        centro = (caja[1] + caja[3]) / 2
        for fila in filas:
            referencia = (fila[0][1] + fila[0][3]) / 2
            if abs(centro - referencia) < alto_tipico:
                fila.append(caja)
                break
        else:
            filas.append([caja])
    ordenadas: list[tuple[int, int, int, int]] = []
    for fila in filas:
        ordenadas.extend(sorted(fila, key=lambda c: c[0]))
    return ordenadas


def _componentes(hoja: Image.Image) -> list[tuple[int, int, int, int]]:
    """Cajas de los grupos de píxeles opacos conectados."""
    ancho, alto = hoja.size
    alfa = hoja.getchannel("A").load()
    assert alfa is not None
    visto = bytearray(ancho * alto)
    cajas = []
    for y0 in range(alto):
        for x0 in range(ancho):
            if visto[y0 * ancho + x0] or alfa[x0, y0] == 0:
                continue
            pila = [(x0, y0)]
            visto[y0 * ancho + x0] = 1
            minx = maxx = x0
            miny = maxy = y0
            while pila:
                x, y = pila.pop()
                minx, maxx = min(minx, x), max(maxx, x)
                miny, maxy = min(miny, y), max(maxy, y)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if not (0 <= nx < ancho and 0 <= ny < alto):
                            continue
                        i = ny * ancho + nx
                        if not visto[i] and alfa[nx, ny] > 0:
                            visto[i] = 1
                            pila.append((nx, ny))
            # Manchas de un par de píxeles: restos del suavizado del fondo,
            # no piezas.
            if (maxx - minx) >= 8 and (maxy - miny) >= 8:
                cajas.append((minx, miny, maxx + 1, maxy + 1))
    return cajas


def montar(
    hoja: Image.Image, piezas: tuple[Pieza, ...], colores: int = 40,
) -> tuple[Image.Image, list[str]]:
    """El atlas final y el nombre de la baldosa que ocupa cada hueco.

    El hueco 0 se deja vacío a propósito: es `vacio` en el contrato del 4-1
    y en Tiled es cómodo tener siempre una celda transparente al principio.
    """
    limpia = quitar_el_fondo(hoja)
    cajas = recortar_piezas(limpia)
    if len(cajas) < len(piezas):
        raise SystemExit(
            f"la hoja tiene {len(cajas)} piezas y la tabla espera {len(piezas)}: "
            f"revisa que ninguna se toque con otra ni se haya salido del fondo"
        )

    huecos: list[Image.Image] = [Image.new("RGBA", (TS, TS), (0, 0, 0, 0))]
    nombres: list[str] = ["vacio"]
    for pieza, caja in zip(piezas, cajas, strict=False):
        ancho_t, alto_t = pieza.huella
        recorte = limpia.crop(caja).resize(
            (ancho_t * TS, alto_t * TS), Image.Resampling.BOX,
        )
        for fila in range(alto_t):
            for col in range(ancho_t):
                trozo = recorte.crop(
                    (col * TS, fila * TS, (col + 1) * TS, (fila + 1) * TS),
                )
                huecos.append(trozo)
                sufijo = "" if pieza.huella == (1, 1) else f"_{col}{fila}"
                nombres.append(f"{pieza.nombre}{sufijo}")

    filas = -(-len(huecos) // COLUMNAS)
    atlas = Image.new("RGBA", (COLUMNAS * TS, filas * TS), (0, 0, 0, 0))
    for i, trozo in enumerate(huecos):
        atlas.paste(trozo, ((i % COLUMNAS) * TS, (i // COLUMNAS) * TS))
    return _aplanar_paleta(atlas, colores), nombres


def _aplanar_paleta(atlas: Image.Image, colores: int) -> Image.Image:
    """Cuantiza a una paleta corta, conservando la transparencia.

    Es este paso, y no la reducción, el que devuelve los colores planos que
    pide el estilo del proyecto: los demás tilesets del juego viven entre 18
    y 38 colores, y `scripts/validate_assets.py` documenta (AUD-011) que una
    cuenta alta en un atlas delata un export reescalado.
    """
    alfa = atlas.getchannel("A")
    plano = atlas.convert("RGB").quantize(
        colors=colores, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE,
    ).convert("RGBA")
    plano.putalpha(alfa.point(lambda v: 255 if v > 127 else 0))
    return plano


def escribir_tsx(destino: Path, imagen: Path, huecos: int, alto_px: int) -> None:
    """El `.tsx` que Tiled abre, con la rejilla ya declarada."""
    destino.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<tileset version="1.10" tiledversion="1.10.2" name="{imagen.stem}" '
        f'tilewidth="{TS}" tileheight="{TS}" tilecount="{huecos}" '
        f'columns="{COLUMNAS}" margin="0" spacing="0">\n'
        f' <image source="{imagen.name}" width="{COLUMNAS * TS}" '
        f'height="{alto_px}"/>\n'
        "</tileset>\n",
        encoding="utf-8",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("hoja", type=Path, help="la hoja de referencia (PNG)")
    ap.add_argument(
        "--salida", type=Path,
        default=Path("assets/tilesets/tileset_stage4_1_fase1.png"),
    )
    ap.add_argument("--colores", type=int, default=40)
    args = ap.parse_args()

    atlas, nombres = montar(Image.open(args.hoja), FASE1, args.colores)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(args.salida)
    tsx = args.salida.with_suffix(".tsx")
    escribir_tsx(tsx, args.salida, len(nombres), atlas.height)

    print(f"{args.salida}  {atlas.width}x{atlas.height}px  {len(nombres)} huecos")
    print(f"{tsx}  (ábrelo en Tiled)")
    for i, nombre in enumerate(nombres):
        print(f"  gid {i + 1:>3}  {nombre}")


if __name__ == "__main__":
    main()

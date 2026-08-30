"""art_lib: paleta maestra compartida + helpers de textura pixel-art reutilizables.

Origen
------
Extraido de `tools/vignette_reference.py` (la prueba de vineta crepuscular de
480x224 aprobada por el usuario el 2026-07-23) — el estandar visual congelado
para el arte del mapa de este boss. Todo lo de abajo es o bien una copia
byte-identica de los datos/logica del original, o una generalizacion directa
de estos (globales hardcodeados como ``canvas``/``W``/``H``/``PAL`` reemplazados
por parametros para que la misma tecnica pueda correr sobre cualquier
arreglo/paleta). Ningun valor de color fue "mejorado" ni re-derivado — la
paleta de aqui debe permanecer byte-identica a la vineta aprobada para que los
generadores subsiguientes (tileset, TMX) compartan una sola verdad visual.

Que expone este modulo
-------------------------
- ``PALETTE``: la paleta maestra de 34 colores, nombre -> (r, g, b). Una vista
  ``types.MappingProxyType`` de solo lectura (endurecimiento de revision de
  calidad: sigue soportando ``len()``/indexado/``.values()``/``.items()`` como
  un dict normal, pero no puede mutarse por accidente).
- ``hash01(x, y, salt=0)``: ruido pseudo-aleatorio determinista por pixel en
  [0, 1). Copia fiel; sustenta tanto a ``mottle`` como al propio desglose
  por pixel de la vineta en todas partes (nubes, cesped, grietas, ...).
- ``BAYER_4X4``: la matriz de ordered-dither 4x4, normalizada a [0, 1).
  De solo lectura (``setflags(write=False)``: endurecimiento de revision de
  calidad).
- ``bayer_dither(x, y, a, b, t)``: eleccion de dither ordenado (Bayer) entre
  dos valores. Copia fiel del ``dither2`` del original.
- ``mottle(x, y, salt=0)``: offset de ruido agrupado multi-octava
  (grueso/medio/fino), extraido de la formula de moteado de estuco de
  ``wall_tone()`` (el muro hastial de la vineta). Con ``salt=45`` reproduce
  exactamente el moteado de ese muro (el original encadenaba los salts
  45/46/47 para sus tres octavas; aqui un solo ``salt`` siembra las tres como
  salt/salt+1/salt+2).
- ``despeckle(canvas, palette, protect_keys=(), min_majority=6)``: version
  generalizada del ``despeckle_key()`` del original — limpia huerfanos de
  color de un solo pixel aislado reemplazandolos con el color mayoritario de
  su vecindario, saltando cualquier color listado en ``protect_keys``. No
  toca el borde exterior de 1px del canvas (ver su propio docstring).
- ``quantize_to_palette(rgb, palette)``: NO presente en el original (el cual
  pinta a mano cada pixel con un color de paleta con nombre directamente y
  nunca necesita ajustar un color arbitrario). Anadido aqui como tecnica
  fundacional para generadores posteriores que puedan sintetizar color de
  forma procedural y necesiten ajustarlo de vuelta a la paleta congelada.
  Cuantizacion estandar de color mas cercano (Euclidiana, espacio RGB); solo
  retorna valores que ya estan en ``palette``.

Mapa de nombres (original -> aqui)
----------------------------
- ``PAL`` -> ``PALETTE`` (mismos 34 nombres de clave: S0-S5, W0-W2, F0, O0-O3, R0-R2,
  C0-C1, V0-V3, G0-G3, K0-K1, P0-P1, RM, RC, PL — sin cambios).
- ``BAYER`` -> ``BAYER_4X4``.
- ``dither2`` -> ``bayer_dither`` (misma firma/cuerpo).
- la expresion inline ``mott = ...`` dentro de ``wall_tone()`` -> ``mottle()``.
- ``despeckle_key()`` -> ``despeckle()`` (globales promovidos a parametros).
- ``hx()`` -> ``_hx()``: se mantiene privada. Es un helper de literal de un
  solo uso, usado solo para construir ``PALETTE`` abajo, no una tecnica de
  textura reutilizable, asi que no forma parte de la superficie publica de
  este modulo.

Las funciones de composicion del original (``build_sky``, ``build_hastial``,
``draw_crack``, los patrones inline del techo corrugado, etc.) son
especificas de la escena — pintan directamente sobre la geometria/canvas fijo
de esa vineta — y a proposito NO se extraen aqui. Lo mismo aplica a cualquier
cosa que requiera que exista una funcion independiente en el original que no
existe (p. ej. "corrugated sheet" y "grass" son one-liners inline dispersos
por edificio/parche, no helpers reutilizables).

Este modulo no tiene efectos secundarios al importarse: sin I/O de archivos,
sin ploteo, sin asignacion de canvas. Cualquier codigo de demo/prueba
pertenece bajo el propio ``if __name__ == "__main__":`` de quien lo llame,
no aqui.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import TypeVar

import numpy as np

T = TypeVar("T")


def _hx(h: str) -> tuple[int, int, int]:
    """Cadena hex ('#RRGGBB' o 'RRGGBB') -> tupla int (r, g, b). Copia fiel.

    Privada: un helper de literal de un solo uso, usado solo para construir
    ``PALETTE`` abajo; no una tecnica de textura reutilizable, asi que no se
    exporta.
    """
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ---------------------------------------------------------------------------
# PALETA MAESTRA — byte-identica a vignette_reference.PAL (34 colores).
# Envuelta en MappingProxyType: de solo lectura, pero sigue soportando len(),
# .values(), .keys(), .items() e indexado palette[name] exactamente como un
# dict normal.
# ---------------------------------------------------------------------------
PALETTE: Mapping[str, tuple[int, int, int]] = MappingProxyType({
    # cielo (arriba -> horizonte), 6
    "S0": _hx("#2A2150"), "S1": _hx("#463A6E"), "S2": _hx("#6E4E7E"),
    "S3": _hx("#9C5E76"), "S4": _hx("#C86C4E"), "S5": _hx("#E8853C"),
    # calido / resplandor, 3
    "W0": _hx("#F2C878"), "W1": _hx("#F5E1A0"), "W2": _hx("#FFF6D0"),
    # silueta lejana, 1
    "F0": _hx("#2E2448"),
    # muro de estuco ocre, 4  (mostaza opaca de crepusculo, base ~#C99046)
    "O0": _hx("#47301F"), "O1": _hx("#6E4A2A"), "O2": _hx("#A2743A"), "O3": _hx("#C6934C"),
    # tejado de terracota, 3  (opaco de crepusculo ~#C74A32)
    "R0": _hx("#2A1418"), "R1": _hx("#6E2E22"), "R2": _hx("#A04A32"),
    # cenefa (fascia crema-blanco), 2
    "C0": _hx("#E6DCC6"), "C1": _hx("#9A8266"),
    # vegetacion, 4
    "V0": _hx("#10160E"), "V1": _hx("#1E2C18"), "V2": _hx("#33482A"), "V3": _hx("#547038"),
    # acera de piedra, 4
    "G0": _hx("#332C2A"), "G1": _hx("#574B44"), "G2": _hx("#7C6C5C"), "G3": _hx("#A08A72"),
    # tinta, 2
    "K0": _hx("#0C0A0C"), "K1": _hx("#1E1620"),
    # flores, 2
    "P0": _hx("#A83A34"), "P1": _hx("#D06048"),
    # borde frio, 1
    "RM": _hx("#B49AB0"),
    # pasada de joyeria: luz de borde AA fria-violeta + yeso claro expuesto (desconchados), 2
    "RC": _hx("#9AA8CE"),   # borde violeta-azul frio en bordes de silueta superior / estrellas
    "PL": _hx("#C9B48A"),   # yeso palido revelado por estuco desconchado
})


def hash01(x: int, y: int, salt: int = 0) -> float:
    """Ruido pseudo-aleatorio determinista en [0, 1) para el pixel (x, y). Copia fiel."""
    v = (x * 374761393 + y * 668265263 + salt * 2246822519) & 0xFFFFFFFF
    v = (v ^ (v >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0


# Ordered dithering (Bayer 4x4), normalizado a [0, 1). Copia fiel de BAYER.
# De solo lectura (setflags(write=False)): constante compartida, nunca pensada para mutarse.
BAYER_4X4: np.ndarray = np.array([
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
], dtype=np.float32) / 16.0
BAYER_4X4.setflags(write=False)


def bayer_dither(x: int, y: int, a: T, b: T, t: float) -> T:
    """Eleccion de dither ordenado (Bayer 4x4) entre dos valores.

    Retorna ``b`` si ``t`` (fraccion hacia ``b``, 0..1) supera el umbral de
    dither en (x, y); si no, ``a``. Copia fiel del ``dither2`` del original;
    ``a``/``b`` son tipicamente nombres de paleta pero pueden ser cualquier cosa.
    """
    return b if t > BAYER_4X4[y & 3, x & 3] else a


def mottle(x: int, y: int, salt: int = 0) -> float:
    """Ruido de moteado agrupado multi-octava (grueso+medio+fino).

    Extraido de la formula de moteado de estuco de ``wall_tone()`` en la
    vineta (campo de agrupamiento suave, sin veta direccional): tres octavas
    de ``hash01`` con tamanos de agrupamiento de 5px/3px/1px con amplitud
    decreciente, sumadas. Retorna un offset flotante con signo (~-0.14..0.14)
    pensado para sumarse a una luminancia/umbral base antes de mapearlo a una
    rampa de paleta.

    ``salt`` siembra las tres octavas (como salt, salt+1, salt+2); el muro
    hastial original usaba los salts 45/46/47, es decir, ``mottle(x, y, salt=45)``
    lo reproduce exactamente.
    """
    return (
        (hash01(x // 5, y // 5, salt) - 0.5) * 0.15
        + (hash01(x // 3, y // 3, salt + 1) - 0.5) * 0.09
        + (hash01(x, y, salt + 2) - 0.5) * 0.04
    )


def quantize_to_palette(
    rgb: Iterable[int] | np.ndarray,
    palette: dict[str, tuple[int, int, int]],
) -> np.ndarray:
    """Ajusta un color RGB (o arreglo de colores) al color mas cercano en `palette`.

    No presente en vignette_reference.py — anadido como tecnica fundacional
    para generadores que sintetizan color de forma procedural (p. ej. a partir
    de ruido o fotos de referencia) y necesitan ajustarlo de vuelta a la
    paleta congelada. Color mas cercano por distancia Euclidiana al cuadrado
    en espacio RGB.

    ``rgb`` puede ser una unica tupla/secuencia (r, g, b) o un arreglo numpy
    de forma (..., 3). Retorna el/los valor(es) de paleta coincidente(s) como
    uint8, en la misma forma que la entrada (nunca un color ausente de
    `palette`).
    """
    names = list(palette.keys())
    values = np.array([palette[n] for n in names], dtype=np.float32)  # (K, 3)
    arr = np.asarray(rgb, dtype=np.float32)
    single = arr.ndim == 1
    if single:
        arr = arr[None, :]
    orig_shape = arr.shape
    flat = arr.reshape(-1, 3)
    d = ((flat[:, None, :] - values[None, :, :]) ** 2).sum(axis=2)
    idx = d.argmin(axis=1)
    out = values[idx].astype(np.uint8).reshape(orig_shape)
    return out[0] if single else out


def despeckle(
    canvas: np.ndarray,
    palette: dict[str, tuple[int, int, int]],
    protect_keys: Iterable[str] = (),
    min_majority: int = 6,
) -> np.ndarray:
    """Limpia huerfanos de color de un solo pixel aislado en `canvas`.

    Generalizado a partir del ``despeckle_key()`` del original (el cual
    hardcodeaba el ``canvas``/``H``/``W``/``PAL`` globales y una lista de
    proteccion fija): para cada pixel cuyo color no coincide con ninguno de
    sus 8 vecinos y no esta en `protect_keys` (nombres de paleta para dejar
    intactos, p. ej. acentos brillantes escasos que estan pensados para
    quedar aislados), lo reemplaza con el color vecino mayoritario si al
    menos `min_majority` de los 8 vecinos coinciden en uno.

    `canvas` es un arreglo uint8 (H, W, 3), mutado in situ. `palette` es el
    dict nombre -> (r, g, b) usado para resolver `protect_keys`. Retorna
    `canvas`.

    Advertencia (fiel al original): el borde exterior de 1px del canvas
    nunca se procesa — el original itera ``range(1, H-1)`` / ``range(1,
    W-1)``, asi que cada pixel que realmente inspecciona tiene un anillo
    completo de 8 vecinos; los pixeles de borde quedan exactamente como
    estaban, sean huerfanos o no.
    """
    H, W = canvas.shape[:2]
    packed = (
        (canvas[:, :, 0].astype(np.int32) << 16)
        | (canvas[:, :, 1].astype(np.int32) << 8)
        | canvas[:, :, 2]
    )
    protect = set()
    for k in protect_keys:
        r, g, b = palette[k]
        protect.add((r << 16) | (g << 8) | b)
    src = packed.copy()
    for y in range(1, H - 1):
        rowm1 = src[y - 1]; row = src[y]; rowp1 = src[y + 1]
        for x in range(1, W - 1):
            cpx = row[x]
            if cpx in protect:
                continue
            n = (rowm1[x - 1], rowm1[x], rowm1[x + 1], row[x - 1], row[x + 1],
                 rowp1[x - 1], rowp1[x], rowp1[x + 1])
            if cpx in n:
                continue                                    # no aislado
            best = None; bc = 0
            for v in n:
                cc = n.count(v)
                if cc > bc:
                    bc = cc; best = v
            if bc >= min_majority:                           # mayoria fuerte -> pixel de borde extraviado
                canvas[y, x] = (best >> 16 & 255, best >> 8 & 255, best & 255)
    return canvas

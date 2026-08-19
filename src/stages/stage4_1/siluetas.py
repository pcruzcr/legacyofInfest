"""
Las siluetas del fondo: los espíritus vencidos y la Cegua.

Qué son y qué NO son
=====================
El lore (§3.4) dice de los ecos: *«Los ecos de los espíritus vencidos —los
cuernos del venado, la masa enroscada del Rey, las alas del Gavilán— aparecen
como siluetas en el fondo. No atacan. **Testifican.**»*

Y el diseño (§4) dice de la Cegua: *«No es un enemigo de combate: es una
presencia. Nunca se dibuja como caricatura, nunca se burla de ella, y no recibe
daño ni se derrota.»*

Así que aquí no hay entidades. No hay colisión, no hay IA, no hay salud y no
hay daño: son **contornos** dibujados en el fondo, detrás del mapa de baldosas,
por el gancho `dibujar_fondo` que AUD-162 añadió a `StageScene`. Si alguna vez
alguien quiere que ataquen, tendrá que escribirlas de cero como enemigos — y
eso rompería la regla de oro del nivel, que es no tener ninguno.

Por qué contornos y no sprites (para la decoración de fase)
-------------------------------------------------------------
El proyecto no tiene arte de bosque cortado, cruces de conquistador ni un
horizonte por fase, y generar un PNG inventado sería arte falso que luego hay
que mantener. Un contorno dibujado con polígonos es honesto: se lee como «una
forma en la niebla», que es exactamente lo que el diseño pide, y no finge ser
una ilustración terminada. Esto sigue siendo cierto para `_arbol_cortado`,
las cruces, la Cegua y la Bruja — nadie les dio arte propio todavía.

Los tres espíritus SÍ tienen arte (AUD-561)
---------------------------------------------
Jugado, el dueño señaló que las siluetas de Venado, Rey Terciopelo y Gavilán
«se ven raras» — un contorno de polígono no se lee como un venado o un
gavilán, sólo como una forma abstracta cualquiera. A diferencia del bosque
cortado o las cruces, el proyecto SÍ tiene arte real de estos tres: cada uno
fue jefe de una zona anterior (`assets/sprites/bosses/boss_venado_*.png`,
`boss_rey_*.png`, `boss_gavilan_*.png`). `silueta_desde_sprite` recorta un
fotograma de ese arte real y lo aplana a un color sólido usando su canal
alfa como máscara — sigue siendo una silueta, no el jefe a todo color, para
no leerse como «el jefe está aquí, en combate»; sólo que ahora la forma es
la de verdad. `ESPIRITUS` (los generadores de polígono de abajo) se
conservan como red de seguridad si algún día falta el sprite.
"""
from __future__ import annotations

import math

import pygame

from src.engine.core import settings

#: Verde espectral del cementerio. El mismo del canon y el mismo con el que se
#: encienden los braseros del mapa.
VERDE_ESPECTRAL: tuple[int, int, int] = (124, 255, 160)

#: La Cegua se dibuja en un blanco frío, no en el verde de los espíritus: no
#: es uno de los vencidos, es otra cosa que estaba aquí antes.
BLANCO_CEGUA: tuple[int, int, int] = (214, 226, 236)


def _venado(ancho: int, alto: int) -> list[tuple[float, float]]:
    """Cuernos y lomo. La prueba de los reflejos (lore §2.4)."""
    w, h = ancho, alto
    return [
        (0.10 * w, 1.00 * h), (0.16 * w, 0.55 * h), (0.30 * w, 0.42 * h),
        # la cornamenta: tres puntas a cada lado
        (0.34 * w, 0.10 * h), (0.40 * w, 0.30 * h), (0.46 * w, 0.02 * h),
        (0.52 * w, 0.28 * h), (0.60 * w, 0.08 * h), (0.64 * w, 0.38 * h),
        (0.78 * w, 0.48 * h), (0.90 * w, 0.72 * h), (0.86 * w, 1.00 * h),
        (0.62 * w, 0.86 * h), (0.34 * w, 0.88 * h),
    ]


def _serpiente(ancho: int, alto: int) -> list[tuple[float, float]]:
    """La masa enroscada del Rey Terciopelo (lore §3.2)."""
    puntos: list[tuple[float, float]] = []
    vueltas = 2.4
    for i in range(26):
        t = i / 25.0
        angulo = t * vueltas * math.tau
        radio = (1.0 - t * 0.72) * 0.42
        puntos.append((
            (0.5 + radio * math.cos(angulo)) * ancho,
            (0.62 + radio * 0.8 * math.sin(angulo)) * alto,
        ))
    # La cabeza levantada, que es lo que la hace leerse como serpiente y no
    # como una espiral cualquiera.
    puntos.append((0.74 * ancho, 0.18 * alto))
    puntos.append((0.90 * ancho, 0.10 * alto))
    puntos.append((0.80 * ancho, 0.30 * alto))
    return puntos


def _gavilan(ancho: int, alto: int) -> list[tuple[float, float]]:
    """Las alas del Gavilán Camionero Mascarero (lore §3.3)."""
    w, h = ancho, alto
    return [
        (0.02 * w, 0.44 * h), (0.22 * w, 0.24 * h), (0.40 * w, 0.40 * h),
        (0.46 * w, 0.22 * h), (0.54 * w, 0.22 * h), (0.60 * w, 0.40 * h),
        (0.78 * w, 0.24 * h), (0.98 * w, 0.44 * h),
        (0.72 * w, 0.52 * h), (0.56 * w, 0.86 * h),
        (0.50 * w, 1.00 * h), (0.44 * w, 0.86 * h), (0.28 * w, 0.52 * h),
    ]


def _sombra_difusa(ancho: int, alto: int) -> list[tuple[float, float]]:
    """Una mancha que cruza el cielo, sin ala ni pico que la identifiquen
    (AUD-513, GAP-062 punto 10): *«no debería aparecer como un sprite
    claramente identificable cada vez... queremos presencia, no
    exposición»*. La variante que rompe la costumbre de ver siempre al
    Gavilán en `_gavilan`: un óvalo alargado e irregular — podría ser un
    ave, una nube baja, o nada."""
    w, h = ancho, alto
    return [
        (0.00 * w, 0.55 * h), (0.10 * w, 0.30 * h), (0.30 * w, 0.15 * h),
        (0.55 * w, 0.10 * h), (0.78 * w, 0.20 * h), (0.94 * w, 0.42 * h),
        (1.00 * w, 0.58 * h), (0.86 * w, 0.72 * h), (0.62 * w, 0.82 * h),
        (0.35 * w, 0.78 * h), (0.14 * w, 0.68 * h),
    ]


def _cegua(ancho: int, alto: int) -> list[tuple[float, float]]:
    """Figura montada, de pie, mirando al sendero.

    Deliberadamente sobria: una silueta erguida sobre una montura. La regla del
    diseño (§4) es tratar lo folclórico con la misma dignidad que lo sagrado,
    así que no se caricaturiza nada — es una forma quieta en la niebla.
    """
    w, h = ancho, alto
    return [
        # la montura
        (0.10 * w, 1.00 * h), (0.14 * w, 0.62 * h), (0.30 * w, 0.54 * h),
        (0.62 * w, 0.54 * h), (0.80 * w, 0.60 * h), (0.86 * w, 0.44 * h),
        (0.94 * w, 0.46 * h), (0.90 * w, 0.66 * h), (0.92 * w, 1.00 * h),
        (0.80 * w, 0.78 * h), (0.34 * w, 0.78 * h), (0.24 * w, 1.00 * h),
        # la figura erguida encima
        (0.40 * w, 0.54 * h), (0.42 * w, 0.20 * h), (0.50 * w, 0.10 * h),
        (0.58 * w, 0.20 * h), (0.58 * w, 0.54 * h),
    ]


def _bruja(ancho: int, alto: int) -> list[tuple[float, float]]:
    """Una figura encorvada cruzando el cielo (AUD-210).

    Diseñada para el pozo vertical de cinco actos (AUD-210, «acto IV: 2–3
    cruzan con el relámpago») y sin uso desde el rebuild horizontal
    (AUD-467): la forma quedó dibujada y sin nadie que la llamara. AUD-475
    le da un papel nuevo en el pasillo de seis fases — la percepción falsa
    de la Fase 3, ver `Stage4_1._dibujar_bruja` — que además es justo lo
    que pide la crítica de diseño del dueño (2026-08-14, punto 3): *«el
    jugador debe dejar de confiar completamente en sus sentidos»*. Como la
    Cegua, no es enemigo y no se caricaturiza: es una silueta con capa,
    alargada por el viaje, y la escoba se lee por la línea horizontal de
    abajo — no hace falta dibujar más para que se entienda qué es.
    """
    w, h = ancho, alto
    return [
        # la escoba, de punta a punta
        (0.00 * w, 0.86 * h), (0.30 * w, 0.78 * h), (1.00 * w, 0.72 * h),
        (0.94 * w, 0.80 * h), (0.34 * w, 0.86 * h),
        # la figura encorvada encima
        (0.30 * w, 0.78 * h), (0.26 * w, 0.46 * h), (0.34 * w, 0.20 * h),
        (0.46 * w, 0.06 * h), (0.62 * w, 0.00 * h), (0.54 * w, 0.16 * h),
        (0.58 * w, 0.34 * h), (0.52 * w, 0.58 * h), (0.46 * w, 0.76 * h),
        # la capa, que es lo que la hace leerse en movimiento
        (0.20 * w, 0.62 * h), (0.06 * w, 0.70 * h), (0.18 * w, 0.74 * h),
    ]


#: Las tres formas de los vencidos, en el orden en que se derrotan. Se
#: conservan como red de seguridad de `_dibujar_espiritu` — ver
#: `silueta_desde_sprite` más abajo para el camino principal (AUD-561).
ESPIRITUS: tuple[tuple[str, object], ...] = (
    ("venado", _venado),
    ("serpiente", _serpiente),
    ("gavilan", _gavilan),
)


# ── Las siluetas de los tres espíritus, desde su arte real (AUD-561) ────
#
# `(archivo, ancho de fotograma, alto de fotograma)`, en el mismo orden que
# `ESPIRITUS` (0=Venado, 1=Rey Terciopelo, 2=Gavilán). Los tamaños de
# fotograma son los mismos que ya usa cada jefe real para cargar su propia
# hoja de sprites — `boss_venado.py` (`_load_boss_sprites(..., 48, 48)`),
# `boss_rey.py` (`"walk": (40, 56)`), `boss_gavilan.py`
# (`_load_boss_sprites("boss_gavilan", 56, 40)`) — así que el primer
# fotograma de cada hoja recorta una pose completa, no una mitad de dos
# fotogramas distintos.
SPRITE_DE_ESPIRITU: tuple[tuple[str, int, int], ...] = (
    ("boss_venado_drift.png", 48, 48),
    ("boss_rey_walk.png", 40, 56),
    ("boss_gavilan_glide.png", 56, 40),
)

#: Silueta base (color sólido, tamaño de fotograma original) por
#: `(archivo, color)`. `None` significa «se buscó y no está» — para no
#: repetir el intento de carga en cada fotograma dibujado si el archivo de
#: verdad falta.
_CACHE_SILUETA_DE_SPRITE: dict[tuple[str, tuple[int, int, int]], pygame.Surface | None] = {}

#: Silueta ya escalada al tamaño de pantalla en que se dibuja, por
#: `(archivo, color, ancho, alto)`. `pygame.transform.smoothscale` no es
#: gratis; sin esta caché se pagaría una vez por fotograma dibujado en vez
#: de una vez por combinación — la misma lección que ya dejó `_lienzo_
#: horizonte` (AUD-514) con el horizonte lejano.
_CACHE_SILUETA_ESCALADA: dict[
    tuple[str, tuple[int, int, int], int, int], pygame.Surface] = {}


def silueta_desde_sprite(
    archivo: str, ancho_fotograma: int, alto_fotograma: int,
    color: tuple[int, int, int],
) -> pygame.Surface | None:
    """El primer fotograma de `archivo`, recortado a silueta plana de
    `color` usando su canal alfa como máscara. `None` si el archivo no
    existe — quien llama decide qué hacer (`_dibujar_espiritu` cae al
    contorno de polígono)."""
    clave = (archivo, color)
    if clave in _CACHE_SILUETA_DE_SPRITE:
        return _CACHE_SILUETA_DE_SPRITE[clave]
    ruta = settings.ASSETS_DIR / "sprites" / "bosses" / archivo
    silueta: pygame.Surface | None = None
    if ruta.exists():
        hoja = pygame.image.load(str(ruta)).convert_alpha()
        fotograma = hoja.subsurface(
            pygame.Rect(0, 0, ancho_fotograma, alto_fotograma)).copy()
        mascara = pygame.mask.from_surface(fotograma, threshold=10)
        silueta = mascara.to_surface(
            setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
    _CACHE_SILUETA_DE_SPRITE[clave] = silueta
    return silueta


def dibujar_silueta_de_sprite(
    surface: pygame.Surface, archivo: str, ancho_fotograma: int,
    alto_fotograma: int, x: int, y: int, ancho: int, alto: int,
    color: tuple[int, int, int], alfa: int,
) -> bool:
    """Pinta la silueta de `silueta_desde_sprite`, escalada a `(ancho, alto)`
    y desvanecida al `alfa` de este fotograma. Devuelve si dibujó algo, para
    que `_dibujar_espiritu` sepa si hace falta el contorno de respaldo.

    El alfa no se hornea en la silueta cacheada —eso volvería la caché
    inútil, porque `alfa` cambia con el fundido de entrada y salida en cada
    fotograma— sino que se aplica sobre una copia con
    `pygame.BLEND_RGBA_MULT`, el mismo truco que ya usa el motor para
    combinar un alfa por fotograma con una superficie de alfa por píxel.
    """
    if alfa <= 0 or ancho <= 0 or alto <= 0:
        return False
    base = silueta_desde_sprite(archivo, ancho_fotograma, alto_fotograma, color)
    if base is None:
        return False
    clave = (archivo, color, ancho, alto)
    escalada = _CACHE_SILUETA_ESCALADA.get(clave)
    if escalada is None:
        escalada = pygame.transform.smoothscale(base, (ancho, alto))
        _CACHE_SILUETA_ESCALADA[clave] = escalada
    capa = escalada
    if alfa < 255:
        capa = escalada.copy()
        capa.fill((255, 255, 255, max(0, min(255, alfa))),
                 special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(capa, (x, y))
    return True


# ── Decoración de fondo por fase (AUD-465) ──────────────────────
#
# Igual que los espíritus: contornos, no PNG. El proyecto no tiene arte de
# bosque cortado ni de cruces de conquistador, y dibujar un contorno es
# honesto —«una forma en la niebla»— mientras que un PNG inventado fingiría
# ser arte terminado.

#: Silueta oscura para lo que no es espectral: un árbol muerto no brilla.
SILUETA_OSCURA: tuple[int, int, int] = (24, 20, 30)
#: Piedra fría, la misma familia que `BLANCO_CEGUA` — las cruces son piedra,
#: no presencia, así que un blanco algo más apagado.
PIEDRA_FRIA: tuple[int, int, int] = (188, 196, 204)


def _arbol_cortado(ancho: int, alto: int) -> list[tuple[float, float]]:
    """Un árbol seco, cortado a media altura — «bosque cortado y muerto»
    (§Fase 4 del diseño). Dos ramas rotas y el tronco en punta astillada, no
    una copa: lo que distingue un árbol talado de uno que sólo perdió las
    hojas es que el corte se ve."""
    w, h = ancho, alto
    return [
        (0.42 * w, 1.00 * h), (0.40 * w, 0.55 * h), (0.28 * w, 0.40 * h),
        (0.36 * w, 0.38 * h), (0.32 * w, 0.18 * h), (0.40 * w, 0.34 * h),
        (0.46 * w, 0.32 * h), (0.50 * w, 0.04 * h), (0.54 * w, 0.30 * h),
        (0.60 * w, 0.32 * h), (0.68 * w, 0.16 * h), (0.64 * w, 0.36 * h),
        (0.72 * w, 0.42 * h), (0.60 * w, 0.56 * h), (0.58 * w, 1.00 * h),
    ]


def _arbol_caido(ancho: int, alto: int) -> list[tuple[float, float]]:
    """El mismo árbol cortado de `_arbol_cortado`, ahora en el suelo — el
    cambio de escenario que el silencio súbito de la Fase 4 deja atrás
    (AUD-513, GAP-062 punto 13: *«un árbol que antes estaba en pie ahora
    está caído... el jugador reconstruye que algo ocurrió sin que se le
    muestre qué»*). Tronco horizontal, no vertical — es lo único que hace
    falta para que se lea «cayó» en vez de «es igual que antes»."""
    w, h = ancho, alto
    return [
        (0.00 * w, 0.82 * h), (0.06 * w, 0.68 * h), (0.20 * w, 0.66 * h),
        (0.16 * w, 0.56 * h), (0.30 * w, 0.60 * h), (0.28 * w, 0.48 * h),
        (0.42 * w, 0.52 * h), (0.48 * w, 0.42 * h), (0.58 * w, 0.50 * h),
        (0.70 * w, 0.46 * h), (0.66 * w, 0.56 * h), (0.80 * w, 0.58 * h),
        (0.94 * w, 0.70 * h), (0.90 * w, 0.82 * h), (0.60 * w, 0.90 * h),
        (0.30 * w, 0.90 * h),
    ]


def _cruz_conquistador(ancho: int, alto: int) -> list[tuple[float, float]]:
    """Una cruz de piedra, la de los que no volvieron — la Planicie de los
    Muertos representa también a los conquistadores caídos aquí (§Fase 5)."""
    w, h = ancho, alto
    return [
        (0.41 * w, 1.00 * h), (0.41 * w, 0.36 * h), (0.15 * w, 0.36 * h),
        (0.15 * w, 0.22 * h), (0.41 * w, 0.22 * h), (0.41 * w, 0.00 * h),
        (0.59 * w, 0.00 * h), (0.59 * w, 0.22 * h), (0.85 * w, 0.22 * h),
        (0.85 * w, 0.36 * h), (0.59 * w, 0.36 * h), (0.59 * w, 1.00 * h),
    ]


def _cruz_caida(ancho: int, alto: int) -> list[tuple[float, float]]:
    """Una cruz de piedra, quebrada e inclinada — otro de los que no
    volvieron, no el mismo de siempre (AUD-513, GAP-063 punto 21: *«árbol
    muerto, torre, capilla, roca, grupo de tumbas»* — landmarks distintos
    entre sí, para poder decir «estoy cerca de aquella» en vez de ver la
    misma cruz repetida)."""
    w, h = ancho, alto
    return [
        (0.10 * w, 1.00 * h), (0.16 * w, 0.66 * h), (0.02 * w, 0.54 * h),
        (0.08 * w, 0.48 * h), (0.22 * w, 0.58 * h), (0.30 * w, 0.42 * h),
        (0.42 * w, 0.30 * h), (0.56 * w, 0.20 * h), (0.50 * w, 0.32 * h),
        (0.62 * w, 0.30 * h), (0.58 * w, 0.42 * h), (0.44 * w, 0.52 * h),
        (0.34 * w, 0.66 * h), (0.30 * w, 1.00 * h),
    ]


def _grupo_de_tumbas(ancho: int, alto: int) -> list[tuple[float, float]]:
    """Tres montículos bajos, no una sola cruz — el tercer landmark de la
    Planicie (AUD-513, GAP-063 punto 21)."""
    w, h = ancho, alto
    return [
        (0.00 * w, 1.00 * h), (0.02 * w, 0.70 * h), (0.16 * w, 0.58 * h),
        (0.30 * w, 0.68 * h), (0.32 * w, 1.00 * h), (0.36 * w, 0.72 * h),
        (0.50 * w, 0.52 * h), (0.66 * w, 0.66 * h), (0.68 * w, 1.00 * h),
        (0.72 * w, 0.78 * h), (0.86 * w, 0.64 * h), (1.00 * w, 0.80 * h),
        (0.98 * w, 1.00 * h),
    ]


#: Las tres siluetas de landmark de la Planicie de los Muertos, en el orden
#: en que se reparten por columna (AUD-513, GAP-063 punto 21).
LANDMARKS_DE_LA_PLANICIE: tuple[object, ...] = (
    _cruz_conquistador, _cruz_caida, _grupo_de_tumbas,
)


#: Cálido y sobrio — no el blanco frío de la Cegua ni el verde espectral de
#: los jefes. El easter egg personal (§7 del diseño, AUD-467) es un
#: recuerdo de familia, no una presencia folclórica ni un vencido: se
#: dibuja distinto a propósito.
BLANCO_RECUERDO: tuple[int, int, int] = (232, 230, 214)


def _fantasma(ancho: int, alto: int) -> list[tuple[float, float]]:
    """Una figura de pie, en calma. El easter egg personal de la Fase 1: dos
    lápidas —Teresa Murillo y Hugo Salazar Castillo— con este fantasma
    rondando la de Teresa. Deliberadamente simple y sin amenaza ni
    caricatura: es un recuerdo, no uno de los tres espíritus de jefe."""
    w, h = ancho, alto
    return [
        (0.50 * w, 0.05 * h), (0.30 * w, 0.20 * h), (0.24 * w, 0.45 * h),
        (0.30 * w, 0.70 * h), (0.20 * w, 1.00 * h), (0.80 * w, 1.00 * h),
        (0.70 * w, 0.70 * h), (0.76 * w, 0.45 * h), (0.70 * w, 0.20 * h),
    ]


def _figura_lejana(ancho: int, alto: int) -> list[tuple[float, float]]:
    """La anomalía ambigua de la Fase 1 (AUD-478, GAP-059): una figura
    entre las tumbas que nunca se confirma.

    Distinta a propósito de `_fantasma`: aquella es el easter egg
    personal —un recuerdo de familia, con un `MessageTrigger` que dice su
    nombre—; ésta no tiene nombre, no tiene disparador y no vuelve a
    aparecer necesariamente en el mismo sitio. El punto 7 de la crítica
    de diseño del dueño (2026-08-14) para la Fase 1: *«si el jugador no
    la vio, no pasa nada; si la vio, ¿qué fue eso?»* — la misma regla que
    ya usa la Bruja de la Fase 3 (AUD-475), aplicada aquí donde no hay
    ningún relámpago del que colgar el instante. El contorno es
    deliberadamente más simple que el del fantasma: cuanto menos detalle,
    menos se puede afirmar sobre qué era.
    """
    w, h = ancho, alto
    return [
        (0.46 * w, 0.00 * h), (0.34 * w, 0.16 * h), (0.30 * w, 0.50 * h),
        (0.36 * w, 0.72 * h), (0.26 * w, 1.00 * h), (0.74 * w, 1.00 * h),
        (0.64 * w, 0.72 * h), (0.70 * w, 0.50 * h), (0.66 * w, 0.16 * h),
    ]


def _horizonte_puntos(
    ancho_pantalla: int, alto_pantalla: int, desplazamiento_x: float,
    base_y: float, amplitud: float, frecuencia: float, fase: float,
) -> list[tuple[float, float]]:
    """Los vértices de una cresta lejana, continua y determinista.

    Determinista en `desplazamiento_x` (no en el tiempo ni en el número de
    fotograma) para que la misma columna de mundo produzca siempre la misma
    silueta — necesario para que el paralaje se lea como una montaña de
    verdad al desplazarse, no como ruido nuevo cada fotograma.

    AUD-514 — `paso=40` y un solo término de seno, no dos: la primera
    versión (paso 14, dos senos por punto) medía ~1,6 ms por fotograma
    ella sola y tumbó `TestCabeEnElPresupuestoDeFotograma` (presupuesto de
    15 ms, ya ajustado sin esto — `aplicar_gradacion` sola consume ~14,6
    ms medidos por perfil). Una cresta lejana y difuminada no necesita el
    detalle de una de primer plano; menos puntos y menos trigonometría por
    punto no se notan a la distancia a la que se pinta.
    """
    paso = 40
    puntos: list[tuple[float, float]] = [(0.0, float(alto_pantalla))]
    x = 0
    while x <= ancho_pantalla + paso:
        mundo_x = x + desplazamiento_x
        y = base_y - amplitud * math.sin(mundo_x * frecuencia + fase)
        puntos.append((float(x), y))
        x += paso
    puntos.append((float(ancho_pantalla), float(alto_pantalla)))
    return puntos


#: Lienzo reutilizado por `dibujar_horizonte`, del tamaño de la pantalla
#: interna. Reutilizado y no creado cada llamada — una `Surface` nueva de
#: pantalla completa con `SRCALPHA` por fotograma es justo lo que
#: `TestCabeEnElPresupuestoDeFotograma` (`tests/test_stage4_1.py`) mide y
#: descarta en el resto del módulo: se cachea una vez por tamaño, igual que
#: `ProyectorDeSombras._lienzo` (AUD-510).
_LIENZO_HORIZONTE: pygame.Surface | None = None


def _lienzo_horizonte(tamano: tuple[int, int]) -> pygame.Surface:
    global _LIENZO_HORIZONTE
    if _LIENZO_HORIZONTE is None or _LIENZO_HORIZONTE.get_size() != tamano:
        _LIENZO_HORIZONTE = pygame.Surface(tamano, pygame.SRCALPHA)
    return _LIENZO_HORIZONTE


def dibujar_horizonte(
    superficie: pygame.Surface,
    ancho_pantalla: int,
    alto_pantalla: int,
    desplazamiento_x: float,
    color: tuple[int, int, int],
    alfa: int,
    base_y: float,
    amplitud: float,
    frecuencia: float,
    fase: float = 0.0,
) -> None:
    """Una cresta lejana que cruza toda la pantalla — la capa `BG_Far`
    (GAP-058/059/065: *"BG_Far/BG_Mid/BG_Near siguen vacías en las seis
    fases"*).

    Procedural y no un contorno fijo repetido, por la misma razón que
    `dibujar_contorno` prefiere un polígono a un PNG: el proyecto no tiene
    arte de horizonte para seis paisajes distintos, y una cresta calculada
    a partir de `frecuencia`/`amplitud`/`base_y` da un perfil propio por
    fase (una tormenta y un cementerio en calma no comparten silueta) sin
    fingir ser una ilustración terminada.

    `desplazamiento_x` debe llevar el paralaje ya aplicado (típicamente
    `offset.x * 0.15` o menos: es el plano más lejano, el que menos se
    mueve al caminar) — esta función sólo dibuja, no decide cuánto se
    desplaza.
    """
    if alfa <= 0 or ancho_pantalla <= 0 or alto_pantalla <= 0:
        return
    puntos = _horizonte_puntos(
        ancho_pantalla, alto_pantalla, desplazamiento_x,
        base_y, amplitud, frecuencia, fase,
    )
    lienzo = _lienzo_horizonte((ancho_pantalla, alto_pantalla))
    lienzo.fill((0, 0, 0, 0))
    pygame.draw.polygon(lienzo, (*color, min(255, alfa)), puntos)
    superficie.blit(lienzo, (0, 0))


#: Silueta gigantesca en el fondo de la Fase 6: el punto de llegada que la
#: escala del nivel entero insinúa sin mostrar completo (GAP-064, puntos
#: 7-8 y 22-23: *"la escala crece hasta revelar parcialmente el lugar donde
#: está Paburu... nunca mostrarlo completo"*). Deliberadamente más simple
#: que los tres espíritus —una masa y unos cuernos apenas sugeridos, no un
#: retrato— porque el diseño pide sugerir, no exponer.
def _paburu(ancho: int, alto: int) -> list[tuple[float, float]]:
    w, h = ancho, alto
    return [
        (0.06 * w, 1.00 * h), (0.02 * w, 0.62 * h), (0.14 * w, 0.40 * h),
        (0.24 * w, 0.44 * h), (0.20 * w, 0.20 * h), (0.30 * w, 0.02 * h),
        (0.38 * w, 0.22 * h), (0.36 * w, 0.38 * h), (0.48 * w, 0.30 * h),
        (0.60 * w, 0.38 * h), (0.58 * w, 0.22 * h), (0.68 * w, 0.02 * h),
        (0.76 * w, 0.20 * h), (0.72 * w, 0.44 * h), (0.82 * w, 0.40 * h),
        (0.94 * w, 0.62 * h), (0.90 * w, 1.00 * h),
    ]


#: Una vértebra gigantesca, apilable en columna — la Fase 3 pide que las
#: osamentas dejen de ser una baldosa de decoración y se lean como
#: arquitectura (GAP-061, punto 15: *"una vértebra, luego una columna,
#: luego una estructura gigantesca"*).
def _vertebra_gigante(ancho: int, alto: int) -> list[tuple[float, float]]:
    w, h = ancho, alto
    return [
        (0.30 * w, 1.00 * h), (0.20 * w, 0.80 * h), (0.24 * w, 0.60 * h),
        (0.08 * w, 0.52 * h), (0.00 * w, 0.36 * h), (0.14 * w, 0.30 * h),
        (0.30 * w, 0.38 * h), (0.30 * w, 0.20 * h), (0.50 * w, 0.00 * h),
        (0.70 * w, 0.20 * h), (0.70 * w, 0.38 * h), (0.86 * w, 0.30 * h),
        (1.00 * w, 0.36 * h), (0.92 * w, 0.52 * h), (0.76 * w, 0.60 * h),
        (0.80 * w, 0.80 * h), (0.70 * w, 1.00 * h), (0.50 * w, 0.88 * h),
    ]


def dibujar_contorno(
    superficie: pygame.Surface,
    forma: object,
    x: int,
    y: int,
    ancho: int,
    alto: int,
    color: tuple[int, int, int],
    alfa: int,
    grosor: int = 2,
) -> None:
    """Pinta un contorno translúcido en `(x, y)`.

    Contorno y no relleno: una figura sólida en el fondo se lee como un objeto
    del escenario, y estas no son objetos — son recuerdos. El borde abierto es
    lo que las hace parecer siluetas en la niebla.
    """
    if alfa <= 0 or ancho <= 0 or alto <= 0:
        return
    puntos = [(x + px, y + py) for px, py in forma(ancho, alto)]  # type: ignore[operator]
    if len(puntos) < 3:
        return
    lienzo = pygame.Surface((ancho + grosor * 2, alto + grosor * 2),
                            pygame.SRCALPHA)
    relativos = [(px - x + grosor, py - y + grosor) for px, py in puntos]
    pygame.draw.polygon(lienzo, (*color, min(255, alfa)), relativos, grosor)
    superficie.blit(lienzo, (x - grosor, y - grosor))

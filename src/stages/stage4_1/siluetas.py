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

Por qué contornos y no sprites
-------------------------------
El proyecto no tiene arte de venado, serpiente ni gavilán en vista de fondo, y
generar un PNG inventado sería arte falso que luego hay que mantener. Un
contorno dibujado con polígonos es honesto: se lee como «una forma en la
niebla», que es exactamente lo que el diseño pide, y no finge ser una
ilustración terminada. Cuando haya arte, se sustituye la función y ya.
"""
from __future__ import annotations

import math

import pygame

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


#: Las tres formas de los vencidos, en el orden en que se derrotan.
ESPIRITUS: tuple[tuple[str, object], ...] = (
    ("venado", _venado),
    ("serpiente", _serpiente),
    ("gavilan", _gavilan),
)


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

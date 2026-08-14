"""El trazado del 4-1: un pasillo horizontal de seis secciones, no un pozo.

Por qué se reconstruyó (AUD-467)
==================================
La primera reconstrucción (AUD-462…466) heredó el pozo vertical del diseño
de La Cegua —repisas en zigzag, hasta 39 de 60 columnas de ancho cada una—
con una gradación de color encima. Jugado, el dueño lo rechazó: en pantalla,
una repisa que ocupa casi todo el ancho se lee como una plataforma
horizontal genérica, no como un pozo. *«El nuevo nivel es horizontal
completamente»* fue el veredicto, y tenía razón — no por casualidad: el
propio guion pide *«atravesar diferentes espacios»*, que es horizontal por
definición.

La forma nueva
---------------
900 × 38 baldosas (14.400 × 608 px). Seis secciones de 150 columnas cada
una (`ANCHO_SECCION`), suelo firme a la fila `FILA_SUELO` en todas partes —
**nunca hay un hueco por el que caer**: cero `DeathPit` por construcción, no
por cuidado. La única variación de altura del suelo es la loma de la
Fase 3, y sube el terreno, no lo perfora.

Terreno propio, no color encima del mismo suelo
-------------------------------------------------
Cada sección tiene su propia familia de baldosa en `tileset_stage4_1.png`
(cripta, bosque, camino de huesos, bosque quemado, tumbas, piedra sagrada —
ver `tools/generate_all_assets.py::_gen_tileset_stage4_1`). El musgo y el
lodo de la Fase 2 son la misma física del prototipo anterior (AUD-236) sobre
tierra de bosque de verdad.

La loma de la Fase 3
----------------------
El guion pide *«ascender por lomas utilizando slopes»*. Aquí es un desnivel
real: el suelo sube de la fila `FILA_SUELO` (30) a la fila `FILA_CIMA` (20)
entre las columnas 340 y 370, se mantiene arriba hasta la 410, y baja de
vuelta hasta la 440. `_altura_del_suelo(columna)` calcula la fila del suelo
para cualquier columna del mapa — el generador la usa para rellenar tierra
y la escena para colocar decoración a la altura correcta. Dos objetos
`Slope` (AUD-297) se superponen exactamente a las rampas para que se puedan
subir y bajar de verdad.
"""
from __future__ import annotations

#: Lado de la baldosa, en píxeles.
TS = 16

#: Ancho de cada sección, en baldosas. Misma proporción que otros
#: escenarios horizontales del proyecto (`stage2_1_oficinas`: 200×38).
ANCHO_SECCION = 150

#: Seis secciones.
MW = ANCHO_SECCION * 6
MH = 38

#: La fila del suelo llano. El jugador nunca cae por debajo de esto salvo
#: en la loma, que **sube**, no baja.
FILA_SUELO = 30

#: Grosor de los muros de los extremos, en columnas.
MURO_ANCHO = 2

# ── La loma de la Fase 3 ─────────────────────────────────────────────────
LOMA_INICIO_SUBIDA = 340
LOMA_FIN_SUBIDA = 370
LOMA_FIN_CIMA = 410
LOMA_FIN_BAJADA = 440
FILA_CIMA = 20


def _altura_del_suelo(columna: int) -> int:
    """La fila del suelo en esa columna. `FILA_SUELO` en todas partes salvo
    en la loma de la Fase 3, que sube y vuelve a bajar."""
    if LOMA_INICIO_SUBIDA <= columna < LOMA_FIN_SUBIDA:
        avance = (columna - LOMA_INICIO_SUBIDA) / (LOMA_FIN_SUBIDA - LOMA_INICIO_SUBIDA)
        return round(FILA_SUELO - avance * (FILA_SUELO - FILA_CIMA))
    if LOMA_FIN_SUBIDA <= columna < LOMA_FIN_CIMA:
        return FILA_CIMA
    if LOMA_FIN_CIMA <= columna < LOMA_FIN_BAJADA:
        avance = (columna - LOMA_FIN_CIMA) / (LOMA_FIN_BAJADA - LOMA_FIN_CIMA)
        return round(FILA_CIMA + avance * (FILA_SUELO - FILA_CIMA))
    return FILA_SUELO


def perfil_del_suelo() -> tuple[int, ...]:
    """La fila del suelo, columna a columna, para todo el mapa."""
    return tuple(_altura_del_suelo(c) for c in range(MW))


def loma() -> tuple[tuple[int, int, int, int, str], ...]:
    """Los dos `Slope` de la loma: `(columna, fila_arriba, ancho, alto, sube)`.

    El rectángulo de un `Slope` es el triángulo entero (AUD-297): de la fila
    de arriba a la de abajo, de la columna de inicio a la de fin.
    """
    alto = FILA_SUELO - FILA_CIMA
    return (
        (LOMA_INICIO_SUBIDA, FILA_CIMA, LOMA_FIN_SUBIDA - LOMA_INICIO_SUBIDA,
         alto, "derecha"),
        (LOMA_FIN_CIMA, FILA_CIMA, LOMA_FIN_BAJADA - LOMA_FIN_CIMA,
         alto, "izquierda"),
    )


def fase_de_la_columna(columna: int) -> int:
    """La fase, 1 a 6, a la que pertenece esa columna del mapa."""
    return min(6, columna // ANCHO_SECCION + 1)


#: Cada cuántas columnas hay un punto de reaparición. 28 columnas = 448 px,
#: por debajo de los 500 px que recomienda el calificador.
CADA_CUANTAS_COLUMNAS_CHECKPOINT = 28


def checkpoints() -> tuple[tuple[int, int], ...]:
    """Los puntos de reaparición, en `(columna, fila)` — a la altura real
    del suelo en esa columna, para que ninguno quede flotando en la loma."""
    columnas = range(10, MW - MURO_ANCHO - 10, CADA_CUANTAS_COLUMNAS_CHECKPOINT)
    return tuple((c, _altura_del_suelo(c)) for c in columnas)


# ── Fase 2 (El Venado): musgo y lodo ─────────────────────────────────────
#
# Segmentos de suelo, en `(columna_inicio, ancho, material)`. La misma
# física del prototipo anterior (AUD-236): el musgo arrastra, el lodo
# frena — aquí sobre tierra de bosque, no sobre piedra de cripta.
SEGMENTOS_FASE2: tuple[tuple[int, int, str], ...] = (
    (170, 15, "musgo"),
    (190, 15, "lodo"),
    (210, 15, "musgo"),
    (230, 15, "lodo"),
    (250, 15, "musgo"),
)
#: Cuánto arrastra el musgo, en px/s. Mismo valor medido del prototipo.
ARRASTRE_DEL_MUSGO = 62.0
#: Cuánto frena el lodo: se anda al 88 %.
FRENO_DEL_LODO = 0.88


# ── Fase 3 (El Rey Terciopelo): huesos en el camino ──────────────────────
#
# Calaveras y costillas incrustadas en el suelo — decoración de
# `Terrain_Detail`, no colisión. El guion: *«un cementerio o camino
# formado por calaveras y osamentas de serpientes»*.
HUESOS_FASE3: tuple[int, ...] = tuple(range(305, 449, 12))


# ── Fase 4 (El Gavilán): tocones del bosque cortado ──────────────────────
ARBOLES_FASE4: tuple[int, ...] = tuple(range(460, 599, 25))


# ── Fase 5 (La Planicie de los Muertos): tumbas de conquistadores ────────
TUMBAS_FASE5: tuple[int, ...] = tuple(range(610, 749, 30))


# ── Fase 6 (El Camino hacia Paburu): grietas que se iluminan al paso ─────
GRIETAS_FASE6: tuple[int, ...] = tuple(range(760, 899, 20))


def grietas_de_pisada() -> tuple[tuple[int, int], ...]:
    return tuple((c, _altura_del_suelo(c)) for c in GRIETAS_FASE6)


# ── El easter egg de la Fase 1 ────────────────────────────────────────────
#
# Dos lápidas, una junto a la otra. Los nombres los dio el dueño del
# proyecto (2026-08-14): no se inventa ninguna fecha ni ningún dato más.
COLUMNA_LAPIDA_TERESA = 30
COLUMNA_LAPIDA_HUGO = 34
NOMBRE_LAPIDA_TERESA = "Teresa Murillo"
NOMBRE_LAPIDA_HUGO = "Hugo Salazar Castillo"

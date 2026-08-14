"""El trazado del 4-1: un descenso, no un pasillo.

Se hereda tal cual del diseño anterior (AUD-225) — ver `docs/niveles/
13_STAGE_4_1.md` §0 para por qué: un cementerio no se recorre de lado, se
baja, y esta forma es la que ya se demostró que funciona jugada (repisas en
zigzag, cero `DeathPit`, cero `HazardZone` fija, cero daño por caída). Lo que
cambia con el rediseño de las seis fases es **qué hay** en cada tramo, no la
forma del pozo.

La geometría, y por qué es tan regular
---------------------------------------
Las repisas van cada 5 filas y alternan lado, así que el descenso es un
zigzag. Cinco filas son 80 px y el salto del jugador llega a 90,25 px medidos
de la física (`level_metrics.JumpEnvelope`), o sea que **se puede volver a
subir**. Consecutivas se solapan siempre entre las columnas 20 y 40, así que
desde cualquier repisa se llega andando al hueco de la siguiente — ningún
descenso puede encerrar a nadie.

Lo nuevo de esta versión
-------------------------
* **Musgo y lodo en la Fase 2 (El Venado)**, no en dos actos separados: el
  guion nuevo los pide juntos —*«superficies con musgo que resbalan y otras
  zonas que frenan el movimiento»*— en el mismo tramo.
* **Un tramo de slope en la Fase 3 (El Rey Terciopelo)**: la petición del
  guion de «ascender por lomas» se resuelve con un `Slope` de verdad
  (`pendientes.py`) metido en el hueco de una repisa, no con una inversión
  del eje del nivel. Ocupa sólo parte del hueco — el resto queda libre para
  seguir cayendo, igual que cualquier otra pieza que se mete en un hueco en
  este nivel.
* **Grietas que se iluminan al paso en la Fase 6**, no braseros que se
  quedan encendidos: el guion las describe como *«cada paso... puede
  activar una luz ambiental»*, un rastro momentáneo, no una barra de
  progreso acumulada. Las enciende la escena (`stage4_1.py`), no el TMX.
"""
from __future__ import annotations

#: Lado de la baldosa, en píxeles. El mismo que `settings.TILE_SIZE`; se repite
#: aquí porque el generador corre como script suelto, sin el paquete instalado.
TS = 16

#: Ancho y alto del mapa, en baldosas. 960 × 4608 px — un pozo, seis tramos.
MW, MH = 60, 288

#: Filas de cada fase. Seis fases de 48 filas: 768 px, más de una pantalla de
#: alto (la pantalla mide 600), así que cada fase se lee como una fase.
ALTO_FASE = 48

#: Grosor de los muros laterales, en columnas.
MURO_ANCHO = 2

#: Cada cuántas filas hay una repisa. Cinco: 80 px, y el salto del jugador
#: llega a 90,25 medidos — así se puede volver a subir una repisa suelta.
FILAS_POR_REPISA = 5

#: Grosor de una repisa, en filas. Una sola: con dos, el hueco libre entre
#: una repisa y la de arriba se quedaba en 48 px y el jugador mide 32.
GROSOR_REPISA = 1

#: Primera y última repisa. La última deja sitio para el suelo final.
PRIMERA_FILA = 10
ULTIMA_FILA = 275

#: El suelo del umbral: firme, de pared a pared. El único sitio del nivel
#: donde se puede estar quieto sin que pase nada, y por eso es el final.
SUELO_FINAL = 280


def repisas() -> tuple[tuple[int, int, int], ...]:
    """Las repisas del pozo, en `(columna, ancho, fila)`.

    Alternan lado: las pares dejan el hueco a la derecha y las impares a la
    izquierda. El solape entre dos consecutivas nunca baja de 20 columnas, lo
    que impide que exista una repisa desde la que no se alcance el hueco
    siguiente — `tests/test_stage4_1.py` lo comprueba en vez de confiar en
    que estos números estén bien.
    """
    salida: list[tuple[int, int, int]] = []
    for i, fila in enumerate(range(PRIMERA_FILA, ULTIMA_FILA + 1,
                                   FILAS_POR_REPISA)):
        if i % 2 == 0:
            x0, ancho = MURO_ANCHO, 39          # hueco a la derecha
        else:
            x0, ancho = 20, MW - MURO_ANCHO - 20  # hueco a la izquierda
        salida.append((x0, ancho, fila))
    return tuple(salida)


def fase_de_la_fila(fila: int) -> int:
    """La fase, 1 a 6, a la que pertenece esa fila del mapa."""
    return min(6, fila // ALTO_FASE + 1)


#: Cada cuántas repisas hay un punto de reaparición.
CADA_CUANTAS_CHECKPOINT = 4

#: Todos los checkpoints van en esta columna, y no en el centro de su repisa.
#:
#: Es la franja que **todas** las repisas tienen en común (20 a 40), así que
#: cabe en cualquiera de las dos orientaciones. `level_metrics.
#: analyse_checkpoints` ordena los puntos de reaparición por `(x, y)`; con la
#: `x` fija, la distancia «entre checkpoints consecutivos» mide lo que de
#: verdad hay que bajar y no un zigzag falso por la alternancia de lado.
COLUMNA_DEL_CHECKPOINT = 30


def checkpoints() -> tuple[tuple[int, int], ...]:
    """Los puntos de reaparición, en `(columna, fila)`.

    Uno cada cuatro repisas y uno en el suelo final. Con 54 repisas eso deja
    tramos de 320 px entre dos consecutivos, por debajo de los 500 que
    recomienda el calificador.
    """
    lista = repisas()
    puestos = [
        (COLUMNA_DEL_CHECKPOINT, fila)
        for i, (_x0, _ancho, fila) in enumerate(lista)
        if i % CADA_CUANTAS_CHECKPOINT == 1
    ]
    puestos.append((COLUMNA_DEL_CHECKPOINT, SUELO_FINAL))
    return tuple(puestos)


# ── Fase 2 (El Venado): musgo y lodo, en el mismo tramo ─────────────────────
#
# El guion los pide juntos: *«El terreno introduce superficies con musgo que
# resbalan y otras zonas que frenan el movimiento»*. Se eligen por índice y
# no por fila para que ajustar la partición de fases no las descoloque. No
# todas las repisas de la Fase 2 llevan superficie especial — dejar algunas
# de piedra normal da un sitio donde pararse a mirar, y un tramo donde cada
# paso resbala deja de leerse como una elección y pasa a ser sólo incómodo.
INDICES_MUSGO: tuple[int, ...] = (9, 11, 13, 15, 17)
INDICES_LODO: tuple[int, ...] = (8, 12, 16)

#: Cuánto arrastra el musgo, en px/s, hacia el hueco de su repisa.
#: `ZonaDeFriccion.arrastre` se aplica a la posición, no a la velocidad, así
#: que al saltar se suelta — es la cinta de Mega Man 2, no un empujón que se
#: acumula. Mismo valor medido que el diseño anterior (AUD-236).
ARRASTRE_DEL_MUSGO = 62.0

#: Cuánto frena el lodo: se anda al 88 % de la velocidad normal.
#: No depende de los fotogramas por segundo (AUD-236: medidos 79,20 px/s a
#: 30, a 60 y a 120).
FRENO_DEL_LODO = 0.88


def superficies() -> tuple[tuple[int, int, int, str], ...]:
    """Qué material tiene cada repisa: `(columna, ancho, fila, material)`."""
    salida = []
    for i, (x0, ancho, fila) in enumerate(repisas()):
        if i in INDICES_MUSGO:
            material = "musgo"
        elif i in INDICES_LODO:
            material = "lodo"
        else:
            material = "piedra"
        salida.append((x0, ancho, fila, material))
    return tuple(salida)


def hueco_de(indice: int) -> tuple[int, int]:
    """Dónde empieza y cuánto mide el hueco de esa repisa, en baldosas."""
    x0, ancho, _fila = repisas()[indice]
    if x0 == MURO_ANCHO:                      # la repisa pega al muro izquierdo
        return x0 + ancho, MW - MURO_ANCHO - (x0 + ancho)
    return MURO_ANCHO, x0 - MURO_ANCHO


# ── Fase 3 (El Rey Terciopelo): la loma ─────────────────────────────────────
#
# El guion pide «ascender por lomas utilizando slopes». Se resuelve con un
# `Slope` (AUD-297, `pendientes.py`) metido en el hueco de una repisa de la
# Fase 3, subiendo del suelo de esa repisa hasta el de la que tiene
# directamente encima — el mismo tramo de 5 filas (80 px) que separa a
# cualquier par de repisas consecutivas, así que no hace falta ensanchar el
# pozo ni tocar la cadencia del zigzag. Ocupa sólo una parte del hueco: el
# resto sigue libre para caer, igual que cualquier otra pieza que se mete en
# un hueco en este nivel (la regla del §6 del diseño: nunca tapar el hueco
# entero).
LOMA_INDICE = 22
#: Ancho de la loma, en baldosas — deja el resto del hueco libre.
ANCHO_DE_LA_LOMA = 10


def loma() -> tuple[int, int, int, int, str]:
    """La loma: `(columna, fila_de_abajo, ancho, alto, sube)`.

    `fila_de_abajo` es la fila de la repisa de `LOMA_INDICE`; la loma sube
    `FILAS_POR_REPISA` filas desde ahí, hasta el nivel de la repisa de
    encima.
    """
    inicio, ancho_hueco = hueco_de(LOMA_INDICE)
    _x0, _ancho, fila = repisas()[LOMA_INDICE]
    ancho = min(ANCHO_DE_LA_LOMA, ancho_hueco)
    columna = inicio + (ancho_hueco - ancho) // 2
    return columna, fila, ancho, FILAS_POR_REPISA, "derecha"


# ── Fase 6 (El Camino hacia Paburu): grietas que se iluminan al paso ───────
#
# El guion: *«Cada paso... puede activar una luz ambiental... se revelan
# tiles con grietas verdes»*. A diferencia de los braseros del diseño
# anterior, **no quedan encendidas**: son un rastro momentáneo, no una barra
# de progreso acumulada. La escena (`stage4_1.py`) las enciende por
# proximidad y las deja apagarse solas — aquí sólo se calcula dónde van.
def grietas_de_pisada() -> tuple[tuple[int, int], ...]:
    """Las grietas de la Fase 6, en `(columna, fila)` — el canto de cada
    repisa del tramo, que es por donde se pisa al bajar."""
    salida = []
    for x0, ancho, fila in repisas():
        if fase_de_la_fila(fila) != 6:
            continue
        borde = x0 if x0 > MURO_ANCHO else x0 + ancho - 1
        salida.append((borde, fila))
    return tuple(salida)

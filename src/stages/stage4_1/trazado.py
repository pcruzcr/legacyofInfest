"""El trazado del 4-1: un descenso, no un pasillo.

Por qué se rehizo (AUD-225)
============================
El nivel era horizontal y estaba lleno de `DeathPit`. Jugado, no funcionaba, y
por tres razones distintas:

1. **Los fosos contradecían la ficha.** `13_STAGE_4_1.md` lo llama «travesía
   atmosférica» y prohíbe enemigos porque *«la tensión ya está: es el silencio
   antes del juez»*. Siete agujeros mortales en el camino convierten eso en un
   nivel de memorizar caídas, que es justo lo contrario.
2. **Las `HazardZone` no se ven.** El motor sólo dibuja las que suben —la
   inundación de AUD-135—; una zona de daño fija espera a que el diseñador
   pinte pinchos en las baldosas, y aquí no había ninguno pintado. El jugador
   recibía daño de la nada. Se quitaron todas: lo que queda son grietas que la
   escena dibuja con luz verde, y que **no hacen daño**.
3. **Un cementerio no se recorre de lado.** Se baja. El nivel es ahora un pozo
   de 240 filas: se desciende de repisa en repisa hasta el círculo de piedra.

Por qué caer no mata
--------------------
El motor **no tiene daño por caída** (comprobado: no existe ninguna constante ni
ninguna rama que lo aplique). Eso hace que un descenso sea seguro por
construcción, y es lo que permite quitar los fosos sin sustituirlos por nada:
la caída deja de ser el castigo y pasa a ser el movimiento.

Lo que sí exige cuidado son las superficies, y ésas se ven:

* **Musgo** (verde, con matas): arrastra hacia el hueco. No hace daño — te
  mueve. Se resbala hacia el borde, que es de donde hay que salir de todas
  formas, así que acelera al que entiende y sólo molesta al que se para.
* **Lodo** (marrón, con raíces): frena. Se camina despacio y la tormenta
  empuja mientras tanto.

Las dos son `FrictionZone` del motor, y las dos **se pintan con su baldosa**:
la regla es que ninguna superficie cambie el movimiento sin que se vea por qué.

La geometría, y por qué es tan regular
---------------------------------------
Las repisas van cada 5 filas y alternan lado, así que el descenso es un zigzag.
Cinco filas son 80 px y el salto del jugador llega a 90,25 px medidos de la
física (`level_metrics.JumpEnvelope`), o sea que **se puede volver a subir**.
La primera versión usaba seis filas —96 px— para que el pozo fuera de un solo
sentido; suena bien y jugado es un defecto, porque lo que hay en este nivel son
epitafios que leer, y pasarse uno de largo lo dejaba perdido. Bajar sigue siendo
gratis y subir sigue costando un salto puesto donde toca: el nivel se lee como
un descenso sin encerrar a nadie.

Consecutivas se solapan siempre entre las columnas 20 y 40, o sea que desde
cualquier repisa se llega andando al hueco de la siguiente. Un descenso no puede
tener un sitio donde el jugador se quede encerrado, y ésta es la forma de
garantizarlo sin comprobarlo a ojo.
"""
from __future__ import annotations

#: Lado de la baldosa, en píxeles. El mismo que `settings.TILE_SIZE`; se repite
#: aquí porque el generador corre como script suelto, sin el paquete instalado.
TS = 16

#: Ancho y alto del mapa, en baldosas. 960 × 3840 px — un pozo.
MW, MH = 60, 240

#: Filas de cada acto. Cinco actos de 48 filas: 768 px, más de una pantalla de
#: alto (la pantalla mide 600), así que cada acto se lee como un acto.
ALTO_ACTO = 48

#: Grosor de los muros laterales, en columnas.
MURO_ANCHO = 2

#: Cada cuántas filas hay una repisa. **Cinco, y no seis, a propósito.**
#:
#: Seis filas son 96 px y el salto del jugador llega a 90,25 medidos de la
#: física (`level_metrics.JumpEnvelope`): con seis, el descenso era de un solo
#: sentido. Sonaba bien —«el cementerio no devuelve a nadie»— y jugado es un
#: defecto: el contenido de este nivel son epitafios que leer y un cielo que
#: mirar, y pasarse uno de largo lo dejaba perdido para siempre. El calificador
#: lo dijo con todas las letras: 37 repechos imposibles.
#:
#: Con cinco son 80 px, se sube desde el lado abierto de cada repisa y el nivel
#: sigue leyéndose como un descenso — porque bajar es gratis y subir cuesta un
#: salto bien puesto.
FILAS_POR_REPISA = 5

#: Grosor de una repisa, en filas. Una sola: con dos, el hueco libre entre una
#: repisa y la de arriba se quedaba en 48 px y el jugador mide 32.
GROSOR_REPISA = 1

#: Primera y última repisa. La última deja sitio para el suelo del umbral.
PRIMERA_FILA = 10
ULTIMA_FILA = 225

#: El suelo del acto V: firme, de pared a pared. Es el único sitio del nivel
#: donde se puede estar quieto sin que pase nada, y por eso es el final.
SUELO_FINAL = 230


def repisas() -> tuple[tuple[int, int, int], ...]:
    """Las repisas del pozo, en `(columna, ancho, fila)`.

    Alternan lado: las pares dejan el hueco a la derecha y las impares a la
    izquierda. El solape entre dos consecutivas nunca baja de 20 columnas, que
    es lo que impide que exista una repisa desde la que no se alcance el hueco
    siguiente — `tests/test_stage4_1.py` lo comprueba en vez de confiar en que
    estos números estén bien.
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


def acto_de_la_fila(fila: int) -> int:
    """El acto, 1 a 5, al que pertenece esa fila del mapa."""
    return min(5, fila // ALTO_ACTO + 1)


#: Cada cuántas repisas hay un brasero. Doce braseros sobre 44 repisas.
CADA_CUANTAS_BRASERO = 4

#: Todos los braseros van en esta columna, y no en el centro de su repisa.
#:
#: Es la franja que **todas** las repisas tienen en común (20 a 40), así que
#: cabe en cualquiera de las dos orientaciones. Dos motivos, uno de dibujo y
#: otro de herramienta: una columna de fuegos bajando por el eje del pozo se lee
#: como un camino, y `level_metrics.analyse_checkpoints` ordena los puntos de
#: reaparición por `(x, y)` — con las `x` alternando entre 21 y 39, la distancia
#: «entre checkpoints consecutivos» salía de 3.459 px porque el orden era el
#: equivocado, no porque faltara ninguno.
COLUMNA_DEL_FUEGO = 30


def braseros() -> tuple[tuple[int, int], ...]:
    """Los braseros, en `(columna, fila)`. Once en las repisas y uno abajo."""
    puestos = [
        (COLUMNA_DEL_FUEGO, fila)
        for i, (_x0, _ancho, fila) in enumerate(repisas())
        if i % CADA_CUANTAS_BRASERO == 1
    ][:11]
    puestos.append((COLUMNA_DEL_FUEGO, SUELO_FINAL))   # el doceavo: el umbral
    return tuple(puestos)


#: Reaparecer en el brasero, y no en un punto invisible a mitad del pozo.
#:
#: El §10 del diseño dice que «los braseros ya cumplen de marcadores». Esto lo
#: hace literal: se vuelve al último fuego encendido, que es el que ilumina el
#: tramo donde acabas de caer. Doce sobre 44 repisas dejan 320 px entre uno y el
#: siguiente, por debajo de los 500 que el calificador recomienda.
def checkpoints() -> tuple[tuple[int, int], ...]:
    return braseros()


#: Las repisas de musgo: **arrastran hacia el hueco**. Se eligen por índice y no
#: por fila para que cambiar el reparto de actos no las descoloque.
#: Empiezan en el acto III, que es donde el diseño (§1) mete la primera
#: exigencia de movimiento, y siguen en el IV mezcladas con el lodo.
#: El acto III son las repisas 18 a 26 y el IV las 27 a 36; el V no lleva
#: ninguna, porque ahí *«el silencio es el jefe»* y una superficie que empuja no
#: es silencio.
INDICES_MUSGO: tuple[int, ...] = (19, 21, 23, 25, 29, 32, 35)

#: Las repisas de lodo: **frenan**. Sólo en el acto IV, donde además sopla el
#: viento: caminar despacio mientras te empujan es la única exigencia real del
#: nivel, y no hace daño.
INDICES_LODO: tuple[int, ...] = (28, 31, 34)

#: Cuánto arrastra el musgo, en px/s, hacia el hueco de su repisa.
#: `ZonaDeFriccion.arrastre` se aplica a la posición, no a la velocidad, así que
#: al saltar se suelta — es la cinta de Mega Man 2, no un empujón que se acumula.
ARRASTRE_DEL_MUSGO = 62.0

#: Cuánto frena el lodo: se anda al 88 % de la velocidad normal.
#:
#: `multiplicador` es una escala de velocidad y no un coeficiente de rozamiento
#: —el jugador reescribe `velocity.x` desde la entrada cada fotograma y esto se
#: aplica encima—, así que el número **no depende de los fotogramas por
#: segundo**: medidos 79,20 px/s a 30, a 60 y a 120 (AUD-236). Lo comprueba
#: `tests/test_stage4_1.py::TestElLodoFrenaIgualEnCualquierMaquina`.
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


def grietas() -> tuple[tuple[int, int, int], ...]:
    """Las grietas verdes de la pared, en `(columna, fila, alto_en_filas)`.

    **No hacen daño y no son `HazardZone`.** Son luz: marcan el canto de cada
    repisa para que el borde del que hay que saltar se vea en la oscuridad. Las
    dibuja la escena (`_dibujar_grietas`), porque una `HazardZone` fija el motor
    no la pinta y era exactamente el problema que tenía este nivel — daño
    invisible desde un rectángulo que nadie ve.
    """
    salida = []
    for x0, ancho, fila in repisas():
        # En el canto del lado por el que se cae, que es el que importa.
        borde = x0 if x0 > MURO_ANCHO else x0 + ancho - 1
        salida.append((borde, fila, 3))
    return tuple(salida)


#: Los nombres de los estudiantes van aquí. Se dejan como marcador de posición
#: a propósito: el diseño (§7) exige que los cargue el profesor, que todos estén
#: sin distinción de nota, y que ninguna inscripción se burle de nadie. Escribir
#: aquí una lista inventada sería justo lo contrario.
#:
#: El índice es el de la repisa donde se apoya la lápida.
EPITAFIOS: tuple[tuple[int, str], ...] = (
    (9, "[NOMBRE] — Computo Grafico, 2026"),
    (12, "[NOMBRE] — Procesamiento de Imagenes, 2026"),
    (15, "[NOMBRE] — Vision por Computadora, 2026"),
    (41, "[NOMBRE] — Reconocimiento de Patrones, 2026"),
)


def marcas_de_pezuna() -> tuple[tuple[int, int, int], ...]:
    """Dónde pisar, en `(columna, fila, ancho)` de baldosa.

    Las huellas que revela la visión espectral (§8 del diseño). En un descenso
    lo que hay que saber no es dónde saltar sino **por dónde caer**, así que
    marcan el hueco de cada repisa de musgo y de lodo: las superficies que
    mueven al jugador son las que merecen que mirar tenga premio.
    """
    salida = []
    for i, (x0, ancho, fila) in enumerate(repisas()):
        if i not in INDICES_MUSGO and i not in INDICES_LODO:
            continue
        # El hueco: lo que queda de pared a pared quitando la repisa.
        if x0 == MURO_ANCHO:
            hueco_x = x0 + ancho
        else:
            hueco_x = MURO_ANCHO
        salida.append((hueco_x, fila, 3))
    return tuple(salida)

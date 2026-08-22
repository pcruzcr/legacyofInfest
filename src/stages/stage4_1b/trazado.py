"""El trazado del 4-1b: la misma travesía horizontal del 4-1
(AUD-467/518), pero re-diseñada como mina inundada (AUD-575).

Por qué el mismo largo y la misma forma
=========================================
4.1b es una de las tres variantes que puede tocarle al jugador en el slot
de la Fase 4 (AUD-518, `src/stages/stage4_1/selector.py`) — no un nivel
aparte con su propia identidad estructural. Que sea horizontal, de
900×38 baldosas en seis secciones de 150, es la misma decisión de diseño
que AUD-467 cerró para el cementerio: una travesía es horizontal por
definición, esté seca o sumergida.

Por qué el agua ya no llega al techo (AUD-575)
===============================================
La primera versión de este nivel era "sumergido de principio a fin"
(AUD-519): la `WaterZone` cubría toda la columna de aire, sin superficie
a la que emerger, y el jugador nadaba en un abismo sin techo. El dueño la
rediseñó con la lectura de SMB 2-2: *«el agua no llega hasta el techo de
la cueva, sino hasta cierta altura, con la intención de generar la
sensación de estar encerrados bajo una gran cantidad de agua»*.

Aquí la superficie está en la fila 11 (176 px desde el techo): el aire
ocupa las once filas superiores y el agua las veintiuna de abajo. El
techo de la cueva (decorado con estalactitas y vigas oxidadas) se ve
siempre, cerca, inalcanzable; el jugador bucea bajo él y emerge cuando
puede — la alternancia agua/aire que da el estrés del 2-2.

El lecho (`FILA_SUELO`) sigue siendo la referencia de suelo, y la
`ZonaDeAgua` grande va de la superficie al lecho. Por encima de la
superficie hay terreno seco: los andenes de la mina (AUD-575), donde el
jugador sale del agua, camina y respira. Los `BLOQUES_DE_TERRENO` listan
todo el terreno que no es lecho: andenes, estribos, pilares y vigas
sumergidas — el generador pinta sus tiles y su colisión con la misma
fuente de verdad, y las pruebas pueden razonar la geometría sin leer el
TMX.

Seis secciones, seis identidades (AUD-575 — cierra el pendiente
"variedad narrativa por sección" de la ficha):

1. **La entrada** (cols 0-150) — respiro: andén seco de salida de la
   mina, agua clara, estalactitas sueltas, luz de trabajo blanca.
2. **La galería de estalactitas** (150-300) — estalactitas densas,
   luces rojas de alarma, maleza que agarra (corriente en contra),
   pilares que obligan a rodearlos.
3. **El patio de carga** (300-450) — andén seco grande en el centro:
   se sale del agua, se camina, cangrejos patrullan; luz de trabajo
   blanca.
4. **La esclusa rota** (450-600) — pilares a media agua, medusas que
   derivan, corriente en contra, luces rojas.
5. **El pozo del drenaje** (600-750) — vigas sumergidas cerca de la
   superficie que cortan el aire: hay que bucear por debajo y abrir
   hueco con el ataque acuático; lo más cerrado y oscuro del nivel.
6. **El desagüe** (750-900) — corriente a favor, faroles blancos de
   salida, el pez ya no sorprende: la salida se ve desde lejos.

AUD-576 — la arquitectura de beats del diseño 10/10: la travesía no es
una línea de distancia, es una secuencia de experiencias conectadas por
una línea horizontal. El orden psicológico es seguridad → curiosidad →
dominio → vulnerabilidad → incertidumbre → miedo → asombro:

| Tramo (cols) | Beat del blueprint | Función |
|---|---|---|
| 0-90 | Entrada | la mina se reconoce: faroles, vagoneta, andén seco |
| 90-150 | Primera inmersión | aprender a nadar; primer bloque de mineral visible |
| 150-250 | Mina inundada | la arquitectura empieza a deshacerse; vagoneta sumergida |
| 250-450 | Corrientes | el puzzle de navegación (dejarse llevar / resistir) |
| 450-553 | Profundidad | la fauna escasea; los faroles se apagan |
| 553-650 | Primer evento | la sombra del pez cruza el fondo (sin persecución) |
| 650-778 | El abismo | ya no es una mina; persecuciones de verdad |
| 778-890 | Clímax y salida | el pez cruza el espacio; la luz regresa; la salida |

Todo lo que el blueprint pide y el motor actual no puede hacer
(corrientes verticales, música por zona, zoom de cámara) está anotado
como decisión en `KNOWN_GAPS.md` (GAP-072) — no se construye a medias.
"""
from __future__ import annotations

#: Lado de la baldosa, en píxeles.
TS = 16

#: Mismas proporciones que `stage4_1/trazado.py` — seis secciones de 150
#: columnas (AUD-518: es la misma travesía, sumergida).
ANCHO_SECCION = 150
MW = ANCHO_SECCION * 6
MH = 38

#: El lecho de la mina inundada. Referencia para el spawn, los
#: checkpoints y la fauna que patrulla el fondo — el jugador nada por
#: encima, no camina sobre él (a menos que un andén lo saque del agua).
FILA_SUELO = 32

#: Grosor de los muros de los extremos, en columnas.
MURO_ANCHO = 2

#: La superficie del agua — AUD-575. Desde esta fila hacia abajo es agua
#: (`ZonaDeAgua`); desde aquí hacia el techo es aire. Las once filas de
#: aire son el colchón de la cueva: el techo con estalactitas se ve
#: cerca, y emerger es de verdad salir del agua (se respira, AUD-575).
FILA_SUPERFICIE_AGUA = 11
FILA_FONDO_AGUA = FILA_SUELO - 1


# ── Terreno que no es lecho (AUD-575) ────────────────────────────────
#
# Tuplas (col_ini, col_fin, fila_techo, fila_fondo): el rectángulo de
# terreno sólido correspondiente a esas columnas, desde el techo hasta el
# fondo indicado. El lecho (filas 32-37) no aparece aquí: es el suelo
# continuo de siempre.
#
# Regla de accesibilidad de un andén seco: su techo debe estar por
# encima de la superficie (fila < 11) y tener un **estribo** al borde —
# una pieza cuyo techo está a nivel del agua (fila 11) o sumergida
# (fila > 11). El jugador nada hacia arriba, sale del agua al nivel del
# estribo (`ControlDeNado._salir`), cae de pie en él y salta los tres
# escalones que faltan al andén (48 px, un salto normal). Sin estribo,
# el borde vertical de un andén seco es una pared de 48+ px de agua que
# no se puede subir nadando.
BLOQUES_DE_TERRENO: tuple[tuple[int, int, int, int], ...] = (
    # S1 — La entrada: andén de salida de la mina con su estribo.
    (0, 16, 8, 32),
    (16, 20, 11, 32),          # estribo: techo a nivel de superficie
    # S1 — AUD-576: el islote del primer checkpoint (CP1 en la col 78):
    # terreno seco justo antes de la primera zona realmente acuática —
    # "checkpoint después de nuevo dominio, no cada X píxeles".
    (68, 72, 11, 32),          # estribo de subida del islote
    (72, 86, 8, 32),           # el islote
    (86, 90, 11, 32),          # estribo de bajada
    # S2 — R1, el refugio de aire 1 (AUD-576): una cavidad seca al final
    # de la galería, antes del patio. Es donde se aprende que "puedo
    # regresar a respirar" — y donde vive el CP2.
    (149, 153, 11, 32),        # estribo de subida del refugio
    (153, 166, 8, 32),         # la cavidad
    # S2 — pilares de la galería (obligan a rodearlos).
    (225, 228, 18, 32),
    (268, 271, 18, 32),
    # S3 — El patio de carga: andén seco central con sus dos estribos.
    (310, 314, 11, 32),        # estribo de subida
    (314, 394, 8, 32),         # el andén
    (394, 398, 11, 32),        # estribo de bajada
    # S3 — R2, el refugio de aire 2 (AUD-576): cavidad seca escondida
    # justo antes del estribo del patio, "no evidente desde el inicio" —
    # descubrirla es la pequeña recompensa de navegación del beat 4.
    (302, 306, 11, 32),        # estribo de subida del refugio
    (306, 310, 8, 32),         # la cavidad
    # S4 — La esclusa rota: pilares a media agua.
    (478, 480, 14, 32),
    (528, 530, 14, 32),
    (565, 568, 18, 32),
    # S5 — El pozo del drenaje: vigas sumergidas que cortan el aire.
    (605, 640, 13, 15),
    (660, 695, 13, 15),
)


def fase_de_la_columna(columna: int) -> int:
    """La sección, 1 a 6, a la que pertenece esa columna del mapa —mismo
    cálculo que `stage4_1.trazado.fase_de_la_columna`, para que las
    pruebas y el diseño de checkpoints puedan razonar igual en las dos
    variantes."""
    return min(6, columna // ANCHO_SECCION + 1)


#: Siete checkpoints, **por evento y no por distancia** (AUD-576,
#: blueprint 10/10 §15-16): después de cada dominio mecánico nuevo, cada
#: evento narrativo y cada set piece — nunca "cada X píxeles". Las
#: columnas son las del blueprint (×16 para píxeles): CP1 1250, CP2 2600,
#: CP3 5200, CP4 7800, CP5 9300, CP6 12450, y el CP7 técnico en 13300 que
#: el propio blueprint deja "opcional si el encuentro final produce
#: muertes frecuentes" — aquí se incluye porque el pez del clímax es el
#: único momento con riesgo real de bucle largo.
#:
#: `(columna, fila)` — la fila es el techo del terreno sobre el que se
#: apoya el checkpoint: los del aire (islote, refugios, patio) en la fila
#: de su andén, los del fondo en la fila 32 (el lecho).
COLUMNAS_CHECKPOINT: tuple[tuple[int, int], ...] = (
    (78, 8),     # S1 — el islote, tras la primera inmersión (x=1248)
    (162, 8),    # S2 — el refugio R1, tras aprender a respirar (x=2592)
    (325, 8),    # S3 — el patio, tras el puzzle de corrientes (x=5200)
    (487, 32),   # S4 — la esclusa, antes del primer evento (x=7792)
    (581, 32),   # S4/S5 — tras la sombra del pez (x=9296)
    (778, 32),   # S6 — antes del clímax (x=12448)
    (831, 32),   # S6 — antes del tramo final (x=13296)
)


def checkpoints() -> tuple[tuple[int, int], ...]:
    """Los puntos de reaparición, en `(columna, fila)`."""
    return COLUMNAS_CHECKPOINT


#: Corrientes de agua y maleza — `ZonaDeAgua` adicionales, más angostas,
#: superpuestas a la grande. `sistema_corriente_de_agua` (motor) suma la
#: `corriente` de **cada** zona que toca al jugador, y una corriente en
#: cero no hace nada — así que la zona grande (corriente cero, sólo marca
#: "esto es agua") y estas franjas conviven sin pisarse.
#
#: La **maleza** es corriente en contra local: algas densas que agarran
#: al que nada por ellas. Es la "flora como obstáculo" del nivel
#: (AUD-575): nada daña (regla del nivel: todo es presencia), pero la
#: maleza frena — y frenar bajo la persecución del pez es exactamente el
#: estrés del SMB 2-2.
#
#: Sólo empuje horizontal, nunca vertical: una corriente vertical
#: empujaría al jugador fuera del estado de nado en pleno tramo sumergido
#: (la salida por superficie la decide `ControlDeNado._salir` con la
#: geometría real, ver `docs/45_SWIMMING_SPEC.md` §3).
#
#: (columna_inicio, columna_fin, corriente_x). El signo sigue la lectura
#: del mapa: positivo empuja hacia la derecha (con el sentido normal de
#: avance), negativo hacia la izquierda (en contra).
#:
#: AUD-576 — corrientes como puzzle de navegación (blueprint §12), no
#: obstáculos sueltos: la primera corriente es **a favor** (aprender a
#: dejarse llevar), la segunda empuja hacia el estribo del patio, la
#: tercera **en contra** justo después (decidir si resistir o subir al
#: refugio R2), y la esclusa en contra es la resistencia a mitad del
#: tramo cuando el pez ya se ha anunciado. El blueprint pide además una
#: corriente vertical (C4 ↓↓) que lleve a una cámara profunda: el motor
#: no la soporta (una `corriente_y` sumaría empuje vertical al eje que
#: los estados acuáticos gobiernan y rompería el nado — ver GAP-072), así
#: que la profundidad se consigue con geometría, no con física.
ZONAS_DE_CORRIENTE: tuple[tuple[int, int, float], ...] = (
    # S1 — C1, la primera corriente: a favor, para aprender a dejarse
    # llevar sin luchar (blueprint: x=2150-2350).
    (134, 146, 40.0),
    # S2 — maleza de la galería de estalactitas (en contra).
    (195, 215, -55.0),
    (250, 268, -55.0),
    # S2/S3 — C2, el empujón hacia el estribo del patio: dejar que la
    # corriente te acerque al refugio, o luchar contra ella.
    (285, 305, 40.0),
    # S3 — C3, en contra justo después del patio: resistir o subir al
    # refugio R2 (306-310), que queda a resguardo de la corriente.
    (400, 430, -40.0),
    # S4 — corriente en contra de la esclusa rota (resistencia a mitad
    # del tramo, cuando el pez ya volvió a aparecer al menos una vez).
    (455, 600, -30.0),
    # S5 — maleza del pozo del drenaje.
    (700, 725, -50.0),
    # S6 — corriente a favor del desagüe, empujón final hacia la salida.
    (800, 900, 45.0),
)

#: Estalactitas colgando del techo, en `(columna, fila_de_la_punta)` —
#: decoración de la capa BG_Near (AUD-575): el techo de la mina se ve
#: cerca, con sus pinchos, contra el aire de arriba. Densas en la
#: galería (S2) y el pozo (S5), sueltas en la entrada y el desagüe.
ESTALACTITAS: tuple[tuple[int, int], ...] = (
    (30, 2), (46, 3), (62, 2), (78, 3), (94, 2), (110, 3), (126, 2), (140, 3),
    (160, 2), (166, 2), (174, 3), (182, 2), (188, 3), (196, 2), (204, 3),
    (212, 2), (218, 3), (228, 2), (236, 3), (244, 2), (252, 3), (260, 2),
    (268, 3), (276, 2), (284, 3), (292, 2),
    (500, 2), (508, 3), (516, 2), (524, 3), (532, 2), (540, 3), (548, 2),
    (556, 3),
    (606, 2), (614, 3), (622, 2), (630, 3), (638, 2), (646, 3), (654, 2),
    (662, 3), (670, 2), (678, 3), (686, 2), (694, 3), (702, 2), (710, 3),
    (718, 2), (726, 3),
    (760, 2), (770, 3), (780, 2),
)

#: Vigas de madera oxidada sobre el andén del patio de carga — `(col,
#: fila)` en la capa Terrain_Detail, dos baldosas de viga por entrada.
VIGAS_DEL_PATIO: tuple[tuple[int, int], ...] = (
    (330, 4), (331, 4),
    (370, 4), (371, 4),
)

#: Algas de la maleza — `(col, fila)` en Terrain_Detail, donde la maleza
#: agarra (S2 y S5): la decoración marca la zona de corriente en contra
#: para que el freno se vea y se explique solo.
ALGAS: tuple[tuple[int, int], ...] = (
    (196, 28), (198, 27), (200, 28), (202, 27), (204, 28), (206, 27),
    (208, 28), (210, 27), (212, 28), (214, 27),
    (251, 28), (253, 27), (255, 28), (257, 27), (259, 28), (261, 27),
    (263, 28), (265, 27), (267, 28),
    (701, 28), (703, 27), (705, 28), (707, 27), (709, 28), (711, 27),
    (713, 28), (715, 27), (717, 28), (719, 27), (721, 28), (723, 27),
)

#: Manchas de óxido en el lecho — `(col, fila)` en Terrain_Detail: la
#: estética "mina abandonada con hierro oxidado" (AUD-575) salpica el
#: suelo de roca con el GID de óxido.
OXIDO_EN_EL_LECHO: tuple[tuple[int, int], ...] = (
    (40, 32), (60, 32), (90, 32), (120, 32), (140, 32),
    (200, 32), (240, 32), (280, 32),
    (340, 32), (370, 32), (410, 32), (430, 32),
    (490, 32), (540, 32), (580, 32),
    (630, 32), (680, 32), (720, 32),
    (780, 32), (820, 32), (860, 32),
)

#: Luces del nivel — AUD-575. Tres familias:
#:   · `warm`  — los faroles de la mina, cerca del techo (el "techo de
#:     luz" que ya marcaba el límite desde AUD-531/574); ahora iluminan
#:     el aire de arriba y la superficie del agua, que los refleja.
#:   · `blood` — luces rojas de peligro: maleza (S2), esclusa (S4) y
#:     pozo (S5). La mina avisa dónde NO conviene nadar.
#:   · `white` — luz de trabajo: la entrada, el patio de carga y el
#:     desagüe. Lugares donde se sale del agua y se respira.
#: `(col, fila, color)`.
#:
#: AUD-576 — densidad decreciente (blueprint §24/46): la secuencia es
#: "L L L L → L L → L → . → X". Muchos faroles al principio (la mina se
#: reconoce), cada vez menos, el último farol cálido en el borde del
#: abismo (col 575), NINGUNO en la zona del pez (cols 585-780) — la
#: oscuridad marca que la arquitectura humana terminó — y la luz regresa
#: en la salida (la "iluminación que vuelve" del blueprint §42). La
#: lámpara apagada de la col 320 (decoración) cuenta la misma historia
#: en miniatura: entre faroles encendidos, uno que ya no alumbra.
LUCES: tuple[tuple[int, int, str], ...] = (
    (45, 4, "warm"), (85, 4, "white"), (125, 4, "warm"),
    (175, 4, "blood"), (205, 4, "blood"), (250, 4, "warm"),
    (330, 4, "white"), (365, 4, "white"), (385, 4, "white"),
    (485, 4, "blood"), (540, 4, "blood"),
    (575, 4, "warm"),
    (830, 4, "white"), (870, 4, "white"),
)

#: Bloques de mineral (BreakableBlock) — AUD-557/575/576. Se rompen con
#: el ataque acuático (o el de tierra, sobre el andén). `(col, fila_techo)`
#: — fila_techo es el techo del bloque (sobre el lecho, sobre una viga o
#: sobre el andén del patio).
#:
#: AUD-576 — nueve bloques en progresión de propósito y de landmark
#: (blueprint §13-14): las columnas crecen de forma monótona (56 → 765)
#: para que el jugador cree un mapa mental del nivel leyendo los
#: minerales, y cada uno tiene un papel:
#:   M1 (56)  — el primer landmark: la mina se reconoce, "hay mineral".
#:   B1 (106) — tutorial: visible nada más bucear, sin riesgo a su lado.
#:   B2 (212) — acceso opcional: tras la vagoneta sumergida (V2).
#:   B3 (250) — recompensa: en la maleza, al borde del refugio R1.
#:   B4 (350) — shortcut: sobre el andén del patio, ataque de tierra.
#:   B5 (460) — ruta alternativa: al borde de la esclusa, antes del pilar.
#:   B6 (618) — pozo: en las vigas, abre el hueco para emerger.
#:   B7 (675) — pozo: segunda viga, el hueco del drenaje.
#:   B8 (765) — clímax: desbloquea el lateral con el último vestigio
#:              humano (la vagoneta cubierta de sedimentos, V3).
BLOQUES_DE_MINERAL: tuple[tuple[int, int], ...] = (
    (56, 32),                   # M1 — S1 — landmark de entrada
    (106, 32),                  # B1 — S1 — tutorial (primera inmersión)
    (212, 32),                  # B2 — S2 — acceso opcional tras la vagoneta
    (250, 32),                  # B3 — S2 — recompensa al borde de la maleza
    (350, 8),                   # B4 — S3 — andén seco (ataque de tierra)
    (460, 32),                  # B5 — S4 — ruta alternativa de la esclusa
    (618, 13),                  # B6 — S5 — EN las vigas: abren hueco para emerger
    (675, 13),                  # B7 — S5 — segunda viga del drenaje
    (765, 32),                  # B8 — S6 — clímax: el lateral de la vagoneta
)

#: Puntos de la fauna fija (la escena los instancia; el pez es aparte).
#: `(col, fila_techo, tipo)` — tipo: "cangrejo" (patrulla terreno) o
#: "medusa" (deriva en la columna). La escena los espacia con su
#: generador aislado (AUD-374).
#:
#: AUD-576 — densidad decreciente (blueprint §48): muchos al principio,
#: menos en el medio, **ninguno en la zona del pez** (cols 585-780: el
#: jugador nota "aquí abajo no hay nada" — cuando desaparece la fauna,
#: algo no está bien), y una medusa de vuelta en la salida: el miedo
#: cede, el ecosistema regresa.
FAUNA: tuple[tuple[int, int, str], ...] = (
    # S1 — los primeros habitantes: la entrada aún es "vida".
    (40, 32, "cangrejo"), (90, 32, "cangrejo"),
    (110, 20, "medusa"),
    # S2 — la galería se despuebla: cangrejo en el lecho, medusas altas.
    (180, 32, "cangrejo"), (200, 20, "medusa"), (240, 22, "medusa"),
    # S3 — el patio: dos cangrejos patrullan el andén seco, uno el lecho.
    (330, 8, "cangrejo"), (380, 8, "cangrejo"),
    (340, 32, "cangrejo"),
    # S4 — la esclusa: una sola medusa (la penúltima).
    (500, 24, "medusa"),
    # S5/S6 — zona del pez: NINGUNA. La fauna vuelve tras el clímax.
    (810, 24, "medusa"),
)

#: Vagonetas de la mina (GID 73, Terrain_Detail) — `(col, fila)`. La
#: narrativa ambiental del blueprint §3/9/24: V1 parcialmente inundada en
#: la entrada ("aquí había personas"), V2 sumergida en la galería, y V3
#: junto al último bloque de mineral del clímax (col 765), cubierta de
#: sedimentos — el último vestigio humano antes de la salida.
VAGONETAS: tuple[tuple[int, int], ...] = (
    (39, 30),     # V1 — la entrada: asomando del agua, junto al andén
    (190, 30),    # V2 — la galería: completamente sumergida
    (763, 30),    # V3 — el clímax: tras el bloque B8 (col 765)
)

#: Cadenas colgando del techo (GID 74) — `(col, fila)`: la maquinaria
#: abandonada de la mina, cada vez más escasa.
CADENAS: tuple[tuple[int, int], ...] = (
    (95, 3), (300, 3), (420, 3), (560, 3),
)

#: Lámparas apagadas (GID 75) — `(col, fila)`: la misma familia que las
#: luces encendidas, muerta. La del patio (col 320) está entre faroles
#: vivos; la del borde del abismo (col 560) es la última — después,
#: ninguna (la secuencia "L L L L → L → X" del blueprint §24).
LAMPARAS_APAGADAS: tuple[tuple[int, int], ...] = (
    (320, 4), (560, 4),
)

#: Herramientas abandonadas (GID 76) — `(col, fila)`: picos y palas en
#: el lecho, cerca de los refugios — los restos de los mineros.
HERRAMIENTAS: tuple[tuple[int, int], ...] = (
    (155, 30), (700, 30),
)


# ── Las fases del pez abismal (AUD-576) ─────────────────────────────
#
# El blueprint 10/10 convierte al pez en el "monstruo psicológico": no
# persigue hasta que el jugador ya está aterrorizado, y su revelación
# completa se reserva para el clímax. Las columnas marcan las fases:
#   · antes de COL_PRIMER_EVENTO: NO hay pez — el nivel entero de la
#     mina se juega sin persecución (la fauna basta).
#   · COL_PRIMER_EVENTO (553, x=8848): el primer evento — la sombra
#     cruza el fondo y suena el gemido, sin pez que persiga.
#   · COL_SEGUNDO_EVENTO (650, x=10400): la segunda sombra, lejana.
#   · COL_PERSECUCIONES (581): a partir de aquí (ya pasado el CP5,
#     tras el primer evento) el pez persigue de verdad.
#   · COL_CLIMAX (778, x=12448): el pez cruza el espacio en el tramo
#     final — la revelación, no un susto.
COL_PRIMER_EVENTO = 553
COL_SEGUNDO_EVENTO = 650
COL_PERSECUCIONES = 581
COL_CLIMAX = 778
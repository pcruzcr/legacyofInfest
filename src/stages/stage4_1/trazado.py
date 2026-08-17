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
lodo de la Fase 2 son dos frenos del mismo tipo (AUD-473), no un arrastre y
un freno — ver la nota junto a `FRENO_DEL_MUSGO` más abajo.

Las lomas de la Fase 3 (AUD-477)
-----------------------------------
El guion pide *«ascender por lomas utilizando slopes»* — en plural.
`LOMAS_FASE3` son dos desniveles reales, no uno: una curva baja y corta de
entrada, y una más alta después — el sube-baja-sube-baja que pide el punto
6 de la crítica de diseño del dueño (2026-08-14), en vez de una sola
joroba simétrica que en pantalla se lee como «una subida», no como un
camino que se enrolla. `altura_del_suelo(columna)` calcula la fila del
suelo para cualquier columna del mapa — el generador la usa para rellenar
tierra y la escena para colocar decoración a la altura correcta. Cuatro
objetos `Slope` (AUD-297, dos por loma) se superponen exactamente a las
rampas para que se puedan subir y bajar de verdad.
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

# ── Las lomas de la Fase 3 (AUD-477) ──────────────────────────────────────
#
# El guion original dice «ascender por LOMAS utilizando slopes» — en
# plural. La primera versión (AUD-467…470) sólo puso una: una subida, una
# meseta larga, una bajada — que en pantalla se lee como *una* subida, no
# como el camino enroscado que pide el punto 6 de la crítica de diseño
# (2026-08-14): *«el jugador no debería sentir que está subiendo una
# montaña. Debería sentir que el escenario se está enrollando alrededor de
# él»*. Dos lomas de distinta altura —una baja, de calentamiento, y la
# alta, la del «cuello» de la serpiente— dan ese sube-baja-sube-baja que
# una sola joroba simétrica no daba.
#
# Cada entrada es `(columna_inicio_subida, ancho_subida, ancho_cima,
# ancho_bajada, fila_cima)`. Se quedan dentro de la Fase 3 (columnas
# 300-449) con margen llano a los dos lados y entre las dos —el disparador
# de diálogo (columna 360) y el de liberar al espíritu (368) caen en ese
# llano intermedio, sobre suelo firme de verdad, no a media rampa.
FILA_CIMA = 20
LOMAS_FASE3: tuple[tuple[int, int, int, int, int], ...] = (
    (309, 30, 10, 16, 24),          # la primera curva: más baja, más corta
    (376, 25, 15, 20, FILA_CIMA),   # la segunda: la más alta de las dos
)


def altura_del_suelo(columna: int) -> int:
    """La fila del suelo en esa columna. `FILA_SUELO` en todas partes salvo
    en las lomas de la Fase 3, que suben y vuelven a bajar."""
    for inicio_subida, ancho_subida, ancho_cima, ancho_bajada, fila_cima in LOMAS_FASE3:
        fin_subida = inicio_subida + ancho_subida
        fin_cima = fin_subida + ancho_cima
        fin_bajada = fin_cima + ancho_bajada
        if inicio_subida <= columna < fin_subida:
            avance = (columna - inicio_subida) / ancho_subida
            return round(FILA_SUELO - avance * (FILA_SUELO - fila_cima))
        if fin_subida <= columna < fin_cima:
            return fila_cima
        if fin_cima <= columna < fin_bajada:
            avance = (columna - fin_cima) / ancho_bajada
            return round(fila_cima + avance * (FILA_SUELO - fila_cima))
    return FILA_SUELO


def perfil_del_suelo() -> tuple[int, ...]:
    """La fila del suelo, columna a columna, para todo el mapa."""
    return tuple(altura_del_suelo(c) for c in range(MW))


def altura_de_colision(columna: int) -> int:
    """La fila de la superficie en esa columna — para **colocar cosas**
    (checkpoints, disparadores, decoración), no para generar bloques sólidos.

    AUD-470 — por qué no es la misma que `altura_del_suelo`
    -----------------------------------------------------------
    La primera versión usaba el mismo perfil escalonado para pintar *y*
    para la colisión: cada columna de la rampa generaba su propio rectángulo
    sólido, un escalón de un renglón. Jugado, el jugador se quedaba clavado
    contra el primer escalón — un muro vertical de 16 px es exactamente lo
    que bloquea el movimiento horizontal en cualquier resolución de AABB,
    y el `Slope` que se superponía nunca llegaba a intervenir porque el
    jugador no conseguía entrar en su rectángulo.

    AUD-477 — la meseta tampoco puede ser un bloque sólido
    ----------------------------------------------------------
    Con la meseta como bloque sólido empezando exactamente donde
    `Slope.altura_en()` llega a `fila_cima`, un recorrido real
    (`TestLasLomasDeLaFase3::test_se_sube_y_se_baja_dos_veces_caminando`,
    caminando de verdad, no teletransportado) se quedaba clavado justo en
    ese punto — reproducible con cualquier ancho de rampa, incluso una
    carísimamente suave (probado a mano con 90 columnas de subida, mismo
    resultado), así que no es la inclinación: es el **orden de resolución
    por fotograma**. `player.py::_resolve_collision` (el AABB normal, contra
    `collision_rects`) corre **antes** que `_resolver_pendientes` (el que
    empuja al jugador por la rampa). El eje X de un fotograma se resuelve
    con la `y` que dejó el fotograma anterior — la de la rampa, que sólo
    llega a `fila_cima` en su último píxel matemático, nunca antes, porque
    eso es lo que hace una recta — así que en el fotograma en que la `x`
    cruza al territorio de la meseta sólida, la `y` todavía está un puñado
    de píxeles por debajo: el AABB los ve solapados y frena el eje X ahí,
    para siempre, porque la `x` congelada hace que `_resolver_pendientes`
    recalcule la misma `y` de siempre. Ningún ancho de rampa lo evita —se
    probó, ver el commit— porque el desajuste no depende de la pendiente,
    depende de que exista una unión dura entre «zona sin bloque sólido» y
    «bloque sólido» en absoluto.

    La solución real, la que sí funciona: la meseta **tampoco** entra en
    `collision_rects`. Es un `Pendiente` más — de altura cero, así que
    `altura_en()` devuelve la misma `y` constante en todo su ancho — y
    `_colisiones()` (`generate_stage4_1.py`) no le genera ningún bloque
    sólido (`es_meseta`). De la rampa a la meseta y de la meseta a la
    bajada, todo el recorrido de una loma es siempre el mismo sistema
    —pendientes, nunca AABB contra un bloque— y la unión dura que causaba
    el enganche deja de existir del todo, no sólo se aplaza.
    """
    for inicio_subida, ancho_subida, ancho_cima, _ancho_bajada, fila_cima in LOMAS_FASE3:
        fin_subida = inicio_subida + ancho_subida
        fin_cima = fin_subida + ancho_cima
        if fin_subida <= columna < fin_cima:
            return fila_cima
    return FILA_SUELO


def es_meseta(columna: int) -> bool:
    """¿Es la cima llana de alguna loma? Esas columnas no llevan bloque
    sólido (AUD-477, ver `altura_de_colision`): las cubre un `Pendiente`
    de altura cero, para que nunca haya una unión dura entre pendiente y
    bloque sólido en el camino de subida de una loma."""
    for inicio_subida, ancho_subida, ancho_cima, _ancho_bajada, _fila_cima in LOMAS_FASE3:
        fin_subida = inicio_subida + ancho_subida
        fin_cima = fin_subida + ancho_cima
        if fin_subida <= columna < fin_cima:
            return True
    return False


def perfil_de_colision() -> tuple[int, ...]:
    """La fila sólida, columna a columna — la que usa `_colisiones()`."""
    return tuple(altura_de_colision(c) for c in range(MW))


def loma() -> tuple[tuple[int, int, int, int, str], ...]:
    """Los `Slope` de subida y bajada de las lomas: `(columna, fila_arriba,
    ancho, alto, sube)`, dos por loma, en el orden de `LOMAS_FASE3`
    (AUD-297/477). La cima llana la da `mesetas_de_las_lomas`, no ésta —
    tiene una unidad distinta (ver por qué ahí).

    El rectángulo de un `Slope` es el triángulo entero (AUD-297): de la fila
    de arriba a la de abajo, de la columna de inicio a la de fin.
    """
    resultado: list[tuple[int, int, int, int, str]] = []
    for inicio_subida, ancho_subida, ancho_cima, ancho_bajada, fila_cima in LOMAS_FASE3:
        fin_subida = inicio_subida + ancho_subida
        fin_cima = fin_subida + ancho_cima
        alto = FILA_SUELO - fila_cima
        resultado.append((inicio_subida, fila_cima, ancho_subida, alto, "derecha"))
        resultado.append((fin_cima, fila_cima, ancho_bajada, alto, "izquierda"))
    return tuple(resultado)


def mesetas_de_las_lomas() -> tuple[tuple[int, int, int], ...]:
    """Las cimas llanas: `(columna_inicio, fila, ancho)`, en columnas —a
    diferencia de `loma()`, no lleva alto ni `sube`: es siempre plana.

    Por qué no es un `Slope` más de `alto=0`
    -------------------------------------------
    Debería serlo: una cuesta de altura cero es plana de verdad —
    `Pendiente.altura_en()` devuelve la misma `y` en todo su ancho—, y por
    eso no necesita, ni debe, ningún bloque sólido debajo (el porqué
    completo vive en `altura_de_colision`). Pero `StageObjectFactory
    ._rect_de` (`stage_objetos.py`) trata un `height` de 0 como «sin
    declarar» (`int(obj.height) or TILE_SIZE`) y le pone una baldosa
    entera de alto sin avisar — 16 px de repecho donde tenía que haber
    suelo llano. Se descubrió jugando de verdad, no en una prueba: el
    jugador caía y se tropezaba exactamente al entrar en la meseta
    (ninguna prueba anterior miraba la trayectoria fotograma a fotograma
    ahí dentro).

    La salida: el generador (`tools/generate_stage4_1.py`) coloca esta
    cima como un `Slope` con 1 **píxel** de alto, no 1 fila — que sigue
    siendo un valor verdadero (sobrevive el `or TILE_SIZE`) y es
    indistinguible de plano jugando. Como esa unidad (píxeles, no filas)
    es distinta de la de `loma()`, esta función devuelve una tupla propia
    en vez de forzar la de `loma()` a mezclar dos unidades.
    """
    resultado: list[tuple[int, int, int]] = []
    for inicio_subida, ancho_subida, ancho_cima, _ancho_bajada, fila_cima in LOMAS_FASE3:
        fin_subida = inicio_subida + ancho_subida
        resultado.append((fin_subida, fila_cima, ancho_cima))
    return tuple(resultado)


def extremos_de_las_lomas() -> tuple[int, int]:
    """`(primera_columna, última_columna)` que ocupa alguna loma —para
    zonas (como el `WindZone`) que deben cubrirlas todas, no sólo una."""
    inicio = min(loma[0] for loma in LOMAS_FASE3)
    fin = max(loma[0] + loma[1] + loma[2] + loma[3] for loma in LOMAS_FASE3)
    return inicio, fin


def fase_de_la_columna(columna: int) -> int:
    """La fase, 1 a 6, a la que pertenece esa columna del mapa."""
    return min(6, columna // ANCHO_SECCION + 1)


#: Uno por fase (AUD-516). Antes había 32 —cada 28 columnas, 448 px—, muy
#: por debajo del mínimo de 700-1200 px que pide `66_GUIA_DE_LEVEL_DESIGN.md`
#: §1: un nivel *psicológico de terror* con reaparición casi inmediata no
#: genera tensión, la anula. Seis puntos —el mismo número que fases— es la
#: densidad que el guion pide: morir cuesta rehacer una fase entera, no un
#: tramo de pantalla.
#:
#: Cada columna se eligió a mano dentro de su fase, no por fórmula, para
#: caer siempre en terreno llano y antes del set piece de esa fase, nunca
#: encima: antes del musgo/lodo de la Fase 2 (`SEGMENTOS_FASE2`, desde 170),
#: antes de que empiece a subir la primera loma de la Fase 3 (`LOMAS_FASE3`,
#: desde 309), y bien antes del mirador (`COLUMNA_MIRADOR_FASE6`, 860) y del
#: umbral del despertar (`Stage4_1.AVANCE_DEL_DESPERTAR`, columna ~888) de
#: la Fase 6.
COLUMNAS_CHECKPOINT: tuple[int, ...] = (20, 155, 302, 470, 620, 760)


def checkpoints() -> tuple[tuple[int, int], ...]:
    """Los puntos de reaparición, en `(columna, fila)` — a la altura
    **sólida**, no la visual: uno colocado en la fila que pinta la rampa
    quedaría flotando sobre el suelo llano de verdad que hay debajo."""
    return tuple((c, altura_de_colision(c)) for c in COLUMNAS_CHECKPOINT)


# ── Fase 2 (El Venado): musgo y lodo ─────────────────────────────────────
#
# Segmentos de suelo, en `(columna_inicio, ancho, material)`.
#
# AUD-473 — el musgo usaba `arrastre`, no `multiplicador`.
# ---------------------------------------------------------
# La primera versión ponía `arrastre=62.0` en el musgo pensando en «el musgo
# te arrastra». Pero en `ZonaDeFriccion` (`components.py`, AUD-236)
# `arrastre` es la cinta transportadora — mueve `posicion.x` directo, ignora
# la entrada del jugador por completo — y `Conveyor` (el tipo de objeto TMX
# dedicado a cintas) usa el mismo campo con 60.0 de valor por defecto. 62 era
# casi ese valor por casualidad de nombre, no de mecánica: el jugador cruzaba
# el tramo de musgo como pasajero de una cinta, sin soltar el control en
# ningún otro momento — comprobado jugando el nivel de verdad, no en una
# prueba (el propio dueño lo vio como «se congela», porque nada más en la
# pantalla decía que el personaje se movía solo).
#
# El campo correcto para «resbaloso» es `multiplicador`, el mismo que ya usa
# el lodo. Con un matiz: el docstring de `ZonaDeFriccion` avisa de que
# `multiplicador > 1` «se dispara sin tope» porque se compone cada fotograma
# mientras el jugador está dentro de la zona — no hay un valor «resbaloso
# pero seguro» por encima de 1 en este motor. Así que el musgo no frena
# menos que el lodo por ser más resbaloso: frena **un poco menos fuerte**,
# con el mismo mecanismo probado (AUD-236), para poder distinguirlo del lodo
# sin reintroducir el problema del arrastre.
SEGMENTOS_FASE2: tuple[tuple[int, int, str], ...] = (
    (170, 15, "musgo"),
    (190, 15, "lodo"),
    (210, 15, "musgo"),
    (230, 15, "lodo"),
    (250, 15, "musgo"),
)
#: Huellas del Venado (AUD-513, GAP-060 punto 28): *«herramienta de
#: navegación... a veces desaparecen o terminan abruptamente»*. En columnas
#: relativas al inicio de la Fase 2, antes de `DESVIO_COLUMNA_DIALOGO` (60):
#: se ven mientras el Venado sigue siendo una presencia que se persigue, no
#: después de que ya habló. Tres grupos, no un rastro continuo —el hueco
#: entre 34 y 42 y el corte antes de llegar al diálogo son el «termina
#: abruptamente»— y espaciado irregular dentro de cada grupo, no una regla
#: fija: un rastro perfectamente uniforme se lee como decoración de baldosa,
#: no como pisadas de verdad.
HUELLAS_FASE2: tuple[int, ...] = (
    12, 14, 17, 19, 22,
    26, 28, 31,
    42, 44, 47, 48, 51,
)

#: Cuánto frena el musgo: se anda al 94 % — un roce más suave que el lodo.
FRENO_DEL_MUSGO = 0.94
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

#: De qué columna viene el canto ancestral de la Fase 5 (AUD-488).
#:
#: GAP-063 pide que en la Planicie *«el sonido sustituya a la vista como
#: orientación»* (puntos 12-14) y observa que hoy no lo hace: el canto es un
#: bucle de ambiente en volumen constante, sin dirección, y por tanto
#: inservible para orientarse. Un punto **fijo** es lo que lo convierte en
#: navegación: el paneo estéreo dice de qué lado queda, y como está al final
#: de la sección —justo antes de la frontera con la Fase 6 (columna 750)—
#: caminar hacia el canto es caminar hacia la salida.
#:
#: Ésta es la mitad *fiable* de la «mezcla de información confiable e
#: información ambigua» del punto 14. La ambigua ya existe y es el grito del
#: Gavilán, que desde AUD-492 hace justo lo contrario: rehúye la mirada del
#: jugador.
COLUMNA_DEL_CANTO: int = 745


# ── Fase 6 (El Camino hacia Paburu): grietas que se iluminan al paso ─────
#
# AUD-482, GAP-063 — antes empezaban en la columna 760, diez columnas
# después de que arrancara la Fase 6 (750): el corte con la Planicie de
# los Muertos era seco. Los puntos 29-30 del documento de la Fase 5
# (2026-08-14) piden justo lo contrario: *«pequeñas luces verdes que
# empiezan a sustituir a la luna como guía»* antes de que termine esa
# sección. El mecanismo que las enciende (`Stage4_1._actualizar_grietas`,
# por proximidad) no mira de qué fase es la columna — así que basta con
# que el rango empiece antes: las tres primeras (700, 720, 740) caen ya
# en el tramo final de la Fase 5 (columnas 600-749), el resto sigue en la
# Fase 6 de siempre.
GRIETAS_FASE6: tuple[int, ...] = tuple(range(700, 899, 20))


# ── El mirador de la Fase 6 (AUD-515, GAP-064 punto 17) ──────────────────
#
# *«El jugador mira atrás y ve el camino que recorrió»*. Antes se daba por
# bloqueado —«necesita un sistema de cámara que este motor no tiene»—, pero
# `CutsceneSystem` ya sabe mover la cámara (`camara x y duración`,
# `cutscene_guion.py`) y ya se usa en este mismo mapa para la cutscene de
# introducción. Columna 860: bien entrada la Fase 6 (750-899) y antes de
# `Stage4_1.AVANCE_DEL_DESPERTAR` (0,92 del tramo, columna ~888) — el
# jugador ya vio casi todo el camino cuando se detiene a mirarlo, y todavía
# le queda tramo por delante hasta el corte.
COLUMNA_MIRADOR_FASE6: int = 860


def grietas_de_pisada() -> tuple[tuple[int, int], ...]:
    return tuple((c, altura_del_suelo(c)) for c in GRIETAS_FASE6)


# ── El easter egg de la Fase 1 ────────────────────────────────────────────
#
# Dos lápidas, una junto a la otra. Los nombres los dio el dueño del
# proyecto (2026-08-14): no se inventa ninguna fecha ni ningún dato más.
COLUMNA_LAPIDA_TERESA = 30
COLUMNA_LAPIDA_HUGO = 34
NOMBRE_LAPIDA_TERESA = "Teresa Murillo"
NOMBRE_LAPIDA_HUGO = "Hugo Salazar Castillo"

#: AUD-513, GAP-059 punto 2 — *«tumbas con reacciones distintas: una con
#: sonido al acercarse»*. Antes la única variación de la Fase 1 era el
#: easter egg (Teresa/Hugo, con nombre y `MessageTrigger`) — una sola
#: historia, no varias. Ésta reacciona por sonido, no por texto ni
#: silueta: nadie le pone nombre, y por eso puede repetirse sin que se lea
#: como el mismo fantasma otra vez. Lejos de las lápidas del easter egg y
#: de la anomalía ambigua (30/34/95) para que las tres lecturas —recuerdo
#: de familia, sonido, duda— no se pisen entre sí.
COLUMNA_TUMBA_SUSURRO = 60


# ── Dónde caen el diálogo y la liberación de cada espíritu ────────────────
#
# A cuántas columnas del inicio de su sección coloca el generador
# (`tools/generate_stage4_1.py`) el `MessageTrigger` de diálogo y, un poco
# más adelante, el `EventTrigger` de liberación (AUD-474). Antes eran dos
# literales (`+ 60`, `+ 68`) repetidos en el generador; ahora también los
# necesita la escena (AUD-479, GAP-060: las apariciones previas del Venado
# terminan justo donde empieza su diálogo) — un solo sitio para los dos,
# para que no puedan desincronizarse, el mismo motivo que ya justificó
# `evento_de_liberacion` más abajo.
DESVIO_COLUMNA_DIALOGO = 60
DESVIO_COLUMNA_LIBERACION = 68


# ── La anomalía ambigua de la Fase 1 (AUD-478, GAP-059) ───────────────────
#
# La crítica de diseño del dueño (2026-08-14, punto 7) pedía que la Fase 1
# tuviera algo sobrenatural que no fuera el easter egg personal: una figura
# que se ve menos de un segundo y nunca se confirma. Lejos de las lápidas
# (columnas 30/34) para no mezclarse con el fantasma de Teresa —ese sí se
# confirma con un `MessageTrigger` y un nombre—, y bien entrada la sección
# para que ocurra cuando el jugador ya se siente cómodo explorando, no en
# los primeros pasos.
COLUMNA_ANOMALIA_FASE1 = 95


# ── Liberar a los espíritus (AUD-474) ─────────────────────────────────────
#
# Nombre del evento del `EventTrigger` que cada espíritu deja junto a su
# punto de diálogo — compartido entre el generador (que lo coloca) y la
# escena (que lo escucha), para que no puedan desincronizarse.
def evento_de_liberacion(numero_de_fase: int) -> str:
    return f"espiritu_liberado_{numero_de_fase}"


#: El mensaje del umbral final, antes de que `Stage4_1` lo ajuste según
#: cuántos espíritus se liberaron de verdad (ver `_actualizar_mensaje_final`).
#: El generador lo escribe tal cual; la escena lo busca por este texto
#: exacto para saber cuál `MessageTrigger` reescribir.
TEXTO_FINAL_BASE = "Paburu despierta."

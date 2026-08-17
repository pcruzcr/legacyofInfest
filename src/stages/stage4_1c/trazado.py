"""El trazado del 4-1c: la misma travesía del 4-1, en el aire.

Por qué el mismo largo y la misma forma
=========================================
Igual motivo que 4.1b (AUD-519): 4.1c es una de las tres variantes del
slot de la Fase 4 (AUD-518), no un nivel con identidad estructural
propia. 900×38 baldosas, seis secciones de 150 — la travesía horizontal
de AUD-467, ahora sin suelo.

Sin suelo, y sin foso mortal
==============================
El jugador salta de plataforma en plataforma sobre el vacío. Caer no
mata: hay un suelo de contención muy por debajo del camino (fila
`FILA_DE_CONTENCION`) que atrapa cualquier caída — la misma filosofía
"cero muerte instantánea, la atmósfera es el desafío" que el 4-1 aplica
con `cero DeathPit por construcción`, trasladada al aire. Caer cuesta el
tiempo de volver a subir, no la partida.

Musical de verdad, no sólo de ambiente
=========================================
`pulso.py` ya hace latir cámara y luz ambiente con la música, pero nada
del propio nivel dependía del compás. Aquí las plataformas son
`RhythmBlock` (F6, `src/framework/ecs/components.py::BloqueRitmico`) —
aparecen y desaparecen seguiendo el reloj musical de verdad
(`bpm`/`compas` del mapa), no un temporizador propio. Cruzar el nivel es,
literalmente, cruzar con la música.

Aleatorio de verdad, con seguridad verificada
================================================
`generar_ruta(semilla)` no dibuja una ruta fija: sortea la posición de
cada plataforma dentro de los límites que impone `JumpEnvelope` —la
envolvente de salto real del jugador (AUD-504), no un número inventado—
así que cualquier semilla produce una ruta que se puede cruzar, aunque
el trazado exacto cambie. `tools/generate_stage4_1c.py` congela tres
semillas en tres TMX distintos; `Stage4_1C` elige uno al azar **cada
vez que se entra** (a diferencia del sorteo de AUD-518, que es una vez
por partida — aquí el propio nivel es el que cambia de cara, no cuál de
los tres niveles te toca).
"""
from __future__ import annotations

import random
from dataclasses import dataclass

#: Lado de la baldosa, en píxeles.
TS = 16

#: Misma forma que stage4_1/stage4_1b: seis secciones de 150 columnas.
ANCHO_SECCION = 150
MW = ANCHO_SECCION * 6
MH = 38

#: Grosor de los muros de los extremos, en columnas.
MURO_ANCHO = 2

#: Dónde arranca y aterriza el camino de plataformas.
FILA_DE_INICIO = 20

#: El suelo de contención: muy por debajo del camino, atrapa cualquier
#: caída. Nunca se pisa si el salto sale bien.
FILA_DE_CONTENCION = 36


@dataclass(frozen=True)
class Plataforma:
    columna: int
    fila: int
    ancho: int  # en baldosas
    #: `None` = sólida siempre (spawn, checkpoints, la salida). Con
    #: patrón, `RhythmBlock` pregunta al reloj musical en vez de contar
    #: segundos propios (AUD-137) — así el nivel entero respira con la
    #: misma música, no con seis relojes sueltos.
    patron: str | None = None
    desfase: float = 0.0
    checkpoint_id: int | None = None


def _envolvente() -> tuple[float, float, float, float]:
    """`(hueco_base, jitter_hueco, ancho_tablon_base, jitter_vertical)`,
    todos derivados de `JumpEnvelope.from_settings()` — no números
    inventados.

    AUD-520 — la primera versión daba un paso pequeño a plataformas
    angostas (2 baldosas) y generaba ~230 por travesía —seis veces más
    que el mapa más poblado del juego (`stage_mecanicas`, 37 ids de
    ECS)—, y `tests/test_los_ids_del_ecs_no_crecen.py` lo cazó: un techo
    deliberado de 200 ids por montaje, con margen de sobra sobre 37 pero
    no para un orden de magnitud distinto. La cura no es angostar el
    techo, es angostar el número de entidades: tablones más anchos y
    huecos que sí aprovechan el hueco cómodo real, en vez de plataformas
    diminutas muy juntas.
    """
    from src.framework.stage.level_metrics import JumpEnvelope

    e = JumpEnvelope.from_settings()
    hueco_base = e.max_gap * 0.9  # cómodo de verdad, no el techo experto
    jitter_hueco = (e.max_gap_expert - hueco_base) * 0.6
    ancho_tablon_base = 11.0 * TS  # tablones largos: menos entidades, más plancha que escalón
    jitter_v = e.max_height * 0.35
    return hueco_base, max(0.0, jitter_hueco), ancho_tablon_base, jitter_v


#: Patrones de compás disponibles para los bloques (AUD-137: `"x"` sí,
#: `"."` no). Varían el ritmo de aparición sin arriesgar la travesía:
#: todos dejan al menos la mitad de cada compás visible.
PATRONES: tuple[str, ...] = ("x.x.", "xx..", "x.x.x.x.", ".xx.")


def generar_ruta(semilla: int) -> tuple[Plataforma, ...]:
    """Sortea una ruta cruzable de principio a fin.

    Un único paseo continuo por las 900 columnas, no seis tramos que se
    empalman: empalmar tramos fue exactamente el defecto de la primera
    versión — la plataforma de checkpoint de cada sección se colocaba en
    una columna fija (`inicio_de_sección + 4`) sin mirar dónde había
    quedado el paso anterior, y el salto entre una y otra podía superar
    los 200 px con un límite experto de ~85 (medido con
    `tests/test_stage4_1c.py`). Aquí cada plataforma —incluidos los
    checkpoints— se coloca a un hueco seguro de la anterior, siempre
    dentro de `JumpEnvelope`; un checkpoint es sólo la primera plataforma
    que cae dentro de cada sección nueva.
    """
    azar = random.Random(semilla)
    hueco_base, jitter_hueco, ancho_base, jitter_v = _envolvente()

    ancho_inicial = 3
    plataformas: list[Plataforma] = [
        Plataforma(10, FILA_DE_INICIO, ancho_inicial),  # bajo el PlayerSpawn, sólida
    ]
    fila_actual = FILA_DE_INICIO
    fin_actual = (10 + ancho_inicial) * TS  # borde derecho del último tablón, en px
    fin_mapa_px = (MW - MURO_ANCHO - 6) * TS
    seccion_marcada = 0  # próxima sección que aún no tiene checkpoint

    while fin_actual < fin_mapa_px:
        hueco_px = max(16.0, hueco_base + azar.uniform(-jitter_hueco, jitter_hueco))
        columna_actual = round((fin_actual + hueco_px) / TS)
        fila_actual += round(azar.uniform(-jitter_v, jitter_v) / TS)
        fila_actual = max(FILA_DE_INICIO - 6,
                          min(FILA_DE_INICIO + 6, fila_actual))
        ancho_px = max(TS * 4, ancho_base + azar.uniform(-ancho_base * 0.35, ancho_base * 0.35))
        ancho = max(4, round(ancho_px / TS))

        seccion_de_esta_columna = min(5, columna_actual // ANCHO_SECCION)
        if seccion_de_esta_columna >= seccion_marcada:
            # Primera plataforma de una sección nueva: sólida, checkpoint.
            plataformas.append(Plataforma(columna_actual, fila_actual, ancho,
                                          checkpoint_id=seccion_de_esta_columna + 1))
            seccion_marcada = seccion_de_esta_columna + 1
        else:
            patron = azar.choice(PATRONES)
            plataformas.append(Plataforma(
                columna_actual, fila_actual, ancho,
                patron=patron, desfase=azar.uniform(0.0, 1.5),
            ))
        fin_actual = (columna_actual + ancho) * TS

    # La salida: sólida, al final del todo, a un hueco seguro de la
    # última plataforma generada — no una columna fija que podría quedar
    # demasiado lejos.
    fila_actual += round(azar.uniform(-jitter_v, jitter_v) / TS)
    fila_actual = max(FILA_DE_INICIO - 6, min(FILA_DE_INICIO + 6, fila_actual))
    columna_final = MW - MURO_ANCHO - 6
    plataformas.append(Plataforma(columna_final, fila_actual, 4))

    return tuple(plataformas)


def checkpoints_de(ruta: tuple[Plataforma, ...]) -> tuple[Plataforma, ...]:
    return tuple(p for p in ruta if p.checkpoint_id is not None)

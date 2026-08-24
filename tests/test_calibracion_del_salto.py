"""AUD-204 — cuánto salta el jugador de verdad, medido y fijado.

Qué fija este fichero
---------------------
`JumpEnvelope` (`src/framework/stage/level_metrics.py`) **calcula** el alcance
del salto con la fórmula del tiro parabólico, y con ese número `grade_stage.py`
califica los 17 mapas y decide si un nivel de estudiante es transitable. Nadie
había comprobado nunca que ese cálculo coincidiera con lo que hace el motor.

Estas pruebas ejecutan al `Player` real sobre huecos y repechos sintéticos
(`tests/playtest/jump_bench.py`) y clavan el resultado. Sirven para dos cosas:

1. **Trinquete de calibración.** `GRAVITY` y `PLAYER_JUMP_FORCE` recalibran los
   17 mapas de golpe y afectan a entregas ya calificadas. Tocarlas puede ser la
   decisión correcta, pero no debe poder hacerse sin enterarse: si alguien las
   cambia, estas pruebas fallan y dicen exactamente qué talla de hueco se acaba
   de volver imposible.
2. **Contraste con el calificador.** Las tres últimas pruebas comparan lo medido
   con lo que el calificador calcula. Hasta AUD-504 documentaban un
   desacuerdo real (GAP-024); ahora documentan que `JumpEnvelope` integra la
   misma física a paso fijo que el jugador y separa técnica natural de
   técnica experta en vez de confundirlas.

Ninguna prueba de aquí propone cambiar la física. Sólo la miden.
"""
from __future__ import annotations

import pytest

from src.engine.core import settings
from src.framework.stage.level_metrics import JumpEnvelope
from tests.playtest.jump_bench import (
    barrido_huecos,
    barrido_repechos,
    maximo_superable,
    medir_hueco,
)

TILE = settings.TILE_SIZE


# El barrido cuesta segundos, no milisegundos: se hace una vez por módulo y las
# pruebas leen el resultado. Los topes están ajustados a lo justo para probar
# cada techo (una talla por encima de la última que se supera) — barrer hasta 12
# no añade información y triplica el coste.
@pytest.fixture(scope="module")
def huecos_naturales(_pygame_init):
    return barrido_huecos(4)


@pytest.fixture(scope="module")
def huecos_expertos(_pygame_init):
    return barrido_huecos(6, soltar_direccion=True)


@pytest.fixture(scope="module")
def repechos(_pygame_init):
    return barrido_repechos(6)


# ── Lo medido ──────────────────────────────────────────────────


def test_manteniendo_la_direccion_se_cruzan_tres_baldosas(huecos_naturales):
    """Jugando como juega cualquiera: 3 baldosas y ni una más.

    Es el número que importa para diseñar niveles, porque es el que consigue un
    jugador que no sabe que soltar la dirección en el aire le lleva más lejos.
    """
    assert maximo_superable(huecos_naturales) == 3


def test_la_tercera_baldosa_ya_es_de_precision(huecos_naturales):
    """Superable no es lo mismo que jugable.

    El hueco de 3 baldosas sale de menos de uno de cada diez despegues. Un nivel
    que lo use como paso obligatorio no está pidiendo un salto: está pidiendo
    doce intentos. Se fija el umbral en 15 % para que la prueba hable de la
    holgura y no del recuento exacto, que sí puede moverse un despegue arriba o
    abajo con un cambio inocuo de colisión.
    """
    tres = next(m for m in huecos_naturales if m.baldosas == 3)
    assert tres.superable
    assert tres.margen < 0.15


def test_soltando_la_direccion_se_cruzan_cinco_baldosas(huecos_expertos):
    """La técnica experta casi duplica el alcance.

    `AirborneState` sólo escribe `velocity.x` cuando hay dirección pulsada, así
    que soltarla conserva los 90 px/s del suelo en vez de bajar a los 45 px/s
    aéreos. Es contraintuitivo —soltar el mando te lleva más lejos— pero es lo
    que hace el motor, y es la única forma de alcanzar lo que la envolvente
    analítica promete.
    """
    assert maximo_superable(huecos_expertos) == 5


def test_los_repechos_llegan_a_cinco_baldosas(repechos):
    """El alcance vertical sí se corresponde con la fórmula.

    90,25 px de altura teórica son 5,64 baldosas, y se suben 5. El error del
    calificador es sólo horizontal: la altura no depende de la velocidad de
    avance, que es justo lo que el modelo analítico se equivoca al suponer.
    """
    assert maximo_superable(repechos) == 5


# ── Lo medido contra lo que calcula el calificador (AUD-504, antes GAP-024) ──


def test_la_envolvente_separa_tecnica_natural_de_tecnica_experta():
    """`max_gap` es la técnica natural (2 baldosas); `max_gap_expert`, la de soltar
    la dirección al despegar (5 baldosas).

    Antes de AUD-504 `JumpEnvelope` calculaba un único número —el techo
    experto— y lo llamaba `max_gap` sin más, así que `classify_gap` medía a
    todo el mundo con la vara del jugador que suelta la dirección en el aire.
    Ahora integra la misma física a paso fijo que `Player._apply_physics`
    (Euler semi-implícito) y separa las dos técnicas, que es lo que
    `AirborneState` realmente distingue (`velocity.x *= 0.5` si se mantiene
    pulsada la dirección).
    """
    env = JumpEnvelope.from_settings()
    assert int(env.max_gap // TILE) == 2
    assert int(env.max_gap_expert // TILE) == 5


def test_el_calificador_ya_no_llama_comodo_a_un_hueco_que_nadie_cruza_normal(
    huecos_naturales,
):
    """Un hueco de 4 baldosas, imposible con entrada natural, ya no es «cómodo».

    Éste era el daño concreto de GAP-024: el calificador aprobaba como holgado
    un hueco que el jugador normal no cruza. AUD-504 lo corrige clasificándolo
    «exigente» (dentro del techo experto, fuera de la comodidad natural), no
    «imposible» del todo —porque con la técnica de soltar la dirección sí se
    cruza el 61 % de las veces (`jump_bench`)— pero ya nunca «cómodo».
    """
    env = JumpEnvelope.from_settings()
    cuatro = next(m for m in huecos_naturales if m.baldosas == 4)

    assert env.classify_gap(4 * TILE) != "cómodo"
    assert cuatro.despegues_validos == 0


def test_el_alcance_experto_ya_no_promete_un_salto_aereo_desconectado(
    huecos_expertos,
):
    """`max_gap_expert` (antes `max_gap_with_air_jump`) ronda las 5 baldosas, no 10,69.

    El nombre viejo prometía que el salto aéreo sumaba un segundo arco; medido,
    no dispara —`AirborneState` nunca consulta `_can_jump` fuera de la ventana
    de coyote, así que la rama de salto aéreo no se alcanza en el aire— y el
    campo se renombró para dejar de prometerlo. 85,5 px (5,34 baldosas) es el
    techo de la técnica de soltar la dirección, que sí es real y que
    `jump_bench` mide al 27 % de margen en la quinta baldosa y al 0 % en la
    sexta.
    """
    env = JumpEnvelope.from_settings()
    seis = next(m for m in huecos_expertos if m.baldosas == 6)

    assert env.max_gap_expert / TILE < 6
    assert env.classify_gap(6 * TILE) == "imposible"
    assert not seis.superable
    assert not medir_hueco(6).superable

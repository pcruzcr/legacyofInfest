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
   con lo que el calificador cree, y documentan dónde no coinciden (GAP-024).

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


# ── Lo medido contra lo que cree el calificador (GAP-024) ──────


def test_la_envolvente_analitica_describe_la_tecnica_experta():
    """85,5 px son 5,34 baldosas: el techo experto, no el natural.

    No es un fallo del cálculo —la fórmula es correcta para su supuesto— sino
    del supuesto: da por hecho que el jugador mantiene la velocidad del suelo
    durante todo el vuelo, y eso sólo pasa si suelta la dirección.
    """
    env = JumpEnvelope.from_settings()
    assert int(env.max_gap // TILE) == 5


def test_el_calificador_llama_comodo_a_un_hueco_que_nadie_cruza_normal(
    huecos_naturales,
):
    """Un hueco de 4 baldosas se califica «cómodo» y es natural-imposible.

    Éste es el daño concreto de GAP-024, y cae del lado peor: el calificador no
    avisa. Un estudiante coloca 64 px de vacío, `grade_stage` se lo aprueba
    como holgado, y el nivel entregado no se puede pasar sin una técnica que no
    está documentada en ninguna parte del material del curso.
    """
    env = JumpEnvelope.from_settings()
    cuatro = next(m for m in huecos_naturales if m.baldosas == 4)

    assert env.classify_gap(4 * TILE) == "cómodo"
    assert cuatro.despegues_validos == 0


def test_el_alcance_con_salto_aereo_no_lo_alcanza_ninguna_tecnica(
    huecos_expertos,
):
    """`max_gap_with_air_jump` promete 10,69 baldosas y no se cruzan ni 6.

    El término existe porque `PLAYER_AIR_JUMPS = 1`, pero el salto aéreo no está
    conectado: `AirborneState` sólo guarda la pulsación en `_pending_jump` para
    gastarla al aterrizar, y la rama de `_can_jump` que autoriza el salto en el
    aire únicamente se consulta desde los estados de suelo, donde ya se está
    pisando algo. La constante está, la mecánica no.

    Importa porque `reachable_platforms` y `exit_is_reachable` usan **este**
    número como alcance de conexión entre plataformas: el grafo de transitabilidad
    de los 17 mapas se construye con el doble del salto real.

    Si alguien conecta el salto aéreo, esta prueba falla. Eso es lo que se quiere:
    el número del calificador y el del motor tienen que volver a compararse.
    """
    env = JumpEnvelope.from_settings()
    seis = next(m for m in huecos_expertos if m.baldosas == 6)

    assert env.max_gap_with_air_jump / TILE > 10
    assert not seis.superable
    assert not medir_hueco(6).superable

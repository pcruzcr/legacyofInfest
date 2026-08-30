"""
Module: test_sol_poniente
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: VI (Animación con easing e interacción por EventBus)
Description: Pruebas del sol que se pone.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

from itertools import pairwise

import pytest

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.stages.stage1_1.animation.sol_poniente import (
    EVENTO_SOL_EN_EL_HORIZONTE,
    SolPoniente,
)


@pytest.fixture
def sol() -> SolPoniente:
    return SolPoniente()


# ── El easing ───────────────────────────────────────────────────────

def test_el_easing_respeta_los_extremos(sol: SolPoniente) -> None:
    """u(0)=0 y u(1)=1: el sol sale y se pone donde el diseño dice.

    Es la propiedad que hace segura cualquier curva de easing. Si no la
    cumpliera, cambiar de curva movería también los puntos de salida y de
    puesta, y elegir el ritmo dejaría de ser independiente de elegir el sitio.
    """
    assert sol.progreso_suavizado(0.0) == pytest.approx(0.0)
    assert sol.progreso_suavizado(1.0) == pytest.approx(1.0)


def test_el_easing_es_monotono(sol: SolPoniente) -> None:
    """El sol nunca sube. Un easing con rebote —`ease_out_bounce`— lo haría
    saltar sobre el horizonte, y por eso no se eligió."""
    valores = [sol.progreso_suavizado(i / 40) for i in range(41)]
    assert all(b >= a for a, b in pairwise(valores))


def test_arranca_y_frena_despacio_y_corre_por_el_medio(sol: SolPoniente) -> None:
    """La firma de `ease_in_out_quad`: velocidad nula en los extremos y
    máxima en el centro. Eso es el arranque y el frenado suaves, y es lo que
    distingue un atardecer de un objeto que se cae.

    Se mide como diferencias finitas sobre la curva, no leyendo la fórmula:
    así la prueba sigue valiendo si algún día se cambia de curva por otra con
    la misma propiedad.
    """
    paso = 0.02
    def velocidad(t: float) -> float:
        return (sol.progreso_suavizado(t + paso) - sol.progreso_suavizado(t)) / paso

    v_inicio, v_medio, v_final = velocidad(0.0), velocidad(0.49), velocidad(1.0 - paso)
    assert v_medio > v_inicio * 1.5
    assert v_medio > v_final * 1.5


def test_el_avance_fuera_de_rango_no_rompe(sol: SolPoniente) -> None:
    """`stage_progress()` puede salirse de [0,1] si el jugador retrocede
    antes del spawn o pasa del NextTrigger. El sol se queda en su sitio."""
    assert sol.progreso_suavizado(-3.0) == pytest.approx(0.0)
    assert sol.progreso_suavizado(9.0) == pytest.approx(1.0)


# ── El recorrido en pantalla ────────────────────────────────────────

def test_el_sol_baja_y_va_hacia_atras(sol: SolPoniente) -> None:
    """El jugador sube hacia el este, así que el sol queda a su espalda: se
    mueve hacia la izquierda mientras baja."""
    x0, y0 = sol.posicion(0.0)
    x1, y1 = sol.posicion(1.0)
    assert x1 < x0, "el sol tiene que quedarse atrás"
    assert y1 > y0, "en pantalla, bajar es que crezca la Y"


def test_el_sol_no_se_sale_de_la_pantalla(sol: SolPoniente) -> None:
    for i in range(21):
        x, y = sol.posicion(i / 20)
        assert 0 <= x <= settings.INTERNAL_WIDTH
        assert 0 <= y <= settings.INTERNAL_HEIGHT


def test_el_halo_crece_al_bajar(sol: SolPoniente) -> None:
    """Cerca del horizonte la luz atraviesa más atmósfera: el disco se ve
    más grande y más difuso."""
    assert sol.radio_del_halo(1.0) > sol.radio_del_halo(0.0)


# ── El evento propio ────────────────────────────────────────────────

class _Oyente:
    """Un oyente con nombre, no un lambda suelto.

    DOS COSAS DEL `EventBus` QUE HAY QUE SABER, y que estas pruebas
    descubrieron a la primera:

    1. **`emit()` sólo ENCOLA.** El reparto ocurre en `dispatch()`, que el
       bucle de juego llama una vez por fotograma. Un `emit` sin `dispatch`
       no le llega a nadie. Por eso los tests de abajo despachan a mano.

    2. **El bus guarda referencias DÉBILES.** Un `lambda` que no esté
       guardado en ninguna parte se recolecta y la suscripción se cae sola
       —con un aviso en el log, pero se cae—. Los métodos enlazados de un
       objeto vivo sí sobreviven, que es como se suscribe la escena.
    """

    def __init__(self) -> None:
        self.recibidos: list[dict] = []

    def __call__(self, **datos: object) -> None:
        self.recibidos.append(datos)


def _escuchar(bus: EventBus) -> _Oyente:
    oyente = _Oyente()
    bus.subscribe(EVENTO_SOL_EN_EL_HORIZONTE, oyente)
    return oyente


def test_al_principio_no_avisa(sol: SolPoniente) -> None:
    bus = EventBus()
    oyente = _escuchar(bus)
    sol.revisar_horizonte(0.0, bus)
    bus.dispatch()
    assert oyente.recibidos == []


def test_avisa_al_cruzar_el_horizonte(sol: SolPoniente) -> None:
    bus = EventBus()
    oyente = _escuchar(bus)
    assert sol.revisar_horizonte(1.0, bus) is True
    bus.dispatch()
    assert len(oyente.recibidos) == 1


def test_avisa_UNA_sola_vez(sol: SolPoniente) -> None:
    """Un evento de «ya ocurrió» que se re-emite cada fotograma es el defecto
    que el profesor apuntó en AUD-602 con el cierre de nivel: sesenta avisos
    por segundo mientras el jugador siga ahí parado."""
    bus = EventBus()
    oyente = _escuchar(bus)
    for _ in range(60):
        sol.revisar_horizonte(1.0, bus)
        bus.dispatch()
    assert len(oyente.recibidos) == 1


def test_reiniciar_vuelve_a_armar_el_aviso(sol: SolPoniente) -> None:
    """Al morir y reaparecer, el jugador vuelve atrás y el sol con él."""
    bus = EventBus()
    oyente = _escuchar(bus)
    sol.revisar_horizonte(1.0, bus)
    bus.dispatch()
    sol.reiniciar()
    sol.revisar_horizonte(1.0, bus)
    bus.dispatch()
    assert len(oyente.recibidos) == 2


def test_sin_bus_no_revienta(sol: SolPoniente) -> None:
    """Las pruebas del motor construyen escenas sin bus. No es motivo para
    caerse."""
    assert sol.revisar_horizonte(1.0, None) is False

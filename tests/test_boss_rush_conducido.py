"""AUD-261 — el Boss Rush deja de ser cuatro jefes seguidos sin marcador.

Lo que había (GAP-030)
======================
`boss_rush_entry` construía el modo, lo arrancaba y lo dejaba en
`context.boss_rush`, **donde nadie lo leía**. Medido:

* `advance_to_next()` y `record_hit()` no tenían llamante fuera del módulo, así
  que la puntuación nunca se calculaba y `hits_taken` se quedaba en 0;
* `_carry_over_health` y `_carry_over_meter` se ponían a 0.0 en el constructor
  y otra vez en `start()`, sin getter ni setter: **el arrastre de vida no
  existía ni dentro del propio módulo**;
* `docs/44` §4 declaraba «✅ Complete — gauntlet logic, scoring, health
  carry-over». Las tres eran falsas.

Lo que hay ahora
----------------
El modo se **conduce** desde `StageScene`, que es quien sabe cuándo empieza un
combate, cuándo el jugador recibe un golpe y cuándo cae el jefe:

* la salud con la que terminas un jefe es con la que empiezas el siguiente,
  con una curación parcial declarada en `CURACION_ENTRE_COMBATES`;
* cada golpe recibido cuenta, y resta puntuación;
* al caer el jefe se acredita el combate y se pasa al siguiente.

Por qué hay curación entre combates
-----------------------------------
Sin ella el arrastre puro convierte el gauntlet en una carrera imposible: se
llega al tercer jefe con media vida y al cuarto sin nada, y nadie ha jugado
esto lo bastante para calibrar lo contrario. Una fracción fija y **declarada
en una constante con nombre** es honesta: se ve, se discute y se cambia en un
sitio. Ocultarla dentro de una fórmula sería repetir el pecado de `docs/44`.
"""
from __future__ import annotations

import pytest

from src.framework.stage.boss_rush_mode import (
    CURACION_ENTRE_COMBATES,
    BossRushMode,
    BossRushStage,
)


def _modo(n: int = 3) -> BossRushMode:
    modo = BossRushMode()
    for i in range(n):
        modo.add_stage(BossRushStage(f"boss{i}", f"Jefe {i}", scene_builder=None))
    modo.start()
    return modo


class TestElArrastreDeSalud:
    def test_existe_como_api_publica(self) -> None:
        """Antes no había ni getter ni setter: el campo era inalcanzable."""
        modo = _modo()

        modo.salud_arrastrada = 2.5

        assert modo.salud_arrastrada == pytest.approx(2.5)

    def test_al_caer_un_jefe_se_guarda_la_salud_con_la_curacion(self) -> None:
        modo = _modo()

        modo.acreditar_combate(salud_restante=2.0, medidor=0.5)

        assert modo.salud_arrastrada == pytest.approx(2.0 + CURACION_ENTRE_COMBATES)

    def test_la_curacion_no_pasa_del_maximo(self) -> None:
        modo = _modo()

        modo.acreditar_combate(salud_restante=5.0, medidor=0.0, salud_maxima=5.0)

        assert modo.salud_arrastrada == pytest.approx(5.0)

    def test_arrancar_el_modo_lo_deja_a_cero(self) -> None:
        """Cero significa «no arrastres nada»: el primer jefe va a vida llena."""
        modo = _modo()
        modo.acreditar_combate(salud_restante=1.0, medidor=0.0)

        modo.start()

        assert modo.salud_arrastrada == pytest.approx(0.0)

    def test_el_medidor_tambien_se_arrastra(self) -> None:
        modo = _modo()

        modo.acreditar_combate(salud_restante=3.0, medidor=0.8)

        assert modo.medidor_arrastrado == pytest.approx(0.8)


class TestElMarcador:
    def test_los_golpes_recibidos_cuentan(self) -> None:
        modo = _modo()

        modo.record_hit()
        modo.record_hit()

        assert modo.get_current_stage().hits_taken == 2

    def test_cada_golpe_resta_puntos(self) -> None:
        limpio, golpeado = _modo(1), _modo(1)

        limpio.acreditar_combate(salud_restante=5.0, medidor=0.0)
        golpeado.record_hit()
        golpeado.acreditar_combate(salud_restante=5.0, medidor=0.0)

        assert golpeado.score < limpio.score

    def test_acreditar_avanza_al_siguiente(self) -> None:
        modo = _modo(2)

        modo.acreditar_combate(salud_restante=3.0, medidor=0.0)

        assert modo.get_current_stage().boss_id == "boss1"

    def test_acreditar_el_ultimo_termina_el_modo(self) -> None:
        modo = _modo(1)

        modo.acreditar_combate(salud_restante=3.0, medidor=0.0)

        assert modo.is_complete() is True

    def test_el_tiempo_del_combate_se_acumula(self) -> None:
        modo = _modo()

        modo.registrar_tiempo(0.5)
        modo.registrar_tiempo(0.25)

        assert modo.get_current_stage().time == pytest.approx(0.75)

    def test_tardar_mas_puntua_menos(self) -> None:
        rapido, lento = _modo(1), _modo(1)

        rapido.registrar_tiempo(1.0)
        rapido.acreditar_combate(salud_restante=5.0, medidor=0.0)
        lento.registrar_tiempo(30.0)
        lento.acreditar_combate(salud_restante=5.0, medidor=0.0)

        assert lento.score < rapido.score


class TestQueNadaDeEstoOcurreFueraDelModo:
    """La partida normal no puede notar nada de esto."""

    def test_un_modo_parado_ignora_las_llamadas(self) -> None:
        modo = BossRushMode()

        modo.registrar_tiempo(1.0)
        modo.record_hit()

        assert modo.score == 0
        assert modo.active is False


class TestLaComprobacionQueLoHabriaEvitado:
    """Lo contrario del guardián anterior: ahora alguien **tiene** que conducirlo.

    `TestLoQueElBossRushHaceDeVerdad` fijaba que nadie lo conducía, y decía que
    el día que alguien lo conectara había que actualizar `docs/44` y GAP-030 en
    el mismo cambio. Ese día es hoy, así que la comprobación se invierte.
    """

    def test_el_juego_conduce_el_modo(self) -> None:
        import ast
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent / "src"
        conducen = set()
        for fichero in raiz.rglob("*.py"):
            if fichero.name == "boss_rush_mode.py":
                continue
            arbol = ast.parse(fichero.read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol):
                if (isinstance(nodo, ast.Call)
                        and isinstance(nodo.func, ast.Attribute)
                        and nodo.func.attr in {"acreditar_combate", "record_hit",
                                               "registrar_tiempo"}):
                    conducen.add(fichero.name)
        assert conducen, (
            "nadie conduce el Boss Rush: la puntuación y el arrastre vuelven a "
            "estar muertos, que es exactamente GAP-030"
        )

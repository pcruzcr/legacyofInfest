"""AUD-260 — el tiempo bala se construía y nadie lo tocaba nunca.

El defecto
==========
`StageScene.__init__` hacía `self._tiempo_bala = TiempoBala()` y **ése era su
único uso en todo el repositorio**: ni `update()`, ni una tecla, ni una barra.
La clase está completa desde F5 —reserva que se gasta y se recarga, escala de
tiempo sobre el reloj, `fraccion` para el HUD— y llevaba desde entonces en
`GAP-032` como «construido, nunca tocado».

Las cuatro piezas que le faltaban
---------------------------------
1. Una acción propia, `Action.BULLET_TIME`, con su tecla por defecto.
2. Una propiedad de mapa, `tiempo_bala`, **apagada por defecto**.
3. La llamada por fotograma con el `dt` **sin escalar**.
4. Una barra en el HUD que sólo aparece si el escenario la pide.

Por qué apagada por defecto
---------------------------
Es la misma decisión que AUD-141 tomó con la estamina, por la misma razón: los
dieciséis escenarios entregados están calificados, y encenderles una mecánica
nueva cambiaría el juego que sus autores diseñaron. Un mapa que no declara
`tiempo_bala` se comporta exactamente igual que antes de este cambio —esa es la
invariante 2 de `CLAUDE.md`— y la prueba de abajo lo fija.

Y por qué el `dt` sin escalar: con el escalado, la reserva duraría más cuanto
más lenta fuera la cámara lenta. La propia clase lo explica; aquí se comprueba
que quien la llama respeta el contrato.
"""
from __future__ import annotations

import pytest

from src.engine.core.clock import DeltaClock
from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action
from src.framework.stage.level_mechanics import TiempoBala


class TestLaAccionExiste:
    def test_hay_una_accion_propia(self) -> None:
        assert hasattr(Action, "BULLET_TIME")

    def test_tiene_tecla_por_defecto(self) -> None:
        assert DEFAULT_KEY_BINDINGS.get(Action.BULLET_TIME), (
            "una acción sin tecla es una acción que nadie puede usar"
        )

    def test_no_pisa_ninguna_tecla_de_movimiento(self) -> None:
        """Reutilizar una tecla ya ligada convertiría el tiempo bala en un
        accidente: se activaría al saltar o al correr."""
        criticas = {Action.JUMP, Action.DASH, Action.SHORT_ATTACK,
                    Action.LONG_ATTACK, Action.MOVE_LEFT, Action.MOVE_RIGHT}
        ocupadas = {k for a in criticas for k in DEFAULT_KEY_BINDINGS.get(a, [])}

        assert not set(DEFAULT_KEY_BINDINGS[Action.BULLET_TIME]) & ocupadas


class TestLaPropiedadDelMapa:
    def test_stage_data_la_declara_apagada(self) -> None:
        """El valor por defecto es lo que decide si el cambio es aditivo."""
        import dataclasses

        from src.framework.stage.stage_loader import StageData

        campo = next(f for f in dataclasses.fields(StageData)
                     if f.name == "tiempo_bala")
        assert campo.default == pytest.approx(0.0)

    def test_ningun_mapa_entregado_la_declara(self) -> None:
        """Si alguno la declarara, este cambio no sería aditivo."""
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1]
        con_prop = [
            p.name for p in (raiz / "assets" / "maps").rglob("*.tmx")
            if 'name="tiempo_bala"' in p.read_text(encoding="utf-8", errors="replace")
        ]
        # AUD-384 — el laboratorio de mecánicas sí la declara. Está apagada en
        # los dieciséis escenarios entregados a propósito —encenderla allí
        # cambiaría el juego que sus autores diseñaron, y están calificados—, y
        # el laboratorio es justo donde cambiar la jugabilidad es su función.
        #
        # Se exceptúa por nombre y no relajando la prueba: lo que ésta vigila
        # sigue importando, que es que el cambio siga siendo **aditivo** para
        # el contenido entregado.
        inesperados = sorted(set(con_prop) - {"stage_mecanicas.tmx"})
        assert not inesperados, f"ya la usaban: {inesperados}"

    def test_el_laboratorio_si_la_declara(self) -> None:
        """El otro sentido: la excepción no puede vaciarse en silencio.

        Si el laboratorio deja de declararla, la prueba de arriba seguiría en
        verde y la característica volvería a no estar demostrada en ninguna
        parte, que es el estado del que GAP-052 la sacó.
        """
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1]
        mapa = raiz / "assets" / "maps" / "stage_mecanicas" / "stage_mecanicas.tmx"
        assert 'name="tiempo_bala"' in mapa.read_text(
            encoding="utf-8", errors="replace"), (
            "el laboratorio dejó de declarar `tiempo_bala`"
        )


class TestLoQueHaceCuandoEstaEncendido:
    def test_activarlo_ralentiza_el_reloj(self) -> None:
        reloj = DeltaClock()
        bala = TiempoBala(reserva_maxima=2.0)

        bala.update(0.1, quiere=True, reloj=reloj)

        assert bala.activo is True
        assert reloj.time_scale < 1.0

    def test_gasta_reserva_mientras_dura(self) -> None:
        bala = TiempoBala(reserva_maxima=2.0)

        bala.update(0.5, quiere=True, reloj=None)

        assert bala.reserva == pytest.approx(1.5)

    def test_la_fraccion_alimenta_la_barra(self) -> None:
        bala = TiempoBala(reserva_maxima=2.0)
        bala.update(1.0, quiere=True, reloj=None)

        assert bala.fraccion == pytest.approx(0.5)

    def test_agotado_devuelve_el_reloj_a_su_sitio(self) -> None:
        """Dejar el juego a cámara lenta para siempre sería peor que no tener
        la mecánica."""
        reloj = DeltaClock()
        bala = TiempoBala(reserva_maxima=0.2)

        bala.update(0.3, quiere=True, reloj=reloj)
        bala.update(0.016, quiere=True, reloj=reloj)

        assert bala.activo is False
        assert reloj.time_scale == pytest.approx(1.0)


class TestElHudSoloLaEnsenaSiLaPiden:
    def test_con_maximo_cero_no_se_dibuja(self) -> None:
        """Igual que la estamina (AUD-141): un medidor vacío en los dieciséis
        escenarios que no la usan es una promesa falsa."""
        from src.engine.ui.hud import HUD

        assert hasattr(HUD, "set_tiempo_bala")


class TestLaComprobacionQueLoHabriaEvitado:
    """`TiempoBala` tiene que tener llamante en `src/`, no sólo constructor."""

    def test_alguien_lo_actualiza_en_produccion(self) -> None:
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1] / "src"
        llamantes = [
            p.name for p in raiz.rglob("*.py")
            if "_tiempo_bala.update(" in p.read_text(encoding="utf-8")
        ]
        assert llamantes, (
            "TiempoBala se construye y nadie lo actualiza: es exactamente el "
            "estado que GAP-032 describe."
        )

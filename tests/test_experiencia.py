"""
Module: test_experiencia
System: tests
Academic Unit: N/A

AUD-249 — la experiencia que deja cada enemigo y los puntos de habilidad.

La decisión de diseño que estas pruebas fijan es que **el árbol de habilidades
no se compra con monedas**. Las monedas ya tienen su economía completa
(`coins_for`, el botín al morir, la tienda); si además pagaran las habilidades,
habría dos formas de comprar lo mismo y el árbol sería una lista de la compra.

Aquí se comprueba lo que se rompería en silencio: que la tabla de experiencia
no se desincronice de la clasificación que ya existe, que subir de nivel dé
puntos **una sola vez**, y que gastar un punto no haga retroceder de nivel.
"""
from __future__ import annotations

import pytest

from src.engine.core.experience import (
    PUNTOS_POR_NIVEL,
    ExperienceSystem,
    exp_for,
    exp_para_nivel,
    nivel_de,
)


@pytest.fixture(autouse=True)
def _limpio():
    ExperienceSystem._reset_instance()
    yield
    ExperienceSystem._reset_instance()


class TestLoQueDaCadaEnemigo:
    def test_un_jefe_da_mucho_mas_que_un_enemigo_normal(self) -> None:
        assert exp_for("BossVenado_1") > exp_for("EnemyWalker_1") * 5

    def test_la_clasificacion_es_la_misma_que_la_de_monedas(self) -> None:
        """No hay una segunda forma de decir «esto es un jefe».

        `exp_for` y `coins_for` derivan del mismo `_tipo_de`. Si alguien
        añadiera una tabla propia aquí, un enemigo nuevo podría contar como
        jefe para las monedas y como básico para la experiencia.
        """
        from src.engine.core.score_system import _tipo_de, coins_for

        for eid in ("BossVenado_1", "EnemyShooter_2", "EnemyFlying_3", "LaSodaMutante"):
            tipo = _tipo_de(eid)
            iguales = [
                otro for otro in ("BossVenado_1", "EnemyShooter_2", "EnemyFlying_3",
                                  "LaSodaMutante")
                if _tipo_de(otro) == tipo
            ]
            assert len({exp_for(o) for o in iguales}) == 1, eid
            assert len({coins_for(o) for o in iguales}) == 1, eid

    def test_un_enemigo_de_una_entrega_da_poco_pero_nunca_cero(self) -> None:
        """Un nivel hecho sólo con enemigos propios tiene que progresar."""
        for eid in ("LaSodaMutante", "CuadernoVolador", "EstudianteInfectado", ""):
            assert exp_for(eid) > 0, eid


class TestLaCurvaDeNiveles:
    def test_el_primer_nivel_es_gratis(self) -> None:
        assert exp_para_nivel(1) == 0
        assert nivel_de(0) == 1

    def test_cada_nivel_cuesta_mas_que_el_anterior(self) -> None:
        costes = [exp_para_nivel(n + 1) - exp_para_nivel(n) for n in range(1, 12)]
        assert costes == sorted(costes)
        assert len(set(costes)) > 1, "la curva es plana: no es una curva"

    def test_el_nivel_y_la_experiencia_son_coherentes(self) -> None:
        for n in range(1, 15):
            justo = exp_para_nivel(n)
            assert nivel_de(justo) == n
            if n > 1:
                assert nivel_de(justo - 1) == n - 1


class TestLosPuntosDeHabilidad:
    def test_subir_de_nivel_da_un_punto(self) -> None:
        s = ExperienceSystem()
        assert s.puntos == 0
        nuevos = s.grant(exp_para_nivel(2))
        assert nuevos == PUNTOS_POR_NIVEL
        assert s.nivel == 2
        assert s.puntos == PUNTOS_POR_NIVEL

    def test_no_se_conceden_dos_veces_los_mismos_puntos(self) -> None:
        """El fallo clásico: recalcular los puntos desde el nivel en cada
        muerte y regalar uno por golpe una vez alcanzado el nivel."""
        s = ExperienceSystem()
        s.grant(exp_para_nivel(2))
        for _ in range(20):
            s.grant(1)
        assert s.puntos == PUNTOS_POR_NIVEL

    def test_saltarse_varios_niveles_de_golpe_da_todos_los_puntos(self) -> None:
        """Matar a un jefe puede subir dos niveles. No se pierde ninguno."""
        s = ExperienceSystem()
        nuevos = s.grant(exp_para_nivel(4))
        assert s.nivel == 4
        assert nuevos == 3 * PUNTOS_POR_NIVEL
        assert s.puntos == 3 * PUNTOS_POR_NIVEL

    def test_gastar_un_punto_no_baja_de_nivel(self) -> None:
        """Los puntos y el nivel son dos contadores con vidas distintas.

        Derivar los puntos del nivel haría que comprar una habilidad pareciera
        un retroceso, y que el siguiente nivel volviera a regalar el punto ya
        gastado.
        """
        s = ExperienceSystem()
        s.grant(exp_para_nivel(3))
        assert s.nivel == 3 and s.puntos == 2
        assert s.spend(1) is True
        assert s.nivel == 3
        assert s.puntos == 1
        assert s.grant(1) == 0, "gastar no puede reabrir la concesión"

    def test_no_se_gasta_lo_que_no_hay(self) -> None:
        s = ExperienceSystem()
        s.grant(exp_para_nivel(2))
        assert s.spend(5) is False
        assert s.puntos == PUNTOS_POR_NIVEL, "un gasto fallido no toca nada"
        assert s.spend(0) is False

    def test_la_experiencia_negativa_no_hace_nada(self) -> None:
        s = ExperienceSystem()
        assert s.grant(-100) == 0
        assert s.exp == 0


class TestElBusYLaPersistencia:
    def test_matar_un_enemigo_da_su_experiencia(self) -> None:
        from src.engine.core.event_bus import EventBus
        from src.engine.core.events import Events

        bus = EventBus()
        s = ExperienceSystem(bus)
        bus.emit(Events.ENEMY_DIED, entity_id="EnemyWalker_1")
        # `emit` sólo encola: el bus entrega en `dispatch()`, para que un
        # suceso lanzado desde un manejador no se reparta en recursión.
        bus.dispatch()
        assert s.exp == exp_for("EnemyWalker_1")

    def test_el_manejador_sobrevive_al_recolector(self) -> None:
        """El bus guarda las suscripciones débilmente: sin una referencia viva
        el sistema deja de contar sin un solo error."""
        import gc

        from src.engine.core.event_bus import EventBus
        from src.engine.core.events import Events

        bus = EventBus()
        s = ExperienceSystem(bus)
        gc.collect()
        bus.emit(Events.ENEMY_DIED, entity_id="BossVenado_1")
        bus.dispatch()
        assert s.exp > 0, "la suscripción se la llevó el recolector"

    def test_el_progreso_va_y_vuelve_entero(self) -> None:
        s = ExperienceSystem()
        s.grant(exp_para_nivel(4))
        s.spend(2)
        datos = s.to_dict()

        otro = ExperienceSystem()
        otro.from_dict(datos)
        assert (otro.exp, otro.puntos, otro.nivel) == (s.exp, s.puntos, s.nivel)
        assert otro.grant(1) == 0, "al cargar se regalaron puntos ya concedidos"

    def test_un_fichero_roto_no_deja_puntos_negativos(self) -> None:
        s = ExperienceSystem()
        s.from_dict({"exp": "no soy un numero", "puntos": -5})
        assert s.exp >= 0 and s.puntos >= 0

    def test_la_barra_de_progreso_tiene_numeros_usables(self) -> None:
        s = ExperienceSystem()
        s.grant(exp_para_nivel(3) + 10)
        dentro, total = s.progreso_del_nivel()
        assert dentro == 10
        assert total > 0 and dentro < total

"""AUD-358: `WorldSimulation`, la autoridad del ambiente.

Qué se fija aquí
================

Que la simulación **produce** el estado y nadie más lo escribe; que reutiliza
los sistemas que ya existían en vez de duplicarlos; que lo caro no se
recalcula sesenta veces por segundo; y que el diseñador puede romper el
realismo cuando la escena lo pide, sin que el mundo se quede incoherente
después.

La prueba que más importa de este fichero es
`test_la_luz_compuesta_es_la_misma_que_calcula_la_escena_hoy`: es la que
permite conectar la simulación a los dieciséis escenarios existentes sin
cambiar un solo píxel. Si esa se pone roja, conectar el sistema deja de ser
una refactorización y pasa a ser un cambio de diseño.
"""
from __future__ import annotations

import pytest

from src.framework.stage.day_night import luz_a_las
from src.framework.stage.seasons import aplicar_tinte, estacion
from src.framework.vfx.weather_system import WeatherSystem
from src.framework.world.environment import FASES_DEL_DIA, EnvironmentState
from src.framework.world.simulation import CLIMAS, WorldSimulation


class TestElRelojYElCalendario:

    def test_sin_duracion_de_dia_el_mundo_esta_congelado(self) -> None:
        """Un prólogo de tres minutos no gana nada con un ciclo.

        Es la decisión de `RelojDeMundo`, y la simulación la hereda en vez de
        tomar una propia: dos sitios decidiendo cuándo corre el tiempo es
        exactamente el defecto que este módulo cierra.
        """
        mundo = WorldSimulation(hora_inicial=19.0)
        mundo.update(10.0)
        assert mundo.estado().hora == pytest.approx(19.0)

    def test_el_dia_avanza_al_pasar_la_medianoche(self) -> None:
        """El calendario se lleva detectando la vuelta del reloj.

        Un acumulador aparte daría dos relojes que se desincronizan.
        """
        # Día de 24 s: 1 s real = 1 h de juego. Arrancando a las 23:00,
        # dos segundos cruzan la medianoche.
        mundo = WorldSimulation(hora_inicial=23.0, duracion_dia=24.0)
        assert mundo.dia == 0
        mundo.update(2.0)
        assert mundo.dia == 1
        assert mundo.estado().hora == pytest.approx(1.0, abs=0.01)

    def test_dos_vueltas_son_dos_dias(self) -> None:
        mundo = WorldSimulation(hora_inicial=0.0, duracion_dia=24.0)
        for _ in range(48):
            mundo.update(1.0)
        assert mundo.dia == 2


class TestReutilizaLoQueYaHabia:
    """No se reimplementa nada: se compone."""

    def test_la_luz_compuesta_es_la_misma_que_calcula_la_escena_hoy(self) -> None:
        """La cuenta de `stage_parts/ambiente.py::_aplicar_hora`, verbatim.

        Ésta es la prueba que hace conectable el sistema. La escena compone
        `factor_ambiente × factor_luz de la estación` y aplica el tinte de la
        estación sobre el color de la hora; si la simulación diera otro
        número, enchufarla cambiaría la iluminación de los dieciséis
        escenarios y dejaría de ser una refactorización.
        """
        for hora in (0.0, 6.0, 7.5, 12.0, 18.0, 20.5, 23.9):
            for nombre in ("spring", "summer", "autumn", "winter"):
                mundo = WorldSimulation(hora_inicial=hora, estacion=nombre)
                e = mundo.estado()
                luz, est = luz_a_las(hora), estacion(nombre)
                assert e.factor_ambiente == pytest.approx(
                    luz.factor_ambiente * est.factor_luz)
                assert e.color_ambiente == aplicar_tinte(luz.color, est)
                assert e.bloom_extra == pytest.approx(luz.bloom_extra)

    def test_la_tabla_cubre_los_climas_del_motor(self) -> None:
        """Dos tablas que se desincronizan en silencio.

        Si alguien añade un clima a `WeatherSystem` y no aquí, ese clima se
        quedaría sin humedad —o sea, sin física— y nadie se enteraría hasta
        que alguien notara que bajo esa lluvia no se resbala.
        """
        assert set(CLIMAS) == set(WeatherSystem.CLIMATE_PARAMS)

    def test_la_visibilidad_sale_de_la_capa_que_ya_se_pinta(self) -> None:
        """Un solo hecho, una sola fuente.

        La capa gris del clima ES cuánto se deja de ver. Declarar un número
        de visibilidad aparte garantiza que los dos se separen.
        """
        for nombre, params in WeatherSystem.CLIMATE_PARAMS.items():
            esperado = 1.0 - params["overlay_alpha"] / 255.0
            assert CLIMAS[nombre]["visibilidad"] == pytest.approx(
                esperado, abs=0.01), nombre


class TestAstronomia:

    @pytest.mark.parametrize(("hora", "signo"), [
        (12.0, 1), (9.0, 1), (15.0, 1),      # de día, sobre el horizonte
        (0.0, -1), (3.0, -1), (22.0, -1),    # de noche, bajo el horizonte
    ])
    def test_el_sol_esta_donde_toca(self, hora: float, signo: int) -> None:
        altura = WorldSimulation(hora_inicial=hora).estado().altura_solar
        assert (altura > 0) is (signo > 0)

    def test_el_sol_cruza_el_horizonte_a_las_6_y_a_las_18(self) -> None:
        for hora in (6.0, 18.0):
            e = WorldSimulation(hora_inicial=hora).estado()
            assert e.altura_solar == pytest.approx(0.0, abs=1e-9)

    def test_mediodia_es_el_maximo_y_medianoche_el_minimo(self) -> None:
        assert WorldSimulation(hora_inicial=12.0).estado().altura_solar == pytest.approx(1.0)
        assert WorldSimulation(hora_inicial=0.0).estado().altura_solar == pytest.approx(-1.0)

    def test_el_crepusculo_tiene_nombre_propio(self) -> None:
        """No basta con `día`/`noche`: ahí está el color.

        Entre el ocaso y la noche cerrada el cielo pasa por tres bandas, y un
        consumidor que sólo distinga dos casos no puede pintar la diferencia
        entre las 18:20 y las 19:00.
        """
        vistas = {
            WorldSimulation(hora_inicial=h).estado().fase_del_dia
            for h in [x / 4.0 for x in range(0, 96)]
        }
        assert vistas == set(FASES_DEL_DIA), sorted(vistas)

    def test_la_luna_recorre_su_ciclo_sinodico(self) -> None:
        """29,53 días, el periodo real: es material del curso."""
        nueva = WorldSimulation(dia_inicial=0).estado().fase_lunar
        assert nueva == pytest.approx(0.0)
        # A mitad del periodo, llena.
        llena = WorldSimulation(dia_inicial=15).estado().fase_lunar
        assert llena == pytest.approx(0.5, abs=0.02)
        # Un periodo entero después, otra vez nueva.
        vuelta = WorldSimulation(dia_inicial=30).estado().fase_lunar
        assert vuelta < 0.05

    def test_luna_llena_de_noche_ilumina_y_de_dia_no(self) -> None:
        """El derivado del contrato, alimentado por la simulación."""
        noche = WorldSimulation(hora_inicial=0.0, dia_inicial=15).estado()
        dia = WorldSimulation(hora_inicial=12.0, dia_inicial=15).estado()
        assert noche.luz_lunar > 0.9
        assert dia.luz_lunar == 0.0


class TestElMapaConfiguraYLaSimulacionCalcula:

    def test_declarar_tormenta_produce_un_mundo_de_tormenta_entero(self) -> None:
        """Una línea en el TMX, no veinte variables a mano."""
        e = WorldSimulation(clima="storm").estado()
        assert e.precipitacion == 1.0
        assert e.cobertura_nubes == 1.0
        # AUD-374 — por la magnitud, no por el valor: el viento pasó a llevar
        # signo, que es lo que el campo declaraba desde el principio
        # («negativo = hacia la izquierda») y lo que el productor no emitía. Un
        # `> 50` fijaba justo el defecto: una tormenta que jamás sopla a la
        # izquierda.
        assert abs(e.viento) > 50.0
        assert e.visibilidad < 0.8
        assert e.suelo_mojado          # y por tanto se resbala
        assert e.factor_friccion < 1.0

    def test_la_niebla_moja_el_aire_pero_no_el_suelo(self) -> None:
        """La distinción que se pierde si la física mira el nombre del clima.

        La niebla sube la humedad y tapa la vista, pero no llueve: el suelo
        no resbala. Con una lista de «climas que mojan» en cada consumidor,
        esto sería imposible de acertar en los tres a la vez.
        """
        e = WorldSimulation(clima="fog").estado()
        assert e.precipitacion == 0.0
        assert e.visibilidad < 0.75
        assert not e.suelo_mojado
        assert e.factor_friccion == 1.0

    def test_el_cielo_raso_no_toca_nada(self) -> None:
        e = WorldSimulation(clima="clear", hora_inicial=12.0).estado()
        assert e.factor_friccion == 1.0
        assert e.visibilidad == 1.0
        assert e.cobertura_nubes < 0.1

    def test_un_clima_desconocido_no_tumba_el_nivel(self) -> None:
        """Un estudiante escribe `lluvia` en vez de `rain`.

        Tiene que ver su nivel para darse cuenta, no un error de carga —la
        misma decisión que toma `seasons.estacion()`.
        """
        e = WorldSimulation(clima="lluvia").estado()
        assert e.clima == "lluvia"
        assert e.visibilidad == 1.0     # cae al despejado


class TestLaValvulaDelDisenador:
    """`forzar`: el realismo y el diseño no siempre coinciden."""

    def test_forzar_la_luna_llena_no_toca_el_calendario(self) -> None:
        mundo = WorldSimulation(hora_inicial=22.0, dia_inicial=3)
        mundo.forzar(fase_lunar=0.5)
        assert mundo.estado().fase_lunar == 0.5
        assert mundo.dia == 3           # el mundo sigue siendo coherente

    def test_soltar_la_sustitucion_devuelve_lo_calculado(self) -> None:
        mundo = WorldSimulation(hora_inicial=22.0, dia_inicial=3)
        calculado = mundo.estado().fase_lunar
        mundo.forzar(fase_lunar=0.5)
        mundo.forzar(fase_lunar=None)
        assert mundo.estado().fase_lunar == pytest.approx(calculado)

    def test_forzar_la_niebla_de_una_escena_narrativa(self) -> None:
        mundo = WorldSimulation(clima="clear")
        mundo.forzar(visibilidad=0.3, humedad=0.9)
        e = mundo.estado()
        assert e.visibilidad == 0.3
        assert e.suelo_mojado           # los derivados siguen la sustitución

    def test_un_campo_inventado_se_ignora_en_silencio(self) -> None:
        """Una demo de clase no se cae por una propiedad mal escrita."""
        mundo = WorldSimulation()
        mundo.forzar(lluvia_de_ranas=1.0)
        assert isinstance(mundo.estado(), EnvironmentState)

    def test_el_estado_forzado_sigue_siendo_comparable(self) -> None:
        """La reconstrucción no cambia el tipo de ningún campo.

        `dataclasses.asdict` habría convertido la tupla del color en lista y
        dos estados iguales habrían dejado de compararse iguales.
        """
        mundo = WorldSimulation(hora_inicial=8.0)
        limpio = mundo.estado()
        mundo.forzar(hora=8.0)          # sustitución que no cambia nada
        assert mundo.estado() == limpio

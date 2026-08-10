"""AUD-358: `EnvironmentState`, el contrato que convierte el ambiente en dato.

Qué se está fijando aquí
========================

Hoy el ambiente de un escenario lo producen tres sistemas que escriben
**directamente** sobre sus consumidores: `RelojDeMundo` y `Estacion` sobre
`_lighting`/`_post_processing` (en `stage_parts/ambiente.py:237`), y
`WeatherSystem` sobre sus propias partículas y su clave de audio. Nadie puede
*preguntar* por el ambiente, y por eso el ambiente sólo puede ser decoración:
todos los caminos terminan en el renderizador.

`EnvironmentState` es la foto inmutable que rompe eso. Estas pruebas fijan las
cuatro propiedades que lo hacen utilizable como contrato — antes de que exista
`WorldSimulation`, porque un contrato que se escribe después del productor
acaba siendo la forma del productor.

1. **Es un valor.** Inmutable, comparable, construible sin SDL.
2. **`neutro()` es la identidad.** Aplicarlo no cambia nada, que es lo que
   permite conectar el sistema sin tocar un solo escenario.
3. **Lo derivado se deriva una vez.** `suelo_mojado`, `factor_friccion`,
   `es_de_noche` y `luz_lunar` viven aquí y en ningún otro sitio.
4. **Está acotado.** La tormenta más cerrada deja el juego jugable, igual que
   `MIN_AMBIENTE` hizo con la noche cerrada: una simulación realista que
   impide jugar es un defecto, no una decisión artística.
"""
from __future__ import annotations

import dataclasses

import pytest

from src.framework.world import (
    PERDIDA_MAXIMA_DE_FRICCION,
    UMBRAL_SUELO_MOJADO,
    EnvironmentState,
)


class TestEsUnValor:

    def test_es_inmutable(self) -> None:
        """Un consumidor no puede escribir en el ambiente.

        Es la propiedad que impide que vuelvan a existir dos sistemas
        discutiéndose la misma luz, que es el modo de fallo que este módulo
        viene a cerrar.
        """
        estado = EnvironmentState.neutro()
        with pytest.raises(dataclasses.FrozenInstanceError):
            estado.hora = 3.0  # type: ignore[misc]

    def test_dos_estados_iguales_son_iguales(self) -> None:
        """Comparable por valor: una prueba puede afirmar sobre el ambiente."""
        assert EnvironmentState(hora=8.0) == EnvironmentState(hora=8.0)
        assert EnvironmentState(hora=8.0) != EnvironmentState(hora=9.0)

    def test_se_construye_sin_pygame(self) -> None:
        """No hay import de pygame en el módulo: el contrato es dato puro."""
        import src.framework.world.environment as modulo

        fuente = (modulo.__file__ or "")
        assert fuente.endswith("environment.py")
        with open(fuente, encoding="utf-8") as f:
            texto = f.read()
        assert "import pygame" not in texto


class TestNeutroEsLaIdentidad:
    """Lo que permite conectar esto sin cambiar ni un escenario."""

    def test_la_luz_no_se_toca(self) -> None:
        e = EnvironmentState.neutro()
        assert e.factor_ambiente == 1.0
        assert e.color_ambiente == (255, 255, 255)
        assert e.bloom_extra == 0.0

    def test_la_fisica_no_se_toca(self) -> None:
        assert EnvironmentState.neutro().factor_friccion == 1.0

    def test_es_mediodia_despejado(self) -> None:
        e = EnvironmentState.neutro()
        assert e.es_de_noche is False
        assert e.clima == "clear"
        assert e.visibilidad == 1.0


class TestLoDerivadoSeDerivaAqui:

    @pytest.mark.parametrize(("altura", "noche"), [
        (1.0, False), (0.4, False), (0.0, True), (-0.5, True), (-1.0, True),
    ])
    def test_es_de_noche_es_el_sol_bajo_el_horizonte(
            self, altura: float, noche: bool) -> None:
        assert EnvironmentState(altura_solar=altura).es_de_noche is noche

    def test_la_luna_no_ilumina_de_dia(self) -> None:
        """Se ve, pero no aporta nada que el juego deba consultar."""
        llena_de_dia = EnvironmentState(altura_solar=1.0, fase_lunar=0.5)
        assert llena_de_dia.luz_lunar == 0.0

    @pytest.mark.parametrize(("fase", "esperado"), [
        (0.0, 0.0),   # luna nueva: noche cerrada
        (0.5, 1.0),   # llena
        (1.0, 0.0),   # nueva otra vez, el ciclo cierra
        (0.25, 0.5),
    ])
    def test_la_luna_de_noche_da_su_fraccion(
            self, fase: float, esperado: float) -> None:
        e = EnvironmentState(altura_solar=-0.5, fase_lunar=fase)
        assert e.luz_lunar == pytest.approx(esperado)

    def test_el_umbral_de_mojado_es_uno_solo(self) -> None:
        """Un solo número para la física, el audio y el render."""
        assert EnvironmentState(humedad=UMBRAL_SUELO_MOJADO).suelo_mojado
        assert not EnvironmentState(
            humedad=UMBRAL_SUELO_MOJADO - 0.01).suelo_mojado


class TestElAmbienteDejaDeSerDecoracion:
    """El hilo `lluvia → humedad → suelo mojado → fricción → control`.

    Ésta es la tesis entera del sistema, y es lo único de ella que se puede
    comprobar con una prueba: que un cambio en el mundo produce un cambio en
    una **regla del juego**, no en un píxel.
    """

    def test_el_suelo_seco_no_cambia_la_fisica(self) -> None:
        assert EnvironmentState(humedad=0.0).factor_friccion == 1.0
        assert EnvironmentState(humedad=0.3).factor_friccion == 1.0

    def test_mojado_frena_menos(self) -> None:
        seco = EnvironmentState(humedad=0.2).factor_friccion
        mojado = EnvironmentState(humedad=0.8).factor_friccion
        assert mojado < seco

    def test_mas_agua_frena_menos_todavia(self) -> None:
        llovizna = EnvironmentState(humedad=0.65).factor_friccion
        tormenta = EnvironmentState(humedad=1.0).factor_friccion
        assert tormenta < llovizna

    def test_la_tormenta_mas_cerrada_sigue_siendo_jugable(self) -> None:
        """El acotado, que es la decisión de diseño, no el efecto.

        Misma razón que `MIN_AMBIENTE` con la noche: un suelo que quita el
        80 % del frenado se lee como un control roto, no como lluvia.
        """
        peor = EnvironmentState(humedad=1.0).factor_friccion
        assert peor == pytest.approx(1.0 - PERDIDA_MAXIMA_DE_FRICCION)
        assert peor >= 0.5

    def test_la_fisica_pregunta_por_humedad_y_no_por_el_nombre_del_clima(self) -> None:
        """Un consumidor no mantiene su propia lista de «cuáles mojan».

        Si `factor_friccion` mirara `clima`, cada sistema tendría que saber
        que `rain`, `storm` y `fog` mojan y `snow` a medias. Con humedad, el
        que decide es quien simula, y sólo hay una lista.
        """
        con_nombre_raro = EnvironmentState(clima="lluvia_de_ceniza", humedad=0.9)
        assert con_nombre_raro.suelo_mojado
        assert con_nombre_raro.factor_friccion < 1.0

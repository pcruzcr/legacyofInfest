"""AUD-270 — una tormenta sin un solo relámpago.

El defecto
==========
`WeatherSystem` tiene cinco climas y el de `storm` era **lluvia con viento**:
cien partículas inclinadas y un velo gris. Medido con
`grep -in "rayo\\|relampago\\|lightning" src/framework/vfx/weather_system.py`:
cero resultados.

Una tormenta que no relampaguea no se lee como tormenta — se lee como lluvia
fuerte. Y es justo el clima del clímax de `stage0`, la zona F, donde el
escenario cambia a `storm` para decirle al jugador que algo ha cambiado.

Cómo se implementa, y por qué así
---------------------------------
El destello **no es una partícula**: es un fogonazo a pantalla completa, breve
y desigual, más un retumbar que llega después. Se hace en el propio sistema de
clima y no en el post-procesado porque el post-procesado no sabe qué tiempo
hace, y pasarle esa información sólo para esto acoplaría dos sistemas que hoy
no se conocen.

Los intervalos son aleatorios dentro de un rango declarado: un rayo cada N
segundos exactos deja de dar miedo a la tercera vez.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.vfx.weather_system import WeatherSystem


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _avanzar(w: WeatherSystem, segundos: float, paso: float = 1 / 60) -> None:
    for _ in range(int(segundos / paso)):
        w.update(paso, pygame.Vector2(0, 0))


class TestSoloLaTormentaRelampaguea:
    def test_la_tormenta_acaba_relampagueando(self) -> None:
        w = WeatherSystem(climate="storm")

        _avanzar(w, 30.0)

        assert w.relampagos_contados > 0, (
            "treinta segundos de tormenta sin un solo rayo"
        )

    @pytest.mark.parametrize("clima", ["clear", "rain", "snow", "fog"])
    def test_los_demas_climas_no(self, clima: str) -> None:
        w = WeatherSystem(climate=clima)

        _avanzar(w, 30.0)

        assert w.relampagos_contados == 0, f"«{clima}» no debería relampaguear"


class TestElDestelloSeVe:
    def test_durante_el_destello_la_pantalla_se_aclara(self) -> None:
        w = WeatherSystem(climate="storm")
        w.forzar_relampago()

        sin = pygame.Surface((800, 600))
        sin.fill((10, 10, 20))
        con = sin.copy()
        w.draw(con, pygame.Vector2(0, 0))

        assert con.get_at((400, 300)) != sin.get_at((400, 300)), (
            "el relámpago no cambia un solo píxel"
        )

    def test_el_destello_se_apaga_solo(self) -> None:
        w = WeatherSystem(climate="storm")
        w.forzar_relampago()

        _avanzar(w, 3.0)

        assert w.brillo_del_relampago == pytest.approx(0.0), (
            "el fogonazo se queda encendido: la pantalla no vuelve nunca"
        )

    def test_no_relampaguea_dos_veces_seguidas_sin_pausa(self) -> None:
        """Un rayo por fotograma sería un estroboscopio, no una tormenta."""
        w = WeatherSystem(climate="storm")
        w.forzar_relampago()
        antes = w.relampagos_contados

        _avanzar(w, 0.5)

        assert w.relampagos_contados == antes


class TestNoRompeNada:
    def test_cambiar_de_clima_apaga_el_destello(self) -> None:
        w = WeatherSystem(climate="storm")
        w.forzar_relampago()

        w.set_climate("clear")

        assert w.brillo_del_relampago == pytest.approx(0.0)

    def test_dibujar_sin_tormenta_no_lanza(self) -> None:
        superficie = pygame.Surface((800, 600))
        for clima in ("clear", "rain", "snow", "fog", "storm"):
            w = WeatherSystem(climate=clima)
            _avanzar(w, 1.0)
            w.draw(superficie, pygame.Vector2(0, 0))


class TestElDestelloNoCompraSuperficies:
    def test_el_fogonazo_no_reasigna_pantalla_en_cada_fotograma(self, monkeypatch) -> None:
        """AUD-410 — cada fotograma de destello compraba una `Surface` nueva.

        El velo de la tormenta (AUD-270) se cachea porque rellenar 800×600 con
        alfa costaba 1,79 ms; el fogonazo del mismo rayo, que también es un
        relleno de pantalla completa con alfa que decae, asignaba 800×600×4
        bytes **en cada `draw`** mientras duraba el brillo. La primera pasada
        puede comprar la caché; las siguientes tienen que reutilizarla.
        """
        w = WeatherSystem(climate="storm")
        w.forzar_relampago()
        superficie = pygame.Surface((800, 600))
        w.draw(superficie, pygame.Vector2(0, 0))  # calienta la caché

        real = pygame.Surface
        creadas = 0

        def _contadas(*args, **kwargs):
            nonlocal creadas
            creadas += 1
            return real(*args, **kwargs)

        monkeypatch.setattr(pygame, "Surface", _contadas)

        w.draw(superficie, pygame.Vector2(0, 0))
        w.draw(superficie, pygame.Vector2(0, 0))

        assert creadas == 0, (
            f"el destello creó {creadas} superficies nuevas tras la primera "
            "pasada: churn de memoria por fotograma durante el rayo"
        )

"""AUD-500 — el sonido de la lluvia se quedaba pegado.

Reportado jugando: *«el sonido de la lluvia genera un bug y queda pegado»*.

El defecto
==========
El bloque que cablea el ambiente al clima (`StageScene._cambiar_clima`)
**sólo sabe arrancar**::

    ruta_relativa = self._weather.get_ambient_audio_key()
    if ruta_relativa and self.context.audio is not None:
        ...arranca o funde...

Y `WeatherSystem.AMBIENTES` dice `"clear": None`. Así que cambiar de `rain`
a `clear` no entra en el `if`, no para nada, y la lluvia sigue sonando —
sobre un cielo despejado, y hasta que algo la pare por otro motivo.

No es un caso raro: el 4-1 pasa por `rain → storm → rain → clear`, y
cualquier escenario que despeje el cielo lo dispara.

El segundo defecto, en el mismo camino
======================================
`AudioManager.crossfade_ambient` manda apagar el canal viejo **antes** de
saber si hay canal libre para el nuevo::

    if old_channel is not None:
        old_channel.fadeout(...)
    new_channel = pygame.mixer.find_channel()
    if new_channel is not None:
        ...

Si `find_channel()` devuelve `None` —todos ocupados—, el ambiente muere
pero `_ambient_active` se queda en `True` y `_ambient_channel` sigue
apuntando al canal que se está apagando. El estado y la realidad se
separan, y quien pregunte `_ambient_active` para decidir si parar —lo hace
`StageScene`, y también el silencio de la Fase 4 del 4-1— decide con un
dato falso.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings


class _AudioEspia:
    """Anota qué se le pidió al canal de ambiente."""

    def __init__(self) -> None:
        self.arrancados: list[str] = []
        self.fundidos: list[str] = []
        self.paradas: int = 0
        self.ecos: list[bool] = []
        self._ambient_active: bool = False

    def activar_eco(self, activo: bool) -> None:
        # AUD-594 — el bus de reverberación de la Fase 6 pasa por aquí.
        self.ecos.append(bool(activo))

    def play_ambient(self, path, volume: float = 0.5, loops: int = -1) -> None:
        self.arrancados.append(str(path))
        self._ambient_active = True

    def crossfade_ambient(self, path, duration: float = 2.0,
                          volume: float = 0.5) -> None:
        self.fundidos.append(str(path))
        self._ambient_active = True

    def stop_ambient(self) -> None:
        self.paradas += 1
        self._ambient_active = False

    # Lo que el resto del ciclo de vida de la escena le pide y aquí no se
    # mide; sin ellos, `on_exit` reventaría y la prueba mediría eso.
    def stop_music(self) -> None:
        pass

    def play_music(self, *a, **k) -> None:
        pass

    def play_sfx(self, *a, **k) -> None:
        pass

    def update(self, *a, **k) -> None:
        pass


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))


class TestUnCieloDespejadoNoSuenaALluvia:
    """El síntoma, tal cual se reportó."""

    def _escena(self, _video):
        from tests.ayudantes_stage4_1 import construir_escena

        return construir_escena()

    def test_cambiar_a_despejado_para_el_ambiente(self, _video, monkeypatch) -> None:
        escena = self._escena(_video)
        try:
            espia = _AudioEspia()
            # `GameContext.audio` es una propiedad de sólo lectura: se
            # sustituye el gestor de debajo, que es de donde lee.
            monkeypatch.setattr(escena.context, "audio_manager", espia,
                                raising=False)

            escena._cambiar_clima("rain")
            assert espia.arrancados or espia.fundidos, (
                "la lluvia ni siquiera arrancó: la prueba mediría otra cosa"
            )
            paradas_antes = espia.paradas

            escena._cambiar_clima("clear")
            assert espia.paradas > paradas_antes, (
                "el cielo se despejó y la lluvia siguió sonando"
            )
        finally:
            escena.on_exit()

    def test_un_clima_con_sonido_no_se_para_de_mas(self, _video, monkeypatch) -> None:
        """El arreglo no puede ser «parar siempre»: pasar de lluvia a
        tormenta tiene que fundir, no cortar y arrancar."""
        escena = self._escena(_video)
        try:
            espia = _AudioEspia()
            # `GameContext.audio` es una propiedad de sólo lectura: se
            # sustituye el gestor de debajo, que es de donde lee.
            monkeypatch.setattr(escena.context, "audio_manager", espia,
                                raising=False)

            escena._cambiar_clima("rain")
            paradas = espia.paradas
            escena._cambiar_clima("storm")
            assert espia.paradas == paradas, (
                "cortó el ambiente en seco en vez de fundir al siguiente"
            )
            assert espia.fundidos, "no hubo fundido entre dos climas con sonido"
        finally:
            escena.on_exit()


class TestElClimaDeclaraSuSilencio:
    def test_despejado_no_tiene_ambiente(self) -> None:
        """La premisa del defecto, fijada para que no se mueva sin querer."""
        from src.framework.vfx.weather_system import WeatherSystem

        assert WeatherSystem.AMBIENTES["clear"] is None

    def test_lluvia_y_tormenta_si_lo_tienen(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem

        assert WeatherSystem.AMBIENTES["rain"]
        assert WeatherSystem.AMBIENTES["storm"]


class TestElEstadoDelAmbienteNoMiente:
    """`_ambient_active` lo consultan varios sitios para decidir si parar o
    fundir. Si miente, deciden mal."""

    def _gestor(self, _video):
        from src.engine.audio.audio_manager import AudioManager

        return AudioManager()

    def test_sin_canal_libre_no_se_queda_activo(self, _video, monkeypatch) -> None:
        gestor = self._gestor(_video)
        ruta = settings.ASSETS_DIR / "sfx/environment/sfx_environment_rain_ambient.wav"
        if not ruta.exists():
            pytest.skip(f"falta {ruta}")

        gestor.play_ambient(ruta, volume=0.3)
        # Todos los canales ocupados: es lo que pasa en un combate con
        # varios emisores, que es justo cuando cambia el clima.
        monkeypatch.setattr(pygame.mixer, "find_channel", lambda *a, **k: None)
        gestor.crossfade_ambient(ruta, duration=0.5, volume=0.3)

        assert gestor._ambient_active is False, (
            "dice que hay ambiente sonando y el canal se está apagando: "
            "quien pregunte para decidir si parar, decidirá mal"
        )
        assert gestor._ambient_channel is None, (
            "sigue apuntando al canal viejo, que ya se mandó apagar"
        )

    def test_con_canal_libre_si_queda_activo(self, _video) -> None:
        """Sin esto, «poner siempre False» pasaría la prueba de arriba."""
        gestor = self._gestor(_video)
        ruta = settings.ASSETS_DIR / "sfx/environment/sfx_environment_rain_ambient.wav"
        if not ruta.exists():
            pytest.skip(f"falta {ruta}")
        gestor.play_ambient(ruta, volume=0.3)
        gestor.crossfade_ambient(ruta, duration=0.5, volume=0.3)
        assert gestor._ambient_active is True

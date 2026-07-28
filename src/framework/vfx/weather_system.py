from __future__ import annotations

import math
import random

import pygame

from src.engine.core import settings
from src.framework.vfx.particle_system import ParticleEmitter


class WeatherSystem:
    """Stage weather effects (rain, snow, fog, storm) driven by TMX climate property."""

    CLIMATE_PARAMS: dict[str, dict] = {
        "clear":  {"particles": 0,  "overlay_alpha": 0,   "overlay_color": (0, 0, 0)},
        "rain":   {"particles": 60, "overlay_alpha": 30,  "overlay_color": (60, 70, 90)},
        "snow":   {"particles": 40, "overlay_alpha": 50,  "overlay_color": (200, 210, 220)},
        "fog":    {"particles": 0,  "overlay_alpha": 80,  "overlay_color": (180, 180, 190)},
        "storm":  {"particles": 100,"overlay_alpha": 60,  "overlay_color": (40, 40, 50)},
    }

    def __init__(self, climate: str = "clear") -> None:
        self._emitter = ParticleEmitter()
        self._timer: float = 0.0
        self._climate: str = climate
        self._overlay = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA
        )
        self._wind: float = 0.0
        #: La capa de color sólo se repinta cuando cambia el clima.
        self._overlay_listo: bool = False
        self._set_climate_params()

    def _set_climate_params(self) -> None:
        params = self.CLIMATE_PARAMS.get(self._climate, self.CLIMATE_PARAMS["clear"])
        self._particle_rate: float = float(params["particles"])
        self._overlay_alpha: int = params["overlay_alpha"]
        self._overlay_color: tuple[int, int, int] = params["overlay_color"]
        self._overlay_listo = False
        # Viento lateral en px/s. Los valores de la tormenta son los que
        # pretendía la línea muerta que se corrigió en `_angulo_con_viento`:
        # ±50 a 100, que sobre una caída de 280 px/s da entre 10 y 20 grados de
        # inclinación. El ±30 anterior daba como máximo 6 grados, indistinguible
        # de la vertical. La nieve deriva menos porque cae mucho más despacio y
        # el mismo viento la desvía más.
        self._wind = {
            "storm": random.choice([-1, 1]) * random.uniform(50, 100),
            "snow": random.uniform(-12, 12),
            "rain": random.uniform(-15, 15),
        }.get(self._climate, 0.0)

    def set_climate(self, climate: str) -> None:
        if climate == self._climate:
            return
        self._climate = climate
        self._emitter.clear()
        self._set_climate_params()

    @property
    def climate(self) -> str:
        return self._climate

    @property
    def _particles(self) -> list:  # backward compat for tests
        return []

    def update(self, dt: float, camera_offset: pygame.Vector2) -> None:
        self._timer += dt
        if self._particle_rate > 0:
            spawn_interval = 1.0 / self._particle_rate
            max_spawn = max(1, int(self._particle_rate * dt))
            spawned = 0
            while self._timer >= spawn_interval and spawned < max_spawn:
                self._timer -= spawn_interval
                self._spawn_particle(camera_offset)
                spawned += 1

        self._emitter.update(dt)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        self._emitter.draw(surface, camera_offset)

        if self._overlay_alpha > 0:
            # F1.3: antes esto hacía `fill` en cada fotograma para pintar
            # siempre el mismo color. Un `fill` sobre 800x600 con alfa cuesta
            # más que el `blit` que viene después; medido, la capa de clima
            # costaba 1,79 ms por fotograma en la arena del jefe, casi todo en
            # rellenar de nuevo una superficie que ya estaba bien.
            if not self._overlay_listo:
                self._overlay.fill((*self._overlay_color, self._overlay_alpha))
                self._overlay_listo = True
            surface.blit(self._overlay, (0, 0))

    def clear(self) -> None:
        self._emitter.clear()

    def _spawn_particle(self, camera_offset: pygame.Vector2) -> None:
        sx = camera_offset.x + random.uniform(-20, settings.INTERNAL_WIDTH + 20)
        sy = camera_offset.y - 10
        color = self._get_particle_color()

        if self._climate == "rain":
            self._emitter.emit_directed(
                sx, sy, angle=self._angulo_con_viento(), speed=280,
                count=1, lifetime=random.uniform(*self._VIDA_LLUVIA),
                size=(1, 2), color=color, spread=5,
                gravity=980, friction=0.99,
            )
        elif self._climate == "snow":
            self._emitter.emit_directed(
                sx, sy, angle=self._angulo_con_viento(), speed=random.uniform(30, 60),
                count=1, lifetime=random.uniform(2.0, 4.0),
                size=(2, 4), color=color, spread=20,
                gravity=50, friction=0.95,
            )
        elif self._climate == "storm":
            self._emitter.emit_directed(
                sx, sy, angle=self._angulo_con_viento(), speed=280,
                count=1, lifetime=random.uniform(*self._VIDA_LLUVIA),
                size=(1, 3), color=color, spread=10,
                gravity=980, friction=0.99,
            )

    #: Cuánto vive una gota, en segundos.
    #:
    #: F1.3 — antes era 0,3 a 0,6 s. Con velocidad inicial de 280 px/s y
    #: gravedad de 980, una gota recorre unos 344 px en 0,6 s, sobre una
    #: pantalla de 600 px de alto. Medido: las gotas existían entre y = -6 y
    #: y = 239, es decir, **la lluvia se evaporaba antes de llegar a la mitad
    #: de la pantalla**. Cruzarla entera requiere 0,87 s.
    _VIDA_LLUVIA = (0.95, 1.25)

    def _angulo_con_viento(self) -> float:
        """Dirección de caída, inclinada por el viento. 90 grados es vertical.

        F1.3 — el viento de la tormenta no existía. La línea que lo calculaba
        era::

            random.choice([-1, 1]) * random.uniform(50, 100)

        Un valor calculado y **asignado a nada**: una sentencia sin efecto.
        `_set_climate_params` sí rellenaba `self._wind`, pero nadie lo leía, así
        que la tormenta caía tan recta como la lluvia mansa. Ruff no lo detecta
        porque la expresión contiene llamadas, y una llamada podría tener
        efectos colaterales.
        """
        if not self._wind:
            return 90.0
        # atan2(viento, velocidad de caída) da la inclinación respecto a la
        # vertical; se resta porque 90 grados es hacia abajo.
        return 90.0 - math.degrees(math.atan2(self._wind, 280.0))

    def _get_particle_color(self) -> tuple[int, int, int]:
        if self._climate == "rain":
            return (150, 170, 200)
        elif self._climate == "snow":
            return (230, 235, 240)
        elif self._climate == "storm":
            return (120, 130, 150)
        return (200, 200, 200)

    def get_ambient_audio_key(self) -> str | None:
        audio_map: dict[str, str | None] = {
            "clear": None,
            "rain": "rain",
            "snow": "wind",
            "fog": "wind",
            "storm": "storm",
        }
        return audio_map.get(self._climate)

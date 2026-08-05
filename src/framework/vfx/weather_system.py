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
        # AUD-270 — los relámpagos. Una tormenta que no relampaguea se lee como
        # lluvia fuerte, y `storm` es justamente el clima del clímax de stage0.
        self._brillo_rayo: float = 0.0
        self._proximo_rayo: float = self._espera_hasta_el_proximo_rayo()
        self._relampagos: int = 0
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
        # AUD-270: salir de la tormenta apaga el fogonazo en curso. Sin esto,
        # cambiar de clima a mitad de destello deja la pantalla aclarada para
        # siempre, porque el decaimiento sólo corre con `storm` activo.
        self._brillo_rayo = 0.0
        self._proximo_rayo = self._espera_hasta_el_proximo_rayo()
        self._set_climate_params()

    # ── relámpagos (AUD-270) ───────────────────────────────────

    #: Rango de espera entre rayos, en segundos. Aleatorio dentro del rango a
    #: propósito: un rayo cada N segundos exactos deja de dar miedo a la
    #: tercera vez, porque el jugador lo empieza a contar.
    ESPERA_ENTRE_RAYOS: tuple[float, float] = (4.0, 11.0)
    #: Cuánto tarda el fogonazo en apagarse, en segundos. Corto: un relámpago
    #: que dura se lee como un error de render, no como un rayo.
    DURACION_DESTELLO: float = 0.35
    #: Alfa máximo del fogonazo. 110 sobre 255 aclara la escena entera sin
    #: cegar — el jugador tiene que seguir viendo dónde pisa.
    ALFA_DESTELLO: int = 110

    @staticmethod
    def _espera_hasta_el_proximo_rayo() -> float:
        return random.uniform(*WeatherSystem.ESPERA_ENTRE_RAYOS)

    def forzar_relampago(self) -> None:
        """Dispara un rayo ahora. Para las cinemáticas y para las pruebas."""
        self._brillo_rayo = 1.0
        self._relampagos += 1
        self._proximo_rayo = self._espera_hasta_el_proximo_rayo()

    @property
    def brillo_del_relampago(self) -> float:
        """0 a 1. Lo lee el dibujado, y las pruebas para ver que se apaga."""
        return self._brillo_rayo

    @property
    def relampagos_contados(self) -> int:
        return self._relampagos

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

        # AUD-270 — el ciclo del rayo: esperar, fogonazo, apagarse.
        if self._climate == "storm":
            self._proximo_rayo -= dt
            if self._proximo_rayo <= 0.0:
                self.forzar_relampago()
        if self._brillo_rayo > 0.0:
            self._brillo_rayo = max(
                0.0, self._brillo_rayo - dt / self.DURACION_DESTELLO)

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

        # AUD-270 — el fogonazo va **encima** del velo de la tormenta: un rayo
        # que se dibujara debajo quedaría teñido de gris y no se vería.
        if self._brillo_rayo > 0.0:
            destello = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            destello.fill((255, 253, 240,
                           int(self.ALFA_DESTELLO * self._brillo_rayo)))
            surface.blit(destello, (0, 0))

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

    #: AUD-145 — clima → fichero REAL, con su ruta completa desde `assets/`.
    #:
    #: Antes esto devolvía «rain», «wind» o «storm» y la escena buscaba
    #: `assets/sfx/ambient/<clave>.wav`. **Esa carpeta no existe.** Los siete
    #: ambientes del proyecto viven en `assets/sfx/environment/` con otros
    #: nombres, así que el `.exists()` de la escena daba falso siempre y el
    #: clima sonaba en silencio sin que nadie se enterara.
    #:
    #: Es el mismo patrón que AUD-127 y AUD-136: una comprobación defensiva
    #: —`if ruta.exists()`— convirtiendo un fallo de integración en silencio.
    #:
    #: `None` significa dos cosas distintas y las dos importan:
    #: en `clear`, que no debe sonar nada; en `rain` y `storm`, que **no hay
    #: fichero todavía**. Lo segundo se avisa; lo primero no.
    AMBIENTES: dict[str, str | None] = {
        "clear": None,
        # AUD-271 — `rain` y `storm` tienen ya su propio ambiente. Hasta aquí
        # eran los dos climas que AUD-145 dejó declarando su carencia en voz
        # alta, que era lo correcto mientras no existieran; ahora se generan
        # por el mismo camino que el resto del audio del proyecto.
        "rain": "sfx/environment/sfx_environment_rain_ambient.wav",
        "snow": "sfx/environment/sfx_environment_wind_indoor.wav",
        "fog": "sfx/environment/sfx_environment_wind_indoor.wav",
        "storm": "sfx/environment/sfx_environment_storm_ambient.wav",
    }

    #: Climas que deberían sonar y no tienen fichero. Se distinguen de `clear`
    #: para poder avisar de la carencia sin avisar del silencio buscado.
    #:
    #: Vacío desde AUD-271. Se deja declarado porque el hueco que vigila es
    #: real: el día que alguien añada un clima nuevo, volverá a hacer falta.
    SIN_ASSET: frozenset[str] = frozenset()

    def get_ambient_audio_key(self) -> str | None:
        """Ruta relativa a `assets/` del ambiente de este clima, o `None`.

        Se mantiene el nombre por compatibilidad con las entregas que ya lo
        llaman; lo que cambia es que ahora devuelve algo que existe.
        """
        return self.AMBIENTES.get(self._climate)

    def falta_su_ambiente(self) -> bool:
        """`True` si este clima debería sonar y no hay fichero para él."""
        return self._climate in self.SIN_ASSET

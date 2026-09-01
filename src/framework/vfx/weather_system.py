from __future__ import annotations

import math
import random

import pygame

from src.engine.core import settings
from src.engine.core.azar import generador
from src.framework.vfx.particle_system import ParticleEmitter
from src.framework.world.simulation import viento_de


class WeatherSystem:
    """Stage weather effects (rain, snow, fog, storm) — HD nativo sin pixelado."""

    # HD nativo 1920×1080: densidad 2.5× vs 800×600. Lluvia real son vetas largas con splash, no puntos.
    CLIMATE_PARAMS: dict[str, dict] = {
        "clear":  {"particles": 0,   "overlay_alpha": 0,   "overlay_color": (0, 0, 0)},
        "rain":   {"particles": 150, "overlay_alpha": 18,  "overlay_color": (55, 65, 85)},
        "snow":   {"particles": 90,  "overlay_alpha": 35,  "overlay_color": (210, 220, 230)},
        "fog":    {"particles": 0,   "overlay_alpha": 70,  "overlay_color": (185, 185, 195)},
        "storm":  {"particles": 220, "overlay_alpha": 45,  "overlay_color": (35, 35, 45)},
    }

    def __init__(self, climate: str = "clear",
                 rng: random.Random | None = None) -> None:
        #: AUD-398 — azar propio (GAP-042). Ver `Camera.__init__` para el
        #: porqué: reproducible igual, pero sin competir por el estado
        #: global con los otros catorce módulos que tiran de `random`.
        self._rng = rng if rng is not None else generador()
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
        # AUD-410 — el fogonazo del rayo con la misma disciplina que el velo
        # de arriba: una superficie que se rellena, no una compra por
        # fotograma. AUD-270 lo dejó asignando `pygame.Surface` de pantalla
        # completa en cada `draw` mientras el brillo decaía — ~1,9 MB por
        # fotograma durante un rayo, en el presupuesto de 16,67 ms. La caché
        # es perezosa y al tamaño real del destino, y `_destello_alfa` evita
        # hasta el `fill` si el brillo no ha cambiado.
        self._destello: pygame.Surface | None = None
        self._destello_alfa: int = -1
        self._indoor_factor: float = 0.0  # 0 outdoor, 1 indoor — ver set_indoor_factor
        self._set_climate_params()

    def _set_climate_params(self) -> None:
        params = self.CLIMATE_PARAMS.get(self._climate, self.CLIMATE_PARAMS["clear"])
        self._particle_rate: float = float(params["particles"])
        self._overlay_alpha: int = params["overlay_alpha"]
        self._overlay_color: tuple[int, int, int] = params["overlay_color"]
        self._overlay_listo = False
        # AUD-374 — el viento ya no se inventa aquí. Era la segunda tabla del
        # mismo hecho: `CLIMAS` en `world/simulation.py` tenía las magnitudes
        # (75 en tormenta, 15 en lluvia, 12 en nieve) y esto sorteaba las
        # suyas con `random.uniform` (±50 a 100, ±15, ±12). Los números
        # coincidían porque uno se copió del otro, y copiado es como se
        # desincroniza: cambiar la tormenta en la tabla del mundo no movía la
        # inclinación de una sola gota.
        #
        # Este repliegue es para quien construye un `WeatherSystem` suelto —una
        # prueba, `stage0`, una entrega—: sigue soplando, y sopla lo que dice
        # la única tabla que queda. Cuando hay escenario, `_aplicar_hora` le
        # pasa el viento del `EnvironmentState` y ése manda.
        self._wind = viento_de(self._climate, self._rng)

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

    # AUD-398 — era `@staticmethod` y ya no puede serlo: la espera sale del
    # generador de **esta** tormenta, no del azar global (GAP-042).
    def _espera_hasta_el_proximo_rayo(self) -> float:
        return self._rng.uniform(*WeatherSystem.ESPERA_ENTRE_RAYOS)

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

    def aplicar_viento(self, viento: float) -> None:
        """Toma el viento del ambiente — AUD-374.

        La entrada que faltaba. `EnvironmentState.viento` se calculaba cada
        fotograma y no había forma de dárselo a quien dibuja la lluvia, así
        que el campo estaba huérfano y este sistema soplaba por su cuenta.

        Con signo: negativo inclina la lluvia hacia la izquierda.
        """
        self._wind = float(viento)

    @property
    def _particles(self) -> list:  # backward compat for tests
        return []

    def update(self, dt: float, camera_offset: pygame.Vector2) -> None:
        self._timer += dt
        # Indoor/outdoor: si está 100% indoor, no llueve (techo). Si 50% indoor (umbral puerta), mitad.
        eff_rate = self._particle_rate * (1.0 - self._indoor_factor)
        if eff_rate > 0:
            spawn_interval = 1.0 / eff_rate
            max_spawn = max(1, int(eff_rate * dt))
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
        # AUD-410 — la superficie es una caché rellenable (ver `__init__`):
        # antes se compraba una nueva en cada fotograma con brillo.
        if self._brillo_rayo > 0.0:
            if (
                self._destello is None
                or self._destello.get_size() != surface.get_size()
            ):
                self._destello = pygame.Surface(
                    surface.get_size(), pygame.SRCALPHA)
                self._destello_alfa = -1
            alfa = int(self.ALFA_DESTELLO * self._brillo_rayo)
            if alfa != self._destello_alfa:
                self._destello.fill((255, 253, 240, alfa))
                self._destello_alfa = alfa
            surface.blit(self._destello, (0, 0))

    def clear(self) -> None:
        self._emitter.clear()

    def _spawn_particle(self, camera_offset: pygame.Vector2) -> None:
        # HD nativo: lluvia son vetas 2×12 con cola alfa, no puntos 1×2. Polvo son nubes suaves.
        sx = camera_offset.x + self._rng.uniform(-40, settings.INTERNAL_WIDTH + 40)
        sy = camera_offset.y - 20
        color = self._get_particle_color()

        if self._climate == "rain":
            # Veta larga 2×14, gravedad alta, fricción 1.0 para caída recta, con viento real
            self._emitter.emit_directed(
                sx, sy, angle=self._angulo_con_viento(), speed=520,
                count=2, lifetime=self._rng.uniform(0.85, 1.1),
                size=(2, 14), color=color, spread=3,
                gravity=1200, friction=1.0,
            )
            # Splash al impactar (10% de las gotas)
            if self._rng.random() < 0.12:
                self._emitter.emit(
                    sx, camera_offset.y + settings.INTERNAL_HEIGHT - 8,
                    config=self._splash_config(color),
                )
        elif self._climate == "snow":
            # Nieve HD: copos 4×4 con rotación y deriva, no cuadrados 2×4
            self._emitter.emit_directed(
                sx, sy, angle=self._angulo_con_viento(), speed=self._rng.uniform(40, 75),
                count=1, lifetime=self._rng.uniform(3.5, 5.5),
                size=(4, 4), color=color, spread=25,
                gravity=18, friction=0.97,
            )
        elif self._climate == "storm":
            self._emitter.emit_directed(
                sx, sy, angle=self._angulo_con_viento(), speed=580,
                count=3, lifetime=self._rng.uniform(0.8, 1.0),
                size=(2, 16), color=color, spread=7,
                gravity=1300, friction=1.0,
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

            random.choice([-1, 1]) * self._rng.uniform(50, 100)

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

    def _splash_config(self, color: tuple[int, int, int]):
        from src.framework.vfx.particle_system import BurstConfig

        # Splash HD: 3 partículas pequeñas que rebotan 2px, vida corta
        return BurstConfig(
            count=3, speed=45, lifetime=0.18, size=(1, 2),
            color=(180, 190, 210), spread=70, gravity=400, friction=0.85,
        )

    def _get_particle_color(self) -> tuple[int, int, int]:
        if self._climate == "rain":
            return (165, 185, 220)  # HD: azul grisáceo con más brillo, no 150,170,200 apagado
        elif self._climate == "snow":
            return (245, 248, 255)  # HD: blanco puro con tinte azul, no 230 gris
        elif self._climate == "storm":
            return (135, 145, 165)
        return (200, 200, 200)

    # ── Indoor/outdoor — afecta lluvia y luz ───────────────────────
    def set_indoor_factor(self, factor: float) -> None:
        """0.0 outdoor (lluvia completa) → 1.0 indoor (sin lluvia, luz cálida).
        Lo llama StageScene cada frame según si el jugador está bajo techo (colisión con IndoorZone o cielo=False).
        """
        # Reduce densidad de partículas proporcionalmente, no binario
        self._indoor_factor = max(0.0, min(1.0, factor))
        # Ajusta overlay: indoor atenúa el velo de tormenta
        base = self.CLIMATE_PARAMS.get(self._climate, self.CLIMATE_PARAMS["clear"])
        self._overlay_alpha = int(base["overlay_alpha"] * (1.0 - self._indoor_factor * 0.7))

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

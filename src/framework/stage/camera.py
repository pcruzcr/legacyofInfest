"""
Module: camera
System: framework.stage
Description: 2D camera with smooth LERP following, parallax support,
screen shake, map clamping, and camera lock zones.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings


def _factor_de_movimiento() -> float:
    """1,0 normalmente; `MOVIMIENTO_REDUCIDO_FACTOR` con la opción activada.

    Se lee en cada disparo en vez de guardarse: el jugador puede cambiar el
    ajuste desde el menú de pausa, y una copia en caché le obligaría a
    reiniciar el nivel para notarlo — que es cuando la gente concluye que la
    opción no funciona.
    """
    try:
        from src.engine.core import user_settings
        from src.engine.core.user_settings import MOVIMIENTO_REDUCIDO_FACTOR
        if user_settings.get().reduced_motion:
            return MOVIMIENTO_REDUCIDO_FACTOR
    except Exception:            # el juego se dibuja igual
        pass
    return 1.0


if TYPE_CHECKING:
    from src.framework.entities.base_entity import BaseEntity


class _CameraLock:
    """Simple camera lock for constraining axes."""
    def __init__(self, rect: pygame.Rect, lock_x: bool = False, lock_y: bool = False) -> None:
        self.rect = rect
        self.lock_x = lock_x
        self.lock_y = lock_y


class Camera:
    """
    The game camera. Follows a target entity with configurable LERP smoothing,
    per-layer parallax, map boundary clamping, screen shake, and camera lock zones.
    """

    def __init__(self) -> None:
        self.offset: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        self._target: BaseEntity | None = None
        self.lerp_speed: float = 8.0
        self._map_w: int = 0
        self._map_h: int = 0
        self._is_locked_x: bool = False
        self._is_locked_y: bool = False
        self._shake_timer: float = 0.0
        self._shake_amplitude: float = 0.0
        self._shake_offset: pygame.Vector2 = pygame.Vector2(0.0, 0.0)

        # Parallax factors (multiplied against camera offset per layer name)
        # AUD-143 — modo de cámara. Hasta ahora sólo había uno.
        #
        # `seguir` es el de siempre: la cámara persigue al jugador con
        # suavizado. Los otros dos existen porque hay géneros enteros que no
        # se pueden hacer sin ellos:
        #
        # * `zona_muerta`: la cámara **no se mueve** mientras el jugador esté
        #   dentro de un rectángulo central. Es lo que hace que un plataformas
        #   no se maree al saltar en el sitio, y lo que usan Celeste y Hollow
        #   Knight. Con la cámara siguiendo cada píxel, saltar mueve el mundo
        #   entero y cansa la vista.
        # * `sala`: la cámara salta de pantalla en pantalla, sin suavizado.
        #   Es Zelda, Metroid y los Castlevania clásicos, y cambia el diseño
        #   por completo: cada sala se compone entera y se lee de un vistazo.
        self.modo: str = "seguir"
        #: Media anchura y altura de la zona muerta, en píxeles.
        self.zona_muerta: pygame.Vector2 = pygame.Vector2(48.0, 32.0)
        #: Cuánto se adelanta la cámara según la velocidad, en segundos de
        #: anticipación. 0 lo apaga.
        self.anticipacion: float = 0.30
        #: Anticipación vertical al caer. Separada porque mirar hacia abajo
        #: al caer es lo que evita el salto de fe, y hacia arriba al subir no
        #: aporta nada: el jugador ya sabe de dónde viene.
        self.anticipacion_caida: float = 0.20
        #: Suavizado de la anticipación. Sin él, cambiar de dirección da un
        #: tirón de cámara de 60 px en un fotograma.
        self._adelanto: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        #: Zonas de bloqueo con su rectángulo. AUD-143: antes se resumían a
        #: dos booleanos y el rectángulo no se leía nunca.
        self._locks: list[Any] = []

        self._parallax_factors: dict[str, float] = {
            "BG_Far": 0.15,
            "BG_Mid": 0.40,
            "BG_Near": 0.70,
            "Terrain": 1.0,
        }

    def follow(self, target: BaseEntity) -> None:
        """Set the camera to follow this entity."""
        self._target = target

    def set_map_size(self, width: int, height: int) -> None:
        """Set map pixel dimensions for boundary clamping."""
        self._map_w = max(width, 1)
        self._map_h = max(height, 1)

    def set_camera_locks(self, locks: list[_CameraLock] | None) -> None:
        """Guarda las zonas de bloqueo. **Se aplican por posición**, no en bloque.

        AUD-143 — un `CameraLock` congelaba el nivel entero.

        Esto era::

            self._is_locked_x = any(line.lock_x for line in locks)

        Es decir: el `rect` de cada zona se guardaba y **no se leía nunca**, y
        bastaba un solo `CameraLock` en cualquier esquina del mapa para que la
        cámara quedara clavada desde el primer fotograma en todo el escenario.

        No es una sospecha: `boss_rey_scene.py` lleva un parche escrito para
        rodearlo, tocando `_is_locked_x` desde fuera con un comentario que
        explica el defecto. Cuando alguien tiene que parchear el motor desde
        su escenario, el defecto es del motor.
        """
        self._locks = list(locks or [])

    def _aplicar_bloqueos(self) -> None:
        """Decide los bloqueos de ESTE fotograma según dónde está el objetivo."""
        self._is_locked_x = False
        self._is_locked_y = False
        objetivo = self._target
        if not self._locks or objetivo is None:
            return
        centro = objetivo.rect.center
        for zona in self._locks:
            rect = getattr(zona, "rect", None)
            # Una zona sin rectángulo se comporta como antes —global—, para
            # no romper el escenario de quien contaba con el defecto.
            if rect is None or rect.collidepoint(centro):
                self._is_locked_x = self._is_locked_x or bool(zona.lock_x)
                self._is_locked_y = self._is_locked_y or bool(zona.lock_y)

    def apply_shake(self, amplitude: float = 2.0, duration: float = 0.1) -> None:
        """Trigger a screen shake. Overwrites current shake if new amplitude is larger.

        AUD-126 — «movimiento reducido» atenúa, no elimina.
        --------------------------------------------------
        La sacudida es la respuesta táctil de un impacto: quitarla del todo
        borra la única señal de que algo golpeó. Se atenúa al 25 %, que basta
        para que no provoque náusea vestibular y sigue leyéndose como golpe.

        Se filtra en el disparador y no en el dibujado a propósito: así ningún
        sistema puede saltarse el ajuste escribiendo `_shake_amplitude`
        directamente y dejar al jugador con la pantalla temblando pese a
        haberlo desactivado.
        """
        amplitude *= _factor_de_movimiento()
        if amplitude > self._shake_amplitude:
            self._shake_amplitude = amplitude
        self._shake_timer = max(self._shake_timer, duration)

    def parallax_factor(self, layer_name: str) -> float:
        """Return the parallax multiplier for the given layer name."""
        return self._parallax_factors.get(layer_name, 1.0)

    def set_parallax_factor(self, layer_name: str, factor: float) -> None:
        """Set the parallax multiplier for a given layer name."""
        self._parallax_factors[layer_name] = factor

    def layer_offset(self, layer_name: str) -> pygame.Vector2:
        """Return the camera offset adjusted for parallax on the given layer."""
        factor = self._parallax_factors.get(layer_name, 1.0)
        return self.offset * factor

    def world_to_screen(self, world_pos: pygame.Vector2) -> pygame.Vector2:
        """Convert a world position to screen position."""
        return world_pos - self.offset

    def screen_to_world(self, screen_pos: pygame.Vector2) -> pygame.Vector2:
        """Convert a screen position to world position."""
        return screen_pos + self.offset

    def update(self, dt: float) -> None:
        """
        Smoothly follow the target using LERP, apply screen shake,
        and clamp to map boundaries.
        BUG-043 FIX: Use temporary offset for shake instead of modifying self.offset directly.
        BUG-044 FIX: Frame-rate-independent LERP using 1 - (1 - speed) ** dt.
        """
        if self._target is None:
            return

        # AUD-143: los bloqueos se deciden cada fotograma según dónde está el
        # jugador, no una vez para todo el nivel.
        self._aplicar_bloqueos()

        target_x = self._target.rect.centerx
        target_y = self._target.rect.centery

        if self.modo == "sala":
            self._encuadrar_sala(target_x, target_y)
            self._aplicar_sacudida(dt)
            return

        # Look-ahead based on player velocity
        # `getattr` con defecto `None` en vez de `hasattr` + acceso: la versión
        # anterior usaba `0.0` como valor ausente y luego comprobaba el tipo,
        # de modo que el mismo nombre era a veces un vector y a veces un
        # número. El `isinstance` de abajo ya decide si hay velocidad usable.
        velocity = getattr(self._target, "velocity", None)
        if isinstance(velocity, pygame.Vector2):
            deseado_x = velocity.x * self.anticipacion
            # Sólo hacia abajo: mirar adelante al caer es lo que evita el
            # salto de fe. Hacia arriba no aporta —el jugador ya sabe de dónde
            # viene— y marea.
            deseado_y = (velocity.y * self.anticipacion_caida
                         if velocity.y > 0 else 0.0)
        else:
            deseado_x = deseado_y = 0.0

        # AUD-143 — la anticipación se suaviza. Antes se aplicaba en crudo, y
        # cambiar de dirección movía la cámara decenas de píxeles en un
        # fotograma: un tirón que se ve y que marea al ir y venir.
        suavizado = 1.0 - (1.0 - 0.08) ** max(0.0, dt * 60.0)
        self._adelanto.x += (deseado_x - self._adelanto.x) * suavizado
        self._adelanto.y += (deseado_y - self._adelanto.y) * suavizado

        # BUG-045 FIX: Clamp look_ahead to prevent pushing target past map boundaries
        look_ahead = self._adelanto.x
        if look_ahead > 0:
            look_ahead = min(look_ahead, float(self._map_w) - float(target_x))
        else:
            look_ahead = max(look_ahead, -float(target_x))
        target_x += look_ahead
        target_y = max(0.0, min(float(target_y) + self._adelanto.y,
                                float(self._map_h)))

        # BUG-044 FIX: Frame-rate-independent LERP using 1 - (1 - speed)**(dt*60)
        lerp_base = max(0.0, min(1.0, self.lerp_speed / 60.0))
        lerp_factor = 1.0 - (1.0 - lerp_base) ** (dt * 60.0)

        screen_w = settings.INTERNAL_WIDTH
        screen_h = settings.INTERNAL_HEIGHT
        # Distancia del objetivo al centro de la pantalla.
        error_x = target_x - self.offset.x - screen_w // 2
        error_y = target_y - self.offset.y - screen_h // 2

        if self.modo == "zona_muerta":
            # Dentro del rectángulo central la cámara NO se mueve. Es lo que
            # impide que saltar en el sitio mueva el mundo entero, y por lo
            # que un plataformas con esto cansa mucho menos la vista.
            error_x = self._fuera_de_la_zona(error_x, self.zona_muerta.x)
            error_y = self._fuera_de_la_zona(error_y, self.zona_muerta.y)

        if not self._is_locked_x:
            self.offset.x += error_x * lerp_factor
        if not self._is_locked_y:
            self.offset.y += error_y * lerp_factor

        self._aplicar_sacudida(dt)

    # ── piezas compartidas por los tres modos ─────────────────────
    @staticmethod
    def _fuera_de_la_zona(error: float, medio_ancho: float) -> float:
        """Lo que sobresale de la zona muerta. Dentro devuelve 0."""
        if abs(error) <= medio_ancho:
            return 0.0
        return error - medio_ancho if error > 0 else error + medio_ancho

    def _encuadrar_sala(self, target_x: float, target_y: float) -> None:
        """Modo `sala`: la cámara salta de pantalla en pantalla, sin suavizar.

        Es Zelda, Metroid y los Castlevania clásicos. El salto es instantáneo
        **a propósito**: suavizarlo convierte el corte en un barrido y se
        pierde justo lo que este modo aporta, que es que cada sala se lea
        entera de un vistazo.
        """
        screen_w = settings.INTERNAL_WIDTH
        screen_h = settings.INTERNAL_HEIGHT
        if not self._is_locked_x:
            self.offset.x = (int(target_x) // screen_w) * screen_w
        if not self._is_locked_y:
            self.offset.y = (int(target_y) // screen_h) * screen_h
        self.offset.x = max(0.0, min(self.offset.x,
                                     max(0, self._map_w - screen_w)))
        self.offset.y = max(0.0, min(self.offset.y,
                                     max(0, self._map_h - screen_h)))

    def _aplicar_sacudida(self, dt: float) -> None:
        # BUG-043 FIX: Remove previous shake offset before computing new one
        self.offset -= self._shake_offset
        self._shake_offset.update(0.0, 0.0)

        if self._shake_timer > 0:
            self._shake_timer -= dt
            sx = random.uniform(-1.0, 1.0) * self._shake_amplitude
            sy = random.uniform(-1.0, 1.0) * self._shake_amplitude
            self._shake_offset.update(sx, sy)
        else:
            self._shake_amplitude = 0.0

        # Clamp to map boundaries
        screen_w = settings.INTERNAL_WIDTH
        screen_h = settings.INTERNAL_HEIGHT
        self.offset.x = max(0.0, min(self.offset.x, self._map_w - screen_w))
        self.offset.y = max(0.0, min(self.offset.y, self._map_h - screen_h))

        # Apply shake offset to final view (temporary, does not persist)
        self.offset += self._shake_offset
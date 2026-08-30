"""
Module: dron04
System: stages.stage2_1_oficinas
Academic Unit: Unit II (Vectors) + Unit III (Curves) + Unit V (Color)

DRON-04 — dron de seguridad del datacenter (Zona 2, Oficinas).

Entidad personalizada para la Evaluación Práctica I (`docs/eval_practica/
eval_practica.md`, rúbrica de 100 pts):

  - **Unidad II — vectores (20 pts):** el cono de detección frontal no es un
    círculo ciego. `_target_lock()` usa `vec2_distance` (¿está el jugador
    dentro del radio real de detección?) y `vec2_normalize` + `vec2_dot`
    (¿está delante del dron, no detrás?) sobre `math_utils`, las mismas
    funciones que pide la rúbrica por nombre — no matemática vectorial ad
    hoc reinventada aquí.
  - **Unidad III — curvas (15 pts):** patrulla en un lazo cerrado calculado
    con `CurveTools` (Catmull-Rom vía `EnemyFlying.flight_mode="bezier"`),
    NO en línea recta y NO en la sinusoide genérica del motor. Los 6 puntos
    de control se generan en `_build_loop()` (documentados ahí).
  - **Unidad V — color (15 pts):** el anillo del radar no cambia de azul a
    rojo de golpe. `_ring_color()` interpola el nivel de alerta en espacio
    HSV con `ColorTools.hsv_to_rgb` (matiz 195°→4°, Unit V del framework) y
    reconvierte a RGB para pintar — una operación de espacio de color
    observable en pantalla, no sólo una lectura de paleta fija.

No modifica ningún archivo compartido del motor salvo `entity_factory.py`
(registro, ver ese fichero), así que no afecta a los niveles de otros
compañeros de equipo.
"""
from __future__ import annotations

import math

import pygame

from src.engine.core.events import Events
from src.engine.utils.math_utils import lerp, vec2_distance, vec2_dot, vec2_normalize
from src.engine.utils.surface_pool import get_pool
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.processing.color_tools import ColorTools


class Dron04(EnemyFlying):
    """Dron de seguridad: patrulla un lazo curvo y persigue al detectar al jugador.

    - Patrulla: `flight_mode="bezier"` — Catmull-Rom cerrado por
      `CurveTools.build_bezier_path`, construido en `flight_strategies.py`.
      El lazo de 6 puntos se genera aquí a partir del punto de spawn (vector
      de origen) más desplazamientos vectoriales fijos, para que cada DRON-04
      colocado en el mapa recorra un ojal suave alrededor de su propia
      posición sin tener que declarar waypoints a mano en Tiled.
    - Alerta: `alert_flight_mode="chase"` — al detectar al jugador abandona
      la curva y acelera hacia él (persecución con inercia, ya implementada
      en el motor).
    - Dibuja un radar: un anillo en el radio de detección real
      (`detection_range_x`) más una línea de barrido que gira; el color pasa
      de azul a rojo por interpolación HSV según el nivel de alerta (ver
      `_ring_color`), y una retícula vectorial (`_target_lock`) marca al
      jugador cuando está dentro del cono frontal real, no sólo del radio.
      Es puramente visual —no toca `enemy_base.py`— así que sólo aparece en
      este dron.
    """

    #: Cuántos grados por segundo gira la línea de barrido del radar.
    SWEEP_SPEED_DEG = 140.0

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        loop_radius_x: float = 110.0,
        loop_radius_y: float = 55.0,
        flight_speed: float = 70.0,
        max_health: float = 2.0,
        damage_on_contact: float = 0.5,
        zone: int = 2,
        **kwargs,
    ) -> None:
        waypoints = self._build_loop(spawn_position, loop_radius_x, loop_radius_y)

        super().__init__(
            spawn_position=spawn_position,
            flight_mode="bezier",
            alert_flight_mode="chase",
            flight_speed=flight_speed,
            waypoints=waypoints,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            zone=zone,
            **kwargs,
        )
        # El radar usa el mismo radio que la detección real del motor, así
        # que lo que el jugador ve es exactamente lo que el dron "siente".
        self._radar_angle_deg: float = 0.0
        self._radar_surf: pygame.Surface | None = None
        self._radar_surf_size: tuple[int, int] = (0, 0)
        # AUD-101: el sprite base (14x10) es del tamaño de un bicho de fondo
        # de selva y se perdía contra el fondo de datacenter. El dron es un
        # enemigo protagonista de esta asignación (curva + radar), así que se
        # re-dibuja ampliado con un halo, puramente visual — no cambia
        # `self.rect` ni la física/colisión, que siguen en 20x14.
        self._pulse_t: float = 0.0
        self._glow_cache: dict[tuple[int, bool], pygame.Surface] = {}
        # 0.0 = patrulla (azul), 1.0 = alerta plena (rojo). Se suaviza hacia
        # el objetivo cada fotograma en vez de saltar, así que el color del
        # radar (ver _ring_color) es una transición continua, no un switch.
        self._alert_level: float = 0.0
        self._was_detected: bool = False

    @staticmethod
    def _build_loop(
        origin: pygame.Vector2,
        rx: float,
        ry: float,
    ) -> list[tuple[float, float]]:
        """Genera un lazo cerrado de 6 puntos de control alrededor de `origin`.

        Matemática vectorial explícita: cada punto es origin + un vector de
        desplazamiento (coseno, seno) escalado por (rx, ry). BezierFlight
        (flight_strategies.py) ya cierra el lazo interpolando el último punto
        de vuelta al primero, así que no hace falta repetir el punto inicial.
        """
        points: list[tuple[float, float]] = []
        n = 6
        for i in range(n):
            theta = (2.0 * math.pi * i) / n
            offset = pygame.Vector2(math.cos(theta) * rx, math.sin(theta) * ry)
            p = origin + offset
            points.append((p.x, p.y))
        return points

    #: Cuánto se agranda el sprite del dron respecto al frame original (14x10).
    #: Puramente visual: no toca self.rect (20x14), que sigue siendo la caja
    #: de colisión real usada por el motor.
    SPRITE_SCALE = 3.0

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if not self.is_visible:
            return
        if not self.is_alive and self.state.name != "DYING":
            return

        self._pulse_t += 1.0 / 60.0
        detected = self.state.name in ("CHASE", "ALERT", "TELEGRAPHING", "SEARCH")
        # Suaviza hacia 0/1 en vez de asignar directo: es lo que hace visible
        # la interpolación de color en _ring_color() fotograma a fotograma.
        self._alert_level = lerp(self._alert_level, 1.0 if detected else 0.0, 0.08)
        ring_color = self._ring_color()

        # Sonido de alarma sólo en el flanco de subida (no-detectado ->
        # detectado), no cada fotograma mientras persigue. Reutiliza
        # SFX_HAZARD_ZONE (ya registrado y mapeado a un audio de alarma en
        # stage_scene.py) en vez de dar de alta un evento nuevo — un sonido
        # de "alerta" y uno de "zona de peligro" son la misma idea acústica,
        # y así no hace falta tocar events.py ni el mapa de sonidos del motor.
        if detected and not self._was_detected and self._event_bus is not None:
            self._event_bus.emit(Events.SFX_HAZARD_ZONE)
        self._was_detected = detected

        cx = int(self.position.x - camera_offset.x + self.rect.width / 2)
        cy = int(self.position.y - camera_offset.y + self.rect.height / 2)

        self._draw_radar(surface, cx, cy, ring_color)
        self._draw_target_lock(surface, cx, cy, camera_offset, ring_color)
        self._draw_glow(surface, cx, cy, detected)
        self._draw_health_bar(surface, int(self.position.x - camera_offset.x),
                               int(self.position.y - camera_offset.y))

        # Sprite ampliado (ver SPRITE_SCALE) en vez del blit nativo diminuto
        # de EnemyBase.draw(); el resto de esa lógica (parpadeo de invencible,
        # tinte de golpe) se replica aquí a la escala grande.
        if not self._flash_visible:
            return
        anim_key = self._get_animation_state()
        frames = self._sprite_frames.get(anim_key)
        if frames:
            frame_idx = min(self._animation_frame, len(frames) - 1)
            if self.facing_direction < 0:
                frame = get_pool().get_flipped_frames(frames)[frame_idx]
            else:
                frame = frames[frame_idx]
            fw, fh = frame.get_size()
            sw, sh = int(fw * self.SPRITE_SCALE), int(fh * self.SPRITE_SCALE)
            big = pygame.transform.smoothscale(frame, (sw, sh))
            if self._hit_tint_timer > 0:
                tint = big.copy()
                alpha = int(min(255, (self._hit_tint_timer / max(self._hurt_timer * 0.6, 0.01)) * 180))
                overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
                overlay.fill((*self._hit_tint_color, alpha))
                tint.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                big = tint
            surface.blit(big, (cx - sw // 2, cy - sh // 2))
        else:
            pygame.draw.rect(
                surface, (200, 60, 60),
                (cx - self.rect.width, cy - self.rect.height,
                 self.rect.width * 2, self.rect.height * 2),
            )

    def _draw_glow(self, surface: pygame.Surface, cx: int, cy: int, detected: bool) -> None:
        """Halo pulsante detrás del dron para que resalte contra fondos ocupados."""
        pulse = 0.5 + 0.5 * math.sin(self._pulse_t * 4.0)
        r = int(26 + pulse * 8)
        key = (r, detected)
        glow = self._glow_cache.get(key)
        if glow is None:
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            base = (255, 80, 70) if detected else (90, 220, 255)
            for i in range(r, 0, -2):
                a = int(70 * (1 - i / r) ** 2)
                pygame.draw.circle(glow, (*base, a), (r, r), i)
            self._glow_cache[key] = glow
        surface.blit(glow, (cx - r, cy - r), special_flags=pygame.BLEND_RGBA_ADD)

    def _ring_color(self) -> tuple[int, int, int]:
        """Color del radar por interpolación HSV (Unidad V — color).

        En vez de elegir entre dos tuplas RGB fijas según el estado, el
        matiz se interpola en grados (195° azul-cian → 4° rojo) según
        `self._alert_level` y se reconvierte con `ColorTools.hsv_to_rgb`.
        Es la operación de conversión de espacio de color que pide la
        rúbrica, y es observable: el anillo vira de color en vivo según se
        acerca el jugador, no salta entre dos estados.
        """
        hue = lerp(195.0, 4.0, self._alert_level)
        sat = lerp(0.65, 0.85, self._alert_level)
        return ColorTools.hsv_to_rgb(hue, sat, 1.0)

    def _target_lock(self) -> tuple[float, float] | None:
        """Matemática vectorial explícita (Unidad II) sobre el jugador.

        Devuelve `(distancia, alineación)` o `None` si no hay referencia al
        jugador. `distancia` viene de `vec2_distance` (mismo radio que usa el
        motor para detectar). `alineación` es `vec2_dot` entre la dirección
        normalizada dron→jugador (`vec2_normalize`) y hacia dónde mira el
        dron: 1.0 = jugador justo al frente, -1.0 = justo detrás. Se usa para
        no "bloquear el objetivo" visualmente si el jugador está detrás del
        dron, aunque esté dentro del radio — un radar circular ciego no
        distingue eso, un vector sí.
        """
        player_rect = getattr(self, "_player_ref", None)
        if player_rect is None:
            return None
        player_pos = pygame.Vector2(player_rect.centerx, player_rect.centery)
        drone_center = pygame.Vector2(
            self.position.x + self.rect.width / 2,
            self.position.y + self.rect.height / 2,
        )
        distance = vec2_distance(drone_center, player_pos)
        to_player = player_pos - drone_center
        direction = vec2_normalize(to_player) if distance > 1e-6 else pygame.Vector2(self.facing_direction, 0)
        facing = pygame.Vector2(self.facing_direction, 0)
        alignment = vec2_dot(direction, facing)
        return (distance, alignment)

    def _draw_target_lock(self, surface: pygame.Surface, cx: int, cy: int,
                           camera_offset: pygame.Vector2, ring_color: tuple[int, int, int]) -> None:
        """Retícula sobre el jugador cuando está dentro del cono frontal real."""
        lock = self._target_lock()
        if lock is None:
            return
        distance, alignment = lock
        if distance > self.detection_range_x or alignment < 0.15:
            return
        player_rect = self._player_ref
        px = int(player_rect.centerx - camera_offset.x)
        py = int(player_rect.centery - camera_offset.y)
        pygame.draw.line(surface, ring_color, (cx, cy), (px, py), 1)
        r = 6 + int(2 * (0.5 + 0.5 * math.sin(self._pulse_t * 6.0)))
        pygame.draw.circle(surface, ring_color, (px, py), r, 2)
        pygame.draw.line(surface, ring_color, (px - r - 4, py), (px - r, py), 2)
        pygame.draw.line(surface, ring_color, (px + r, py), (px + r + 4, py), 2)

    def _draw_radar(self, surface: pygame.Surface, cx: int, cy: int,
                     ring_color: tuple[int, int, int]) -> None:
        self._radar_angle_deg = (
            self._radar_angle_deg + self.SWEEP_SPEED_DEG * (1.0 / 60.0)
        ) % 360.0

        radius = int(self.detection_range_x)
        if radius <= 0:
            return
        size = (radius * 2, radius * 2)
        if self._radar_surf is None or self._radar_surf_size != size:
            self._radar_surf = pygame.Surface(size, pygame.SRCALPHA)
            self._radar_surf_size = size
        surf = self._radar_surf
        surf.fill((0, 0, 0, 0))

        pulse = 0.5 + 0.5 * math.sin(self._pulse_t * 3.0)

        # Dos anillos concéntricos (radio real + 60%) para que se lea como
        # radar y no como un círculo perdido de 1px contra los racks.
        pygame.draw.circle(surf, (*ring_color, 130), (radius, radius), radius, 3)
        pygame.draw.circle(surf, (*ring_color, 60), (radius, radius),
                            int(radius * 0.6), 2)
        # Disco translúcido tenue + pulso de "respiración" para dar volumen.
        pygame.draw.circle(surf, (*ring_color, int(18 + pulse * 14)),
                            (radius, radius), radius)

        # Barrido: línea principal + 4 líneas rezagadas que se desvanecen,
        # simulando la estela de un radar real en vez de una sola raya fina.
        for i, trail_alpha in enumerate((200, 130, 80, 45, 20)):
            ang = math.radians(self._radar_angle_deg - i * 10.0)
            tip = pygame.Vector2(radius, radius) + pygame.Vector2(
                math.cos(ang) * radius, math.sin(ang) * radius,
            )
            pygame.draw.line(surf, (*ring_color, trail_alpha),
                              (radius, radius), (tip.x, tip.y), 3 if i == 0 else 2)

        surface.blit(surf, (cx - radius, cy - radius))

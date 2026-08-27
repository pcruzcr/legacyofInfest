"""
Module: enemy_base
System: framework.entities
Academic Unit: Unit II (Vectors, Collision), Unit III (State Machines)
Description: Abstract base class for all enemy entities. Provides FSM
(PATROL/ALERT/HURT/DYING), detection system, contact damage, invincibility,
hitbox/hurtbox infrastructure, and death handling.
"""
from __future__ import annotations

import warnings
from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.surface_pool import get_pool
from src.framework.combate import dano as combate_dano
from src.framework.entities.base_entity import BaseEntity
from src.framework.vfx.contorno import COLOR_ENEMIGO, dibujar_con_contorno

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class EnemyState(str, Enum):
    """Estados de un enemigo.

    AUD-051: la máquina tenía siete estados y le faltaban seis de los doce que
    `docs/05_ENEMY_SPEC.md` §12 describe. Los que faltaban no eran adornos: son
    justamente los que hacen legible un combate.

    * ``IDLE`` — un enemigo estacionario (patrol_length = 0) estaba en PATROL
      "patrullando" cero píxeles. Distinguirlos permite animarlos distinto y
      deja de mentir sobre lo que el enemigo está haciendo.
    * ``SEARCH`` — el jugador fue visto y se perdió. Sin este estado el enemigo
      te olvida en el fotograma en que sales de rango, lo que hace inútil
      romper la línea de visión. Con él, el enemigo tiene memoria corta y
      esconderse significa algo.
    * ``CHASE`` — persecución activa, distinta de ALERT (consciente). Permite
      una velocidad y una animación propias.
    * ``RETREAT`` — repliegue con poca vida. `SquadBrain` ya emitía la táctica
      "retreat"; ahora hay un estado que la representa.
    * ``RECOVER`` — ventana de vulnerabilidad tras atacar. Es *la* pieza que
      vuelve justo el combate: sin recuperación, un enemigo que ataca sin pausa
      no se puede castigar y la única respuesta posible es evitarlo.
    * ``STUNNED`` — aturdido por una parada o un golpe pesado. Recompensa la
      defensa activa en lugar de premiar sólo esquivar.
    """

    IDLE = "IDLE"
    PATROL = "PATROL"
    SEARCH = "SEARCH"
    ALERT = "ALERT"
    CHASE = "CHASE"
    TELEGRAPHING = "TELEGRAPHING"
    FIRING = "FIRING"
    RECOVER = "RECOVER"
    RETREAT = "RETREAT"
    STUNNED = "STUNNED"
    HURT = "HURT"
    LAUNCHED = "LAUNCHED"
    DYING = "DYING"


class EnemyBase(BaseEntity):
    """
    Abstract root class for all enemies. Inherits from BaseEntity.
    Subclasses implement _patrol_behavior, _alert_behavior,
    _get_animation_key, _build_hitbox, _build_hurtbox.
    Do NOT override update() — use the master update pattern.
    """

    #: AUD-279 — exención del culling: se sigue simulando lejos de la cámara.
    #:
    #: `False` para un enemigo normal, que fuera del encuadre no le importa a
    #: nadie. Ponlo a `True` en una subclase cuyo comportamiento sólo tenga
    #: sentido simulado de continuo —un perseguidor que se acerca desde el otro
    #: extremo del mapa, un enemigo con un temporizador largo—. Los proyectiles
    #: en vuelo **no** hacen falta declararlos: `culling.se_simula` los detecta.
    siempre_activo: bool = False

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float,
        damage_on_contact: float = 0.5,
        contact_knockback: float = 120.0,
        detection_range_x: float = 160.0,
        detection_range_y: float = 64.0,
        hurt_duration: float = 0.25,
        invincibility_duration: float = 0.5,
        deaggro_margin: float = 32.0,
        event_bus=None,
        species_id: str | None = None,
        **kwargs,
    ) -> None:
        """Initialize the enemy at the given spawn position."""
        super().__init__(spawn_position, event_bus)

        # --- Health ---
        from src.engine.core.difficulty import get_config
        scaled_max = max_health * get_config().enemy_health_mult
        self.max_health: float = scaled_max
        self.current_health: float = scaled_max
        self.is_alive: bool = True

        # --- Combat ---
        self.damage_on_contact: float = damage_on_contact
        self.contact_knockback: float = contact_knockback
        self._invincibility_timer: float = 0.0

        # AUD-050: táctica decidida por SquadBrain. Es una lectura, no una
        # inferencia: el cerebro de escuadra reevalúa a 4 Hz por lotes y escribe
        # aquí, y el comportamiento de alerta la consulta cada fotograma sin
        # coste. Por defecto "approach" para que un enemigo instanciado en un
        # test o en un template de alumno se comporte igual que antes.
        self.tactic: str = "approach"

        # AUD-051: temporizadores de los estados nuevos.
        self._search_timer: float = 0.0
        self._recover_timer: float = 0.0
        self._stun_timer: float = 0.0
        #: Última posición conocida del jugador; alimenta el estado SEARCH.
        self._last_seen: pygame.Vector2 | None = None
        #: Límites de la arena (AUD-615). La escena los fija vía set_arena_bounds.
        #: None = sin límites; el enemigo puede moverse libremente.
        self.arena_bounds: pygame.Rect | None = None
        self._contact_cooldown: float = 0.0
        self._hurt_timer: float = 0.0
        self._death_timer: float = 0.0
        self._hurt_duration: float = hurt_duration
        self._invincibility_duration: float = invincibility_duration
        self._knockback_velocity: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        self._hitstun_type: str = "light"  # light, heavy, launch
        # BUG-030 FIX: Initialize telegraph timer to duration so it doesn't fire instantly
        self._telegraph_timer: float = 0.4
        self._telegraph_duration: float = 0.4
        self._ground_y: float = spawn_position.y
        self._is_airborne: bool = False

        #: AUD-387 — resistencias por canal de daño. Multiplicadores: 0,5 es
        #: resistencia, 2,0 debilidad, 0,0 inmunidad. **Vacío por defecto**, y
        #: eso importa: sin resistencias declaradas la mitigación es 1,0 y las
        #: 26 llamadas a `apply_hit` que viven en entregas siguen pegando
        #: exactamente lo mismo. Se declara en Tiled con la propiedad
        #: `resistencias`, por ejemplo `veneno:0.5, fuego:2`.
        self.resistencias: dict[str, float] = {}

        # --- Collision ---
        self._collision_rects: list[pygame.Rect] = []
        self._one_way_rects: list[pygame.Rect] = []
        # AUD-325 — suelo inclinado para los enemigos. Vacía por defecto:
        # ningún mapa entregado tiene pendientes, y el paso entero se salta.
        # `_hug_slopes` excluye a los voladores, que no pisan suelo.
        self._pendientes: list = []
        self._hug_slopes: bool = True

        # --- Detection ---
        self.detection_range_x: float = detection_range_x
        self.detection_range_y: float = detection_range_y
        self._deaggro_margin: float = deaggro_margin
        self._player_ref: pygame.Rect | None = None

        # --- State ---
        self.state: EnemyState = EnemyState.PATROL
        self.facing_direction: int = 1  # -1 left, 1 right

        # --- Hitbox / Hurtbox (world-space, recomputed each frame) ---
        self.hitbox: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.hurtbox: pygame.Rect = pygame.Rect(0, 0, 0, 0)

        # --- Animation ---
        self._animation_timer: float = 0.0
        self._animation_frame: int = 0

        # --- Invincibility flash ---
        self._flash_counter: float = 0.0
        self._flash_visible: bool = True
        self._was_alive: bool = True
        self._hit_tint_color: tuple[int, int, int] = (255, 255, 255)  # Tint during hitstun
        self._hit_tint_timer: float = 0.0

        # --- Sprite ---
        self.species_id: str | None = species_id
        self._species_id: str | None = species_id
        if kwargs:
            # allow extra species params without breaking
            for k, v in list(kwargs.items()):
                if k == "species_id":
                    self.species_id = v
                    self._species_id = v
        self._sprite_zone: int = 0
        self._sprite_frames: dict[str, list[pygame.Surface]] = {}
        self._sprite_fw: int = 16
        self._sprite_fh: int = 12

        # --- Rect ---
        self.rect = pygame.Rect(
            int(self.position.x),
            int(self.position.y),
            24,
            28,
        )

        # Cached surfaces (reused to avoid per-frame allocations)
        self._telegraph_warning_surf: pygame.Surface | None = None
        self._telegraph_warning_size: tuple[int, int] = (0, 0)
        self._tint_surf: pygame.Surface | None = None
        self._tint_surf_size: tuple[int, int] = (0, 0)

    # ──────────────────────────────────────────────
    # Master update (do NOT override in subclasses)
    # ──────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """
        Master update. Called every frame.
        Order: pre_update -> invincibility -> state machine -> rects ->
               contact -> animation -> post_update.
        Subclasses override _pre_update or _post_update instead.
        TEMPLATE METHOD: algorithm skeleton fixed; hook methods supply
        per-subclass behavior without overriding the skeleton.
        """
        if not self.is_alive:
            if self.state == EnemyState.DYING:
                self._tick_cooldowns(dt)
                self._advance_animation(dt)
                self._run_state_machine(dt)
            return
        if self._pre_update(dt):
            return
        self._update_invincibility(dt)
        self._run_state_machine(dt)
        self._apply_knockback(dt)
        self._update_rects()
        self._tick_cooldowns(dt)
        self._advance_animation(dt)
        self._post_update(dt)
        # AUD-667 — anclaje al suelo plano para que HURT/DYING no desplacen
        # `rect.bottom`. Evita que el cambio de sprite o el retroceso deje al
        # enemigo levitando por un decimales de colisión. No afecta a
        # LAUNCHED/DYING ni a voladores.
        self._mantener_en_suelo()
        # AUD-325 — el suelo inclinado, al final: las subclases mueven la
        # posición en distintos puntos (estado, knockback, `_post_update`),
        # y éste es el único lugar que las ve a todas.
        self._resolver_pendientes()

    def _apply_knockback(self, dt: float) -> None:
        """Apply knockback velocity and decelerate."""
        if self._knockback_velocity.length_squared() > 0:
            self.position.x += self._knockback_velocity.x * dt
            self.position.y += self._knockback_velocity.y * dt
            # BUG-032 FIX: Collision resolution after knockback
            entity_rect = pygame.Rect(
                int(self.position.x), int(self.position.y),
                self.rect.width, self.rect.height,
            )
            for tile in self._collision_rects:
                    if entity_rect.colliderect(tile):
                        overlap_x = min(entity_rect.right - tile.left, tile.right - entity_rect.left)
                        overlap_y = min(entity_rect.bottom - tile.top, tile.bottom - entity_rect.top)
                        if overlap_x < overlap_y:
                            if entity_rect.centerx < tile.centerx:
                                self.position.x = tile.left - entity_rect.width
                            else:
                                self.position.x = tile.right
                            entity_rect.x = int(self.position.x)
                        else:
                            if entity_rect.centery < tile.centery:
                                self.position.y = tile.top - entity_rect.height
                            else:
                                self.position.y = tile.bottom
                            entity_rect.y = int(self.position.y)
            # BUG-033 FIX: Frame-rate independent deceleration
            self._knockback_velocity.x *= (0.85 ** (dt * 60.0))
            self._knockback_velocity.y *= (0.85 ** (dt * 60.0))
            if abs(self._knockback_velocity.x) < 1.0 and abs(self._knockback_velocity.y) < 1.0:
                self._knockback_velocity.x = 0.0
                self._knockback_velocity.y = 0.0

    def _pre_update(self, dt: float) -> bool:
        """
        Optional pre-update hook. Return True to skip the rest of update().
        Used by BossBase for phase transitions.
        """
        return False

    def _post_update(self, dt: float) -> None:
        """
        Optional post-update hook.
        Used by EnemyShooter to update projectiles.
        """

    @property
    def death_timer(self) -> float:
        return self._death_timer

    def _load_zone_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Load zone-specific enemy sprite sheets.

        AUD-XXX — corrección del bug de early-return y recorte garbled.

        * Cada estado (walk/hurt/die) se intenta por separado: primero
          ``enemy_{sid}_{key}.png`` en la carpeta de zona, luego en
          ``species/``. Si falta tras probar ``fw,fh`` con
          ``AssetLoader``, se intenta el genérico de zona con el mismo
          ``fw,fh``. Sólo si también falla (``frames==[]`` o recorte
          garbled — ``0 filas`` cuando ``fh`` no divide la hoja —) se
          genera un placeholder coloreado por zona para que nunca quede
          un cuadro rojo.
        * No hay early-return global: que walk exista no exime de probar
          hurt/die, que es justo lo que dejaba HURT/DYING en rojo.
        * La validación ``frames[0].get_size()==(fw,fh)`` detecta el caso
          ``Archer 12×14 sobre hoja 16×12 → 0 filas`` donde el recorte da
          ``[]`` o frames de tamaño inesperado y fuerza el fallback.
        """
        self._sprite_zone = zone
        self._sprite_fw = fw
        self._sprite_fh = fh
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        species_id = getattr(self, "species_id", None)
        if species_id is None:
            species_id = getattr(self, "_species_id", None)
        # Colores por zona para placeholder (si no hay arte)
        ZONE_PLACEHOLDER = {
            1: (120, 80, 40),
            2: (60, 120, 60),
            3: (80, 60, 120),
            4: (100, 90, 70),
        }
        base_col = ZONE_PLACEHOLDER.get(zone, (120, 80, 40))
        for key, fname_generic, expected, placeholder_col in [
            ("walk", f"enemy_{zone_key}_walk.png", 6, base_col),
            ("hurt", f"enemy_{zone_key}_hurt.png", 3, (200, 60, 60)),
            ("die", f"enemy_{zone_key}_die.png", 5, (80, 30, 30)),
        ]:
            frames: list[pygame.Surface] = []
            # 1) intento especie-específico con fw,fh correctos
            if species_id:
                sid = str(species_id).lower()
                candidates = [
                    base / f"enemy_{sid}_{key}.png",
                    settings.ASSETS_DIR / "sprites" / "enemies" / "species" / f"{species_id}_{key}.png",
                    settings.ASSETS_DIR / "sprites" / "enemies" / "species" / f"{sid}_{key}.png",
                ]
                # compat: el walk legacy a veces se guardó como {sid}_walk.png sin key
                if key == "walk":
                    candidates.append(
                        settings.ASSETS_DIR / "sprites" / "enemies" / "species" / f"{species_id}_walk.png"
                    )
                for cand in candidates:
                    if not cand.exists():
                        continue
                    try:
                        tmp = AssetLoader.load_sprite_sheet(cand, fw, fh)
                    except Exception:
                        continue
                    if tmp and len(tmp) > 0 and tmp[0].get_size() == (fw, fh):
                        frames = tmp
                        break
                    # recorte garbled (0 filas o tamaño inesperado) → tratar como fallo y probar siguiente candidato
                    continue
                if frames:
                    self._sprite_frames[key] = frames
                    continue
            # 2) fallback genérico de zona, pero sólo si el archivo existe y el recorte cuadra
            generic_path = base / fname_generic
            if generic_path.exists():
                try:
                    gen = AssetLoader.load_sprite_sheet(generic_path, fw, fh)
                except Exception:
                    gen = []
                if gen and len(gen) > 0 and gen[0].get_size() == (fw, fh):
                    # genérico válido con fw,fh — aceptar aunque el conteo no coincida exactamente,
                    # pero evitar el caso 12×14 sobre 16×12 que da 0 filas ([] ya filtrado)
                    self._sprite_frames[key] = gen
                    continue
            # 3) placeholder coloreado por zona si frames==[] o garbled
            placeholder: list[pygame.Surface] = []
            col = placeholder_col
            hi = tuple(min(255, c + 30) for c in col)
            for _ in range(expected):
                surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                surf.fill((*col, 255))
                # silueta mínima para que no sea un rectángulo rojo genérico
                if fw >= 6 and fh >= 6:
                    pygame.draw.ellipse(surf, hi, (1, 1, fw - 2, fh - 2))
                    pygame.draw.ellipse(surf, col, (2, 2, fw - 4, fh - 4))
                    if fw >= 10 and fh >= 6:
                        pygame.draw.circle(surf, (255, 255, 255), (fw // 3, fh // 3), 1)
                        pygame.draw.circle(surf, (255, 255, 255), (2 * fw // 3, fh // 3), 1)
                        pygame.draw.circle(surf, (40, 40, 40), (fw // 3, fh // 3 + 1), 1)
                        pygame.draw.circle(surf, (40, 40, 40), (2 * fw // 3, fh // 3 + 1), 1)
                    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 1)
                placeholder.append(surf)
            self._sprite_frames[key] = placeholder
        self._load_extra_sprites(zone, fw, fh)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Hook for subclasses to load extra sprites beyond walk/hurt/die."""

    # Per-state animation FPS (subclasses override as needed)
    _ANIM_FPS: dict[str, float] = {
        "walk": 10.0, "fly": 12.0, "shoot": 16.0,
        "hurt": 12.0, "die": 10.0,
    }
    # Alert-mode FPS override (same animation keys, faster playback)
    _ALERT_ANIM_FPS: dict[str, float] = {
        "walk": 14.0, "fly": 16.0,
    }

    def _advance_animation(self, dt: float) -> None:
        """Advance the sprite animation frame at state-specific FPS."""
        anim_key = self._get_animation_state()
        fps = self._ANIM_FPS.get(anim_key, 10.0)
        if self.state == EnemyState.ALERT and anim_key in self._ALERT_ANIM_FPS:
            fps = self._ALERT_ANIM_FPS[anim_key]
        frame_duration = 1.0 / fps
        self._animation_timer += dt
        frames = self._sprite_frames.get(anim_key)
        if not frames:
            return
        if self._animation_timer >= frame_duration:
            self._animation_timer -= frame_duration
            self._animation_frame = (self._animation_frame + 1) % len(frames)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """
        Draw the enemy via sprite sheet or placeholder fallback.
        """
        if not self.is_visible:
            return
        # BUG-031 FIX: Death animation visible until death timer expires
        if not self.is_alive and self.state != EnemyState.DYING:
            return
        if not self.is_alive and self.state == EnemyState.DYING and self._death_timer <= 0:
            return

        # Invincibility flash: skip draw when invisible
        if not self._flash_visible:
            return

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        self._draw_health_bar(surface, screen_x, screen_y)

        # Telegraph warning indicator
        if self.state == EnemyState.TELEGRAPHING:
            elapsed = self._telegraph_duration - self._telegraph_timer
            radius = 4 + int(elapsed * 40)
            alpha = 128 + int(127 * (1.0 - self._telegraph_timer / self._telegraph_duration))
            if int(pygame.time.get_ticks() / 80) % 2 == 0:
                size = (radius * 2, radius * 2)
                if (self._telegraph_warning_surf is None
                        or self._telegraph_warning_size != size):
                    self._telegraph_warning_surf = pygame.Surface(size, pygame.SRCALPHA)
                    self._telegraph_warning_size = size
                warning_surf = self._telegraph_warning_surf
                warning_surf.fill((0, 0, 0, 0))
                pygame.draw.circle(warning_surf, (255, 50, 50, alpha), (radius, radius), radius, 2)
                surface.blit(
                    warning_surf,
                    (screen_x + self.rect.width // 2 - radius,
                     screen_y + self.rect.height // 2 - radius))

        # Try sprite rendering
        anim_key = self._get_animation_state()
        frames = self._sprite_frames.get(anim_key)
        if frames:
            frame_idx = min(self._animation_frame, len(frames) - 1)
            if self.facing_direction < 0:
                flipped_frames = get_pool().get_flipped_frames(frames)
                frame = flipped_frames[frame_idx]
            else:
                frame = frames[frame_idx]
            # AUD-667 — anclaje abajo-centro independiente del sprite.
            # Usar el tamaño real del frame y no `_sprite_fw/_sprite_fh` evita
            # que HURT/DYING con altura distinta desplace `rect` o `position`:
            # el cuerpo (`rect`) manda y el dibujo se adapta al frame, igual
            # que `player.py:draw` hace con `SPRITE_W/H`.
            ox = (self.rect.width - frame.get_width()) // 2
            oy = self.rect.height - frame.get_height()
            destino = (screen_x + ox, screen_y + oy)
            # AUD-304 — el contorno de AUD-190, disponible también aquí. Se
            # consulta cada fotograma y no se cachea en el enemigo a propósito:
            # la opción se cambia desde el menú sin salir de la partida, y una
            # copia local haría falso el interruptor hasta reiniciar. Es el
            # mismo patrón que `reduced_motion` en `stage/camera.py`.
            #
            # Y el import va aquí dentro por el mismo motivo que allí, que
            # costó un fallo descubrir: `user_settings` importa `orjson`, y
            # subirlo al cuerpo del módulo mete esa dependencia en la cadena de
            # `stage_loader` → `entities` → `enemy_base`. `grade_stage.py`
            # carga escenarios en un entorno pelado, así que el calificador
            # empezó a dar 0 de 12 en `design_completable` a los dieciséis
            # mapas — incluido stage0, que tenía nota perfecta.
            from src.engine.core import user_settings

            if user_settings.preferencia("contorno_de_enemigos", False):
                dibujar_con_contorno(surface, frame, destino, COLOR_ENEMIGO)
            else:
                surface.blit(frame, destino)
            return

        # Hit reaction tint overlay
        if self._hit_tint_timer > 0:
            size = (self.rect.width, self.rect.height)
            if (self._tint_surf is None
                    or self._tint_surf_size != size):
                self._tint_surf = pygame.Surface(size, pygame.SRCALPHA)
                self._tint_surf_size = size
            tint = self._tint_surf
            tint_alpha = int(min(255, (self._hit_tint_timer / max(self._hurt_timer * 0.6, 0.01)) * 120))
            tint.fill((*self._hit_tint_color, tint_alpha))
            surface.blit(tint, (screen_x, screen_y))

        # Fallback placeholder
        pygame.draw.rect(
            surface,
            (200, 0, 0),
            (screen_x, screen_y, self.rect.width, self.rect.height),
        )
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (screen_x, screen_y, self.rect.width, self.rect.height),
            1,
        )

    #: Alto de la barra de vida, y a cuántos píxeles por encima del enemigo se
    #: dibuja. Cuatro píxeles de alto es lo mínimo que se lee a esta escala.
    _HEALTH_BAR_H = 3
    _HEALTH_BAR_GAP = 6

    def _draw_health_bar(
        self, surface: pygame.Surface, screen_x: int, screen_y: int,
    ) -> None:
        """Barra de vida sobre el enemigo, sólo si ya ha recibido daño.

        AUD-091 — los enemigos normales no tenían ninguna
        --------------------------------------------------
        `BossBase` sí dibuja la suya, y el jugador tiene sus corazones en el
        HUD. Un enemigo corriente no tenía nada: la única señal de que un golpe
        había entrado era un destello de 0,09 s. Con un Walker de 3 puntos de
        vida y ataques de 0,5, hacen falta **seis impactos**, y durante los
        cinco primeros el jugador no tiene forma de saber si está avanzando o
        pegando al aire.

        La barra aparece **sólo tras el primer golpe**. A plena vida no aporta
        información y llenaría la pantalla de barras sobre enemigos intactos;
        en cuanto falta un punto, es exactamente lo que hace falta ver.
        """
        if self.max_health <= 0 or self.current_health >= self.max_health:
            return
        if not self.is_alive:
            return

        ancho = self.rect.width
        fraccion = max(0.0, min(1.0, self.current_health / self.max_health))
        y = screen_y - self._HEALTH_BAR_GAP

        # Fondo oscuro para que la barra se lea sobre cualquier terreno.
        pygame.draw.rect(surface, (28, 20, 24),
                         (screen_x - 1, y - 1, ancho + 2, self._HEALTH_BAR_H + 2))
        # El color pasa de verde a rojo con la vida restante, para que la
        # gravedad se lea sin contar píxeles.
        relleno = int(ancho * fraccion)
        color = (
            int(220 - 40 * fraccion),
            int(60 + 160 * fraccion),
            60,
        )
        if relleno > 0:
            pygame.draw.rect(surface, color,
                             (screen_x, y, relleno, self._HEALTH_BAR_H))

    # ──────────────────────────────────────────────
    # Public methods (provided, do not override)
    # ──────────────────────────────────────────────

    def apply_hit(
        self,
        damage: float,
        source_position: tuple[float, float],
        canal: str | None = None,
    ) -> None:
        """
        Apply damage to the enemy. No-op if invincibility is active
        or if already dying. Emits ENEMY_DIED on death.
        Hitstun type depends on damage amount:
          light  (< 0.8)  -> short stun, small knockback
          heavy  (>= 0.8) -> long stun, big knockback
          launch (>= 1.5) -> airborne knockback

        AUD-387 — `canal` es el tipo de daño, y entra **al final y opcional**
        porque este método tiene 32 llamantes y 26 están en `src/stages/`, o
        sea en entregas de estudiantes. Sin canal se aplica el físico, y sin
        `resistencias` declaradas la mitigación es 1,0: un enemigo que nadie
        toque se comporta exactamente igual que antes de este cambio.

        El aturdimiento sigue decidiéndose con el daño **ya mitigado**, que es
        lo coherente: si el veneno apenas le hace nada a un enemigo resistente,
        tampoco debería frenarlo como un mazazo.
        """
        if self._invincibility_timer > 0:
            return
        if self.state == EnemyState.DYING:
            return

        damage = combate_dano.mitigar(damage, canal, self.resistencias)
        self.current_health -= damage

        # AUD-064: el sonido de impacto tenía archivo, handler y hasta subtítulo
        # en `subtitle_overlay.py` — y nadie lo emitía. Golpear a un enemigo era
        # completamente mudo, y quien juega con subtítulos tampoco recibía nada.
        # Los jefes tienen su propio sonido, más grave.
        from src.framework.entities.boss_base import BossBase
        self._event_bus.emit(
            Events.SFX_BOSS_HIT if isinstance(self, BossBase)
            else Events.SFX_ENEMY_HIT,
        )

        # Determine hitstun type
        if damage >= 1.5:
            self._hitstun_type = "launch"
            self._hurt_timer = 0.5
            self._hit_tint_color = (255, 80, 80)
        elif damage >= 0.8:
            self._hitstun_type = "heavy"
            self._hurt_timer = 0.35
            self._hit_tint_color = (255, 200, 80)
        else:
            self._hitstun_type = "light"
            self._hurt_timer = 0.15
            self._hit_tint_color = (255, 255, 200)
        self._hit_tint_timer = self._hurt_timer * 0.6

        # Knockback direction from source
        dx = self.position.x - source_position[0]
        dir_x = 1 if dx >= 0 else -1
        kb_power = 80.0 if self._hitstun_type == "light" else 150.0
        # AUD-667 — los enemigos de suelo no deben salir del piso por HURT.
        # El impulso vertical hacía que `rect.bottom` subiera y, con la
        # resolución por colisión en flotantes, quedara despegado o con
        # deriva. Sólo LAUNCHED tiene impulso vertical real; HURT se limita
        # a retroceso horizontal. Los voladores (`_hug_slopes=False`) conservan
        # el impulso porque no pisan suelo.
        if self._hitstun_type == "launch":
            self._knockback_velocity.x = dir_x * kb_power * 0.5
            self._knockback_velocity.y = -250.0
        elif self._hitstun_type == "heavy":
            self._knockback_velocity.x = dir_x * kb_power
            self._knockback_velocity.y = -100.0 if not self._hug_slopes else 0.0
        else:
            self._knockback_velocity.x = dir_x * kb_power
            self._knockback_velocity.y = -30.0 if not self._hug_slopes else 0.0

        if self.current_health <= 0:
            self._die()
        else:
            # BUG-034 FIX: Set invincibility only if not dead
            self._invincibility_timer = self._invincibility_duration
            if self._hitstun_type == "launch":
                self._ground_y = self.position.y
                self._is_airborne = True
                self.state = EnemyState.LAUNCHED
            else:
                self.state = EnemyState.HURT

    def _die(self) -> None:
        """Handle death: set state, emit event, schedule removal."""
        self.state = EnemyState.DYING
        self._death_timer = 0.5
        self._flash_counter = 0.0
        self._flash_visible = True
        # AUD-636 — destello blanco de muerte: se emite ANTES de ENEMY_DIED
        # para que el destello llegue el mismo fotograma que la sangre.
        self._event_bus.emit(
            Events.VFX_KILL_FLASH,
            pos=(self.position.x, self.position.y),
        )
        # BUG-058 FIX: Reset _was_alive so revived enemies re-trigger on_enemy_died
        self._was_alive = True
        # BUG-031 FIX: Keep is_alive=True until death animation completes
        # is_alive will be set to False in _tick_cooldowns when _death_timer <= 0
        # AUD-238: la habilidad viaja en el evento. `BossBase.skill_drop` la
        # declara y `getattr` con reserva vacía la hace opcional — un enemigo
        # normal, o el de una entrega que no sepa de esto, no la lleva y la
        # escena no concede nada.
        #
        # AUD-263: pueden ser varias. `habilidades_que_suelta()` normaliza las
        # dos formas —`str` de siempre y lista nueva—; los enemigos normales no
        # tienen el método y caen a la lectura antigua, que es la que el
        # `getattr` de abajo ya hacía.
        sueltas = self.habilidades_que_suelta() if hasattr(
            self, "habilidades_que_suelta") else [str(getattr(self, "skill_drop", ""))]
        self._event_bus.emit(
            Events.ENEMY_DIED,
            entity_id=f"{type(self).__name__}_{id(self)}",
            position=(self.position.x, self.position.y),
            skill_drop=",".join(s for s in sueltas if s),
        )
        is_large = self.rect.width > 24 or self.rect.height > 28
        # AUD-489 — mismo `pos` que `ENEMY_DIED` dos líneas arriba: sin él,
        # `sonido.py._make_sfx_handler` cae al canal ciego (`_play_sfx_named`)
        # en vez del posicional (`_play_sfx_spatial`) que ya sabe usar cuando
        # el evento lo trae.
        self._event_bus.emit(
            Events.SFX_ENEMY_DIE_LARGE if is_large else Events.SFX_ENEMY_DIE_SMALL,
            pos=(self.position.x, self.position.y),
        )

    # ──────────────────────────────────────────────
    # Required overrides (abstract)
    # ──────────────────────────────────────────────

    @abstractmethod
    def _patrol_behavior(self, dt: float) -> None:
        """Default movement/AI when no player detected."""

    @abstractmethod
    def _alert_behavior(self, dt: float) -> None:
        """AI when player is within detection range."""

    def _firing_behavior(self, dt: float) -> None:
        """AI during FIRING state. Default: return to ALERT."""
        self.state = EnemyState.ALERT

    @abstractmethod
    def _get_animation_key(self) -> str:
        """Return animation key for the current non-DYING, non-HURT state."""

    @abstractmethod
    def _build_hurtbox(self) -> pygame.Rect:
        """Returns LOCAL-space rect (offset from entity position)."""

    # ──────────────────────────────────────────────
    # AUD-108 — cajas que no se salen del cuerpo
    # ──────────────────────────────────────────────

    def caja_ajustada(self, margen_x: int = 0, margen_y: int = 0) -> pygame.Rect:
        """Caja local recortada hacia dentro del cuerpo, y centrada.

        **Por qué existe.** `_build_hurtbox` devuelve coordenadas locales que
        `_update_rects` suma a la posición. Diez de los doce cuerpos del
        bestiario declaraban un desplazamiento **sin encoger el tamaño**::

            EnemyWalker:  cuerpo 24 × 28   →   Rect(4, 2, 24, 28)

        Eso no es una caja ajustada: es el cuerpo entero movido 4 px a la
        derecha y 2 hacia abajo. En un `Flying` de 20 px de ancho el
        desplazamiento era de 6, así que **el 30 % de su cuerpo visible no se
        podía golpear** por la izquierda, y había 6 px de aire a su derecha que
        sí golpeaban. En un `Shooter` la caja sobresalía 12 px: daño de un
        enemigo que no está ahí.

        Y como todos los desplazamientos iban hacia la derecha, atacar por la
        izquierda era sistemáticamente más difícil en los catorce escenarios.

        **Cómo se evita que vuelva.** Aquí se calcula el rectángulo a partir
        del cuerpo en vez de escribirlo a mano, así que el margen es un margen
        de verdad y no puede convertirse en un desplazamiento por descuido. Los
        márgenes se recortan si son mayores que el cuerpo: una caja de área
        cero es un enemigo invulnerable, y prefiero uno estrecho a uno
        intocable.

        El jugador ya lo hacía bien —misma anchura, sólo recorte vertical— y de
        ahí se dedujo cuál era la intención de todos estos.
        """
        ancho = max(2, self.rect.width - margen_x * 2)
        alto = max(2, self.rect.height - margen_y * 2)
        return pygame.Rect(
            (self.rect.width - ancho) // 2,
            (self.rect.height - alto) // 2,
            ancho,
            alto,
        )

    # ──────────────────────────────────────────────
    # Concrete hooks with sensible defaults
    # ──────────────────────────────────────────────

    def _get_animation_state(self) -> str:
        """
        TEMPLATE METHOD: fixed mapping for DYING/HURT states;
        subclasses provide _get_animation_key() for the rest.
        """
        if self.state == EnemyState.DYING:
            return "die"
        if self.state == EnemyState.HURT:
            return "hurt"
        return self._get_animation_key()

    def _face_player(self) -> None:
        """Face toward the player's horizontal position."""
        if self._player_ref is not None:
            self.facing_direction = (
                1 if self._player_ref.centerx >= self.rect.centerx else -1
            )

    # ──────────────────────────────────────────────
    # Provided methods (do not override)
    # ──────────────────────────────────────────────

    _INV_FLASH_INTERVAL: float = 4.0 / 60.0

    def set_collision_rects(
        self,
        rects: list[pygame.Rect],
        one_way: list[pygame.Rect] | None = None,
    ) -> None:
        """Store collision rects for Y-snapping and movement."""
        self._collision_rects = rects
        self._one_way_rects = one_way if one_way is not None else []

    def set_pendientes(self, pendientes: list) -> None:
        """Suelo inclinado que el enemigo respeta — AUD-325.

        Vacía por defecto: ningún mapa entregado tiene pendientes, y el paso
        entero se salta (la condición de siempre para no tocar nada).
        """
        self._pendientes = pendientes

    def _resolver_pendientes(self) -> None:
        """Pies pegados a la hipotenusa y freno lateral — AUD-325.

        Los enemigos no tienen gravedad propia: andan sobre suelo llano a la
        altura a la que se colocaron. Con pendientes, la misma geometría del
        jugador los mantiene sobre la cuesta (subiendo y bajando) y les
        cierra la cara empinada, sin tocar la física de las subclases.
        """
        if not self._pendientes or not self._hug_slopes:
            return
        from src.framework.stage.pendientes import resolver, resolver_lateral

        rect = pygame.Rect(int(self.position.x), int(self.position.y),
                           self.rect.width, self.rect.height)
        x = resolver_lateral(rect, self._pendientes)
        if x is not None:
            self.position.x = x
            rect.x = int(x)
        superficie = resolver(rect, 0.0, True, self._pendientes)
        if superficie is not None:
            self.position.y = float(superficie) - self.rect.height

    def _mantener_en_suelo(self) -> None:
        """Mantiene `rect.bottom` anclado al suelo plano (AUD-667)."""
        if not self._hug_slopes:
            return
        if self.state in (EnemyState.LAUNCHED, EnemyState.DYING):
            return
        if self._is_airborne:
            return
        todos = self._collision_rects + self._one_way_rects
        if not todos:
            return
        feet_y = self.position.y + self.rect.height
        cx = self.rect.centerx
        for r in todos:
            if r.left < cx < r.right:
                if abs(feet_y - r.top) <= 2.0 or (r.top <= feet_y < r.bottom):
                    self.position.y = float(r.top - self.rect.height)
                    self.rect.y = int(self.position.y)
                    self._knockback_velocity.y = 0.0
                    self._update_rects()
                    break
                if feet_y > r.top and feet_y - r.top < 4.0:
                    self.position.y = float(r.top - self.rect.height)
                    self.rect.y = int(self.position.y)
                    self._knockback_velocity.y = 0.0
                    self._update_rects()
                    break

    def _update_invincibility(self, dt: float) -> None:
        """Tick down invincibility timer and toggle flash."""
        if self._invincibility_timer > 0:
            self._invincibility_timer -= dt
            self._flash_counter += dt
            if self._flash_counter >= self._INV_FLASH_INTERVAL:
                self._flash_counter -= self._INV_FLASH_INTERVAL
                self._flash_visible = not self._flash_visible
        else:
            self._flash_visible = True
            self._flash_counter = 0.0
        if self._hit_tint_timer > 0:
            self._hit_tint_timer -= dt
        else:
            self._hit_tint_timer = 0.0

    @abstractmethod
    def _build_hitbox(self) -> pygame.Rect:
        """Returns LOCAL-space rect for the enemy's active damage zone."""

    def _check_player_contact(self, player: Player) -> None:
        """
        Check if this enemy's hurtbox overlaps the player's hurtbox.
        If so, deal contact damage (respecting cooldown).
        Respects player parry — parried enemies get deflected.
        player: Player — imported locally to avoid circular imports.
        """
        if not self.is_alive or self.state == EnemyState.DYING:
            return
        if self._contact_cooldown > 0:
            return
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        if self.hurtbox.colliderect(player_hurtbox):
            # Parry check — deflect the enemy instead of taking damage
            if getattr(player, "_parry_active", False) and getattr(player, "_parry_window", 0) > 0:
                dx = self.position.x - player.position.x
                dir_x = 1 if dx >= 0 else -1
                self._knockback_velocity.x = dir_x * 200.0
                # AUD-667 — en suelo el parry no levanta al enemigo (mismo
                # motivo que `apply_hit`); el retroceso es horizontal.
                self._knockback_velocity.y = -150.0 if not self._hug_slopes else 0.0
                self._hurt_timer = 0.3  # sólo el tinte del golpe, no el estado
                # AUD-206: aquí ponía `state = HURT`, y HURT es el estado en el
                # que cae el enemigo con un golpe normal — sale de él directo a
                # ALERT. Es decir: parar, la acción más difícil del juego,
                # devolvía exactamente lo mismo que esquivar y costaba una
                # ventana de 0,2 s de precisión. `stun()` y la rama STUNNED
                # llevaban desde AUD-051 escritas y sin un solo llamante en
                # producción; esta línea es la que las conecta. STUNNED sale a
                # RECOVER, así que un parry acertado abre ventana de castigo.
                self.stun(self._aturdimiento_por_parry())
                player._parry_success = True
                player._parry_active = False
                player._parry_window = 0.0
                self._event_bus.emit(Events.VFX_PARRY, pos=(self.position.x, self.position.y))
                # AUD-064: parar es la acción más difícil del juego y era muda.
                # AUD-489 — mismo `pos` que el efecto visual de la línea de
                # arriba, para que el sonido venga del mismo sitio que el destello.
                self._event_bus.emit(Events.SFX_PLAYER_PARRY, pos=(self.position.x, self.position.y))
                self._contact_cooldown = 0.3
                return
            player.apply_damage(
                self.damage_on_contact,
                self.rect.center,
                self.contact_knockback,
            )
            self._contact_cooldown = 0.3

    def check_player_contact(self, player: Player) -> None:
        """Deprecated alias for _check_player_contact."""
        warnings.warn(
            "check_player_contact is deprecated, use _check_player_contact instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self._check_player_contact(player)

    def _escalar_local(self, caja: pygame.Rect) -> pygame.Rect:
        """Gancho de escalado de cajas locales. Identidad por defecto.

        AUD-606 — las subclases que cambian de tamaño en juego (jefes con
        `escala` por fase) sobreescriben esto para que sus hitbox y hurtbox
        sigan al cuerpo. Sin el gancho, las cajas se construían con los
        offsets crudos del sprite base y un jefe ×1.25 pegaba y recibía
        golpes en el cuerpo que tenía antes de crecer.
        """
        return caja

    def _update_rects(self) -> None:
        """Recompute hitbox and hurtbox world positions from local offsets."""
        local_hitbox = self._escalar_local(self._build_hitbox())
        local_hurtbox = self._escalar_local(self._build_hurtbox())

        self.hitbox = pygame.Rect(
            self.position.x + local_hitbox.x,
            self.position.y + local_hitbox.y,
            local_hitbox.width,
            local_hitbox.height,
        )
        self.hurtbox = pygame.Rect(
            self.position.x + local_hurtbox.x,
            self.position.y + local_hurtbox.y,
            local_hurtbox.width,
            local_hurtbox.height,
        )

        # Update main rect
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

    def _tick_cooldowns(self, dt: float) -> None:
        """Tick contact cooldown and hurt/death timers."""
        if self._contact_cooldown > 0:
            self._contact_cooldown -= dt
        if self._hurt_timer > 0:
            self._hurt_timer -= dt
        if self._death_timer > 0:
            self._death_timer -= dt
            if self._death_timer <= 0:
                self.is_alive = False
                self.is_active = False

    # ──────────────────────────────────────────────
    # State machine runner
    # ──────────────────────────────────────────────

    def _run_state_machine(self, dt: float) -> None:
        """
        Evaluate current state and dispatch to the appropriate behavior.
        Priority: DYING > LAUNCHED > HURT > TELEGRAPHING > FIRING > ALERT > PATROL
        Deaggro hysteresis: once ALERT, player must leave detection range
        + deaggro_margin to return to PATROL.
        """
        if self.state == EnemyState.DYING:
            return

        if self.state == EnemyState.LAUNCHED:
            self._knockback_velocity.y += 600.0 * dt  # gravity during launch
            # AUD-667 — sólo aterrizar cuando se va cayendo y se alcanzó el
            # suelo; antes se comprobaba `y >= ground` incluso subiendo y en
            # el primer fotograma `y == ground`, lo que anulaba el impulso
            # de lanzamiento y dejaba al enemigo pegado.
            if self._knockback_velocity.y >= 0 and self.position.y >= self._ground_y:
                self.position.y = self._ground_y
                self._knockback_velocity.y = 0.0
                self._knockback_velocity.x = 0.0
                self._is_airborne = False
                if self._hurt_timer <= 0:
                    if self._check_detection_range():
                        self.state = EnemyState.ALERT
                    else:
                        self.state = EnemyState.PATROL
            return

        if self.state == EnemyState.HURT:
            # Fix reporte Guillermo 5: HURT también cae, si no un impulso
            # hacia arriba lo deja flotando (Shooter con gravity=0).
            # Se aplica la misma gravedad que en LAUNCHED pero sin el lock
            # de suelo de LAUNCHED: caemos con _apply_knockback + gravedad
            # y dejamos que _resolver_pendientes/_apply_knockback haga el resto.
            # Solo si no tiene gravedad propia (HURT no mueve, así que no
            # compensa duplicar si la subclase ya integra gravedad).
            # AUD-667 — los enemigos de suelo no tienen caída en HURT porque
            # su velocidad vertical es 0 (ver `apply_hit`); aplicar gravedad
            # aquí los hundiría y la corrección por colisión dejaría deriva.
            if self._hug_slopes and not self._is_airborne:
                self._knockback_velocity.y = 0.0
            elif self._knockback_velocity.y < 500.0:
                self._knockback_velocity.y += 600.0 * dt
            if self._hurt_timer <= 0:
                if self._check_detection_range():
                    self.state = EnemyState.ALERT
                else:
                    self.state = EnemyState.PATROL
            return

        if self.state == EnemyState.TELEGRAPHING:
            self._telegraph_timer -= dt
            if self._telegraph_timer <= 0:
                self.state = EnemyState.FIRING
                self._firing_behavior(dt)
            return

        if self.state == EnemyState.FIRING:
            self._firing_behavior(dt)
            return

        # STUNNED: indefenso. Prioridad alta a propósito — una parada acertada
        # debe interrumpir cualquier plan del enemigo, o parar deja de valer.
        if self.state == EnemyState.STUNNED:
            self._stun_timer -= dt
            if self._stun_timer <= 0:
                self.state = EnemyState.RECOVER
                self._recover_timer = self.RECOVER_DURATION
            return

        # RECOVER: ventana de castigo tras atacar. Sin esto el enemigo puede
        # cadenar ataques sin pausa y no hay hueco para responder (AUD-051).
        if self.state == EnemyState.RECOVER:
            self._recover_timer -= dt
            self._recover_behavior(dt)
            if self._recover_timer <= 0:
                self.state = (
                    EnemyState.CHASE if self._check_detection_range()
                    else EnemyState.SEARCH
                )
            return

        # RETREAT: se repliega mientras siga con poca vida y el jugador cerca.
        if self.state == EnemyState.RETREAT:
            self._retreat_behavior(dt)
            if not self._should_retreat():
                self.state = (
                    EnemyState.CHASE if self._check_detection_range()
                    else EnemyState.PATROL
                )
            return

        player_in_range = self._check_detection_range()

        if player_in_range:
            self._last_seen = pygame.Vector2(
                self._player_ref.centerx, self._player_ref.centery,
            )
            self._search_timer = self.SEARCH_DURATION
            if self._should_retreat():
                self.state = EnemyState.RETREAT
                self._retreat_behavior(dt)
            else:
                # ALERT es el primer fotograma de detección; a partir de ahí es
                # CHASE. Separarlos permite un sonido y una animación de "te vi"
                # que telegrafían la agresión antes de que llegue.
                self.state = (
                    EnemyState.CHASE if self.state in (EnemyState.ALERT, EnemyState.CHASE)
                    else EnemyState.ALERT
                )
                self._alert_behavior(dt)
            return

        if self.state in (EnemyState.ALERT, EnemyState.CHASE):
            # Histéresis de desenganche: el jugador debe salir del rango
            # ampliado antes de que el enemigo deje de perseguir.
            if self._player_in_range(self._player_ref, margin=self._deaggro_margin):
                self.state = EnemyState.CHASE
                self._alert_behavior(dt)
            else:
                self.state = EnemyState.SEARCH
                self._search_timer = self.SEARCH_DURATION
                self._search_behavior(dt)
            return

        if self.state == EnemyState.SEARCH:
            self._search_timer -= dt
            self._search_behavior(dt)
            if self._search_timer <= 0:
                self.state = self._resting_state()
            return

        self.state = self._resting_state()
        if self.state == EnemyState.IDLE:
            self._idle_behavior(dt)
        else:
            self._patrol_behavior(dt)

    # ── nuevos estados: duraciones y comportamiento por defecto ──

    #: Cuánto sigue buscando el enemigo tras perder de vista al jugador.
    SEARCH_DURATION: float = 3.0
    #: Ventana de vulnerabilidad tras un ataque.
    RECOVER_DURATION: float = 0.45
    #: Vida por debajo de la cual un enemigo se repliega, como fracción.
    RETREAT_HEALTH_FRACTION: float = 0.25
    #: Cuánto queda aturdido un enemigo al que le paran un ataque (AUD-206).
    #: Tiene que ser holgadamente mayor que los 0,3 s de HURT que había antes,
    #: o parar sigue costando más precisión de la que devuelve. Las subclases
    #: la suben para los enemigos pesados y la bajan para los ágiles.
    PARRY_STUN_DURATION: float = 0.9

    def _resting_state(self) -> EnemyState:
        """IDLE si el enemigo es estacionario, PATROL si tiene ruta.

        Un enemigo con `patrol_length` 0 estaba antes en PATROL recorriendo cero
        píxeles, lo que hacía imposible distinguir "quieto por diseño" de
        "quieto porque algo falla".

        El valor por defecto del `getattr` es **positivo** a propósito. Con 0.0
        como reserva, cualquier enemigo que no use `patrol_length` —todos los
        voladores, que se mueven por estrategia de vuelo— caía en IDLE y dejaba
        de moverse por completo. Lo detectó
        ``test_sine_reverses_at_boundary``: la ausencia del atributo significa
        "esta clase no se rige por longitud de patrulla", no "está quieta".

        AUD-660 — reportado como “default positivo debería ser IDLE”; no se
        cambia: voladores sin patrol_length deben seguir en PATROL (su lógica
        de vuelo no usa longitud de patrulla). Verificado por test_sine.
        """
        if not hasattr(self, "patrol_length"):
            return EnemyState.PATROL
        # pylint: disable=no-member  # el hasattr de arriba es la comprobación
        return (
            EnemyState.IDLE
            if float(self.patrol_length) <= 0.0
            else EnemyState.PATROL
        )

    def _should_retreat(self) -> bool:
        max_hp = float(self.max_health) or 1.0
        return (self.current_health / max_hp) <= self.RETREAT_HEALTH_FRACTION

    def stun(self, duration: float = 0.8) -> None:
        """Aturde al enemigo. La llama una parada o un golpe pesado.

        AUD-206: LAUNCHED se suma a la guarda. Un enemigo por los aires tiene
        su propia rama con gravedad y aterrizaje; meterlo en STUNNED lo dejaba
        congelado a media altura. La guarda vivía duplicada en el bloque de
        parry de `_check_player_contact`; está mejor aquí, donde alcanza
        también a quien llame a `stun()` desde una entrega.
        """
        if self.state in (EnemyState.DYING, EnemyState.LAUNCHED):
            return
        self._cancelar_ataque_en_curso()
        self._stun_timer = max(self._stun_timer, duration)
        self.state = EnemyState.STUNNED

    def _aturdimiento_por_parry(self) -> float:
        """Cuánto dura el aturdimiento de un parry acertado (AUD-243).

        Por defecto, la constante de la clase. Existe como gancho porque los
        jefes tienen su propia mecánica de desvío —`BossAttack.parriable`, con
        un `aturde_al_parry` por ataque— y su punto de entrada,
        `BossBase.recibir_parry()`, **no tenía un solo llamante**. Toda la
        cadena estaba escrita y desconectada justo por arriba, que es el modo
        de fallo de este repositorio.
        """
        return self.PARRY_STUN_DURATION

    def _cancelar_ataque_en_curso(self) -> None:
        """Gancho: abandonar el ataque a medias al ser aturdido (AUD-239).

        No hace nada por defecto. Lo sobreescriben los enemigos que llevan su
        propia máquina de ataque en banderas —`EnemyCharger`, `EnemyWalker`—
        porque `stun()` sólo cambia el estado de la base y esas banderas
        sobreviven al aturdimiento: al volver a ALERT, el enemigo **reanudaba
        la misma embestida** contra el jugador que se había acercado a
        castigarle. Parar salía peor que no parar.

        Si tu enemigo guarda «estoy atacando» fuera de `EnemyState`, límpialo
        aquí. Se llama después de la guarda, así que un cadáver no lo recibe.
        """

    def set_arena_bounds(self, bounds: pygame.Rect) -> None:
        """Define los límites dentro de los que el enemigo puede moverse (AUD-615).

        La escena lo llama con la zona de arena declarada en el TMX (ArenaZone).
        Si no se llama, el enemigo no tiene límites de arena (compatibilidad
        hacia atrás con entregas existentes).
        """
        self.arena_bounds = pygame.Rect(bounds)

    def clamp_to_arena(self, margin: int = 16) -> None:
        """Devuelve al enemigo dentro de su arena si se ha salido (AUD-615).

        Se aplica a position y rect a la vez para evitar un fotograma de
        desincronización que usen las comprobaciones de colisión.
        """
        if self.arena_bounds is None:
            return
        left = self.arena_bounds.left + margin
        right = self.arena_bounds.right - margin - self.rect.width
        if right < left:  # arena más estrecha que el enemigo: se centra
            left = right = self.arena_bounds.centerx - self.rect.width // 2
        self.position.x = max(left, min(self.position.x, right))
        self.rect.x = int(self.position.x)

    def begin_recovery(self, duration: float | None = None) -> None:
        """Entra en la ventana de castigo. La llaman los estados de ataque."""
        if self.state == EnemyState.DYING:
            return
        self._recover_timer = duration if duration is not None else self.RECOVER_DURATION
        self.state = EnemyState.RECOVER

    def _idle_behavior(self, dt: float) -> None:
        """Quieto. Las subclases pueden añadir un vaivén o mirar alrededor."""

    def _search_behavior(self, dt: float) -> None:
        """Avanza hacia el último punto donde se vio al jugador.

        Deliberadamente simple: sin pathfinding. Un enemigo que camina hacia
        donde te vio por última vez ya comunica "te está buscando", y eso es lo
        que hace que romper la línea de visión sea una decisión táctica.
        """
        if self._last_seen is None:
            return
        dx = self._last_seen.x - self.position.x
        if abs(dx) < 4.0:
            return
        self.facing_direction = 1 if dx > 0 else -1
        speed = float(getattr(self, "patrol_speed", 40.0))
        self.position.x += self.facing_direction * speed * dt
        self.rect.x = int(self.position.x)
        # AUD-615: acotar a la arena si existe
        self.clamp_to_arena()

    def _recover_behavior(self, dt: float) -> None:
        """Sin movimiento durante la recuperación: es la ventana de castigo."""

    def _retreat_behavior(self, dt: float) -> None:
        """Se aleja del jugador sin darle la espalda."""
        if self._player_ref is None:
            return
        dx = self._player_ref.centerx - self.rect.centerx
        self.facing_direction = 1 if dx > 0 else -1
        speed = float(getattr(self, "alert_speed", 60.0)) * 0.8
        self.position.x -= self.facing_direction * speed * dt
        self.rect.x = int(self.position.x)
        # AUD-615: acotar a la arena si existe
        self.clamp_to_arena()

    def set_player_ref(self, player_rect: pygame.Rect) -> None:
        """Set or update the reference to the player's rect for detection."""
        self._player_ref = player_rect

    def _check_detection_range(self) -> bool:
        """
        Check if player is within detection range.
        Returns True if player is close enough.
        """
        if self._player_ref is None:
            return False
        return self._player_in_range(self._player_ref)

    def _player_in_range(
        self, player_rect: pygame.Rect | None = None, margin: float = 0.0
    ) -> bool:
        """
        Check if the given player rect is within detection range.
        Optional margin extends the detection zone (for deaggro hysteresis).
        Called by stage code.
        """
        pr = player_rect if player_rect is not None else self._player_ref
        if pr is None:
            return False
        dx = abs(pr.centerx - self.rect.centerx)
        dy = abs(pr.centery - self.rect.centery)
        return (
            dx <= self.detection_range_x + margin
            and dy <= self.detection_range_y + margin
        )
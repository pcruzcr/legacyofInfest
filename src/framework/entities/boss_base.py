from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
import pygame

from src.engine.core.event_bus import emit
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_base import EnemyBase, EnemyState
from src.framework.processing.filter_tools import FilterTools


@dataclass
class BossPhase:
    """Definition of a single boss phase."""

    phase_index: int
    health_threshold: float
    attack_patterns: list[str] = field(default_factory=list)
    movement_type: str = "stationary"
    speed_multiplier: float = 1.0
    sprite_override: str | None = None
    filter_effect: str | None = None


_APPLY_FILTER_EVERY_N_FRAMES = 5


class BossBase(EnemyBase):
    """
    Base class for all boss entities. Extends EnemyBase with phase management,
    phase transition protocol, and boss HUD integration.

    Subclasses define phases; this class handles health threshold checks,
    transition animation, and BOSS_PHASE_CHANGED event emission.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 20.0,
        damage_on_contact: float = 1.0,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            contact_knockback=0.0,
        )

        self.phases: list[BossPhase] = []
        self.current_phase: int = 0
        self.phase_health_thresholds: list[float] = []
        self.is_transitioning: bool = False
        self.transition_timer: float = 0.0
        self._phase_max_health: float = max_health
        self._boss_name: str = "BOSS"
        self._filter_frame: int = 0
        self._boss_sprite_prefix: str = ""

    def _load_boss_sprites(
        self, prefix: str, fw: int = 48, fh: int = 48,
    ) -> None:
        """Load boss sprites from assets/sprites/bosses/{prefix}_{name}.png."""
        from pathlib import Path
        base = Path("assets/sprites/bosses")
        self._boss_sprite_prefix = prefix
        self._sprite_fw = fw
        self._sprite_fh = fh
        for anim_key in ("drift", "hurt", "charge", "stomp", "vine", "death"):
            path = base / f"{prefix}_{anim_key}.png"
            try:
                frames = AssetLoader.load_sprite_sheet(path, fw, fh)
                self._sprite_frames[anim_key] = frames
            except Exception:
                pass

    def set_phases(self, phases: list[BossPhase]) -> None:
        """Set the phase list and extract health thresholds."""
        self.phases = phases
        self.phase_health_thresholds = [p.health_threshold for p in phases]

    def set_boss_name(self, name: str) -> None:
        self._boss_name = name

    @property
    def boss_name(self) -> str:
        return self._boss_name

    @property
    def phase_count(self) -> int:
        return len(self.phases) if self.phases else 1

    def _get_animation_state(self) -> str:
        """Boss-specific animation mapping: uses 'death' instead of 'die'."""
        if self.state == EnemyState.DYING:
            return "death"
        if self.state == EnemyState.HURT:
            return "hurt"
        return self._get_animation_key()

    def _get_animation_key(self) -> str:
        """Return the sprite animation key for the current non-DYING/HURT state."""
        return "drift"

    def apply_hit(
        self,
        damage: float,
        source_position: tuple[float, float],
    ) -> None:
        if not self.is_alive or self.is_transitioning:
            return
        if self._invincibility_timer > 0:
            return
        super().apply_hit(damage, source_position)

        if self.is_alive:
            self._check_phase_transition()

    def _check_phase_transition(self) -> None:
        """Check if health dropped below the next phase threshold."""
        if self.current_phase >= len(self.phase_health_thresholds) - 1:
            return
        next_threshold = self.phase_health_thresholds[self.current_phase + 1]
        if self.current_health <= next_threshold:
            self._start_phase_transition()

    def _start_phase_transition(self) -> None:
        """Begin phase transition: invincible, timer starts."""
        self.is_transitioning = True
        self._invincibility_timer = float("inf")
        self.transition_timer = 2.5

    def _finish_phase_transition(self) -> None:
        """Complete phase transition: advance phase, emit event."""
        self.current_phase += 1
        self.is_transitioning = False
        self._invincibility_timer = 0.0

        phase = self.phases[self.current_phase]
        if phase.speed_multiplier != 1.0:
            pass

        # Update phase max health to current threshold for HUD bar
        if self.current_phase < len(self.phase_health_thresholds):
            self._phase_max_health = self.phase_health_thresholds[self.current_phase]
        self.current_health = self._phase_max_health

        emit(
            Events.BOSS_PHASE_CHANGED,
            boss_name=self._boss_name,
            phase=self.current_phase,
            phase_count=self.phase_count,
            new_max_health=self._phase_max_health,
        )

    def _pre_update(self, dt: float) -> bool:
        """Handle phase transitions. Return True to skip normal update."""
        if self.is_transitioning:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self._finish_phase_transition()
            return True

        # Load phase-specific speed multiplier on phase properties
        if self.phases and self.current_phase < len(self.phases):
            self.phases[self.current_phase]

        return False

    def _apply_filter(self, frame: pygame.Surface) -> pygame.Surface:
        """Apply the current phase's filter effect to a sprite frame."""
        if not self.phases or self.current_phase >= len(self.phases):
            return frame
        if self._filter_frame % _APPLY_FILTER_EVERY_N_FRAMES != 0:
            return frame
        phase = self.phases[self.current_phase]
        effect = phase.filter_effect
        if effect is None:
            return frame
        if effect == "sobel":
            return FilterTools.sobel_edge(frame)
        if effect == "sobel_x":
            k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
            return FilterTools.apply_kernel(frame, k)
        return frame

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        if not self.is_visible or not self.is_alive:
            return

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        # Try sprite rendering with filter effects
        anim_key = self._get_animation_state()
        frames = self._sprite_frames.get(anim_key)
        if frames:
            frame_idx = min(self._animation_frame, len(frames) - 1)
            frame = frames[frame_idx]
            if self.facing_direction < 0:
                frame = pygame.transform.flip(frame, True, False)
            if self.is_transitioning:
                overlay = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                overlay.fill((200, 200, 0, 80))
                frame.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                frame = self._apply_filter(frame)
            ox = (self.rect.width - self._sprite_fw) // 2
            oy = self.rect.height - self._sprite_fh
            surface.blit(frame, (screen_x + ox, screen_y + oy))
            return

        # Fallback placeholder
        color = (120, 40, 140) if not self.is_transitioning else (200, 200, 0)
        pygame.draw.rect(
            surface,
            color,
            (screen_x, screen_y, self.rect.width, self.rect.height),
        )
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (screen_x, screen_y, self.rect.width, self.rect.height),
            1,
        )

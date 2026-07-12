from __future__ import annotations

import pygame

from src.engine.core import settings

LEARNING_PANELS: dict[int, dict[str, object]] = {
    pygame.K_F2: {
        "title": "Math Concepts [F2]",
        "color": (100, 200, 255),
        "lines": [
            "Vectors: position, velocity, acceleration",
            "  - Player pos/vel uses Vector2 math",
            "  - Enemy projectiles use atan2 for aiming",
            "Trigonometry: sin/cos for wave motion",
            "  - Flying enemy uses sine path",
            "  - Water effect uses sine waves",
            "Interpolation: lerp for smooth motion",
            "  - Camera follow uses lerp",
            "  - Cutscene camera moves lerp",
        ],
    },
    pygame.K_F3: {
        "title": "Physics [F3]",
        "color": (150, 255, 150),
        "lines": [
            "Gravity: GRAVITY * gravity_multiplier",
            "  - Current GRAVITY = 980 px/s^2",
            "  - Gravity multiplier: stage-defined",
            "Jump: instant velocity impulse",
            "  - Jump velocity: -280 px/s",
            "  - Coyote time: 4 frames after ledge",
            "Max fall speed: clamped per state",
            "  - Normal: 400 px/s",
            "  - Wall slide: 200 px/s (reduced)",
            "Drag/Deceleration: ground vs air",
        ],
    },
    pygame.K_F4: {
        "title": "Collision [F4]",
        "color": (255, 200, 100),
        "lines": [
            "AABB Axis-Separated Resolution:",
            "  1. Integrate X → resolve X overlap",
            "  2. Integrate Y → resolve Y overlap",
            "  - Each axis only sees its own error",
            "One-way platforms: passable from below",
            "  - Only resolve when feet <= platform top",
            "Broad-phase: rect list iteration",
            "  - Narrow-phase: per-rect colliderect",
            "Contact damage: hurtbox overlap check",
        ],
    },
    pygame.K_F5: {
        "title": "State Machines [F5]",
        "color": (255, 150, 200),
        "lines": [
            "Player has 22 state classes:",
            "  - IDLE, RUNNING, JUMPING, FALLING",
            "  - ATTACKING, DASHING, CROUCHING",
            "  - HURT, DYING, SWIMMING, WALL_SLIDE",
            "  - And more (see PlayerState enum)",
            "Enemy base FSM: PATROL→ALERT→HURT→DYING",
            "  - Subclasses add states (CHARGE, FIRING)",
            "State transitions: priority-ordered",
            "  - DYING > HURT > ALERT > PATROL",
        ],
    },
    pygame.K_F6: {
        "title": "Rendering [F6]",
        "color": (200, 180, 255),
        "lines": [
            "Draw pipeline order:",
            "  1. Background fill (sky color)",
            "  2. Parallax layers (far/mid/near)",
            "  3. Tile map (BG layers, terrain, FG)",
            "  4. Weather / Ambient particles",
            "  5. Entities (depth-sorted by Y)",
            "  6. VFX (particles, damage numbers)",
            "  7. UI (message box, banner, HUD)",
            "  8. Lighting + Post-processing",
            "Parallax: each BG layer scrolls at",
            "  different speed relative to camera",
        ],
    },
    pygame.K_F7: {
        "title": "Audio [F7]",
        "color": (255, 200, 200),
        "lines": [
            "Audio layers (AudioManager):",
            "  - Music: single track or dynamic",
            "  - Dynamic: calm + combat crossfade",
            "  - SFX: one-shot from SoundBank",
            "  - Ambient: looped (wind, rain, etc.)",
            "  - Stinger: short overlay on music",
            "Dynamic intensity: 0.0 (calm) → 1.0",
            "  - Controlled by boss/enemy presence",
            "Spatial audio: stereo pan by world X",
        ],
    },
    pygame.K_F8: {
        "title": "Performance [F8]",
        "color": (255, 255, 150),
        "lines": [
            "FPS: target 60 (uncapped)",
            "Entity count: varies by stage",
            "  - Player: 1",
            "  - Enemies: stage-defined",
            "  - Projectiles: per-shooter (max 3-5)",
            "Particle count:",
            "  - Weather: rate-based spawn + decay",
            "  - VFX: burst-based (attack, death)",
            "Collision rects: stage-defined from TMX",
            "Light sources: 2D with per-pixel alpha",
        ],
    },
    pygame.K_F9: {
        "title": "Controls [F9]",
        "color": (200, 200, 200),
        "lines": [
            "Movement: LEFT/RIGHT or A/D",
            "Jump: SPACE or UP/W",
            "Crouch: DOWN/S",
            "Short attack: Z or J",
            "Long attack: X or K (hold to charge)",
            "Dash: SHIFT or L-ALT",
            "Parry: Attack + Crouch together",
            "Pause: ESC or P",
            "Debug: F1 (collision/hitbox overlay)",
            "Learning panels: F2-F10 toggle",
        ],
    },
    pygame.K_F10: {
        "title": "Learning Mode Help [F10]",
        "color": (255, 220, 150),
        "lines": [
            "F1: Debug overlay (hitboxes, info)",
            "F2: Math Concepts (vectors, trig)",
            "F3: Physics (gravity, velocity)",
            "F4: Collision (AABB resolution)",
            "F5: State Machines (FSM patterns)",
            "F6: Rendering (draw pipeline)",
            "F7: Audio (music, SFX, ambient)",
            "F8: Performance (FPS, counts)",
            "F9: Controls reference",
            "F10: This panel",
            "Press same F-key again to close panel.",
        ],
    },
}


class LearningOverlay:
    """Educational overlay panels toggled with F2-F10 during gameplay."""

    def __init__(self) -> None:
        self._active_key: int | None = None
        self._font = pygame.font.Font(None, 14)
        self._title_font = pygame.font.Font(None, 18)

    def toggle(self, key: int) -> None:
        if self._active_key == key:
            self._active_key = None
        elif key in LEARNING_PANELS:
            self._active_key = key

    def hide(self) -> None:
        self._active_key = None

    @property
    def active(self) -> bool:
        return self._active_key is not None

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        if self._active_key is None:
            return
        panel = LEARNING_PANELS.get(self._active_key)
        if panel is None:
            return

        title: str = panel["title"]
        color: tuple[int, int, int] = panel["color"]
        lines: list[str] = panel["lines"]

        line_h = 16
        title_h = 22
        pad = 10
        max_line_w = max(self._font.size(l)[0] for l in lines) if lines else 200
        panel_w = max(max_line_w + pad * 2, self._title_font.size(title)[0] + pad * 2)
        total_h = title_h + len(lines) * line_h + pad * 2
        panel_w = min(panel_w, settings.INTERNAL_WIDTH - 40)

        box = pygame.Surface((panel_w, total_h), pygame.SRCALPHA)
        box.fill((0, 0, 0, 210))
        pygame.draw.rect(box, (*color, 200), (0, 0, panel_w, total_h), 2, border_radius=3)

        title_surf = self._title_font.render(title, True, color)
        box.blit(title_surf, (pad, pad))

        for i, line in enumerate(lines):
            txt = self._font.render(line, True, (220, 220, 220))
            box.blit(txt, (pad, pad + title_h + i * line_h))

        bx = (settings.INTERNAL_WIDTH - panel_w) // 2
        by = (settings.INTERNAL_HEIGHT - total_h) // 2
        surface.blit(box, (bx, by))

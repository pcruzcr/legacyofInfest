---
document_id: "LOI-GUIDE-BOSS"
title: "Boss Creation Guide"
aliases: ["Boss Creation Guide"]
tags: ["boss", "creation", "guide", "tutorial"]
description: "Boss creation tutorial"
source: "docs/BOSS_CREATION.md"
date_processed: "2026-07-14"
---

# Boss Creation Guide

## 1. Overview

Bosses extend the enemy system with a **phase system**. `BossBase` (`src/framework/entities/boss_base.py`) extends `EnemyBase` and adds:

- Phase management (`BossPhase` dataclass)
- Health threshold transitions
- Phase transition animation + events
- Per-phase movement types, speed multipliers, and filter effects
- Boss HUD integration

---

## 2. Inherit from BossBase

```python
from __future__ import annotations
import pygame
from src.framework.entities.boss_base import BossBase, BossPhase

class BossMyBoss(BossBase):
    def __init__(self, spawn_position: pygame.Vector2) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=20.0,
            damage_on_contact=1.0,
        )
        self.set_boss_name("MY BOSS NAME")
        self.rect.width = 36
        self.rect.height = 44

        self._load_boss_sprites("boss_myboss", 48, 48)
        self.set_phases()
```

---

## 3. The Phase System

### BossPhase Dataclass

```python
@dataclass
class BossPhase:
    phase_index: int                     # 0-based
    health_threshold: float              # health at which this phase becomes active
    attack_patterns: list[str]           # attack names (used in _try_attack)
    movement_type: str                   # "sine", "bezier", "stationary"
    speed_multiplier: float              # movement speed multiplier
    sprite_override: str | None          # optional sprite prefix override
    filter_effect: str | None            # "sobel", "sobel_x", or None
    combos: dict[str, list[str]]         # attack → combo queue mapping
```

### Define Phases

Override `set_phases()`:

```python
def set_phases(self, phases: list[BossPhase] | None = None) -> None:
    if phases is None:
        phases = [
            BossPhase(
                phase_index=0,
                health_threshold=20.0,
                attack_patterns=["SLAM", "SPIT"],
                movement_type="sine",
                speed_multiplier=1.0,
                filter_effect=None,
                combos={},
            ),
            BossPhase(
                phase_index=1,
                health_threshold=10.0,
                attack_patterns=["SPIT", "CHARGE"],
                movement_type="bezier",
                speed_multiplier=1.5,
                filter_effect="sobel",
                combos={"SPIT": ["COMBO_CHARGE"]},
            ),
        ]
    super().set_phases(phases)
```

---

## 4. Required Overrides

### `_patrol_behavior(self, dt: float)`

Route to movement update:

```python
def _patrol_behavior(self, dt: float) -> None:
    self._update_movement(dt)
```

### `_alert_behavior(self, dt: float)`

Route to movement + attack logic:

```python
def _alert_behavior(self, dt: float) -> None:
    self._update_movement(dt)
    self._tick_attack_timers(dt)
    for pattern in self.phases[self.current_phase].attack_patterns:
        self._try_attack(pattern, dt)
```

### `_get_animation_key(self) -> str`

```python
def _get_animation_key(self) -> str:
    return "drift"  # default idle animation
```

### `_build_hitbox(self) -> pygame.Rect`

```python
def _build_hitbox(self) -> pygame.Rect:
    return pygame.Rect(6, 4, 36, 44)
```

### `_build_hurtbox(self) -> pygame.Rect`

```python
def _build_hurtbox(self) -> pygame.Rect:
    ox = (self.rect.width - 30) // 2
    oy = (self.rect.height - 40) // 2
    return pygame.Rect(ox, oy, 30, 40)
```

---

## 5. Movement Types

Implement `_update_movement(dt)` and branch on `phase.movement_type`:

```python
def _update_movement(self, dt: float) -> None:
    phase = self.phases[self.current_phase]
    speed = 60.0 * phase.speed_multiplier

    if phase.movement_type == "sine":
        self._elapsed += dt
        self.position.x += speed * dt * self.facing_direction
        self.position.y = self._base_y + 40.0 * math.sin(2 * math.pi * 0.4 * self._elapsed)
        # Clamp to arena bounds...

    elif phase.movement_type == "bezier" and self._bezier_path:
        self._bezier_t += self._bezier_speed * dt * phase.speed_multiplier
        pos = CurveTools.sample_path(self._bezier_path, self._bezier_t)
        self.position.x = pos[0]
        self.position.y = pos[1]
```

---

## 6. Attack System

### Attack Timers

Track cooldowns per attack:

```python
self._attack_timers: dict[str, float] = {"SLAM": 0.0, "SPIT": 0.0}
self._attack_cooldowns: dict[str, float] = {"SLAM": 3.0, "SPIT": 5.0}
```

### Try Attack Pattern

```python
def _try_attack(self, pattern: str, dt: float) -> None:
    if self._attack_timers.get(pattern, 0) > 0:
        return
    if pattern == "SLAM" and self._player_is_close():
        self._do_slam()
    elif pattern == "SPIT" and self._player_is_far():
        self._do_spit()
```

### Combo Queue System

Chain attacks using the combo queue:

```python
def _queue_combo(self, combo_names: list[str]) -> None:
    self._combo_queue = list(combo_names)
    self._combo_timer = 0.5

def _do_combo_slam_charge(self) -> None:
    self._attack_timers["CHARGE"] = 0.0
    self._do_charge()
```

---

## 7. Combat Methods

### `apply_hit(damage, source_position)`

Override to handle death transition:

```python
def apply_hit(self, damage: float, source_position: tuple[float, float]) -> None:
    super().apply_hit(damage, source_position)
    if self.current_health <= 0 and self.is_alive:
        self.on_defeated()
```

### `on_defeated()`

Custom death sequence:

```python
def on_defeated(self) -> None:
    self.state = EnemyState.DYING
    self._death_timer = 1.5  # death animation duration
```

### `_check_player_contact(self, player)`

Add projectile collision and attack zone checks:

```python
def _check_player_contact(self, player: Player) -> None:
    super()._check_player_contact(player)
    for proj in self._projectiles:
        if proj["alive"] and proj_rect.colliderect(player.hurtbox):
            player.apply_damage(proj["damage"], self.rect.center)
            proj["alive"] = False
```

---

## 8. Drawing

Override `draw()` to render projectiles and attack zones:

```python
def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
    super().draw(surface, camera_offset)
    for proj in self._projectiles:
        if proj.get("alive"):
            sx = int(proj["pos"].x - camera_offset.x)
            sy = int(proj["pos"].y - camera_offset.y)
            pygame.draw.circle(surface, (100, 200, 100), (sx, sy), 4)
```

---

## 9. Boss Scene (Optional)

Create a dedicated scene for your boss (like `BossVenadoScene`):

```python
class BossMyBossScene(StageScene):
    STAGE_ID: str = "boss_myboss"
    STAGE_NAME: str = "MY BOSS"
    ZONE: int = 0

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path("assets/maps/boss_myboss/boss_myboss.tmx"))
```

---

## 10. Reference: BossVenado

See `src/stages/boss_venado/boss_venado.py` for a complete implementation:

- **Phase 1**: Sine wave movement + STOMP/CHARGE/VINE_TOSS attacks, Sobel edge filter
- **Phase 2**: Bézier figure-8 path + VINE_SWEEP/MUSHROOM_SPORE, Sobel-X filter
- Combo chaining (STOMP → CHARGE, SWEEP → SPORE)
- Projectile management (Bézier vine toss, spore spread)
- Attack zone rects (stomp, vine sweep)
- Death sequence with particle effects



--- Traducción al Español ---

*Este documento está disponible en inglés. Para una traducción completa al español, contacte al profesor.*


---
## 🔗 Documentos Relacionados

- [[17_BOSS_SPEC.md|Boss Specification]]
- [[ENEMY_CREATION.md|Enemy Creation Guide]]

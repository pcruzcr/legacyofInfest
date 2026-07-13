# Enemy Creation Guide

## 1. Overview

All enemies inherit from `EnemyBase` (`src/framework/entities/enemy_base.py`), which itself inherits from `BaseEntity`. The base class provides a state machine (FSM), detection system, hitbox/hurtbox infrastructure, contact damage, invincibility frames, and death handling.

---

## 2. Inherit from EnemyBase

```python
from __future__ import annotations
import pygame
from src.framework.entities.enemy_base import EnemyBase

class EnemyMyType(EnemyBase):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        patrol_speed: float = 50.0,
        alert_speed: float = 90.0,
        max_health: float = 3.0,
        damage_on_contact: float = 0.5,
        zone: int = 0,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=160.0,
            detection_range_y=48.0,
        )
        self.patrol_speed = patrol_speed
        self.alert_speed = alert_speed
        self.rect.width = 24
        self.rect.height = 28
        self._load_zone_sprites(zone, 16, 12)
```

---

## 3. Required Methods

### `_build_hitbox(self) -> pygame.Rect`

Return a **local-space** rect for the enemy's active damage zone (the area that hurts the player on contact):

```python
def _build_hitbox(self) -> pygame.Rect:
    return pygame.Rect(4, 2, 24, 28)
```

### `_build_hurtbox(self) -> pygame.Rect`

Return a **local-space** rect for where the enemy receives damage:

```python
def _build_hurtbox(self) -> pygame.Rect:
    return pygame.Rect(4, 2, 24, 28)
```

### `_get_animation_key(self) -> str`

Return the sprite animation key for non-DYING/non-HURT states:

```python
def _get_animation_key(self) -> str:
    return "walk"
```

Animation keys must correspond to sprite sheets loaded by `_load_zone_sprites()` or `_load_extra_sprites()`. Default loaded keys are `"walk"`, `"hurt"`, `"die"`.

### `_patrol_behavior(self, dt: float) -> None`

Movement/AI when no player is detected:

```python
def _patrol_behavior(self, dt: float) -> None:
    self.position.x += self.facing_direction * self.patrol_speed * dt
```

### `_alert_behavior(self, dt: float) -> None`

AI when the player is within detection range:

```python
def _alert_behavior(self, dt: float) -> None:
    self._face_player()
    self.position.x += self.facing_direction * self.alert_speed * dt
```

---

## 4. FSM States

The state machine (`_run_state_machine` in `EnemyBase`) manages these states automatically:

| State | Triggered By | Description |
|---|---|---|
| `PATROL` | Default / deaggro | Enemy patrols normally |
| `ALERT` | Player detected | Enemy pursues / attacks |
| `TELEGRAPHING` | Enemy logic | Wind-up before attack (0.4s default) |
| `FIRING` | After telegraph | Execute attack |
| `HURT` | `apply_hit()` called | Hitstun (timer-based) |
| `LAUNCHED` | Heavy knockback (≥1.5 dmg) | Airborne state with gravity |
| `DYING` | Health ≤ 0 | Death animation, then removal |

**Priority order**: `DYING > LAUNCHED > HURT > TELEGRAPHING > FIRING > ALERT > PATROL`

### Transition helpers

- `self._face_player()` — flip facing direction toward player
- `self._telegraph_timer` / `self._telegraph_duration` — control telegraph timing
- `self.state = EnemyState.FIRING` — transition to firing (then `_firing_behavior` is called)

Override `_firing_behavior(dt)` to customize what happens in the FIRING state:

```python
def _firing_behavior(self, dt: float) -> None:
    # Fire a projectile, then return to ALERT
    self._spawn_projectile()
    self.state = EnemyState.ALERT
```

---

## 5. Detection System

Detection is handled automatically. The base class manages:

- `detection_range_x` / `detection_range_y` — set in `__init__`
- `set_player_ref(player_rect)` — called by `StageScene` to provide the player's rect
- `_check_detection_range()` — returns `True` if player is within range
- Deaggro hysteresis — once `ALERT`, player must leave range + 32px margin before returning to `PATROL`

---

## 6. Optional Hooks

### `_pre_update(self, dt: float) -> bool`

Called at the start of `update()`. Return `True` to skip the rest of the update (used by `BossBase` for phase transitions).

### `_post_update(self, dt: float)`

Called at the end of `update()`. Used by `EnemyShooter` to update projectiles.

### `_load_extra_sprites(self, zone: int, fw: int, fh: int)`

Load additional sprite sheets beyond `walk`/`hurt`/`die`:

```python
def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
    path = settings.ASSETS_DIR / "sprites" / "enemies" / f"zone{zone}" / "enemy_mytype_shoot.png"
    frames = AssetLoader.load_sprite_sheet(path, fw, fh)
    self._sprite_frames["shoot"] = frames
```

---

## 7. Animations

The base class expects sprite sheets at `assets/sprites/enemies/zone{zone}/`:

- `enemy_zone{zone}_walk.png`
- `enemy_zone{zone}_hurt.png`
- `enemy_zone{zone}_die.png`

Animation FPS can be tuned via class variables:

```python
_ANIM_FPS = {"walk": 10.0, "hurt": 12.0, "die": 10.0, "shoot": 16.0}
_ALERT_ANIM_FPS = {"walk": 14.0}  # faster in alert mode
```

---

## 8. Adding to the Spawn Registry

Register the new enemy in `src/framework/entities/entity_factory.py`:

```python
from src.framework.entities.enemy_mytype import EnemyMyType   # add this import

_ENTITY_REGISTRY: dict[str, type[EnemyBase]] = {
    "Walker": EnemyWalker,
    "Flying": EnemyFlying,
    "Shooter": EnemyShooter,
    "Charger": EnemyCharger,
    "Archer": EnemyArcher,
    "Brute": EnemyBrute,
    "Caster": EnemyCaster,
    "Assassin": EnemyAssassin,
    "MyType": EnemyMyType,   # add this line
    "BossVenado": BossVenado,
}
```

The string key (`"MyType"`) is what you use as the `type` field on TMX objects.

---

## 9. Full Example (EnemyWalker)

See `src/framework/entities/enemy_walker.py` for a complete walker implementation with patrol, ledge detection, alert pursuit, and charge attack.


--- Traducción al Español ---

## Guía de Creación de Enemigos

### Resumen
Todos los enemigos heredan de `EnemyBase`, que a su vez hereda de `BaseEntity`.

### Métodos Requeridos
- `_build_hitbox()` — Rectángulo de zona de daño activa
- `_build_hurtbox()` — Rectángulo donde recibe daño
- `_get_animation_key()` — Clave de animación
- `_patrol_behavior(dt)` — IA en modo patrulla
- `_alert_behavior(dt)` — IA cuando detecta al jugador

### Estados del FSM
PATROL, ALERT, TELEGRAPHING, FIRING, HURT, LAUNCHED, DYING

Para ejemplos completos de código y registro en EntityFactory, consultar el documento original en inglés.

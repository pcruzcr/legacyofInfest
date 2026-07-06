# Legacy of InFest — API Contracts

**Document ID:** LOI-API-022  
**Version:** 1.1.0  
**Status:** Official  
**Compatibility:** Authoritative signature reference for all of `03_ARCHITECTURE.md` through `17_BOSS_SPEC.md`  
**Audience:** AI coding assistants (Claude Code, Cline, OpenCode, Codex)

---

## 1. Purpose and Precedence Rule

This document is the **single source of truth for exact function and class signatures** across the entire Legacy of InFest codebase. Every prose description in Documents 03–17 is authoritative for *behavior*; this document is authoritative for *syntax* — parameter names, types, order, defaults, and return types.

**Precedence rule:** If this document and a narrative spec document (e.g., `04_PLAYER_SPEC.md`) ever appear to disagree on a signature, this document wins for syntax, and the narrative document wins for behavior. Flag the discrepancy in `KNOWN_GAPS.md` rather than guessing.

All type hints use Python 3.14+ syntax. All signatures assume `from __future__ import annotations` is not required (native syntax).

---

## 2. Engine Core

### 2.1 `src/engine/core/settings.py`

No classes. Module-level constants only. Full list — do not add undocumented constants without updating this table.

```python
from pathlib import Path

INTERNAL_WIDTH: int = 320
INTERNAL_HEIGHT: int = 224
TARGET_FPS: int = 60
DISPLAY_SCALE: int = 3
TILE_SIZE: int = 16

ASSETS_DIR: Path = Path("assets")
STAGES_DIR: Path = Path("src/stages")
STUDENT_TEMPLATES_DIR: Path = Path("student_templates")

PLAYER_MAX_HEALTH: float = 5.0
GRAVITY: float = 800.0
PLAYER_WALK_SPEED: float = 90.0
PLAYER_JUMP_FORCE: float = -380.0
PLAYER_MAX_FALL_SPEED: float = 500.0
PLAYER_COYOTE_FRAMES: int = 6
PLAYER_INVINCIBILITY_DURATION: float = 1.5
PLAYER_DASH_SPEED: float = 200.0
PLAYER_AIR_DASH_LIMIT: int = 1
PLAYER_SHORT_ATTACK_DURATION: float = 0.15
PLAYER_LONG_ATTACK_DURATION: float = 0.4
PLAYER_COOLDOWN_SHORT: float = 0.0
PLAYER_COOLDOWN_LONG: float = 0.067
```

### 2.2 `src/engine/core/clock.py`

```python
class DeltaClock:
    def __init__(self) -> None: ...

    def tick(self) -> float:
        """Returns delta time in seconds, scaled by self.time_scale."""

    @property
    def fps(self) -> float: ...

    time_scale: float  # public mutable attribute, default 1.0
```

### 2.3 `src/engine/core/event_bus.py`

```python
from typing import Callable, Any

class EventBus:
    """Instance-based publish/subscribe event bus (v1.1.0: changed from static class)."""

    def __init__(self) -> None: ...

    def subscribe(self, event_name: str, callback: Callable[..., None]) -> None: ...
    def unsubscribe(self, event_name: str, callback: Callable[..., None]) -> None: ...
    def unsubscribe_all(self, events: list[str], callback: Callable[..., None]) -> None: ...
    def subscriber_count(self) -> int: ...

    def emit(self, event_name: str, **data: Any) -> None:
        """Queues the event; dispatched at the start of the next frame."""

    def dispatch(self) -> None:
        """Called once per frame by App, before scene update. Drains the queue."""

    def clear(self) -> None:
        """Clear all subscribers and pending events. Useful for testing."""


# Module-level convenience functions delegate to a default instance:
def subscribe(event_name: str, callback: Callable[..., None]) -> None: ...
def unsubscribe(event_name: str, callback: Callable[..., None]) -> None: ...
def unsubscribe_all(events: list[str], callback: Callable[..., None]) -> None: ...
def subscriber_count() -> int: ...
def emit(event_name: str, **data: Any) -> None: ...
def dispatch() -> None: ...
def clear() -> None: ...
```

**Standard event payloads** (exact `**data` keys — see `23_DATA_SCHEMAS.md` §2 for the full table):

| Event | Keys |
|---|---|
| `PLAYER_DAMAGED` | `amount: float`, `source: tuple[float, float]` |
| `PLAYER_HEALED` | `amount: float` |
| `PLAYER_DIED` | *(no keys)* |
| `CHECKPOINT_REACHED` | `checkpoint_id: int` |
| `ENEMY_DIED` | `entity_id: str`, `position: tuple[float, float]` |
| `STAGE_COMPLETE` | *(no keys)* |
| `BOSS_PHASE_CHANGED` | `phase: int` |
| `SHOW_MESSAGE` | `text: str`, `duration: float` |
| `HIDE_MESSAGE` | *(no keys)* |

### 2.4 `src/engine/core/app.py`

```python
import pygame

class App:
    def __init__(self) -> None:
        """
        Initializes pygame, pygame.mixer, creates internal_surface (320x224)
        and window_surface (scaled by settings.DISPLAY_SCALE), constructs
        DeltaClock, EventBus, AssetLoader, InputManager, AudioManager,
        SceneManager. Pushes SplashScene onto the SceneManager.
        """

    def run(self) -> None:
        """Enters the main loop. Does not return until quit."""

    def quit(self) -> None:
        """Stops music, calls pygame.quit(), sys.exit(0)."""

    internal_surface: pygame.Surface
    window_surface: pygame.Surface
    clock: "DeltaClock"
    scene_manager: "SceneManager"
    input_manager: "InputManager"
    audio_manager: "AudioManager"
```

---

## 3. Engine Input

### 3.1 `src/engine/input/action_map.py`

```python
from enum import Enum, auto

class Action(Enum):
    """Abstract game actions. Bindings map physical keys to these actions."""
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    JUMP = auto()
    CROUCH = auto()
    SHORT_ATTACK = auto()
    LONG_ATTACK = auto()
    DASH = auto()
    CONFIRM = auto()
    CANCEL = auto()
    PAUSE = auto()

DEFAULT_KEY_BINDINGS: dict[Action, list[int]]   # pygame key constants
```

### 3.2 `src/engine/input/input_manager.py`

```python
class InputManager:
    def __init__(self) -> None: ...

    def pump(self, events: list[pygame.event.Event]) -> None:
        """Called once per frame by App with the current event list."""

    def is_action_pressed(self, action: "Action") -> bool:
        """True only on the frame the action was activated."""

    def is_action_held(self, action: "Action") -> bool:
        """True for every frame the action is held."""

    def is_action_released(self, action: "Action") -> bool:
        """True only on the frame the action was released."""
```

---

## 4. Engine Audio

### 4.1 `src/engine/audio/sound_bank.py`

```python
class SoundBank:
    def __init__(self) -> None:
        """Scans assets/sfx/ for .wav files on construction."""

    def load_all(self) -> None:
        """Scan assets/sfx/ recursively and register every .wav file."""

    def load(self, name: str, path: str | Path) -> None:
        """Register a sound by name, loading from the given path."""

    def get(self, name: str) -> pygame.mixer.Sound | None:
        """Retrieve a registered sound by name. Returns None if not found."""

    def play(self, name: str, loops: int = 0, volume: float = 1.0) -> None:
        """Play a registered sound at the given volume. Silently skip if not found."""
```

### 4.2 `src/engine/audio/audio_manager.py`

```python
class AudioManager:
    def __init__(self) -> None: ...

    def play_music(self, name: str, loop: bool = True, fade_ms: int = 0) -> None: ...
    def stop_music(self, fade_ms: int = 0) -> None: ...
    def resume_music(self) -> None: ...
    def play_sfx(self, name: str) -> None:
        """Play a sound effect from the sound bank at the current SFX volume."""
    def set_music_volume(self, volume: float) -> None:
        """volume clamped to [0.0, 1.0]."""
    def set_sfx_volume(self, volume: float) -> None: ...
    def toggle_mute(self) -> None: ...
    @property
    def is_muted(self) -> bool: ...
```

---

## 5. Engine Utils

### 5.1 `src/engine/utils/math_utils.py`

```python
def lerp(a: float, b: float, t: float) -> float: ...
def clamp(value: float, min_v: float, max_v: float) -> float: ...

def ease_in_quad(t: float) -> float: ...
def ease_out_quad(t: float) -> float: ...
def ease_in_out_quad(t: float) -> float: ...
def ease_in_cubic(t: float) -> float: ...
def ease_out_cubic(t: float) -> float: ...
def ease_out_bounce(t: float) -> float: ...
def ease_out_elastic(t: float) -> float: ...
def ease_in_sine(t: float) -> float: ...
def ease_out_sine(t: float) -> float: ...
# All wrap pytweening; t must be in [0, 1]; undefined behavior outside that range.

def vec2_normalize(v: tuple[float, float]) -> tuple[float, float]: ...
def vec2_length(v: tuple[float, float]) -> float: ...
def vec2_dot(a: tuple[float, float], b: tuple[float, float]) -> float: ...
def vec2_distance(a: tuple[float, float], b: tuple[float, float]) -> float: ...
```

### 5.2 `src/engine/utils/asset_loader.py`

```python
from pathlib import Path

class AssetLoader:
    """All methods classmethods; internal cache is a class-level dict keyed by str(path)."""

    @classmethod
    def load_image(
        cls,
        path: str | Path,
        *,
        scale: float | None = None,
        size: tuple[int, int] | None = None,
        alpha: bool = True,
    ) -> pygame.Surface: ...

    @classmethod
    def load_sound(cls, path: str | Path) -> pygame.mixer.Sound: ...

    @classmethod
    def load_spritesheet(cls, path: str | Path, frame_w: int, frame_h: int) -> "SpriteSheet": ...
```

### 5.3 `src/engine/utils/spritesheet.py`

```python
class SpriteSheet:
    def __init__(self, surface: pygame.Surface, frame_w: int, frame_h: int) -> None: ...

    def get_frame(self, index: int) -> pygame.Surface: ...
    def get_frames(self, start: int, end: int) -> list[pygame.Surface]: ...

    @property
    def frame_count(self) -> int: ...
```

---

## 6. Engine Scene

### 6.1 `src/engine/scene/base_scene.py`

```python
from abc import ABC, abstractmethod

class BaseScene(ABC):
    @abstractmethod
    def on_enter(self) -> None: ...

    @abstractmethod
    def on_exit(self) -> None: ...

    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None: ...

    def on_pause(self) -> None:
        """Optional override. Default: no-op."""

    def on_resume(self) -> None:
        """Optional override. Default: no-op."""
```

### 6.2 `src/engine/scene/scene_manager.py`

```python
class SceneManager:
    def __init__(self) -> None: ...

    def push(self, scene: "BaseScene") -> None:
        """Calls current.on_pause() if a scene exists, then scene.on_enter()."""

    def pop(self) -> None:
        """Calls current.on_exit(), then new current.on_resume()."""

    def replace(self, scene: "BaseScene") -> None:
        """Calls current.on_exit(), then scene.on_enter(). No pause/resume."""

    @property
    def current(self) -> "BaseScene | None": ...
```

**Call-order guarantee (sequence diagram):**

```
push(B) while A is current:
    A.on_pause()
    B.on_enter()
    # current is now B

pop() while B is current (A below it):
    B.on_exit()
    A.on_resume()
    # current is now A

replace(C) while A is current:
    A.on_exit()
    C.on_enter()
    # current is now C, A is discarded (not on the stack)
```

### 6.3 `src/engine/scene/transitions.py`

```python
class FadeTransition:
    def __init__(self, duration: float, color: tuple[int, int, int] = (0, 0, 0)) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...
    @property
    def is_complete(self) -> bool: ...

class WipeTransition:
    def __init__(self, duration: float, direction: str = "left_to_right") -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...
    @property
    def is_complete(self) -> bool: ...
```

---

## 7. Engine UI

### 7.1 `src/engine/ui/hud.py`

```python
class HUD:
    def __init__(self) -> None:
        """Subscribes to PLAYER_DAMAGED, PLAYER_HEALED, PLAYER_DIED via EventBus."""

    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...

    def start_timer(self, seconds: int) -> None:
        """seconds=0 means an ascending (count-up) timer (Stage 0 mode)."""

    def pause_timer(self) -> None: ...
    def resume_timer(self) -> None: ...
    def bind_player(self, player: "Player") -> None:
        """Stores a weak reference for portrait-state queries only; HUD never mutates Player."""
```

### 7.2 `src/engine/ui/message_box.py`

```python
class MessageBox:
    def __init__(self) -> None:
        """Subscribes to SHOW_MESSAGE, HIDE_MESSAGE."""

    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...

    @property
    def is_active(self) -> bool: ...
```

### 7.3 `src/engine/ui/screen_banner.py`

```python
class ScreenBanner:
    def __init__(self) -> None: ...

    def play(self, stage_id: str, stage_name: str) -> None:
        """Triggers the slide-in/hold/slide-out animation sequence."""

    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...

    @property
    def is_active(self) -> bool: ...
```

---

## 8. Framework Entities — BaseEntity

### 8.1 `src/framework/entities/base_entity.py`

```python
from abc import ABC, abstractmethod

class BaseEntity(ABC):
    def __init__(self, position: pygame.Vector2) -> None: ...

    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...

    position: pygame.Vector2
    rect: pygame.Rect
    is_active: bool       # default True
    is_visible: bool      # default True
    layer: int            # default 4 (mid-layer; see pyscroll default_layer)
```

---

## 9. Framework Entities — Player

### 9.1 `src/framework/entities/player.py`

```python
from enum import Enum

class PlayerState(str, Enum):
    IDLE = "IDLE"
    WALKING = "WALKING"
    JUMPING = "JUMPING"
    FALLING = "FALLING"
    CROUCHING = "CROUCHING"
    DASHING = "DASHING"
    SHORT_ATTACK = "SHORT_ATTACK"
    LONG_ATTACK = "LONG_ATTACK"
    HURT = "HURT"
    DYING = "DYING"

class Player(BaseEntity):
    def __init__(self, spawn_position: pygame.Vector2) -> None: ...

    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...

    def apply_damage(self, amount: float, source_position: tuple[float, float], knockback_force: float = 150.0) -> None:
        """
        No-op if invincibility_timer > 0. Otherwise: subtracts amount, clamps to
        [0, PLAYER_MAX_HEALTH], sets invincibility_timer, emits PLAYER_DAMAGED,
        transitions to HURT, applies knockback with given force away from source.
        Emits PLAYER_DIED if health reaches 0.
        """

    def set_spawn(self, position: pygame.Vector2) -> None:
        """The ONLY sanctioned way to reposition the player (e.g., checkpoint respawn)."""

    def consume_hitbox(self) -> None:
        """Called by the stage collision system after an attack hitbox connects,
        to prevent multi-hit on the same frame."""

    @property
    def current_health(self) -> float:
        """Read-only. Stage/entity code must never write _health directly."""

    @property
    def state(self) -> "PlayerState": ...

    @property
    def active_hitbox(self) -> pygame.Rect | None:
        """None unless currently in an active attack frame window."""

    @property
    def current_attack_damage(self) -> float:
        """0.50 during SHORT_ATTACK active frames, 1.00 during LONG_ATTACK active frames,
        0.0 otherwise."""

    facing_direction: int  # -1 or 1
```

---

## 10. Framework Entities — Enemies

### 10.1 `src/framework/entities/enemy_base.py`

```python
from abc import abstractmethod
from enum import Enum

class EnemyState(str, Enum):
    PATROL = "PATROL"
    ALERT = "ALERT"
    HURT = "HURT"
    DYING = "DYING"

class EnemyBase(BaseEntity):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float,
        damage_on_contact: float = 0.5,
        contact_knockback: float = 120.0,
        detection_range_x: float = 160.0,
        detection_range_y: float = 64.0,
        hurt_duration: float = 0.3,
        invincibility_duration: float = 0.5,
    ) -> None: ...

    def update(self, dt: float) -> None:
        """Master update — calls _update_invincibility, _run_state_machine,
        _update_rects, _check_player_contact. Subclasses do NOT override update()."""

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...

    def apply_hit(self, damage: float, source_position: tuple[float, float]) -> None:
        """Provided. Do not override."""

    # --- Required overrides (abstract) ---
    @abstractmethod
    def _patrol_behavior(self, dt: float) -> None: ...

    @abstractmethod
    def _alert_behavior(self, dt: float) -> None: ...

    @abstractmethod
    def _get_animation_key(self) -> str:
        """Return the base animation key for the current non-DYING, non-HURT state."""

    @abstractmethod
    def _build_hitbox(self) -> pygame.Rect:
        """Returns LOCAL-space rect (offset from entity position)."""

    @abstractmethod
    def _build_hurtbox(self) -> pygame.Rect:
        """Returns LOCAL-space rect (offset from entity position)."""

    # --- Template method (override only via _get_animation_key) ---
    def _get_animation_state(self) -> str:
        """Concrete template method — fixed mapping for DYING/HURT;
        delegates to _get_animation_key() for the rest."""

    # --- Provided hooks (may override for custom projectile logic) ---
    def _check_player_contact(self, player: "Player") -> None: ...

    # --- Provided, do not override ---
    def _die(self) -> None: ...
    def _update_invincibility(self, dt: float) -> None: ...
    def _update_rects(self) -> None: ...

    current_health: float
    is_alive: bool
    facing_direction: int  # -1 or 1
    state: "EnemyState"
    hitbox: pygame.Rect    # world-space, recomputed every frame
    hurtbox: pygame.Rect   # world-space, recomputed every frame
```

### 10.2 `src/framework/entities/enemy_walker.py`

```python
class EnemyWalker(EnemyBase):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        patrol_length: float = 96.0,
        facing: str = "right",
        patrol_speed: float = 45.0,
        alert_speed: float = 75.0,
        damage_on_contact: float = 0.5,
        max_health: float = 2.0,
        zone: int = 0,
    ) -> None: ...

    # Inherited abstracts implemented; no new public methods.
```

### 10.3 `src/framework/entities/enemy_flying.py`

```python
class EnemyFlying(EnemyBase):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        flight_mode: str = "sine",          # "sine" | "bezier" | "patrol"
        flight_speed: float = 60.0,
        sine_amplitude: float = 28.0,
        sine_frequency: float = 1.5,
        waypoints: list[tuple[float, float]] | None = None,  # required for "bezier"/"patrol"
        max_health: float = 1.5,
        damage_on_contact: float = 0.5,
        zone: int = 0,
    ) -> None: ...

    # Inherited abstracts implemented; no new public methods.
```

### 10.4 `src/framework/entities/enemy_shooter.py`

```python
class EnemyShooter(EnemyBase):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        fire_rate: float = 0.5,             # shots per second
        projectile_speed: float = 120.0,
        projectile_damage: float = 0.5,
        patrol_length: float = 0.0,         # 0 = stationary
        max_health: float = 3.0,
        damage_on_contact: float = 0.25,
        zone: int = 0,
    ) -> None: ...

    # Inherited abstracts implemented; no new public methods.


class Projectile(BaseEntity):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        velocity: pygame.Vector2,
        damage: float,
        lifetime: float = 3.0,
    ) -> None: ...

    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...
```

### 10.5 `src/framework/entities/boss_base.py`

See `22_API_CONTRACTS.md` §17.

---

## 11. Framework Stage

### 11.1 `src/framework/stage/camera.py`

```python
class Camera:
    def __init__(self) -> None: ...

    def follow(self, target: "BaseEntity") -> None: ...
    def update(self, dt: float) -> None: ...

    def world_to_screen(self, pos: pygame.Vector2) -> pygame.Vector2: ...
    def screen_to_world(self, pos: pygame.Vector2) -> pygame.Vector2: ...

    @property
    def offset(self) -> pygame.Vector2: ...
```

### 11.2 `src/framework/stage/checkpoint.py`

```python
class Checkpoint(BaseEntity):
    def __init__(self, position: pygame.Vector2, rect: pygame.Rect, checkpoint_id: int) -> None: ...

    def update(self, dt: float) -> None:
        """Checks player overlap; if first activation, emits CHECKPOINT_REACHED."""

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...

    @property
    def is_active(self) -> bool: ...
```

### 11.3 `src/framework/stage/stage_loader.py`

```python
from dataclasses import dataclass, field

@dataclass
class StageData:
    map_layer: "pyscroll.PyscrollGroup"
    collision_rects: list[pygame.Rect] = field(default_factory=list)
    entity_list: list["BaseEntity"] = field(default_factory=list)
    checkpoints: list["Checkpoint"] = field(default_factory=list)
    spawn_point: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    next_trigger: pygame.Rect | None = None
    background_layers: list[pygame.Surface] = field(default_factory=list)
    stage_id: str = ""
    stage_name: str = ""
    time_limit: int = 0
    bgm_track: str = ""


class StageLoader:
    _entity_registry: dict[str, type["BaseEntity"]] = {}

    @classmethod
    def register_entity(cls, type_name: str, entity_class: type["BaseEntity"]) -> None: ...

    @classmethod
    def load(cls, tmx_path: "Path") -> "StageData":
        """
        Raises FrameworkUsageError if:
        - any required layer (06_TMX_SPEC.md §3.1) is missing
        - no PlayerSpawn object is found
        - more than one PlayerSpawn object is found
        """


class FrameworkUsageError(Exception):
    """Raised when student/stage code misuses the framework API."""
```

---

## 12. Framework Processing — ColorTools and CurveTools

### 12.1 `src/framework/processing/color_tools.py`

```python
class ColorTools:
    @classmethod
    def rgb_to_hsv(cls, r: int, g: int, b: int) -> tuple[float, float, float]:
        """Returns (h: 0-360, s: 0-1, v: 0-1)."""

    @classmethod
    def hsv_to_rgb(cls, h: float, s: float, v: float) -> tuple[int, int, int]:
        """Returns (r, g, b) each 0-255."""

    @classmethod
    def rgb_to_hsl(cls, r: int, g: int, b: int) -> tuple[float, float, float]: ...

    @classmethod
    def hsl_to_rgb(cls, h: float, s: float, l: float) -> tuple[int, int, int]: ...

    @classmethod
    def rgb_to_cmyk(cls, r: int, g: int, b: int) -> tuple[float, float, float, float]:
        """Returns (c, m, y, k) each 0-1."""

    @classmethod
    def cmyk_to_rgb(cls, c: float, m: float, y: float, k: float) -> tuple[int, int, int]: ...

    @classmethod
    def alpha_blend(cls, src: pygame.Surface, dst: pygame.Surface, alpha: float) -> pygame.Surface:
        """out = src*alpha + dst*(1-alpha). Surfaces must be same size."""

    @classmethod
    def apply_tint(cls, surface: pygame.Surface, color: tuple[int, int, int]) -> pygame.Surface: ...

    @classmethod
    def surface_to_array(cls, surface: pygame.Surface) -> "np.ndarray":
        """Returns shape (W, H, 3) uint8, via pygame.surfarray.array3d."""

    @classmethod
    def array_to_surface(cls, array: "np.ndarray") -> pygame.Surface:
        """Expects shape (W, H, 3) uint8."""
```

### 12.2 `src/framework/processing/curve_tools.py`

```python
class CurveTools:
    @classmethod
    def bezier(
        cls,
        control_points: list[tuple[float, float]],
        n_samples: int,
    ) -> list[tuple[float, float]]:
        """Degree = len(control_points) - 1. Computed via Bernstein basis."""

    @classmethod
    def b_spline(
        cls,
        control_points: list[tuple[float, float]],
        degree: int,
        n_samples: int,
    ) -> list[tuple[float, float]]: ...

    @classmethod
    def nurbs(
        cls,
        control_points: list[tuple[float, float]],
        weights: list[float],
        knots: list[float],
        degree: int,
        n_samples: int,
    ) -> list[tuple[float, float]]: ...

    @classmethod
    def catmull_rom(
        cls,
        control_points: list[tuple[float, float]],
        n_samples: int,
    ) -> list[tuple[float, float]]: ...

    @classmethod
    def build_bezier_path(
        cls,
        waypoints: list[pygame.Vector2],
        t: float,
    ) -> pygame.Vector2:
        """Catmull-Rom smooth interpolation through waypoints at parameter t [0, 1].
        Despite the name, this uses Catmull-Rom splines, not true Bézier.
        Used by BezierStrategy in flight_strategies.py."""

    @classmethod
    def sample_path(
        cls,
        points: list[tuple[float, float]],
        t: float,
    ) -> tuple[float, float]:
        """t in [0, 1]. Interpolates between the pre-sampled points list."""
```

---

## 13. Framework Processing — FilterTools

### 13.1 `src/framework/processing/filter_tools.py`

```python
class FilterTools:
    @classmethod
    def compute_histogram(cls, surface: pygame.Surface) -> dict[str, "np.ndarray | int"]:
        """Returns {'r': ndarray(256,), 'g': ndarray(256,), 'b': ndarray(256,),
        'luminance': ndarray(256,), 'total_pixels': int}."""

    @classmethod
    def histogram_equalize(cls, surface: pygame.Surface) -> pygame.Surface: ...

    @classmethod
    def adjust_brightness(cls, surface: pygame.Surface, factor: float) -> pygame.Surface:
        """factor in [0.0, 4.0]. Raises ValueError if out of range."""

    @classmethod
    def adjust_contrast(cls, surface: pygame.Surface, factor: float) -> pygame.Surface:
        """factor in [0.0, 4.0]."""

    @classmethod
    def stretch_contrast(cls, surface: pygame.Surface) -> pygame.Surface: ...

    @classmethod
    def apply_kernel(cls, surface: pygame.Surface, kernel: "np.ndarray") -> pygame.Surface:
        """kernel must be square, odd-sized, 3x3 to 15x15. Raises ValueError otherwise."""

    @classmethod
    def get_standard_kernel(cls, name: str) -> "np.ndarray":
        """name in {'identity','sharpen','box_blur','box_blur_5','edge_laplacian',
        'emboss','ridge','sobel_x','sobel_y'}. Raises KeyError with valid names listed."""

    @classmethod
    def gaussian_blur(cls, surface: pygame.Surface, sigma: float) -> pygame.Surface:
        """sigma in (0.0, 10.0]."""

    @classmethod
    def sobel_edge(cls, surface: pygame.Surface) -> pygame.Surface:
        """Returns grayscale-as-RGB surface (no alpha)."""

    @classmethod
    def canny_edge(
        cls,
        surface: pygame.Surface,
        low_threshold: int,
        high_threshold: int,
    ) -> pygame.Surface:
        """1 <= low_threshold < high_threshold <= 255. Returns binary RGB surface."""
```

---

## 14. Framework Processing — VisionTools

### 14.1 `src/framework/processing/vision_tools.py`

```python
from dataclasses import dataclass

@dataclass
class ComponentResult:
    label_array: "np.ndarray"        # int32, shape (H, W)
    num_components: int
    component_sizes: dict[int, int]
    label_surface: pygame.Surface

@dataclass
class RegionInfo:
    label: int
    area: int
    centroid: tuple[float, float]
    bounding_rect: pygame.Rect
    eccentricity: float
    solidity: float
    perimeter: float


class VisionTools:
    @classmethod
    def threshold_binary(cls, surface: pygame.Surface, threshold: int) -> pygame.Surface:
        """0 <= threshold <= 255."""

    @classmethod
    def threshold_otsu(cls, surface: pygame.Surface) -> tuple[pygame.Surface, int]:
        """Returns (mask_surface, computed_threshold)."""

    @classmethod
    def morphological_erode(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface: ...

    @classmethod
    def morphological_dilate(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface: ...

    @classmethod
    def morphological_open(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface: ...

    @classmethod
    def morphological_close(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface: ...

    @classmethod
    def connected_components(cls, mask_surface: pygame.Surface) -> "ComponentResult": ...

    @classmethod
    def filter_components_by_area(
        cls,
        result: "ComponentResult",
        min_area: int,
        max_area: int,
    ) -> "ComponentResult": ...

    @classmethod
    def analyze_regions(cls, mask_surface: pygame.Surface) -> list["RegionInfo"]:
        """Sorted by area descending."""

    @classmethod
    def largest_region(cls, mask_surface: pygame.Surface) -> "RegionInfo | None": ...

    @classmethod
    def watershed_segment(
        cls,
        surface: pygame.Surface,
    ) -> tuple[pygame.Surface, "np.ndarray"]:
        """Returns (label_surface, label_array)."""

    @classmethod
    def extract_features(cls, surface: pygame.Surface, method: str = "hog") -> "np.ndarray":
        """method in {'hog','lbp','color_hist','combined'}."""

    @classmethod
    def extract_hog(cls, surface: pygame.Surface) -> "np.ndarray":
        """Returns shape (512,) for 32x32 canonical resize."""

    @classmethod
    def extract_lbp(cls, surface: pygame.Surface) -> "np.ndarray":
        """Returns shape (256,)."""

    @classmethod
    def extract_color_histogram(cls, surface: pygame.Surface, bins: int = 256) -> "np.ndarray":
        """Returns shape (bins*3,). 4 <= bins <= 256."""

    @classmethod
    def find_contours(cls, mask_surface: pygame.Surface) -> list["np.ndarray"]: ...

    @classmethod
    def bounding_boxes_from_mask(cls, mask_surface: pygame.Surface) -> list[pygame.Rect]: ...
```

---

## 15. Framework Processing — PatternRecognitionTools

### 15.1 `src/framework/processing/pattern_recognition_tools.py`

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class TrainedModel:
    model_type: str                  # 'knn' | 'tree' | 'forest' | 'svm'
    estimator: Any                   # fitted sklearn Pipeline (scaler + classifier)
    classes: list[str]
    feature_method: str              # 'hog' | 'lbp' | 'color_hist' | 'combined' | 'external'
    feature_length: int
    training_accuracy: float
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class EvaluationResult:
    accuracy: float
    per_class_accuracy: dict[str, float]
    confusion_matrix: "np.ndarray"
    report: str


class PatternRecognitionTools:
    # --- Feature extractors (delegate to VisionTools) ---
    @classmethod
    def extract_hog(cls, surface: pygame.Surface) -> "np.ndarray": ...
    @classmethod
    def extract_lbp(cls, surface: pygame.Surface) -> "np.ndarray": ...
    @classmethod
    def extract_color_histogram(cls, surface: pygame.Surface, bins: int = 256) -> "np.ndarray": ...
    @classmethod
    def extract_combined(cls, surface: pygame.Surface) -> "np.ndarray": ...

    # --- Training pipeline (offline use only) ---
    @classmethod
    def train(
        cls,
        X: "np.ndarray",          # shape (n_samples, n_features), float32
        y: "np.ndarray",          # shape (n_samples,)
        model_type: str,          # 'knn' | 'tree' | 'forest' | 'svm'
        **kwargs: Any,
    ) -> "TrainedModel": ...

    @classmethod
    def evaluate(
        cls,
        model: "TrainedModel",
        X_test: "np.ndarray",
        y_test: "np.ndarray",
    ) -> "EvaluationResult": ...

    # --- Serialization ---
    @classmethod
    def save_model(cls, model: "TrainedModel", path: str | Path) -> None:
        """path must end in .pkl. Creates parent dirs if needed."""

    @classmethod
    def load_model(cls, path: str | Path) -> "TrainedModel":
        """Raises FileNotFoundError / TypeError as documented in 13_PATTERN_RECOGNITION_SPEC.md §11.2."""

    # --- Model registry (in-memory only) ---
    @classmethod
    def register_model(cls, name: str, model: "TrainedModel") -> None: ...
    @classmethod
    def get_model(cls, name: str) -> "TrainedModel":
        """Raises KeyError listing available names if not found."""
    @classmethod
    def list_models(cls) -> list[str]: ...

    # --- Inference (runtime use) ---
    @classmethod
    def classify(cls, features: "np.ndarray", model: "TrainedModel") -> str: ...

    @classmethod
    def classify_proba(cls, features: "np.ndarray", model: "TrainedModel") -> dict[str, float]:
        """Raises NotImplementedError if model.model_type == 'tree'."""

    @classmethod
    def predict(
        cls,
        model: "TrainedModel",
        surface: pygame.Surface,
        method: str = "hog",
    ) -> str:
        """Combines extract_features(surface, method) + classify()."""
```

---

## 16. Academic Demo Scenes

### 16.1 `src/engine/scenes/demo_menu_scene.py`

```python
class DemoMenuScene(BaseScene):
    def __init__(self) -> None: ...
    # Implements BaseScene abstract methods. No additional public API.
```

### 16.2 `src/engine/scenes/filter_demo_scene.py`

```python
class FilterDemoScene(BaseScene):
    def __init__(self) -> None: ...
    # Internal mode index 0-8 per 15_ACADEMIC_DEMO_SCENES.md §3.3.
    # No public API beyond BaseScene — all interaction via InputManager polling internally.
```

### 16.3 `src/engine/scenes/vision_demo_scene.py`

```python
class VisionDemoScene(BaseScene):
    def __init__(self) -> None: ...
    # Internal mode index 0-9 per 15_ACADEMIC_DEMO_SCENES.md §4.3.
```

### 16.4 `src/engine/scenes/pattern_demo_scene.py`

```python
class PatternDemoScene(BaseScene):
    def __init__(self) -> None: ...
    # Internal mode index 0-4 per 15_ACADEMIC_DEMO_SCENES.md §5.3.
    # Loads PatternRecognitionTools.load_model(ASSETS_DIR / "models" / "professor_sample.pkl")
    # on_enter() by default.
```

---

## 17. Boss Framework

### 17.1 `src/framework/entities/boss_base.py`

```python
from dataclasses import dataclass

@dataclass
class BossPhase:
    phase_index: int
    health_threshold: float
    attack_patterns: list[str]
    movement_type: str            # 'stationary' | 'bezier' | 'sine' | 'random_walk'
    speed_multiplier: float
    sprite_override: str | None = None
    filter_effect: str | None = None   # 'sobel' | 'canny' | 'tint_green' | ... | None


class BossBase(EnemyBase):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float,
        phases: list["BossPhase"],
        boss_name: str,
    ) -> None: ...

    def update(self, dt: float) -> None:
        """Extends EnemyBase.update with phase-transition checking."""

    # --- Phase transition protocol (provided, do not override) ---
    def _check_phase_transition(self) -> None: ...
    def _begin_phase_transition(self, next_phase_index: int) -> None: ...

    current_phase: int
    is_transitioning: bool
    transition_timer: float
    boss_name: str
```

**Reference subclass example** (El Venado Sagrado, Phase 1 only, illustrative):

```python
class BossVenado(BossBase):
    def __init__(self, spawn_position: pygame.Vector2) -> None:
        phases = [
            BossPhase(
                phase_index=0,
                health_threshold=6.0,
                attack_patterns=["STOMP", "CHARGE", "VINE_TOSS"],
                movement_type="sine",
                speed_multiplier=1.0,
                filter_effect="sobel",
            ),
            BossPhase(
                phase_index=1,
                health_threshold=0.0,
                attack_patterns=["VINE_SWEEP", "MUSHROOM_SPORE", "CHARGE"],
                movement_type="bezier",
                speed_multiplier=1.5,
                sprite_override="boss_venado_frenzy_drift.png",
                filter_effect="sobel",
            ),
        ]
        super().__init__(spawn_position, max_health=12.0, phases=phases, boss_name="El Venado Sagrado")
```

---

## 18. Exception Types Reference

Every framework module must raise one of these — never a bare `Exception` or an unrelated builtin where one of these is more specific:

```python
class FrameworkUsageError(Exception):
    """Student/stage code misused the framework API (e.g., missing TMX layer)."""

class EngineError(RuntimeError):
    """Unrecoverable engine-level failure."""
```

`FilterTools`/`VisionTools`/`PatternRecognitionTools` raise standard `TypeError`/`ValueError`/`KeyError`/`RuntimeError` as documented per-method in Documents 11–13 — they do not raise `FrameworkUsageError` (that is reserved for stage/entity construction misuse, not processing-call misuse).

---

## 19. Naming Convention Quick Reference

(Restates `02_CODEX_CONTEXT.md` §5.2 for fast lookup during code generation.)

| Element | Convention | Example |
|---|---|---|
| Module | `snake_case` | `enemy_walker.py` |
| Class | `PascalCase` | `EnemyWalker` |
| Method/function | `snake_case` | `apply_damage()` |
| Property | `snake_case` | `current_health` |
| Constant | `UPPER_SNAKE_CASE` | `PLAYER_MAX_HEALTH` |
| Private | leading underscore | `_collision_rect` |
| Event name string | `UPPER_SNAKE_CASE` | `"PLAYER_DAMAGED"` |
| Enum member | `UPPER_SNAKE_CASE` | `PlayerState.IDLE` |

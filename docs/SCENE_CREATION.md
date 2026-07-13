# Scene Creation Guide

## 1. Overview

All scenes inherit from `BaseScene` (`src/engine/scene/base_scene.py`). The scene lifecycle is managed by `SceneManager`, which maintains a stack of scenes (push/pop/replace).

---

## 2. Inherit from BaseScene

```python
from __future__ import annotations
from typing import TYPE_CHECKING
import pygame
from src.engine.scene.base_scene import BaseScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class MyScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        # Initialize your scene resources here
        self._background = None
        self._timer = 0.0
```

---

## 3. Lifecycle Methods

### `on_enter(self)`

Called when the scene becomes active. Set up game state, load assets, play music:

```python
def on_enter(self) -> None:
    self._background = pygame.Surface((320, 224))
    self._background.fill((30, 30, 60))
    self.context.scene_manager.transition.start_fade_in(0.5)
    audio = self.audio
    if audio is not None:
        audio.play_music("assets/music/bgm_scene.wav")
```

### `update(self, dt: float)`

Called every frame. Handle input, update game logic:

```python
def update(self, dt: float) -> None:
    im = self.input
    if im is None:
        return

    if im.is_action_just_pressed(Action.CONFIRM):
        self.context.scene_manager.replace(OtherScene(self.context))

    if im.is_action_just_pressed(Action.CANCEL):
        self.context.scene_manager.pop()

    self._timer += dt
```

### `draw(self, surface: pygame.Surface)`

Render everything to the given surface:

```python
def draw(self, surface: pygame.Surface) -> None:
    if self._background:
        surface.blit(self._background, (0, 0))
    # Draw other elements...
    self.context.scene_manager.transition.draw(surface)
```

### `on_exit(self)`

Clean up resources when the scene is removed:

```python
def on_exit(self) -> None:
    audio = self.audio
    if audio is not None:
        audio.stop_music()
    AssetLoader.clear_cache()
```

### Optional: `on_pause()` / `on_resume()`

Called when another scene is pushed on top / the top scene is popped.

---

## 4. GameContext Dependency Injection

`BaseScene` stores `self.context: GameContext`, which provides access to all engine subsystems:

| Property | Shortcut | Type | Purpose |
|---|---|---|---|
| `self.context.input_manager` | `self.input` | `InputManager` | Keyboard + controller input |
| `self.context.audio_manager` | `self.audio` | `AudioManager` | Music and SFX playback |
| `self.context.scene_manager` | — | `SceneManager` | Scene stack (push/pop/replace) |
| `self.context.event_bus` | `self.events` | `EventBus` | Pub/sub event dispatch |
| `self.context.clock` | — | `DeltaClock` | Global clock with `time_scale` |
| `self.context.save_manager` | — | `SaveManager` | Save/load persistence |
| `self.context.running` | — | `bool` | False to quit the game loop |

### Scene Navigation

```python
# Replace current scene
self.context.scene_manager.replace(NewScene(self.context))

# Push a scene on top (pauses current)
self.context.scene_manager.push(OverlayScene(self.context))

# Pop back to previous scene
self.context.scene_manager.pop()

# Fade transition
self.context.scene_manager.transition.start_fade_out(0.4)
self.context.scene_manager.transition.start_fade_in(0.5)
```

---

## 5. Input Handling via InputManager

Access input through `self.input` or `self.context.input_manager`. Actions are defined in `Action` enum (`src/engine/input/action_map.py`):

| Action | Default Key |
|---|---|
| `Action.MOVE_LEFT` | Left arrow / A |
| `Action.MOVE_RIGHT` | Right arrow / D |
| `Action.JUMP` | Space / W |
| `Action.CROUCH` | Down arrow / S |
| `Action.CONFIRM` | Z / Enter |
| `Action.CANCEL` | X / Escape |
| `Action.PAUSE` | Escape / P |

```python
if self.input.is_action_just_pressed(Action.CONFIRM):
    # Only true on the frame the key is first pressed

if self.input.is_action_held(Action.MOVE_RIGHT):
    # True every frame while held

if self.input.is_action_released(Action.JUMP):
    # True on the release frame
```

---

## 6. Scene Registry Registration

Non-stage scenes can be registered in the `SceneRegistry` (`src/engine/scenes/scene_registry.py`) for lazy loading via the academic demo menu:

```python
# In register_demo_scenes() in scene_registry.py:
reg.register("my_scene", lambda ctx: _build_scene(ctx, "my_scene_module", "MyScene"))
```

The registered key must match a module in `src/engine/scenes/`. The `_build_scene` helper handles the lazy import:

```python
def _build_scene(ctx: GameContext, module_name: str, class_name: str) -> BaseScene:
    import importlib
    mod = importlib.import_module(f"src.engine.scenes.{module_name}")
    cls = getattr(mod, class_name, None)
    return cls(ctx)
```

**For stage scenes**, do not register in `SceneRegistry`. Instead, instantiate them directly via navigation code (e.g., `WorldMapScene` creates and replaces with the appropriate `StageScene` subclass).

---

## 7. Full Example (TitleScene)

See `src/engine/scenes/title_scene.py` for a complete scene implementation with:
- Background rendering and logo animation
- Menu selection with keyboard and mouse
- Particle effects
- Scene transitions (push/replace)
- Audio playback
- Save manager integration


--- Traducción al Español ---

## Guía de Creación de Escenas

### Resumen
Todas las escenas heredan de `BaseScene`. El ciclo de vida es gestionado por `SceneManager`.

### Métodos del Ciclo de Vida
- `on_enter()` — Configurar estado, cargar assets, reproducir música
- `update(dt)` — Lógica por frame, manejo de entrada
- `draw(surface)` — Renderizado a la superficie dada
- `on_exit()` — Limpiar recursos

### Inyección de Dependencias (GameContext)
- `self.input` — InputManager
- `self.audio` — AudioManager
- `self.events` — EventBus
- `self.context.scene_manager` — SceneManager

Para ejemplos completos de código, consultar el documento original en inglés.

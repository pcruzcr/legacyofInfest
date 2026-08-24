---
document_id: "LOI-GUIDE-SCENE"
title: "Guía de creación de escenas"
aliases: ["Guía de creación de escenas", "Scene Creation Guide"]
tags: ["escena", "creacion", "guia", "tutorial"]
description: "Cómo escribir una escena nueva: ciclo de vida, contexto, entrada y registro"
source: "docs/SCENE_CREATION.md"
date_processed: "2026-08-11"
---

# Guía de creación de escenas

## 1. Panorama

Todas las escenas heredan de `BaseScene` (`src/engine/scene/base_scene.py`).
El ciclo de vida lo gobierna `SceneManager`, que mantiene una **pila** de
escenas: apilar, desapilar y sustituir.

Que sea una pila y no una variable es lo que permite que una pausa o un
inventario se abran **encima** del nivel sin destruirlo: al desapilar, el nivel
sigue donde estaba.

---

## 2. Heredar de `BaseScene`

```python
from __future__ import annotations
from typing import TYPE_CHECKING
import pygame
from src.engine.scene.base_scene import BaseScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class MiEscena(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        # Aquí se inicializan los recursos de la escena
        self._fondo = None
        self._temporizador = 0.0
```

---

## 3. Métodos del ciclo de vida

### `on_enter(self)`

Se llama cuando la escena pasa a estar activa. Es donde se prepara el estado,
se cargan los recursos y arranca la música:

```python
def on_enter(self) -> None:
    self._fondo = pygame.Surface((320, 224))
    self._fondo.fill((30, 30, 60))
    self.context.scene_manager.transition.start_fade_in(0.5)
    audio = self.audio
    if audio is not None:
        audio.play_music("assets/music/bgm_scene.wav")
```

### `update(self, dt: float)`

Se llama en cada fotograma. Aquí van la entrada y la lógica:

```python
def update(self, dt: float) -> None:
    im = self.input
    if im is None:
        return

    if im.is_action_just_pressed(Action.CONFIRM):
        self.context.scene_manager.replace(OtraEscena(self.context))

    if im.is_action_just_pressed(Action.CANCEL):
        self.context.scene_manager.pop()

    self._temporizador += dt
```

### `draw(self, surface: pygame.Surface)`

Dibuja todo sobre la superficie que se recibe:

```python
def draw(self, surface: pygame.Surface) -> None:
    if self._fondo:
        surface.blit(self._fondo, (0, 0))
    # Dibuja aquí el resto de elementos…
    self.context.scene_manager.transition.draw(surface)
```

### `on_exit(self)`

Libera los recursos cuando la escena se retira:

```python
def on_exit(self) -> None:
    audio = self.audio
    if audio is not None:
        audio.stop_music()
    AssetLoader.clear_cache()
```

### Opcionales: `on_pause()` y `on_resume()`

Se llaman cuando otra escena se apila encima y cuando la de encima se desapila.
Son las que permiten que un menú de pausa detenga el nivel sin recargarlo.

---

## 4. `GameContext`: la inyección de dependencias

`BaseScene` guarda `self.context: GameContext`, que da acceso a todos los
subsistemas del motor. Ninguno es un *singleton* global: se reciben, y por eso
una escena se puede probar sola.

| Propiedad | Atajo | Tipo | Para qué |
|---|---|---|---|
| `self.context.input_manager` | `self.input` | `InputManager` | Entrada de teclado y mando |
| `self.context.audio_manager` | `self.audio` | `AudioManager` | Música y efectos de sonido |
| `self.context.scene_manager` | — | `SceneManager` | La pila de escenas |
| `self.context.event_bus` | `self.events` | `EventBus` | Publicación y suscripción de eventos |
| `self.context.clock` | — | `DeltaClock` | Reloj global, con escala de tiempo |
| `self.context.save_manager` | — | `SaveManager` | Guardado y carga de la partida |
| `self.context.running` | — | `bool` | Ponerlo a `False` termina el bucle |

### Navegación entre escenas

```python
# Sustituir la escena actual
self.context.scene_manager.replace(EscenaNueva(self.context))

# Apilar una escena encima (la actual queda en pausa)
self.context.scene_manager.push(EscenaSuperpuesta(self.context))

# Volver a la escena anterior
self.context.scene_manager.pop()

# Transición con fundido
self.context.scene_manager.transition.start_fade_out(0.4)
self.context.scene_manager.transition.start_fade_in(0.5)
```

---

## 5. La entrada, a través de `InputManager`

Se accede con `self.input` o con `self.context.input_manager`. Las acciones
están declaradas en el enumerado `Action` (`src/engine/input/action_map.py`).

Nunca se leen teclas directamente: se leen **acciones**. Es lo que permite que
el jugador reasigne los controles y que el mando funcione sin tocar ninguna
escena.

| Acción | Teclas por defecto |
|---|---|
| `Action.MOVE_LEFT` | ← · A |
| `Action.MOVE_RIGHT` | → · D |
| `Action.JUMP` | Espacio · ↑ · W |
| `Action.CROUCH` | ↓ · S |
| `Action.CONFIRM` | Intro · Espacio · Z |
| `Action.CANCEL` | Escape · X |
| `Action.PAUSE` | Escape · P |

> **Corregido el 2026-08-11 (AUD-429).** Esta tabla decía «Espacio / W» para
> saltar y «Z / Intro» para confirmar, y se dejaba fuera la **flecha arriba**
> en `JUMP` y el **espacio** en `CONFIRM`. Las dos están enlazadas desde
> siempre en `DEFAULT_KEY_BINDINGS`. Que la flecha arriba salte importa más de
> lo que parece: es la tecla con la que la mitad de la gente prueba un
> plataformas por primera vez.

```python
if self.input.is_action_just_pressed(Action.CONFIRM):
    # Sólo cierto en el fotograma en que se pulsa

if self.input.is_action_held(Action.MOVE_RIGHT):
    # Cierto en todos los fotogramas mientras se mantiene

if self.input.is_action_released(Action.JUMP):
    # Cierto en el fotograma en que se suelta
```

También existe el **buffer de entrada** (AUD-373): `pulsada_en_buffer(accion)`
dice si la acción se pulsó en los últimos fotogramas, aunque no fuera en éste.
Es lo que hace que saltar justo antes de aterrizar funcione en vez de perderse.

---

## 6. Registro en `SceneRegistry`

Las escenas que **no** son escenarios se pueden registrar en `SceneRegistry`
(`src/engine/scenes/scene_registry.py`) para que el menú de demos académicas
las cargue de forma perezosa:

```python
# Dentro de register_demo_scenes(), en scene_registry.py:
reg.register("mi_escena", lambda ctx: _build_scene(ctx, "mi_modulo", "MiEscena"))
```

La clave registrada tiene que corresponder a un módulo de
`src/engine/scenes/`. El ayudante `_build_scene` se encarga de la importación
perezosa:

```python
def _build_scene(ctx: GameContext, module_name: str, class_name: str) -> BaseScene:
    import importlib
    mod = importlib.import_module(f"src.engine.scenes.{module_name}")
    cls = getattr(mod, class_name, None)
    return cls(ctx)
```

**Los escenarios no se registran aquí.** Se instancian directamente desde el
código de navegación — por ejemplo, `WorldMapScene` construye la subclase de
`StageScene` que toque y la pone en su sitio.

La carga perezosa no es un adorno: importar el laboratorio de la Unidad IX
arrastra scikit-learn, y hacerlo al arrancar costaba **2.461 ms** de congelación
(AUD-288).

---

## 7. Un ejemplo completo

`src/engine/scenes/title_scene.py` es una escena terminada, con:

- fondo dibujado y animación del logotipo;
- selección de menú con teclado y ratón;
- efectos de partículas;
- transiciones entre escenas (apilar y sustituir);
- reproducción de audio;
- integración con el gestor de guardado.

---

## 🔗 Documentos relacionados

- [[STAGE_CREATION.md|Guía de creación de escenarios]]
- [[03_ARCHITECTURE.md|Arquitectura]]

---
document_id: "LOI-HUD-009"
title: "Legacy of InFest — HUD Specification"
aliases: ["HUD Specification", "HUD Spec"]
tags: ["hud", "ui", "specification"]
description: "HUD layout, hearts, timer, messages, Game Over"
source: "docs/09_HUD_SPEC.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — HUD Specification

**Document ID:** LOI-HUD-009  
**Version:** 1.1.0  
**Status:** Official  
**Audience:** Professor, Teaching Assistants, AI coding assistants

---

<!-- cita-historica -->
> **Corrección AUD-150 — nombres que este documento daba por existentes.**
> Comprobados uno por uno contra el código. Ninguno rompe nada al jugar; todos
> engañan a quien lea el documento para programar.
>
> * `hurt_display_timer` y `reveal_count` **no existen.** Son nombres de un pseudocódigo que nunca se escribió así: el HUD no lleva esos contadores.
> * `Message` **no es un tipo de objeto de Tiled.** El tipo se llama `MessageTrigger` (y `MessageTrigger_Once`). Un estudiante que escriba «Message» recibe un aviso de tipo desconocido.
<!-- /cita-historica -->


## 1. Overview

The HUD (Heads-Up Display) is the persistent on-screen layer that communicates player state, stage information, and game events to the player. All HUD elements are drawn in screen space — they do not move with the camera. They are rendered on top of all stage content on every frame.

The HUD is implemented in `engine/ui/hud.py` and is a professor-owned system. Students do not modify the HUD. Students may trigger HUD elements through the EventBus (`SHOW_MESSAGE`, etc.).

All HUD graphics are pixel art sprites consistent with the SNES-era aesthetic. No anti-aliasing. No gradients. No alpha-blended shadows. Transparency is used only for tutorial message box backgrounds.

---

## 2. Layout

The HUD occupies fixed regions of the 320×224 internal screen. All coordinates are in pixels, origin at top-left.

```
┌──────────────────────────────────────────────────────────────┐  Y=0
│  ═══════════════════════════════════════════════════════════  │
│  │   TUTORIAL / STORY MESSAGE BOX (if active)               │  Y=0
│  │   320×28 pixels, top of screen                          ││
│  │                                                           │  Y=14
│  └─────────────────────────────────────────────────────────┘ │
│  [PORTRAIT]  [♥♥♥♥♥]                          [TIMER: 0:00] │  Y=16
│   32×32       76×8                               54×12       │
│                                                               │  Y=28
│                                                               │
│                                                               │  Y=224
└──────────────────────────────────────────────────────────────┘
```

### 2.1 HUD Regions

| Element | X | Y | Width | Height | Notes |
|---|---|---|---|---|---|---|
| Message box | 0 | 0 | 320 | 28 | Top overlay (moved from bottom in v1.1.0) |
| Portrait frame | 2 | 16 | 34 | 34 | Shifted down to accommodate message box |
| Portrait sprite | 3 | 17 | 32 | 32 | Inner sprite |
| Heart row | 38 | 20 | 76 | 8 | Five hearts at 14px each + 2px gap |
| Timer box | 262 | 16 | 56 | 12 | Right-aligned |
| Timer digits | 264 | 24 | — | — | Format: `M:SS` |
| Stage banner | 0 | 88 | 320 | 48 | Center screen, slide-in |

---

## 3. Portrait

### 3.1 Description

The portrait is a 32×32 pixel close-up sprite of the hooded player character, displayed in the top-left corner. It is static (not animated) during normal play. It animates in specific events.

### 3.2 Portrait States

| State | Sprite File | Trigger |
|---|---|---|
| Normal | `ui/portrait_normal.png` | Default |
| Hurt | `ui/portrait_hurt.png` | Player receives damage — display for 0.8s |
| Critical | `ui/portrait_critical.png` | Player health ≤ 1.0 heart |
| Dead | `ui/portrait_dead.png` | Player health == 0 |

### 3.3 Portrait Frame

The portrait is surrounded by a 1px border frame drawn from the tileset `ui/hud_frame.png`. The frame is a 9-slice scalable sprite: corners are 2×2, edges are 1px thick.

### 3.4 Portrait State Logic

```
if current_health == 0:
    portrait_state = "DEAD"
elif current_health <= 1.0:
    portrait_state = "CRITICAL"
elif temporizador_de_dolor > 0:
    portrait_state = "HURT"
    temporizador_de_dolor -= dt
else:
    portrait_state = "NORMAL"
```

Ese temporizador dura 0,8 s desde cada `PLAYER_DAMAGED`. **Es pseudocódigo**: el HUD real no lleva un campo con ese nombre (AUD-150).

---

## 4. Heart System

### 4.1 Heart Meter Layout

The heart meter displays five heart icons in a horizontal row at X=38, Y=6. Each heart icon is 14×8 pixels (wide format for SNES clarity). Hearts are drawn left to right. The leftmost heart represents the first full heart; the rightmost heart represents the last fraction.

**Heart spacing:** 14px icon + 2px gap = 16px per slot. Total width: 5×14 + 4×2 = 78px.

### 4.2 Heart Icon Sprites

| State | File | Description |
|---|---|---|
| Full | `ui/heart_full.png` | Solid heart, 14×8 px |
| Three-quarter | `ui/heart_three_quarter.png` | Right 25% empty |
| Half | `ui/heart_half.png` | Right half empty |
| Quarter | `ui/heart_quarter.png` | Only left quarter solid |
| Empty | `ui/heart_empty.png` | Outline only |

### 4.3 Heart Rendering Algorithm

For each of the five heart slots (i = 0 to 4):

```python
heart_value = clamp(current_health - i, 0.0, 1.0)

if heart_value >= 1.0:
    sprite = "heart_full"
elif heart_value >= 0.75:
    sprite = "heart_three_quarter"
elif heart_value >= 0.50:
    sprite = "heart_half"
elif heart_value >= 0.25:
    sprite = "heart_quarter"
else:
    sprite = "heart_empty"

blit(sprite, x=(38 + i * 16), y=6)
```

### 4.4 Heart Damage Flash

When `PLAYER_DAMAGED` is received, the heart meter flashes the lost heart:

- The heart icon that decreased flashes between its new state and its old state.
- Flash rate: alternates every 4 frames.
- Flash duration: 0.6 seconds (approximately 9 flashes at 60 FPS).

### 4.5 Heart Heal Effect

When `PLAYER_HEALED` is received (e.g., after a checkpoint restores health):

- Hearts fill from right to left in sequence.
- Each heart fills with a 0.1-second delay between them.
- A small sparkle particle effect plays at each heart as it fills (sprite: `ui/heart_sparkle.png`, 4 frames, 12 FPS).

---

## 5. Timer

### 5.1 Description

The timer is displayed in the top-right corner of the HUD. It shows elapsed time in `M:SS` format (minutes and seconds). Stage 0 uses an ascending timer for demonstration purposes. Student stages use a descending countdown timer (configurable via `HUD.start_timer(seconds)`).

### 5.2 Timer Display

| Property | Value |
|---|---|
| Position | X=264, Y=24 (adjusted in v1.1.0 for message box at top) |
| Width | 54 px |
| Format | `M:SS` (e.g., `2:34`) |
| Font | **TTF** — `assets/fonts/game.ttf` at size 12, loaded through `AssetLoader.load_font` |
| Color | White on dark background |
| Background | Solid dark rectangle behind digits |

### 5.3 Timer Behavior

- **Ascending (Stage 0):** Counts up from `0:00`. No game over trigger.
- **Descending (Stage 1–3):** Counts down from `time_limit`. When it reaches `0:00`, emits `PLAYER_DIED` (causes Game Over).
- **Pause:** `HUD.pause_timer()` freezes the display. `HUD.resume_timer()` continues.
- **Flash on low time:** When ≤ 30 seconds remain on a countdown timer, the digits flash red at 2 Hz.

### 5.4 Timer Font

The timer renders through `AssetLoader.load_font` using `assets/fonts/game.ttf` at size 12 (`engine/ui/hud.py`).

> **AUD-098 — corregido contra el código.**
> Esta sección nombraba fuentes que el motor no usa. El reloj decía cargar
> `fonts/PixeloidSans.ttf`, **un fichero que no existe en el repositorio**;
> el banner, la caja de mensajes y la pantalla de fin de partida decían
> dibujarse con hojas de píxeles `.png`, que tampoco: la clase que sabía
> leerlas (`engine/ui/bitmap_font.py`) estaba muerta y se ha retirado.
>
> Todo el texto del juego pasa por `AssetLoader.load_font` sobre
> `assets/fonts/game.ttf`. Los `.png` de fuente siguen en `assets/fonts/`
> como material de referencia, pero ningún código los carga.


---

## 6. Stage Banner

### 6.1 Description

The stage banner slides in from both sides of the screen when a stage begins. It displays the stage number and stage name in large pixel text. After displaying, it slides back out.

### 6.2 Banner Layout

```
        ┌────────────────────────────────────┐
        │         STAGE  0                   │   Y=88, height=48
        │     THE  CORRIDOR  OF  TRUTHS      │
        └────────────────────────────────────┘
```

The banner is a composite of two horizontal strips that slide in from left and right respectively:
- Top strip (contains stage number): slides in from the left
- Bottom strip (contains stage name): slides in from the right

### 6.3 Banner Animation

| Phase | Duration | Easing |
|---|---|---|
| Slide in | 0.5 seconds | `ease_out_quad` |
| Hold | 2.0 seconds | Static |
| Slide out | 0.4 seconds | `ease_in_quad` |

During the banner animation, the game is still running (entities update, player can move). The banner is a purely visual overlay.

### 6.4 Banner Sprites

- Top strip: `ui/banner_top.png` — 320×24 px dark rectangle with gold border
- Bottom strip: `ui/banner_bottom.png` — 320×24 px dark rectangle with gold border
- Stage number font: `assets/fonts/game.ttf` at size 22 (`engine/ui/screen_banner.py`)
- Stage name font: `assets/fonts/game.ttf` at size 20 (same module)

### 6.5 Triggering the Banner

The banner is triggered automatically when a stage's `on_enter()` is called. The `ScreenBanner` reads the `stage_name` and `stage_id` from the stage's TMX map properties.

```python
# Called automatically from stage initialization:
self.screen_banner.play(stage_id="stage0", stage_name="The Corridor of Truths")
```

---

## 7. Tutorial Messages

### 7.1 Description

Tutorial messages are text boxes that appear at the bottom of the screen. They are triggered by `MessageTrigger` zones in the TMX map (see `06_TMX_SPEC.md` §10). They communicate framework system explanations, hints, and narrative flavor to the player.

### 7.2 Message Box Layout

```
┌──────────────────────────────────────────────────────────────┐ Y=0
│  ▶  Walk right to continue.                                  │
│     Use Z to attack enemies.                                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘ Y=28
```

| Property | Value |
|---|---|
| Position | X=0, Y=0 |
| Size | 320×28 px |
| Background | Semi-transparent dark (alpha 180/255) |
| Border | 1px solid gold |
| Text color | White |
| Font | `assets/fonts/game.ttf` at size 12 (`engine/ui/message_box.py`) |
| Max lines | 3 |
| Max chars/line | 58 (with left/right padding of 6px) |
| Indicator icon | `ui/message_arrow.png` — 5×7 arrow, animates when waiting for confirm |

### 7.3 Message Reveal Animation

Text reveals character by character at a rate of 30 characters per second (typewriter effect). Se implementa con un contador en coma flotante que sube `30 * dt` cada fotograma y del que se dibujan sólo los primeros `int(...)` caracteres. **El nombre del campo real está en `MessageBox`**; aquí se describe el algoritmo, no la variable (AUD-150).

### 7.4 Message Dismiss

Messages are dismissed in two ways:

1. **Auto-dismiss:** If `duration > 0`, the message is removed after `duration` seconds from when text reveal completes.
2. **Manual dismiss:** If `duration == 0`, the player must press `CONFIRM` (Enter/Z/A-button) to dismiss. The animated arrow indicator is shown when waiting for confirm.

### 7.5 Message Queue

If a second `SHOW_MESSAGE` event is emitted while a message is already displayed, the new message is queued. The queue processes messages in order.

### 7.6 Event Interface

```python
# Trigger a message from a stage (module-level emit works as well):
from src.engine.core.event_bus import emit
emit("SHOW_MESSAGE", text="Walk right to continue.\nUse Z to attack.", duration=5.0)

# Trigger a message requiring confirmation:
emit("SHOW_MESSAGE", text="Press Enter to continue.", duration=0)

# Clear all messages:
emit("HIDE_MESSAGE")
```

---

## 8. Game Over Screen

### 8.1 Description

When the player dies, the `GameOverScene` is pushed over the current stage. The stage is paused beneath it. The Game Over screen presents the player with two options.

### 8.2 Layout

```
        ╔══════════════════════════════════╗
        ║                                  ║  (Dark overlay, alpha 200/255)
        ║         G A M E   O V E R        ║  Y=80, centered
        ║                                  ║
        ║    ▶  CONTINUE                   ║  Y=120, option 1
        ║       QUIT TO TITLE              ║  Y=136, option 2
        ║                                  ║
        ╚══════════════════════════════════╝
```

### 8.3 Animation

1. Screen slowly darkens over 1.0 second (background alpha lerps from 0 to 200).
2. `GAME OVER` text appears via scanline wipe effect (top to bottom, 0.5 seconds).
3. Options fade in after the text is fully visible (0.3 second alpha lerp).

### 8.4 Options

| Option | Action |
|---|---|
| CONTINUE | Pop `GameOverScene`. Resume stage from last checkpoint. Restore player to full health. |
| QUIT TO TITLE | Replace scene stack with `TitleScene`. No state preservation. |

### 8.5 Selection Navigation

- `MOVE_UP` / `MOVE_DOWN` navigate between options.
- `CONFIRM` selects the highlighted option.
- The selected option is highlighted with a brighter color and the `▶` indicator.

### 8.6 Sprites

| Element | File |
|---|---|
| Background overlay | Filled `pygame.Surface` with `set_alpha()` |
| `GAME OVER` text | `assets/fonts/game.ttf`, via the shared UI kit |
| Option text | `assets/fonts/game.ttf`, via the shared UI kit |
| Selection arrow | `ui/menu_arrow.png` — 5×8 px |

---

## 9. Continue Screen

### 9.1 Description

If the player selects CONTINUE from the Game Over screen, the `GameOverScene` pops and the stage resumes. A brief visual confirmation plays:

1. The screen fades up from black over 0.5 seconds.
2. The player respawns at the checkpoint position with a "materialize" animation (player sprite fades in over 0.4 seconds, applying `set_alpha()` from 0 to 255).
3. The HUD heart meter refills from 0 to full using the heal animation (§4.5).
4. The stage timer resumes (if countdown, the timer does not reset — remaining time carries over).

### 9.2 Invincibility on Respawn

The player receives 2.0 seconds of invincibility immediately upon respawning (double the standard invincibility duration). This prevents instant re-death from nearby enemies that may have pursued the player to the checkpoint.

---

## 10. HUD Event Subscriptions

The HUD subscribes to the following EventBus events:

| Event | Handler | Effect |
|---|---|---|
| `PLAYER_DAMAGED` | `_on_player_damaged(amount, source)` | Update hearts, trigger hurt portrait, start flash |
| `PLAYER_HEALED` | `_on_player_healed(amount)` | Animate heart refill |
| `PLAYER_DIED` | `_on_player_died()` | Set portrait to DEAD; freeze timer |
| `CHECKPOINT_REACHED` | `_on_checkpoint(checkpoint_id)` | No HUD change (checkpoint handles visuals) |
| `SHOW_MESSAGE` | `_on_show_message(text, duration)` | Display message box |
| `HIDE_MESSAGE` | `_on_hide_message()` | Clear message box immediately |
| `STAGE_COMPLETE` | `_on_stage_complete()` | Hide HUD elements, begin fade-out |

---

## 11. HUD Integration with Stages

The HUD is instantiated once per application session by `App`. It is passed to each stage during initialization via the stage's `on_enter()` method.

```python
# In App initialization:
self.hud = HUD()

# In stage on_enter():
self.hud.start_timer(seconds=self.time_limit)  # 0 for ascending (Stage 0)

# In stage draw():
# HUD is drawn last — on top of everything
self.hud.update(dt)
self.hud.draw(self.internal_surface)
```

Students do not call `HUD.draw()` directly. The stage base class calls it automatically after the stage's own `draw()` method completes.


--- Traducción al Español ---

## Especificación del HUD

El HUD es la capa persistente en pantalla que comunica el estado del jugador, información del escenario y eventos del juego.

### Diseño
El HUD ocupa regiones fijas de la pantalla interna de 320×224. Todos los elementos se dibujan en espacio de pantalla (no se mueven con la cámara).

### Elementos
- **Retrato** — 32×32 px, esquina superior izquierda
- **Corazones** — 5 corazones, 14×8 px cada uno
- **Temporizador** — Formato M:SS, esquina superior derecha
- **Banner de Escenario** — Animación de entrada/salida
- **Mensajes Tutoriales** — Cuadro de texto en parte superior
- **Pantalla de Game Over** — Opciones Continuar / Salir al Título

Para la especificación completa de cada elemento con coordenadas, sprites y lógica de eventos, consultar el documento original en inglés.


---
## 🔗 Documentos Relacionados

- [[40_DIALOGUE_SYSTEM.md|Dialogue System]]
- [[04_PLAYER_SPEC.md|Player Specification]]

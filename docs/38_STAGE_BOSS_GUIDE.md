---
document_id: "LOI-GUIDE-038"
title: "Legacy of InFest — Guía Rápida de Creación de Stages y Bosses"
aliases: ["Stage Boss Guide"]
tags: ["stage", "boss", "guide", "creation"]
description: "Referencia rápida para construir escenarios y jefes"
source: "docs/38_STAGE_BOSS_GUIDE.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Guía Rápida de Creación de Stages y Bosses

**ID del Documento:** LOI-STAGEBOSS-QUICK-038  
**Versión:** 1.0.0  
**Estado:** Oficial  
**Audiencia:** Estudiantes (referencia rápida para construir su asignación)

> **AUD-455 (2026-08-13).** Tres correcciones verificadas contra el código
> real. §2.2 inventaba los tipos de `Collision` `Solid_OneWay`/`Hazard`/
> `Death` — la capa sólo admite `Solid` y `Platform`; poner ahí un peligro
> lo convierte en suelo sólido en silencio (ver `06_TMX_SPEC.md` §9.2). §3.2
> pasaba `phases=`/`boss_name=` al constructor de `BossBase`, que no los
> acepta — se fijan después con `set_phases()`/`set_boss_name()` (ver
> `BOSS_CREATION.md` §2 y `src/stages/boss_venado/boss_venado.py`). Y el
> mismo ejemplo definía `_get_animation_state()`, un nombre que la clase
> base nunca llama — el gancho real es `_get_animation_key()`.

---

## 1. Primeros Pasos

```bash
# 1. Clonar y setup
git clone <repo-url>
cd legacy-of-infest
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Crear tu branch
git checkout -b student/<tu_id>

# 3. Copiar plantilla
# Para Stage:
cp -r student_templates/stage_template/ src/stages/<tu_id>/
# Para Boss:
cp student_templates/boss_template/boss_template.py src/stages/<tu_id>/<tu_id>.py
```

---

## 2. Guía Rápida para Crear un Stage

### 2.1 Archivos que Necesitas

```
src/stages/<tu_id>/
├── <tu_id>.py          # Clase del stage (hereda de StageScene)
├── <tu_id>.tmx         # Mapa hecho en Tiled Map Editor
└── README.md           # Documentación de tu stage
```

### 2.2 Configurar el TMX en Tiled

Abre Tiled → Nuevo mapa:

| Propiedad | Valor |
|---|---|
| Orientation | Orthogonal |
| Tile size | 16×16 px |
| Map size | Mínimo 20×14 tiles (320×224 px) |
| Render order | Right-down |

**Capas requeridas (de abajo arriba):**

| Nombre | Tipo | Descripción |
|---|---|---|
| `BG_Far` | Tile | Fondo lejano (parallax 0.15) |
| `BG_Mid` | Tile | Fondo medio (parallax 0.40) |
| `BG_Near` | Tile | Fondo cercano (parallax 0.70) |
| `Terrain` | Tile | Terreno sólido principal |
| `Terrain_Detail` | Tile | Decoración no sólida |
| `Objects` | Objeto | Spawns, triggers, checkpoints |
| `Collision` | Objeto | Rectángulos de colisión |
| `FG_Overlay` | Tile | Foreground sobre entidades |

**Propiedades del mapa (custom properties):**

| Propiedad | Tipo | Ejemplo |
|---|---|---|
| `stage_id` | string | `stage1_2_la_soda` |
| `stage_name` | string | `"La Soda"` |
| `time_limit` | int | `120` |
| `bgm_track` | string | `bgm_stage0` |
| `background_zone` | string | `zone1` (opcional) |

**Objetos requeridos en `Objects`:**

| Objeto | Propiedades |
|---|---|
| `PlayerSpawn_01` | Punto de inicio del jugador |
| `NextTrigger_01` | Trigger de fin de nivel (full altura) |
| `Checkpoint_01` | Checkpoint con `checkpoint_id=0` |

**Colisiones en `Collision`:**

La capa `Collision` sólo admite **dos** tipos — cualquier otro valor, o ninguno, se trata como `Solid`:

| Tipo | Descripción |
|---|---|
| `Solid` | Paredes, pisos, techos (colisión completa) |
| `Platform` | Plataforma de un solo sentido (atravesable desde abajo) |

**Los peligros van en `Objects`, nunca en `Collision`.** `HazardZone` (daño al
contacto) y `DeathPit` (muerte instantánea) son objetos de la capa `Objects`,
con su propio `type` (ver `06_TMX_SPEC.md` §9.2). Ponerlos en `Collision` no
los convierte en zona de daño: los convierte en **suelo sólido**,
silenciosamente — es el error más común al construir un mapa.

### 2.3 Escribir la Clase del Stage

La clase hereda de `StageScene`, que provee automáticamente: sistema de colisiones, hazards, progression system (checkpoints/triggers), boss HUD, save/load, menú de pausa, SFX, y time scaling.

```python
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

class MiStage(StageScene):
    STAGE_ID: str = "<tu_id>"
    STAGE_NAME: str = "NOMBRE DE TU STAGE"
    ZONE: int = 1

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path("assets/maps/<tu_id>/<tu_id>.tmx"))

    # ── Hooks opcionales ────────────────────────────────────────────
    def on_stage_start(self) -> None:
        pass  # Setup adicional al cargar el stage

    def on_player_landed(self) -> None:
        pass  # Cuando el jugador toca suelo tras estar en aire

    def on_enemy_died(self, enemy) -> None:
        pass  # Cuando un enemigo muere

    def on_next_trigger_entered(self) -> None:
        pass  # Cuando el jugador toca NextTrigger

    def on_debug_toggle(self, enabled: bool) -> None:
        pass  # F1 toggle
```

### 2.4 Agregar Enemigos

Agrega enemies al TMX en la capa `Objects` con tipo `EnemyWalker`, `EnemyFlying` o `EnemyShooter`. Ver `docs/05_ENEMY_SPEC.md` para propiedades.

### 2.5 Agregar Features Académicas

```python
# En update(), después del código base:
from src.framework.processing.filter_tools import FilterTools
from src.framework.processing.vision_tools import VisionTools

# Ejemplo: ajustar brillo dinámicamente
brightness_surface = FilterTools.adjust_brightness(
    some_surface, factor=1.5
)

# Ejemplo: detección de bordes con Canny
edges = VisionTools.canny_edge(
    some_surface, low_threshold=50, high_threshold=150
)
```

### 2.6 Probar tu Stage

```bash
# Lanzar tu stage directamente (sin pasar por título)
python main.py --stage <tu_id>

# Pruebas unitarias
python -m pytest tests/ -v -k <tu_id>
```

---

## 3. Guía Rápida para Crear un Boss

### 3.1 Archivos que Necesitas

```
src/stages/<tu_id>/
├── <tu_id>.py          # Clase del boss (hereda de BossBase)
└── README.md           # Documentación de tu boss
```

Los bosses no requieren TMX (el arena se define en código o en un TMX separado).

### 3.2 Estructura de la Clase

```python
import pygame
from src.framework.entities.boss_base import BossBase, BossPhase

class MiBoss(BossBase):
    def __init__(self, spawn_position: pygame.Vector2):
        # `BossBase.__init__` NO acepta `phases` ni `boss_name` — se fijan
        # después, con `set_phases()` y `set_boss_name()`.
        super().__init__(
            spawn_position=spawn_position,
            max_health=100.0,
            damage_on_contact=0.5,
        )
        self.set_boss_name("Mi Boss")
        self.set_phases([
            BossPhase(
                phase_index=0,
                health_threshold=0.0,      # Transiciona en health < threshold
                attack_patterns=["SHOOT", "DASH"],
                movement_type="sine",
                speed_multiplier=1.0,
            ),
            # Fase 2 (health < 50%):
            # BossPhase(phase_index=1, health_threshold=0.5, ...)
        ])

    def _patrol_behavior(self, dt):
        # Movimiento idle/patrulla
        pass

    def _alert_behavior(self, dt):
        # Movimiento en combate + disparar ataques
        pass

    def _get_animation_key(self) -> str:
        return "idle"

    def _build_hitbox(self) -> pygame.Rect:
        # Hitbox de ataque en coordenadas locales
        return pygame.Rect(0, 0, 32, 32)

    def _build_hurtbox(self) -> pygame.Rect:
        # Hitbox de daño en coordenadas locales
        return pygame.Rect(0, 0, 32, 32)
```

### 3.3 Estructura de Fases

Cada `BossPhase` define:

| Campo | Descripción |
|---|---|
| `phase_index` | Índice 0-based |
| `health_threshold` | Salud threshold para activar esta fase (0.0 = fase inicial) |
| `attack_patterns` | Lista de nombres de ataques (`"SHOOT"`, `"DASH"`, `"VINE"`, etc.) |
| `movement_type` | `"stationary"`, `"bezier"`, `"sine"`, `"random_walk"` |
| `speed_multiplier` | Multiplicador de velocidad |
| `sprite_override` | Sprite sheet alternativo para esta fase |
| `filter_effect` | Efecto visual de FilterTools (`"sobel"`, `"canny"`, `"tint_green"`) |

### 3.4 Ciclo de Vida del Boss

```
1. Boss aparece → _patrol_behavior()
2. Jugador detectado → _alert_behavior()
3. Salud < threshold → is_transitioning = True (invulnerable)
4. Animación de transición (2-3 segundos)
5. Emite BOSS_PHASE_CHANGED
6. current_phase += 1
7. is_transitioning = False
8. Combate reanuda con nueva fase
```

### 3.5 Sprites del Boss

Coloca los spritesheets en `assets/sprites/bosses/<tu_id>/` con el formato:

```
<tu_id>_idle.png       # frames horizontales, frame_width×frame_height
<tu_id>_walk.png
<tu_id>_attack.png
<tu_id>_hurt.png
```

Cada PNG es un spritesheet con frames ordenados horizontalmente. `BossBase` carga `(frame_width, frame_height)` definidos en el constructor.

### 3.6 Probar tu Boss

```bash
# Lanzar tu boss directamente
python main.py --boss <tu_id>
```

---

## 4. Checklist de Entregable

### Stage

- [ ] TMX con las 8 capas requeridas
- [ ] `PlayerSpawn_01`, `NextTrigger_01`, `Checkpoint_01` en Objects
- [ ] Colisiones `Solid`, `Solid_OneWay`, etc. en Collision
- [ ] Al menos 2 tipos de enemigos (de los 3 disponibles)
- [ ] Propiedades de mapa completas (stage_id, stage_name, time_limit, bgm_track)
- [ ] Clase del stage hereda de `StageScene`
- [ ] `STAGE_ID`, `STAGE_NAME`, `ZONE` definidos como class attributes
- [ ] TMX con ruta correcta en `super().__init__()`
- [ ] Hooks opcionales sobreescritos según necesidad (`on_stage_start`, `on_player_landed`, `on_enemy_died`, `on_next_trigger_entered`)
- [ ] Funcionalidad académica de las unidades requeridas (filtros, visión, patrones)
- [ ] README.md con front-matter YAML, screenshots, explicación académica

### Boss

- [ ] Hereda de `BossBase`
- [ ] Mínimo 2 fases con distintos `attack_patterns`
- [ ] `_patrol_behavior()` y `_alert_behavior()` implementados
- [ ] `_build_hitbox()` y `_build_hurtbox()` definidos
- [ ] Spritesheets en `assets/sprites/bosses/<tu_id>/`
- [ ] Transiciones de fase funcionales (invulnerabilidad, animación, evento)
- [ ] Efecto académico (filter_effect o integración con FilterTools/VisionTools)
- [ ] README.md con tabla de fases y explicación académica

---

## 5. Referencias

| Para... | Documento |
|---|---|
| Diseño del mundo y zonas | `docs/16_WORLD_DESIGN.md` |
| Especificación de jefes | `docs/17_BOSS_SPEC.md` |
| Enemigos por zona | `docs/18_ENEMY_ROSTER.md` |
| Formato TMX detallado | `docs/06_TMX_SPEC.md` |
| API del framework | `docs/22_API_CONTRACTS.md` |
| Plantillas de estudiante | `docs/26_STUDENT_TEMPLATE_SPEC.md` |
| Rúbricas de evaluación | `docs/27_ACADEMIC_RUBRICS.md` |
| Flujo de trabajo git | `CONTRIBUTING.md` |
| Roadmap de implementación | `docs/63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` |


---
## 🔗 Documentos Relacionados

- [[STAGE_CREATION.md|Stage Creation Guide]]
- [[BOSS_CREATION.md|Boss Creation Guide]]

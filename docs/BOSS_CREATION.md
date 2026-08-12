---
document_id: "LOI-GUIDE-BOSS"
title: "Guía de creación de jefes"
aliases: ["Guía de creación de jefes", "Boss Creation Guide"]
tags: ["jefe", "creacion", "guia", "tutorial"]
description: "Cómo escribir un jefe: fases, movimiento, ataques, combos y la escena de arena"
source: "docs/BOSS_CREATION.md"
date_processed: "2026-08-11"
---

# Guía de creación de jefes

## 1. Panorama

Un jefe es un enemigo con **fases**. `BossBase`
(`src/framework/entities/boss_base.py`) extiende `EnemyBase` y añade:

- gestión de fases (la dataclass `BossPhase`);
- transiciones por umbral de vida;
- animación y eventos al cambiar de fase;
- tipo de movimiento, multiplicador de velocidad y efecto de filtro **por fase**;
- integración con el HUD del jefe.

---

## 2. Heredar de `BossBase`

```python
from __future__ import annotations
import pygame
from src.framework.entities.boss_base import BossBase, BossPhase

class BossMiJefe(BossBase):
    def __init__(self, spawn_position: pygame.Vector2) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=20.0,
            damage_on_contact=1.0,
        )
        self.set_boss_name("NOMBRE DE MI JEFE")
        self.rect.width = 36
        self.rect.height = 44

        self._load_boss_sprites("boss_mijefe", 48, 48)
        self.set_phases()
```

---

## 3. El sistema de fases

### La dataclass `BossPhase`

Son **diez** campos:

```python
@dataclass
class BossPhase:
    phase_index: int                     # empieza en 0
    health_threshold: float              # vida a la que entra esta fase
    attack_patterns: list[str]           # nombres de ataque, para _try_attack
    movement_type: str                   # "sine", "bezier", "stationary"
    speed_multiplier: float              # multiplicador de velocidad
    sprite_override: str | None          # prefijo de sprite alternativo
    filter_effect: str | None            # "sobel", "sobel_x" o None
    combos: dict[str, list[str]]         # ataque → cola de combo
    invulnerable: bool = False           # inmune durante toda la fase
    escala: float = 1.0                  # multiplicador de tamaño
```

> **Corregido el 2026-08-11 (AUD-429).** Esta guía documentaba **ocho** campos
> y son diez. Los dos que faltaban son de la fase 5.7 y valen para diseñar:
>
> * **`invulnerable`** — una fase entera inmune al daño. Es Nosk, Metal Sonic,
>   Mother Brain: sirve para una puesta en escena o para obligar a hacer otra
>   cosa antes de poder volver a golpear. Cuidado: una fase invulnerable **sin
>   nada que hacer** es una pausa forzada y se nota. El calificador no puede
>   distinguirlo; un jugador sí.
> * **`escala`** — el jefe crece. En el dossier de 185 análisis, once lo usan
>   como señal de cambio de fase.

### Declarar las fases

Sobreescribe `set_phases()`:

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

## 4. Métodos que hay que escribir

### `_patrol_behavior(self, dt: float)`

Encamina hacia el movimiento:

```python
def _patrol_behavior(self, dt: float) -> None:
    self._update_movement(dt)
```

### `_alert_behavior(self, dt: float)`

Movimiento más lógica de ataque:

```python
def _alert_behavior(self, dt: float) -> None:
    self._update_movement(dt)
    self._tick_attack_timers(dt)
    for patron in self.phases[self.current_phase].attack_patterns:
        self._try_attack(patron, dt)
```

### `_get_animation_key(self) -> str`

```python
def _get_animation_key(self) -> str:
    return "drift"  # animación en reposo
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

Una caja de daño **más pequeña** que la de golpe es lo que convierte al jefe en
un problema de posición y no de aguante.

---

## 5. Tipos de movimiento

Escribe `_update_movement(dt)` y ramifica según `phase.movement_type`:

```python
def _update_movement(self, dt: float) -> None:
    fase = self.phases[self.current_phase]
    velocidad = 60.0 * fase.speed_multiplier

    if fase.movement_type == "sine":
        self._elapsed += dt
        self.position.x += velocidad * dt * self.facing_direction
        self.position.y = self._base_y + 40.0 * math.sin(2 * math.pi * 0.4 * self._elapsed)
        # …y acotar a los límites de la arena

    elif fase.movement_type == "bezier" and self._bezier_path:
        self._bezier_t += self._bezier_speed * dt * fase.speed_multiplier
        pos = CurveTools.sample_path(self._bezier_path, self._bezier_t)
        self.position.x = pos[0]
        self.position.y = pos[1]
```

---

## 6. Los ataques

### Temporizadores

Cada ataque lleva su enfriamiento:

```python
self._attack_timers: dict[str, float] = {"SLAM": 0.0, "SPIT": 0.0}
self._attack_cooldowns: dict[str, float] = {"SLAM": 3.0, "SPIT": 5.0}
```

### Intentar un patrón

```python
def _try_attack(self, patron: str, dt: float) -> None:
    if self._attack_timers.get(patron, 0) > 0:
        return
    if patron == "SLAM" and self._player_is_close():
        self._do_slam()
    elif patron == "SPIT" and self._player_is_far():
        self._do_spit()
```

Que el ataque dependa de la **distancia** es lo que hace que el jefe se lea:
el jugador aprende que acercarse trae una cosa y alejarse otra.

### La cola de combos

```python
def _queue_combo(self, nombres: list[str]) -> None:
    self._combo_queue = list(nombres)
    self._combo_timer = 0.5

def _do_combo_slam_charge(self) -> None:
    self._attack_timers["CHARGE"] = 0.0
    self._do_charge()
```

---

## 7. Combate

### `apply_hit(damage, source_position)`

Sobreescríbelo para encadenar la muerte:

```python
def apply_hit(self, damage: float, source_position: tuple[float, float]) -> None:
    super().apply_hit(damage, source_position)
    if self.current_health <= 0 and self.is_alive:
        self.on_defeated()
```

### `on_defeated()`

Tu secuencia de muerte:

```python
def on_defeated(self) -> None:
    self.state = EnemyState.DYING
    self._death_timer = 1.5  # lo que dura la animación
```

### `_check_player_contact(self, player)`

Añade aquí la colisión de proyectiles y de zonas de ataque:

```python
def _check_player_contact(self, player: Player) -> None:
    super()._check_player_contact(player)
    for proj in self._projectiles:
        if proj["alive"] and proj_rect.colliderect(player.hurtbox):
            player.apply_damage(proj["damage"], self.rect.center)
            proj["alive"] = False
```

> **Llama a `super()`.** Cuatro enemigos del motor sobreescribieron el alias
> **público** de este método mientras el motor llamaba al privado, y el
> resultado fue que sus flechas y orbes no hacían daño durante meses sin que
> nada fallara (AUD-149).

---

## 8. Dibujado

Sobreescribe `draw()` para pintar proyectiles y zonas de ataque:

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

## 9. La escena de la arena (opcional)

```python
class BossMiJefeScene(StageScene):
    STAGE_ID: str = "boss_mijefe"
    STAGE_NAME: str = "MI JEFE"
    ZONE: int = 0

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path("assets/maps/boss_mijefe/boss_mijefe.tmx"))
```

Las arenas son fijas —320×224, sin desplazamiento—, así que **no hay plantilla
TMX para jefes**: se construye una en Tiled en blanco o se declara la geometría
en Python. Las dos formas valen y `boss_template.py` soporta ambas.

---

## 10. La referencia: `BossVenado`

`src/stages/boss_venado/boss_venado.py` es una implementación completa:

- **Fase 1** — movimiento senoidal, ataques `STOMP` / `CHARGE` / `VINE_TOSS`,
  filtro de bordes Sobel;
- **Fase 2** — recorrido de Bézier en forma de ocho, `VINE_SWEEP` /
  `MUSHROOM_SPORE`, filtro Sobel-X;
- encadenado de combos (`STOMP` → `CHARGE`, `SWEEP` → `SPORE`);
- gestión de proyectiles (liana por Bézier, dispersión de esporas);
- rectángulos de zona de ataque (pisotón y barrido);
- secuencia de muerte con partículas.

Se califica con `python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json`,
que corre en CI.

---

## 🔗 Documentos relacionados

- [[17_BOSS_SPEC.md|Especificación de jefes]]
- [[ENEMY_CREATION.md|Guía de creación de enemigos]]
- [[26_STUDENT_TEMPLATE_SPEC.md|Qué contienen las plantillas]]

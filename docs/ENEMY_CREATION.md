---
document_id: "LOI-GUIDE-ENEMY"
title: "Guía de creación de enemigos"
aliases: ["Guía de creación de enemigos", "Enemy Creation Guide"]
tags: ["enemigo", "creacion", "guia", "tutorial"]
description: "Cómo escribir un enemigo nuevo: herencia, métodos obligatorios, la máquina de estados y el registro"
source: "docs/ENEMY_CREATION.md"
date_processed: "2026-08-11"
---

# Guía de creación de enemigos

## 1. Panorama

Todos los enemigos heredan de `EnemyBase`
(`src/framework/entities/enemy_base.py`), que a su vez hereda de `BaseEntity`.
La clase base te da hechos: la máquina de estados, la detección del jugador, la
infraestructura de cajas de golpe y de daño, el daño por contacto, los
fotogramas de invulnerabilidad y la muerte.

Lo que escribes tú es **el comportamiento**: qué hace cuando patrulla y qué
hace cuando te ve.

---

## 2. Heredar de `EnemyBase`

```python
from __future__ import annotations
import pygame
from src.framework.entities.enemy_base import EnemyBase

class EnemyMiTipo(EnemyBase):
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

## 3. Métodos que hay que escribir

### `_build_hitbox(self) -> pygame.Rect`

Devuelve un rectángulo **en coordenadas locales** con la zona que hace daño al
jugador al tocarla:

```python
def _build_hitbox(self) -> pygame.Rect:
    return pygame.Rect(4, 2, 24, 28)
```

### `_build_hurtbox(self) -> pygame.Rect`

Devuelve un rectángulo **en coordenadas locales** con la zona por la que el
enemigo recibe daño:

```python
def _build_hurtbox(self) -> pygame.Rect:
    return pygame.Rect(4, 2, 24, 28)
```

Que sean dos rectángulos distintos y no uno es lo que permite un enemigo con
punto débil: una caja de daño pequeña en la espalda y una de golpe grande al
frente.

### `_get_animation_key(self) -> str`

Devuelve la clave de animación para los estados que no son `DYING` ni `HURT`:

```python
def _get_animation_key(self) -> str:
    return "walk"
```

Las claves tienen que corresponder a hojas de sprites cargadas por
`_load_zone_sprites()` o `_load_extra_sprites()`. Las que se cargan por defecto
son `"walk"`, `"hurt"` y `"die"`.

### `_patrol_behavior(self, dt: float) -> None`

Movimiento e IA cuando **no** hay jugador detectado:

```python
def _patrol_behavior(self, dt: float) -> None:
    self.position.x += self.facing_direction * self.patrol_speed * dt
```

### `_alert_behavior(self, dt: float) -> None`

IA cuando el jugador está dentro del rango de detección:

```python
def _alert_behavior(self, dt: float) -> None:
    self._face_player()
    self.position.x += self.facing_direction * self.alert_speed * dt
```

---

## 4. La máquina de estados

`_run_state_machine`, en `EnemyBase`, gestiona **trece** estados por su cuenta.

> **Corregido el 2026-08-11 (AUD-429).** Esta guía documentaba **siete**. Los
> otros seis existen desde que se añadieron y un estudiante que leyera sólo
> esto no sabía que su enemigo podía buscar, perseguir, replegarse o quedar
> aturdido. Seis estados invisibles en la guía son seis mecánicas que nadie usa.

| Estado | Lo dispara | Qué es |
|---|---|---|
| `IDLE` | `patrol_length = 0` | Enemigo estacionario. Sin este estado, uno quieto seguía «patrullando» sin moverse |
| `PATROL` | Por defecto, o al perder al jugador | Patrulla normal |
| `SEARCH` | Vio al jugador y lo perdió | Busca donde lo vio. Sin él, el enemigo se olvida en el acto |
| `ALERT` | Jugador detectado | Consciente del jugador |
| `CHASE` | Persecución activa | Distinto de `ALERT`: perseguir no es lo mismo que estar en guardia |
| `TELEGRAPHING` | Lógica del enemigo | El aviso antes de atacar (0,4 s por defecto) |
| `FIRING` | Tras el telegrafiado | Ejecuta el ataque |
| `RECOVER` | Tras atacar | Ventana de vulnerabilidad. Es **la** pieza que hace que un combate se pueda leer |
| `RETREAT` | Poca vida | Repliegue. `SquadBrain` ya emitía la táctica antes de que existiera el estado |
| `STUNNED` | Parada o golpe pesado | Aturdido. Recompensa al que hace *parry* |
| `HURT` | `apply_hit()` | Aturdimiento breve por daño |
| `LAUNCHED` | Empuje fuerte (≥ 1,5 de daño) | Por el aire, con gravedad |
| `DYING` | Vida ≤ 0 | Animación de muerte y retirada |

**Orden de prioridad:**
`DYING > LANZADO > HURT > STUNNED > TELEGRAPHING > FIRING > RECOVER > CHASE > ALERT > SEARCH > PATROL > IDLE`

### Ayudas para las transiciones

- `self._face_player()` — gira al enemigo hacia el jugador
- `self._telegraph_timer` / `self._telegraph_duration` — controlan el aviso
- `self.state = EnemyState.FIRING` — pasa a disparar, y entonces se llama a
  `_firing_behavior`

Sobreescribe `_firing_behavior(dt)` para decidir qué ocurre al atacar:

```python
def _firing_behavior(self, dt: float) -> None:
    # Lanza un proyectil y vuelve a estar alerta
    self._spawn_projectile()
    self.state = EnemyState.ALERT
```

---

## 5. La detección

Funciona sola. La clase base se encarga de:

- `detection_range_x` y `detection_range_y` — se fijan en el `__init__`;
- `set_player_ref(player_rect)` — lo llama `StageScene` para pasarle el
  rectángulo del jugador;
- `_check_detection_range()` — devuelve si el jugador está a tiro;
- **histéresis**: una vez en `ALERT`, el jugador tiene que salir del rango
  **más 32 px** para que vuelva a `PATROL`. Sin ese margen, un enemigo en el
  borde exacto parpadea entre los dos estados.

---

## 6. Ganchos opcionales

### `_pre_update(self, dt: float) -> bool`

Se llama al principio de `update()`. Devolver `True` **salta el resto** de la
actualización; es lo que usa `BossBase` para las transiciones de fase.

### `_post_update(self, dt: float)`

Se llama al final de `update()`. Lo usa `EnemyShooter` para mover sus
proyectiles.

### `_load_extra_sprites(self, zone: int, fw: int, fh: int)`

Carga hojas de sprites además de `walk`, `hurt` y `die`:

```python
def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
    ruta = settings.ASSETS_DIR / "sprites" / "enemies" / f"zone{zone}" / "enemy_mitipo_shoot.png"
    frames = AssetLoader.load_sprite_sheet(ruta, fw, fh)
    self._sprite_frames["shoot"] = frames
```

---

## 7. Animaciones

La clase base espera las hojas en `assets/sprites/enemies/zone{zone}/`:

- `enemy_zone{zone}_walk.png`
- `enemy_zone{zone}_hurt.png`
- `enemy_zone{zone}_die.png`

La cadencia se ajusta con variables de clase:

```python
_ANIM_FPS = {"walk": 10.0, "hurt": 12.0, "die": 10.0, "shoot": 16.0}
_ALERT_ANIM_FPS = {"walk": 14.0}  # más rápido cuando está alerta
```

---

## 8. Registrar el enemigo

Aquí hay **dos caminos**, y el que te toca casi seguro es el segundo.

### 8.1 Desde tu propio paquete — el camino del estudiante

Es lo que pide el curso y lo que hacen las entregas. Al final de tu módulo, a
**nivel de módulo**:

```python
# src/stages/mi_nivel/mi_enemigo.py
from src.framework.stage.stage_loader import StageLoader

class MiEnemigo(EnemyBase):
    ...

StageLoader.register_entity("MiEnemigo", MiEnemigo)
```

La cadena `"MiEnemigo"` es lo que escribes en el campo `type` del objeto en
Tiled.

**A nivel de módulo, no dentro de una función.** Si registras dentro de un
método, esa línea sólo se ejecuta cuando alguien llama al método — y el
previsualizador, el validador y el calificador **abren tu mapa sin construir la
escena**. El resultado no es que falte el enemigo: es que aparece **otro**, el
que el bestiario tenga con ese nombre, y nada falla (AUD-418).

**Ponle un nombre propio.** Si registras `FlyingBird` o `ShooterFrog`, estás
sustituyendo una especie que el motor ya trae, y cuál de las dos aparece pasa
a depender de si tu función se ejecutó. `validate_tmx.py` te avisa de las dos
cosas.

### 8.2 Dentro del motor — sólo si añades un arquetipo

Los ocho arquetipos y el jefe de referencia se dan de alta en
`ensure_registered()`, dentro de `src/framework/entities/entity_factory.py`:

```python
_ENTITY_REGISTRY: dict[str, type[EnemyBase]] = {
    "Walker": EnemyWalker,
    "Flying": EnemyFlying,
    "Shooter": EnemyShooter,
    "Charger": EnemyCharger,
    "Archer": EnemyArcher,
    "Brute": EnemyBrute,
    "Caster": EnemyCaster,
    "Assassin": EnemyAssassin,
    "BossVenado": BossVenado,
}
```

Ojo: es una variable **local de esa función**, no un diccionario de módulo que
puedas importar y modificar desde fuera.

Y las **21 especies con nombre** —`WalkerInsect`, `ShooterQuetzal`…— no están
ahí: se registran en `_register_named_species()` a partir de
`bestiary_registry.SPECIES`, cada una como una factoría que aplica sus
estadísticas sobre el arquetipo que le corresponde. Si lo tuyo es una especie
nueva y no un arquetipo, ése es el sitio.

---

## 9. Un ejemplo completo

`src/framework/entities/enemy_walker.py` es un caminante terminado: patrulla,
detección de bordes para no caerse, persecución y ataque de embestida.

---

## 🔗 Documentos relacionados

- [[05_ENEMY_SPEC.md|Especificación de enemigos]]
- [[18_ENEMY_ROSTER.md|Bestiario: las 21 especies]]
- [[BOSS_CREATION.md|Guía de creación de jefes]]

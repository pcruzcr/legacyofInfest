---
document_id: "LOI-ENEMY-005"
title: "Legacy of InFest — Especificación de enemigos"
aliases: ["Especificación de enemigos", "Enemy Specification"]
tags: ["enemigos", "especificacion", "entidad"]
description: "La clase base de enemigo y los 8 tipos de enemigo"
source: "docs/05_ENEMY_SPEC.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación de enemigos

**ID del documento:** LOI-ENEMY-005
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento completo (antes en inglés, con un
> resumen final que remitía de vuelta al inglés para la especificación
> completa) y corrige la numeración de subsecciones de §13–§16, que seguía
> citando los números 8–11 de una versión anterior del documento (por
> ejemplo, "### 9.2" bajo "## 14. Reglas de colisión").

---

---

## 0. Los cinco nombres que este documento tenía mal (AUD-150)

> Comprobado contra el código, uno por uno. Ninguno rompía nada al jugar;
> todos engañaban a quien leyera el documento para programar.

<!-- cita-historica -->

| El documento decía | En el código es | Qué pasó |
|---|---|---|
| `detection_rect` | `detection_range_x` y `detection_range_y` | La detección nunca fue un rectángulo guardado: son dos distancias que se comparan. §2 lo describe ahora así |
| `patrol_origin` | `_patrol_origin` | Existe, es privado. `patrol_length` sí es público y sí se lee del TMX |
| `WIND_UP` | `TELEGRAPHING` | El estado de aviso previo al ataque **sí existe**, con otro nombre y en el enum base. El Charger no añade estados propios: usa `TELEGRAPHING` y un temporizador de aturdimiento |
| `sfx_walker_die`, `sfx_flying_die`, `sfx_shooter_die` | `SFX_ENEMY_DIE_SMALL` y `SFX_ENEMY_DIE_LARGE` | **Corregido en AUD-133, y es mejor diseño que el documentado**: dos sonidos por tamaño en vez de uno por especie. Con treinta especies, treinta ficheros que mantener y treinta oportunidades de que falte uno |

<!-- /cita-historica -->

**Los trece estados reales**, leídos del enum `EnemyState`:

`IDLE`, `PATROL`, `SEARCH`, `ALERT`, `CHASE`, `TELEGRAPHING`, `FIRING`,
`RECOVER`, `RETREAT`, `STUNNED`, `HURT`, `LAUNCHED`, `DYING`.

<!-- cita-historica -->
**Ninguna subclase añade estados.** §12 dice que el Charger añade
`WIND_UP`/`CHARGE`/`STUN`; no los añade: usa `TELEGRAPHING` para el aviso,
`CHASE` para la embestida y `STUNNED` para la recuperación, que es justo lo
que esos tres nombres describían.
<!-- /cita-historica -->

---

## 1. Filosofía de los enemigos

### 1.1 Los enemigos como vehículo académico

Los enemigos de Legacy of InFest no están diseñados para la máxima dificultad de juego. Están diseñados para la máxima claridad educativa. Cada plantilla de enemigo demuestra una combinación distinta de conceptos del curso — búsqueda de camino con matemática de curvas, máquinas de estado de comportamiento, colisión e interacción, y retroalimentación de procesamiento visual.

Cada clase de enemigo es intencionalmente lo bastante simple como para que un estudiante la lea y la entienda en una sola sesión. Todo estudiante que construya un enemigo personalizado para su escenario debe poder explicar, en un README escrito, exactamente qué conceptos del curso implementa su enemigo y cómo.

### 1.2 Restricciones de diseño de enemigos

| Restricción | Razón |
|---|---|
| Máximo 3 tipos de enemigo por escenario de estudiante | Mantiene el alcance manejable; obliga a profundidad antes que amplitud |
| Todos los enemigos heredan de `EnemyBase` | Garantiza compatibilidad de ciclo de vida con el sistema de escenario |
| Los enemigos se comunican con el jugador sólo vía EventBus | Evita acoplamiento fuerte |
| Los enemigos no llaman a `InputManager` | Los enemigos son agentes autónomos; la entrada es un sistema exclusivo del jugador |
| Las paletas de sprite de enemigo no superan los 16 colores | Restricción de la época SNES |

### 1.3 Taxonomía de enemigos

El framework da tres arquetipos de enemigo (más cinco tipos especialistas avanzados). Los estudiantes pueden heredar de cualquiera de ellos para crear variaciones en sus escenarios.

| Clase | Movimiento | Ataque | Foco académico |
|---|---|---|---|
| `EnemyWalker` | Patrulla horizontal | Daño de contacto | Máquinas de estado, colisión |
| `EnemyFlying` | Vuelo curvo/por waypoints | Daño de contacto | Matemática de curvas, interpolación |
| `EnemyShooter` | Estacionario o patrulla lenta | Emisión de proyectiles | Detección de rango, trigonometría |

---

## 2. Clase base de enemigo — `EnemyBase`

`EnemyBase` es la clase raíz abstracta de todos los enemigos. Hereda de `BaseEntity` y añade el sistema de salud, la recepción de daño, el manejo de la muerte, la infraestructura de hitbox/hurtbox y la gestión de estado de animación.

### 2.1 Propiedades

| Propiedad | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `max_health` | float | Definido por subclase | Puntos de vida máximos |
| `current_health` | float | `max_health` | Puntos de vida actuales |
| `is_alive` | bool | `True` | Falso cuando la vida llega a 0 |
| `facing_direction` | int | `1` (derecha) | -1 para izquierda, +1 para derecha |
| `state` | str | `"PATROL"` | Nombre del estado actual de la máquina de estados |
| `hitbox` | pygame.Rect | Definido por subclase | Zona que inflige daño |
| `hurtbox` | pygame.Rect | Definido por subclase | Zona que recibe daño |
| `damage_on_contact` | float | 0.50 | Corazones de daño al colisionar hurtbox |
| `contact_knockback` | float | 120.0 | Velocidad de empuje horizontal aplicada al jugador |

<!-- cita-historica -->
> **AUD-150: `death_sfx` y `hit_sfx` no son atributos y nunca lo fueron.**
> Un enemigo no guarda el nombre de su sonido: **emite un evento** y la escena
> decide qué suena. `EnemyBase._die` emite `SFX_ENEMY_DIE_SMALL` o `_LARGE`
> según el tamaño, y el golpe emite `SFX_ENEMY_HIT`. Es mejor así: cambiar el
> sonido de la muerte de todo el bestiario es una línea en `StageScene`, no
> treinta atributos.
<!-- /cita-historica -->

### 2.2 A sobreescribir obligatoriamente

Las subclases deben implementar:

| Método | Firma | Descripción |
|---|---|---|
| `_patrol_behavior(dt)` | `(float) → None` | Movimiento/IA por defecto cuando no se detecta al jugador |
| `_alert_behavior(dt)` | `(float) → None` | IA cuando el jugador está dentro del rango de detección |
| `_get_animation_key()` | `() → str` | Devuelve la clave de animación del estado actual (las subclases la sobreescriben; la base `_get_animation_state()` la llama) |
| `_build_hitbox()` | `() → pygame.Rect` | Define el rectángulo de hitbox en espacio local |
| `_build_hurtbox()` | `() → pygame.Rect` | Define el rectángulo de hurtbox en espacio local |

### 2.3 Métodos provistos (no sobreescribir)

| Método | Descripción |
|---|---|
| `apply_hit(damage, source_position)` | Aplica daño, dispara el estado de daño, emite eventos |
| `_die()` | Gestiona la muerte: reproduce la animación, emite `ENEMY_DIED`, programa la eliminación |
| `_update_invincibility(dt)` | Descuenta el temporizador de invencibilidad, alterna el parpadeo |
| `_check_player_contact(player)` | Si las hurtbox se solapan, inflige daño de contacto al jugador |
| `_update_rects()` | Recalcula las posiciones de mundo de hitbox y hurtbox a partir de los desplazamientos locales |
| `update(dt)` | Actualización maestra: avanza la máquina de estados, llama al comportamiento, actualiza rects y animación |
| `draw(surface, camera_offset)` | Vuelca el fotograma de animación actual, opcionalmente dibuja rects de depuración |

### 2.4 Ciclo de vida

```
Se instancia EnemyBase
    ↓
Se llama a on_spawn() (sobreescritura opcional)
    ↓
Cada fotograma: update(dt)
    ├── _update_invincibility(dt)
    ├── _run_state_machine(dt)
    │     ├── state == "PATROL" → _patrol_behavior(dt)
    │     ├── state == "ALERT" → _alert_behavior(dt)
    │     ├── state == "HURT" → cuenta atrás del temporizador de daño
    │     └── state == "DYING" → avanza la animación de muerte → _die()
    ├── _update_rects()
    └── _check_player_contact(player)
    ↓
apply_hit() la llama el sistema de colisión del ataque del jugador
    ├── current_health -= damage
    ├── si current_health <= 0: state = "DYING"
    └── si no: state = "HURT", arranca hurt_timer
    ↓
Termina la animación de muerte
    ├── EventBus.emit("ENEMY_DIED", entity_id, position)
    └── is_active = False (se quita de la lista de entidades el siguiente fotograma)
```

### 2.5 Sistema de detección

<!-- cita-historica -->
Todos los enemigos comparten una comprobación de rango de detección. La posición del jugador se compara contra `detection_range_x` y `detection_range_y` — **dos distancias, no un rectángulo guardado** (AUD-150: este párrafo antes nombraba un `detection_rect` que nunca existió).
<!-- /cita-historica -->

| Propiedad | Por defecto | Descripción |
|---|---|---|
| `detection_range_x` | 160 píxeles | Medio ancho horizontal de la zona de detección |
| `detection_range_y` | 64 píxeles | Medio alto vertical de la zona de detección |

Cuando el jugador entra en la zona de detección, el enemigo pasa de `PATROL` a `ALERT`. Cuando el jugador sale de la zona de detección extendida por un `deaggro_margin` (32 píxeles por defecto), el enemigo vuelve a `PATROL`.

---

## 3. Enemigo Walker — `EnemyWalker`

### 3.1 Descripción

El Walker es un enemigo terrestre que patrulla horizontalmente a lo largo de un segmento definido. Invierte de dirección en los límites de patrulla o en los bordes de repisa. Cuando el jugador entra en su rango de detección, acelera hacia él.

El Walker es el enemigo más simple y el vehículo principal de demostración de:
- Comportamiento de máquina de estados horizontal
- Detección de borde de plataforma
- Daño de contacto y empuje
- Resolución básica de colisión

### 3.2 Atributos

| Atributo | Valor |
|---|---|
| Vida máxima | 2.0 corazones |
| Velocidad de patrulla | 45.0 px/s |
| Velocidad de alerta | 75.0 px/s |
| Daño de contacto | 0.50 corazones |
| Rango de detección X | 160 px |
| Rango de detección Y | 48 px |
| Longitud del segmento de patrulla | Definida en propiedades de TMX (96 px por defecto) |

### 3.3 Estados

| Estado | Comportamiento |
|---|---|
| `PATROL` | Se mueve a velocidad de patrulla en la dirección de cara. Invierte en el límite de patrulla o en el borde de repisa. |
| `ALERT` | Se mueve hacia el jugador a velocidad de alerta. Continúa hasta que el jugador sale de la zona de des-aggro. |
| `HURT` | Detiene el movimiento 0.25 segundos. Parpadea el sprite. |
| `DYING` | Reproduce la animación de muerte. Sin movimiento. |

### 3.4 Detección del límite de patrulla

El Walker guarda `_patrol_origin` (posición de aparición, privada) y un `patrol_length` público leído del TMX. Invierte cuando:

```
abs(position.x - _patrol_origin.x) >= patrol_length / 2
```

### 3.5 Detección de repisa

Antes de cada movimiento horizontal, el Walker sondea una baldosa por delante y una por debajo con un lanzamiento de punto contra la lista de rectángulos de colisión. Si no hay baldosa de suelo debajo del siguiente paso, el Walker invierte. Se calcula así:

```
probe_x = position.x + (facing_direction * (rect.width / 2 + 2))
probe_y = position.y + rect.height + 4
ledge_check = any(probe_x in r.x_range and probe_y in r.y_range for r in collision_rects)
```

### 3.6 Animaciones

| Estado | Fichero | Fotogramas | FPS | Bucle |
|---|---|---|---|---|
| Caminar | `enemy_walker_walk.png` | 6 | 10 | Sí |
| Caminar alerta | `enemy_walker_walk.png` | 6 | 14 | Sí |
| Daño | `enemy_walker_hurt.png` | 3 | 12 | No |
| Morir | `enemy_walker_die.png` | 6 | 10 | No |

### 3.7 Hitbox y hurtbox

El Walker no tiene hitbox de ataque activa — su daño es por contacto (solape de hurtbox con la del jugador).

| Caja | Desplaz. X | Desplaz. Y | Ancho | Alto |
|---|---|---|---|---|
| Hurtbox | 4 px desde el borde izquierdo del sprite | 2 px desde arriba | 24 px | 28 px |

---

## 4. Enemigo Flying — `EnemyFlying`

### 4.1 Descripción

El enemigo Flying viaja por el aire a lo largo de un camino calculado. En su implementación por defecto, el camino es una oscilación senoidal o una curva de Bézier definida por waypoints en el mapa TMX. Este enemigo es la demostración académica principal de:

- Curvas de Bézier y muestreo paramétrico de camino (Unidad III)
- Movimiento senoidal y matemática de trayectoria (Unidad III)
- Interpolación entre waypoints (Unidad VI)

### 4.2 Atributos

| Atributo | Valor |
|---|---|
| Vida máxima | 1.5 corazones |
| Velocidad de vuelo | 60.0 px/s (a lo largo del camino) |
| Amplitud senoidal | 28.0 px (por defecto) |
| Frecuencia senoidal | 1.5 Hz (por defecto) |
| Daño de contacto | 0.50 corazones |
| Rango de detección X | 180 px |
| Rango de detección Y | 96 px |

### 4.3 Seguimiento en Y (modo alerta)

Cuando el jugador entra en el rango de detección, el enemigo volador acelera la velocidad del camino ×1.5 y sigue activamente la posición Y del jugador. Usa un **desplazamiento de integrador con fuga** (`_y_track_offset`) que persiste entre fotogramas de estrategia:

```
# Cada fotograma en alerta:
# 1. La estrategia se ejecuta (resetea del todo position.y en los modos seno/bezier)
# 2. Calcula el error en Y: player_center_y - (position.y + _y_track_offset + rect.height/2)
# 3. Empuja el desplazamiento hacia el jugador a 0.4 × flight_speed
# 4. Amortigua el desplazamiento: _y_track_offset *= 0.98
# 5. Aplica: position.y += _y_track_offset
```

La amortiguación de 0.98 evita el sobregiro mientras mantiene al enemigo cerca de la posición vertical del jugador. El desplazamiento vuelve a 0.0 al regresar al estado PATROL.

### 4.4 Modos de vuelo

El modo de vuelo se especifica en las propiedades del objeto TMX:

| Modo | Clave de propiedad | Descripción |
|---|---|---|
| `sine` | `flight_mode=sine` | Movimiento horizontal con oscilación vertical senoidal |
| `bezier` | `flight_mode=bezier` | Sigue un camino de Bézier definido por objetos waypoint en el TMX |
| `patrol` | `flight_mode=patrol` | Vaivén lineal entre dos waypoints |

**Modo seno:**
```
position.x += speed * facing_direction * dt
position.y = origin.y + amplitude * sin(2π * frequency * elapsed_time)
```

**Modo Bézier:**
La capa de objetos TMX define los puntos de control como objetos `Waypoint` etiquetados con el `id` de este enemigo. La función `CurveTools.bezier(control_points, n_samples=64)` precalcula el camino al aparecer. El enemigo usa entonces `CurveTools.sample_path(path_points, t)` para hallar su posición actual, donde `t` avanza a `speed / path_length` por segundo.

### 4.5 Estados

| Estado | Comportamiento |
|---|---|
| `PATROL` | Follow defined flight path continuously |
| `ALERT` | Acelera la velocidad del camino x1.5, sigue el eje Y del jugador vía el desplazamiento de integrador con fuga (`_y_track_offset`, amortiguacion 0.98) que sobrevive a los reseteos de posicion de la estrategia |
| `HURT` | Se detiene 0.2 segundos. Parpadea. |
| `DYING` | Animacion de caida lenta con deriva horizontal. Deja de seguir el camino. |

### 4.6 Animaciones

| State | File | Frames | FPS | Loop |
|---|---|---|---|---|
| Volar | `enemy_flying_fly.png` | 4 | 12 | Sí |
| Alerta | `enemy_flying_fly.png` | 4 | 16 | Sí |
| Daño | `enemy_flying_hurt.png` | 3 | 12 | No |
| Morir | `enemy_flying_die.png` | 8 | 10 | No |

### 4.7 Hitbox y hurtbox

| Caja | Desplaz. X | Desplaz. Y | Ancho | Alto |
|---|---|---|---|---|
| Hurtbox | 6 px desde el borde izquierdo del sprite | 4 px desde arriba | 20 px | 14 px |

---

## 5. Enemigo Shooter — `EnemyShooter`

### 5.1 Descripción

El enemigo Shooter dispara proyectiles al jugador cuando se cumplen las condiciones de detección. Puede ser estacionario o patrullar despacio. Este enemigo demuestra:

- Detección de rango con cálculo de distancia (Unidad II — vectores)
- Cálculo de ángulo con `atan2` (Unidad II — vectores)
- El proyectil como sub-entidad con su propia velocidad y tiempo de vida (Unidad IV — sprites)

### 5.2 Atributos

| Atributo | Valor |
|---|---|
| Vida máxima | 3.0 corazones |
| Velocidad de patrulla | 20.0 px/s (si es móvil) |
| Velocidad del proyectil | 120.0 px/s |
| Daño del proyectil | 0.50 corazones |
| Cadencia de disparo | 1 shot per 2.0 seconds |
| Proyectiles activos máximos | 3 |
| Rango de detección X | 200 px |
| Rango de detección Y | 64 px |
| Daño de contacto | 0.25 corazones |

### 5.3 Estados

| Estado | Comportamiento |
|---|---|
| `PATROL` | Slow horizontal movement or idle |
| `ALERT` | Face player, enter firing stance |
| `FIRING` | Emit projectile at computed angle, respect fire rate |
| `HURT` | Interrumpe el disparo 0.4 segundos. Parpadea. |
| `DYING` | Play death animation. Expire all projectiles. |

### 5.4 Sistema de proyectiles

#### Projectile Entity

Cada proyectil disparado es una entidad `Projectile` ligera con estas propiedades:

| Propiedad | Valor |
|---|---|
| Velocidad | Calculada del angulo tirador → jugador en el momento del disparo |
| Lifetime | 3.0 seconds |
| Dano | Heredado del `projectile_damage` del tirador |
| Sprite | `enemy_shooter_projectile.png` (4×4 px glowing orb) |
| Hurtbox | 4×4 px, centered on position |
| Colision | Expira al tocar baldosas de colision O la hurtbox del jugador |

**Angle Calculation:**
```python
dx = player.rect.centerx - shooter.rect.centerx
dy = player.rect.centery - shooter.rect.centery
angle = math.atan2(dy, dx)  # Radians
velocity_x = math.cos(angle) * PROJECTILE_SPEED
velocity_y = math.sin(angle) * PROJECTILE_SPEED
```

Este calculo esta documentado en linea en el codigo fuente como ilustracion de la matematica vectorial de la Unidad II.

#### Projectile Lifecycle

```
El Shooter dispara:
  ├── Create Projectile at shooter's muzzle position
  ├── Fija la velocidad segun el calculo de angulo
  ├── Add to stage entity list
  └── Reset fire_cooldown_timer

Cada fotograma:
  ├── Update projectile position (velocity * dt)
  ├── Comprueba colision con baldosas solidas → expira
  ├── Comprueba solape de hurtbox con el jugador → inflige dano, expira
  └── Check lifetime elapsed → expire

Expiracion:
  └── is_active = False (removed next frame)
```

### 5.5 Animaciones

| State | File | Frames | FPS | Loop |
|---|---|---|---|---|
| Reposo/Patrulla | `enemy_shooter_idle.png` | 4 | 6 | Sí |
| Alerta/Apuntar | `enemy_shooter_aim.png` | 3 | 8 | No (mantiene el último) |
| Disparar | `enemy_shooter_fire.png` | 5 | 16 | No |
| Daño | `enemy_shooter_hurt.png` | 3 | 12 | No |
| Morir | `enemy_shooter_die.png` | 7 | 10 | No |

### 5.6 Hitbox y hurtbox

| Caja | Desplaz. X | Desplaz. Y | Ancho | Alto |
|---|---|---|---|---|
| Hurtbox | 4 px desde el borde izquierdo del sprite | 2 px desde arriba | 24 px | 30 px |

---

## 6. Enemigo Charger — `EnemyCharger`

### 6.1 Descripción

El Charger embiste al jugador a gran velocidad con un aviso previo. Su ciclo de ataque tiene tres fases, y **los tres son estados del enum base**: `TELEGRAPHING` (barra roja) → `CHASE` (embestida) → `STUNNED` (recuperación). Este enemigo demuestra:

- Maquina de estados de ataque multifase con temporizacion
- Indicadores de aviso para que el jugador pueda leer el ataque
- Dano variable segun el estado

### 6.2 Atributos

| Atributo | Valor |
|---|---|
| Vida máxima | 4.0 corazones |
| Velocidad de patrulla | 30.0 px/s |
| Velocidad de embestida | 250.0 px/s |
| Duración del aviso previo | 0.4 s |
| Duración de la embestida | 0.7 s |
| Duración del aturdimiento | 1.0 s |
| Daño de contacto (embestida) | 1.50 corazones |
| Daño de contacto (aturdido) | 0.50 corazones |
| Rango de detección X | 200 px |
| Rango de detección Y | 48 px |
| Duración del daño | 0.3 s |
| Invencibilidad tras el golpe | 0.4 s |

### 6.3 Estados

| Estado | Comportamiento |
|---|---|
| `PATROL` | Vaiven lento, gira a ±48 px del origen |
| `ALERT` | Faces player; if 40-180px away, begins `TELEGRAPHING` → `CHASE` → `STUNNED` |
| `TELEGRAPHING` | 0.4 s de aviso (barra roja) antes de embestir |
| `CHARGE` | Embiste a 250.0 px/s durante 0.7s, dano 1.5, luego entra en STUN |
| `STUN` | Se recupera 1.0s, dano reducido a 0.5, vuelve a ALERT |
| `HURT` | Se detiene 0.3s |
| `DYING` | Play death animation |

### 6.4 Rango de embestida

La embestida solo se dispara cuando el jugador esta entre 40 y 180 pixeles del Charger. Esta comprobacion de proximidad evita embestir desde fuera de pantalla o cuando el jugador ya esta demasiado cerca.

---

## 7. Enemigo Archer — `EnemyArcher`

### 7.1 Descripción

El Archer dispara proyectiles en arco al jugador con punteria predictiva y altura de arco variable. Este enemigo demuestra:

- Fisica de proyectil con gravedad y trayectoria en arco
- Punteria predictiva (adelanto) segun la distancia al jugador
- Ataques a distancia telegrafiados

### 7.2 Atributos

| Atributo | Valor |
|---|---|
| Vida máxima | 2.5 corazones |
| Velocidad de patrulla | 15.0 px/s |
| Velocidad del proyectil | 90.0 px/s |
| Daño del proyectil | 0.75 corazones |
| Cadencia de disparo | 1 shot per 3.75 s |
| Proyectiles activos máximos | 4 |
| Tiempo de vida del proyectil | 3.0 s |
| Rango de detección X | 220 px |
| Rango de detección Y | 80 px |
| Daño de contacto | 0.25 corazones |

### 7.3 Estados

| Estado | Comportamiento |
|---|---|
| `PATROL` | Patrulla horizontal lenta, gira a ±48 px del origen |
| `ALERT` | Faces player, counts down shoot cooldown |
| `TELEGRAPHING` | 0.4s telegraph (orange glow), then FIRING |
| `FIRING` | Dispara un proyectil en arco con punteria predictiva, fija el tiempo de espera |
| `HURT` | Interrumpe el disparo 0.35s |
| `DYING` | Play death animation |

### 7.4 Puntería predictiva

El Archer usa un `predict_factor` de 0.3 para adelantarse al objetivo segun la distancia del jugador. El proyectil sigue una trayectoria en arco: velocidad ascendente inicial con gravedad aplicada cada fotograma para crear una parabola.

---

## 8. Enemigo Brute — `EnemyBrute`

### 8.1 Descripción

El Brute es un enemigo cuerpo a cuerpo pesado con un ataque de onda de choque al golpear el suelo. Grande, lento y peligroso. Este enemigo demuestra:

- Ataque de area (AOE) con zona de dano retardada
- Indicador de aviso de varios fotogramas (rectangulo amarillo)
- draw() personalizado con la elipse visual de la onda de choque

### 8.2 Atributos

| Atributo | Valor |
|---|---|
| Vida máxima | 5.0 corazones |
| Velocidad de patrulla | 40.0 px/s |
| Tiempo de espera del golpe de tierra | 3.0 s |
| Duración del aviso | 0.3 s |
| Duración de la onda de choque | 0.4 s |
| Daño de la onda de choque | 1.50 corazones |
| Daño de contacto | 0.50 corazones |
| Rango de detección X | 120 px |
| Rango de detección Y | 60 px |

### 8.3 Estados

| Estado | Comportamiento |
|---|---|
| `PATROL` | Patrulla lenta, gira a ±64 px del origen |
| `ALERT` | Faces player, counts down slam cooldown (3.0s) |
| `TELEGRAPHING` | Aviso de 0.3s con barra amarilla, luego FIRING |
| `FIRING` | Activa la onda de choque 0.4s, inflige 1.5 de dano en area |
| `HURT` | Se detiene 0.35s |
| `DYING` | Play death animation |

### 8.4 Onda de choque

La onda de choque es una zona de dano (60x20 px a los pies del Brute) que permanece activa 0.4 segundos. Se dibuja una elipse visual (naranja/amarillo con desvanecimiento de alfa) en el suelo. El dano se aplica solo una vez por onda de choque, mediante un flag `_shockwave_has_hit`.

### 8.5 Aviso visual

Un rectangulo amarillo crece horizontalmente durante la fase de aviso, empezando en la posicion del Brute y expandiendose para indicar el area del AOE.

---

## 9. Enemigo Caster — `EnemyCaster`

### 9.1 Descripción

El Caster es un enemigo magico a distancia que dispara orbes teledirigidos al jugador. Mantiene activamente una distancia ideal. Este enemigo demuestra:

- Proyectil teledirigido con aceleracion
- IA de gestion de distancia (mantener el rango de combate ideal)
- Carga previa telegrafiada con un circulo purpura visual

### 9.2 Atributos

| Atributo | Valor |
|---|---|
| Vida máxima | 2.0 corazones |
| Velocidad de patrulla | 15.0 px/s |
| Velocidad del orbe | 120.0 px/s (acelera hasta el tope) |
| Daño del orbe | 0.75 corazones |
| Cadencia de disparo | 1 orb per 2.5 s |
| Orbes activos máximos | 5 |
| Tiempo de vida del orbe | 3.0 s |
| Distancia ideal | 150 px del jugador |
| Rango de detección X | 250 px |
| Rango de detección Y | 80 px |

### 9.3 Estados

| Estado | Comportamiento |
|---|---|
| `PATROL` | Patrulla lenta, gira a ±48 px del origen |
| `ALERT` | Mira al jugador, mantiene la distancia ideal, cuenta atrás el tiempo de espera |
| `TELEGRAPHING` | Aviso de 0.3s (círculo de carga púrpura), luego FIRING |
| `FIRING` | Dispara un orbe teledirigido, reinicia el tiempo de espera a 2.5s |
| `HURT` | Se detiene 0.3s |
| `DYING` | Play death animation |

### 9.4 Orbe teledirigido

HomingOrb acelera hacia el jugador a 60.0 px/s2, con tope de 120.0 px/s. Cada orbe tiene 3 segundos de vida y puede pararse con parry o destruirse por colision con la geometria del mundo.

### 9.5 Gestión de distancia

En estado ALERT, el Caster comprueba la distancia al jugador. Si esta a menos de 150 px, se aleja. Si esta mas lejos, se acerca. Esto mantiene al Caster en rango de combate efectivo.

---

## 10. Enemigo Assassin — `EnemyAssassin`

### 10.1 Descripción

El Assassin es un enemigo sigiloso que se camufla, flanquea y se lanza sobre el jugador. Se repliega tras un golpe fallido. Este enemigo demuestra:

- Mecanica de camuflaje/sigilo con transparencia de alfa
- IA de ataque multifase (flanquear → embestir → replegarse)
- Ciclo de ataque cuerpo a cuerpo con estado

### 10.2 Atributos

| Atributo | Valor |
|---|---|
| Vida máxima | 1.5 corazones |
| Velocidad de patrulla | 120.0 px/s |
| Velocidad de flanqueo | 80.0 px/s |
| Velocidad de embestida | 200.0 px/s |
| Velocidad de repliegue | 120.0 px/s |
| Daño de la embestida | 1.00 corazones |
| Duración de la embestida | 0.3 s |
| Duración del repliegue | 2.0 s |
| Rango de aproximación | 40 px (dispara la embestida) |
| Rango de detección X | 280 px (el mayor) |
| Rango de detección Y | 80 px |

### 10.3 Estados

| Estado | Comportamiento |
|---|---|
| `PATROL` | Patrulla rapida a 120.0 px/s, gira a ±64 px del origen |
| `ALERT` | Full FSM: flank (cloaked) → lunge → retreat (cloaked) |
| `HURT` | Se detiene 0.25s |
| `DYING` | Play death animation |

### 10.4 Camuflaje

Al flanquear o replegarse, el Assassin se renderiza con alfa semitransparente (80). Mientras esta camuflado, el dano de contacto se suprime. El camuflaje distingue visualmente las fases sigilosas de las agresivas.

### 10.5 Ciclo de ataque

1. **Flanquear**: se mueve en direccion opuesta al jugador (camuflado) hasta quedar a menos de 40px
2. **Embestir**: se descamufla, se lanza a 200 px/s hacia el jugador durante 0.3s, infligiendo 1.0 de dano
3. **Replegarse**: se camufla y se aleja a 120 px/s durante 2.0s
4. Repite desde el paso 1

---

## 11. Tabla resumen de atributos

| Attribute | EnemyWalker | EnemyFlying | EnemyShooter | EnemyCharger | EnemyArcher | EnemyBrute | EnemyCaster | EnemyAssassin |
|---|---|---|---|---|---|---|---|---|
| Vida máxima | 2.0 | 1.5 | 3.0 | 4.0 | 2.5 | 5.0 | 2.0 | 1.5 |
| Daño de contacto | 0.50 | 0.50 | 0.25 | 1.50 (charge) | 0.25 | 0.50 | 0.25 | 0.25 |
| Invencibilidad tras el golpe | 0.5 s | 0.3 s | 0.4 s | 0.4 s | 0.35 s | 0.5 s | 0.35 s | 0.35 s |
| Death SFX (AUD-133: por TAMAÑO, no por especie) | `sfx_enemies_die_small` | `sfx_enemies_die_small` | `sfx_enemies_die_small` | `sfx_enemies_die_large` | `sfx_enemies_die_small` | `sfx_enemies_die_large` | `sfx_enemies_die_small` | `sfx_enemies_die_small` |
| Tiene proyectiles | No | No | Sí | No | Sí (arco) | No | Sí (teledirigido) | No |
| Afectado por gravedad | Sí | No | Sí (si es móvil) | Sí | Sí | Sí | Sí | Sí |
| Límite de patrulla (por defecto) | 96 px | según camino | 48 px | 96 px | 96 px | 128 px | 96 px | 128 px |

---

## 12. Referencia de estados

Todos los enemigos comparten los nombres de estado base listados abajo. `EnemyState` define **trece** estados: `IDLE`, `PATROL`, `SEARCH`, `ALERT`,
`CHASE`, `TELEGRAPHING`, `FIRING`, `RECOVER`, `RETREAT`, `STUNNED`, `HURT`,
<!-- cita-historica -->
`LAUNCHED`, `DYING`. **Ninguna subclase añade estados** (AUD-150: aquí se decía
que el Charger añadía `WIND_UP`/`CHARGE`/`STUN`; usa `TELEGRAPHING`, `CHASE` y
`STUNNED`, que son esos mismos tres con los nombres del enum).
<!-- /cita-historica -->

Los trece, con lo que hace cada uno. **Todos están en el enum base y ninguna
subclase añade ninguno.**

| Estado | Quién lo usa | Qué es |
|---|---|---|
| `IDLE` | Estacionarios (`patrol_length = 0`) | Quieto. Sin este estado, uno inmóvil seguía «patrullando» sin moverse |
| `PATROL` | Todos | El movimiento por defecto |
| `SEARCH` | Todos | Vio al jugador y lo perdió: busca donde lo vio. Sin él, el enemigo se olvida en el acto |
| `ALERT` | Todos | Consciente del jugador |
| `CHASE` | Todos | Persecución activa. Distinta de `ALERT`: perseguir no es estar en guardia |
| `TELEGRAPHING` | Arquero, bruto, hechicero | El aviso antes de atacar |
| `FIRING` | Tirador, arquero, hechicero | Lanzando el proyectil |
| `RECOVER` | Todos | Ventana de vulnerabilidad tras atacar. Es **la** pieza que hace legible un combate |
| `RETREAT` | Todos | Repliegue con poca vida. `SquadBrain` ya emitía la táctica antes de que existiera el estado |
| `STUNNED` | Todos | Aturdido por un *parry* o un golpe pesado. Recompensa defenderse bien |
| `HURT` | Todos | Aturdimiento breve por daño |
| `LAUNCHED` | Empujados fuerte | Por el aire, con gravedad |
| `DYING` | Todos | Animación de muerte |

> **Corregido el 2026-08-11 (AUD-433).** El párrafo de arriba ya decía «trece»
> desde AUD-150, y **esta tabla seguía contradiciéndolo**: listaba siete
> estados y añadía `CHARGE` y `STUN` como «sólo de subclase», que es
> exactamente lo que AUD-150 había desmentido tres líneas antes. No existen:
> son `CHASE` y `STUNNED`, y están en el enum base como todos los demás.
>
> Una corrección aplicada al texto y no a la tabla es peor que no haberla
> hecho: deja el documento contradiciéndose consigo mismo, y quien lea sólo la
> tabla —que es lo que se consulta— se lleva el dato viejo.

---

## 13. Reglas de animación

### 13.1 Reglas generales

- Todas las hojas de sprite de enemigo son horizontales, con fotogramas de ancho igual.
- Todas las hojas miran a la derecha. Se aplica volteo horizontal cuando `facing_direction == -1`.
- Las animaciones sin bucle se mantienen en el ultimo fotograma hasta que el estado termina.
- Las animaciones con bucle reinician desde el fotograma 0 al completarse.

### 13.2 Regla especial de la animación de muerte

La animacion de muerte no se puede interrumpir. Una vez que se entra en `DYING`, ninguna llamada a `apply_hit()` tiene efecto. La entidad es inmune a mas cambios de estado hasta `is_active = False`.

### 13.3 Parpadeo durante daño/invencibilidad

Cuando un enemigo recibe un golpe y esta dentro de su ventana de invencibilidad:
- El alfa alterna entre 255 y 0 cada 4 fotogramas.
- El numero de parpadeos es `ceil(invincibility_duration * 60 / 4)`.

### 13.4 Regla de extensión de animación para estudiantes

Los estudiantes que creen subclases de enemigo personalizadas deben:
1. Anadir una hoja de sprites nueva en `student_assets/sprites/enemies/`.
2. Definir todas las entradas de animacion en el `__init__` de la subclase, usando `AssetLoader`.
3. Sobreescribir `_get_animation_state()` para devolver la clave correcta de los estados de la subclase.
4. No modificar ningun fichero de animacion existente en `assets/sprites/enemies/`.

---

## 14. Reglas de colisión

### 14.1 Enemigo contra baldosas sólidas

Walkers y Shooters participan en la gravedad y la colision de plataformas igual que el jugador (resolucion por ejes separados). Los enemigos voladores no aplican gravedad ni resuelven colision de baldosas: pasan por encima y a traves del terreno (su camino se define por encima del terreno).

### 14.2 Enemigo contra hurtbox del jugador (daño de contacto)

Cada fotograma, cada enemigo activo llama a `_check_player_contact(player)`. Si el rectangulo `hurtbox` del enemigo se solapa con el del jugador, y el jugador no es invencible:

1. Se llama a `player.apply_damage(self.damage_on_contact, self.rect.center, self.contact_knockback)` (la fuerza de empuje es 120.0 por defecto y se puede sobreescribir por enemigo).
2. Un tiempo de espera de 0.3 s evita aplicar dano repetido por un solape sostenido.

### 14.3 Ataque del jugador contra hurtbox de enemigo

La colision de la hitbox de ataque del jugador la comprueba el sistema de colision del escenario (no el enemigo). En el bucle de actualizacion del escenario:

```python
for enemy in active_enemies:
    if player.active_hitbox and player.active_hitbox.colliderect(enemy.hurtbox):
        enemy.apply_hit(
            damage=player.current_attack_damage,
            source_position=player.rect.center
        )
        player.consume_hitbox()  # Prevent multi-hit on same frame
```

### 14.4 Proyectil contra hurtbox del jugador

La colision del proyectil se comprueba en el propio metodo `update()` del proyectil:

```python
if self.hurtbox.colliderect(player.hurtbox):
    player.apply_damage(self.damage, source_position=self.rect.center)
    self.is_active = False
```

### 14.5 Enemigo contra enemigo

Los enemigos no colisionan entre si. Sus rectangulos se atraviesan. Esta simplificacion es intencionada: la colision enemigo-enemigo no es un objetivo academico y anade complejidad innecesaria.

---

## 15. Reglas de IA

### 15.1 Regla de detección

La deteccion no es linea de vision. Es una comprobacion de rango pura. Es intencionado: mantiene la IA lo bastante simple como para estudiarla y entenderla en el contexto de un ejercicio del curso.

```python
@property
def _player_in_range(self) -> bool:
    dx = abs(player.rect.centerx - self.rect.centerx)
    dy = abs(player.rect.centery - self.rect.centery)
    return dx <= self.detection_range_x and dy <= self.detection_range_y
```

### 15.2 Regla de orientación

Todos los enemigos siempre miran en la direccion de su movimiento actual. Estacionarios en estado `ALERT`, miran al jugador.

```python
if target_x < self.rect.centerx:
    self.facing_direction = -1
elif target_x > self.rect.centerx:
    self.facing_direction = 1
```

### 15.3 Momento de transición de estado

Las transiciones de estado no pueden ocurrir mas de una vez por fotograma. Si varias condiciones son ciertas a la vez (p. ej., jugador en rango Y vida a cero en el mismo fotograma), el orden de prioridad es:

```
DYING > HURT > ALERT > PATROL
```

### 15.4 Reglas de extensión de IA para estudiantes

Los estudiantes pueden extender la IA de enemigo dentro de su escenario heredando de las plantillas provistas. La IA personalizada debe:

1. Llamar a `super().update(dt)` para conservar el comportamiento base del ciclo de vida.
2. Implementar el comportamiento personalizado solo dentro de sobreescrituras de `_patrol_behavior()` o `_alert_behavior()`.
3. No saltarse la maquina de estados fijando `self.state` directamente desde fuera de la clase.
4. Documentar en un bloque de comentario el concepto academico que motiva la IA personalizada.

---

## 16. Ejemplos

### 16.1 Generar un Walker vía TMX

En la capa de objetos TMX, crea un objeto de tipo `Walker` con estas propiedades:

```
Type: Walker
Properties:
  patrol_length: 128
  damage_on_contact: 0.5
  patrol_speed: 40.0
```

`StageLoader` lee estas propiedades y se las pasa al constructor de `EnemyWalker`.

### 16.2 Subclase de enemigo personalizada (ejemplo de estudiante)

```python
# stages/stage1/entities/patrol_guard.py

from framework.entities.enemy_walker import EnemyWalker
from framework.processing.curve_tools import CurveTools

class PatrolGuard(EnemyWalker):
    """
    Una subclase de Walker que patrulla a lo largo de una curva de Bezier.
    Unidad academica III: curvas de Bezier y muestreo parametrico de camino.
    """

    def __init__(self, spawn_position, control_points, **kwargs):
        super().__init__(spawn_position, **kwargs)
        # Pre-compute Bézier path (Unit III concept)
        self.path = CurveTools.bezier(control_points, n_samples=80)
        self.path_t = 0.0
        self.path_speed = 0.4  # t-units per second

    def _patrol_behavior(self, dt: float) -> None:
        # Avanza a lo largo del camino de Bezier
        self.path_t = (self.path_t + self.path_speed * dt) % 1.0
        target = CurveTools.sample_path(self.path, self.path_t)
        dx = target[0] - self.position.x
        self.facing_direction = 1 if dx > 0 else -1
        self.position.x = target[0]
        self.position.y = target[1]
```

### 16.3 Visualización del rango de disparo del Shooter (modo depuración de Stage 0)

En Stage 0, el modo de depuracion dibuja el rectangulo de deteccion del Shooter como una capa amarilla semitransparente, y traza una linea del canon del Shooter al centro del jugador cuando esta en estado ALERT. Esta visualizacion se activa con la tecla `F1` y sirve de demostracion en vivo del calculo de distancia vectorial de la Unidad II.


---
## 🔗 Documentos relacionados

- [[18_ENEMY_ROSTER.md|Elenco de enemigos]]
- [[17_BOSS_SPEC.md|Especificación de jefes]]
- [[03_ARCHITECTURE.md|Arquitectura]]

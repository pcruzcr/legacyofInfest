# Boss Battle Design — El Rey Terciopelo

**Student Name:** PABLO  
**Boss Name:** El Rey Terciopelo (BossRey)

---

## 1. Boss Concept

El Rey Terciopelo es el jefe de Zona 2 ("El Datacenter"). Aparece como una figura grotesca colgada de hilos invisibles, moviéndose de forma errática como marioneta tirada por un titiritero frenético. Su Fase 1 ("La Marioneta") ocurre con 15–10 corazones de vida: se desplaza por la arena mediante una curva Catmull-Rom recalculada cada 0.3 s sobre 4 puntos de control aleatorios, y escupe globs de veneno cuando el jugador entra en rango (200 px). Las Fases 2 y 3 (división y frenesí) se implementan en la Práctica II.

El escenario es un **data center búnker enterrado bajo tierra**: el jugador entra por un corredor de servidores y cruza un portal de franjas de peligro hacia la sala del jefe, donde la cámara se bloquea y comienza la pelea.

---

## 2. Attack Patterns

| Attack Name | Type       | Damage | Cooldown | Description                                                              |
| ----------- | ---------- | ------ | -------- | ------------------------------------------------------------------------ |
| VENOM_SPIT  | projectile | 0.5    | 2.5 s    | Glob de veneno recto apuntado al jugador usando vectores de math_utils. Solo se dispara si la distancia al jugador ≤ 200 px. |

---

## 3. Phase Transitions

| Phase | HP           | Behaviour                                                    |
| ----- | ------------ | ------------------------------------------------------------ |
| 1     | 15–0 (Práctica I: 1 fase) | Movimiento Catmull-Rom errático + VENOM_SPIT cada 2.5 s en rango. |
| 2     | (Práctica II) | División en ReyMetad — no implementado.                     |
| 3     | (Práctica II) | Frenesí — no implementado.                                  |

---

## 4. Fórmulas Exactas (Unidades I–III)

### Unidad I — Coordenadas y Transformaciones

**Layout del mapa (70×37 tiles = 1120×592 px):**

```
corredor de entrada:  x = 0 … 578 px    (el jugador lo recorre antes de la pelea)
sala del jefe:        x = 578 … 1120 px (542 px de ancho)
piso (colisión):      y = 576
```

**Arena del boss** — no es el mapa completo, es el rect del `CameraLock`:

```
arena_bounds = CameraLock.rect = Rect(578, 270, 542, 321)
```

El framework asigna por defecto `arena_bounds = Rect(0, 0, map_w, map_h)` (el
mapa completo, corredor incluido). `BossReyScene.on_enter()` lo corrige al rect
del `CameraLock` para que el Rey no pueda caminar hacia el corredor.

**Posición del boss en el suelo** — se deriva del rect de colisión `Floor`, que
es el suelo real, **no** de `arena_bounds`:

```
floor_y = floor_surface_y - sprite_height
        = 576 - 50
        = 526   (posición de la cabeza)

pies = floor_y + sprite_height = 576 = superficie del piso   ✓
```

Esta separación importa: `arena_bounds` responde "¿hasta dónde puede caminar?"
y `floor_surface_y` responde "¿a qué altura camina?". Son preguntas distintas y
mezclarlas hacía flotar al jefe (ver §6).

**Spawn del boss** (stage_loader pasa la coordenada TMX cruda):

```
position.y = spawn_y_tmx - sprite_height
```

En el primer frame de movimiento la Y se reemplaza por `floor_y`, así que el
jefe se asienta en el suelo aunque el spawn del TMX no esté exacto.

**Cámara por zona** (punto ∈ rectángulo): la cámara se congela solo cuando el
centro del jugador está dentro del rect de la sala:

```
in_room = room_rect.collidepoint(player.rect.center)
        = (578 ≤ px < 1120) and (270 ≤ py < 591)
camera.locked_x = camera.locked_y = in_room
```

**Hurtbox** (centrada en el sprite 40×56):

```
ox = (sprite_w - hurtbox_w) // 2 = (40 - 28) // 2 = 6
oy = (sprite_h - hurtbox_h) // 2 = (56 - 48) // 2 = 4
hurtbox = Rect(6, 4, 28, 48)
```

---

### Unidad II — Vectores y Distancias (`math_utils`)

**Distancia jugador–boss para activar VENOM_SPIT:**

```
d = vec2_distance(boss_center, player_center)
  = sqrt((bx - px)^2 + (by - py)^2)
```

Se dispara solo si `d ≤ VENOM_SPIT_RANGE = 200`.

**Dirección normalizada del proyectil:**

```
dir = vec2_normalize(player_center - boss_center)
    = (player_center - boss_center) / |player_center - boss_center|
```

**Velocidad del glob de veneno:**

```
vel = dir * VENOM_SPIT_SPEED = dir * 90.0   [px/s]
```

**Posición del proyectil en cada frame:**

```
pos += vel * dt
```

---

### Unidad III — Curvas Catmull-Rom (`CurveTools`)

**Puntos de control** (1 actual + 3 aleatorios en la arena):

```
P_0 = (boss.x, boss.y)
P_1, P_2, P_3 = puntos aleatorios en [arena_left + 24, arena_right - 24] × {floor_y ± 5}
```

**Fórmula Catmull-Rom** (segmento entre P_i y P_{i+1} con parámetro t ∈ [0,1]):

```
q(t) = 0.5 * [ (2*P_1)
              + (-P_0 + P_2)*t
              + (2*P_0 - 5*P_1 + 4*P_2 - P_3)*t^2
              + (-P_0 + 3*P_1 - 3*P_2 + P_3)*t^3 ]
```

La curva pasa exactamente por cada punto de control (diferencia clave con Bézier, que solo pasa por los extremos). Esto produce el movimiento nervioso de marioneta.

**Muestreo de la ruta** (PATH_SAMPLES = 20 puntos por segmento):

```
para t en linspace(0, 1, PATH_SAMPLES):
    (x, y) = CurveTools.sample_path(path_points, t)
```

El path se recalcula cada `PATH_RECALC_INTERVAL = 0.3 s`.

---

## 5. Representación Gráfica (lógica del diseño visual)

### Capas TMX y Z-order (de atrás hacia adelante)

| Capa | Contenido | Por qué ahí |
|---|---|---|
| `BG_Far` | Muro interior claro y liso | Los tiles lisos (sin borde) dan máximo contraste: el jugador y el boss son oscuros y resaltan sobre la pared. |
| `BG_Mid` | Pilares, portal de franjas, bandeja de cables, tubería | Estructura a media distancia, con parallax. |
| `BG_Near` | Torres de racks con LEDs, monitores, consolas | Mobiliario "pegado a la pared": detrás de las entidades pero delante de la estructura. |
| `Terrain` | Tierra, grava, losa de concreto, viga, piso diamantado | El mundo sólido visual (la colisión real vive en el objectgroup `Collision`). |
| `Terrain_Detail` | Lámparas con cono de luz, cables colgando, racks en primer plano | Decoración al mismo plano que las entidades, sin colisión. |
| `FG_Overlay` | Vacía | Nada debe tapar al jugador ni al boss durante la pelea. |

### Tileset propio (`tileset_boss_rey_deco.png`)

Los tilesets base del curso solo traen paneles lisos, así que **creé un tileset
pixel-art de 32 tiles (16×16)** para contar la historia del escenario: el búnker
está *enterrado*. De arriba a abajo el mapa se lee: tierra con rocas → estrato
de grava → losa de concreto remachado → viga de acero → sala interior → piso de
placa diamantada. La tierra usa un **hash espacial XOR determinista**
(`((r·73856093) ⊕ (c·19349663)) mod 97`) para elegir entre 8 variantes de tile
sin patrones repetitivos visibles.

En el corredor los racks llevan LEDs ámbar/rojos (alerta) y en la sala el centro
queda despejado a propósito: donde patrulla el Rey la pared es lisa para que la
silueta del boss siempre se lea durante el combate.

### Entidades

- **Sprite:** 40×56 px, hojas "walk", "spit", "hurt", "death" (placeholders en Práctica I).
- **Hitbox:** `Rect(5, 3, 30, 50)` — área de golpe del boss al jugador.
- **Hurtbox:** `Rect(6, 4, 28, 48)` — área donde el jugador puede herir al boss.
- **Proyectil:** círculo verde oscuro de radio 4 px dibujado con `pygame.draw.circle`.
- **Mapa:** 70×37 tiles (1120×592 px): corredor de entrada (0–578 px) + sala del jefe (578–1120 px). Piso en y=576. `CameraLock` sobre la sala (lock_x=true, lock_y=true), aplicado por zona desde `BossReyScene.update()`.

---

## 6. Reflection

Los tres problemas más difíciles fueron todos de **sistemas de coordenadas**, y los tres se veían "bien" en pantalla hasta que se revisaron los números:

1. **`_floor_y` no descontaba el grosor del tile.** La fórmula original dejaba al
   boss con los pies 16 px *dentro* del piso. Corregido con
   `arena_bounds.bottom - 16 - rect.height`, que apoya los pies exactamente en
   la superficie transitable (y=560).

2. **`arena_bounds` es el mapa completo, no la sala.** El framework asigna
   `Rect(0, 0, map_w, map_h)` a todos los jefes. Mientras el mapa *era* la sala
   eso funcionaba por coincidencia; al agregar el corredor de entrada, el Rey
   podía caminar fuera de su arena hacia el pasillo. La corrección aplica el
   rect del `CameraLock` como `arena_bounds`, usando **una sola fuente de
   verdad** para la geometría de la sala en vez de duplicar coordenadas.

3. **`CameraLock` es un interruptor global, no una zona.** Leyendo
   `camera.py` se ve que `set_camera_locks()` hace
   `any(line.lock_x for line in locks)` — el campo `rect` se guarda pero nunca
   se lee. Un solo `CameraLock` en el mapa congela la cámara en todo el nivel
   desde el primer frame. `BossReyScene.update()` recalcula el bloqueo por
   posición (`rect.collidepoint(player.center)`) para que la cámara siga libre
   en el corredor y se fije solo al entrar a la arena.

4. **Acoplar dos sistemas de coordenadas distintos se paga caro.** Tras
   resolver (2), el suelo del jefe seguía saliendo de `arena_bounds` — que ya
   era el rect del `CameraLock`. Al reajustar el mapa en Tiled, el borde
   inferior del `CameraLock` cayó en `592.0`; `pygame.Rect` **trunca a entero**
   (591) y el jefe quedó caminando 1 px flotando, con el jitter amplificándolo
   hasta ~9 px. La corrección fue **desacoplar**: `floor_surface_y` se lee del
   rect de colisión `Floor` y `arena_bounds` solo limita el eje X. Ahora los
   pies caen en y=576 con desviación 0 px, y mover el `CameraLock` en Tiled ya
   no afecta la altura del jefe.

La lección transversal: la geometría hay que **verificarla numéricamente**, no
por inspección visual — un desfase de 1 px es invisible en pantalla pero delata
un error de modelo. Las correcciones se validan con un arnés headless
(`SDL_VIDEODRIVER=dummy`) que corre la escena real y comprueba `arena_bounds`,
la altura de los pies contra el piso real, el bloqueo de cámara por zona
(incluidos los píxeles frontera) y la posición del jefe durante 120 frames de
movimiento Catmull-Rom. El arnés **deriva sus expectativas del propio TMX** en
vez de codificar números, así sigue siendo válido al editar el mapa en Tiled.

---

*Evaluación Práctica I — Computación Gráfica y Procesamiento de Imágenes*

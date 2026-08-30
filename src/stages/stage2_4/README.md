---
assignment_type: boss
assignment_name: "El Rey Terciopelo"
assignment_id: stage2_4
zone: 2
student_name: "José Pablo Ramírez Sánchez"
units_demonstrated: [I, II, III, V, VI, VII, IX]
evaluation_milestone: "Evaluación Práctica II"
---

# El Rey Terciopelo — Jefe de Zona 2

**Estudiante:** José Pablo Ramírez Sánchez  
**Ejecutar con:** `python main.py --stage stage2_4`

---

## 1. Descripción

| | |
|---|---|
| **Nombre** | El Rey Terciopelo (`BossRey`) |
| **Ubicación** | Zona 2, Stage 2-4 — «El Datacenter» |
| **Objetivo del jugador** | Cruzar el corredor de servidores, entrar a la sala del jefe y **vaciar sus 15 corazones**. La cámara se bloquea al entrar: desde ahí no se puede huir. |
| **Mecánica principal** | **Leer el aviso y castigar la recuperación.** Cada ataque avisa entre 0.45 y 0.90 s —con pose propia y realce de silueta— y deja al jefe vulnerable al terminar. La pelea se gana observando, no machacando el botón. |
| **Mecánica secundaria** | **La luz es una decisión táctica.** El Rey caza por contraste: en penumbra falla la puntería y avanza más lento, pero acierta cuando sales a la luz. |
| **Inicio y final** | Empieza al entrar a la sala (bloqueo de cámara). Termina al llegar a 0 corazones. |
| **Progresión** | Tres fases que cambian la *intención* del jefe, no solo sus números: 15→10, 10→4 y 4→0. |
| **Dificultad** | Sube por **legibilidad decreciente**: la Fase 1 enseña a leerlo, la 2 obliga a repartir la atención entre dos enemigos y la 3 acorta los avisos y añade subtipos que no se anuncian. |

### Concepto

El Rey Terciopelo es el jefe de Zona 2 ("El Datacenter"). No es una criatura: son miles de serpientes terciopelo fundidas en una inteligencia colectiva que anima un cuerpo humanoide descompuesto como si fuera su **marioneta**. El cuerpo se mueve a tirones, de forma antinatural, gobernado desde dentro.

El combate recorre las **tres fases** del spec §4.3, y cada una cambia la *intención* del jefe, no solo sus números:

1. **«La Marioneta» (15 → 10 corazones)** — vagabundeo nervioso por una curva Catmull-Rom recalculada cada 0.3 s. Escupe veneno a distancia y embiste si te le pegas.
2. **«La División» (10 → 4)** — el cuerpo **se parte en dos**. El Rey se aparta del combate (invisible, invulnerable y sin atacar) y pelean dos `ReyMetad` de 3 corazones que se turnan.
3. **«El Frenesí» (4 → 0)** — abandona las curvas. Persecución en línea recta a ×2.6, abanico de veneno y cargas de 160 px.

El escenario es un **data center búnker enterrado bajo tierra**: el jugador entra por un corredor de servidores y cruza un portal de franjas de peligro hacia la sala del jefe, donde la cámara se bloquea y comienza la pelea.

### «La División»: el desdoblamiento en dos `ReyMetad`

La Fase 2 es la única del jefe que no se resuelve con ataques, sino con una
mecánica: el cuerpo **se parte en dos sub-jefes independientes** (`rey_metad.py`).

Al entrar en la fase, el Rey se vuelve **invisible e invulnerable** y salen dos
mitades de **3 corazones cada una** (los números del spec). Que el Rey no sea
golpeable no es solo fidelidad: si lo fuera, el jugador podría saltarse la fase
entera pegándole a él en vez de a las mitades.

**Coordinan por turnos.** El spec pide que «uno ataque mientras el otro se
reposiciona», y eso vive en `CoordinadorDeMitades`: un único reloj compartido
decide de quién es el turno. Está fuera de las mitades a propósito — si cada
una llevara su propio temporizador, un aturdimiento las desincronizaría y
acabarían atacando a la vez, que es justo lo que el spec prohíbe. Con un solo
reloj es imposible por construcción.

La mitad que no ataca **no huye**: se coloca en el flanco opuesto, de modo que
el jugador queda en medio y tiene que decidir a cuál dar la espalda.

**Fase «La Furia» (añadida, no está en el spec).** Cada mitad tiene una segunda
fase que se dispara por dos vías: bajar de 1.5 corazones, o quedarse sola. La
segunda cierra un agujero real del diseño: con una sola mitad viva el turno ya
no reparte nada entre nadie, así que respetarlo la dejaba pasiva media pelea y
matar una mitad hacía la fase *más fácil*. Enfurecida deja de ceder el turno,
acelera ×1.45 y acorta su enfriamiento de 2.6 s a 1.56 s.

Cuando caen las dos, el Rey se rearma y arranca «El Frenesí».

---

## 2. Computación Gráfica — dónde está cada cosa

Índice para no tener que buscar: cada tema de la rúbrica, dónde vive y qué lo
respalda. Todo está medido; los números de esta tabla salen de arneses que
corren la escena real, no de estimaciones.

| Tema | Dónde | Cómo se aplicó | Evidencia |
|---|---|---|---|
| **Curvas y modelado** | §5 · Unidad III | `CurveTools.catmull_rom` en Fase 1 y `CurveTools.bezier` en Fase 2, con los **mismos 4 puntos de control**. Catmull-Rom pasa por todos (andar a tirones de marioneta); Bézier esquiva los intermedios (serpenteo). El cambio de carácter sale de una sola llamada. | 30.5 px/s medidos, salto máximo 2.01 px/fotograma, 22 cambios de dirección en 10 s |
| **Representación de escenas** | §6 · Capas TMX | Seis capas con z-order justificado una a una. El parallax se **desactiva** en las tres de fondo: son la pared de una sala cerrada, y a 0.15/0.40/0.70 los racks se despegaban del suelo. La cámara se bloquea por zona al entrar a la arena. | La sala se ve entera; los ~11 px ocultos son pared, el suelo transitable acaba en x = 1104 |
| **Color** | §5 · Unidad V | Tinte de fase con `ColorTools.apply_tint`, que **multiplica** por `color/255` y por tanto solo puede oscurecer. La progresión sube los factores: verde sucio → verde vivo, conforme las serpientes toman el cuerpo. | Sobre el hueso `(232,226,205)`: `(100,177,72)` → `(127,203,96)` → `(159,226,116)` |
| **Transparencia** | §5 · Unidad V y VII | Las cuatro herramientas de imagen del framework **destruyen el alfa por píxel** (`make_surface` solo copia RGB). Se guarda `array_alpha` antes y se reinyecta con `pixels_alpha` después. Sin eso el jefe se dibuja como un rectángulo negro. | Comprobado: un píxel `(0,0,0,0)` sale `(0,0,0,255)` sin el envoltorio |
| **Texturas** | §6 · Tileset propio | Tileset pixel-art de **32 tiles de 16×16** hecho para este nivel, porque los del curso solo traen paneles lisos. Cuenta que el búnker está enterrado: tierra → grava → losa remachada → viga → sala → placa diamantada. La tierra elige entre 8 variantes con un hash espacial XOR determinista. | `((r·73856093) ⊕ (c·19349663)) mod 97` — sin patrones repetidos visibles |
| **Animación** | §6 · Animación y §5 · Unidad VI | Cuatro hojas propias de 40×56 (`walk` 4, `spit` 3, `hurt` 2, `death` 4). El escupitajo **no lleva reloj propio**: su fotograma sale de `telegraph_progress`, así que la última pose cae en el disparo. `LUNGE` acelera con `ease_in_quad` sobre la *distancia*. | `WINDUP` → poses `[0,1]`, `ACTIVE` → pose `[2]`; 24/24 transiciones entran por el fotograma 0 |

**Dos criterios que gobernaron todas estas decisiones**, y que explican las
desviaciones del spec documentadas más abajo:

1. **Si no se lee, no sirve.** El tinte literal del spec `(30,80,0)` dejaba al
   jefe casi negro sobre el fondo del búnker, y el desenfoque nunca se aplica
   durante un aviso de ataque. Un jefe que no se distingue no es una decisión
   estética, es un defecto de jugabilidad.
2. **Cada recurso tiene una función mecánica, no decorativa.** El histograma
   no adorna: dirige la puntería y la velocidad de persecución. El realce por
   convolución no adorna: es la segunda señal del aviso. Las hojas de sprite no
   adornan: la pose delata cuál de las dos mitades tiene el turno.

---

## 3. Patrones de ataque

Los **seis** ataques del spec §4.3. Los cuatro directos son métodos `_do_*`
registrados en el `AttackScheduler`; los dos de invocación son `SummonWave` del
`SummonTracker`, que es el sistema del framework para esbirros:

| Attack | Tipo | Daño | Fases | Rango | Cooldown | Descripción |
|---|---|---|---|---|---|---|
| `VENOM_SPIT` | proyectil | 0.5 | 1, 2 | ≤ 200 px | 2.5 s | Glob de veneno recto apuntado al jugador. |
| `BODY_SLAM` | cuerpo a cuerpo | 1.0 | 1, 2 | ≤ 64 px | 4.0 s | Se abalanza 80 px de golpe. Castiga pegarse al jefe. |
| `SERPENT_CARPET` | invocación | 0.25 c/u | 1, 2 | — | 15 s | Suelta serpientes `WalkerSerpientePequena`. |
| `VENOM_BURST` | proyectil ×5 | 0.25 c/u | 3 | — | 6.0 s | Abanico de 5 globos a −30°, −15°, 0°, +15°, +30°. |
| `SERPENT_WAVE` | invocación | 0.25 c/u | 3 | — | 10.5 s | Igual, pero con el ritmo del frenesí. |
| `LUNGE` | carga | 1.25 | 3 | — | 8.0 s | Carga 160 px a 350 px/s. Recorrido visible, esquivable. |

### Las invocaciones: desviación deliberada del spec

El spec pide **6 serpientes cada 10 s** en Fase 1 y **12** en Fase 3. Jugado en
una arena de 400 px eso es un muro: la pelea deja de ser contra el Rey y pasa a
ser contra la alfombra. La propia guía del curso lo anticipa —`66_GUIA §4.2`:
«carpet con demasiadas serpientes en fase 1 satura el rendimiento y al
jugador»— y `86_ESPEC §5` manda calibrar por playtest, no por el número escrito.

Tres cambios, los tres para que el jefe siga siendo el protagonista:

- **2 por oleada** en vez de 6/12.
- **Tope de 2 vivas a la vez**, contando oleadas anteriores.
- **No invoca hasta bajar de 12 corazones**: el primer tramo de la pelea sirve
  para aprender a leer al Rey, y meterle serpientes desde el primer segundo
  tapa justo eso.

Un efecto emergente que resultó mejor que el temporizador: como el tope bloquea
la siguiente oleada mientras vivan las anteriores, **el ritmo lo marca el
jugador** — si no las mata, no vienen más.

### Telegrafiado (aviso → golpe → castigo)

El ciclo lo lleva `AttackScheduler` (`boss_kit.py`), **no temporizadores
propios**. Cada ataque recorre `WINDUP → ACTIVE → RECOVER`; el golpe se ejecuta
en `on_attack_fired()`, que el framework invoca justo al entrar en `ACTIVE`:

| Attack | windup | active | recover |
|---|---|---|---|
| `VENOM_SPIT` | 0.50 s | 0.20 s | 0.60 s |
| `BODY_SLAM` | 0.45 s | 0.25 s | 0.80 s |
| `VENOM_BURST` | 0.80 s | 0.25 s | 0.90 s |
| `LUNGE` | 0.90 s | 0.45 s | 1.10 s |

Dos reglas de diseño detrás de esos números:

- **Ningún `windup` baja de `MIN_READABLE_WINDUP = 0.35 s`** (constante del
  framework). Por debajo el aviso no se alcanza a leer y el ataque se vuelve
  injusto.
- **A más daño, más aviso.** `LUNGE` pega 1.25 corazones y avisa 0.90 s;
  `VENOM_SPIT` pega 0.5 y avisa 0.50 s.

Además el Rey **se planta durante el aviso**: si siguiera recorriendo su curva
mientras telegrafía, el jugador no podría deducir desde dónde llega el golpe y
el aviso no serviría de nada.

---

## 4. Transiciones de fase

`health_threshold[i]` es la vida **máxima en la fase i**, no el punto de corte:
`BossBase` salta a la fase `i+1` cuando la vida baja de `threshold[i+1]`, y
entonces fija `_phase_max_health = threshold[i+1]`. Por eso el primer umbral
vale lo mismo que `max_health` (mismo patrón que el jefe de referencia).

| Fase | Umbral | Vida | Movimiento | Ataques | Velocidad |
|---|---|---|---|---|---|
| 1 «La Marioneta» | 15.0 | 15 → 10 | `catmull_rom` errático | VENOM_SPIT, BODY_SLAM | ×1.0 |
| 2 «La División» | 10.0 | 10 → 4 | — (pelean las mitades) | ninguno: el Rey se aparta | ×1.6 |
| 3 «El Frenesí» | 4.0 | 4 → 0 | persecución recta | VENOM_BURST, LUNGE | ×2.6 |

**La Fase 2 es la excepción: el Rey no actúa.** Sus ataques siguen declarados
para esa fase —y por eso aparecen como «1, 2» en §3— pero mientras esté partido
el encuentro queda suspendido. La causa fue un error propio que solo se vio
midiendo: **`is_visible = False` únicamente apaga el dibujo**. `BossBase.draw`
es el único sitio del motor que consulta esa bandera (`boss_base.py:640`), así
que el planificador seguía corriendo y el Rey borrado de la pantalla **atacaba
igual** —medido: 5 `VENOM_SPIT` y 4 `BODY_SLAM` en 20 s, más la hitbox de
contacto activa—. El jugador recibía golpes de algo que no podía ver, no podía
esquivar y no podía castigar, que es la negación exacta del telegrafiado que
sostiene el resto de la pelea. `_update_encounter` lo corta con el mismo gesto
que usa el motor para un jefe aturdido (`attacks.interrupt()` y salir) y
`_build_hitbox` devuelve un rect vacío mientras dure la división. Los
enfriamientos sí siguen descontando, para que al rearmarse entre al frenesí con
el ritmo en marcha y no con todo cargado.

La maquinaria de transición (invencibilidad, temporizador de 2.5 s,
`speed_multiplier`, evento `BOSS_PHASE_CHANGED`) la aporta `BossBase`. El Rey
solo detecta el flanco en `_detect_phase_change()` para cancelar lo que es
estado suyo —la carga a medio recorrer y el trazado de la curva de la fase que
muere— y emitir su sonido de división.

**Aviso del calificador:** `_check_phase_transition()` solo se invoca desde
`apply_hit()`. Asignar `current_health` a mano no dispara ninguna transición;
para probarlas hay que infligir daño por la vía real del framework.

---

## 5. Fórmulas Exactas por Unidad

### Unidad I — Coordenadas y Transformaciones

**Layout del mapa (70×38 tiles = 1120×608 px):**

```
corredor de entrada:  x = 0 … 720 px    (el jugador lo recorre antes de la pelea)
sala del jefe:        x = 720 … 1120 px (400 px de ancho)
piso (colisión):      y = 576
```

El alto de 608 px es el mínimo que exige `86_ESPEC §2.1` para una arena de jefe
(800 × 608). El ancho de 1120 está dentro del máximo de 1600.

**Arena del boss** — no es el mapa completo, es el rect del `CameraLock`:

```
arena_bounds = CameraLock.rect = Rect(720, 0, 400, 608)
```

**Por qué la zona empieza en 720 y no en la entrada visual de la sala.** El
motor **no encuadra** la zona del `CameraLock`: la congela donde esté la cámara
al entrar. Como la cámara va media pantalla por detrás del jugador, bloquearla
antes de que llegue a su tope dejaba parte de la sala invisible para siempre —
medido: 153 px ocultos. El punto correcto es aquel donde la cámara **ya tocó su
tope**:

```
tope de cámara = ancho_mapa − ancho_pantalla = 1120 − 800 = 320
el objetivo va media pantalla por delante  → zona desde 320 + 400 = 720
```

Con eso la cámara congela en offset ≈ 309 y muestra 309…1109. Quedan ~11 px sin
ver por el desfase asintótico del LERP, pero son **solo pared**: el suelo
transitable termina en x = 1104 y sí se ve entero.

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
mezclarlas hacía flotar al jefe (ver §8).

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
        = (720 ≤ px < 1120) and (0 ≤ py < 608)
camera.locked_x = camera.locked_y = in_room
```

Lo aplica el propio motor desde `Camera._aplicar_bloqueos`. Este escenario
llegó a llevar un parche que lo hacía a mano, porque `set_camera_locks`
guardaba el `rect` de cada zona y no lo leía nunca; el profesor corrigió el
motor (AUD-143) y **el parche se retiró**.

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

**BODY_SLAM — embestida corta (Fase 1–2):**

```
d = vec2_distance(boss_center, player_center)
si d ≤ BODY_SLAM_RANGE (64 px):
    dir       = vec2_normalize(player_center - boss_center)
    boss.x   += dir.x * BODY_SLAM_LUNGE = dir.x * 80
```

Solo se desplaza en **X**: el Rey camina por el suelo, así que la Y la sigue
gobernando `floor_y` y la embestida no lo despega del piso.

**VENOM_BURST — abanico de 5 globos (Fase 3):**

Un único vector unitario de puntería, rotado a los 5 ángulos del spec. La
rotación es la matriz de rotación 2D estándar, aplicada por `Vector2.rotate(θ)`
(no se reimplementa a mano):

```
aim = vec2_normalize(player_center - boss_center)

R(θ) = [ cos θ   −sin θ ]
       [ sin θ    cos θ ]

para θ ∈ {−30°, −15°, 0°, +15°, +30°}:
    vel_θ = R(θ) · aim * VENOM_SPIT_SPEED = R(θ) · aim * 90
    daño   = 0.25
```

Verificado midiendo los proyectiles reales: separaciones `[15.0, 15.0, 15.0,
15.0]` grados y cobertura `[−30 … +30]` respecto al globo central.

**LUNGE — carga de recorrido visible (Fase 3):**

A diferencia de `BODY_SLAM` (empujón instantáneo), la carga se reparte en el
tiempo, así que tiene trayectoria que el jugador puede leer y esquivar:

```
al armarla (on_attack_fired):
    dir_x     = signo( vec2_normalize(player_center - boss_center).x )
    restante  = LUNGE_DISTANCE = 160 px

cada frame, mientras restante > 0:
    paso      = min(LUNGE_SPEED * dt, restante) = min(350 * dt, restante)
    boss.x   += dir_x * paso
    restante -= paso
```

El `min(...)` es lo que impide pasarse de los 160 px en el último fotograma.

**Persecución de la Fase 3 (spec: 130 px/s):**

```
dir     = vec2_normalize(player_center - boss_center)
boss.x += dir.x * PURSUIT_SPEED * dt = dir.x * 130 * dt
boss.y  = floor_y                      (pegado al suelo, sin curva)
```

---

### Unidad III — Curvas (`CurveTools`)

Las dos primeras fases recorren una curva recalculada cada 0.3 s; **la Fase 3
abandona las curvas** y persigue en línea recta. El contraste entre ambos modos
es lo que hace que «El Frenesí» se lea como un cambio de intención y no solo de
velocidad.

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

La curva **pasa exactamente por cada punto de control**. Esto produce el
movimiento nervioso y entrecortado de una marioneta tirada por hilos.

**Fórmula Bézier — Fase 2 «La División»** (`CurveTools.bezier`, mismos 4 puntos
de control, grado n = 3). El trazado sigue siendo el de la fase, aunque durante
la división el Rey no se dibuje: lo recorre en el instante entre partirse y
rearmarse, y es lo que gobierna dónde reaparece.

```
B(t) = Σ  C(n,i) · (1−t)^(n−i) · t^i · P_i        para i = 0..n
     = (1−t)³·P_0 + 3(1−t)²·t·P_1 + 3(1−t)·t²·P_2 + t³·P_3
```

**La diferencia que importa:** una Bézier **no pasa** por sus puntos de control
intermedios (`P_1`, `P_2`) — solo por los extremos. Con los mismos 4 puntos, la
Catmull-Rom da un recorrido que toca cada punto (andar a tirones) y la Bézier da
uno que los esquiva suavemente (serpenteo). Es exactamente el contraste que
separa «La Marioneta» de «La División», y sale de cambiar una sola llamada.

Ambas funciones tienen firma idéntica en `CurveTools`, así que son
intercambiables:

```python
catmull_rom(control_points, n_samples) -> list[(x, y)]
bezier(control_points, n_samples)      -> list[(x, y)]
```

**Muestreo de la ruta** (PATH_SAMPLES = 20 puntos por segmento):

```
para t en linspace(0, 1, PATH_SAMPLES):
    (x, y) = CurveTools.sample_path(path_points, t)
```

El path se recalcula cada `PATH_RECALC_INTERVAL = 0.3 s`.

---

### Unidad V — Color y transparencia (`ColorTools`)

El cuerpo del Rey se tiñe de verde venenoso, y el tinte **cambia con la fase**:
es la señal visual de que las serpientes van tomando el control del cadáver.

**Fórmula.** `ColorTools.apply_tint` multiplica canal a canal:

```
resultado.R = origen.R · (tinte.R / 255)
resultado.G = origen.G · (tinte.G / 255)
resultado.B = origen.B · (tinte.B / 255)
```

Como es un producto por un factor ≤ 1, **solo puede oscurecer**: un canal en
255 deja el original intacto y uno en 0 lo elimina. Por eso la progresión no va
«de verde a más verde», sino de un verde apagado y sucio a uno cada vez más
vivo, subiendo los factores:

| Fase | Tinte | Factores (R, G, B) | Sobre el hueso (232, 226, 205) |
|---|---|---|---|
| 1 «La Marioneta» | `(110, 200, 90)` | 0.43 · 0.78 · 0.35 | `(100, 177, 72)` cadáver verdoso |
| 2 «La División» | `(140, 230, 120)` | 0.55 · 0.90 · 0.47 | `(127, 203, 96)` las serpientes asoman |
| 3 «El Frenesí» | `(175, 255, 145)` | 0.69 · **1.00** · 0.57 | `(159, 226, 116)` veneno puro |

En la Fase 3 el canal verde va a 255, o sea factor 1.0: el verde **no se
atenúa**. Es lo más cerca de «el cuerpo pulsa con veneno» que permite una
operación multiplicativa.

**Desviación deliberada del spec, y por qué.** El spec §4.3 pide literalmente
`ColorTools.apply_tint(boss_surface, (30, 80, 0))`, que son factores
0.12 / 0.31 / **0.00**. Ese valor asume un sprite claro: aplicado al hueso y la
carne del Rey da `(27, 71, 0)`, un verde casi negro. Jugándolo, el jefe se veía
como una mancha oscura sin silueta legible sobre el fondo del búnker. **Un jefe
que no se distingue del fondo no es una decisión estética, es un defecto de
jugabilidad**, así que se conservan la intención y la progresión —verde
venenoso que se enciende conforme las serpientes toman el cuerpo— con factores
que dejan ver de qué está hecho.

**El detalle que casi arruina el efecto.** `apply_tint` reconstruye la
superficie con `pygame.surfarray.make_surface`, que **solo copia RGB**. La
transparencia por píxel se pierde: comprobado, un píxel `(0, 0, 0, 0)` sale
como `(0, 0, 0, 255)`. Aplicado tal cual al sprite, el Rey se dibujaría como un
**rectángulo negro** con la figura dentro. La solución guarda el canal alfa
antes de teñir y lo reinyecta después, dejando el color exactamente como lo
calculó `ColorTools`:

```python
alfa   = pygame.surfarray.array_alpha(frame).copy()
tenido = ColorTools.apply_tint(frame, color).convert_alpha()
pygame.surfarray.pixels_alpha(tenido)[:] = alfa
```

**Coste.** El tinte de una fase no cambia y los fotogramas son fijos, así que
teñir en cada `draw()` repetiría la misma ida y vuelta a NumPy 60 veces por
segundo. Se calcula **una vez por (fotograma, fase)** y se cachea; la clave es
la superficie misma y no su `id()`, para que el recolector no pueda liberar el
fotograma y reasignar ese `id` a otro objeto dando un acierto falso.

**Dónde se engancha.** Se sobreescribe `BossBase._apply_filter`, que `draw()`
llama con el fotograma ya elegido y volteado. Se tiñe primero y se delega
después en la clase base, de modo que el tinte de la Unidad V es **constante**
y el `filter_effect` de la fase (Unidad VII) conserva su parpadeo de 1 de cada
5 fotogramas, que es como el framework lo diseñó.

---

### Unidad VI — Animación por easing e interacción con el `EventBus`

**La carga acelera.** `LUNGE` no va a velocidad constante: recorre los 160 px
del spec siguiendo `ease_in_quad` de `math_utils`.

```
recorrido(t) = LUNGE_DISTANCE · ease_in_quad(t) = 160 · t²
t avanza de 0 a 1 en LUNGE_DURATION = 160/350 ≈ 0.457 s
```

El easing se aplica a la **distancia**, no a la velocidad. Al revés la carga
quedaría clavada: `ease_in_quad(0) = 0`, así que la velocidad inicial sería
cero y nunca despegaría.

Medido en octavos de la carga:

| Octavo | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| px recorridos | 2.5 | 7.5 | 12.5 | 17.5 | 22.5 | 27.5 | 32.5 | 37.5 |

El último tramo es **15× más rápido** que el primero. No es adorno: el
arranque lento hace visible el compromiso del Rey —todavía se puede esquivar—
y el tramo final rápido castiga haberse quedado quieto. A velocidad constante
los dos tramos se ven igual y la carga se vuelve ilegible.

**Reacción a eventos.** El jefe define `set_event_bus`, que es el gancho por el
que la escena le entrega el bus (en `__init__` todavía no existe), y se
suscribe a `PLAYER_DAMAGED`. Al herir al jugador se detiene a «saborear» el
golpe y reanuda con una rampa `ease_out_quad`:

```
factor de movimiento: 0.31 → 0.56 → 0.75 → 0.89 → 0.97 → 1.00
```

Le da al jugador un respiro legible para reposicionarse en vez de encadenar
ataques sin aire. El factor escala el `dt` del movimiento, no la posición: así
la curva no se recalcula ni salta, solo se recorre más despacio.

> **Detalle del motor:** `EventBus.emit()` **solo encola**; la entrega ocurre
> en `dispatch()`, que llama el bucle principal una vez por fotograma. El bus
> guarda referencias débiles, pero usa `WeakMethod` para métodos ligados, así
> que suscribir `self._on_player_damaged` es seguro.

---

### Unidad VII — El histograma dirige la cacería

El Rey es un cadáver animado por serpientes, y las víboras no cazan con la
vista. Aquí eso deja de ser narrativa: **el brillo real del escenario gobierna
el combate**.

**Medición.** Cada 24 fotogramas (~0.4 s) se muestrea un cuadrado de 96×96 px
alrededor del jugador y se calcula el brillo con `FilterTools.compute_histogram`:

```
brillo = Σ i · luminancia[i] / (255 · total_píxeles)      para i = 0..255
oscuridad = 1 − brillo
```

Es la media ponderada de los 256 cubos del histograma de luminancia,
normalizada a 0..1. Verificado: pantalla negra → 0.000, gris → 0.498,
blanca → 1.000.

Se mide dentro de `draw()` y no de `update()` a propósito: ahí el fondo, el
terreno, las lámparas y la niebla **ya están dibujados**, así que se mide lo
que el jugador realmente ve. Y se mide *antes* de que el jefe se dibuje a sí
mismo — si no, su propio tinte verde contaminaría la lectura.

**Qué dirige.** Dos consecuencias mecánicas, ambas medidas:

| | A plena luz | Penumbra | A ciegas |
|---|---|---|---|
| Dispersión del escupitajo | **0.00°** | 5.11° | 10.82° |
| Avance en persecución (0.5 s) | **62.3 px** | — | 37.4 px (×0.6) |

```
error_angular = PUNTERIA_ERROR_MAX · oscuridad          (máx 18°)
velocidad     = PURSUIT_SPEED · lerp(0.6, 1.0, brillo)
```

Esconderse en la oscuridad no es un castigo: **compra distancia** (el Rey
avanza cauto y falla más) a cambio de que acierte cuando salgas a la luz. Las
lámparas del mapa pasan a ser una decisión táctica en vez de decoración.

### Unidad VII — Convolución y desenfoque

La misma lectura del histograma alimenta el aspecto del jefe, de modo que lo
que se ve y lo que ocurre digan lo mismo.

**Matriz del kernel** (`FilterTools.get_standard_kernel("sharpen")`), aplicada
durante el aviso de ataque:

```
        ⎡  0  −1   0 ⎤
    K = ⎢ −1   5  −1 ⎥        Σ K = 1
        ⎣  0  −1   0 ⎦
```

La suma de los coeficientes es 1, así que **no cambia el brillo medio**: solo
sube el contraste local. Resta a los cuatro vecinos y lo devuelve al centro, lo
que marca los bordes y deja intacto el interior de una zona uniforme
(5·v − 4·v = v). Por eso el efecto se lee en la silueta, que es justo lo que
hace falta para que un aviso destaque.

Medido sobre una fila que cruza el borde del sprite:

```
antes:   [0, 0, 200, 200, 200, 200, 0, 0]
después: [0, 0, 255, 200, 200, 255, 0, 0]      contraste 200 → 255
```

**Desenfoque** (`FilterTools.gaussian_blur`, σ = 1.2) cuando el brillo cae por
debajo de 0.35: el Rey se vuelve difícil de leer justo cuando también falla la
puntería. Medido en un píxel de borde: `200 → 88`.

**Orden de la pila, y por qué importa:**

```
1. tinte de fase          (Unidad V)   — siempre
2. realce por convolución (Unidad VII) — si está avisando
3. desenfoque gaussiano   (Unidad VII) — si caza a ciegas
4. filter_effect de fase  (framework)  — parpadeo 1 de cada 5 fotogramas
```

El aviso **gana** al desenfoque a propósito: si el Rey estuviera borroso
mientras telegrafía, el ataque no se podría leer y la pelea dejaría de ser
justa. Difuminar es una desventaja para el jugador, y no se acumula con la
única señal que le queda para defenderse.

> **Trampa de las herramientas de imagen.** Las cuatro que usa este jefe
> reconstruyen la superficie con `pygame.surfarray.make_surface`, que **solo
> copia RGB**: `apply_tint`, `gaussian_blur`, `apply_kernel` y `sobel_edge`
> **destruyen la transparencia por píxel**. Comprobado: un `(0,0,0,0)` sale
> `(0,0,0,255)`. Aplicadas tal cual, el Rey se dibujaría como un rectángulo
> negro con la figura dentro. Todas pasan por un envoltorio que guarda el alfa
> antes y lo reinyecta después. Se difumina el color pero **no** la silueta:
> difuminar el alfa sangraría fuera del rect donde el motor recorta.

**Coste.** Tinte y filtros se cachean por (fotograma, variante). La entrada es
un sprite fijo y el resultado no cambia, así que convolucionar en cada `draw()`
sería repetir el mismo cálculo 60 veces por segundo. El histograma se remuestrea
1 de cada 24 fotogramas por el mismo motivo.

---

### Unidad IX — Subtipos que se detectan, no se anuncian

En «El Frenesí» el Rey alterna entre tres modos cada 8–15 s y **nada lo
anuncia**: ni evento, ni sonido, ni indicador en el HUD. El jugador solo puede
deducir en cuál está observando cómo se comporta. Es el examen de
reconocimiento de patrones que pide el spec §4.3.

| Subtipo | Avance | Cadencia | `VENOM_BURST` | `LUNGE` | Cómo se lee |
|---|---|---|---|---|---|
| `AGGRESSIVE` | ×1.3 | ×0.6 | 3.6 s | 4.8 s | carga y acosa |
| `DISPERSED` | ×0.8 | ×1.0 | 6.0 s | 8.0 s | suelta serpientes |
| `DEFENSIVE` | ×0.5 | ×1.4 | 8.4 s | 11.2 s | aguanta a distancia |

Dos decisiones de diseño que sostienen la mecánica:

- **La duración es aleatoria dentro de la ventana**, no fija. Con un periodo
  constante el jugador aprendería a *contar segundos* en vez de leer al jefe, y
  eso no es reconocer un patrón: es mirar el reloj.
- **Nunca se repite el mismo subtipo dos veces seguidas.** Si se repitiera, el
  jugador no podría distinguir «cambió y sigue igual» de «leí mal», y la
  señal dejaría de ser fiable.

La cadencia reescala los `cooldown` del propio planificador en vez de llevar un
reloj paralelo — pero siempre **desde los valores del spec**, no sobre el valor
actual: multiplicar lo ya multiplicado los haría crecer sin tope en segundos.

### Invocaciones: cómo están cableadas

Los valores calibrados y el porqué de apartarse del spec están en §3. Aquí va
la mecánica:

| Patrón | Fases | Cantidad | Cadencia | Tope vivas |
|---|---|---|---|---|
| `SERPENT_CARPET` | 1, 2 | 2 | 15 s | 2 |
| `SERPENT_WAVE` | 3 | 2 | 10.5 s (×0.7) | 2 |

Las lleva `SummonTracker`, que `BossBase` ya conduce: mide enfriamientos, purga
a los muertos y respeta el tope. **El tope no es una optimización, es diseño**:
sin él un jefe que invoca cada N segundos llena la pantalla y el encuentro deja
de ser sobre el jefe.

Las oleadas **no se registran al construir el jefe**, sino cuando la vida baja
de `SERPIENTES_DESDE = 12`. Y se arman desde el `update()` propio, no desde
`_alert_behavior`: ese gancho solo corre en `ALERT`, así que un Rey en `PATROL`
nunca llegaría a armarlas.

Los `spawn_offsets` reparten las serpientes a lo ancho en vez de sacarlas todas
del mismo punto.

**Las serpientes nacen en el suelo, no donde diga el jefe.** `SummonTracker`
coloca cada esbirro en `boss.position + offset`, y `position` es la **cabeza**
del Rey (y = 526), no sus pies. Tal cual, las serpientes aparecían 58 px en el
aire y caían al entrar. Se corrigen en `take_summons()`, que es donde ya se
conoce `floor_surface_y` — verificado: desviación 0 px respecto al piso.

---

## 6. Representación Gráfica (lógica del diseño visual)

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

- **Sprite propio:** 40×56 px, dibujado en pixel art para esta entrega
  (`assets/maps/stage2_4/boss_rey_{walk,spit,hurt,death}.png`; 4 / 3 / 2 / 4
  fotogramas). Vive junto al mapa y no en `assets/sprites/bosses/`, que es
  carpeta común a todos los jefes; el jefe lo carga con el parámetro `base_dir`
  de `_load_boss_sprites`.

  **La primera versión se descartó y se volvió a dibujar.** Seguía el spec §4.1
  al pie de la letra —cadáver humanoide: cráneo hueco, costillar a la vista,
  extremidades colgando— y jugado se leía como un **esqueleto genérico**. En un
  juego de zombis eso es el enemigo básico, no un jefe, y sobre todo no decía
  «serpiente» por ninguna parte. El rehecho conserva la idea del spec —un cuerpo
  movido desde dentro— pero la cuenta con **anatomía de víbora**: cabeza
  triangular con foseta y ojo de pupila vertical, cuerpo con el patrón
  romboidal del terciopelo y cola que se enrosca. La lectura a 40×56 px pesa
  más que la fidelidad literal: si el jugador no distingue al jefe de un
  esbirro, el sprite está mal por muy fiel que sea.

  La paleta es **clara a propósito**: el tinte de fase multiplica, así que solo
  puede oscurecer. Un sprite oscuro tintado queda negro — que es exactamente lo
  que le pasaba al marcador de posición anterior.
- **Hitbox:** `Rect(5, 3, 30, 50)` — área de golpe del boss al jugador.
- **Hurtbox:** `Rect(6, 4, 28, 48)` — área donde el jugador puede herir al boss.
- **Proyectil:** círculo verde oscuro de radio 4 px dibujado con `pygame.draw.circle`.
- **Mapa:** 70×38 tiles (1120×608 px): corredor de entrada (0–720 px) + sala del jefe (720–1120 px). Piso en y=576. `CameraLock` sobre la sala (lock_x=true, lock_y=true), aplicado por zona por el propio motor.

### Animación (hojas de sprites y sincronización)

Cuatro hojas de 40×56, todas dibujadas para esta entrega:

| Hoja | Poses | FPS | Cuándo se dibuja |
|---|---|---|---|
| `walk` | 4 | 10 (14 en `ALERT`) | por defecto: patrulla, persecución, `BODY_SLAM`, `LUNGE` |
| `spit` | 3 | — (ver abajo) | `VENOM_SPIT` y `VENOM_BURST`, en `WINDUP` y `ACTIVE` |
| `hurt` | 2 | 12 | estado `HURT`; lo mapea `BossBase` |
| `death` | 4 | 8 | estado `DYING`; lo mapea `BossBase` |

`BODY_SLAM` y `LUNGE` se quedan con `walk` **a propósito**: son embestidas con
el cuerpo, y lanzarse hacia el jugador es exactamente lo que la pose de caminar
representa. Meterles la pose de escupir sería usar una animación por tenerla,
no por lo que hace.

**El escupitajo no lleva reloj propio.** Las demás hojas avanzan a fps fijos;
`spit` deriva su fotograma del aviso del ataque:

```
si tramo == WINDUP:  fotograma = min( int(telegraph_progress · (n−1)), n−2 )
si no:               fotograma = n−1
```

Con las tres poses de la hoja: **0 y 1 son el Rey tomando aire** y **2 es el
veneno saliendo**, y la 2 coincide con el instante en que el ataque entra en
`ACTIVE` y aparece el proyectil. A fps fijos la animación y el ataque serían
dos relojes independientes y la pose del disparo saldría distinta cada vez;
así el aviso se lee en la postura, no solo en el filtro de realce. Medido en
50 s de combate: durante `WINDUP` se ven las poses `[0, 1]` y durante `ACTIVE`
siempre la `[2]`.

**La muerte no se repite.** El motor avanza con `(frame + 1) % len(frames)`,
que es lo correcto para un ciclo de caminar y no para morirse. Se congela en
la última pose.

Las mismas cuatro hojas las usan los dos `ReyMetad`, y ahí la pose hace un
trabajo extra: con dos mitades en pantalla y solo una con el turno, **la
postura es lo que delata cuál va a atacar**.

### Propiedades de mapa

```
author  = José Pablo Ramírez Sánchez
climate = fog
```

**Por qué `fog`.** El validador acepta 7 climas, pero `CLIMATE_PARAMS`
(`weather_system.py`) solo implementa 5: `wind` y `sandstorm` pasan la
validación y caen al *fallback* de `clear`, sin efecto visual. De los 5 reales,
`fog` es el único coherente con un interior enterrado:

| Clima | Partículas | Efecto | Encaje |
|---|---|---|---|
| `clear` | 0 | ninguno | desaprovecha la propiedad |
| `rain` / `snow` / `storm` | 40–100 | partículas **cayendo** | absurdo bajo techo |
| **`fog`** | **0** | velo gris, alpha 80 | vapor de refrigeración |

Es el único con **cero partículas cayendo**, que es lo decisivo en un interior.
Y su color de velo, `(180, 180, 190)`, coincide exactamente con el `_ARENA_BG`
de la escena, así que la niebla se integra con el fondo en vez de ensuciarlo.

### Transitabilidad (auditoría de saltos)

El presupuesto de salto sale de `settings.py`, no de estimación:

```
GRAVITY = 800    PLAYER_JUMP_FORCE = −380    PLAYER_WALK_SPEED = 90

tiempo de vuelo = 2·380 / 800            = 0.950 s
altura máxima   = 380² / (2·800)         = 90.2 px
alcance real    = (90/2) · 0.950         = 42.8 px
```

El alcance útil es **42.8 px, no 85.5**, porque el controlador aplica **media
velocidad en el aire**. Diseñar contra los 85.5 px teóricos produce huecos
imposibles de saltar.

Geometría auditada (barrido píxel a píxel de x = 69 a x = 864, spawn → jefe).
Las coordenadas son las del TMX, sin transformar:

| Elemento | Coordenadas | Estado |
|---|---|---|
| `Floor` | x = 0 … 1120, y = 576 … 592 | continuo, **sin huecos** |
| `Ceiling` | x = 0 … 1120, y = 272 … 288 | 288 px libres |
| `LeftWall` | x = 0 … 16, y = 272 … 592 | límite exterior |
| `RightWall` | x = 1104 … 1120, y = 272 … 592 | límite exterior |
| `PlayerSpawn_01` | (69.25, 565) | con suelo debajo |
| `BossRey_01` | (864, 567.75) | con suelo debajo, dentro de la arena |

**0 plataformas one-way · 0 death pits · 0 repechos internos.** El nivel no
exige ni un solo salto: el trayecto del spawn a la arena es suelo continuo, así
que el límite de 42.8 px nunca llega a ponerse a prueba.

---

## 7. Testing — problemas encontrados y correcciones

Ciclo seguido: **VERSIÓN → PRUEBA → PROBLEMA → CORRECCIÓN → NUEVA PRUEBA**.
Las correcciones se validan con arneses *headless* (`SDL_VIDEODRIVER=dummy`)
que corren la escena real y comprueban números, no impresiones.

### Ronda de animación

Los tres salieron de una misma revisión: las hojas estaban dibujadas y
cargadas, pero solo una llegaba a pantalla.

| # | Problema | Causa | Corrección | Nueva prueba |
|---|---|---|---|---|
| 1 | La hoja `spit` **no se dibujaba nunca**. El Rey escupía veneno con la pose de patrullar, así que el aviso dependía por completo del filtro de realce. | `_get_animation_key` devolvía `"walk"` incondicionalmente, en `BossRey` y en `ReyMetad`. `hurt` y `death` sí funcionaban porque los mapea `BossBase._get_animation_state` antes de llamar al método. | Devuelve `"spit"` cuando `VENOM_SPIT` o `VENOM_BURST` están en `WINDUP` o `ACTIVE`. | 50 s de combate: `walk` 2428 fotogramas, **`spit` 572** (antes 0), recorriendo sus 3 poses. |
| 2 | Al cambiar de hoja la animación **empezaba por el final**. | `_animation_frame` es un contador único compartido por todas las hojas y el motor no lo reinicia al cambiar de clave: pasar de `walk` (4 poses) a `spit` (3) entraba a media animación. No reventaba porque `draw` recorta con `min(...)`, así que solo se veía mal. | `_advance_animation` pone el contador y el temporizador a cero cuando la clave cambia. | **24 de 24** transiciones medidas entran por el fotograma 0. |
| 3 | La muerte **se repetía en bucle**: el Rey se deshacía en serpientes y se recomponía. | El motor avanza con `(frame + 1) % len(frames)` — correcto para caminar, absurdo para morir. | Se congela en la última pose. Además `_ANIM_FPS` declara `death: 8.0`: el motor no conoce esa clave (la suya es `die`) y caía al valor por defecto de 10, demasiado rápido para leer las cuatro poses. | 3 s de agonía: `[0,0,0,1,1,…,3,3,3,3]` — llega al final y se queda. |

**Resultado:** las cuatro hojas se ven, las transiciones arrancan limpias y el
veneno sale sincronizado con el aviso. `grade_boss` sigue en 100/100 en los dos
archivos.

### Otras rondas

| Problema | Corrección | Nueva prueba |
|---|---|---|
| El jefe **se teletransportaba** (~900 px/s) en vez de patrullar. | La curva se recorría **entera** cada 0.3 s (`t = timer / 0.3`), diera lo que diera de largo. Ahora se avanza por **distancia**. | 30.5 px/s, salto máximo 2.01 px/fotograma, y sigue girando 22 veces en 10 s. |
| Las serpientes invocadas **nacían 58 px en el aire**. | `SummonTracker` las coloca en `boss.position + offset`, y `position` es la **cabeza** del Rey, no sus pies. Se corrigen en `take_summons`, donde sí se conoce `floor_surface_y`. | Desviación **0 px** respecto al piso. |
| El jefe **se salía del mapa** al golpearlo siempre desde el mismo lado. | `_post_update` no corre en `HURT` (medido: 0 de 12 fotogramas). El acotado se movió a un `update()` propio, que sí corre siempre. | 80 golpes desde ambos lados: se mantiene entre x = 879 y 958. |
| **153 px de la sala** quedaban invisibles para siempre. | El `CameraLock` congela la cámara donde esté, no la encuadra. Se movió la zona al punto donde la cámara ya topó (x = 720). | Congela en offset 309; lo que queda sin ver son ~11 px de **pared**, y el suelo transitable se ve entero. |
| Un jefe **invisible seguía atacando** durante «La División». | `is_visible = False` solo apaga el dibujo. Se suspende el encuentro con el mismo gesto que usa el motor para un jefe aturdido. | 0 ataques en 30 s de Fase 2 y hitbox vacía; al rearmarse vuelve a atacar con normalidad. |
| El jefe se veía como **una mancha oscura**. | Dos causas: el tinte literal del spec `(30,80,0)` lo dejaba casi negro, y la v1 del sprite leía como esqueleto genérico. Tinte subido con la desviación justificada, y sprite rehecho con anatomía de víbora. | Sobre el hueso: `(27,71,0)` → `(100,177,72)`. |

### Comprobaciones que no encontraron nada (y por qué se listan)

«Las serpientes atraviesan paredes» y «las mitades se salen de la sala» eran
**dos sospechas mías**, no síntomas observados. Se midieron las dos y **ninguna
resultó cierta**. Van aquí porque una prueba que descarta una hipótesis es
trabajo hecho, no trabajo perdido: sin ella habría «arreglado» algo que
funcionaba.

| Sospecha | Medición | Resultado |
|---|---|---|
| Las mitades no reciben `arena_bounds` — la escena no se lo pasa a los invocados, y `clamp_to_arena` **sale sin hacer nada** si vale `None`. | Cableado replicado tal como lo hace `stage_scene.py`. | **Falsa.** Ambas tienen `Rect(720, 0, 400, 608)`: se lo pasa el propio Rey en `take_summons`. En 60 s se mueven en x = 740…883 y 886…1021, dentro de la sala. |
| Las serpientes no reciben rects de colisión. | Lo mismo. | **Falsa, y el error era de medición:** el `0` se había leído antes del cableado. Con la escena replicada llegan **4 rects**. |
| ¿Puedo atravesar zonas incorrectamente? (lista de playtesting) | Serpiente empujada 20 s contra cada muro, con el cebo al otro lado. | **Verdadera, pero latente** — ver §8: `EnemyWalker` usa esos rects solo como suelo. No se dispara en juego normal: con el jugador huyendo al corredor las serpientes se quedan en x = 832…1000. |

**Lección transversal:** la geometría hay que verificarla numéricamente. Un
desfase de 1 px es invisible en pantalla y delata un error de modelo. Y va en
las dos direcciones: **varias veces el arnés falló con el código correcto** —
la última, al dar por hecho que la pose del disparo debía leerse en el instante
de `on_attack_fired`, cuando ahí la animación todavía no ha avanzado ese
fotograma. Una prueba que falla no siempre acusa al código.

---

## 8. Reflexión

§7 recoge **qué** se rompió y cómo se arregló. Aquí va **qué enseñó**.

Los problemas más difíciles fueron casi todos de **sistemas de coordenadas**, y
se veían «bien» en pantalla hasta que se revisaron los números:

1. **`_floor_y` no descontaba el grosor del tile.** La fórmula original dejaba al
   boss con los pies 16 px *dentro* del piso. La primera corrección fue
   `arena_bounds.bottom - 16 - rect.height`; más tarde se sustituyó por el rect
   de colisión `Floor` (ver punto 4), que es el suelo de verdad.

2. **`arena_bounds` es el mapa completo, no la sala.** El framework asigna
   `Rect(0, 0, map_w, map_h)` a todos los jefes. Mientras el mapa *era* la sala
   eso funcionaba por coincidencia; al agregar el corredor de entrada, el Rey
   podía caminar fuera de su arena hacia el pasillo. La corrección aplica el
   rect del `CameraLock` como `arena_bounds`, usando **una sola fuente de
   verdad** para la geometría de la sala en vez de duplicar coordenadas.

3. **`CameraLock` congela; no encuadra — y el parche que lo suplia se retiró.**
   Aquí hubo dos problemas encadenados. El primero era del motor:
   `set_camera_locks()` hacía `any(line.lock_x for line in locks)` y no leía el
   campo `rect`, así que un solo `CameraLock` congelaba la cámara en todo el
   nivel desde el primer fotograma; este escenario lo parcheaba recalculando el
   bloqueo desde `update()`. El profesor lo corrigió en el motor (AUD-143) y
   **el parche se eliminó**: cuando un escenario tiene que corregir al motor, el
   defecto es del motor.

   El segundo era mío, y solo se vio jugando: la zona congela la cámara **donde
   esté**, no la centra en el rect. Puesta en la entrada visual de la sala,
   congelaba antes de que la cámara llegara a su tope y **153 px de la sala
   quedaban invisibles para siempre**. La corrección no fue tocar código sino
   mover la zona a x = 720, el punto donde la cámara ya topó (§5, Unidad I).
   Vale la pena separarlos: el mismo síntoma —«la cámara hace algo raro»— tenía
   una causa en el motor y otra en el mapa.

4. **Acoplar dos sistemas de coordenadas distintos se paga caro.** Tras
   resolver (2), el suelo del jefe seguía saliendo de `arena_bounds` — que ya
   era el rect del `CameraLock`. Al reajustar el mapa en Tiled, el borde
   inferior del `CameraLock` cayó en `592.0`; `pygame.Rect` **trunca a entero**
   (591) y el jefe quedó caminando 1 px flotando, con el jitter amplificándolo
   hasta ~9 px. La corrección fue **desacoplar**: `floor_surface_y` se lee del
   rect de colisión `Floor` y `arena_bounds` solo limita el eje X. Ahora los
   pies caen en y=576 con desviación 0 px, y mover el `CameraLock` en Tiled ya
   no afecta la altura del jefe.

5. **Tener dos relojes para lo mismo es peor que no tener ninguno.** La primera
   versión de los ataques llevaba sus propios contadores de enfriamiento. Al
   añadir el telegrafiado había ya un `AttackScheduler` gestionando exactamente
   eso, así que dos sistemas decidían cuándo podía atacar el jefe y cuál ganaba
   dependía del orden de llamadas. Se eliminaron los contadores propios: el
   planificador es ahora el único dueño de los tiempos, y a cambio regala el
   aviso legible (`telegraph_progress`) y la ventana de castigo
   (`is_vulnerable`).

Lo que las cinco tienen en común: **cada una nace de creerle a una
abstracción lo que su nombre promete** y no lo que hace. `arena_bounds` suena a
«el sitio donde pelea» y era el mapa entero; `CameraLock` suena a «encuadra la
sala» y solo congela; `is_visible` suena a «está o no está» y solo apaga el
dibujo; `_post_update` suena a «después de actualizar» y no corre en `HURT`.
Ninguna está mal documentada: simplemente había que ir a leerlas.

De ahí sale el método que acabé usando, y que es lo que me llevo de la entrega:
**medir antes de afirmar**. Los arneses corren la escena real, derivan sus
expectativas del propio TMX en vez de codificar números —así siguen valiendo al
editar el mapa en Tiled— y comprueban cosas concretas: los pies contra el piso
real, el bloqueo de cámara en los píxeles frontera, las transiciones de fase
infligiendo daño de verdad, los ángulos del abanico y la pose que acompaña a
cada disparo.

Y el reverso, que costó aprender: **una prueba que falla no siempre acusa al
código**. Varias veces el arnés dio falso negativo con el código correcto
—ordenar el abanico por ángulo absoluto se rompe cuando `atan2` cruza ±180°;
leer la posición antes del primer `update()` devuelve la coordenada cruda del
TMX; muestrear la pose en el instante de `on_attack_fired` la lee un fotograma
antes de que la animación avance—. Cuando la medición contradice al código, lo
primero es dudar de la medición.

### Hallazgos del framework (fuera de mi alcance)

Defectos del motor que este jefe destapó. **No se han tocado**: están fuera de
`src/stages/boss_rey/`, así que se documentan y se rodean desde mi código.

**Abiertos:**

- **El retroceso de `HURT` no tiene gravedad: los enemigos golpeados flotan.**
  En `EnemyBase._run_state_machine` solo el estado `LAUNCHED` recibe gravedad y
  re-anclaje al suelo (`enemy_base.py:860-862`). `HURT` aplica una
  `_knockback_velocity.y` negativa, la amortigua a cero y deja al enemigo en el
  aire. Medido sobre suelo y = 576: un golpe de 0.5 lo sube 4 px, uno de 1.0 lo
  sube 12 px, y uno de 2.0 —que sí pasa por `LAUNCHED`— lo deja en 0 px. En un
  jefe **se acumula**: 12 golpes seguidos lo dejan 29 px por encima del suelo.
  Afecta a todo el juego, no solo a este jefe. Rodeado con `_asentar_rey` y
  `_asentar_serpientes`, que reimponen el suelo cada fotograma.
- **`EnemyWalker` no choca con las paredes: los rects de colisión solo le
  sirven de suelo.** La lista que cablea la escena se consulta a través de
  `_all_ground_rects` —y el nombre dice exactamente lo que hace—: gravedad y
  detección de bordes. **Nada frena el avance horizontal.** Un caminante
  empujado contra un muro lo atraviesa y sale del mapa.

  Medido con una serpiente invocada, sus 4 rects ya cableados y el cebo al otro
  lado del muro: **302 px dentro de la pared derecha**, acabando en x = 1348,
  a 228 px fuera de un mapa de 1120. El control sin rects penetró 107 px, así
  que la prueba distingue de verdad entre los dos casos — lo cual confirma que
  cablearlos **sí cambia algo**, pero solo en el eje vertical.

  **En juego normal no se dispara**, y conviene decirlo con la misma claridad:
  con el jugador huyendo hasta el spawn del corredor —una posición legal— tras
  60 s las serpientes seguían en x = 832…1000, dentro de la sala; su radio de
  persecución las mantiene cerca del jefe. Para reproducirlo hay que poner el
  cebo fuera del mapa, donde un jugador no puede estar. Es un defecto
  **latente**: no afecta a esta arena, que es un pasillo cerrado, pero sí a
  cualquier nivel con muros o pilares interiores que los enemigos no deberían
  cruzar. Por eso se reporta en vez de rodearse.
- **Las herramientas de imagen destruyen la transparencia por píxel** —
  detallado en §5, Unidad VII. Es el más grave de los tres para un estudiante:
  el spec §4.3 manda usar `apply_tint` sin advertirlo, así que seguirlo al pie
  de la letra pinta al jefe como un rectángulo negro.

**Retirado tras volver a medirlo:** llegó a figurar aquí que «los enemigos
invocados no reciben los rects de colisión». Era **falso**, y el error estaba
en la medición: leí `len(_collision_rects) == 0` en una `SummonWave` recién
salida de `SummonTracker`, **antes** de que la escena la cablee.
`stage_scene.py:1037-1041` sí llama a `set_collision_rects`, y replicando ese
cableado se leen los **4 rects** del TMX. Queda escrito porque el fallo de
método —medir una entidad a medio construir y culpar al motor— es más útil de
recordar que el dato.

**Resueltos por el profesor** (confirmado tras actualizar el repositorio):
`validate_tmx` rechazaba `type='BossRey'`; el HUD rotulaba la fase con el
**total** en vez de con la actual (AUD-512); un solo `CameraLock` congelaba el
nivel entero (AUD-143); y el registro del tipo dentro de `on_enter` no llegaba
a las herramientas (AUD-151). Los dos últimos permitieron **retirar parches**
de este escenario — ver punto 3.

---

*Evaluación Práctica I (corregida) y avance de Práctica II — Computación Gráfica
y Procesamiento de Imágenes · José Pablo Ramírez Sánchez*

# Boss Battle Design — Student Worksheet

**Student Name:** Alejandro Josué Rodríguez Zamora
**Boss Name:** El Gran Shaman Paburu — Stage 4-2 (Jefe Final)

**Curso:** Computación Gráfica y PDI I — Universidad Invenio
**Entrega:** Evaluación Práctica I — Prototipo Funcional (15%)
**Correr con:** `python main.py --boss boss_paburu` (o doble clic en `jugar_paburu.bat`)

**Teclas 1-4 — cambio de forma (debug).** EP1 implementa la Forma 1; las
otras tres están cargadas con su hoja de sprites y su iluminación, pero en
partida normal el boss no baja de fase todavía, así que no habría manera de
verlas. Las teclas 1, 2, 3 y 4 saltan a cada forma para poder mostrarlas.

**Entrada del jefe (6 s, ESC para saltarla).** Al entrar a la sala corre una
secuencia en cuatro tiempos: la arena baja a penumbra, los cuatro cuencos de
fuego se encienden uno a uno subiendo la luz, la cabeza de piedra abre los
ojos y nace su aura, y entra la placa con el nombre. Está construida sobre el
`CutsceneSystem` del framework (`intro.py`), heredando acciones propias de
`CutsceneAction` — el mismo patrón que usa `stages/stage0`. Se ve una sola
vez: al morir y reaparecer no se repite.

---

## 1. Boss Concept

El Gran Shaman Paburu es una figura espiritual Tilawa de poder inmenso, corrompida
por un duelo antiguo. No pelea para destruir: pelea para **examinar**. La Pepita y
La Perla que cargan John y Jill son las llaves de su ritual, y necesita ver si son
dignos. Sus cuatro formas no son entidades distintas, sino capas de su poder: cada
una revela más de quién es en realidad.

En la Forma 1, **"La Cabeza de Piedra"**, aparece como una cabeza colosal de piedra
verde precolombina, semienterrada en el centro del cementerio, con los ojos
cerrados. Juzga sin mirar — sus ataques son ciegos y mecánicos, exactamente como
juzgó siglos atrás a Kavë, la portadora a la que condenó por error y por cuya
muerte se selló a sí mismo. Los siglos de espera no fueron vigilancia: fueron
penitencia. Cuando John y Jill llegan, Paburu no está furioso, está aterrado de
volver a equivocarse.

---

## 2. Attack Patterns

Los tres patrones de la Forma 1, implementados y medidos:

| Attack Name  | Type           | Damage    | Cooldown | Description                                                                                                                                            |
| ------------ | -------------- | --------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `STONE_SPIT` | projectile     | 0.5 c/u   | 4.0 s    | Escupe 3 piedras en abanico, separadas 15°. Trayectoria parabólica resuelta para caer sobre el jugador; apunta a dónde está, nunca a dónde estará.        |
| `EYE_BEAM`   | rayo (hitscan) | 1.0       | 8.0 s    | Rayo horizontal de 8 px que avanza a 200 px/s desde los ojos. Telegraph de 0.5 s con los ojos encendidos. Se esquiva agachándose o subiendo a plataforma. |
| `EL SELLO`   | zona / control | 0.5       | 10.0 s   | Emergen 5 columnas de piedra en los vértices de un pentágono. Telegraph de 0.8 s con grietas luminosas. Al retraerse dejan marcas grabadas permanentes.   |
| `ánimas`     | decorativo     | —         | —        | Al grabarse cada marca, sube de ella la luz de un nombre siguiendo una spline Catmull-Rom hacia el centro del sello. No hace daño: es la arena recordando. |

**Cadencia adaptativa:** los cooldowns se acortan a medida que cae la vida de la
forma — ×0.85 por debajo del 60 %, ×0.70 por debajo del 30 % (`_pattern_cooldown`).
La piedra no aprende ni cambia de patrón: solo insiste más.

---

## 3. Phase Transitions

Vida total: 20 corazones, 5 por forma. El umbral de cada `BossPhase` es la vida
**máxima de esa forma**, no un porcentaje del total.

| Phase                        | HP        | New Behaviour                                                                                                              |
| ---------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------- |
| 1 — La Cabeza de Piedra      | 20 → 15 ♥ | Estática. `STONE_SPIT`, `EYE_BEAM`, `EL SELLO`. **Implementada.** Juzga sin mirar.                                          |
| 2 — La Máscara Espectral     | 15 → 10 ♥ | Deriva senoidal. Solo la máscara recibe daño. `SPIRIT_WAVE`, `EL DUELO DE LOS ECOS`, `MASK_PULSE`. *Arte hecho; mecánicas EP2.* |
| 3 — La Reliquia (3A / 3B)    | 10 → 5 ♥  | Esfera. Se elige Pepita o Perla **al azar al entrar a la forma**. Persecución u órbita. *Arte hecho; mecánicas EP3.*         |
| 4 — El Espíritu del Shaman   | 5 → 0 ♥   | Flotación. Visión Espectral, `EL OFRECIMIENTO`. *Arte hecho; mecánicas EP3.*                                                |

> **Alcance real de esta entrega, sin adornos.** Las cuatro formas tienen
> arte de idle y las transiciones entre ellas funcionan, así que la pelea
> se ve completa de principio a fin. Pero **solo la Forma 1 tiene
> comportamiento**: las Formas 2, 3 y 4 no atacan ni se mueven — reciben
> daño y transicionan, nada más. Sus mecánicas llegan en EP2 y EP3 según
> el roadmap del GDD §7. El arte se adelantó porque tener tres formas como
> rectángulos grises entre dos terminadas se veía peor que tenerlas todas
> resueltas visualmente, no porque estén jugables.

La transición 1→2 dura 2.5 s de invulnerabilidad, durante los cuales se reproduce
la hoja `stone_crack`: la piedra se agrieta y sale la luz. El último frame cae
exactamente cuando termina la transición, porque la animación va atada a
`transition_timer` y no a un reloj propio.

---

## 4. Fórmulas matemáticas exactas

### 4.1 Sistemas de coordenadas

Todo el mundo del juego usa coordenadas de pantalla: **origen arriba-izquierda,
+X a la derecha, +Y hacia abajo**. Por eso la gravedad es positiva y las
velocidades de subida son negativas. La arena mide 800 × 608 px con la cámara
fijada por `CameraLock`, y el suelo está en `y = 560`.

Los rects de las entidades se expresan en espacio de mundo; los hurtbox/hitbox se
declaran en **espacio local** (offset desde `self.position`) y `EnemyBase._update_rects`
los traslada a mundo cada frame.

### 4.2 Vectores — `STONE_SPIT` (Unidad II)

Archivo: `form1_attacks.py` → `spit_flight_time`, `spit_velocities`, `StoneProjectile.update`

**(a) Tiempo de vuelo, proporcional a la distancia.** Con `vec2_distance`, que es
la norma euclídea ‖·‖₂:

```
d = ‖target − origin‖₂ = √( (Δx)² + (Δy)² )

t = clamp( d / 320 ,  0.80 ,  1.25 )      [segundos]
```

**(b) Resolución del tiro parabólico.** Se despeja la velocidad inicial que hace
que la piedra central caiga sobre el objetivo en exactamente `t` segundos.
Partiendo de la ecuación de movimiento con aceleración constante:

```
Δp = v₀·t + ½·g·t²

        Δx                    Δy
v₀ₓ = ────            v₀ᵧ = ──── − ½·g·t
         t                     t

con  g = 420 px/s²
```

**(c) Abanico de 15°.** Las otras dos piedras salen de **rotar** ese vector, no de
recalcular dos tiros. Rotación 2D canónica:

```
⎡x'⎤   ⎡cos θ   −sen θ⎤ ⎡x⎤
⎣y'⎦ = ⎣sen θ    cos θ⎦ ⎣y⎦        θ = −15°, 0°, +15°
```

Rotar preserva el módulo ‖v₀‖₂ en las tres piedras: el abanico se abre sin
desbalancearse.

**(d) Integración del proyectil.** Euler semi-implícito (velocidad primero), que
con Δt variable conserva mejor la forma de la parábola que el explícito:

```
v ← v + g·Δt
p ← p + v·Δt
```

### 4.3 Vectores — geometría de `EL SELLO` (Unidad II)

Archivo: `form1_attacks.py` → `seal_vertices`

Conversión **polar → cartesiana con escalado anisótropo**. El escalado distinto en
X e Y es el escorzo del círculo ceremonial visto desde la cámara lateral: se lee
como un círculo apoyado en el suelo, no como un aro flotando.

```
p(θₖ) = C + ( Rx·cos θₖ ,  Ry·sen θₖ )

θₖ = −90° + k·(360°/5) + φ        k = 0,1,2,3,4

C  = (400, 532)      centro del sello
Rx = 104             semieje horizontal
Ry =  28             semieje vertical (escorzo)
φ  = 30°·n           rotación de la n-ésima invocación
```

Es la composición de tres transformaciones elementales: generación en polares,
escalado no uniforme (Rx ≠ Ry) y traslación a C. Cada invocación gira la figura
30°, así las columnas nunca emergen dos veces en las mismas X.

### 4.4 Vectores — las ánimas (Unidad II)

Archivo: `form1_attacks.py` → `SealAnima`

```
dirección de avance:    v̂ = v / ‖v‖₂        (vec2_normalize, ‖v‖₂ ≠ 0)
desvanecimiento:        α = min(1, ‖p − C‖₂ / 46)   (vec2_distance)
```

El ánima se apaga a medida que se acerca al centro del sello.

### 4.5 Curvas — trayectoria de las ánimas (Unidad III)

Archivo: `form1_attacks.py` → `SealAnima.__init__`, `SealAnima.update`
API: `CurveTools.catmull_rom` + `CurveTools.sample_path`

**Spline de Catmull-Rom**, forma polinómica evaluada por el framework:

```
P(t) = ½·[ 2·P₁
         + (−P₀ + P₂)·t
         + (2·P₀ − 5·P₁ + 4·P₂ − P₃)·t²
         + (−P₀ + 3·P₁ − 3·P₂ + P₃)·t³ ]        t ∈ [0,1]
```

o en forma matricial:

```
                              ⎡  0   2   0   0 ⎤ ⎡P₀⎤
P(t) = ½·[1  t  t²  t³] ·     ⎢ −1   0   1   0 ⎥ ⎢P₁⎥
                              ⎢  2  −5   4  −1 ⎥ ⎢P₂⎥
                              ⎣ −1   3  −3   1 ⎦ ⎣P₃⎦
```

**Puntos de control de la i-ésima ánima** (de n = 5 por invocación):

```
s  = ( i − (n−1)/2 ) · 13          desvío lateral, reparte las 5 ánimas

P₀ = M                             la marca grabada (base de la columna)
P₁ = ( Mₓ + s        ,  Mᵧ − 34 )  sube y se abre
P₂ = ( (Mₓ+Cₓ)/2 + s/2 , Mᵧ − 48 ) punto alto camino al centro
P₃ = C = (400, 532)                el centro del sello, donde está Kavë
```

**Por qué Catmull-Rom y no Bézier:** la spline **pasa por** sus puntos de control,
no solo los aproxima. Así el ánima arranca exactamente en su marca y termina
exactamente en el centro, que es justo lo que la narrativa necesita. Una Bézier
cúbica trataría P₁ y P₂ como puntos de atracción y la curva no tocaría ni la marca
ni el centro.

**Muestreo:** la curva se evalúa **una sola vez al nacer** en 24 puntos con
`CurveTools.catmull_rom`, y después se recorre con `CurveTools.sample_path`
usando `t = elapsed / 1.6 s`. Evaluar la spline una vez y luego interpolar dentro
de la polilínea es más barato que evaluarla cada frame.

**Verificación de que la trayectoria es realmente curva** (medida corriendo):

```
puntos muestreados       : 24
longitud de la cuerda    : 28.0 px
longitud del arco        : 146.6 px      ratio 5.24   (1.00 sería una recta)
desviación máx. de la cuerda : 26.2 px
arranca en (400, 504) = la marca     ✓
termina en (400, 532) = el centro    ✓
```

### 4.6 Interpolación — columnas de `EL SELLO` (Unidad VI)

Archivo: `form1_attacks.py` → `SealColumn.extension`
API: `math_utils.ease_out_quad`, `math_utils.ease_in_quad`

```
subida    (0.35 s):  h = H · ease_out_quad(τ) = H · τ·(2 − τ)
retracción (0.40 s):  h = H · (1 − ease_in_quad(τ)) = H · (1 − τ²)

con H = 48 px,  τ = tiempo local normalizado ∈ [0,1]
```

Sube con arranque brusco (la piedra revienta el suelo) y baja despacio
acelerando (se hunde). Las dos funciones son del `math_utils` del framework, no
reimplementadas.

---

## 5. Representación gráfica y Z-order

### 5.1 Geometría de la escena

La arena es un TMX de 50 × 38 tiles (800 × 608 px) con las 8 capas obligatorias
del spec y **tileset propio** (`tileset_paburu.png`, 52 tiles dibujados para este
stage). Objetos: `PlayerSpawn`, `Checkpoint`, `BossPaburu` y `CameraLock` (bloquea
X e Y: la pelea es de una sola pantalla). AUD-538: se eliminó el `NextTrigger`
fantasma que colgaba en y=-64 — el nivel termina en la escena al vencer al
jefe, como `boss_venado` y `boss_rey`.

El escenario sigue el croquis del GDD §3.1: cielo púrpura con luna velada y
montañas y un cementerio lejano en `BG_Far`, ruinas a media distancia en
`BG_Mid`, pilares quebrados y lápidas en `BG_Near`, y cruces, obeliscos y
escombro en `Terrain_Detail`. Los tres guardianes espectrales **ya no van
horneados en el fondo**: son entidades con movimiento propio
(`guardianes.py`) y no aparecen hasta la Forma 2. Los cuatro cuencos de fuego se encienden de a uno por forma
(GDD §3.2 — *"el escenario se ilumina a medida que Paburu se revela"*),
implementado con `LightSystem` en `boss_paburu_scene.py`.

**El decorado no tiene colisión.** Todo lo de `Terrain_Detail` se atraviesa, y
está puesto contra los bordes a propósito: en el centro estorbaría la lectura
de los ataques. La zona del sello (x = 288–512) se deja limpia porque ahí el
boss dibuja su propio sello.

Colisión: 6 sólidos (suelo, techo, 2 muros, 2 aleros de refugio) + 4 plataformas
one-way. Las dos one-way bajas flanquean la zona del sello exactamente
(x = 144–288 y 512–656, contra la zona 288–512): subirse a ellas es la salida
limpia de `EL SELLO`, y también esquiva el `EYE_BEAM` por altura.

Se regenera con `python tools/gen_paburu_tmx.py`.

### 5.2 Orden de renderizado

**Entre entidades**, lo resuelve `DrawingSystem`, que ordena los drawables por
`rect.centery`. El jugador (centery 544) queda delante del boss (centery 528),
que es lo correcto: el jugador puede pararse frente a la cabeza y verse.

**Dentro del boss**, `BossPaburu.draw` dibuja en cuatro capas, de atrás hacia
adelante, y el orden es una decisión de lectura, no un accidente:

| # | Capa                      | Por qué ahí                                                     |
| - | ------------------------- | --------------------------------------------------------------- |
| 1 | Sello grabado             | Está en el piso: todo lo demás lo tapa                           |
| 2 | Columnas de `EL SELLO`    | Emergen del piso, delante del sello pero detrás del boss         |
| 3 | Cuerpo de Paburu          | El sujeto                                                        |
| 4 | Ánimas, proyectiles, rayo | En vuelo: delante de todo, son la información urgente            |

La regla es que **lo que puede matarte se dibuja último**. Un proyectil escondido
detrás de la cabeza sería daño no evitable.

### 5.3 Arte

Hojas propias en `assets/sprites/boss_paburu/`, generadas por
`tools/gen_paburu_art.py` (Forma 1) y `tools/gen_paburu_art_formas.py`
(Formas 2-4). El escenario sale de `gen_paburu_tileset.py` (30 tiles) y
`gen_paburu_fondos.py` (los tres fondos a 800×600):

| Hoja              | Frames | Tamaño | Cuándo se dibuja                                  |
| ----------------- | ------ | ------ | ------------------------------------------------- |
| `stone`           | 4      | 64×64  | Forma 1 idle, 6 FPS                               |
| `hurt`            | 4      | 64×64  | `EnemyState.HURT` en Forma 1, atada a `_hurt_timer` |
| `stone_slam`      | 8      | 64×64  | Con `EL SELLO` activo; la greca se enciende        |
| `stone_crack`     | 8      | 64×64  | Transición 1→2, atada a `transition_timer`         |
| `stone_proyectil` | 3      | 8×8    | Las piedras de `STONE_SPIT`                        |
| `mask`            | 6      | 56×72  | Forma 2 idle, 10 FPS                              |
| `gold`            | 6      | 32×32  | Forma 3A — La Pepita, 14 FPS                       |
| `black`           | 6      | 32×32  | Forma 3B — La Perla, 14 FPS                        |
| `spirit`          | 8      | 64×80  | Forma 4 idle, 10 FPS                              |

Los tamaños de frame **cambian por forma** (64×64 → 56×72 → 32×32 → 64×80,
canon §6.2). Eso es precisamente lo que `BossBase._load_boss_sprites` no
soporta: asume un único tamaño para todo el boss. `sprites.py` carga cada
hoja con su tamaño y `_draw_body` calcula el offset desde el frame real,
así que cada forma calza exacta con su rect — verificado, offset (0,0) en
las cuatro.

Una trampa que hubo que cubrir: la hoja `hurt` es de 64×64 y las Formas 3
miden 32×32. Dibujarla ahí pondría la cabeza de piedra encima de la esfera,
desbordando el rect. Por eso `_pick_frame` solo usa `hurt` en la Forma 1.

El generador es determinista (sin `random`) y es evidencia académica en sí mismo:
iluminación **Lambert sobre un superelipsoide** con rampa de tonos cuantizada de 7
niveles (Unidad V) y **texturizado procedural** con ruido de valor interpolado por
smoothstep 3t²−2t³ para el desgaste y el musgo (Unidad VI).

**Carpeta propia a propósito:** `tools/generate_all_assets.py` (código del profesor)
tiene a Paburu en su tabla de bosses y regenera placeholders de 64×64 en
`assets/sprites/bosses/`. Poner el arte ahí significaría perderlo la próxima vez
que alguien corra ese script. La ruta propia es además la que indica el GDD §8.

El encendido de los ojos del telegraph del `EYE_BEAM` **no** es una hoja: se pinta
como overlay sobre `EYE_BOXES`, porque es un tell de gameplay y tiene que poder
aparecer sobre cualquier pose.

**Tinte espectral (Unidad V):** el placeholder de la piedra usa
`ColorTools.apply_tint(superficie, (0,120,40))`, que sigue activo como fallback si
falta una hoja.

---

## 6. Visual / Audio Design

**Visual.** Paleta canónica del cementerio (Asset Bible): cielo púrpura-negro
`#1a0d26`, piedra pálida `#c8c3b8`, verde espectral `#00c864`, dorado `#e8b12c`,
negro perla `#0d0d14`. La cabeza es piedra verde tallada con un tocado de **greca
escalonada** precolombina, ceja como cornisa saliente, nariz en pirámide truncada
de tres planos y boca de jaguar con las comisuras caídas. Los ojos y la boca están
en el tercio inferior porque la cabeza está semienterrada — y porque es lo que
hace que el `EYE_BEAM` alcance a un jugador de pie.

La arena empieza vacía y oscura, y **se ilumina a medida que Paburu se revela**:
cada invocación de `EL SELLO` deja más marcas grabadas, y al final del combate el
sello está completo y legible.

**Audio.** `bgm_paburu.wav` (pista dedicada, ya existía en el repo).
SFX conectados por EventBus: `SFX_BOSSES_PABURU_EYE_BEAM` para el rayo,
`SFX_PROJECTILE_FIRE` para las piedras, y `SFX_ENVIRONMENT_SCREEN_SHAKE` +
`VFX_SLAM` para `EL SELLO` (que da screen shake y partículas). Falta un sonido
propio para las columnas.

---

## 7. Reflection

Lo más difícil no fue diseñar los ataques sino descubrir que el motor no hacía lo
que yo creía. `EnemyBase` trae un rango de detección de 160×64 px pensado para
enemigos de patrulla, así que mi boss —estático, en el centro de una arena de
800 px— nunca entraba en estado `ALERT` y literalmente no atacaba nunca. Y cuando
por fin atacó, el `EYE_BEAM` no le pegaba a nadie: había calibrado la altura contra
el `rect` del jugador, pero el daño se resuelve contra su `hurtbox`, que empieza
4 px más abajo. El rayo pasaba exactamente 0 px por encima.

Las dos cosas las encontré midiendo, no leyendo. Si tuviera que mejorar algo,
sería empezar por escribir las pruebas de geometría antes que el código de dibujo:
me habrían ahorrado las dos.

---

## 8. Mapeo mecánica → unidad del curso

| Mecánica                             | Unidad | Dónde señalarlo                    | API / matemática                                              |
| ------------------------------------ | ------ | ---------------------------------- | ------------------------------------------------------------- |
| Tiempo de vuelo de `STONE_SPIT`      | **II** | `form1_attacks.spit_flight_time`   | `math_utils.vec2_distance` — norma euclídea                    |
| Resolución balística + abanico       | **II** | `form1_attacks.spit_velocities`    | `v₀ᵧ = Δy/t − ½gt` + matriz de rotación 2D                     |
| Integración del proyectil            | **II** | `StoneProjectile.update`           | Euler semi-implícito                                           |
| Geometría de `EL SELLO`              | **II** | `form1_attacks.seal_vertices`      | Polar→cartesiano con escalado anisótropo + rotación            |
| Dirección y fade de las ánimas       | **II** | `SealAnima.update`, `.alpha`       | `math_utils.vec2_normalize`, `vec2_distance`                   |
| **Trayectoria de las ánimas**        | **III**| `SealAnima.__init__`, `.update`    | `CurveTools.catmull_rom` + `CurveTools.sample_path`            |
| Geometría de la escena y Z-order     | **IV** | `boss_paburu.draw`, el TMX         | 8 capas, parallax, orden por `rect.centery`                    |
| Tinte espectral de la piedra         | **V**  | `BossPaburu._draw_body`            | `ColorTools.apply_tint`                                        |
| Iluminación del arte generado        | **V**  | `tools/gen_paburu_art.py`          | Lambert sobre superelipsoide, rampa de 7 tonos                 |
| Columnas que suben y bajan           | **VI** | `SealColumn.extension`             | `math_utils.ease_out_quad` / `ease_in_quad`                    |
| Texturizado procedural del arte      | **VI** | `tools/gen_paburu_art.py`          | Ruido de valor + smoothstep 3t²−2t³                            |
| *Brillo respirante de la máscara*    | VII    | *EP2*                              | `FilterTools.adjust_brightness`                                |
| *Visión Espectral*                   | VIII   | *EP3*                              | `VisionTools.threshold_binary`                                 |
| *Duelo de los Ecos*                  | IX     | *EP2*                              | Clasificación por umbrales del comportamiento del jugador      |

---

## 9. Archivos

| Archivo                    | Qué es                                                        |
| -------------------------- | ------------------------------------------------------------- |
| `boss_paburu.py`           | La entidad: 4 formas, reloj de ataques, daño y dibujo          |
| `form1_attacks.py`         | Los tres patrones de la Forma 1 + las ánimas, cada uno autónomo |
| `arena.py`                 | Constantes geométricas (espejo de `tools/gen_paburu_tmx.py`)   |
| `sprites.py`               | Carga del sprite del proyectil                                 |
| `boss_paburu_scene.py`     | La escena: registra la entidad, carga el TMX y los cuencos     |
| `GDD.md`                   | Documento de diseño completo hasta EP3                         |
| `ARTE.md`                  | Guía para dibujar el arte a mano sin romper la calibración     |
| `tools/gen_paburu_tmx.py`  | Genera la arena TMX                                            |
| `tools/gen_paburu_art.py`  | Genera el arte de la Forma 1                                   |
| `tools/gen_paburu_art_formas.py` | Genera el arte de idle de las Formas 2-4                 |
| `tools/gen_paburu_tileset.py` | Genera `tileset_paburu.png` — 30 tiles del cementerio       |
| `tools/gen_paburu_fondos.py` | Genera los tres fondos de parallax a 800×600                 |

### Los `# TODO(student)` de `boss_template.py`

| TODO de la plantilla                  | Dónde quedó resuelto                                              |
| ------------------------------------- | ----------------------------------------------------------------- |
| Renombrar la clase                    | `class BossPaburu(BossBase)`                                       |
| Lista de fases completa               | `set_phases()` — 4 formas, umbrales 20/15/10/5                     |
| `max_health` según el spec            | 20.0 (canon 17_BOSS_SPEC §6.1), configurable por propiedad del TMX |
| Nombre del boss para el HUD           | `set_boss_name("EL GRAN SHAMAN PABURU")`                           |
| `_patrol_behavior`                    | Delega en `_update_movement` — la piedra es estática               |
| `_alert_behavior`                     | Movimiento + `_face_player`; el reloj de ataques va en `_post_update` |
| `_get_animation_key`                  | Mapea forma → clave de hoja (`stone`/`mask`/`gold`/`black`/`spirit`) |
| `_build_hitbox` / `_build_hurtbox`    | Rect completo en Forma 1; en Forma 2 será solo la máscara (40×40)   |
| Archivo de escena acompañante         | `boss_paburu_scene.py`                                             |

---

## 10. Verificación (medida corriendo, headless)

| Qué                              | Resultado                                                                                  |
| -------------------------------- | ------------------------------------------------------------------------------------------ |
| Cadencias en 60 s                | `STONE_SPIT` 15× cada 4.02 s · `EYE_BEAM` 7× cada 8.02 s · `EL SELLO` 6× cada 10.00 s        |
| `EYE_BEAM` — daño efectivo       | 7 rayos lanzados, **7 conectan, 0 bloqueados** por invulnerabilidad ajena                     |
| Puntería de `STONE_SPIT`         | La piedra central cae a 0.5–5.5 px del objetivo, a cualquier distancia                      |
| Arco de `STONE_SPIT`             | 27 px de altura pegado al boss, 45 px a media arena — parábola legible en todo el rango     |
| `EYE_BEAM` (rayo y 530..538)     | De pie (hurtbox 532..560) → **toca** · agachado (542..560) → esquiva · en one-way → esquiva  |
| `EL SELLO` — huecos              | En las 12 rotaciones quedan ≥2 huecos ≥26 px; fuera de x = 288–512 nunca alcanza             |
| Curva de las ánimas              | arco/cuerda = 5.24, desviación máx. 26.2 px; arranca en la marca y termina en el centro      |
| Presión sobre un jugador quieto  | 14 ♥ en 60 s. Subió de ~5 al corregir el `EYE_BEAM`, que antes no conectaba nunca: el jefe siempre debió pegar esto. **Es el número a ajustar con playtesting.** |
| No-regresión                     | Las 4 fases se alcanzan, la reliquia se sortea, las marcas persisten entre formas            |
| Consola                          | 20 s de combate con `warnings.simplefilter("error")`: sin excepciones ni warnings            |
| `ruff`                           | Limpio (`EXE002` salta por permisos del checkout, igual que en `boss_venado/` y `engine/`)   |
| `scripts/grade_boss.py`          | **100/100**                                                                                  |

Sobre el autograder: antes daba 95/100 y los 5 puntos faltantes eran
imposibles de obtener. La categoría `boss_name_config` buscaba una asignación
literal `self.boss_name = ...`, pero `BossBase.boss_name` es una **property de
solo lectura** — asignarla lanza `AttributeError`. La forma correcta es
`set_boss_name()`, que es la que usa este boss. Era un chequeo que ningún
alumno que respetara el framework podía pasar. Corregido como **BUG-079** (ver
`REPORTE_MOTOR.md`), el autograder ahora reconoce ambas formas y da 100/100.

---

## 11. Hallazgos del motor

Durante EP1 rigió la regla de no tocar `engine/` ni `framework/`: los hallazgos
se sortearon con workarounds en la escena y en la entidad. **Terminada la
entrega, el profesor dio permiso explícito para corregirlos de raíz.** El
detalle completo —archivo, causa, corrección e impacto de cada uno— está en
`REPORTE_MOTOR.md`, en la raíz del repo.

Veintinueve bugs corregidos (BUG-071 a 081 y BUG-101 a 118). Línea base antes
de tocar nada: `601 passed`. Después: `601 passed`. Sin regresiones. Cada
cambio está marcado en el código con el comentario `BUG-0XX FIX`.

Los más relevantes para este stage:

1. **El parallax no se veía en ningún stage del proyecto** — y por dos bugs
   independientes, cada uno suficiente por sí solo. `StageLoader` construía el
   renderer de pyscroll sin `alpha`, así que el buffer del mapa era opaco y
   tapaba los fondos; y `DrawingSystem` creaba el mosaico de fondo sin
   `SRCALPHA`, así que toda capa con transparencia se volvía negro sólido.
   Corregidos, aparecieron fondos que nunca se habían visto en el proyecto.
2. **`BossBase` heredaba el rango de detección de un enemigo de patrulla**
   (160×64). Un boss estático en una arena de 800 px nunca entraba en `ALERT`
   y no atacaba jamás. Ahora el default es de boss (640×480) y es parámetro.
3. **`_load_boss_sprites` solo servía para el Venado**: seis claves fijas y un
   único tamaño de frame. Ahora acepta `sheets={clave: (ancho, alto)}` y
   `base_dir`, que es exactamente lo que necesitan las formas de Paburu
   (64×64, 56×72, 32×32, 64×80). Esto permitió borrar el cargador propio que
   se había escrito para esquivar la limitación.
4. **`StageData.zone` no existía**, pero `StageScene` lo leía con `getattr`.
   Toda la iluminación por zona era código muerto y el atributo `ZONE` que
   declaran las escenas no se usaba en ningún lado.
5. **`play_music` mataba el juego** si faltaba el `.wav`: atrapaba
   `pygame.error` pero pygame lanza `FileNotFoundError`.

Lo que **no** era un bug del motor y sigue siendo criterio de diseño de este
boss:

- **El reloj de ataques va en `_post_update`, no en `_alert_behavior`.**
  `_run_state_machine` corta antes de los behaviors cuando el boss está en
  `HURT` o `LAUNCHED`; ahí los proyectiles en vuelo se congelarían.
  `_post_update` corre en todos los estados vivos y `_pre_update` ya lo saltea
  durante las transiciones.
- **El daño se resuelve contra `Player.hurtbox`, no contra `Player.rect`** (de
  pie `rect.y+4` con 28 de alto). Calibrar alturas de ataque contra el `rect`
  deja errores de hasta 4 px — en el `EYE_BEAM` era la diferencia entre tocar
  y no tocar.

Pendiente para EP3: `DrawingSystem` filtra por `is_alive`, así que cuando
Paburu muera dejará de dibujarse — y con él las marcas del sello. La secuencia
de derrota (GDD §6, paso 6) necesita que el sello brille *después* de su
muerte, así que las marcas van a tener que mudarse a un drawable de la escena.

---

## Regla de trabajo

Durante EP1: no se modificó `src/engine/` ni `src/framework/`; todo fue código
nuevo bajo `boss_paburu/` más los generadores en `tools/`, y el registro de la
entidad vía `StageLoader.register_entity()`, que es API pública.

Después de EP1, con permiso del profesor, se corrigieron veintinueve bugs del
motor (ver `REPORTE_MOTOR.md`). El criterio se mantuvo: cambio mínimo, sin alterar
comportamiento del que dependan otros stages, y con la suite de tests como red
antes y después de cada cambio.

---
assignment_type: stage
assignment_name: "Entrada y Antenas"
assignment_id: "stage2_2"
zone: 2
student_name: "César Ubáu Calvo"
units_demonstrated: [II, III, IV, V]
evaluation_milestone: "Evaluación Práctica I"
---

# Stage 2-2 — Entrada y Antenas

Sub-zona 1 de la Zona 2 (El Datacenter). Viene después de Stage 2-1 (La
Planicie) y desemboca en el Lobby.

---

## 1. Contexto narrativo

El acercamiento exterior al complejo del datacenter. Un parqueo abandonado bajo
sol de mediodía, una caseta de seguridad con la barrera baja, y sobre el
edificio un campo de antenas: tres mástiles coronados por balizas rojas y dos
parabólicas de comunicación.

El nivel es el **primer contacto del jugador con el complejo**, y su lectura
visual está construida sobre un contraste deliberado: el parqueo es exterior,
soleado y coloreado; el edificio es gris, industrial y cerrado. El jugador
atraviesa el primero y escala el segundo, de modo que la transición hacia el
interior oscuro que continúa el Lobby ocurre como recorrido, no como corte.

Los enemigos son serpientes y variantes serpiente —los "terciopelo" migraron al
datacenter por el calor de los servidores— más el personal de seguridad
infestado.

**Estructura en tres secciones**, sobre un plano único de 120 × 50 tiles
(1920 × 800 px):

| Sección | Columnas | Contenido |
|---|---|---|
| Suelo | 0 – 79 | Parqueo, zanja con pasarela, caseta de seguridad |
| Escalada | 68 – 79 | Seis repechos por el costado del edificio |
| Azotea | 80 – 119 | Mástiles, dos parabólicas y pasarelas angostas |

**Límite de tiempo:** 170 s · **Banner:** `2-2  ENTRADA Y ANTENAS`

---

## 2. Conceptos académicos demostrados

### Unidad II — Sistemas de coordenadas y vectores

**Archivo:** `camara_seguridad.py` · **Clase:** `CamaraSeguridad`

Dos cámaras de vigilancia —una en la caseta (1166, 634), otra en la azotea
(1332, 248)— barren un arco y detectan al jugador dentro de un cono de visión.
La detección se resuelve enteramente con álgebra vectorial de
`src/engine/utils/math_utils.py`.

Sean `C` la posición de la cámara, `P` el centro del jugador y `m` el vector
unitario de mira. El vector cámara→jugador es `v = P − C`.

**Paso 1 — magnitud.** `vec2_distance(C, P)` calcula la norma euclidiana:

```
d = √((Pₓ − Cₓ)² + (P_y − C_y)²)
```

Es un escalar: mide *cuánto*, no *hacia dónde*. Si `d > alcance` se descarta
sin más cálculo.

**Paso 2 — dirección.** `vec2_normalize(v)` divide el vector por su magnitud:

```
v̂ = v / |v|,    con |v̂| = 1
```

Conserva **solo la dirección** y descarta la longitud, que ya se midió en el
paso 1. Normalizar es obligatorio para el paso 3: sin ello el producto punto
mezclaría distancia con ángulo.

**Paso 3 — ángulo.** `vec2_dot(v̂, m)` calcula:

```
v̂ · m = v̂ₓmₓ + v̂_y m_y = |v̂||m| cos θ = cos θ
```

Como ambos vectores son unitarios, sus magnitudes valen 1 y **el producto punto
es directamente el coseno del ángulo**. El jugador está dentro de un cono de
apertura `fov` si:

```
cos θ ≥ cos(fov / 2)
```

**Por qué se comparan cosenos y no ángulos.** En [0°, 180°] el coseno es
monótono decreciente, así que comparar cosenos equivale a comparar ángulos.
Pero `cos(fov/2)` se calcula **una sola vez en el constructor** y por fotograma
solo hay dos multiplicaciones y una suma — cero llamadas trigonométricas, y sin
el análisis de cuadrantes que exigiría `atan2`.

**Cuarta aplicación:** `_alertar_enemigos_cercanos` usa `vec2_distance` otra vez
para despertar a los enemigos en patrulla dentro de un radio de 150 px. La
detección no solo cambia de color: comunica la posición del jugador.

**Verificación** (umbral `cos(35°) = 0.81915`):

| Caso | cos θ | Detecta | Esperado |
|---|---|---|---|
| Al frente, 100 px | +1.0000 | sí | sí |
| Al frente, 200 px (fuera de alcance) | — | no | no |
| A 30° del eje, 100 px | +0.8670 | sí | sí |
| A 50° del eje, 100 px | +0.6392 | no | no |
| Detrás, 100 px | −1.0000 | no | no |
| **Jugador exactamente encima (v = 0)** | +0.0000 | no | no |

El último caso es el degenerado: normalizar el vector nulo sería dividir por
cero. `vec2_normalize` devuelve el vector nulo cuando `|v| < 1e-10`, el
producto punto da 0, y 0 < 0.819 → no detecta. No lanza excepción.

**Funciones usadas:** `vec2_normalize`, `vec2_dot`, `vec2_distance`

---

### Unidad III — Curvas paramétricas (B-Spline)

**Archivo:** `patrulla_bspline.py` · **Clase:** `PatrullaBSpline`

Un `FlyingBoa` patrulla el campo de antenas siguiendo una B-Spline cúbica que
se enrolla alrededor de los tres mástiles, según exige
`docs/16_WORLD_DESIGN.md` §4.3 para este escenario.

#### Bézier contra B-Spline

Una Bézier de grado `n` se evalúa sobre la base de Bernstein:

```
B(t) = Σ  C(n,i) · tⁱ · (1−t)^(n−i) · Pᵢ
      i=0..n
```

Cada polinomio de Bernstein es distinto de cero en **todo** el intervalo (0, 1).
De ahí dos problemas para una ruta de patrulla:

1. **Soporte global.** Mover un punto de control deforma la curva completa.
   Ajustar cómo el enemigo rodea el tercer mástil cambiaría su vuelta alrededor
   del primero.
2. **Grado atado al número de puntos.** Con 8 puntos, la Bézier es de grado 7:
   un polinomio que oscila y se aleja del polígono de control.

Una B-Spline separa ambas cosas mediante un **vector de nodos**:

```
C(t) = Σ  N_{i,p}(t) · Pᵢ
      i=0..n−1
```

con las bases dadas por la recursión de **Cox–de Boor**:

```
N_{i,0}(t) = 1  si  tᵢ ≤ t < t_{i+1},  0 en otro caso

              t − tᵢ                    t_{i+p+1} − t
N_{i,p}(t) = ──────────── N_{i,p−1}(t) + ───────────────── N_{i+1,p−1}(t)
             t_{i+p} − tᵢ               t_{i+p+1} − t_{i+1}
```

La propiedad decisiva es el **soporte local**: `N_{i,p}(t) = 0` fuera de
`[tᵢ, t_{i+p+1})`. Cada punto de control influye solo sobre `p+1` tramos, así
que cada mástil se ajusta por separado. Y el grado se mantiene en 3 sin
importar cuántos waypoints se agreguen.

#### La relación m = n + p + 1

```
m nodos = n puntos de control + grado p + 1
12      = 8                   + 3         + 1
```

Es la restricción que obliga a `n ≥ p + 1`: con menos de 4 puntos de control no
existe una cúbica. `PatrullaBSpline.__init__` lanza `ValueError` en ese caso, en
vez de dejar que `CurveTools.b_spline` devuelva los puntos sin curvar — que
produciría un enemigo moviéndose en línea recta sin aviso de que la curva nunca
se calculó.

Vector de nodos generado por `CurveTools._uniform_knots(8, 3)`:

```
[0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 6, 6]      dominio: t ∈ [0, 5]
```

#### Puntos de control

Objetos `Waypoint` de la capa `Objects`, enlazados por `owner_id = FlyingBoa_01`
y ordenados por `waypoint_index`. Mástiles en x = 1376–1392, 1504–1520 y
1632–1648, de y = 128 (punta) a y = 256 (azotea).

| `waypoint_index` | Coordenada | Posición relativa |
|---|---|---|
| 0 | (1328, 216) | entrada, bajo |
| 1 | (1376, 100) | **sobre el mástil A** |
| 2 | (1440, 248) | bajo, entre A y B |
| 3 | (1504, 100) | **sobre el mástil B** |
| 4 | (1568, 248) | bajo, entre B y C |
| 5 | (1632, 100) | **sobre el mástil C** |
| 6 | (1680, 200) | extremo derecho |
| 7 | (1616, 244) | retorno, bajo |

La alternancia de los puntos es **más extrema que el zigzag que se quiere ver**,
y es a propósito: una B-Spline **no interpola** sus puntos de control, los
aproxima, y queda contenida en su envolvente convexa. Medido: con la alternancia
inicial (y = 128 / 224) la curva daba 54 px de amplitud; con 100 / 248 da 76 px.

#### Parametrización por longitud de arco

`CurveTools.b_spline` devuelve muestras uniformes **en el parámetro t**, no en
distancia. Una curva no tiene rapidez constante respecto de su parámetro: donde
se curva mucho, muestras consecutivas quedan juntas. Avanzar de muestra en
muestra a ritmo fijo produciría un enemigo que acelera en las rectas y frena en
las vueltas.

Se tabula la longitud acumulada de la poligonal y se avanza sobre esa magnitud:

```
s(k) = Σ |Q_j − Q_{j−1}|     para j = 1..k
```

Dado `s`, `bisect` localiza el tramo en O(log n) y se interpola linealmente.

**Verificación:**

| Comprobación | Resultado |
|---|---|
| `m = n + p + 1` | 12 nodos para n = 8, p = 3 |
| Envolvente convexa | curva contenida en la caja de los puntos de control |
| **Rapidez constante** | **0.7499 px/fotograma, σ = 0.0001** (esperado 0.75 a 45 px/s y 60 fps) |
| Se enrolla | 6 cruces de la altura media |
| Guarda `n < p+1` | lanza `ValueError` con la fórmula en el mensaje |

Longitud de arco: 474 px · Ida y vuelta: 21.1 s · 160 muestras

El recorrido es de **vaivén** y no cíclico: la B-Spline que genera
`_uniform_knots` es abierta, así que cerrar el ciclo teletransportaría al
enemigo del final al principio.

**Funciones usadas:** `CurveTools.b_spline`

---

### Unidad IV — Representación de escena y scroll vertical

**Archivos:** `stage2_2.tmx`, `stage2_2.py`

#### Las ocho capas

El TMX declara las ocho capas de `docs/06_TMX_SPEC.md` §3.1 en orden, de abajo
hacia arriba: `BG_Far`, `BG_Mid`, `BG_Near`, `Terrain`, `Terrain_Detail`,
`Objects` (objetos), `Collision` (objetos), `FG_Overlay`.

El mapa es un plano cartesiano discreto de 120 × 50 celdas con origen
arriba-izquierda y **eje Y hacia abajo** (convención de pantalla, no
matemática). La conversión celda→píxel es `x = columna × 16`, `y = fila × 16`.

Contiene **50 objetos**: 34 en `Objects` y 16 en `Collision`.

| Tipo | Cantidad | | Tipo | Cantidad |
|---|---|---|---|---|
| `PlayerSpawn` | 1 | | `Solid` | 14 |
| `Checkpoint` | 5 | | `Platform` | 2 |
| `NextTrigger` | 1 | | `Waypoint` | 8 |
| `CameraLock` | 1 | | `Light` | 7 |
| `DeathPit` | 1 | | `MessageTrigger_Once` | 3 |
| Enemigos | 7 | | | |

#### Parallax como razón de desplazamiento

La cámara asigna un factor por nombre de capa:

| Capa | Parallax X | Parallax Y |
|---|---|---|
| `BG_Far` | 0.15 | 0.05 |
| `BG_Mid` | 0.40 | 0.15 |
| `BG_Near` | 0.70 | 0.30 |
| `Terrain` | 1.00 | 1.00 |

El factor es la razón entre el desplazamiento de la capa y el de la cámara. Una
capa a 0.15 se mueve al 15 % de la velocidad del primer plano, y el ojo lee eso
como distancia. Es **paralaje de movimiento**: profundidad codificada como razón
de velocidades, sin proyección 3D. Las tres capas están pintadas: cielo y nubes
en `BG_Far`, línea de pinos lejana en `BG_Mid`, arbustos en `BG_Near`.

#### Bloqueo de cámara por zona

Un objeto `CameraLock` en `Rect(1072, 256, 224, 448)` con `lock_x=true`,
`lock_y=false` cubre la sección de escalada. Dentro de esa zona la cámara
**congela su desplazamiento horizontal y solo sigue el vertical** — el eje de
seguimiento cambia, que es lo que pide el documento de diseño.

| Posición del jugador | `locked_x` | `locked_y` |
|---|---|---|
| Parqueo (48, 672) | False | False |
| **Escalada (1120, 500)** | **True** | False |
| Azotea (1400, 224) | False | False |
| Salida (1700, 200) | False | False |

#### Geometría derivada de la física

Las alturas no son estéticas. De `settings.py` (`PLAYER_JUMP_FORCE = −380.0`,
`GRAVITY = 800.0`, `PLAYER_WALK_SPEED = 90.0`):

```
h_max   = v² / (2g)    = 380² / (2 × 800)  = 90.25 px
t_aire  = 2v / g       = 2 × 380 / 800     = 0.95 s
gap_max = v_h × t_aire = 90 × 0.95         = 85.5 px
```

Bandas de clasificación: cómodo ≤ 68.4 px · exigente ≤ 171.0 px.

`level_metrics.JumpEnvelope.classify_ledge` marca **imposible** todo repecho
mayor a `h_max`, y **no cuenta el doble salto** aunque el jugador lo tenga. Por
eso los seis repechos de la escalada están separados exactamente **64 px**:
dentro de la banda "cómodo" con margen.

El único salto exigente del nivel es un repecho **opcional** en (928, 448), a
96 px de `Solid_P4`. Está por encima de `gap_max` de un salto simple, así que
obliga al doble salto, y recompensa con un fragmento de lore. La ruta crítica
es cómoda; el desafío es opcional y está premiado.

Cinco checkpoints en (400, 672), (800, 672), (1184, 480), (1232, 672) y
(1312, 224). Distancias consecutivas: 352, 400, 429, 198, 455 y 400 px — todas
por debajo del `MAX_CHECKPOINT_GAP` de 500 px.

---

### Unidad V — Espacios de color y transparencia

**Archivo:** `atmosfera.py` · **Clase:** `AtmosferaAntenas`

#### Por qué HSV y no RGB

HSV es una reparametrización cilíndrica del cubo RGB. Con `M = max(R,G,B)` y
`m = min(R,G,B)`:

```
V = M
S = (M − m) / M          (0 si M = 0)
H = 60° · f(R,G,B)       según cuál canal sea el máximo
```

La propiedad que importa es que **V es un eje ortogonal a H y S**. Atenuar un
rojo en RGB obliga a escalar los tres canales de forma coordinada, y cualquier
descoordinación corrompe el matiz. En HSV basta con mover V.

#### Efecto 1 — Balizas de antena

Tres luces rojas parpadean desfasadas en las puntas de los mástiles
—(1384, 136), (1512, 136) y (1640, 136)— modulando **solo el canal V**:

```
V(t) = V_min + (V_max − V_min) · (1 + sin(2π f t)) / 2
```

con `V_min = 0.22`, `V_max = 1.00`, `f = 0.85 Hz`. La sinusoide se elige sobre
una onda cuadrada porque una luz de advertencia real tiene inercia térmica en
el filamento: sube y baja de forma continua.

**Verificación** — el matiz y la saturación no deben cambiar:

| t (s) | V | Color RGB | h | s |
|---|---|---|---|---|
| 0.0 | 0.610 | (156, 34, 25) | 4.1° | 0.840 |
| 0.2 | 0.952 | (243, 52, 39) | 3.8° | 0.840 |
| 0.8 | 0.257 | (66, 14, 11) | 3.3° | 0.833 |

Matiz en **[3.1°, 4.9°]**, saturación en **[0.831, 0.846]** mientras el brillo
recorre todo su rango. La variación residual es error de cuantización a 8 bits.

#### Efecto 2 — Velo atmosférico por altura

La escena pasa de un tono cálido en el parqueo (y = 704) a uno frío en la
azotea (y = 256), interpolando **en HSV**. El matiz es un ángulo, así que se
toma el arco corto:

```
d    = ((h₂ − h₁ + 180) mod 360) − 180        con d ∈ [−180, 180]
h(t) = (h₁ + d·t) mod 360
```

**Un caso degenerado que la prueba destapó.** Naranja está en 29° y azul en
214°: **exactamente 180° de separación**. Los dos arcos miden lo mismo y la
fórmula no puede preferir uno; elige el negativo, que recorre la zona magenta. A
media escalada el velo salía en **RGB(255, 134, 253)**.

Forzar el sentido contrario no arregla nada: pasaría por verde. Interpolar a
saturación plena entre matices opuestos **siempre** atraviesa un color ajeno a
los dos extremos.

La solución es física: la perspectiva atmosférica no conserva la pureza del
color, el aire dispersa y **desatura** hacia el blanco. Se deprime la saturación
en el centro del recorrido:

```
S(t) = lerp(S₁, S₂, t) · (1 − c · sin(π t))        con c = 0.80
```

El seno vale 0 en los extremos y 1 en el medio, así que los colores declarados
se respetan exactamente y el tránsito pasa por bruma pálida:

| Altura | Antes | Ahora | s |
|---|---|---|---|
| Parqueo (y = 704) | (255, 186, 122) | (255, 186, 122) | 0.522 |
| Media escalada (y = 480) | **(255, 134, 253)** | **(255, 231, 255)** | 0.094 |
| Azotea (y = 256) | (146, 194, 255) | (146, 194, 255) | 0.427 |

Es el mismo motivo por el que una montaña lejana se ve azul **claro** y no azul
intenso.

#### Alfa y composición aditiva

`ColorTools.apply_tint` usa internamente `pygame.surfarray.array3d`, que
**descarta el canal alfa por píxel**: la superficie que devuelve es de 24 bits.
Un halo con degradado de transparencia perdería su desvanecido y saldría como un
cuadrado sólido.

Por eso el halo se construye como un **degradado de brillo sobre negro** y se
compone con `BLEND_RGB_ADD`. En composición aditiva el negro suma cero, así que
las esquinas son invisibles sin necesitar alfa. Es además físicamente correcto:
la luz emitida se **suma** a lo que hay detrás, no lo reemplaza.

La caída del halo es cuadrática, `(1 − d/r)²`, porque la irradiancia de una
fuente puntual decae con el cuadrado de la distancia.

**Coste medido:** 0.86 ms por fotograma, de los 16.7 disponibles a 60 fps.

**Funciones usadas:** `ColorTools.rgb_to_hsv`, `ColorTools.hsv_to_rgb`,
`ColorTools.apply_tint`

---

## 3. Cómo ejecutar

```powershell
cd <raíz del repositorio>
.\.venv\Scripts\Activate.ps1
python main.py --stage stage2_2
```

**Modo de pruebas** — deja a los enemigos visibles pero sin daño, para recorrer
el nivel sin combate:

```powershell
$env:LOI_SIN_ENEMIGOS=1
python main.py --stage stage2_2
```

Se lee de una variable de entorno y no de una constante en el código: un
interruptor que hay que acordarse de apagar antes de entregar es un interruptor
que se queda encendido.

**Tecla F1** — dibuja el polígono de control de la B-Spline y sus vértices sobre
la curva, haciendo visible la propiedad de la envolvente convexa.

---

## 4. Verificación

```powershell
python scripts\validate_tmx.py assets\maps\stage2_2\stage2_2.tmx
python scripts\grade_stage.py assets\maps\stage2_2\stage2_2.tmx
python scripts\preview_tmx.py assets\maps\stage2_2\stage2_2.tmx --salida vista.png --con-etiquetas
```

`validate_tmx.py`: **1/1 passed**.
`grade_stage.py`: **129 / 130 (99.2 %)**. Como referencia, el `stage0` del
equipo docente obtiene 121 / 130 (93.1 %).

| Criterio | Puntos |
|---|---|
| `checkpoints` | 15 / 15 |
| `design_completable` | 12 / 12 |
| `design_geometry` | 10 / 10 |
| `design_pacing` | 8 / 8 |
| `enemies_placed` · `enemies_valid_types` | 10 / 10 · 10 / 10 |
| `collectibles` | 10 / 10 |
| `required_layers` · `player_spawn` | 10 / 10 · 10 / 10 |
| `tileset_valid` · `climate_valid` | 5 / 5 · 5 / 5 |
| `map_bounds_reasonable` · `time_limit_reasonable` | 5 / 5 · 5 / 5 |
| `file_parses` | 5 / 5 |
| `metadata` | 9 / 10 — máximo alcanzable, ver §5 |

Análisis de `level_metrics.analyse_stage`: `exit_reachable = True`, **0
plataformas huérfanas de 12**, cero huecos imposibles, cero repechos imposibles,
un único salto exigente de 96 px.

Se simularon además **600 fotogramas (10 s)** de `update()` y `draw()` sin
ninguna excepción.

---

## 5. Discrepancias encontradas entre documentación y código

Documentadas con evidencia, porque varias condicionaron decisiones de diseño de
este escenario.

### Contradicciones en la documentación

| # | Discrepancia | Resolución |
|---|---|---|
| 1 | `30_ASSIGNMENT_01_STAGE_DESIGN.md` indica tiles de 32×32 y mapa mínimo 40×23; `06_TMX_SPEC.md`, la plantilla y `settings.TILE_SIZE` indican **16×16** | Se usa 16×16 |
| 2 | `16_WORLD_DESIGN.md` §4.3 asigna `FlyingAntena` y `ShooterSerpiente` a este stage; **ninguno existe** en `bestiary_registry.SPECIES` | Se usan especies reales del roster (§6) |
| 3 | El brief indica resolución interna 320×224; `settings.py` define `INTERNAL_WIDTH = 800`, `INTERNAL_HEIGHT = 600`, y deja 320×224 solo como `REFERENCE_*` para arte legacy | El mapa se dimensiona contra 800×600 |

### Defectos en el código

| # | Archivo | Defecto | Impacto |
|---|---|---|---|
| 4 | `scripts/grade_stage.py` | `metadata` puntúa `meta_score × 3` sobre 3 propiedades, contra un máximo declarado de 10 | **Nadie puede obtener 10/10** |
| 5 | `scripts/grade_stage.py` | Busca la capa `Collision` entre las capas de tiles (`<layer>`), siendo una capa de objetos (`<objectgroup>`) | Aviso falso en todos los mapas |
| 6 | `scripts/grade_stage.py` | `KNOWN_ENEMY_TYPES` solo lista arquetipos y cuatro nombres legacy (`MushMom`, `Bat`, `Skitter`, `Mantis`) que ya no existen; **ninguna de las 21 especies del roster está incluida** | Un stage 100 % fiel a `18_ENEMY_ROSTER.md` obtiene **0/20** en enemigos |
| 7 | `StageLoader._build_waypoints` | Acumula los waypoints en orden de aparición en el XML y **nunca los ordena por `waypoint_index`**, pese a que `06_TMX_SPEC.md` §6.3 afirma que sí | Reordenar dos objetos en Tiled cambia la curva sin ningún error visible |
| 8 | `Camera.set_camera_locks` | `_CameraLock` guarda un `rect` que **no se consulta jamás**: basta con que exista un lock con `lock_x=True` para congelar el eje X durante todo el nivel | El `CameraLock` de la Unidad IV **no se puede demostrar** con el motor tal cual |
| 9 | `LightingSystem.render` (línea 224) | `int(ambient_color[i] × brillo)` sin recortar a [0, 255]. El brillo es `ambient_light × factor_ambiente(hora) × factor_luz(estación)`, y `summer` aporta ×1.08 | Cualquier `ambient_light > 0.925` con `noon` + `summer` **lanza `ValueError` al dibujar** |

**Cómo se rodearon 7, 8 y 9 sin modificar el framework:**

- **7** — `Stage2_2._leer_waypoints` lee el TMX directamente y ordena por
  `waypoint_index`, en vez de confiar en `entity.waypoints`.
- **8** — `Stage2_2._corregir_bloqueo_camara` filtra los locks por contención
  del jugador y vuelve a llamar a `set_camera_locks`. Funciona porque
  `StageScene._update_camera_map` llama primero a `camera.update(dt)` y después
  a `set_camera_locks`, así que las banderas de un fotograma se aplican en el
  siguiente y la última escritura gana. Coste: un fotograma de latencia.
- **9** — `ambient_light` se topa en 0.88, de modo que
  `0.88 × 1.00 × 1.08 = 0.950` queda en rango.

Ninguna línea de `src/engine/` ni de `src/framework/` fue modificada. Las
entidades propias se integran sobreescribiendo `update()` y `draw()` con
llamada a `super()`, que es herencia normal.

---

## 6. Enemigos

Mezcla deliberada de especies con nombre del roster (identidad de la Zona 2) y
arquetipos base. Los arquetipos son necesarios porque `grade_stage.py` no
reconoce las especies (defecto 6).

| Tipo | Cantidad | Posición | Sección |
|---|---|---|---|
| `Walker` | 1 | (600, 704) | Parqueo |
| `WalkerGuardia` | 2 | (1216, 704) y (1120, 640) | Suelo y techo de la caseta |
| `Flying` | 1 | (1040, 500) | Hueco de la escalada |
| `FlyingBoa` | 1 | (1344, 160) | Azotea — **recorre la B-Spline** |
| `ShooterSerpienteArbol` | 1 | (1440, 192) | Pasarela entre antenas |
| `WalkerSerpientePequena` | 1 | (1536, 256) | Azotea |

Los primeros 560 px del parqueo quedan **sin enemigos**: es la caminata de
apertura, y el jugador necesita aprender a moverse antes de recibir presión.
`alert_speed` se baja a 55 px/s (contra `PLAYER_WALK_SPEED = 90`) para que huir
sea posible, y `damage_on_contact` a 0.25.

---

## 7. Archivos entregados

| Archivo | Contenido |
|---|---|
| `src/stages/stage2_2/stage2_2.py` | `Stage2_2(StageScene)` — integración y correcciones |
| `src/stages/stage2_2/camara_seguridad.py` | Unidad II — matemática vectorial |
| `src/stages/stage2_2/patrulla_bspline.py` | Unidad III — curva B-Spline |
| `src/stages/stage2_2/atmosfera.py` | Unidad V — espacios de color |
| `src/stages/stage2_2/README.md` | Este documento |
| `assets/maps/stage2_2/stage2_2.tmx` | Mapa 120 × 50, 8 capas, 50 objetos |
| `student_assets/tilesets/tileset_parqueo.png` | Tileset propio, 128 tiles de 16 × 16 |

El TMX declara **dos tilesets**: `firstgid = 1` para `tileset_datacenter_ext`
(edificio y mástiles) y `firstgid = 65` para `tileset_parqueo` (exterior).

El tileset propio existe porque los diez tilesets provistos son el mismo archivo
recoloreado: siete tiles de color plano, sin cielo, vegetación ni vehículos.
Contiene cielo y nubes, césped y tierra, asfalto, árboles frondosos y pinos,
tres carros, farolas, bancas, reja, barrera, señalética, la caseta y **dos
parabólicas de comunicación**. Se ubica en `student_assets/tilesets/` según
`06_TMX_SPEC.md` §5.2.

El módulo se llama `stage2_2` y no `entrada_antenas` porque
`src/engine/core/stage_registry.py` declara el orden canónico en `STAGE_ORDER`,
y esa ranura se llama `stage2_2`. Un módulo con otro nombre arranca con
`--stage` pero `discover_stages()` nunca lo encuentra.

---

## 8. Capturas

No aplican a esta entrega. `docs/entregables/entregables.md` las exige para
operaciones de `FilterTools` y `VisionTools`, que corresponden a la Evaluación
Práctica II (histograma, kernels, detección de bordes).

---

# Hoja de trabajo (`README_template.md`)

Secciones exigidas por la plantilla `student_templates/stage_template/README_template.md`.

**Nombre del estudiante:** César Ubáu Calvo · **Stage ID:** `stage2_2`

---

## T1. Concepto del escenario

El acercamiento exterior al datacenter, en tres actos encadenados sin cortes. El
jugador aparece en un parqueo abandonado a mediodía, con carros que llevan
semanas sin moverse, y camina hacia la derecha durante ~9 segundos con nada más
que cielo, árboles y asfalto en pantalla. Al fondo aparece la caseta de
seguridad con la barrera baja, y detrás de ella la fachada del edificio: seis
repechos de servicio que hay que escalar. Arriba está el campo de antenas, con
tres mástiles de baliza roja y dos parabólicas de comunicación. La lectura
visual va de exterior soleado y coloreado a industrial gris y cerrado, de modo
que la transición hacia el interior que continúa el Lobby ocurre como recorrido
y no como corte.

---

## T2. Requisitos del tileset

Dos tilesets. El del datacenter es provisto; el del parqueo es propio, creado
porque los diez tilesets del repositorio son el mismo archivo recoloreado —
siete tiles de color plano, sin cielo, vegetación ni vehículos.

### `tileset_datacenter_ext` (provisto) — `firstgid = 1`

| GID | Descripción | ¿Colisión? |
|---|---|---|
| 0 | Vacío / aire | No |
| 2 | Panel de acero estriado — edificio y mástiles | Sí (vía `Collision`) |
| 4 | Gris claro — repechos y pasarelas | Sí (vía `Collision`) |
| 5 | Panel azul con línea de luz — ventanas | No |
| 6 | Rejilla naranja de ventilación | No |
| 7 | Rejilla roja — puntas de baliza, señalética | No |

### `tileset_parqueo` (propio, 128 tiles) — `firstgid = 65`

| GID | Descripción | ¿Colisión? |
|---|---|---|
| 65 – 69 | Cielo y cuatro variantes de nube | No |
| 81 – 83 | Césped, tierra, tierra con piedras | No |
| 84 – 86 | Bordillo, acera (pasarela), muro de piedra | Sí — solo la acera, vía `Solid_Puente` |
| 97 – 101 | Asfalto y sus variantes: línea, oscuro, raya, mancha | Sí (vía `Collision`) |
| 113 – 121 | Copa de árbol frondoso, 3 × 3 tiles | No |
| 122 – 124 | Tronco, arbusto, flores | No |
| 125 – 127 | Pino: punta, medio, base | No |
| 129 – 130 | Poste de farola, lámpara | No |
| 131 – 132 | Banca de madera, izquierda y derecha | No |
| 133 – 134 | Señal de parqueo, basurero | No |
| 135 – 137 | Reja, poste de barrera, brazo de barrera | No |
| 145 – 147, 161 – 163 | Carro rojo: techo y carrocería | No |
| 148 – 150, 164 – 166 | Carro azul: techo y carrocería | No |
| 151 – 153, 167 – 169 | Carro verde: techo y carrocería | No |
| 177 – 180 | Caseta: muro, ventana, techo, puerta | Sí (vía `Solid_Caseta`) |
| 181 – 192 | **Antena parabólica, 3 × 4 tiles** | No |

**Ningún tile es placeholder.** La colisión nunca se deriva de los tiles: sale
exclusivamente de los 16 rectángulos de la capa `Collision`, tal como exige
`06_TMX_SPEC.md` §9.5. Eso permite que el terreno visual se dibuje libremente
sin quedar atado a la geometría jugable.

---

## T3. Colocación de entidades

| X | Y | Tipo | Propiedades |
|---|---|---|---|
| 48 | 704 | `PlayerSpawn` | — (la Y son los pies) |
| 600 | 704 | `Walker` | `patrol_length=96`, `facing=right`, `alert_speed=55.0`, `damage_on_contact=0.25` |
| 1216 | 704 | `WalkerGuardia` | `patrol_length=64`, `facing=left`, `alert_speed=55.0`, `damage_on_contact=0.25` |
| 1120 | 640 | `WalkerGuardia` | `patrol_length=64`, `facing=left`, `alert_speed=55.0`, `damage_on_contact=0.25` |
| 1040 | 500 | `Flying` | `flight_mode=sine`, `flight_speed=45.0`, `sine_amplitude=36.0`, `sine_frequency=1.0`, `damage_on_contact=0.25` |
| 1344 | 160 | `FlyingBoa` | `flight_mode=patrol`, `flight_speed=45.0`, `damage_on_contact=0.25` |
| 1440 | 192 | `ShooterSerpienteArbol` | `fire_rate=0.35`, `projectile_speed=100.0`, `projectile_damage=0.25` |
| 1536 | 256 | `WalkerSerpientePequena` | `patrol_length=96`, `facing=left`, `alert_speed=60.0`, `damage_on_contact=0.25` |
| 1696 | 192 | `NextTrigger` | rect 32 × 64 |
| 1072 | 256 | `CameraLock` | `lock_x=true`, `lock_y=false`, rect 224 × 448 |
| 224 | 784 | `DeathPit` | rect 64 × 16, bajo la pasarela |
| 160 / 944 / 1632 | 672 / 416 / 224 | `MessageTrigger_Once` | `text`, `duration=4.0` — fragmentos de lore |
| 8 posiciones | — | `Waypoint` | `owner_id=FlyingBoa_01`, `waypoint_index` 0–7 (ver §2, Unidad III) |
| 7 posiciones | — | `Light` | 3 balizas rojas, 3 farolas cálidas, 1 foco frío en la caseta |

### Geometría de colisión

| Nombre | Tipo | X | Y | Ancho | Alto |
|---|---|---|---|---|---|
| `Solid_Muro_Izq` | Solid | −16 | 0 | 16 | 800 |
| `Solid_Muro_Der` | Solid | 1920 | 192 | 16 | 608 |
| `Solid_Parqueo_A` | Solid | 0 | 704 | 224 | 96 |
| `Solid_Puente` | Solid | 224 | 704 | 64 | 16 |
| `Solid_Parqueo_B` | Solid | 288 | 704 | 992 | 96 |
| `Solid_Caseta` | Solid | 1072 | 640 | 96 | 64 |
| `Solid_Edificio` | Solid | 1280 | 256 | 640 | 544 |
| `Solid_P1` … `Solid_P5` | Solid | 1088 / 1168 | 640 → 384 | 80 | 16 |
| `Solid_P6` | Solid | 1216 | 320 | 64 | 16 |
| `Solid_Bonus` | Solid | 928 | 448 | 64 | 16 |
| `Platform_Antena_A` | **Platform** | 1424 | 192 | 64 | 16 |
| `Platform_Antena_B` | **Platform** | 1552 | 192 | 64 | 16 |

Las dos pasarelas de antena son `Platform` —atravesables desde abajo— porque
son rejillas angostas y subir a ellas debe sentirse fluido. Los repechos de la
escalada son `Solid` por dos razones: narrativamente son repechos de concreto
en una fachada, y `level_metrics.analyse_stage` **solo lee `collision_rects`**,
así que un repecho declarado `Platform` es invisible para el análisis de
alcanzabilidad y rompería `design_completable`.

---

## T4. Checkpoints

| ID | X | Y | Ubicación |
|---|---|---|---|
| 0 | 400 | 672 | Parqueo, tras los primeros carros |
| 1 | 800 | 672 | Parqueo, mitad del recorrido |
| 2 | 1184 | 480 | Mitad de la escalada, sobre `Solid_P3` |
| 3 | 1232 | 672 | Pie de la escalada |
| 4 | 1312 | 224 | Azotea, al salir de la escalada |

Todos son rectángulos de 32 × 32 con su borde inferior alineado al borde
superior de un tile de terreno, como exige `06_TMX_SPEC.md` §7.5. Distancias
consecutivas: 352, 400, 429, 198, 455 y 400 px, todas bajo el
`MAX_CHECKPOINT_GAP` de 500 px.

Son cinco y no uno porque con 1920 px de recorrido un solo punto de reaparición
haría que morir en la azotea costara todo el nivel.

---

## T5. Notas de lógica personalizada

Tres comportamientos propios, todos integrados sobreescribiendo `update()` y
`draw()` de `StageScene` con llamada a `super()`. **No se modificó ninguna línea
de `src/engine/` ni de `src/framework/`.**

1. **Cámaras de vigilancia** (`camara_seguridad.py`) — dos cámaras barren un
   arco sinusoidal y detectan al jugador por producto punto de vectores
   unitarios. Al detectarlo, despiertan a los enemigos en patrulla dentro de
   150 px. Detalle en §2, Unidad II.

2. **Patrulla sobre B-Spline** (`patrulla_bspline.py`) — la curva se evalúa una
   sola vez al iniciar el escenario y se recorre a rapidez constante mediante
   una tabla de longitud de arco. La entidad se localiza por tener waypoints
   asignados, no por nombre: `StageLoader._handle_entity_spawn` descarta el
   nombre del objeto TMX al construir la entidad. Detalle en §2, Unidad III.

3. **Atmósfera** (`atmosfera.py`) — balizas que modulan el canal V de HSV y un
   velo cuyo color se interpola en HSV según la altura del jugador. Detalle en
   §2, Unidad V.

Además, tres correcciones que rodean defectos del framework sin tocarlo:
lectura ordenada de waypoints, filtrado del `CameraLock` por contención, y tope
de `ambient_light` para no desbordar el multiplicador de iluminación. Las tres
están explicadas con su mecanismo en §5.

Y un **modo de pruebas** (`LOI_SIN_ENEMIGOS`) que anula el daño de todos los
enemigos sin borrarlos, para poder recorrer y revisar el nivel sin combate. Se
lee de una variable de entorno y no de una constante en el código, para que el
archivo entregado nunca quede con el modo activado.

---

## T6. Reflexión

Lo más difícil no fue la matemática, fue distinguir mis errores de los del
motor. Tres veces di por hecho que algo estaba mal en mi escenario y resultó
ser un defecto del framework: la cámara no seguía al jugador porque
`Camera.set_camera_locks` guarda un `rect` que nunca consulta; el juego
colapsaba al dibujar porque `LightingSystem.render` no recorta los canales de
color a [0, 255]; y los enemigos del roster puntuaban cero porque la lista de
tipos válidos del calificador quedó desactualizada. Aprendí que la forma de
salir de eso es medir: cada vez que escribí una prueba que imprimía números
—el coseno del cono, los píxeles por fotograma de la curva, el matiz durante el
parpadeo— el problema quedó localizado en minutos en lugar de horas.

Lo que mejoraría es el orden de trabajo. Diseñé el mapa con 64 tiles de ancho
dando por buena una resolución interna de 320×224 que el brief mencionaba, y
resultó ser 800×600: el edificio quedaba visible desde el primer fotograma y no
existía una sección de parqueo. Rehacerlo a 120 tiles costó una tarde que me
habría ahorrado leyendo `settings.py` antes que la documentación. También
subestimé el arte: asumí que el tileset provisto alcanzaba, y solo al intentar
poner un carro descubrí que los diez tilesets del repositorio son el mismo
archivo recoloreado con siete tiles planos. Verificar los supuestos contra el
código, y no contra los documentos, habría sido más rápido en los dos casos.

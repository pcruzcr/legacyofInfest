---
assignment_type: stage
assignment_name: "El Patio"
assignment_id: "stage3_3_el_patio"
zone: 3
student_name: "Rebeca"
units_demonstrated: [II, III, IV, V, VI, VII]
evaluation_milestone: "Evaluación Práctica II"
---

# Stage 3-3 — El Patio

## 1. Contexto narrativo

El Patio es un patio interior de la Sede Heredia de la Universidad Invenio, en un piso
alto del edificio: un espacio con muros a los lados, una fuente central, y el horizonte
nocturno de la ciudad visible por encima de los muros. Es la tercera parada de la Zona 3,
dominada por El Gavilán Camionero Mascarero — un halcón enmascarado que ha convertido a
las aves del campus (palomas, halcones, quetzales) en sus cazadores. El jugador atraviesa
el patio esquivando ataques aéreos y obstáculos, mientras la fuente central ofrece un
breve respiro (cura al acercarse).

La estética de la ciudad nocturna usa el mismo tileset (`tileset_gavilan_ciudad`) que la
guarida del jefe de esta zona ("El Bungaló"), para que la Zona 3 se sienta visualmente
coherente entre el escenario de traversal y el enfrentamiento final.

## 2. Conceptos académicos demostrados

### Unidad II — Sistemas de coordenadas y vectores

Archivo: [`fountain.py`](fountain.py)

La fuente central detecta cuándo el jugador está lo bastante cerca para curarse usando
matemática vectorial explícita de `src/engine/utils/math_utils.py`:

- **Distancia euclidiana** (`vec2_distance`), para saber si el jugador está dentro del
  radio de curación (28 px):

  d = sqrt( (p_x - c_x)² + (p_y - c_y)² )

- **Normalización** (`vec2_normalize`), para obtener el vector unitario de dirección
  desde el centro de la fuente hacia el jugador:

  u = v / |v|

- **Producto punto** (`vec2_dot`), para proyectar esa dirección sobre el eje horizontal
  (1, 0) y decidir de qué lado (izquierda/derecha) del jugador aparece el destello de
  curación:

  a · b = a_x·b_x + a_y·b_y

### Unidad III — Curvas

Archivo: [`fountain.py`](fountain.py), usando `CurveTools.catmull_rom`
(`src/framework/processing/curve_tools.py`).

El chorro de agua de la fuente sigue una **spline Catmull-Rom** calculada a partir de 5
puntos de control (en coordenadas relativas al centro de la fuente, en píxeles):

| Punto | Posición (x, y) | Descripción |
|-------|------------------|-------------|
| P0 | (0, 0)     | Boquilla (salida del agua) |
| P1 | (-18, -60) | Sube hacia la izquierda |
| P2 | (0, -84)   | Pico del arco |
| P3 | (18, -60)  | Baja hacia la derecha |
| P4 | (0, 0)     | Vuelve a la boquilla |

`CurveTools.catmull_rom` evalúa 48 puntos intermedios usando la fórmula estándar de
Catmull-Rom (matriz base, por segmento, con t en [0,1]):

P(t) = 0.5 · [ 2·P1 + (-P0+P2)·t + (2P0-5P1+4P2-P3)·t² + (-P0+3P1-3P2+P3)·t³ ]

Seis gotas de agua recorren esa misma curva con fases de tiempo distintas
(`self._t`, desfasado por gota), dando la sensación de un chorro continuo en vez de un
único punto animado.

### Unidad IV — Representación de escena (TMX)

Archivo: [`../../../assets/maps/stage3_3_el_patio/stage3_3_el_patio.tmx`](../../../assets/maps/stage3_3_el_patio/stage3_3_el_patio.tmx)

Mapa de 60×38 tiles (960×608 px — dimensionado para la resolución interna real del motor,
800×600), tileset `tileset_gavilan_ciudad.png` (60 tiles con nombre, sin placeholders,
compartido con el mapa del jefe de la zona), con las 8 capas obligatorias:

| Capa | Contenido |
|------|-----------|
| `BG_Far` | Cielo (vacío, deja ver el parallax real de `background_zone="zone3"`) + horizonte de edificios lejanos y pálidos (`lej_*`) |
| `BG_Mid` | Edificios medios y cercanos (`med_*`, `cer_*`), más altos y con ventanas más brillantes cuanto más cerca |
| `BG_Near` | Vacía (no hay pared de fondo que recortar: el patio es abierto, no un cuarto cerrado) |
| `Terrain` | Piso, muros laterales (el derecho deja un hueco como puerta de salida), 3 plataformas de un solo sentido, 2 jardineras y 2 cajones-obstáculo |
| `Terrain_Detail` | Grietas, manchas, tuberías, luz de piso bajo ventanas/plataformas, lámparas y cuadros contra los muros |
| `Objects` | `PlayerSpawn_01`, `Checkpoint_01`, `NextTrigger_01`, y los enemigos (ver tabla abajo) |
| `Collision` | Piso, muros, jardineras, cajones, 4 plataformas (incluida la de la fuente), y una `HazardZone` |
| `FG_Overlay` | Dos columnas de primer plano (delante del jugador), para profundidad |

El diseño de capas sigue la técnica documentada por el equipo para esta estética: la
profundidad se logra con el arte y el orden de dibujado (no hay parallax real entre
capas de tiles — eso es código muerto en `camera.py`), y el horizonte de la ciudad se
apoya sobre la línea de las copas de los muros en vez de recortarse en una ventana,
porque a diferencia del cuarto del jefe, El Patio no tiene pared de fondo.

**Enemigos** (roster oficial de Zona 3, `docs/18_ENEMY_ROSTER.md`):

| Objeto TMX (`type`) | Nombre narrativo | Cantidad | Notas |
|---|---|---|---|
| `Walker` | WalkerPalom | 3 | Patrulla el piso, `patrol_speed=30`, `alert_speed=55` |
| `Flying` | FlyingHalcon | 5 | Vuelo `sine`, con picado en alerta (ya incluido en `EnemyFlying`) |
| `Shooter` | ShooterQuetzal | 3 | Estacionarios, en las ventanas de los muros, `fire_rate=0.8` |

Todos con la propiedad `zone=3` para cargar los sprites de zona correctos automáticamente.

### Unidad V — Color

Archivo: [`fountain.py`](fountain.py), usando `ColorTools.apply_tint`
(`src/framework/processing/color_tools.py`).

El sprite de la fuente (`assets/sprites/shared/fountain_anim.png`) se tiñe con un tono
dorado (255, 214, 140) para simular la luz de tarde descrita en `docs/16_WORLD_DESIGN.md`
para la Zona 3. La operación multiplica cada canal de color del sprite original por el
canal correspondiente del tinte, normalizado a 255:

out_R = clamp(orig_R · tinte_R / 255, 0, 255)
out_G = clamp(orig_G · tinte_G / 255, 0, 255)
out_B = clamp(orig_B · tinte_B / 255, 0, 255)

Se aplica una sola vez, al cargar los 6 cuadros de animación, no en cada frame de juego.

### Unidad VI — Animación con easing + interacción propia de EventBus

Archivos: [`moneda_fx.py`](moneda_fx.py), [`stage3_3_el_patio.py`](stage3_3_el_patio.py),
usando `ease_out_elastic` de `src/engine/utils/math_utils.py`.

Cuando se recoge una moneda, el motor emite el evento del framework
`EVENTO_RECOGIDO` (`src/framework/stage/interactable_system.py`) con
`item_id`, `cantidad` y `pos` (dónde ocurrió). `MonedaFxController` se
suscribe a ese evento en `on_stage_start()` — es la interacción propia: nadie
más en el motor sabe que "El Patio" reacciona a que agarren monedas — y por
cada una crea un `MonedaSparkle` en esa posición exacta.

El destello no crece de forma lineal: su radio en el instante `t` (0 a 1
sobre 0.5 s) sigue `ease_out_elastic(t)`, que **se pasa de 1 y vuelve**, dando
el efecto de "rebote" en vez de un crecimiento uniforme:

```
radio(t) = RADIO_MAX · ease_out_elastic(t)
alpha(t) = 255 · (1 − t)
```

### Unidad VII — Filtros (histograma + convolución)

Archivo: [`fountain.py`](fountain.py), usando `FilterTools.compute_histogram`,
`FilterTools.adjust_brightness` y `FilterTools.gaussian_blur`
(`src/framework/processing/filter_tools.py`).

**Histograma dirigiendo una decisión:** antes de teñir el sprite de la
fuente, se calcula su histograma de luminancia y se promedia:

brillo_medio = Σ (i · cantidad_de_píxeles_con_luminancia_i) / total_píxeles, para i en [0, 255]

Si `brillo_medio < 140`, el sprite se aclara con `adjust_brightness(1.35)`
**antes** de aplicar el tinte dorado — el histograma decide si hace falta el
paso extra, no un número puesto a ojo.

**Convolución (desenfoque gaussiano):** el aura de luz detrás de la fuente
sale de desenfocar un círculo blanco sólido con `gaussian_blur(sigma=6.0)`.
El resultado es un degradado de brillo del centro hacia afuera; ese mismo
degradado (0 a 255) se reutiliza directamente como canal alfa de la textura
final, así el halo se funde con el fondo en vez de recortarse como un
cuadrado.

## 3. Cómo ejecutar

```bash
.venv\Scripts\activate
python main.py --stage stage3_3_el_patio
```

Controles: A/D moverse, W saltar, S agacharse (según `docs/04_PLAYER_SPEC.md`).
Verificado sin errores de consola durante la carga y el recorrido del nivel.

## 4. Checkpoints

| ID | X | Y |
|----|---|---|
| 0 | 320 | 576 |
| 1 | 816 | 576 |
| 2 | 1264 | 576 |

## 4b. Coleccionables

6 objetos `Pickup` (`Moneda_01`..`Moneda_06`) — repartidos por el piso y tres
de ellos sobre la escalera de nubes (premian tomar la ruta de plataformeo).

## 4c. Migración al motor actualizado (2026-08-26)

El profesor publicó una versión nueva del motor en GitHub
(`github.com/pcruzcr/legacyofInfest`, rama `dev`). Se migró el trabajo de esta
carpeta a esa base siguiendo la regla de alcance: **solo se tocaron los
archivos de `stage3_3_el_patio`**, nada del motor ni de otras entregas. El
historial local resultó ser ancestro directo de `origin/dev` — sin conflictos
de fondo. Se instaló la dependencia opcional `moderngl`, requerida por el
análisis de diseño del calificador (el juego ya funcionaba sin ella).

## 4d. Rediseño con desplazamiento horizontal y ascenso obligatorio (2026-08-26)

El mapa pasó de 960 a **1600 px de ancho** (100 tiles) para que el
desplazamiento horizontal de cámara se note de verdad — con 960 px casi no
había margen de scroll (el viewport ya mide 800 px). El fondo cambió a una
ambientación diurna de campus, propia (cielo, nubes, árboles, edificio),
inspirada en una referencia pero no copiada, cargada vía
`background_zone="stage3_3_el_patio"` desde `assets/backgrounds/stage3_3_el_patio/`.

Se agregó una **zona de ascenso obligatorio** (`docs` del proyecto no tienen
un objeto tipo "Escalera" real — trepar requeriría tocar `player.py`, fuera
de alcance — así que el mismo efecto se logra con la técnica estándar de
plataformas): `Solid_MuroBloqueo` (96×128 px, más alto que el salto máximo
del jugador, ~87 px) corta el piso por completo entre las columnas 36-41; se
sortea subiendo por 3 `Platform_NubeSub0{1,2,3}` (nube) y bajando por 2
`Platform_NubeBaj0{1,2}` al otro lado. Verificado con la función de
alcanzabilidad real del motor (`level_metrics.reachable_platforms`, con
`collision_rects` + `one_way_rects` juntos): **17 de 19 rectángulos
alcanzables desde el spawn** — los 2 no alcanzables son los muros de cierre
del mapa (correcto, no son plataformas).

**Aviso conocido del calificador automático:** `grade_stage.py` bajó a 1/10
en "geometría" porque su análisis de plataformas huérfanas solo mira
`collision_rects` (sólidos) y no ve las plataformas de un solo sentido —
así que no puede ver el camino de la escalera de nubes, aunque exista y esté
verificado arriba con la física real. El puntaje total con este rediseño:
**118/130 (90.8%)**.

## 5. Obstáculos y plataformeo

| Objeto | Tipo | Notas |
|---|---|---|
| `Solid_MuroBloqueo` | Sólido (96×128 px) | Corta el piso; obliga a subir por las nubes |
| `Platform_NubeSub01/02/03` | Un solo sentido | Escalera subiendo, ~48 px de salto cada una |
| `Platform_NubeBaj01/02` | Un solo sentido | Escalera bajando, del otro lado del muro |
| `Solid_Roca01/02/03` | Sólido (16 px), roca | Obstáculos de piso — hay que saltarlos |
| `Solid_CajonMadera01/02/03` | Sólido (16 px), madera | Roca02+Madera02 están pegados: salto más exigente |
| `HazardZone_01` | Daño 0.25 | Zona de peligro en el tramo final del recorrido |
| `Solid_Planter01/02` | Sólido (32 px) | Jardineras — también sirven de cobertura contra las aves |
| `Platform_Fountain` | Un solo sentido | Plataforma de piedra de la fuente, en el centro del nivel |

## 6. Notas de lógica personalizada

La fuente (`Fountain`, en `fountain.py`) no es un enemigo ni un objeto del registro de
tipos del TMX: se instancia manualmente en `on_stage_start()` de
`stage3_3_el_patio.py`, en la posición `FOUNTAIN_POS = (816, 544)`, que coincide con el
centro del objeto `Platform_Fountain` de la capa `Collision`. Cura 0.25 corazones al
jugador si se mantiene a menos de 28 px del centro, con un cooldown de 6 segundos.

## 7. Reflexión

_(a completar por la estudiante: ¿qué fue lo más difícil de armar el escenario? ¿qué
mejorarías?)_

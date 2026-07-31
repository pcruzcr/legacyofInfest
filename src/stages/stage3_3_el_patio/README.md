---
assignment_type: stage
assignment_name: "El Patio"
assignment_id: "stage3_3_el_patio"
zone: 3
student_name: "Rebeca"
units_demonstrated: [II, III, IV, V]
evaluation_milestone: "Evaluación Práctica I"
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
| 0 | 448 | 576 |

## 5. Obstáculos y plataformeo

| Objeto | Tipo | Notas |
|---|---|---|
| `Platform_Step1/2/3` | Un solo sentido | Alturas distintas, para variar el salto entre el spawn y la salida |
| `Solid_Cajon01/02` | Sólido (16 px) | Hay que saltarlos, están a ras de piso |
| `HazardZone_01` | Daño 0.25 | Zona de peligro en el tramo medio del recorrido |
| `Solid_Planter01/02` | Sólido (32 px) | Jardineras — también sirven de cobertura contra las aves |

## 6. Notas de lógica personalizada

La fuente (`Fountain`, en `fountain.py`) no es un enemigo ni un objeto del registro de
tipos del TMX: se instancia manualmente en `on_stage_start()` de
`stage3_3_el_patio.py`, en la posición `FOUNTAIN_POS = (496, 544)`, que coincide con el
centro del objeto `Platform_Fountain` de la capa `Collision`. Cura 0.25 corazones al
jugador si se mantiene a menos de 28 px del centro, con un cooldown de 6 segundos.

## 7. Reflexión

_(a completar por la estudiante: ¿qué fue lo más difícil de armar el escenario? ¿qué
mejorarías?)_

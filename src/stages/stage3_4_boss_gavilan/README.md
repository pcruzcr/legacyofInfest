# Boss Battle Design — Student Worksheet

**Student Name:** Isaac Felipe Morún Moreira
**Boss Name:** El Gavilán Camionero Mascarero

---

## 1. Boss Concept (3–5 sentences)

Describe your boss's appearance, personality, and role in the game world.

Aún por definir, pero la idea es que sea un gavilán con una máscara ceremonial de colores, muy protector, que solo ataca si te ve cerca de su huevo.

## 2. Attack Patterns

*(Práctica I: sin ataques todavía — solo movimiento de Fase 1. Se completa en Práctica II/III.)*

| Attack Name | Type | Damage | Cooldown | Description |
| ----------- | ---- | ------ | -------- | ----------- |
| — | — | — | — | Pendiente para Práctica II |

## 3. Phase Transitions

| Phase | HP % | New Behaviour |
| ----- | ---- | -------------- |
| 1 | 100–0 (única fase implementada) | Lazo de planeo curvo alrededor del punto de aparición |
| 2 | Pendiente | Práctica II |
| 3 | Pendiente | Práctica III |

## 4. Visual / Audio Design

Se mueve rápido para hacer embestidas y golpear con sus plumas cortantes de colores brillantes, acompañado de un grito fuerte, como el de un camión.

## 5. Matemática Aplicada (requerido por la Evaluación Práctica I)

### 5.1 Transformación geométrica / sistema de coordenadas — colocación de los puntos de control

**Fórmula usada** (`boss_gavilan.py`, método `_build_orbit_path`):

```
para k = 0..7:
    ángulo_k = 2π · k / 8
    radio_k  = 80 px si k es par, 58 px si k es impar
    P_k = ( centro.x + cos(ángulo_k) · radio_k ,
            centro.y + sin(ángulo_k) · radio_k )
```

Con `centro` = la posición exacta donde aparece el jefe en el mapa
(`BossSpawn_01` = (824, 336)), **no** el origen del mundo. Los 8 puntos se
reparten en ángulos iguales y se alterna el radio entre 80 y 58 px para que el
recorrido no sea una circunferencia perfecta.

Cuando lo probé sin sumarle la posición del centro (`BossSpawn_01`), el jefe
orbitaba alrededor de la esquina superior izquierda (0,0) del mapa en vez de su
arena. Entender que había que trasladar esas coordenadas trigonométricas al
punto exacto donde lo puse en Tiled fue lo que corrigió la órbita para que
quedara sobre la zona de combate.

### 5.2 Vectores explícitos — orientación hacia el jugador

**Fórmula usada** (`boss_gavilan.py`, método `_face_player`, con `math_utils.py`):

```
distancia = vec2_distance(posición_jefe, posición_jugador)
dirección = vec2_normalize(posición_jugador - posición_jefe)
facing_direction = +1 si dirección.x ≥ 0, sino -1
```

Normalizar un vector reduce su longitud a 1 sin cambiar su dirección, así que
`dirección.x` solo me dice si el jugador está a la izquierda (-1) o a la derecha
(+1), sin importar qué tan lejos esté. Al probar la lógica con el jugador parado
justo encima del jefe, noté que la distancia daba 0 — validar ese caso evita
dividir por cero y que el juego colapse, y logra una orientación estable incluso
en esa posición límite.

### 5.3 Curva básica — `CurveTools` (Catmull-Rom)

**Dónde:** `boss_gavilan.py`, métodos `_build_orbit_path` y `_update_orbit`. La
Fase 1 del jefe **no** se mueve con una circunferencia de `cos/sin`: recorre una
curva calculada con `CurveTools`.

**Fórmulas usadas:**

```
# una sola vez, al construir el jefe:
lazo = [P_0, P_1, ... P_7, P_0]          # se repite P_0 para cerrar el lazo
camino = CurveTools.catmull_rom(lazo, n_samples = 160)

# en cada frame:
t = (t + dt / segundos_por_vuelta) mod 1.0
posición = CurveTools.sample_path(camino, t)

segundos_por_vuelta = 2π / velocidad_angular = 2π / 0.6 ≈ 10.47 s
```

Catmull-Rom interpola una curva suave que **pasa exactamente por cada punto de
control**. Elegí esta y no una Bézier a propósito: la Bézier trata los puntos
intermedios como imanes que atraen la curva sin tocarla, así que el radio real
del recorrido habría quedado por debajo de los 80 px que documenta la spec.
Catmull-Rom sí pasa por cada punto.

Lo comprobé midiendo la curva ya muestreada: el radio recorrido va de 58 a
**exactamente 80 px**, o sea que la interpolación no se pasa de los puntos de
control y el jefe nunca sale de la zona despejada que le dejé en el mapa.
También medí el salto de posición entre frames al cerrar la vuelta (`mod 1.0`):
0,84 px como máximo, así que el lazo empalma sin tirón visible.

El parámetro `t` es una fracción del recorrido (0 a 1), no un ángulo. Es la
diferencia de fondo con la versión anterior: antes avanzaba un ángulo y la
trigonometría decidía la posición; ahora avanzo por la curva y la curva decide.

**Secundario:** dos de los halcones tutorial (`Flying_02` y `Flying_03` en el
TMX) usan `flight_mode = bezier`, que internamente también llama a
`CurveTools.build_bezier_path()` en `flight_strategies.py`. A diferencia del modo
`sine`, que genera un zigzag rígido, el modo `bezier` interpola una trayectoria
suave entre waypoints con Catmull-Rom.

> Nota de corrección: estos dos halcones tenían `flight_mode = "beizer"` mal
> escrito. `make_strategy()` cae a `SineFlight` ante un modo desconocido **sin
> avisar** (está documentado como AUD-047 en `flight_strategies.py`), así que
> volaban en seno y la curva no ocurría. Corregido a `bezier`.

### 5.4 Representación gráfica — capas y Z-order

El `.tmx` ordena las capas de tiles de atrás hacia adelante: `BG_Far`, `BG_Mid`,
`BG_Near`, `Terrain`, `Terrain_Detail` y `FG_Overlay`. Ese Z-order controla qué
se dibuja encima de qué: los fondos (`BG_*`) quedan siempre detrás, el terreno y
sus detalles en el medio, y `FG_Overlay` delante de todas las demás capas de
tiles. `Objects`, `Design_Notes` y `Collision` no se dibujan en pantalla (son
datos de spawn, notas de diseño y física), por eso su posición en el orden no
afecta lo que se ve.

**Hay dos sistemas de fondo distintos y solo uno tiene parallax.** Al principio
creí que el motor aplicaba parallax a las capas de tiles `BG_*` según su nombre,
porque `camera.py` define `layer_offset()` y `parallax_factor()` con los factores
0.15 / 0.40 / 0.70. Al buscar quién los llama, resulta que **nadie**: son código
muerto. El parallax real está en `_draw_background()` de `drawing_system.py`, se
aplica a las tres **imágenes** de `assets/backgrounds/zone3/` y usa otros
factores, `(0.15, 0.35, 0.6, 0.8)`. Además el tilemap entero se dibuja en una
sola pasada de pyscroll con un único centro (`_draw_stage_layers`), así que por
construcción no puede tener parallax por capa: `BG_Far`, `BG_Mid` y `BG_Near` se
mueven 1:1 con `Terrain`.

Por eso la profundidad de este nivel se consigue **con el arte, no con el
movimiento**, y las tres capas `BG_*` se reparten por orden de dibujado: cielo y
horizonte lejano al fondo, torres medias y cercanas después, y en `BG_Near` la
pared interior del cuarto con los huecos de ventana recortados — por esos huecos
se ve la ciudad de las capas de atrás. Los tiles lejanos son pálidos y casi del
color de la bruma, y los cercanos oscuros con las ventanas más brillantes: como
se mira hacia abajo desde un piso alto, la profundidad crece hacia abajo.

Algo que asumí mal al principio: creía que `FG_Overlay`, por ir al final, taparía
también al jugador y a los enemigos. Al revisar `drawing_system.py` vi que no es
así — `_draw_stage_layers()` dibuja todo el tilemap de una sola pasada y
`_draw_entities()` corre después, así que las entidades siempre quedan encima de
todas las capas de tiles, incluida `FG_Overlay`. Es decir, en este motor
`FG_Overlay` está al frente del escenario pero no de los personajes; para lograr
que algo tape al jugador habría que dibujarlo como entidad, no como capa.

### 5.5 Objetos base obligatorios del TMX

| Objeto | Class | Posición | Para qué |
| --- | --- | --- | --- |
| `PlayerSpawn_01` | `PlayerSpawn` | (24, 574) | dónde aparece y reaparece el jugador |
| `NextTrigger_01` | `NextTrigger` | (672, 192) 304×16 | salida del nivel, en el techo de la arena |
| `Checkpoint_SalaJefe` | `Checkpoint` | (624, 544) | justo antes de la boca de la arena del jefe |
| `Checkpoint_AntesAbismo` | `Checkpoint` | (1040, 544) | justo antes del abismo (empieza en x=1088) |
| `DeathPit` | `DeathPit` | (1088, 582) 464×26 | el abismo mortal |

Los dos `Checkpoint` llevan la propiedad `checkpoint_id` (1 y 2). Es obligatoria:
`_handle_checkpoint()` lanza `FrameworkUsageError` si falta.

> Nota de corrección: el `DeathPit` estaba en la capa `Collision`, pero
> `_process_objects()` solo recorre la capa `Objects`, así que nunca llegaba a
> `stage.death_pits` y el abismo no mataba. Y como `_load_collision()` convierte
> todo objeto de `Collision` en rectángulo sólido sin mirar su Class, el abismo
> se cargaba además como suelo invisible por el que se podía cruzar caminando.
> Movido a `Objects`.

## 6. Reflection (2–3 sentences)

What was the most challenging aspect of designing this boss? What would you improve?
Aún por definir — de momento, lo más difícil fue lograr que el jefe orbitara dentro de los límites de su propia arena y no se saliera hacia otras zonas del mapa.

---



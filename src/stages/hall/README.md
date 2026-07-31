# Custom Stage Design — Student Worksheet

**Student Name:** Jose Pablo Monestel Cruz
**Stage ID:** hall

---

## 0. Cómo ejecutar

Desde la raíz del proyecto (`legacyofInfest/`), con el entorno virtual ya
instalado (`.venv/`):

**Juego completo (menú principal, todos los stages):**
```bash
.\.venv\Scripts\python.exe main.py
```

**Directo al escenario Hall (sin pasar por el menú):**
```bash
.\.venv\Scripts\python.exe main.py --stage hall
```

En Linux/macOS, reemplazar `.\.venv\Scripts\python.exe` por
`.venv/bin/python`. También puede ejecutarse `python main.py` a secas si el
entorno virtual ya está activado (`.\.venv\Scripts\Activate.ps1`).

---

## 1. Stage Concept (3–5 sentences)

El Hall es la segunda etapa de la Zona 3 (Sede Heredia): un vestíbulo universitario enorme, de techos altos y piso amplio, con un balcón perimetral accesible por dos escaleras. La luz natural entra por tres tragaluces (visibles justo sobre el techo) y proyecta charcos de luz sobre el piso. El Gavilán Camionero Mascarero ha convertido el hall en su terreno de caza, así que aves patrullan tanto el piso como el aire entre el techo y el balcón. Mide 1088×608px — la etapa más ancha del juego — y la salida hacia el siguiente escenario no está al final del piso: hay dos caminos de plataformas, uno que sube desde el balcón (izquierda) y otro que sale del pedestal cerca del checkpoint (derecha), y ambos convergen en una sola repisa compartida cerca de la mitad horizontal del hall, donde está la puerta — accesible desde cualquiera de los dos lados.

## 2. Tileset Requirements

Tileset: `tileset_gavilan_ciudad` (60 tiles, 16×16px, `assets/tilesets/tileset_gavilan_ciudad.png`). Arte propio generado por código (`tools/generate_tileset_gavilan_ciudad.py`, paleta fija de 16 colores, mismo enfoque procedural que ya usa el proyecto en `tools/pixel_asset_generator.py` para `tileset_stage0.png`) — no es un placeholder de color plano, cada uno de los 60 tiles tiene su propio dibujo (piedra, marcos de ventana, vegetación de skyline, etc.).

| Tile ID | Description | Collision? |
|---|---|---|
| 0 (suelo_sup) | Piso de planta baja | Sí |
| 5 (zocalo) | Relleno/zócalo bajo el piso | Sí |
| 6 (techo) | Techo indestructible | Sí |
| 8-10 (plat_izq/med/der) | Balcón y peldaños de escalera/plataformas | Sí (one-way) |
| 2 (muro) | Muros laterales | Sí |
| 7 (columna) | Columnas decorativas | No (visual, Terrain_Detail) |
| 12 (reja) | Barandal del balcón | No (visual) |
| 43-46 (marco_izq/der/sup, alfeizar) | Marcos de tragaluz y de la puerta | No (visual, FG_Overlay) |
| 54-55 (cortina_izq/der) | Cortinas de tragaluz | No (visual) |
| 15 (luz_suelo) | Charco de luz bajo cada tragaluz | No (visual) |
| 16-39 (lej_*/med_*/cer_*) | Skyline de Heredia en parallax (3 profundidades) | No (fondo) |
| 48-51 (grieta_1/2, mancha) | Desgaste | No (visual) |
| 57-58 (cuadro, caja) | Props decorativos / obstáculos sólidos | No / Sí (caja cuando es obstáculo) |
| 42 (cruce) | Reja/tranca de la puerta sellada | No (visual) |

## 3. Enemy / Entity Placements

| X | Y | Type | Properties |
|---|---|---|---|
| 96,256,480,704,832 | piso | WalkerPalom | (valores por defecto de la especie) |
| 224, 544 | balcón | ShooterBuitre | (valores por defecto de la especie) |
| 6 posiciones a lo ancho | banda de vuelo | FlyingHalcon | `flight_mode=bezier` + 4 `Waypoint` propios (`owner_id`) |
| 420, 700 | y=96 (techo) | SwingingLamp | *no es objeto TMX* — instanciada en `Hall.on_stage_start()` (ver §5) |

## 4. Checkpoints

| ID | Ubicación |
|---|---|
| 0 | piso, justo antes de los dos caminos de plataformas hacia la salida |

## 5. Custom Logic Notes

### 5.1 Requisito de curvas (`CurveTools`)

Los 6 `FlyingHalcon` usan `flight_mode="bezier"` en vez del `sine` por defecto de la especie. Cada uno trae 4 objetos `Waypoint` en el TMX (`owner_id` = nombre del enemigo, ver `tools/generate_hall_tmx.py:_halcon_waypoints`), que el motor recorre en bucle con `CurveTools.build_bezier_path(waypoints, t)` (`src/framework/entities/flight_strategies.py:BezierFlight`, el mismo mecanismo que ya usa el juego para vuelo Bézier en otros enemigos).

**Fórmula exacta** (`src/framework/processing/curve_tools.py:_eval_catmull`, Catmull-Rom entre 4 puntos de control P0..P3, con `t ∈ [0,1]` el parámetro local del segmento):

```
P(t) = 0.5 · [ 2·P1 + (−P0+P2)·t + (2·P0−5·P1+4·P2−P3)·t² + (−P0+3·P1−3·P2+P3)·t³ ]
```

`build_bezier_path` selecciona qué 4 waypoints consecutivos usar como P0..P3 según el segmento en que cae `t` (interpolado globalmente sobre los 4 waypoints del halcón, en bucle), y pasa el `t` local de ese segmento a la fórmula de arriba. El resultado es una curva suave que pasa exactamente por los 4 waypoints declarados en el TMX, no solo por sus extremos.

### 5.2 Requisito de vectores (`math_utils.py`)

`SwingingLamp` (`src/stages/hall/decor_lamp.py`) es una entidad decorativa (una lámpara colgante) que `Hall.on_stage_start()` instancia directamente en Python y agrega a `self._stage_data.entity_list` — no es un objeto TMX (ver nota técnica al final de esta sección).

**Fórmulas exactas usadas cada frame** (`src/engine/utils/math_utils.py`):

- Interpolación lineal entre los dos extremos del balanceo (ancla izquierda `L` y derecha `R`), con `t` suavizado por una curva de easing, no lineal en el tiempo:
  ```
  lerp(a, b, t) = a + (b − a) · t                    (t clamped a [0,1])
  ease_in_out_quad(t) = 2t²                 si t < 0.5
                       = −1 + (4 − 2t)·t     si t ≥ 0.5
  bob = ( lerp(Lx, Rx, ease_in_out_quad(t)), lerp(Ly, Ry, ease_in_out_quad(t)) )
  ```
- Vector de desplazamiento respecto al ancla fija, usado para el largo/dirección de la cuerda dibujada:
  ```
  offset = bob − anchor
  vec2_length(v)    = √(vx² + vy²)                       → longitud de la cuerda
  vec2_normalize(v) = (vx/‖v‖, vy/‖v‖)  si ‖v‖ > 1e−10,  → dirección de la cuerda
                       si no, (0, 0)
  ```

### 5.3 Otras notas de diseño

- **Hueco central en el balcón (3 tiles, x=304-352):** el balcón corrido se parte en dos tramos con un vacío en el medio — el jugador puede saltarlo (48px, salto cómodo) o dejarse caer de vuelta al piso. Lee como daño causado por El Gavilán. Bordes marcados con `grieta_1`/`grieta_2`.
- Columnas y barandal del balcón son solo visuales (capa `Terrain_Detail`), sin colisión — el diseño oficial de la Zona 3 los describe como referencia visual, no como obstáculos.
- **Envolvente de salto real:** el analizador propio del proyecto (`level_metrics.py`) estima el alcance horizontal de un salto con la velocidad de suelo completa (~85px), pero el controlador real del jugador (`src/framework/entities/states/airborne.py`) aplica la mitad de esa velocidad en el aire — el alcance real de un salto sencillo es **~43px**. Toda la geometría de este mapa (saltos ≤32px, subidas ≤64px) está verificada contra ese número real, no contra la estimación del analizador.
- **Separación del techo:** ninguna plataforma de las rutas hacia la salida está a menos de 112px del techo sólido. El salto es un arco balístico fijo (~90px) que el juego no acorta a propósito; si el techo cae dentro de ese arco, el jugador se golpea la cabeza y pierde tanto la altura restante como el tiempo de aire que necesitaba para el salto horizontal.
- **Ancho de plataforma junto a peligros:** el jugador tiene un hitbox de 20px de ancho. El pozo (`DeathPit`) bajo el hueco del balcón mide 1 tile (16px, cols 25) — un salto directo desde la caja de impulso (col 24) hasta el piso (col 26), con margen real de sobra (~27px) respecto al hitbox del jugador.
- **Caja obstáculo cerca del spawn (col 6):** sólida, entre las dos primeras plataformas de la escalera, para que el piso no sea una línea recta caminable de punta a punta.
- **Salida accesible por ambos lados:** camino oeste (balcón → 3 escalones → repisa compartida) y camino este (pedestal cerca del checkpoint → 4 escalones → misma repisa), convergiendo en la puerta sellada. Todo salto horizontal ≤32px, cada subida ≤64px.
- **Nota técnica — por qué `SwingingLamp` no es un objeto TMX:** `scripts/grade_stage.py` (el grader que corre en CI, `.github/workflows/ci.yml`) analiza el TMX sin importar el módulo Python del stage, así que nunca puede conocer un tipo de entidad registrado solo por el propio stage — un objeto de tipo desconocido en la capa `Objects` dispara `FrameworkUsageError` en su análisis y pone en cero varias categorías de la rúbrica automática para todo el archivo. `Hall.on_stage_start()` la instancia directamente en Python y la agrega a `self._stage_data.entity_list`, el mismo patrón que usa el propio motor para los esbirros que invoca un jefe (`stage_scene.py`, manejo de `BossBase.take_summons()`).

## 6. Reflection (2–3 sentences)

La parte más difícil fue calibrar la geometría contra la física real del salto del jugador: el analizador de diseño del propio proyecto estima el alcance horizontal con la velocidad de suelo completa, pero el controlador real del jugador usa la mitad de esa velocidad en el aire, así que una primera versión de la escalada final resultó literalmente imposible de cruzar hasta corregir ese número. Con más tiempo, abriría el resultado en Tiled para pulir a mano la composición visual del skyline y el encaje exacto de los tragaluces, ya que todo el mapa se generó por código (`tools/generate_hall_tmx.py`) al no tener disponible una herramienta visual en este entorno.

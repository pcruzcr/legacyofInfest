---
document_id: "LOI-DEMO-015"
title: "Legacy of InFest — Escenas de demostración académica"
aliases: ["Escenas de demostración académica", "Academic Demo Scenes"]
tags: ["demo", "laboratorio", "academico", "interactivo"]
description: "10 escenas interactivas de demo/laboratorio"
source: "docs/15_ACADEMIC_DEMO_SCENES.md"
date_processed: "2026-08-13"
---

# Legacy of InFest — Escenas de demostración académica

**ID del documento:** LOI-DEMO-015
**Versión:** 1.4.0
**Estado:** Oficial
**Compatibilidad:** Requiere `03_ARCHITECTURE.md`, `11_FILTER_TOOLS_SPEC.md`, `12_VISION_TOOLS_SPEC.md`, `13_PATTERN_RECOGNITION_SPEC.md`, `09_HUD_SPEC.md`, `07_STAGE0_DESIGN.md`
**Audiencia:** Profesor, ayudantes de cátedra, asistentes de programación con IA

> **AUD-455.** Traduce el documento completo. Corrige la ruta de los
> ficheros de escena, que carecía del prefijo `src/` en todo el documento
> (es `src/engine/scenes/`, verificado — los 10 ficheros de escena y los 5
> módulos utilitarios existen ahí); la numeración rota de §13 (`### 13.1`
> seguido de `### 6.2`/`### 6.3` en vez de `### 13.2`/`### 13.3`); y la
> referencia a `STUDENT_ASSETS_DIR` en §5.10 y §15.3, una constante que no
> existe en `src/engine/core/settings.py` (la única constante de plantillas
> de estudiante ahí es `STUDENT_TEMPLATES_DIR` — ver `22_API_CONTRACTS.md`
> §2.1).

---

## 1. Visión general

Las Escenas de Demostración Académica son diez escenas interactivas construidas por el profesorado — 7 laboratorios de teoría (Unidades II–VI/VIII) más 3 demos avanzadas (Unidades VII–IX) — que funcionan como **laboratorios vivos** dentro del framework de Legacy of InFest. Se accede a ellas desde el menú principal de la Pantalla de Título, en un submenú dedicado **"Demos Académicas"**.

A diferencia de Stage 0, que demuestra sistemas de jugabilidad, las Escenas de Demostración Académica demuestran **operaciones de procesamiento de imágenes y aprendizaje automático** directamente sobre superficies del juego. Cada escena es completamente interactiva: los estudiantes ajustan parámetros con controles de teclado y observan los resultados en tiempo real. Los valores de salida se muestran en pantalla para reforzar la conexión matemática entre parámetro y efecto.

Estas escenas son **propiedad del profesorado y las mantiene el profesorado**. Los estudiantes no las modifican. Las usan como:

1. Una referencia para entender qué produce cada función del framework.
2. Una herramienta de calibración para elegir parámetros antes de aplicarlos en sus propios escenarios.
3. Un entorno de evaluación donde se realizan parcialmente los Exámenes Prácticos II y III.

---

## 2. Arquitectura de escena

### 2.1 Integración con el framework

Las Escenas Demo son subclases estándar de `BaseScene`. Siguen todas las reglas del ciclo de vida de escena definidas en `03_ARCHITECTURE.md`.

```
TitleScene
    ↓ (menú: Demos Académicas)
DemoMenuScene              ← Selector de las diez escenas demo/laboratorio (Unidades II–IX)
    ↓      ↓         ↓           ↓            ↓
Vector   Transform  Curve       Interpolate  Color
(II)     (II/III)   (III)       (III/IV)     (V)
    ↓      ↓         ↓           ↓            ↓
Noise    Collision  Filter      Vision       Pattern
(V/VIII) (VI)       (VII)       (VIII)       (IX)
    ↓ (ESC)
DemoMenuScene
```

### 2.2 Ubicación de ficheros

```
src/engine/
└── scenes/
    ├── demo_menu_scene.py              ← Selector de las 10 escenas
    ├── vector_lab_scene.py             ← Unidad II  (Vectores)
    ├── transform_lab_scene.py          ← Unidad II/III (Transformaciones 2D)
    ├── curve_editor_scene.py           ← Unidad III (Bézier, splines)
    ├── interpolation_lab_scene.py      ← Unidad III/IV (Interpolación y easing)
    ├── color_theory_scene.py           ← Unidad V (Espacios de color)
    ├── noise_lab_scene.py              ← Unidad V/VIII (Ruido y procedural)
    ├── collision_lab_scene.py          ← Unidad VI (Colisión AABB)
    ├── filter_demo_scene.py            ← Unidad VII
    ├── vision_demo_scene.py            ← Unidad VIII
    └── pattern_demo_scene.py           ← Unidad IX
```

Módulos utilitarios (compartidos por todas las escenas):
```
src/engine/scenes/
    ├── demo_layout.py                  ← Constantes de layout y funciones de dibujo auxiliares
    ├── demo_utils.py                   ← SourceSurfaceManager, FrameThrottle, ErrorDisplay, save_png
    ├── demo_common.py                  ← Re-exportaciones heredadas de demo_layout + demo_utils
    ├── scene_registry.py               ← Contenedor de DI: patrón register → build
    ├── param_panel.py                  ← Widget ParamPanel reutilizable
    └── debug_overlay.py                ← Consola de depuración F11 (de toda la app, no específica de escena)
```

Todos los ficheros de escena demo/laboratorio están en `src/engine/scenes/`. Son propiedad del profesorado. Los estudiantes no los modifican.

### 2.3 Layout compartido de las escenas demo

Las tres escenas de demostración académica (Filter, Vision, Pattern) comparten una estructura de layout común.
Los siete laboratorios de teoría (Unidades II–VI/VIII) usan layouts más simples adaptados a cada tema.
Hay una referencia de layout compartida disponible para las tres demos académicas:

```
┌──────────────────────────────────────────────────────────────────┐ Y=0
│  [SCENE TITLE]                              [UNIT: VII/VIII/IX]  │ Y=2
│  [Current Mode Name]                        [ESC: Back to Menu]  │ Y=12
├──────────────────────────────────────────────────────────────────┤ Y=22
│                                                                  │
│   [LEFT PANEL — 160×180]        [RIGHT PANEL — 160×180]         │ Y=22
│   Source / Input Surface        Result / Output Surface          │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤ Y=202
│  [PARAMETER DISPLAY — 320×12]                                    │
│  Param: name = value  |  Param: name = value  |  [TAB: switch]  │
└──────────────────────────────────────────────────────────────────┘ Y=224
```

| Región | Dimensiones | Contenido |
|---|---|---|
| Barra superior | 320×22 px | Título de escena, etiqueta de unidad, indicación de navegación |
| Panel izquierdo | 160×180 px | Superficie de entrada (fuente, estado previo) |
| Panel derecho | 160×180 px | Superficie de salida (resultado, estado posterior) |
| Línea divisoria | 1 px vertical en X=160 | Separación visual |
| Barra inferior | 320×22 px | Nombre del parámetro actual, valor, controles |

### 2.4 Controles compartidos

| Tecla | Acción |
|---|---|
| `TAB` | Cicla al siguiente modo de operación dentro de la escena |
| `IZQUIERDA` / `DERECHA` | Disminuye / aumenta el parámetro principal |
| `ARRIBA` / `ABAJO` | Disminuye / aumenta el parámetro secundario (si aplica) |
| `ESPACIO` | Alterna entre las opciones de superficie fuente |
| `F` | Congela/descongela la superficie fuente (captura el fotograma actual) |
| `S` | Guarda la superficie de salida actual en `tests/output/demo/` como PNG |
| `R` | Reinicia todos los parámetros a sus valores por defecto |
| `ESC` | Vuelve a DemoMenuScene |

### 2.5 Opciones de superficie fuente

Las tres escenas de demostración académica (Filter, Vision, Pattern) comparten el mismo conjunto de superficies fuente. `ESPACIO` cicla entre estas opciones:

| Índice | Fuente | Descripción |
|---|---|---|
| 0 | `assets/sprites/player/player_idle.png` (fotograma 0) | Sprite del jugador — contenido pequeño y conocido |
| 1 | `assets/backgrounds/bg_stage0_far.png` | Fondo lejano de Stage 0 — grande, bajo contraste |
| 2 | `assets/tilesets/tileset_stage0.png` | Tileset — alta frecuencia, muchos bordes |
| 3 | Captura en vivo — stage0 corriendo en segundo plano | Superficie de juego en tiempo real (320×224) |
| 4 | `assets/sprites/enemies/enemy_walker_walk.png` (fotograma 0) | Sprite de enemigo |

La captura en vivo (índice 3) transmite la superficie interna de Stage 0 corriendo en segundo plano. Stage 0 debe haberse cargado al menos una vez en la sesión para que esta opción esté disponible. Si no está disponible, se salta el índice 3.

---

## 3. Escena demo de la Unidad VII — `FilterDemoScene`

### 3.1 Propósito de la escena

`FilterDemoScene` demuestra todas las operaciones que ofrece `FilterTools`. Es la referencia interactiva principal para los conceptos de la Unidad VII: histograma, brillo, contraste, convolución, desenfoque gaussiano, y detección de bordes de Sobel y Canny.

Los estudiantes usan esta escena para:
- Entender el efecto visual de cada parámetro antes de aplicarlo en su escenario.
- Calibrar sus elecciones de kernel, valores de sigma y pares de umbral.
- Capturar imágenes de antes/después para el README de su escenario.
- Completar las tareas de histograma y detección de bordes del Examen Práctico II.

### 3.2 Layout de la escena (detalle)

```
┌─────────────────────────────────────────────────────────────────┐
│  FILTER DEMO                                        UNIDAD VII  │
│  [Modo: HISTOGRAM]                          [ESC: Volver]       │
├────────────────────────┬────────────────────────────────────────┤
│                        │                                        │
│   SUPERFICIE FUENTE    │   SUPERFICIE RESULTADO                 │
│   160×180 px           │   160×180 px                           │
│                        │                                        │
│   (fuente actual)      │   (salida filtrada)                    │
│                        │                                        │
│   ▼  HISTOGRAMA        │   ▼  HISTOGRAMA                        │
│   [barra canal R]      │   [barra canal R]                      │
│   [barra canal G]      │   [barra canal G]                      │
│   [barra canal B]      │   [barra canal B]                      │
│   [barra Lum]          │   [barra Lum]                          │
│                        │                                        │
├────────────────────────┴────────────────────────────────────────┤
│  Umbral: 128  | Sigma: 1.0  | Kernel: identity  [TAB:modo]     │
└─────────────────────────────────────────────────────────────────┘
```

En modo HISTOGRAM, los 60px inferiores de cada panel se reemplazan por un gráfico de barras de histograma compacto (canales R, G, B y luminancia, cada uno mostrado como un gráfico de barras de 40px de alto escalado al ancho del panel).

### 3.3 Modos de operación

`TAB` cicla por los siguientes modos en orden:

| Índice de modo | Nombre del modo | Descripción | Parámetros activos |
|---|---|---|---|
| 0 | `HISTOGRAM` | Muestra el histograma por canal de la fuente y el resultado | Umbral para comparación binaria |
| 1 | `BRIGHTNESS` | Aplica `adjust_brightness(factor)` | `factor` (IZQUIERDA/DERECHA, paso 0.05, rango 0.0–4.0) |
| 2 | `CONTRAST` | Aplica `adjust_contrast(factor)` | `factor` (IZQUIERDA/DERECHA, paso 0.05, rango 0.0–4.0) |
| 3 | `STRETCH` | Aplica `stretch_contrast()` | Sin parámetros (sólo alternar) |
| 4 | `KERNEL` | Aplica `apply_kernel(kernel)` | Nombre de kernel (ARRIBA/ABAJO cicla los kernels estándar) |
| 5 | `GAUSSIAN` | Aplica `gaussian_blur(sigma)` | `sigma` (IZQUIERDA/DERECHA, paso 0.1, rango 0.1–5.0) |
| 6 | `SOBEL` | Aplica `sobel_edge()` | Sin parámetros |
| 7 | `CANNY` | Aplica `canny_edge(low, high)` | `low` (IZQUIERDA/DERECHA), `high` (ARRIBA/ABAJO) |
| 8 | `EQUALIZE` | Aplica `histogram_equalize()` | Sin parámetros |
| 9 | `CONV_STEP` | Animación paso a paso de la convolución de un kernel sobre la imagen, celda a celda | ESPACIO pausa/reanuda, IZQUIERDA/DERECHA ajustan la velocidad (2–64), ARRIBA/ABAJO ciclan el kernel |

> **AUD-455.** Faltaba el modo 9 (`CONV_STEP`) — verificado contra
> `src/engine/scenes/filter_demo_scene.py` (`MODE_NAMES` tiene 10 entradas,
> no 9).

### 3.4 Controles (específicos por modo)

#### Modo 1 — BRIGHTNESS
| Tecla | Efecto |
|---|---|
| `DERECHA` | Aumenta `factor` en 0.05 |
| `IZQUIERDA` | Disminuye `factor` en 0.05 |

La barra inferior muestra: `factor = 1.35 | Rango: [0.0, 4.0] | Fórmula: out = in × factor`

#### Modo 4 — KERNEL
| Tecla | Efecto |
|---|---|
| `ARRIBA` | Siguiente kernel de la lista |
| `ABAJO` | Kernel anterior de la lista |

La barra inferior muestra: `Kernel: sharpen | Tamaño: 3×3 | [matriz mostrada como texto]`

La matriz del kernel se renderiza en la barra inferior como una representación de texto compacta:
```
[[ 0 -1  0][-1  5 -1][ 0 -1  0]]
```

#### Modo 7 — CANNY
| Tecla | Efecto |
|---|---|
| `DERECHA` | Aumenta `low_threshold` en 5 |
| `IZQUIERDA` | Disminuye `low_threshold` en 5 |
| `ARRIBA` | Aumenta `high_threshold` en 5 |
| `ABAJO` | Disminuye `high_threshold` en 5 |

La barra inferior muestra: `low=50 | high=150 | ratio=3.0 | [Tubería: desenfoque→Sobel→NMS→umbral→histéresis]`

### 3.5 Entradas esperadas

| Tipo de entrada | Descripción |
|---|---|
| Superficie fuente | Cualquiera de las 5 opciones de fuente (ESPACIO para ciclar) |
| Controles de parámetro | Teclas IZQUIERDA/DERECHA/ARRIBA/ABAJO según documentado por modo |
| Selección de modo | TAB para avanzar por los 10 modos |

### 3.6 Salidas esperadas

| Salida | Ubicación |
|---|---|
| Superficie filtrada | Panel derecho, actualizada cada fotograma (limitada para operaciones costosas) |
| Barras de histograma | 60px inferiores de cada panel en modo HISTOGRAM |
| Lectura de parámetro | Barra inferior: valores actuales, fórmula, rango válido |
| PNG guardado | `tests/output/demo/filter_{mode}_{timestamp}.png` al presionar `S` |

### 3.7 Frecuencia de actualización por modo

| Modo | Frecuencia de actualización | Razón |
|---|---|---|
| HISTOGRAM | Cada fotograma | El histograma es rápido |
| BRIGHTNESS | Cada fotograma | Muy rápido |
| CONTRAST | Cada fotograma | Muy rápido |
| STRETCH | Cada fotograma | Rápido |
| KERNEL 3×3 | Cada fotograma | Rápido |
| KERNEL 7×7+ | Cada 3 fotogramas | Costo moderado |
| GAUSSIAN σ<2.0 | Cada fotograma | Rápido |
| GAUSSIAN σ≥2.0 | Cada 3 fotogramas | Costo moderado |
| SOBEL | Cada 3 fotogramas | Moderado |
| CANNY | Cada 5 fotogramas | Costo mayor |
| EQUALIZE | Cada fotograma | Rápido |

### 3.8 Reglas de visualización

1. **Barras de histograma:** dibujadas como barras verticales con `pygame.draw.rect()`. La altura de cada barra es proporcional al conteo de frecuencia, normalizado al conteo máximo. Colores: R=rojo, G=verde, B=azul, Lum=blanco.
2. **Texto de kernel:** renderizado con la fuente de mapa de bits del HUD a 5×7 px por carácter.
3. **Etiqueta de modo:** se muestra en la barra superior con la fuente de banner a 6×9 px. Se resalta en dorado cuando cambia el modo, y vuelve a blanco tras 0.5 segundos.
4. **Valor de parámetro:** se muestra como una lectura numérica en la barra inferior. Los valores que cambiaron en los últimos 0.3 segundos se muestran en amarillo; el resto en blanco.

### 3.9 Uso en evaluación

`FilterDemoScene` se usa durante el **Examen Práctico II** así:

| Tarea | Modo de escena | Objetivo de evaluación |
|---|---|---|
| Aplicar desenfoque gaussiano con sigma que iguale un desenfoque objetivo | GAUSSIAN | Selección correcta de sigma |
| Aplicar Canny con umbrales para detectar sólo bordes fuertes | CANNY | Comprensión de umbrales |
| Aplicar un kernel e identificar si realza o desenfoca | KERNEL | Comprensión de kernel |
| Calcular el histograma de una superficie dada y reportar el canal dominante | HISTOGRAM | Lectura de histograma |

El profesorado guarda un PNG de salida objetivo, y el estudiante debe igualarlo usando los controles de la escena demo. El estudiante captura su salida coincidente y la entrega como evidencia de examen.

### 3.10 Integración con Stage 0

Stage 0, Zona F, incluye una breve demostración de `adjust_brightness` y `gaussian_blur` sobre la superficie del juego. `FilterDemoScene` la extiende dando control interactivo completo sobre las 10 operaciones y las 5 superficies fuente.

### 3.11 Entregables del profesorado

| Entregable | Descripción |
|---|---|
| `src/engine/scenes/filter_demo_scene.py` | Implementación completa |
| 10 modos de operación | Todos los modos listados en §3.3 implementados |
| Visualización de histograma en vivo | Gráficos de barras por canal actualizándose cada fotograma |
| Renderizador de texto de matriz de kernel | Visualización compacta del kernel en la barra inferior |
| Función de guardar a PNG | La tecla `S` guarda la superficie de salida |

### 3.12 Reutilización por parte de los estudiantes

Los estudiantes usan `FilterDemoScene` para:
- Previsualizar resultados de filtro antes de codificarlos en su escenario.
- Calibrar valores de parámetro (sigma, umbrales, factor).
- Capturar imágenes de antes/después para su README.
- Practicar para el Examen Práctico II.

Los estudiantes **no** modifican `FilterDemoScene`.

### 3.13 Evidencia de aprendizaje

Un estudiante ha usado `FilterDemoScene` efectivamente cuando el README de su escenario:
- Contiene capturas tomadas de, o inspiradas en, la escena demo.
- Documenta los valores exactos de parámetro (sigma, umbrales, factor) elegidos y por qué.
- Incluye la matriz de kernel que usó.
- Anota la estrategia de frecuencia de actualización que adoptó para su escenario.

---

## 4. Escena demo de la Unidad VIII — `VisionDemoScene`

### 4.1 Propósito de la escena

`VisionDemoScene` demuestra todas las operaciones que ofrece `VisionTools`. Es la referencia interactiva principal para la Unidad VIII: umbralización, método de Otsu, operaciones morfológicas, componentes conectados, análisis de regiones, segmentación watershed, y extracción de características.

Los estudiantes usan esta escena para:
- Visualizar máscaras binarias, regiones etiquetadas, y superposiciones de segmentación.
- Observar cómo las operaciones morfológicas transforman una máscara.
- Ver datos de `RegionInfo` de superficies reales del juego.
- Preparar su estrategia de extracción de características para la Unidad IX.
- Completar las tareas de segmentación del Examen Práctico II.

### 4.2 Layout de la escena (detalle)

```
┌─────────────────────────────────────────────────────────────────┐
│  VISION DEMO                                      UNIDAD VIII   │
│  [Modo: THRESHOLD]                          [ESC: Volver]       │
├────────────────────────┬────────────────────────────────────────┤
│   SUPERFICIE FUENTE    │   SUPERFICIE RESULTADO                 │
│   160×180 px           │   160×180 px                           │
│                        │                                        │
│   (fuente actual)      │   (máscara / etiquetado / característica)│
│                        │                                        │
│                        │   ══ INFO DE REGIÓN (si aplica) ══     │
│                        │   Regiones: N                          │
│                        │   Mayor: A=1234 C=(80,90)              │
│                        │   Umbral: 128 [Otsu: auto]              │
│                        │                                        │
├────────────────────────┴────────────────────────────────────────┤
│  Umbral: 128  |  Kernel: 3×3  |  Método: hog  [TAB:modo]       │
└─────────────────────────────────────────────────────────────────┘
```

En modo REGIONS o CONNECTED_COMPONENTS, los 60px inferiores del panel derecho muestran una lectura de texto de las 3 mejores estadísticas de región: área, centroide (x, y) y dimensiones de la caja envolvente.

### 4.3 Modos de operación

| Índice de modo | Nombre del modo | Descripción | Parámetros activos |
|---|---|---|---|
| 0 | `THRESHOLD` | Máscara de umbral binario | `threshold` (IZQUIERDA/DERECHA, paso 5, rango 0–255) |
| 1 | `OTSU` | Auto-umbral de Otsu | Sin parámetros; se muestra el valor calculado |
| 2 | `ERODE` | Erosión de máscara binaria | `kernel_size` (IZQUIERDA/DERECHA, paso 2, rango 1–15) |
| 3 | `DILATE` | Dilatación de máscara binaria | `kernel_size` (IZQUIERDA/DERECHA, paso 2, rango 1–15) |
| 4 | `OPEN` | Apertura morfológica | `kernel_size` (IZQUIERDA/DERECHA) |
| 5 | `CLOSE` | Cierre morfológico | `kernel_size` (IZQUIERDA/DERECHA) |
| 6 | `COMPONENTS` | Componentes conectados (etiquetados) | `threshold` (IZQUIERDA/DERECHA) + conteo de componentes |
| 7 | `REGIONS` | Superposición de análisis de regiones | `threshold` (IZQUIERDA/DERECHA) + top-3 de RegionInfo |
| 8 | `WATERSHED` | Segmentación watershed | Sin parámetros; se muestra superposición de color |
| 9 | `FEATURES` | Visualización de extracción de características | `method` (ARRIBA/ABAJO: hog, lbp, color_hist) |

### 4.4 Controles (específicos por modo)

#### Modo 0 — THRESHOLD
| Tecla | Efecto |
|---|---|
| `DERECHA` | Aumenta el umbral en 5 |
| `IZQUIERDA` | Disminuye el umbral en 5 |

Barra inferior: `Umbral: 128 | Píxeles blancos: 14.302 | Píxeles negros: 57.418`

#### Modo 1 — OTSU
Sin controles de parámetro. La barra inferior muestra:
`Umbral de Otsu: 112 | Varianza inter-clase maximizada en este valor`

El valor de umbral de Otsu se muestra en dorado para llamar la atención. Este valor cambia con cada cambio de superficie fuente (`ESPACIO`).

#### Modos 2–5 — Morfología
| Tecla | Efecto |
|---|---|
| `DERECHA` | Aumenta kernel_size en 2 |
| `IZQUIERDA` | Disminuye kernel_size en 2 |

En estos modos, la tubería es **siempre**: `umbral (128 por defecto) → operación morfológica`. El umbral queda fijo en 128 en los modos de morfología para centrar la atención del estudiante en el efecto morfológico. Una nota en la barra inferior: `Umbral pre-aplicado: 128 | Kernel: {k}×{k}`

#### Modo 6 — COMPONENTS
| Tecla | Efecto |
|---|---|
| `DERECHA` | Aumenta el umbral en 5 |
| `IZQUIERDA` | Disminuye el umbral en 5 |

El panel derecho renderiza `ComponentResult.label_surface` (regiones coloreadas por código). Barra inferior: `Componentes: 7 | Umbral: 128 | [Clave de color: cada color = región distinta]`

#### Modo 7 — REGIONS
Mismos controles que COMPONENTS. El panel derecho renderiza la label_surface con superposiciones de caja envolvente (borde blanco fino por región). Los 60px inferiores del panel derecho muestran:
```
Regiones encontradas: 7
#1  A=2.840  C=(82, 91)  Rect=64×44
#2  A=1.102  C=(140,112)  Rect=33×33
#3  A=   98  C=(21, 160)  Rect=12×8
```

#### Modo 8 — WATERSHED
Sin parámetros. Barra inferior: `Watershed: {N} segmentos | Actualiza cada 15 fotogramas | Presiona S para guardar la superposición`

El resultado de watershed se precalcula al entrar al modo y al cambiar de superficie fuente. No se recalcula cada fotograma. Se muestra una superposición `[calculando...]` durante el cálculo.

#### Modo 9 — FEATURES
| Tecla | Efecto |
|---|---|
| `ARRIBA` | Cicla al siguiente método de característica |
| `ABAJO` | Cicla al método anterior |

Los métodos ciclan: `hog → lbp → color_hist → combined → hog`

El panel derecho renderiza una **visualización de vector de características**:

- **HOG:** la cuadrícula de celdas HOG se dibuja sobre la fuente (panel izquierdo), con pequeños segmentos de línea orientados que muestran el gradiente dominante en cada celda. El panel derecho muestra el vector de características completo como un gráfico de barras (512 barras para la entrada canónica de 32×32).
- **LBP:** el panel derecho muestra la imagen de códigos LBP (escala de grises, cada píxel = su código LBP). Abajo se muestra el histograma de 256 bins de los códigos LBP.
- **Histograma de color:** el panel derecho muestra tres gráficos de barras superpuestos (R, G, B), uno por canal.
- **Combinado:** el panel derecho muestra un gráfico de barras concatenado de todas las características, coloreado por segmento (HOG=azul, LBP=verde, color=rojo).

Barra inferior: `Método: hog | Longitud del vector: 512 | Tamaño de entrada canónico: 32×32`

### 4.5 Entradas esperadas

| Tipo de entrada | Descripción |
|---|---|
| Superficie fuente | ESPACIO cicla entre 5 opciones |
| Modo | TAB cicla entre 10 modos |
| Parámetro principal | IZQUIERDA/DERECHA |
| Parámetro secundario | ARRIBA/ABAJO (sólo modo 9) |

### 4.6 Salidas esperadas

| Salida | Descripción |
|---|---|
| Superficie del panel derecho | Máscara binaria, superposición de etiquetas, superposición de watershed, o visualización de características |
| Texto de info de región | Los 3 mejores objetos `RegionInfo` mostrados abajo en el panel derecho |
| Umbral de Otsu | Valor auto-calculado resaltado en dorado |
| Barras de vector de características | Longitud completa del vector mostrada como gráfico de barras |
| PNG guardado | `tests/output/demo/vision_{mode}_{timestamp}.png` con la tecla `S` |

### 4.7 Reglas de visualización

1. **Máscaras binarias:** píxeles blancos sobre fondo negro. Blanco = primer plano.
2. **Superficie de etiquetas:** 8 colores distintos de tono separado. El fondo (etiqueta 0) siempre es negro.
3. **Cajas envolventes:** contornos blancos finos de 1px dibujados sobre la superficie de etiquetas.
4. **Marcadores de centroide:** una cruz de 3×3 píxeles dibujada en cada posición de centroide.
5. **Superposición de watershed:** superposición de color semitransparente (alfa=160) mezclada sobre la superficie fuente en el panel derecho.
6. **Visualización HOG:** cuadrícula de celdas dibujada a 8×8 px por celda. La dirección de gradiente dominante por celda se muestra como un segmento de línea de 5px centrado en la celda.
7. **Gráfico de barras de características:** cada barra tiene 1px de ancho. La altura de la barra es proporcional al valor, normalizada al máximo. Los valores cero son invisibles. Los valores positivos se dibujan hacia arriba.

### 4.8 Uso en evaluación

`VisionDemoScene` se usa durante el **Examen Práctico II**:

| Tarea | Modo de escena | Objetivo de evaluación |
|---|---|---|
| Aplicar umbral para separar primer plano de fondo | THRESHOLD | Selección de umbral |
| Explicar el valor de Otsu para una superficie dada | OTSU | Comprensión del criterio de Otsu |
| Aplicar erosión para eliminar pequeñas manchas de ruido | ERODE | Razonamiento morfológico |
| Contar los componentes conectados en una máscara | COMPONENTS | Análisis de componentes |
| Reportar el área y centroide de la región más grande | REGIONS | Lectura de RegionInfo |
| Extraer características HOG y reportar la longitud del vector | FEATURES | Comprensión de descriptores de características |

### 4.9 Integración con Stage 0

`VisionDemoScene` complementa a Stage 0 dando el conjunto de herramientas de la Unidad VIII que no se demuestra en la jugabilidad. Stage 0 demuestra sistemas de jugabilidad; `VisionDemoScene` demuestra los sistemas de análisis de imagen sobre los que construirán los escenarios de estudiante de Stage 2 y 3.

### 4.10 Entregables del profesorado

| Entregable | Descripción |
|---|---|
| `src/engine/scenes/vision_demo_scene.py` | Implementación completa |
| 10 modos de operación | Todos los modos de §4.3 implementados |
| Visualización de celdas HOG | Líneas de gradiente orientado dibujadas por celda |
| Visualización de imagen de código LBP | Render de código LBP en escala de grises |
| Superposición de texto de info de región | Top-3 `RegionInfo` en el panel derecho |
| Precálculo de watershed | Calculado al entrar al modo, no por fotograma |

### 4.11 Reutilización por parte de los estudiantes

Los estudiantes usan `VisionDemoScene` para:
- Elegir su valor de umbral antes de fijarlo en código o usar Otsu.
- Decidir qué operación morfológica aplicar y con qué tamaño de kernel.
- Extraer un vector de características de una superficie que usarán para entrenar.
- Capturar visualizaciones HOG y LBP para su README.

### 4.12 Evidencia de aprendizaje

Un estudiante ha usado `VisionDemoScene` efectivamente cuando su README:
- Muestra una captura de máscara binaria de su escenario (coincide con la salida del modo threshold).
- Documenta el valor de umbral de Otsu para al menos una de las superficies de su escenario.
- Muestra una tabla de análisis de región (área, centroide, caja envolvente) para una superficie segmentada.
- Muestra una visualización HOG o LBP de la región de su escenario.

---

## 5. Escena demo de la Unidad IX — `PatternDemoScene`

### 5.1 Propósito de la escena

`PatternDemoScene` demuestra la tubería completa de aprendizaje automático en un contexto interactivo y en tiempo real. Es la referencia principal para la Unidad IX: extracción de características, entrenamiento, evaluación, e inferencia en tiempo de ejecución.

Esta escena es única en que incluye dos fases:

**Fase A — Fuera de línea (precargada):** un modelo pre-entrenado construido sobre el dataset de muestra del profesorado se carga al inicializar la escena. Los estudiantes pueden ver de inmediato la inferencia corriendo sobre superficies de juego en vivo.

**Fase B — Interactiva:** los estudiantes pueden seleccionar su propio modelo guardado (de `student_assets/models/`) y cargarlo en la escena, reemplazando el modelo del profesorado. Su propio clasificador corre entonces en la escena.

Los estudiantes usan esta escena para:
- Ver clasificación en tiempo real sobre superficies de juego.
- Validar que su modelo entrenado carga e infiere correctamente.
- Comparar la salida de su modelo con la del modelo de muestra del profesorado.
- Completar las tareas de clasificación del Examen Práctico III.

### 5.2 Layout de la escena (detalle)

```
┌─────────────────────────────────────────────────────────────────┐
│  PATTERN DEMO                                        UNIDAD IX  │
│  [Modelo: professor_sample | Método: hog | Inferencia: 3 fot.]  │
├────────────────────────┬────────────────────────────────────────┤
│   SUPERFICIE FUENTE    │   RESULTADO DE CLASIFICACIÓN           │
│   160×180 px           │   160×180 px                           │
│                        │                                        │
│   [fuente actual]      │   ▶  CLASE: dark_zone                  │
│   [rect de análisis    │   Confianza: 0.72                      │
│    resaltado en        │                                        │
│    borde amarillo]     │   ── TOP 3 PREDICCIONES ──             │
│                        │   dark_zone    ████████████ 72%        │
│                        │   neutral      ████         18%        │
│                        │   light_zone   ██           10%        │
│                        │                                        │
│                        │   ── VECTOR DE CARACTERÍSTICAS ──      │
│                        │   [gráfico de barras — HOG 512 barras] │
│                        │                                        │
├────────────────────────┴────────────────────────────────────────┤
│  [L] Cargar modelo propio | [M] Ciclar método | [TAB] modo     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Modos de operación

| Índice de modo | Nombre del modo | Descripción |
|---|---|---|
| 0 | `INFERENCE` | Clasificación en tiempo real de la región fuente seleccionada |
| 1 | `FEATURE_COMPARE` | Vector de características de la fuente lado a lado con la muestra de entrenamiento más cercana |
| 2 | `CLASS_GRID` | Cuadrícula 4×4 de muestras de entrenamiento aleatorias coloreadas por clase |
| 3 | `CONFUSION` | Muestra la matriz de confusión del modelo cargado |
| 4 | `PIPELINE` | Visualización paso a paso de la tubería (filter → vision → features → classify) |
| 5 | `TREE_VIEW` | Visualiza la estructura del árbol de decisión del modelo cargado (`model_type == 'tree'`), con la profundidad ajustable por `ParamPanel` (AUD-146) |

> **AUD-455.** Faltaba el modo 5 (`TREE_VIEW`); `MODE_NAMES` tiene 6
> entradas, no 5. Verificado contra `src/engine/scenes/pattern_demo_scene.py`.

### 5.4 Modo 0 — INFERENCE (modo principal)

**Descripción:** el rect de análisis (sub-rectángulo de borde amarillo de la superficie fuente) se clasifica cada N fotogramas usando el modelo cargado. El resultado, la confianza, y las 3 mejores predicciones se muestran en el panel derecho.

**Rect de análisis:** un rectángulo de 32×32 píxeles inicialmente centrado en la superficie fuente. Se controla con:
| Tecla | Efecto |
|---|---|
| `W/A/S/D` | Mueve el rect de análisis 8 píxeles |
| `+/-` | Aumenta/disminuye el tamaño del rect en 8 píxeles (mín 16×16, máx 80×80) |

El rect de análisis siempre se muestra como un borde amarillo de 1px en el panel izquierdo.

**Visualización de clasificación (panel derecho):**
```
▶  CLASE: dark_zone
Confianza: 0.72

── TOP 3 PREDICCIONES ──
dark_zone    ████████████ 72%
neutral      ████         18%
light_zone   ██           10%

── VECTOR DE CARACTERÍSTICAS ──
[gráfico de 512 barras para HOG]

Inferencia: cada 3 fotogramas
Modelo: professor_sample (knn, k=5)
Característica: hog | Vector: 512
```

**Frecuencia de inferencia:** fija en cada 3 fotogramas. Se muestra en la barra inferior.

**Código de color por clase:** a cada clase se le asigna un color único al cargar el modelo. El nombre de la clase con mayor predicción se muestra en ese color. Las barras de probabilidad usan los mismos colores.

### 5.5 Modo 1 — FEATURE_COMPARE

**Descripción:** extrae el vector de características del rect de análisis actual y encuentra la muestra de entrenamiento más cercana en el espacio de características. Muestra ambos vectores de características lado a lado.

Panel izquierdo, abajo: vector de características del rect de análisis actual (gráfico de barras).
Panel derecho: vector de características de la muestra de entrenamiento más cercana (gráfico de barras) + la superficie de la muestra (si está disponible en el dataset).

Barra inferior: `Distancia: 0.342 | Clase más cercana: dark_zone | k=1 más cercano`

Este modo ilustra qué hace k-NN: encontrar el punto más cercano en el espacio de características.

### 5.6 Modo 2 — CLASS_GRID

**Descripción:** muestra una cuadrícula 4×4 (16 celdas) de muestras de entrenamiento aleatorias del dataset cargado, cada celda coloreada por clase en el borde. Tamaño de celda: 32×32 píxeles.

Si el dataset tiene más de 16 muestras, se seleccionan 16 al azar (con semilla, para reproducibilidad).

El panel derecho muestra: 16 celdas en una cuadrícula de 4 columnas. Cada celda tiene un borde coloreado de 2px (color de clase) y la etiqueta de clase impresa en fuente 5×7 px al pie de la celda.

Barra inferior: `Dataset: {nombre} | Clases: {lista} | Muestras totales: {N}`

### 5.7 Modo 3 — CONFUSION

**Descripción:** renderiza la matriz de confusión del modelo cargado como una cuadrícula coloreada. Cada celda `(i, j)` muestra el número de muestras de prueba de la clase `i` predichas como clase `j`. Las celdas diagonales (predicciones correctas) son verdes; las celdas fuera de la diagonal (errores) son rojas (intensidad proporcional al conteo de errores).

La matriz de confusión se precalcula a partir del `EvaluationResult` del modelo, guardado en `TrainedModel.metadata`. Si no está disponible, se muestra un mensaje de marcador de posición: `"Matriz de confusión no disponible — ejecuta evaluate() durante el entrenamiento y guárdala en model.metadata"`

Barra inferior: `Precisión: 84.3% | Clases: 3 | Muestras de prueba: 60`

### 5.8 Modo 4 — PIPELINE

**Descripción:** una visualización paso a paso de la tubería de procesamiento completa para el rect de análisis actual. Muestra 5 paneles secuenciales (de arriba a abajo en el área del panel derecho):

```
Paso 1: Región fuente (32×32, cruda)
   ↓ FilterTools.gaussian_blur(sigma=1.0)
Paso 2: Preprocesada
   ↓ VisionTools.extract_hog()
Paso 3: Visualización HOG (cuadrícula de celdas)
   ↓ PatternRecognitionTools.classify()
Paso 4: Gráfico de barras del vector de características
   ↓ Resultado
Paso 5: ETIQUETA DE CLASE + confianza
```

Cada paso se renderiza como una pequeña superficie (aprox. 32×32 o gráfico de barras) con una etiqueta y una flecha. Este modo usa el espacio completo de 160×180 del panel derecho como un diagrama de tubería vertical.

Barra inferior: `Tubería: filter→vision→features→classify | Método: hog`

### 5.9 Controles

| Tecla | Acción |
|---|---|
| `TAB` | Cicla entre los 6 modos |
| `ESPACIO` | Cicla la superficie fuente |
| `W/A/S/D` | Mueve el rect de análisis (Modos 0 y 1) |
| `+/-` | Redimensiona el rect de análisis (Modos 0 y 1) |
| `M` | Cicla el método de extracción de características (hog / lbp / color_hist / combined) |
| `L` | Abre el cargador de modelo — ingresa el nombre de fichero en la barra inferior |
| `R` | Recarga el modelo de muestra del profesorado |
| `F` | Congela la superficie fuente |
| `S` | Guarda el PNG del panel derecho en `tests/output/demo/pattern_{mode}_{timestamp}.png` |
| `ESC` | Vuelve a DemoMenuScene |

### 5.10 Carga de modelo (tecla `L`)

Al presionar `L`, la barra inferior se convierte en un campo de entrada de texto:

```
Cargar modelo: student_assets/models/[  ]
```

El estudiante escribe el nombre del fichero (sin prefijo de ruta — el prefijo `student_assets/models/` es fijo). Sólo se aceptan ficheros `.pkl`. Al presionar `ENTER`:

1. Se llama a `PatternRecognitionTools.load_model(Path("student_assets") / "models" / filename)`.
   (AUD-455: `STUDENT_ASSETS_DIR` no existe como constante en `settings.py` —
   ver la nota de cabecera de este documento.)
2. Si tiene éxito: el modelo nuevo reemplaza al actual. La información del modelo se muestra en la barra superior.
3. Si falla: se muestra un mensaje de error durante 2 segundos en la barra inferior. Se restaura el modelo del profesorado.

Este mecanismo permite a los estudiantes validar sus modelos entrenados sin modificar ningún código del juego.

### 5.11 Entradas esperadas

| Tipo de entrada | Descripción |
|---|---|
| Superficie fuente | ESPACIO cicla entre 5 opciones |
| Rect de análisis | W/A/S/D para posicionar, +/- para redimensionar |
| Modo | TAB cicla entre 6 modos |
| Método de característica | M para ciclar |
| Modelo del estudiante | Tecla L + nombre de fichero + ENTER |

### 5.12 Salidas esperadas

| Salida | Ubicación |
|---|---|
| Etiqueta de clase predicha | Panel derecho, fuente grande |
| Porcentaje de confianza | Panel derecho |
| Barras de probabilidad top-3 | Panel derecho |
| Gráfico de barras del vector de características | Abajo en el panel derecho |
| Muestra de entrenamiento más cercana | Modo 1: panel derecho |
| Matriz de confusión | Modo 3: panel derecho |
| Diagrama de tubería | Modo 4: panel derecho |
| PNG guardado | `tests/output/demo/` con la tecla `S` |

### 5.13 Reglas de visualización

1. **Barras de probabilidad:** barras horizontales, cada una de 6px de alto con 2px de separación. Longitud proporcional a la probabilidad (barra máxima = 120px = 100%). Etiqueta a la izquierda de la barra, porcentaje a la derecha.
2. **Colores de clase:** asignados de forma determinista al hashear el nombre de clase: `color = PALETTE[hash(class_name) % len(PALETTE)]`. Paleta: 8 colores distintos de la paleta SNES.
3. **Indicador de umbral de confianza:** una línea vertical fina al 70% en las barras de probabilidad. Si la barra de la predicción principal alcanza esta línea, el indicador de confianza brilla en verde. Por debajo del 70%, brilla en amarillo.
4. **Rect de análisis:** borde amarillo de 1px. Cuando el rect se mueve, parpadea brevemente en blanco (2 fotogramas) para indicar movimiento.
5. **Celda de matriz de confusión:** tamaño de celda 20×20px. Valor impreso en fuente 5×7. Color: verde para la diagonal (intensidad = valor / máximo_diagonal), rojo fuera de la diagonal (intensidad = valor / máximo_fuera_de_diagonal).
6. **Flechas de tubería:** flecha hacia abajo (▼) de 4px de ancho dibujada entre cada paso en el Modo 4.

### 5.14 Uso en evaluación

`PatternDemoScene` se usa durante el **Examen Práctico III**:

| Tarea | Modo de escena | Objetivo de evaluación |
|---|---|---|
| Cargar un modelo y ejecutar inferencia sobre una superficie especificada | INFERENCE | Carga de modelo + inferencia |
| Reportar la predicción principal y la confianza para una entrada dada | INFERENCE | Lectura de clasificación |
| Encontrar la muestra de entrenamiento más cercana a una entrada de prueba | FEATURE_COMPARE | Comprensión de k-NN |
| Reportar la precisión de prueba del modelo a partir de la matriz de confusión | CONFUSION | Lectura de evaluación |
| Rastrear una superficie a través de la tubería completa | PIPELINE | Comprensión de la tubería |

### 5.15 Integración con el framework

`PatternDemoScene` se integra con el framework así:

| Componente del framework | Rol en PatternDemoScene |
|---|---|
| `PatternRecognitionTools.predict()` | Llamada de inferencia central en modo INFERENCE |
| `PatternRecognitionTools.load_model()` | Carga de modelo vía tecla `L` |
| `PatternRecognitionTools.classify_proba()` | Barras de probabilidad en el panel derecho |
| `VisionTools.extract_features()` | Extracción de características para visualización |
| `FilterTools.gaussian_blur()` | Paso de preprocesamiento opcional en modo PIPELINE |
| `BaseScene` | Gestión del ciclo de vida de la escena |
| `InputManager` | Entrada W/A/S/D, M, L, TAB, ESPACIO |
| `AudioManager` | Sin audio en las escenas demo (silenciado) |
| `AssetLoader` | Carga de superficies fuente |

### 5.16 Entregables del profesorado

| Entregable | Descripción |
|---|---|
| `src/engine/scenes/pattern_demo_scene.py` | Implementación completa |
| `student_assets/datasets/sample_dataset.npz` | Dataset de 90 muestras, 3 clases (dark_zone, neutral, light_zone) |
| `student_assets/models/professor_sample.pkl` | k-NN pre-entrenado (k=5) sobre el dataset de muestra |
| 6 modos de operación | Todos los modos de §5.3 implementados |
| Diálogo de carga de modelo | Entrada de texto con tecla `L` para el modelo del estudiante |
| Visualización de barras de probabilidad | Barras top-3 con colores de clase |
| Renderizador de matriz de confusión | Cuadrícula coloreada por código a partir de `EvaluationResult` |
| Diagrama de tubería | Visualización paso a paso en Modo 4 |

### 5.17 Reutilización por parte de los estudiantes

Los estudiantes usan `PatternDemoScene` para:
- Verificar que su modelo entrenado carga y produce una salida no trivial.
- Confirmar que el método de características de su modelo coincide con el que usaron para entrenar.
- Capturar imágenes de inferencia para el README de su escenario.
- Prepararse para las tareas del Examen Práctico III.

### 5.18 Evidencia de aprendizaje

Un estudiante ha usado `PatternDemoScene` efectivamente cuando:
- Su modelo carga con éxito vía la tecla `L`.
- La inferencia produce al menos 2 salidas de clase distintas entre diferentes posiciones del rect de análisis o superficies fuente.
- Su README incluye una captura del modo INFERENCE mostrando la predicción de su modelo.
- Su README incluye la matriz de confusión del modo CONFUSION.

---

## 6. Escena de laboratorio de la Unidad II — `VectorLabScene`

### 6.1 Propósito de la escena

`VectorLabScene` es un laboratorio interactivo de aritmética vectorial, normalización, producto punto y movimiento de persecución. Es la referencia interactiva principal para los conceptos de vectores de la Unidad II.

Los estudiantes usan esta escena para:
- Visualizar componentes de vector, magnitud y dirección.
- Observar vectores normalizados y su relación con el movimiento.
- Calcular y leer el producto punto y el ángulo entre dos vectores en tiempo real.
- Completar las tareas de vectores del Examen Práctico II.

### 6.2 Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  VECTOR LAB                                          UNIDAD II   │
│  [Modo: FREE MOVE]                         [ESC: Volver]         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│      [Área experimental — 320×180 px]                           │
│      Dos puntos arrastrables/controlables (Player, Enemy)        │
│      Flecha de vector de Enemy a Player con punta de flecha      │
│                                                                  │
│      Panel de información matemática (esquina inferior derecha): │
│      v = (dx, dy)  |v| = N   ^v = (nx, ny)                     │
│      Dot = D   Ángulo = θ°                                      │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  v=(24, -36)  |v|=43.3  ^v=(0.55,-0.83)  Dot= -0.27  θ=106°    │
│  [TAB: modo]  [N: alternar normalizado]  [R: reiniciar]  [flechas: mover] │
└──────────────────────────────────────────────────────────────────┘
```

### 6.3 Modos de operación

| Modo | Nombre | Descripción |
|---|---|---|
| 0 | FREE MOVE | Ambos puntos se mueven independientemente. El vector AB se actualiza en vivo. |
| 1 | CHASE | Enemy se mueve hacia Player usando `vec2_normalize()` cada fotograma. |
| 2 | ORBIT | Player orbita alrededor del centro; Enemy mira hacia Player. Lectura de producto punto. |
| 3 | DISTANCE CHECK | Distancia entre puntos mostrada con indicador de umbral. |

### 6.4 Controles

| Tecla | Acción |
|---|---|
| `FLECHAS` | Mueve el punto Player (modos 0, 1) / orbita (modo 2) |
| `W/A/S/D` | Mueve el punto Enemy (sólo modo 0) |
| `TAB` | Cicla modos |
| `N` | Alterna la visualización del vector normalizado |
| `R` | Reinicia las posiciones a sus valores por defecto |
| `S` | Guarda captura |
| `ESC` | Vuelve a DemoMenuScene |

### 6.5 Propósito pedagógico

Los estudiantes aprenden a conectar las fórmulas vectoriales abstractas (`|v|`, `v̂`, `a·b`, `θ`) con resultados espaciales visibles. El modo CHASE demuestra por qué los vectores normalizados son esenciales para una persecución de velocidad consistente. El panel de información matemática refuerza el mapeo entre fórmula y visual.

---

## 7. Escena de laboratorio de la Unidad II/III — `TransformLabScene`

### 7.1 Propósito de la escena

`TransformLabScene` demuestra transformaciones afines 2D: traslación, rotación, escalado, cizallamiento, y transformaciones compuestas. Es la referencia interactiva principal para los conceptos de transformación de la Unidad II/III.

Los estudiantes usan esta escena para:
- Ver el efecto de cada matriz de transformación sobre una forma.
- Entender la diferencia entre las matrices de traslación y rotación.
- Observar que la composición de matrices no es conmutativa (trasladar→rotar ≠ rotar→trasladar).
- Leer e interpretar una matriz de transformación 3×3 en vivo.

### 7.2 Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  TRANSFORM LAB                                  UNIDAD II/III    │
│  [Modo: TRANSLATE]                           [ESC: Volver]       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│      [Área experimental — 320×160 px]                           │
│      Forma original (contorno fantasma) + forma transformada (rellena) │
│      Fondo de cuadrícula de coordenadas                         │
│                                                                  │
│      ┌──────────────────────┐                                    │
│      │  TRANSFORMACIÓN      │  visualización de matriz 3×3      │
│      │  [1.00 0.00 32.00]  │  (alternar con N)                  │
│      │  [0.00 1.00 16.00]  │                                    │
│      │  [0.00 0.00  1.00]  │                                    │
│      └──────────────────────┘                                    │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  dx=32  dy=16  |  [TAB:modo]  [flechas:trasladar]  [N:matriz]  │
└──────────────────────────────────────────────────────────────────┘
```

### 7.3 Modos de operación

| Modo | Nombre | Descripción |
|---|---|---|
| 0 | TRANSLATE | Mueve la forma con las flechas. La matriz muestra los componentes de traslación. |
| 1 | ROTATE | Rota la forma alrededor de su centro. La matriz muestra valores sin/cos. |
| 2 | SCALE | Escala la forma (las flechas cambian el factor de escala). |
| 3 | SHEAR | Cizalla la forma horizontal/verticalmente. |
| 4 | COMPOSITE | Aplica trasladar y luego rotar frente a rotar y luego trasladar (alternar). |

### 7.4 Controles

| Tecla | Acción |
|---|---|
| `IZQUIERDA/DERECHA` | Parámetro principal (trasladar X, ángulo de rotación, escala X, cizalla X) |
| `ARRIBA/ABAJO` | Parámetro secundario (trasladar Y, escala Y, cizalla Y) |
| `TAB` | Cicla modos |
| `N` | Alterna el panel de matriz 3×3 |
| `R` | Reinicia la forma al origen |
| `S` | Guarda captura |
| `ESC` | Vuelve a DemoMenuScene |

### 7.5 Propósito pedagógico

El contorno fantasma de la forma original hace la transformación visualmente obvia. La visualización en vivo de la matriz 3×3 conecta los efectos visuales con el álgebra lineal. El modo COMPOSITE demuestra la no conmutatividad — los estudiantes ven resultados visiblemente distintos entre trasladar→rotar y rotar→trasladar.

---

## 8. Escena de laboratorio de la Unidad III — `CurveEditorScene`

### 8.1 Propósito de la escena

`CurveEditorScene` es un editor interactivo de curvas Bézier y splines. Los estudiantes colocan puntos de control y ven la curva actualizarse en tiempo real. Soporta Bézier cuadrática, Bézier cúbica, Bézier de alto grado, spline Catmull-Rom, B-Spline, y un modo de animación paso a paso de de Casteljau.

Los estudiantes usan esta escena para:
- Entender cómo los puntos de control definen la forma de la curva.
- Visualizar el algoritmo de de Casteljau una iteración a la vez.
- Comparar el comportamiento de interpolación de Bézier frente a Catmull-Rom frente a B-Spline.
- Prepararse para las tareas de examen de curvas de la Unidad III.

### 8.2 Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  CURVE EDITOR                                      UNIDAD III    │
│  [Modo: BEZIER_CUBIC (grado 3)]              [ESC: Volver]       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│      [Lienzo — 320×180 px]                                      │
│      Puntos de control (círculos arrastrables)                   │
│      Polígono de control (líneas entre puntos)                   │
│      Curva (línea gruesa a través de la interpolación)           │
│      Líneas de de Casteljau (si está activado)                   │
│                                                                  │
│      Fondo de cuadrícula con espaciado de 16px                  │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  Puntos: 4  |  Grado: 3  |  [TAB:modo]  [D:de Casteljau]  [+/-]│
└──────────────────────────────────────────────────────────────────┘
```

### 8.3 Modos de operación

| Modo | Nombre | Descripción |
|---|---|---|
| 0 | BEZIER_QUAD | 3 puntos de control, Bézier cuadrática |
| 1 | BEZIER_CUBIC | 4 puntos de control, Bézier cúbica |
| 2 | BEZIER_HIGH | N puntos de control, Bézier de alto grado |
| 3 | CATMULL_ROM | Spline Catmull-Rom (pasa por todos los puntos) |
| 4 | BSPLINE | B-Spline (los puntos de control influyen pero no se pasa por ellos) |
| 5 | DE_CASTELJAU | Animación paso a paso de de Casteljau |

### 8.4 Controles

| Tecla | Acción |
|---|---|
| `CLIC+ARRASTRAR RATÓN` | Mueve un punto de control |
| `TAB` | Cicla modos |
| `D` | Alterna la visualización de de Casteljau (modos 0–2) |
| `+` / `-` | Añade / quita un punto de control (modos 2, 4) |
| `1`–`5` | Salta directamente al modo |
| `R` | Reinicia los puntos de control a sus posiciones por defecto |
| `S` | Guarda captura |
| `ESC` | Vuelve a DemoMenuScene |

### 8.5 Propósito pedagógico

Arrastrar puntos de control da retroalimentación visual inmediata de cómo cada punto influye en la curva. El modo de animación de de Casteljau revela la interpolación lineal recursiva detrás de las curvas de Bézier. Comparar Bézier, Catmull-Rom, y B-Spline sobre los mismos puntos de control aclara la diferencia matemática entre aproximación (Bézier) e interpolación (Catmull-Rom).

---

## 9. Escena de laboratorio de la Unidad III/IV — `InterpolationLabScene`

### 9.1 Propósito de la escena

`InterpolationLabScene` demuestra la interpolación lineal, las funciones de easing, y las curvas de animación por fotogramas clave. Los estudiantes ajustan `t` y ven el valor interpolado moverse entre los extremos.

Los estudiantes usan esta escena para:
- Entender la fórmula de lerp `P = A + t(B - A)`.
- Comparar 10 funciones de easing (Linear, Quad In/Out/InOut, Cubic In/Out, Bounce Out, Elastic Out, Sine In/Out).
- Construir una animación multi-fotograma-clave y ver la interpolación con easing entre fotogramas.
- Prepararse para tareas relacionadas con animación en sus escenarios.

### 9.2 Modos de operación

| Modo | Nombre | Descripción |
|---|---|---|
| 0 | LERP | Dos extremos A y B. El deslizador `t` mueve un punto entre ellos. Se muestra la fórmula. |
| 1 | EASING CURVES | Gráfico de la función de easing actual. 10 funciones cicladas con ARRIBA/ABAJO. |
| 2 | KEYFRAME ANIM | 3 fotogramas clave con bucle de animación con easing. ESPACIO alterna la auto-reproducción. |

### 9.3 Controles

| Tecla | Acción |
|---|---|
| `IZQUIERDA/DERECHA` | Ajusta el valor de `t` (modo 0) |
| `ARRIBA/ABAJO` | Cicla la función de easing (modos 1, 2) |
| `ESPACIO` | Alterna la auto-animación (modo 2) |
| `TAB` | Cicla modos |
| `R` | Reinicia |
| `S` | Guarda captura |
| `ESC` | Vuelve a DemoMenuScene |

### 9.4 Propósito pedagógico

El modo LERP desmitifica la fórmula al mostrar cada posición intermedia. El gráfico de curvas de easing da una intuición visual de "entra lento, sale rápido" frente a lineal. El modo de animación por fotogramas clave conecta la teoría de interpolación con la práctica de animación en videojuegos.

---

## 10. Escena de laboratorio de la Unidad V — `ColorTheoryScene`

### 10.1 Propósito de la escena

`ColorTheoryScene` es un explorador interactivo de espacios de color para RGB, HSV, HSL, CMYK, y mezcla alfa. Muestra los algoritmos de conversión paso a paso, no sólo los valores finales.

Los estudiantes usan esta escena para:
- Explorar cómo los deslizadores R/G/B afectan el color resultante.
- Entender HSV y HSL como espacios de color perceptuales.
- Seguir la matemática de conversión paso a paso de RGB→HSV y RGB→HSL.
- Practicar la mezcla alfa con la fórmula `out = src·α + dst·(1-α)`.

### 10.2 Modos de operación

| Modo | Nombre | Descripción |
|---|---|---|
| 0 | RGB EXPLORER | Deslizadores R/G/B con muestra de color en vivo y lectura hexadecimal |
| 1 | HSV EXPLORER | Deslizadores H/S/V. `SHIFT` alterna la visualización de conversión paso a paso |
| 2 | HSL EXPLORER | Deslizadores H/S/L. `SHIFT` alterna la visualización de conversión paso a paso |
| 3 | CMYK EXPLORER | Deslizadores C/M/Y/K con vista previa RGB en vivo |
| 4 | ALPHA BLEND | Mezcla de dos capas con deslizador α. Fórmula mostrada con valores en vivo |
| 5 | CHALLENGE | Igualar un color objetivo aleatorio con deslizadores RGB. `ESPACIO` envía, se muestra la diferencia |

### 10.3 Controles

| Tecla | Acción |
|---|---|
| `IZQUIERDA/DERECHA` | Disminuye/aumenta el canal seleccionado |
| `ARRIBA/ABAJO` | Cicla al canal siguiente/anterior |
| `TAB` | Cicla modos |
| `SHIFT` | Alterna la visualización paso a paso del algoritmo (modos 1, 2) |
| `ESPACIO` | Envía el intento del desafío (modo 5) |
| `R` | Reinicia / nuevo desafío |
| `S` | Guarda captura |
| `ESC` | Vuelve a DemoMenuScene |

### 10.4 Propósito pedagógico

Los modos de exploración de color dejan que los estudiantes construyan intuición para cada espacio de color por manipulación directa. La visualización de conversión paso a paso revela la matemática detrás de RGB→HSV/HSL, haciendo el algoritmo concreto en vez de opaco. El modo Challenge gamifica el emparejamiento de colores y refuerza la distancia de color perceptual.

---

## 11. Escena de laboratorio de la Unidad V/VIII — `NoiseLabScene`

### 11.1 Propósito de la escena

`NoiseLabScene` demuestra la generación de ruido de valor, ruido Perlin, y ruido fractal. Los estudiantes ajustan parámetros y ven el mapa de ruido actualizarse en tiempo real.

Los estudiantes usan esta escena para:
- Entender cómo las octavas, la persistencia y la lacunaridad afectan el ruido fractal.
- Comparar visualmente el ruido de valor (en bloques) frente al ruido Perlin (suave).
- Observar cómo la escala cambia la frecuencia del patrón de ruido.
- Prepararse para tareas de generación procedural en sus escenarios.

### 11.2 Modos de operación

| Modo | Nombre | Descripción |
|---|---|---|
| 0 | VALUE NOISE | Textura de ruido de valor en escala de grises |
| 1 | PERLIN NOISE | Textura de ruido Perlin más suave |
| 2 | FRACTAL NOISE | Ruido fractal multi-octava (base de valor o Perlin) |

### 11.3 Parámetros

| Parámetro | Rango | Paso | Descripción |
|---|---|---|---|
| Octavas | 1–8 | 1 | Número de capas de ruido sumadas |
| Persistencia | 0–1 | 0.05 | Decaimiento de amplitud por octava |
| Lacunaridad | 1–8 | 0.1 | Multiplicador de frecuencia por octava |
| Escala | 0.005–0.5 | 0.005 | Frecuencia base del ruido |
| Semilla | 0–9999 | 1 | Semilla aleatoria para el patrón de ruido |

### 11.4 Controles

| Tecla | Acción |
|---|---|
| `ARRIBA/ABAJO` | Cicla el parámetro seleccionado |
| `IZQUIERDA/DERECHA` | Ajusta el valor del parámetro seleccionado |
| `ESPACIO` | Aleatoriza la semilla |
| `TAB` | Cicla el tipo de ruido |
| `R` | Reinicia todos los parámetros a sus valores por defecto |
| `S` | Guarda captura |
| `ESC` | Vuelve a DemoMenuScene |

### 11.5 Propósito pedagógico

El mapa de ruido en tiempo real da retroalimentación visual inmediata para cada parámetro. Los estudiantes pueden ver cómo aumentar las octavas añade detalle, cómo la persistencia controla la aspereza, y cómo la lacunaridad cambia la frecuencia de los rasgos. Comparar el ruido de valor directamente contra el ruido Perlin aclara por qué se prefiere la salida más suave de Perlin para terrenos naturales.

---

## 12. Escena de laboratorio de la Unidad VI — `CollisionLabScene`

### 12.1 Propósito de la escena

`CollisionLabScene` demuestra la resolución de colisión AABB por eje separado. Los estudiantes observan por qué importa el orden de resolución de ejes: resolver Y antes que X causa el bug de escalar paredes (la entidad camina por las paredes hacia arriba), mientras que X antes que Y resuelve correctamente.

Los estudiantes usan esta escena para:
- Entender la resolución de colisión por eje separado.
- Ver el bug de escalar paredes en acción y entender su causa raíz.
- Observar el comportamiento de colisión de plataformas de un solo sentido.
- Prepararse para implementar colisión en sus propios escenarios.

### 12.2 Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  COLLISION LAB                                       UNIDAD VI   │
│  [Modo: Y-FIRST (bug de escalar paredes)]     [ESC: Volver]      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│      [Nivel de prueba — 320×180 px]                             │
│      Suelo, hueco de pared, plataformas, plataforma de un sentido│
│      Rect del jugador (20×32 px, coloreado)                     │
│                                                                  │
│      Superposición de info de colisión (arriba a la derecha):    │
│      prev_bottom=184  velocidad=(64,-120)  en_suelo=SÍ          │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  Modo: Y-FIRST  |  prev_bottom: 184  |  [B: demostrar bug]  [R]│
└──────────────────────────────────────────────────────────────────┘
```

### 12.3 Modos de operación

| Modo | Nombre | Descripción |
|---|---|---|
| 0 | NO COLLISION | El jugador atraviesa todo |
| 1 | Y-FIRST | Resuelve el eje Y primero — muestra el bug de escalar paredes al caminar contra una pared |
| 2 | X-FIRST | Resuelve el eje X primero — resolución correcta |

### 12.4 Controles

| Tecla | Acción |
|---|---|
| `IZQUIERDA/DERECHA` | Mueve al jugador horizontalmente |
| `ESPACIO`/`ARRIBA` | Salta |
| `TAB` | Cicla el modo de colisión |
| `B` | Auto-demuestra el bug de escalar paredes en modo Y-FIRST |
| `R` | Reinicia la posición del jugador |
| `S` | Guarda captura |
| `ESC` | Vuelve a DemoMenuScene |

### 12.5 Propósito pedagógico

Los tres modos (sin colisión → con bug → correcto) escalonan la comprensión de la colisión por eje separado. Los estudiantes primero ven el problema (escalar pared en Y-FIRST), luego el comportamiento correcto (X-FIRST). La superposición de información de colisión (`prev_bottom`, velocidad, en_suelo) da los datos necesarios para entender por qué ocurre el bug.

---

## 13. Escena de menú de demos — `DemoMenuScene`

### 13.1 Propósito

`DemoMenuScene` es el punto de entrada de las Demos Académicas. Presenta diez opciones (7 laboratorios de teoría + 3 demos académicas) y navega a la escena seleccionada.

### 13.2 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│              DEMOSTRACIONES ACADÉMICAS                          │
│                                                                 │
│         ▶  Unidad II          — Vectores y transformaciones     │
│            Unidad II/III      — Transformaciones 2D             │
│            Unidad III         — Curvas de Bézier y splines      │
│            Unidad III/IV      — Interpolación y easing          │
│            Unidad V           — Espacios de color y mezcla alfa │
│            Unidad V/VIII      — Ruido y generación procedural   │
│            Unidad VI          — Resolución de colisión AABB     │
│            Unidad VII         — Procesamiento digital de imágenes│
│            Unidad VIII        — Segmentación y análisis          │
│            Unidad IX          — Reconocimiento de patrones      │
│                                                                 │
│                     [ESC: Volver al Título]                     │
└─────────────────────────────────────────────────────────────────┘
```

### 13.3 Controles

| Tecla | Acción |
|---|---|
| `ARRIBA` / `ABAJO` | Navega entre opciones |
| `CONFIRMAR` (Enter/Z/A) | Entra a la demo seleccionada |
| `ESC` | Vuelve a TitleScene |

---

## 14. Integración con los instrumentos de evaluación

### 14.1 Examen Práctico II — Unidades VII y VIII

El examen se realiza en el laboratorio. Los estudiantes reciben:
1. Un PNG de salida objetivo (guardado desde la escena demo por el profesorado).
2. Un PNG de superficie fuente.
3. 90 minutos para reproducir la salida objetivo usando la escena demo.

Deben documentar los parámetros usados (kernel, sigma, umbral, tamaño de kernel) en su hoja de examen.

### 14.2 Examen Práctico III — Unidad IX

El examen se realiza en el laboratorio. Los estudiantes reciben:
1. Un fichero de dataset (`.npz`).
2. Instrucciones para entrenar un clasificador específico con hiperparámetros específicos.
3. 90 minutos para entrenar, evaluar, y demostrar inferencia usando la escena demo.

Entregan: el modelo `.pkl`, una captura de la matriz de confusión, y una captura de la inferencia en Modo 0.

### 14.3 Integración con la presentación final

Durante la presentación final, los estudiantes usan las escenas demo como referencia en vivo para:
- Mostrar cómo calibraron sus parámetros antes de implementarlos en su escenario.
- Demostrar la tubería de procesamiento desde la superficie cruda hasta el resultado de clasificación.
- Comparar la matriz de confusión de su modelo con la del modelo de muestra del profesorado.

---

## 15. Notas técnicas de implementación

Estas notas van dirigidas al asistente de programación con IA que implementa las escenas demo.

### 15.1 Patrón de limitación por fotograma

Todas las operaciones costosas en las escenas demo usan un patrón de limitación compartido:

```
DemoScene.update_counter: int  # Se incrementa cada fotograma
DemoScene.cached_result: pygame.Surface | None  # Salida en caché

on update():
    update_counter += 1
    if should_update(current_mode, update_counter):
        cached_result = apply_operation(source, params)
    dibujar cached_result en el panel derecho
```

`should_update(mode, counter)` devuelve True según la tabla de frecuencia de actualización del modo (ver §3.7 para FilterDemoScene; se aplican tablas equivalentes a VisionDemoScene y PatternDemoScene).

### 15.2 Gestión de la superficie fuente

La superficie fuente siempre se renderiza a 160×180 píxeles en el panel izquierdo. Si la fuente original es más grande (p. ej., captura en vivo de 320×224), se escala a 160×180 con `pygame.transform.scale()` sólo para mostrarla. La operación real se aplica al tamaño original, salvo que supere el techo de rendimiento.

Para las operaciones WATERSHED y CANNY sobre superficies grandes, la fuente se escala a un máximo de 160×112 antes de procesar (manteniendo la relación de aspecto).

### 15.3 Entrada de texto para la carga de modelo

La entrada de texto para la carga de modelo en `PatternDemoScene` se implementa como un buffer de caracteres simple:

```
text_buffer: str = ""
cursor_visible: bool = True  # Parpadea cada 0.5 segundos

Al KEYDOWN:
    si la tecla es BACKSPACE: text_buffer = text_buffer[:-1]
    si no, si la tecla es RETURN: attempt_load(text_buffer); text_buffer = ""
    si no, si la tecla es imprimible: text_buffer += event.unicode

Al renderizar:
    dibujar "Cargar modelo: student_assets/models/" + text_buffer + ("|" si cursor_visible)
```

(AUD-455: el prefijo `student_assets/models/` se construye directamente
como texto, no vía una constante `STUDENT_ASSETS_DIR` — ésa no existe en
`settings.py`, ver la nota de cabecera de este documento.)

Sólo se acepta entrada con extensión `.pkl`. Si el estudiante ingresa un nombre sin `.pkl`, se añade automáticamente.

### 15.4 Funcionalidad de guardado

La tecla `S` guarda la superficie del panel derecho en disco:

```
path = Path("tests/output/demo") / f"{scene_prefix}_{mode_name}_{timestamp}.png"
pygame.image.save(right_panel_surface, str(path))
# Muestra "Guardado: {filename}" en la barra inferior durante 2 segundos
```

El directorio `tests/output/demo/` se crea si no existe.

### 15.5 Tamaño de fuente

| Contexto | Tamaño anterior | Tamaño actual |
|---|---|---|
| Fuente de mapa de bits del HUD (texto pequeño, corazones, números) | 5×7 px | 5×7 px (sin cambios) |
| Fuente de banner (nombres de escenario/jefe) | 6×9 px | 6×15 px |
| Fuente de diálogo/UI (cajas de mensaje, menús) | 7×11 px | 7×18 px |

Los tamaños de fuente más grandes mejoran la legibilidad en pantallas modernas. `SDL_HINT_RENDER_SCALE_QUALITY=0` garantiza el escalado de vecino más cercano para nitidez de pixel art. El antialiasing está activado en todo el renderizado de fuente.

### 15.6 Visualización de errores

Todas las excepciones capturadas durante las operaciones demo (parámetro inválido, fallo de carga, error de procesamiento) se muestran en la barra inferior durante 2 segundos:

```
error_message: str = ""
error_timer: float = 0.0

Al capturar una excepción:
    error_message = f"Error: {str(e)[:60]}"
    error_timer = 2.0

Al actualizar:
    if error_timer > 0:
        error_timer -= dt
    if error_timer <= 0:
        error_message = ""

Al dibujar:
    if error_message:
        dibujar error_message en rojo en la barra inferior
    else:
        dibujar la barra inferior normal
```

---

## 16. Restricciones

| Restricción | Alcance |
|---|---|
| Las escenas demo son propiedad del profesorado; los estudiantes no las modifican | Todos los ficheros de escena demo |
| Las escenas demo no llaman a `EventBus` | Sin emisión de eventos desde las demos |
| Las escenas demo no afectan el estado del juego | Sin generación de entidades, sin progresión de escenario |
| La carga de modelo sólo acepta ficheros `.pkl` de `student_assets/models/` | Restricción de seguridad |
| Sin reproducción de audio en las escenas demo | `AudioManager.stop_music()` se llama al entrar a una demo |
| Las escenas demo no son accesibles a mitad de escenario | Sólo accesibles desde DemoMenuScene vía TitleScene |

---

## 17. Extensiones futuras

| Extensión | Descripción | Objetivo |
|---|---|---|
| Modo de exportación de vídeo | Grabar la sesión demo como GIF | Herramientas del profesorado |
| Guardar/cargar preajustes de parámetros | Guardar conjuntos de parámetros con nombre para uso en exámenes | Exámenes prácticos |
| Comparación de clasificadores lado a lado | Dos modelos mostrados simultáneamente | Unidad IX avanzada |
| Modo de inferencia por lotes | Clasificar las 5 superficies fuente automáticamente | Examen de Unidad IX |
| Constructor de dataset personalizado | Dibujar regiones etiquetadas sobre la superficie fuente | Unidad IX avanzada |

---
## 🔗 Documentos relacionados

- [[11_FILTER_TOOLS_SPEC.md|Especificación de FilterTools]]
- [[12_VISION_TOOLS_SPEC.md|Especificación de VisionTools]]
- [[13_PATTERN_RECOGNITION_SPEC.md|Especificación de reconocimiento de patrones]]
- [[37_DEMO_QUICK_GUIDE.md|Demo Quick Guide]]

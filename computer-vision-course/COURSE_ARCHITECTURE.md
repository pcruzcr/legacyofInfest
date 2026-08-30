# COURSE_ARCHITECTURE.md — Bloque de 5 clases: PDI, Segmentación y Visión por Computadora

**Estado:** Fase 0 (decisiones, §11) y Fase 1 (cimientos, §10) cerradas y verificadas.
Siguiente: Fase 2 (datasets) y Fase 3 (Clase 1).
**Alcance:** Unidades VII, VIII y IX del programa (TIIT3002.1), en 5 sesiones de 4 horas.
**Autor del análisis:** auditoría ejecutada sobre el repositorio `legacyofInfest`, rama `dev`, 2026-08-05.
**Fuera de alcance explícito:** texturizado, sprite sheets y animación (Unidad VI).

Este documento es el entregable de la Fase 2 del prompt maestro. Contiene los diez
puntos pedidos en §22. Cada afirmación sobre el repositorio está medida, no supuesta;
la evidencia ejecutada va en §1.7.

---

## 1. Diagnóstico del repositorio

### 1.1 Qué es este repositorio, en una línea

Un motor 2D en Python + pygame-ce que **ya es** material docente de esta misma
asignatura, con 11 clases documentadas, 9 unidades mapeadas, 10 escenas-laboratorio
jugables y una capa de procesamiento de imagen propia con 196 ficheros de prueba.

**La consecuencia más importante del diagnóstico es esta: el curso no se construye
desde cero. Se construye sobre una capa de CV que ya existe, funciona y está
probada.** Lo que falta es distinto de lo que yo esperaba encontrar, y está en §1.5.

### 1.2 La capa de procesamiento que ya existe — `src/framework/processing/`

| Módulo | Líneas | Qué aporta al bloque de 5 clases |
|---|---|---|
| `filter_tools.py` | 246 | **Clase 1 y 2 completas.** `compute_histogram`, `histogram_equalize`, `adjust_brightness`, `adjust_contrast`, `stretch_contrast`, `apply_kernel`, `get_standard_kernel`, `gaussian_blur`, `sobel_edge`, `canny_edge` |
| `edge_detection.py` | 229 | **Clase 2, implementación propia en NumPy puro:** `a_gris`, `convolucionar`, `gradiente`, `sobel`, `_gauss_1d`, `suavizar`, `supresion_no_maxima`, `histeresis`, `canny` |
| `vision_tools.py` | 310 | **Clase 3 completa.** `threshold_binary`, `threshold_otsu`, `morphological_{erode,dilate,open,close}`, `connected_components`, `filter_components_by_area`, `analyze_regions`, `largest_region`, `watershed_segment`, `find_contours`, `bounding_boxes_from_mask`, `extract_features(hog\|lbp\|color_hist\|combined)` |
| `pattern_recognition_tools.py` | 388 | **Clase 4 parte A.** `train`, `evaluate`, `save_model`, `load_model`, `classify`, `classify_proba`, `predict`, `generate_training_report`; dataclases `TrainedModel` y `EvaluationResult` |
| `reference_model.py` | 157 | Reentrena el modelo de referencia en la máquina del estudiante desde el `.npz`, para no distribuir un pickle ajeno |
| `color_tools.py`, `curve_tools.py` | 383 | Unidades III y V — **fuera del alcance** de estas 5 clases |

Dos hallazgos con valor pedagógico directo, que no estaban en el plan del prompt y
que conviene aprovechar:

1. **`filter_tools.py` trae la operación duplicada a propósito**: `sobel_edge` /
   `canny_edge` (OpenCV) junto a `sobel_edge_propio` / `canny_edge_propio`, que
   delegan en `edge_detection.py`. Es exactamente el ejercicio "biblioteca contra
   implementación propia" que pide el prompt para la Clase 2, y ya está escrito y
   probado. Comparar sus salidas píxel a píxel es un laboratorio real, no un
   ejercicio inventado.
2. **`edge_detection.py` implementa Canny paso a paso y legible**: suavizado
   gaussiano → gradiente → supresión no máxima → histéresis, cada etapa una función
   separada con nombre en español. Es material de pizarra ejecutable. El prompt pide
   "MATEMÁTICA → ALGORITMO → CÓDIGO → RESULTADO"; aquí las cuatro cosas ya están en
   el mismo fichero.

`RegionInfo` expone `label, area, centroid, bounding_rect, eccentricity, solidity,
perimeter`. Es casi el `features.csv` que pide la Clase 3 — faltan `width`, `height`,
`aspect_ratio` y `circularity`, todos derivables de esos campos sin tocar el motor.

### 1.3 Las escenas-laboratorio jugables — `src/engine/scenes/`

De 45 escenas, tres son exactamente las tres unidades del bloque:

| Escena | Unidad | Registrada como | Especificada en |
|---|---|---|---|
| `filter_demo_scene.py` | VII | `"filter"` | `docs/15_ACADEMIC_DEMO_SCENES.md` §3 |
| `vision_demo_scene.py` | VIII | `"vision"` | `docs/15_ACADEMIC_DEMO_SCENES.md` §4 |
| `pattern_demo_scene.py` | IX | `"pattern"` | `docs/15_ACADEMIC_DEMO_SCENES.md` §5 |

Se construyen por `src/engine/scenes/scene_registry.py` (carga perezosa por clave) y
se llega a ellas desde `DemoMenuScene`, que se abre desde `title_scene.py:255`.
Comparten infraestructura en `demo_utils.py`: `SourceSurfaceManager` (ciclar y
congelar la imagen fuente), `FrameThrottle`, `ErrorDisplay` y `save_png`, que guarda
capturas en `tests/output/demo/` — el sitio natural para la evidencia de laboratorio.

### 1.4 Recursos, datos y herramientas disponibles

- **186 PNG**: 87 sprites, 30 fondos, 16 tilesets. 16 mapas TMX.
- **`assets/datasets/sample_dataset.npz`**: `X (90, 288) float32`, `y (90,)`,
  3 clases balanceadas (`dark_zone`, `light_zone`, `neutral`, 30 cada una).
  288 = HOG(8 orientaciones, celdas 8×8) sobre el tamaño canónico.
- **`tools/build_dataset.py`**: carpeta-por-clase → `.npz` con `X`/`y`. Ya escrito.
- **`scripts/train_reference_model.py`**: reentrena y documenta el porqué.
- **`src/stages/boss_venado/tools/capture_map.py`**: arranca el App real bajo
  `SDL_VIDEODRIVER=dummy`, teletransporta al jugador y vuelca
  `app.internal_surface` a PNG. **Es el generador de datasets del videojuego que
  necesitan las Clases 3 y 4**, ya probado, y sólo usa el bucle público
  `update()`/`draw()`. Hay que generalizarlo, no reinventarlo.
- **Rúbricas y evaluación ya existentes**: `docs/27_ACADEMIC_RUBRICS.md`,
  `docs/rubricas/`, `docs/eval_practica/`, `scripts/generate_exam.py`,
  `scripts/grade_stage.py`, `scripts/grade_boss.py`, `scripts/feedback_generator.py`.
- **3 notebooks Colab** en `colab/` (vectores, espacios de color, kernels) y
  **3 guiones de laboratorio** en `docs/labs/`. `lab03.md` ya cubre Unidades VIII–IX
  con las escenas del motor: es la plantilla de la que partir.

### 1.5 Lo que falta — cinco huecos reales, medidos

| # | Hueco | Evidencia | Impacto |
|---|---|---|---|
| **H1** | **No hay adquisición desde cámara.** Cero apariciones de `cv2.VideoCapture` en todo el árbol | `grep -rn VideoCapture` → 0 resultados fuera de `.venv` | La Clase 1 pide webcam / escáner / vídeo / fichero. Sólo existe "fichero" |
| **H2** | **No hay captura de fotograma en vivo.** `demo_utils.build_default_sources()` incluye una fuente literalmente llamada `"Live Capture (unavailable)"`: un rectángulo gris | `src/engine/scenes/demo_utils.py:107-111` | El vínculo "el juego genera los datos" está prometido en la interfaz y no implementado |
| **H3** | **No hay Regresión Logística.** `PatternRecognitionTools._build_model` acepta `knn`, `tree`, `forest`, `svm` y lanza `ValueError` con cualquier otra cosa | `pattern_recognition_tools.py:243-264` | La Clase 4 exige comparar 5 modelos, incluida LogReg. **Resuelto sin tocar el motor** — ver D3 en §11 |
| **H4** | **No hay pandas, torch ni ultralytics.** Ni en `pyproject.toml` ni instalados | verificado en el `.venv`: los tres dan `AUSENTE` | Clase 4 partes C y D, y todo el bloque de Data Analytics |
| **H5** | **Las escenas de las Unidades VII–IX están bloqueadas el primer día.** El temario es una cadena lineal: `esta_desbloqueada` sólo abre una unidad si la anterior está aprobada (4 de 5 aciertos) | `progress.py:129-143`, `curriculum.py` PLAN | Un curso que **empieza** en la Unidad VII encuentra `filter`, `vision` y `pattern` cerradas tras 7 unidades previas. **Es un bloqueo duro del laboratorio del día 1** |

H5 es el hallazgo más serio y no es un defecto: la cadena de desbloqueo es una
decisión deliberada y bien razonada (`curriculum.py`, cabecera AUD-095) para el curso
de 11 clases. Choca con un bloque intensivo que arranca en la Unidad VII. Requiere
decisión del profesor — ver §7 R1 y §11 D2.

### 1.6 Relación con el calendario ya existente — resuelta

`docs/21_COURSE_SCHEDULE.md` es un documento **oficial** que define **11 clases** de
4 horas y sitúa las tres unidades del bloque en las clases 8, 9 y 10, con
evaluaciones asociadas (Quiz 4, Lab 3, Evaluación Práctica II). El bloque de 5 clases
cubre las mismas tres unidades en cinco sesiones, así que había riesgo de dejar dos
documentos docentes contradictorios — el fallo que `docs/77_SYLLABUS_ALIGNMENT_AUDIT.md`
ya tuvo que reparar una vez.

**Decisión D1: este bloque es un módulo intensivo paralelo.** El calendario de 11
clases sigue vigente y sin cambios; `21_COURSE_SCHEDULE.md`, `08_SYLLABUS_MAPPING.md`,
`27_ACADEMIC_RUBRICS.md` y `84_EDUCATIONAL_ROADMAP.md` no se tocan. No hay
contradicción porque no hay solapamiento de autoridad: el curso de 11 clases sigue
siendo el de la asignatura TIIT3002.1, y este es material independiente que se apoya
en el mismo motor.

### 1.7 Evidencia ejecutada

```
$ .venv/Scripts/python.exe -m pytest tests/test_demo_scenes.py tests/test_vision_tools.py \
    tests/test_filter_tools.py tests/test_pattern_recognition_tools.py tests/test_edge_detection.py -q
187 passed in 10.26s
```

```
python 3.14.6
cv2 4.11.0 | skimage 0.26.0 | sklearn 1.9.0 | scipy 1.17.1 | mpl 3.11.0 | PIL 12.3.0 | numpy 1.26.4
pandas AUSENTE | torch AUSENTE | ultralytics AUSENTE | numba OK | moderngl OK
histograma claves: ['r','g','b','luminance','total_pixels']
sobel -> (64, 64)     otsu t=0     regiones: 1     features shape: (288,)
```

```
assets/datasets/sample_dataset.npz → X (90, 288) float32, y (90,) 
clases: {'dark_zone': 30, 'neutral': 30, 'light_zone': 30}
```

La capa de CV del motor **funciona hoy**, sin tocar nada. El curso puede apoyarse en
ella con confianza.

---

## 2. Arquitectura propuesta

### 2.1 Principio rector

> El curso **consume** el motor. No lo modifica.

Tras las decisiones de §11 el principio es literal y sin excepciones: **el curso no
escribe ni un byte fuera de `computer-vision-course/`.**

Tres consecuencias operativas, derivadas de las invariantes de `CLAUDE.md`:

1. **El curso vive en `computer-vision-course/`**, un subárbol nuevo, aislado e
   independiente de la documentación del repositorio. `src/`, `assets/`, `tests/`,
   `docs/` y `pyproject.toml` no se tocan — sin excepciones.
2. **Ninguna dependencia nueva entra en `pyproject.toml`.** El curso trae su propio
   `requirements.txt`, y torch/YOLO son **opcionales y sólo en Colab**. El motor ya
   degrada a heurística determinista sin scikit-learn (invariante 7); meterle torch
   sería el error opuesto y mucho más caro.
3. **`src/stages/` y `revisar/` no se abren.** Las 26 entregas de estudiantes y sus
   26 clases siguen funcionando sin tocar una línea.

### 2.2 Las cuatro capas del curso

```
  ┌─ capa 0 — EL MOTOR (existe, no se toca) ───────────────────────────────┐
  │  src/framework/processing/{filter,vision,pattern_recognition}_tools.py │
  │  src/framework/processing/edge_detection.py                            │
  │  src/engine/scenes/{filter,vision,pattern}_demo_scene.py               │
  │  assets/  (186 PNG, 16 TMX)   tools/build_dataset.py                   │
  └────────────────────────────────────────────────────────────────────────┘
                                    ▲  consume, nunca escribe
  ┌─ capa 1 — PUENTE (código nuevo del curso) ────────────────────────────┐
  │  cvcourse/acquisition.py   Fuente unificada: cámara │ fichero │ vídeo  │
  │                            │ carpeta │ FOTOGRAMA DEL MOTOR   [H1, H2]  │
  │  cvcourse/engine_bridge.py Surface ⇄ ndarray, arranque headless del    │
  │                            App real, captura de escena  (patrón de     │
  │                            boss_venado/tools/capture_map.py)           │
  │  cvcourse/features.py      RegionInfo → fila de features.csv           │
  │                            (+ width, height, aspect_ratio, circularity)│
  │  cvcourse/synthetic.py     Generador determinista de piezas industriales│
  │  cvcourse/viz.py           Rejillas antes/después, histogramas, CM     │
  │  cvcourse/course_mode.py   Perfil aislado que abre VII–IX el día 1 [H5]│
  └────────────────────────────────────────────────────────────────────────┘
                                    ▲
  ┌─ capa 2 — EJEMPLOS .py (profesionales, ejecutables en local) ──────────┐
  │  examples/class0N_*/{game,mechatronics,industrial,data_analysis}/      │
  └────────────────────────────────────────────────────────────────────────┘
  ┌─ capa 3 — NOTEBOOKS .ipynb (laboratorio experimental, Colab) ──────────┐
  │  notebooks/class01..class04.ipynb  +  class05_template.ipynb           │
  └────────────────────────────────────────────────────────────────────────┘
```

**Por qué una capa puente y no ejemplos sueltos.** El prompt prohíbe inventar APIs
del motor. La capa 1 es el único sitio donde el curso conoce al motor: si el motor
cambia, se arregla ahí y los 20 ejemplos siguen funcionando. Sin ella, cada ejemplo
tendría su propia copia de "cómo convertir una Surface en ndarray" y la primera
refactorización del motor rompería el curso entero en silencio.

**Cómo abre `course_mode.py` las Unidades VII–IX sin tocar el motor** (decisión D2).
`SesionAcademica` acepta un directorio de progreso propio —`reiniciar(directorio)`
fija el singleton, y es API pública ya usada por las pruebas—, y `registrar_examen`
también es pública. El modo intensivo crea un **perfil aparte** dentro de
`computer-vision-course/profiles/` y siembra ahí las siete unidades previas como
aprobadas, de modo que `esta_desbloqueada` abre `filter`, `vision` y `pattern` desde
el primer minuto.

Dos propiedades que hacen que esto sea aceptable y no un truco:

- **Los ficheros de progreso del curso de 11 clases no se tocan.** Son otro
  directorio. Un estudiante matriculado en la asignatura puede hacer este taller sin
  que su expediente del curso normal cambie en nada.
- **No se falsifica una nota.** El perfil del taller es un artefacto del taller, y
  así se documenta en la guía del profesor: dice "estas unidades están abiertas
  porque este módulo empieza aquí", no "este estudiante aprobó siete cuestionarios".

Verificado sobre el código: `sesion.py:59-64` (`reiniciar`), `sesion.py:150-158`
(`registrar_examen`), `progress.py:129-143` (`esta_desbloqueada`).

**Por qué `acquisition.Fuente` es una abstracción y no `cv2.VideoCapture` a pelo.**
El mismo código de laboratorio tiene que correr en: el portátil del profesor con
cámara, el del estudiante sin cámara, Colab sin cámara, y CI sin pantalla. Una fuente
que degrada —cámara → vídeo de ejemplo → carpeta de imágenes— es la diferencia entre
un laboratorio que funciona en las 30 máquinas del aula y uno que funciona en la del
profesor. Es el mismo criterio con el que el motor trata a numba y ModernGL.

### 2.3 Coherencia `.py` ↔ notebook

Regla dura, verificable por prueba: **el notebook nunca redefine lo que el `.py` ya
hace.** El notebook importa de `cvcourse` y de los ejemplos, y añade experimento,
visualización y preguntas. Un `.ipynb` que copia y pega una función del `.py` es un
defecto, no una comodidad: son dos copias que divergen a la primera corrección.

En Colab, la primera celda de cada notebook clona el repositorio o instala
`cvcourse` desde el subárbol; sin repositorio, degrada a datos sintéticos
(`cvcourse/synthetic.py`) para que el notebook siga siendo ejecutable de principio a
fin. Esto se verifica, no se supone (§10, Fase 8).

---

## 3. Mapa de contenidos de las 5 clases

Cada sesión: 4 h = teoría aplicada (45–60′) + demostración (30–45′) + laboratorio
(≈2 h, grupos de 3) + cierre (30–45′).

### Clase 1 — Adquisición, histogramas y mejoramiento

- **Pregunta que responde:** *¿de dónde sale una imagen y cómo sé si sirve?*
- **Teoría:** píxel, resolución, canales, profundidad de color, RGB↔gris, la imagen
  como matriz NumPy, `Surface` de pygame como matriz, histograma, brillo, contraste,
  ecualización, estiramiento de contraste.
- **Demostración:** las cuatro fuentes de `acquisition.Fuente` lado a lado (cámara,
  fichero, vídeo, fotograma del motor) con su histograma en vivo.
- **Videojuego:** sprite, tile y fondo reales del motor → `FilterTools.compute_histogram`
  → diagnóstico. *¿Por qué el histograma de un sprite con transparencia miente?*
- **Industrial:** pieza metálica subexpuesta → estiramiento de contraste → inspección posible.
- **Mecatrónica:** cámara sobre mesa de trabajo → histograma como **criterio de
  aceptación de la toma**, no como adorno: si el 40 % de los píxeles está saturado,
  la imagen se rechaza antes de procesarla.
- **Laboratorio:** mejorar 3 imágenes de contextos distintos, justificar cada ajuste
  con su histograma.
- **Producto:** original, procesada, ambos histogramas, análisis escrito.

### Clase 2 — Filtrado, convolución, ruido y bordes

- **Pregunta:** *¿cómo limpio una imagen y cómo encuentro su estructura?*
- **Teoría:** ruido (gaussiano, sal y pimienta), kernel, convolución, promedio,
  gaussiano, mediana, derivada discreta, gradiente, Sobel, Canny y sus 4 etapas.
- **Demostración:** `edge_detection.py` etapa por etapa —`suavizar` → `gradiente` →
  `supresion_no_maxima` → `histeresis`— con la imagen intermedia de cada una.
- **Videojuego:** escena del motor → gaussiano → mediana → Sobel → Canny.
- **Industrial:** superficie con ruido → filtrado → Canny → candidatos a defecto.
- **Mecatrónica:** preprocesado que hace posible el contorno de la Clase 3.
- **Rendimiento:** `convolucionar` en NumPy vs. `cv2.filter2D` vs. Numba, cronometrado
  sobre la misma imagen. Por qué importa a 60 fps y en una línea de producción.
- **Laboratorio:** diseñar un kernel propio, medir el efecto, romper Canny a propósito
  bajando el umbral alto y explicar el resultado.
- **Producto:** original, con ruido, resultados por filtro, Sobel, Canny, tabla de
  tiempos, conclusiones.

### Clase 3 — Segmentación y extracción de características

- **Pregunta:** *¿cómo paso de píxeles a objetos medidos?*
- **Teoría:** umbral fijo, Otsu, umbral adaptativo, máscara, erosión, dilatación,
  apertura, cierre, watershed, componentes conexas, contorno, centroide, bounding box,
  área, perímetro, relación de aspecto, circularidad.
- **Demostración:** `VisionDemoScene` en modos THRESHOLD → ERODE/DILATE → COMPONENTS
  → REGIONS, sobre un sprite del motor.
- **Videojuego:** separar sprite del fondo; contar entidades en un fotograma capturado.
- **Manufactura:** **watershed sobre piezas que se tocan** — el caso donde el umbral
  solo falla y se ve por qué.
- **Mecatrónica:** contorno → centroide → **calibración píxel → mm** con una
  referencia de tamaño conocido. Es el puente a coordenadas del mundo real.
- **Data Analytics:** construir `features.csv` con
  `object_id, area, perimeter, width, height, aspect_ratio, circularity, class`
  y **visualizar sus distribuciones**. Aquí **no** se entrena nada: el objetivo es
  entender qué información tendrá el modelo de la Clase 4.
- **Producto:** `features.csv`, imágenes, máscaras, objetos detectados, gráficas.

### Clase 4 — Reconocimiento de patrones: scikit-learn, PyTorch y YOLO

- **Pregunta:** *¿cómo hago que la computadora decida?*
- **Parte A — scikit-learn sobre las características de la Clase 3.** `X`/`y`,
  train/test, validación, sobreajuste, generalización. Comparar **KNN, Regresión
  Logística, SVM, Árbol de decisión y Random Forest** por accuracy, precision,
  recall, F1, matriz de confusión, tiempo de entrenamiento y tiempo de inferencia.
  Cuatro de los cinco salen de `PatternRecognitionTools.train`; la Regresión
  Logística se instancia con `sklearn.linear_model.LogisticRegression` directamente
  (decisión D3 — el motor no se toca). El material explica por qué se hace así, que
  de paso enseña algo útil: el framework es una capa de conveniencia sobre sklearn,
  no un muro.
- **Parte B — scikit-learn con píxeles.** `imagen → resize → gris → flatten → modelo`,
  contra el mismo modelo alimentado con características geométricas. La comparación
  es el contenido: por qué 4096 píxeles crudos rinden peor que 7 números bien elegidos,
  y en qué condiciones deja de ser cierto.
- **Parte C — PyTorch, conceptual.** `imagen → tensor → red → loss → backprop →
  optimizador → épocas`. Una red pequeña sobre el mismo dataset. **No es un tutorial
  de PyTorch**: es entender qué cambia respecto a la Parte B.
- **Parte D — YOLO, demostración.** `imagen → detección → bbox → clase → confianza`.
  Inferencia con pesos preentrenados; sin entrenamiento. El contraste conceptual es
  el objetivo: clasificar (A) ≠ aprender la representación (C) ≠ detectar y localizar (D).
- **Videojuego:** dataset de entidades a partir de fotogramas capturados del motor.
- **Industrial / Mecatrónica:** clasificación OK/NO OK; detección y localización sobre superficie.
- **Producto:** dataset, modelos, métricas, matrices de confusión, comparación,
  modelo elegido **con su justificación**, conclusiones.

### Clase 5 — Integración (sin contenido nuevo)

Grupos de 3. Cada grupo implementa un sistema completo en un dominio (videojuego,
mecatrónica, industrial, manufactura o análisis de datos) con la misma arquitectura:

```
ADQUISICIÓN → PREPROCESAMIENTO → SEGMENTACIÓN/DETECCIÓN → EXTRACCIÓN
            → ML/DL → ANÁLISIS → VISUALIZACIÓN → INTERACCIÓN
```

Se entrega plantilla de proyecto, esqueleto de código por dominio, guía de
integración y rúbrica. La sesión es de trabajo y acompañamiento, no de exposición.

---

## 4. Matriz CLASE × CONCEPTO × BIBLIOTECA × EJEMPLOS

Una tabla por clase, para que sea legible. `LOI` = código del motor ya existente.

### Clase 1

| Concepto | Biblioteca | Ej. videojuego | Ej. industrial | Ej. mecatrónica | Data analytics |
|---|---|---|---|---|---|
| Adquisición (cámara/fichero/vídeo/motor) | OpenCV, Pillow, `cvcourse.acquisition` | Fotograma del `App` real | Carga de lote de piezas | Cámara sobre mesa | — |
| Imagen como matriz | NumPy, `pygame.surfarray` | `Surface` → `ndarray` | — | — | — |
| RGB / gris / profundidad | OpenCV, `LOI.edge_detection.a_gris` | Sprite con canal alfa | Pieza metálica | — | — |
| Histograma | `LOI.FilterTools.compute_histogram`, Matplotlib | Histograma de tile y fondo | Histograma de la pieza | **Criterio de aceptación de toma** | Distribución de luminancia por lote |
| Brillo / contraste | `LOI.FilterTools.adjust_brightness/contrast` | Ajuste sobre fondo | Realce previo a inspección | — | — |
| Ecualización / estiramiento | `LOI.FilterTools.histogram_equalize/stretch_contrast` | — | **Pieza subexpuesta recuperada** | — | Antes/después medido |

### Clase 2

| Concepto | Biblioteca | Ej. videojuego | Ej. industrial | Ej. mecatrónica | Data analytics |
|---|---|---|---|---|---|
| Ruido y su modelo | NumPy, `skimage.util.random_noise` | Ruido sobre escena | Ruido de sensor en línea | — | — |
| Kernel y convolución | `LOI.edge_detection.convolucionar`, `LOI.FilterTools.apply_kernel`, SciPy | Kernels sobre tileset | — | — | — |
| Promedio / gaussiano / mediana | OpenCV, SciPy, `LOI.gaussian_blur` | Comparativa visual | **Mediana contra sal y pimienta** | Preproceso para contorno | — |
| Gradiente y Sobel | `LOI.edge_detection.{gradiente,sobel}` | Bordes de sprite | Bordes de superficie | Estructura del objeto | — |
| Canny, 4 etapas | `LOI.edge_detection.canny` (propio) vs. `cv2.Canny` | Etapa por etapa | **Candidatos a defecto** | — | — |
| Rendimiento | NumPy vs. OpenCV vs. Numba, `time.perf_counter` | Presupuesto de 16.6 ms | Ritmo de línea | Latencia de control | **Tabla de tiempos y gráfica** |

### Clase 3

| Concepto | Biblioteca | Ej. videojuego | Ej. industrial | Ej. mecatrónica | Data analytics |
|---|---|---|---|---|---|
| Umbral fijo / Otsu / adaptativo | `LOI.VisionTools.threshold_binary/threshold_otsu`, OpenCV | Sprite vs. fondo | Pieza vs. banda | Objeto vs. mesa | Umbral elegido por lote |
| Morfología (E, D, apertura, cierre) | `LOI.VisionTools.morphological_*` | Limpiar máscara de sprite | Quitar motas del sensor | — | — |
| Componentes conexas | `LOI.VisionTools.connected_components` | **Contar entidades del fotograma** | **Conteo de piezas** | Objetos en la escena | Conteo por imagen |
| Watershed | `LOI.VisionTools.watershed_segment`, skimage | — | **Piezas que se tocan** | Objetos apilados | — |
| Contornos, centroide, bbox | `LOI.VisionTools.find_contours/analyze_regions` | Bbox de entidad | Bbox de pieza | **Centroide → pick-and-place** | — |
| Píxel → mundo real | NumPy, `cvcourse.features` | — | Medición dimensional | **Calibración con referencia** | Error de medida en mm |
| Características geométricas | `cvcourse.features` sobre `RegionInfo` | — | — | — | **`features.csv` + distribuciones** |

### Clase 4

| Concepto | Biblioteca | Ej. videojuego | Ej. industrial | Ej. mecatrónica | Data analytics |
|---|---|---|---|---|---|
| X/y, train/test, sobreajuste | scikit-learn | Dataset de entidades | Dataset OK/NO OK | Dataset de componentes | Curva train vs. test |
| KNN, SVM, Árbol, Bosque | `LOI.PatternRecognitionTools.train` | Clasificar entidad | **Clasificar defecto** | Clasificar componente | **Comparativa de 5 modelos** |
| Regresión Logística | `sklearn.linear_model` directo (D3) | ídem | ídem | ídem | ídem |
| Métricas y matriz de confusión | `LOI.PatternRecognitionTools.evaluate`, sklearn | — | Coste de falso negativo | — | **Precision/recall/F1 + CM** |
| Características vs. píxeles crudos | scikit-learn, NumPy | — | — | — | **Accuracy y tiempo, lado a lado** |
| Tensor, loss, backprop, épocas | PyTorch *(sólo Colab)* | Mismo dataset | — | — | Curva de pérdida |
| Detección y localización | YOLO/ultralytics *(sólo Colab)* | Detectar entidades en captura | Detectar piezas | **Localizar sobre superficie** | Confianza por detección |

### Clase 5

| Etapa | Biblioteca | Videojuego | Industrial | Mecatrónica | Data analytics |
|---|---|---|---|---|---|
| Pipeline completo | Todas las anteriores | Analizador de fotogramas del motor | Estación de inspección | Percepción para pick-and-place | Panel de resultados |
| Interfaz | pygame-ce / Matplotlib / `pygame-gui` | Escena del motor | Panel de operador | Vista de cámara | Gráficas |

---

## 5. Dependencias

### 5.1 Ya instaladas y verificadas — el curso no pide nada para las Clases 1, 2, 3 y 4A/4B

| Paquete | Versión medida | Uso en el curso |
|---|---|---|
| numpy | 1.26.4 | todo |
| opencv-python | 4.11.0 | adquisición, filtros, contornos |
| scikit-image | 0.26.0 | ruido, HOG, LBP, watershed |
| scikit-learn | 1.9.0 | Clase 4A/4B |
| scipy | 1.17.1 | convolución, filtros |
| matplotlib | 3.11.0 | todas las visualizaciones |
| Pillow | 12.3.0 | E/S de imagen |
| pygame-ce | — | fuente de imágenes y escenas del motor |
| numba | instalado (extra `accel`) | comparativa de rendimiento, Clase 2 |

### 5.2 Nuevas — y dónde entran

| Paquete | Necesario para | Dónde | Obligatorio |
|---|---|---|---|
| `pandas` | `features.csv`, tablas comparativas | `computer-vision-course/requirements.txt` | Recomendado; hay camino de respaldo con `csv` + NumPy |
| `torch` | Clase 4 parte C | **Colab únicamente** (viene preinstalado) | No, en local |
| `ultralytics` | Clase 4 parte D | **Colab únicamente** (`pip install`) | No, en local |

**Ninguno entra en `pyproject.toml`.** Instalar torch en el `.venv` del motor añade
~2.5 GB y una matriz de compatibilidad CUDA a un repositorio del que copian 26
estudiantes; el coste no guarda ninguna proporción con dos apartados conceptuales de
una sola clase. Las partes C y D son demostraciones, no laboratorios evaluados
mediante instalación local.

---

## 6. Datasets necesarios

Cuatro, en orden de preferencia. Todos con procedencia y licencia claras — ninguna
descarga arbitraria (prompt §13).

| ID | Origen | Contenido | Cómo se produce | Licencia |
|---|---|---|---|---|
| **D1 — Motor (existente)** | `assets/` | 186 PNG, 16 TMX | ya en el repositorio | la del repositorio |
| **D2 — Fotogramas del motor** | generado | ~200 capturas etiquetadas de entidades | `cvcourse.engine_bridge` sobre el patrón de `capture_map.py`, headless | la del repositorio |
| **D3 — Piezas sintéticas** | generado | ~300 piezas con defectos controlados (grieta, mota, deformación), OK/NO OK | `cvcourse/synthetic.py`, con **semilla fija** | generado, sin restricción |
| **D4 — Referencia existente** | `assets/datasets/` | `sample_dataset.npz`, 90×288, 3 clases | ya existe | la del repositorio |

**Por qué sintético para lo industrial.** Un dataset sintético con semilla fija da
tres cosas que ninguna descarga da: verdad-terreno exacta (sabemos dónde pusimos el
defecto, así que la métrica es comprobable, no estimada), reproducibilidad bit a bit
en las 30 máquinas del aula, y control del eje de dificultad — se puede subir el
ruido y ver la accuracy caer, que es el experimento. No sustituye a imágenes reales
en un proyecto real, y eso se dice explícitamente en el material.

Ninguno se descarga en tiempo de clase. Todo se genera o ya está en el repositorio.
Peso estimado del material nuevo: < 25 MB.

---

## 7. Riesgos técnicos

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| **R1** | Las escenas VII–IX están bloqueadas el día 1 (H5) | **Cerrado** | — | **D2 aplicada**: modo intensivo en `cvcourse`, que abre las tres unidades del bloque sin tocar `progress.py` ni el progreso guardado de nadie |
| **R2** | Falta Regresión Logística en el framework (H3) | **Cerrado** | — | **D3 aplicada**: el notebook usa `sklearn.linear_model.LogisticRegression` directamente. El motor no se toca. Queda anotado como hueco del framework, no del curso |
| **R3** | Sin internet en el aula → YOLO no descarga pesos | Media | Cae la Clase 4D | Descargar pesos con antelación y llevarlos en USB; alternativa: vídeo de la demostración + salidas ya calculadas |
| **R4** | Sin cámara en las máquinas del aula | Media | Cae la parte "webcam" de la Clase 1 | `acquisition.Fuente` degrada a vídeo de ejemplo y carpeta de imágenes; la comparación entre fuentes se conserva |
| **R5** | Colab cambia de versiones y rompe los notebooks | Media | Laboratorio no ejecutable | Fijar versiones en la primera celda; una prueba ejecuta los notebooks en CI |
| **R6** | El `.venv` local corre **Python 3.14**, fuera de la matriz de CI (3.11–3.13) | Alta | Un ejemplo puede funcionar en local y fallar en el aula | Todo el código del curso se prueba en 3.11 y 3.12; sin sintaxis exclusiva de 3.13+ |
| **R7** | La captura headless del motor rompe si cambian las escenas | Baja | D2 no se genera | Aislada en `engine_bridge.py`; el dataset se versiona generado, no sólo el guion |
| **R8** | torch/YOLO en CPU son lentos | Media | La demostración se alarga | Modelos diminutos, pocas imágenes, salidas precalculadas de respaldo |
| **R9** | La suite del motor pasa de 196 ficheros; añadir pruebas del curso alarga CI | Baja | Fricción | Marcador `-m curso`, ejecución separada |

## 8. Riesgos pedagógicos

| # | Riesgo | Mitigación |
|---|---|---|
| **P1** | **Chocar con el calendario oficial de 11 clases** (§1.6) y dejar dos documentos docentes contradictorios — el fallo que `77_SYLLABUS_ALIGNMENT_AUDIT.md` ya tuvo que reparar una vez | Decisión D1 antes de generar nada. El resultado se escribe en `21_COURSE_SCHEDULE.md` o en un documento de alcance, no en los dos |
| **P2** | 4 h por sesión es mucho contenido; el riesgo real es no terminar el laboratorio | Cada clase declara un **núcleo mínimo** y un bloque de ampliación explícitamente recortable |
| **P3** | Adelantar ML antes de que se entienda la extracción de características | La Clase 3 **prohíbe entrenar**. `features.csv` se produce y se mira; el modelo llega en la Clase 4 |
| **P4** | Que el curso se lea como cuatro bibliotecas en fila | La estructura es por preguntas (§3). Cada biblioteca aparece cuando resuelve un problema ya planteado |
| **P5** | ML como caja negra | Comparación obligatoria de 5 modelos y análisis de errores; la matriz de confusión se interpreta, no sólo se imprime |
| **P6** | Cuatro contextos que acaban siendo el mismo ejercicio con otra imagen | Cada contexto tiene su **pregunta propia**: el videojuego cuenta entidades, el industrial decide OK/NO OK, mecatrónica calcula coordenadas en mm, datos compara modelos |
| **P7** | Grupos de 3 con un solo teclado | Roles rotatorios por bloque, en la guía del estudiante |
| **P8** | Nivel matemático desigual | Cada fórmula va con su código al lado — el patrón que `curriculum.py` ya usa: de la pizarra al fichero, un clic |
| **P9** | Que el material dependa del profesor línea a línea | Criterio de terminado §21: soluciones completas y ejercicios autocontenidos |

---

## 9. Propuesta de estructura de archivos

```
computer-vision-course/
├── COURSE_ARCHITECTURE.md          ← este documento
├── README.md                        (visión general, cómo empezar)
├── requirements.txt                 (pandas; torch/ultralytics comentados: sólo Colab)
├── docs/
│   ├── GUIA_DEL_PROFESOR.md
│   ├── GUIA_DEL_ESTUDIANTE.md
│   ├── REQUISITOS_TECNICOS.md
│   ├── RUBRICA_PROYECTO_FINAL.md    (alineada con docs/27_ACADEMIC_RUBRICS.md)
│   └── clase0N_guia.md              × 5   (objetivos, competencias, guion, laboratorio, criterios)
├── cvcourse/                        ← capa puente, importable
│   ├── __init__.py
│   ├── acquisition.py               [H1]
│   ├── engine_bridge.py             [H2]
│   ├── features.py
│   ├── synthetic.py
│   ├── viz.py
│   └── course_mode.py               [H5]
├── examples/
│   ├── class01_acquisition/{game,mechatronics,industrial}/
│   ├── class02_processing/{game,mechatronics,industrial}/
│   ├── class03_segmentation/{game,mechatronics,manufacturing,data_analysis}/
│   ├── class04_ml_dl/{game,mechatronics,industrial,data_analysis}/
│   └── class05_integration/{game,mechatronics,industrial,manufacturing,data_analysis}/
├── notebooks/
│   ├── class01.ipynb … class04.ipynb
│   └── class05_project_template.ipynb
├── datasets/
│   ├── README.md                    (procedencia y licencia de cada uno)
│   ├── engine_frames/               [D2, generado]
│   ├── synthetic_parts/             [D3, generado]
│   └── features/                    (features.csv de la Clase 3)
├── models/                          (modelos entrenados en clase; ignorados por git)
├── solutions/                       (soluciones de cada laboratorio)
└── tests/
    ├── test_examples_run.py         (todo .py ejecuta)
    ├── test_notebooks_run.py        (todo .ipynb ejecuta)
    ├── test_cvcourse.py
    └── test_engine_apis_exist.py    (las APIs del motor que usa el curso siguen existiendo)
```

`test_engine_apis_exist.py` merece una nota: es la prueba que convierte "no inventes
APIs del motor" en algo verificable. Si alguien renombra `VisionTools.analyze_regions`,
el curso falla en CI en lugar de fallar delante de 30 estudiantes.

Se añade `profiles/` (perfil del modo intensivo, ignorado por git) junto a `models/`.

**Registro en la documentación del repositorio: ninguno** (decisión D4). Este curso
es material **independiente**, no parte del corpus documental del motor. No se añade
fila en `docs/00_MASTER_INDEX.md` ni documento en `docs/`. La regla de `CLAUDE.md` §4
—«un documento nuevo sin fila en el índice está mal puesto»— gobierna `docs/`, que es
donde vive la documentación del motor; este subárbol no está ahí y no la invoca. El
punto de entrada del curso es su propio `README.md`.

---

## 10. Plan de generación

Fase por fase, con criterio de terminado ejecutable en cada una. Cada fase termina en
verde o no termina.

| Fase | Contenido | Verificación de cierre |
|---|---|---|
| **0. Decisiones** | D1–D5 de §11 | ✅ **Cerrada** (2026-08-05) |
| **1. Cimientos** | `cvcourse/` completo + `tests/` + `README.md` + `requirements.txt` | ✅ **Cerrada** — `147 passed in 10.01s`; `ruff check` → *All checks passed* |
| **2. Datasets** | Generar D2 y D3 con semilla fija; `datasets/README.md` | ✅ **Cerrada** — `--check` → 515 ficheros, hashes idénticos |
| **3. Clase 1** | Guía + 4 ejemplos `.py` + `class01.ipynb` + laboratorio + solución | ✅ **Cerrada** — todo ejecuta; verificado por `tests/test_material_ejecuta.py` |
| **4. Clase 2** | Ídem + comparativa de rendimiento | Ídem + tabla de tiempos reproducible |
| **5. Clase 3** | Ídem + `features.csv` | Ídem + el CSV tiene las 8 columnas y ninguna fila vacía |
| **6. Clase 4** | Ídem + comparativa de 5 modelos + partes C/D en Colab | Ídem + métricas reproducibles con semilla fija |
| **7. Clase 5** | Plantilla de proyecto, esqueletos por dominio, rúbrica | La plantilla ejecuta de extremo a extremo con datos de ejemplo |
| **8. Auditoría final** | Coherencia teoría↔código, cobertura del temario, nada adelantado, progresión entre las 5 clases, `.py` ↔ notebook | Suite completa del curso en verde **y** la del motor sin regresión (`pytest -q` sobre `tests/`) |

**Compromisos de cómo se trabaja**, tomados de `CLAUDE.md` §6 porque aquí aplican
igual: lotes pequeños y verificables por separado, nada declarado terminado sin salida
de comando pegada, y ninguna fase que se cierra con "debería funcionar".

---

## 11. Decisiones de alcance — tomadas

Resueltas por el profesor el 2026-08-05, antes de generar material.

| # | Decisión | Consecuencia |
|---|---|---|
| **D1** | **Módulo intensivo paralelo.** No sustituye ni amplía el calendario de 11 clases | `docs/21_COURSE_SCHEDULE.md` y el resto del corpus docente siguen vigentes **sin cambios**. Cero riesgo de documentación contradictoria |
| **D2** | **Modo intensivo en `cvcourse`**, con perfil de progreso aislado | `src/framework/academic/progress.py` no se toca. El progreso del curso de 11 clases y de las 26 entregas queda intacto. Sólo usa API pública (§2.2) |
| **D3** | **Regresión Logística vía sklearn directo**, no en el motor | `PatternRecognitionTools` no se modifica. H3 queda documentado como hueco **del framework**, no del curso; si algún día se cierra, será con su propio `AUD-NNN` y fuera de este trabajo |
| **D4** | **El curso es independiente de la documentación del repositorio** | No hay fila en `docs/00_MASTER_INDEX.md` ni documento nuevo en `docs/`. El punto de entrada es `computer-vision-course/README.md` |
| **D5** | **Material en español**, identificadores de código en inglés | Coherente con `CLAUDE.md` invariante 5. Sin duplicación bilingüe: no hay dos lectores, hay uno |

**El efecto conjunto es el que importa: el curso completo se genera sin modificar ni
un byte fuera de `computer-vision-course/`.** Ninguna invariante de `CLAUDE.md` entra
en juego, no hay que ejecutar los validadores del motor por cambios del curso, y la
suite de 196 ficheros de prueba no puede regresar por nada de lo que se escriba aquí.
Eso convierte la Fase 8 en una verificación del curso, no en una auditoría del motor.

**Deuda anotada, no perdida.** D3 deja `_build_model` sin Regresión Logística y D2
deja H1/H2 (adquisición por cámara y captura en vivo) resueltos *en el curso* y no en
el motor. Son decisiones correctas para este trabajo y a la vez huecos reales del
framework. Quedan escritos aquí para que quien los mire después sepa que se vieron y
por qué se dejaron fuera; llevarlos a `KNOWN_GAPS.md` sería tocar el motor, que es
justo lo que estas decisiones evitan.

---

## 12. Estado actual y alcance de lo escrito

**Hecho (Fases 0 a 3).** `cvcourse/` con sus seis módulos; el generador de datasets;
la Clase 1 completa —guía, cuatro ejemplos, notebook, laboratorio y solución—; 170
pruebas. Evidencia ejecutada:

```
$ python -m pytest computer-vision-course/tests -q
170 passed in 26.73s

$ python -m ruff check computer-vision-course/
All checks passed!

$ python computer-vision-course/scripts/build_datasets.py --check
OK: 515 ficheros, hashes idénticos. Reproducible.

# Compatibilidad con la matriz de CI (el .venv local es 3.14, fuera de ella):
sintaxis compatible con Python 3.11 y 3.12
```

`tests/test_material_ejecuta.py` es la prueba que hace cumplir el criterio de
terminado del §21 del encargo: lanza cada `.py` del material en un subproceso,
ejecuta todas las celdas de cada notebook en orden, y comprueba que ninguno lleva
rutas absolutas ni magias de IPython.

**Pendiente:** Fases 4 a 8 — Clases 2, 3, 4 y 5, y la auditoría final.

**Alcance de lo tocado.** `git status --short` → `?? computer-vision-course/`, y
`git diff --stat HEAD -- src/ tests/ assets/ docs/ pyproject.toml` sin salida: el
motor está byte a byte como en HEAD. `src/stages/` y `revisar/` no se han abierto en
ningún momento. Con D1–D4 aplicadas, el curso no necesita ningún `AUD-NNN`.

**Hallazgo ajeno al curso.** La suite del motor tiene 19 fallos y 4 errores **en
HEAD** (fc995bf), por el traslado de `_make_sfx_handler` de `SenalesDeEscenario` a
`stage_parts/sonido.py` sin actualizar las pruebas que lo buscan. No tiene relación
con este trabajo —el árbol del motor no se ha modificado— y se ha anotado aparte para
que se arregle con su propio `AUD-NNN`.

### Lo que la Fase 1 cambió de la arquitectura

Una decisión de §11 no sobrevivió al contacto con su propia prueba, y conviene que
quede escrito por qué:

**D2 se implementó por tramos, no de golpe.** La primera versión de `course_mode`
abría las Unidades VII, VIII y IX el día 1. Su prueba la tumbó al descubrir que la
cadena de desbloqueo es *transitiva*: abrir la IX exige dar por aprobadas la VII y la
VIII, que son dos de las tres unidades que este taller **evalúa**. Sus cuestionarios
se habrían quedado en decorado. La versión final abre un tramo por clase —`activar()`
en la Clase 1, `abrir("vision")` en la 3, `abrir("patrones")` en la 4—, de modo que
se respeta la cadena del motor en vez de esquivarla y el profesor conserva la llave
para quien se atasque.

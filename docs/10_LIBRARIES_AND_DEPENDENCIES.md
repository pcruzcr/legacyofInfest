---
document_id: "LOI-DEPS-010"
title: "Legacy of InFest — Librerías y dependencias"
aliases: ["Librerías y dependencias", "Libraries and Dependencies"]
tags: ["dependencias", "librerias", "setup"]
description: "Cada librería de terceros, para qué sirve y cómo se integra"
source: "docs/10_LIBRARIES_AND_DEPENDENCIES.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Librerías y dependencias

**ID del documento:** LOI-LIBS-010
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de programación con IA

---

## 1. Visión general

Este documento especifica cada librería de terceros que usa Legacy of InFest:
qué es, por qué existe en este proyecto, cómo se usa, qué restricciones tiene y
ejemplos concretos de su integración en el motor.

Todas las librerías listadas aquí están en `requirements.txt` y en
`[project.dependencies]` de `pyproject.toml`, que es la fuente de verdad única
(`scripts/check_dependency_sync.py` comprueba que los dos ficheros no
diverjan). Los estudiantes no deben importar ninguna librería que no esté en
este documento sin aprobación explícita del profesor.

> **AUD-455.** Esta versión traduce el documento (antes íntegramente en
> inglés, con un resumen al final que remitía de vuelta al original en
> inglés) y corrige varios desajustes verificados contra el código real:
> todos los ejemplos usaban rutas de importación `from framework...` /
> `from engine...`, que no existen — el paquete real es `src.framework` /
> `src.engine` (746 importaciones en el árbol lo confirman, cero con la ruta
> corta). La sección de `pytweening` describía una librería que
> `pyproject.toml` retiró explícitamente por no tener ningún importador
> (`# AUD-007: Packages removed... pytweening`) — `math_utils.py` implementa
> sus propias funciones de easing, no envuelve esa librería. La sección de
> `scikit-learn` documentaba una función `VisionTools.classify_region()` que
> no existe en `vision_tools.py`; la integración real de scikit-learn está en
> `ai_predictor.py` (IA de enemigos) y en `reference_model.py` /
> `pattern_recognition_tools.py` (demo académica de la Unidad IX). Faltaban
> por completo `pydantic`, `orjson` y `matplotlib`, que sí son dependencias
> obligatorias reales. La tabla de dependencias y el `requirements.txt` de
> ejemplo estaban desactualizados frente al fichero real del repositorio.

---

## 2. pygame-ce

### 2.1 Identidad

| Propiedad | Valor |
|---|---|
| Nombre del paquete | `pygame-ce` |
| Nombre al importar | `pygame` |
| Versión mínima | `>=2.5` (`pyproject.toml`) |
| Tipo | Framework de videojuegos |
| Licencia | LGPL 2.1 |

### 2.2 Propósito

Pygame CE (Community Edition) es el framework principal de Legacy of InFest.
Da la superficie de vídeo, el bucle de eventos, el volcado acelerado de
superficies, la gestión de sprites, la reproducción de audio, la entrada
(teclado y mando) y el renderizado de texto.

Es el fork comunitario del Pygame original: mejor rendimiento, mejor soporte
de mandos y mantenimiento activo.

### 2.3 Por qué existe

Toda la salida visual, el procesamiento de entrada, el audio y el bucle en
tiempo real del juego corren sobre Pygame CE. Sin él, el motor no arranca.

### 2.4 Reglas de uso

| Regla | Descripción |
|---|---|
| Importar sólo a través del motor | El código de escenario no importa `pygame` directamente; se accede vía la API del motor |
| Sin llamadas directas a la pantalla | `pygame.display.set_mode()` se llama sólo en `src/engine/core/app.py` |
| Sin sondeo directo de entrada | No se llama a `pygame.key.get_pressed()` en entidades o escenarios; se usa `InputManager` |
| Sin llamadas directas de sonido | No se llama a `pygame.mixer.Sound.play()` en escenarios; se usa el gestor de audio |
| Sin carga directa de imágenes | No se llama a `pygame.image.load()` en escenarios; se usa el cargador de recursos |
| Creación de superficies permitida | Se pueden crear objetos `pygame.Surface` en código de escenario para renderizado fuera de pantalla |

### 2.5 Reglas de integración

Pygame CE se inicializa exclusivamente en `src/engine/core/app.py`:

```python
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.display.set_mode(window_size, pygame.SCALED | pygame.RESIZABLE)
```

El flag `pygame.SCALED` activa el escalado entero acelerado por hardware
desde 320×224 al tamaño de ventana real.

### 2.6 Ejemplos

#### Superficie fuera de pantalla para filtrado (escenario de estudiante):
```python
from src.framework.processing.filter_tools import FilterTools

bg_copy = self.background_surface.copy()
filtered_bg = FilterTools.gaussian_blur(bg_copy, sigma=1.5)
# volcar la versión filtrada con el desplazamiento de parallax correspondiente
```

#### Detección de mando (la hace el motor, no se escribe en un escenario):
```python
joystick_count = pygame.joystick.get_count()
if joystick_count > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
```

---

## 3. numpy

### 3.1 Identidad

| Propiedad | Valor |
|---|---|
| Nombre del paquete | `numpy` |
| Nombre al importar | `numpy` (con alias `np`) |
| Versión mínima | `>=1.26` (sin tope superior, ver nota de AUD-173 en `pyproject.toml`) |
| Tipo | Librería de cómputo numérico |
| Licencia | BSD 3-Clause |

### 3.2 Propósito

NumPy da el tipo de arreglo N-dimensional (`ndarray`) usado en todo el
pipeline de procesamiento de imágenes. Las superficies de Pygame se
convierten a arreglos de NumPy para operar por píxel de forma eficiente.

### 3.3 Por qué existe

Operar píxel a píxel sobre una superficie de Pygame con bucles puros de
Python es demasiado lento para 60 FPS. NumPy vectoriza esas operaciones.

### 3.4 Reglas de uso

| Regla | Descripción |
|---|---|
| Alias siempre `np` | `import numpy as np` en todo el árbol |
| `np.uint8` para datos de píxel | Los arreglos de píxeles van en rango `uint8` (0–255) |
| Reconvertir a superficie tras procesar | Usar las utilidades de `color_tools.py` |
| No guardar arreglos grandes en el estado de una entidad | Son transitorios: se crean, se usan y se descartan por operación |

### 3.5 Reglas de integración

```python
# Superficie → ndarray (alto × ancho × 3 para RGB, × 4 para RGBA)
array = pygame.surfarray.array3d(surface)
array_alpha = pygame.surfarray.array_alpha(surface)

# ndarray → Superficie
surface = pygame.surfarray.make_surface(array)
```

**Importante:** `pygame.surfarray.array3d()` devuelve un arreglo con forma
`(ancho, alto, 3)` — el orden de ejes está invertido respecto a la convención
habitual de imagen (`alto × ancho`). Todas las operaciones de filtrado deben
tenerlo en cuenta.

### 3.6 Ejemplos

```python
import numpy as np
import pygame

def ajustar_brillo(surface: pygame.Surface, factor: float) -> pygame.Surface:
    """Multiplica cada valor de píxel por `factor`. Unidad VII: ajuste de brillo."""
    arr = pygame.surfarray.array3d(surface).astype(np.float32)
    arr = np.clip(arr * factor, 0, 255).astype(np.uint8)
    return pygame.surfarray.make_surface(arr)
```

---

## 4. scipy

### 4.1 Identidad

| Propiedad | Valor |
|---|---|
| Nombre del paquete | `scipy` |
| Nombre al importar | `scipy` |
| Versión mínima | `>=1.13` |
| Tipo | Librería de cómputo científico |
| Licencia | BSD 3-Clause |

### 4.2 Propósito

SciPy aporta el submódulo `ndimage`, usado para convolución espacial. Es más
conveniente y eficiente que implementar la convolución a mano con NumPy para
núcleos de forma arbitraria.

### 4.3 Por qué existe

`scipy.ndimage.convolve` y `scipy.ndimage.gaussian_filter` dan
implementaciones académicamente correctas de convolución y desenfoque
gaussiano, los conceptos de la Unidad VII.

### 4.4 Reglas de uso

| Regla | Descripción |
|---|---|
| Sólo `scipy.ndimage` | Ningún otro submódulo de SciPy se usa en el proyecto |
| Siempre sobre `np.float32` | Convertir a float antes de filtrar, volver a uint8 después |
| No aplicar a pantalla completa cada fotograma | Es caro; aplicar a sub-superficies o a frecuencia reducida |

### 4.5 Reglas de integración

SciPy se usa exclusivamente dentro de `src/framework/processing/filter_tools.py`. El código de escenario nunca lo importa directamente.

### 4.6 Ejemplos

```python
from scipy.ndimage import gaussian_filter
import numpy as np
import pygame

def desenfoque_gaussiano(surface: pygame.Surface, sigma: float) -> pygame.Surface:
    arr = pygame.surfarray.array3d(surface).astype(np.float32)
    blurred = gaussian_filter(arr, sigma=[sigma, sigma, 0])
    return pygame.surfarray.make_surface(blurred.astype(np.uint8))
```

---

## 5. opencv-python

### 5.1 Identidad

| Propiedad | Valor |
|---|---|
| Nombre del paquete | `opencv-python` |
| Nombre al importar | `cv2` |
| Versión mínima | `>=4.10` |
| Tipo | Librería de visión por computadora |
| Licencia | Apache 2.0 |

### 5.2 Propósito

OpenCV aporta detección de bordes de Canny, umbralización de Otsu,
segmentación por watershed, operaciones morfológicas y extracción de
características — las herramientas principales de las Unidades VII, VIII y IX.

### 5.3 Por qué existe

Reimplementar estos algoritmos desde cero no es razonable en el contexto de
un proyecto estudiantil. OpenCV da implementaciones estándar de la industria
y académicamente reconocidas, para que el estudiante aplique el concepto en
vez de depurar aritmética de bajo nivel.

### 5.4 Reglas de uso

| Regla | Descripción |
|---|---|
| Importar como `cv2` | Convención estándar |
| Ojo con BGR vs RGB | OpenCV usa orden de canal BGR; Pygame usa RGB. Convertir siempre |
| Sólo vía `vision_tools.py` | El acceso a OpenCV pasa por las herramientas de visión del framework, no directo |
| No procesar pantalla completa cada fotograma | Las operaciones de OpenCV son caras; usar sub-superficies o limitar la frecuencia |

### 5.5 Regla de conversión BGR/RGB

```python
# Pygame/NumPy (RGB) → OpenCV (BGR):
bgr_array = cv2_array[:, :, ::-1]

# Resultado de OpenCV (BGR) → Pygame (RGB):
rgb_array = cv2_result[:, :, ::-1]
```

Todas las conversiones BGR/RGB están dentro de
`src/framework/processing/vision_tools.py`. El estudiante nunca las maneja
directamente.

### 5.6 Reglas de integración

```python
arr = pygame.surfarray.array3d(surface)
arr_cv = np.transpose(arr, (1, 0, 2))   # (ancho, alto, 3) → (alto, ancho, 3)
arr_bgr = arr_cv[:, :, ::-1]            # RGB → BGR
# ... operación de OpenCV ...
arr_rgb = cv2_result[:, :, ::-1]        # BGR → RGB
arr_pygame = np.transpose(arr_rgb, (1, 0, 2))
surface = pygame.surfarray.make_surface(arr_pygame)
```

### 5.7 Ejemplos

Ver `FilterTools.canny_edge()` y `VisionTools.watershed_segment()` en
`src/framework/processing/filter_tools.py` y
`src/framework/processing/vision_tools.py` para las implementaciones reales
usadas por el motor.

---

## 6. scikit-image

### 6.1 Identidad

| Propiedad | Valor |
|---|---|
| Nombre del paquete | `scikit-image` |
| Nombre al importar | `skimage` |
| Versión mínima | `>=0.24` |
| Tipo | Librería de procesamiento de imágenes |
| Licencia | BSD 3-Clause |

### 6.2 Propósito

scikit-image complementa a OpenCV con una API más "pythónica". Es
particularmente útil para operaciones morfológicas, patrones binarios
locales (LBP) e histograma de gradientes orientados (HOG).

### 6.3 Por qué existe

`VisionTools.extract_hog()` y `VisionTools.extract_lbp()`
(`src/framework/processing/vision_tools.py`) usan `skimage.feature.hog` y
`skimage.feature.local_binary_pattern` para la extracción de características
de las Unidades VIII y IX.

### 6.4 Reglas de uso

| Regla | Descripción |
|---|---|
| Sólo vía `vision_tools.py` | El código de escenario no importa `skimage` directamente |
| Rango float [0, 1] | Las funciones de scikit-image suelen esperar arreglos float en [0,1], no uint8 en [0,255] |

### 6.5 Ejemplos

```python
arr_float = arr.astype(np.float32) / 255.0
# ... operación de scikit-image ...
result_uint8 = (result_float * 255).astype(np.uint8)
```

---

## 7. scikit-learn

### 7.1 Identidad

| Propiedad | Valor |
|---|---|
| Nombre del paquete | `scikit-learn` |
| Nombre al importar | `sklearn` |
| Versión mínima | `>=1.5` |
| Tipo | Librería de aprendizaje automático |
| Licencia | BSD 3-Clause |

### 7.2 Propósito

scikit-learn aporta los algoritmos de clasificación de la Unidad IX. Hay dos
integraciones reales en el motor, no una sola:

1. **`src/framework/entities/ai_predictor.py`** — `BehaviorPredictor` usa
   `KNeighborsClassifier` y `DecisionTreeClassifier` para recomendar tácticas
   a los enemigos. No se consulta enemigo por enemigo y fotograma a fotograma
   (saldría demasiado caro: 1,89 ms por inferencia individual, ver el
   docstring de `squad_brain.py`); `SquadBrain`
   (`src/framework/entities/squad_brain.py`) agrupa a todos los enemigos
   vivos de la escena y reevalúa el lote a 4 Hz.
2. **`src/framework/processing/reference_model.py`** y
   **`pattern_recognition_tools.py`** — el modelo de referencia de la demo
   académica de la Unidad IX (`pattern_demo_scene.py`). Entrena
   `KNeighborsClassifier`, `DecisionTreeClassifier`, `RandomForestClassifier`
   o `SVC` (según lo que elija el estudiante) desde
   `assets/datasets/sample_dataset.npz` **en la máquina de quien juega**, en
   vez de cargar un estimador ya serializado — un `.pkl` entrenado con otra
   versión de scikit-learn produce resultados distintos sin ningún aviso en
   pantalla (`InconsistentVersionWarning`), y deserializar con `joblib.load`
   ejecuta código arbitrario, dos razones para no repartir el archivo
   entrenado entre estudiantes.

### 7.3 Por qué existe

La Unidad IX exige clasificación. scikit-learn da implementaciones
documentadas y estándar de k-NN, árboles de decisión, bosques aleatorios y
SVM, con una API `fit`/`predict` consistente.

### 7.4 Reglas de uso

| Regla | Descripción |
|---|---|
| Nunca por entidad y por fotograma | Usar el lote de `SquadBrain`, no una llamada individual por enemigo |
| Entrenar desde datos, no distribuir el modelo | El estimador entrenado no se versiona ni se reparte; se reentrena desde el dataset |
| Serializar con `joblib` cuando haga falta | `joblib.dump(model, ruta)` / `joblib.load(ruta)` |

### 7.5 Nota sobre disponibilidad en tiempo de ejecución

`scikit-learn` está en `[project.dependencies]` de `pyproject.toml` — es una
dependencia **obligatoria** de instalación, no un extra opcional. `ai_predictor.py`
sigue importándolo a nivel de módulo sin `try`/`except`.

> **AUD-455/AUD-457.** Que la instalación sea obligatoria ya no significa que
> el fallo en runtime sea un `ImportError` sin red: `SquadBrain._decide_batch`
> (en `src/framework/entities/squad_brain.py`) envuelve su `import` de
> `ai_predictor` en `try`/`except ImportError` y, si falla, recurre a
> `src/framework/entities/tactica_por_reglas.py` — una heurística por reglas
> sin ninguna dependencia de sklearn. `src/framework/entities/precarga_ia.py`
> hace lo mismo al precargar el módulo desde la pantalla de presentación o
> desde `main.py --stage`/`--boss`. En la práctica sklearn siempre está
> instalado (es obligatoria), así que esta ruta de repliegue rara vez se
> ejercita — pero a diferencia de lo que decía una versión anterior de esta
> nota, hoy sí es una degradación real y alcanzable, no una promesa sin
> implementar.

### 7.6 Ejemplos

Entrenamiento y evaluación reales están en
`src/framework/processing/reference_model.py::TrainedModel`. La toma de
decisión de un enemigo, en `src/framework/entities/ai_predictor.py`:

```python
from src.framework.entities.ai_predictor import get_predictor

predictor = get_predictor()
acciones = predictor.predict_batch(lista_de_vectores_de_caracteristicas)
```

---

## 8. Pillow

### 8.1 Identidad

| Propiedad | Valor |
|---|---|
| Nombre del paquete | `Pillow` |
| Nombre al importar | `PIL` |
| Versión mínima | `>=12.3.0` (suelo de seguridad, AUD-176 — ver `SUELOS_POR_SEGURIDAD` en `tests/test_dependencias_coherentes.py`) |
| Tipo | Librería de E/S y manipulación de imágenes |
| Licencia | HPND (código abierto) |

### 8.2 Propósito

Pillow gestiona la carga y conversión de formato de imagen del pipeline de
recursos. Aunque Pygame CE carga PNG y JPEG de forma nativa, Pillow soporta
mejor los casos límite: PNG en modo paleta, imágenes de color indexado, e
imágenes que necesitan preprocesarse antes de cargarse como superficie de
Pygame.

También la usa `scripts/validate_assets.py` para comprobar que los recursos
de los estudiantes cumplen las restricciones de paleta y dimensiones.

### 8.3 Reglas de uso

| Regla | Descripción |
|---|---|
| No se usa en tiempo de ejecución del juego | Es una herramienta de desarrollo y validación; ningún módulo del motor o del framework la importa |
| Sólo validación de recursos | `scripts/validate_assets.py` la usa para comprobar la paleta |
| No en código de escenario de estudiante | El estudiante no la importa |

---

## 9. pytmx

### 9.1 Identidad

| Propiedad | Valor |
|---|---|
| Nombre del paquete | `pytmx` |
| Nombre al importar | `pytmx` |
| Versión mínima | `>=3.32` |
| Tipo | Analizador de ficheros de mapa de Tiled |
| Licencia | LGPL |

### 9.2 Propósito

`pytmx` analiza los ficheros `.tmx` creados con el editor Tiled: capas de
baldosas, capas de objetos, referencias de tileset y propiedades
personalizadas, expuestos como objetos de Python.

### 9.3 Reglas de uso

| Regla | Descripción |
|---|---|
| Se usa sólo en el cargador de escenarios | Es responsabilidad exclusiva del motor |
| El estudiante nunca importa pytmx | El análisis de TMX es responsabilidad del motor |
| Todo acceso al mapa vía los datos de escenario que expone el cargador | No se toca `pytmx` directamente desde un escenario |

### 9.4 Reglas de integración

```python
import pytmx

tmx_data = pytmx.util_pygame.load_pygame(str(tmx_path))

for layer in tmx_data.visible_layers:
    if isinstance(layer, pytmx.TiledTileLayer):
        for x, y, gid in layer:
            tile_surface = tmx_data.get_tile_image_by_gid(gid)
```

---

## 10. pyscroll

### 10.1 Identidad

| Propiedad | Valor |
|---|---|
| Nombre del paquete | `pyscroll` |
| Nombre al importar | `pyscroll` |
| Versión mínima | `>=2.31` |
| Tipo | Renderizador de mapas con scroll para pytmx |
| Licencia | LGPL |

### 10.2 Propósito

`pyscroll` renderiza sólo la parte visible del mapa en cada fotograma,
gestiona la ventana de cámara y el scroll de capas de parallax.

### 10.3 Por qué existe

Redibujar un mapa entero de miles de píxeles de ancho sobre una superficie de
320×224 en cada fotograma es innecesario y lento. `pyscroll` sólo renderiza
las baldosas visibles, con un búfer que precalcula las baldosas cercanas para
un scroll fluido.

### 10.4 Reglas de integración

```python
import pyscroll

map_data = pyscroll.data.TiledMapData(tmx_data)
map_layer = pyscroll.BufferedRenderer(map_data, size=(320, 224), clamp_camera=True)
group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=4)

# en el draw() del escenario:
group.center(player.rect.center)
group.draw(surface)
```

---

## 11. Funciones de easing (`src/engine/utils/math_utils.py`)

**No hay ninguna dependencia `pytweening` en este proyecto.** La versión
anterior de este documento la documentaba como una librería instalada; se
retiró de `pyproject.toml` porque nada en el árbol la importaba
(`# AUD-007: Packages removed... pytweening`). Las funciones de easing que
usa el motor están **implementadas directamente** en
`src/engine/utils/math_utils.py`: `ease_in_quad`, `ease_out_quad`,
`ease_in_out_quad`, `ease_in_cubic`, `ease_out_cubic`, `ease_out_bounce`,
`ease_out_elastic`, `ease_in_sine`, `ease_out_sine`.

Siguen ilustrando el contenido de la Unidad VI del curso: la interpolación y
las funciones de aceleración/desaceleración no son una caja negra — son
funciones matemáticas (polinómicas, senoidales) aplicadas a un parámetro
normalizado `t ∈ [0, 1]`, y en este motor están a la vista, no detrás de una
librería externa.

### 11.1 Reglas de uso

| Regla | Descripción |
|---|---|
| `t` debe estar en [0, 1] | Las funciones de easing no están definidas fuera de ese rango |
| La función no muta `t` | Es sin estado; quien llama gestiona el avance de `t` |

### 11.2 Ejemplo

```python
from src.engine.utils.math_utils import ease_in_out_quad, lerp

eased_t = ease_in_out_quad(self.t)
self.position.x = lerp(self.start_pos.x, self.end_pos.x, eased_t)
```

---

## 12. pydantic

| Propiedad | Valor |
|---|---|
| Nombre al importar | `pydantic` |
| Versión mínima | `>=2.7` |
| Tipo | Validación de datos y modelos tipados |

Valida el esquema de los datos que se guardan y se cargan: logros
(`src/engine/core/achievements.py`), dificultad (`difficulty.py`), inventario
(`inventory.py`), partidas guardadas (`save_data.py`) y los parámetros del
modelo de referencia de la Unidad IX (`pattern_recognition_tools.py`). Evita
que una partida guardada con un campo corrupto o de tipo equivocado se cargue
en silencio.

---

## 13. orjson

| Propiedad | Valor |
|---|---|
| Nombre al importar | `orjson` |
| Versión mínima | `>=3.10` |
| Tipo | Serialización JSON rápida |

Serializa y deserializa partidas guardadas, marcadores, ajustes de usuario y
progreso — más rápido que el `json` de la biblioteca estándar en los ficheros
que se escriben cada vez que se guarda la partida
(`save_manager.py`, `score_system.py`, `user_settings.py`, `bestiary.py`,
`enemy_base.py`, `speedrun_mode.py`, entre otros).

---

## 14. matplotlib

| Propiedad | Valor |
|---|---|
| Nombre al importar | `matplotlib` |
| Versión mínima | `>=3.10` |
| Tipo | Trazado de gráficas |

Genera las gráficas de la demo de reconocimiento de patrones
(`pattern_demo_scene.py`) y el informe de entrenamiento de
`reference_model.py`/`pattern_recognition_tools.py` (matriz de confusión,
curvas). Si `matplotlib` o `scikit-learn` faltaran, esa ruta concreta lo
registra como aviso y devuelve `None` en vez de fallar — es la única de las
dependencias de procesamiento con una salida de repliegue explícita en el
código (`except ImportError: logger.warning(...)`).

---

## 15. Extras opcionales

Estos tres grupos **no** están en `[project.dependencies]`: el juego los
detecta en tiempo de importación y sigue funcionando sin ellos, con una ruta
de repliegue.

| Extra | Instala | Repliegue si falta |
|---|---|---|
| `accel` | `numba>=0.62` (JIT del integrador de partículas), `ModernGL>=5.10` (post-proceso por GPU) | Integrador puro en Python; volcado por software |
| `scripting` | `lupa>=2.1` (comportamientos de enemigo en Lua) | — |
| `audiotools` | `pydub>=0.25` (conversión de audio fuera de línea, `tools/convert_audio.py`) | — |

```bash
pip install -e ".[accel]"
pip install -e ".[scripting]"
pip install -e ".[audiotools]"
```

---

## 16. Tabla resumen de dependencias

| Librería | Obligatoria | Código de escenario | Código de framework | Código de motor |
|---|---|---|---|---|
| `pygame-ce` | ✅ | indirecto | ✅ | ✅ |
| `numpy` | ✅ | indirecto | ✅ | — |
| `pydantic` | ✅ | — | ✅ | ✅ |
| `orjson` | ✅ | — | ✅ | ✅ |
| `scipy` | ✅ | — | ✅ | — |
| `opencv-python` | ✅ | — | ✅ | — |
| `scikit-image` | ✅ | — | ✅ | — |
| `scikit-learn` | ✅ | — | ✅ | — |
| `Pillow` | ✅ (sólo herramientas) | — | — | — |
| `pytmx` | ✅ | — | ✅ | — |
| `pyscroll` | ✅ | — | ✅ | — |
| `joblib` | ✅ | — | ✅ | — |
| `matplotlib` | ✅ | — | ✅ (demo) | — |
| `numba`, `ModernGL` | extra `accel` | — | — | ✅ |
| `lupa` | extra `scripting` | — | ✅ | — |
| `pydub` | extra `audiotools` | — | herramientas | — |

---

## 17. `requirements.txt`

El fichero real (sincronizado a mano con `pyproject.toml`,
`scripts/check_dependency_sync.py` lo comprueba):

```
pygame-ce>=2.5
numpy>=1.26
pydantic>=2.7
orjson>=3.10
scipy>=1.13
opencv-python>=4.10
scikit-image>=0.24
scikit-learn>=1.5
Pillow>=12.3.0
pytmx>=3.32
pyscroll>=2.31
joblib>=1.4
matplotlib>=3.10
```

---

## 18. Instalación y entorno

Los pasos completos, con solución de problemas, están en
[`82_ENVIRONMENT_SETUP_GUIDE.md`](82_ENVIRONMENT_SETUP_GUIDE.md). En resumen:

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux — en Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"        # instalación recomendada, incluye pytest/ruff/mypy
```

---

## Documentos relacionados

- [[82_ENVIRONMENT_SETUP_GUIDE.md]]
- [[23_DATA_SCHEMAS.md]]

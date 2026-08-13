---
document_id: "LOI-VISION-012"
title: "Legacy of InFest — Especificación de VisionTools"
aliases: ["Especificación de VisionTools", "Vision Tools Spec"]
tags: ["vision", "segmentacion", "processing"]
description: "Subsistema de segmentación de la Unidad VIII"
source: "docs/12_VISION_TOOLS_SPEC.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación de VisionTools

**ID del documento:** LOI-VISION-012
**Versión:** 1.1.0
**Estado:** Oficial
**Compatibilidad:** Requiere `03_ARCHITECTURE.md`, `11_FILTER_TOOLS_SPEC.md`, `10_LIBRARIES_AND_DEPENDENCIES.md`
**Audiencia:** Profesor, ayudantes de cátedra, asistentes de programación con IA

> **AUD-455.** Traduce el documento (cuerpo en inglés, resumen condensado en
> español al final). Corrige la ruta del módulo, que carecía del prefijo
> `src/` en seis apariciones, y quita `classify_region(features, model)` del
> resumen final: ese método **no existe** en `VisionTools` — verificado por
> AST contra `src/framework/processing/vision_tools.py` — ni lo describe el
> cuerpo en inglés del propio documento. La clasificación con un modelo
> entrenado vive en `PatternRecognitionTools.classify()`
> (`13_PATTERN_RECOGNITION_SPEC.md`), no aquí.

---

## 1. Visión general

`VisionTools` es el subsistema de segmentación y análisis de imágenes del framework académico de Legacy of InFest. Encapsula todas las operaciones que enseña la **Unidad VIII** del programa del curso: umbralización, método de Otsu, operaciones morfológicas, análisis de componentes conectados, análisis de regiones, segmentación watershed y extracción de características.

Este módulo es el puente entre las operaciones de filtro puras de la Unidad VII (cubiertas por `FilterTools`) y las operaciones de clasificación de la Unidad IX (cubiertas por `PatternRecognitionTools`). Transforma superficies filtradas en datos estructurados — regiones, etiquetas, contornos, máscaras y vectores de características — que la lógica del juego puede interpretar y sobre los que puede actuar.

El módulo está en:

```
src/framework/processing/vision_tools.py
```

---

## 2. Propósito académico

`VisionTools` hace que los conceptos de la Unidad VIII sean **espacialmente visibles** dentro del juego. Los estudiantes no procesan imágenes científicas abstractas — procesan regiones de su propio escenario de juego, identifican zonas significativas dentro de ellas, y dejan que esas zonas dirijan el comportamiento del juego. Esto transforma la segmentación de un ejercicio teórico en una decisión de diseño.

### 2.1 Objetivos de aprendizaje que soporta

| Objetivo | Mecanismo de VisionTools |
|---|---|
| Aplicar umbralización binaria como frontera de decisión | `threshold_binary()` separa los píxeles en dos clases |
| Aplicar el método de Otsu como selección automática de umbral | `threshold_otsu()` calcula el umbral óptimo de forma adaptativa |
| Aplicar erosión y dilatación a imágenes binarias | `morphological_erode()`, `morphological_dilate()` |
| Identificar regiones conectadas en imágenes binarias | `connected_components()` devuelve regiones etiquetadas |
| Extraer propiedades de región (área, centroide, caja envolvente) | `analyze_regions()` devuelve estadísticas por región |
| Aplicar watershed a imágenes sobre-segmentadas | `watershed_segment()` devuelve una superficie etiquetada |
| Extraer un vector de características de una región de superficie | `extract_features()` devuelve un descriptor numérico |

### 2.2 Posición en la tubería académica

```
Superficie cruda (fondo de juego, sprite, región de pantalla)
    ↓ FilterTools (Unidad VII)
Superficie preprocesada (desenfocada, con bordes detectados, brillo ajustado)
    ↓ VisionTools (Unidad VIII)
Datos estructurados (máscaras, regiones, etiquetas, vectores de características)
    ↓ PatternRecognitionTools (Unidad IX)
Resultado de clasificación → Comportamiento de juego
```

---

## 3. Ubicación en el framework

```
src/framework/
└── processing/
    ├── filter_tools.py
    └── vision_tools.py          ← Este módulo
```

### 3.1 Posición en la jerarquía de dependencias

```
Escenarios (código de estudiante)
    ↓
src/framework/processing/vision_tools.py   ← Los estudiantes llaman a esto
    ↓
src/framework/processing/filter_tools.py   ← VisionTools puede llamar a FilterTools internamente
    ↓
numpy, scipy, opencv-python, scikit-image
```

---

## 4. Integración con la arquitectura

### 4.1 Conexiones con el framework

| Punto de integración | Descripción |
|---|---|
| `FilterTools` | VisionTools puede llamar internamente a `FilterTools.gaussian_blur()` para preprocesar dentro de watershed; los estudiantes también pueden encadenarlos explícitamente |
| `PatternRecognitionTools` | El `extract_features()` de VisionTools produce el vector de características que consumen los clasificadores de PatternRecognitionTools |
| Escenas de escenario (código de estudiante) | Los estudiantes llaman a `VisionTools` desde el `update()` del escenario para dirigir el comportamiento a partir de datos visuales |
| Suite de pruebas unitarias (`tests/test_vision_tools.py`) | Cada método guarda imágenes etiquetadas y máscaras PNG en `tests/output/vision/` |

### 4.2 Lo que VisionTools NO hace

| Acción prohibida | Razón |
|---|---|
| No llama a `EventBus` | Módulo de cómputo puro |
| No modifica el estado de entidades directamente | Los estudiantes usan los valores de retorno para modificar el estado |
| No llama a `InputManager` ni `AudioManager` | Sin lógica de interacción |
| No lee ni escribe ficheros | Toda la E/S es vía valores de retorno |
| No modifica las superficies de entrada in situ | Todas las operaciones devuelven datos nuevos |

---

## 5. Dependencias

| Biblioteca | Importación | Se usa para |
|---|---|---|
| `numpy` | `import numpy as np` | Representación en arreglo, arreglos de etiqueta, vectores de características |
| `cv2` (opencv-python) | `import cv2` | Umbral, morfología, componentes conectados, watershed, contornos |
| `scipy.ndimage` | `from scipy.ndimage import label` | Etiquetado de componentes conectados (alternativa a cv2) |
| `skimage.feature` | `from skimage.feature import hog, local_binary_pattern` | Extracción de características HOG y LBP |
| `skimage.measure` | `from skimage.measure import regionprops` | Propiedades de región (área, centroide, excentricidad) |
| `pygame` | `import pygame` | Entrada/salida de superficies |

**Los estudiantes nunca importan nada de lo anterior.**

---

## 6. Diagrama de clase

```
VisionTools
│
├── [Umbral]
│   ├── threshold_binary(surface, threshold) → Surface (máscara)
│   └── threshold_otsu(surface) → tuple[Surface, int]
│
├── [Morfología]
│   ├── morphological_erode(surface, kernel_size) → Surface
│   ├── morphological_dilate(surface, kernel_size) → Surface
│   ├── morphological_open(surface, kernel_size) → Surface
│   └── morphological_close(surface, kernel_size) → Surface
│
├── [Componentes conectados]
│   ├── connected_components(mask_surface) → ComponentResult
│   └── filter_components_by_area(result, min_area, max_area) → ComponentResult
│
├── [Análisis de regiones]
│   ├── analyze_regions(mask_surface) → list[RegionInfo]
│   └── largest_region(mask_surface) → RegionInfo | None
│
├── [Watershed]
│   └── watershed_segment(surface) → Surface (superposición de color etiquetada)
│
├── [Extracción de características]
│   ├── extract_features(surface, method) → np.ndarray
│   ├── extract_hog(surface) → np.ndarray
│   ├── extract_lbp(surface) → np.ndarray
│   └── extract_color_histogram(surface, bins) → np.ndarray
│
├── [Cajas envolventes y contornos]
│   ├── find_contours(mask_surface) → list[np.ndarray]
│   └── bounding_boxes_from_mask(mask_surface) → list[pygame.Rect]
│
└── [Utilidades internas — privadas]
    ├── _to_gray_array(surface) → np.ndarray
    ├── _to_binary_array(mask_surface) → np.ndarray
    ├── _label_array_to_color_surface(label_array) → Surface
    ├── _validate_mask(surface) → None
    └── _validate_surface(surface) → None
```

### 6.1 Definiciones de tipo de retorno

#### `ComponentResult` (named tuple o dataclass)

| Campo | Tipo | Descripción |
|---|---|---|
| `label_array` | `np.ndarray` (`int32`, forma `(H, W)`) | Cada píxel etiquetado con su ID de componente (0 = fondo) |
| `num_components` | `int` | Número total de componentes conectados distintos |
| `component_sizes` | `dict[int, int]` | Mapeo de ID de etiqueta → conteo de píxeles |
| `label_surface` | `pygame.Surface` | Superficie coloreada por código, para depuración visual |

#### `RegionInfo` (named tuple o dataclass)

| Campo | Tipo | Descripción |
|---|---|---|
| `label` | `int` | ID de etiqueta del componente |
| `area` | `int` | Área en píxeles |
| `centroid` | `tuple[float, float]` | Centroide `(x, y)` en coordenadas de píxel |
| `bounding_rect` | `pygame.Rect` | Caja envolvente alineada a los ejes |
| `eccentricity` | `float` | Excentricidad de forma: 0 = círculo, 1 = línea |
| `solidity` | `float` | Razón entre el área y el área de la envolvente convexa |
| `perimeter` | `float` | Perímetro en píxeles |

---

## 7. Clase VisionTools

### 7.1 Responsabilidades

1. Aceptar objetos `pygame.Surface` y devolver datos estructurados.
2. Convertir superficies a arreglos en escala de grises/binarios según necesite cada operación.
3. Aplicar la operación matemática usando la biblioteca adecuada.
4. Devolver los resultados como `pygame.Surface`, arreglos de NumPy, o estructuras de datos documentadas.
5. Validar todas las entradas y lanzar excepciones descriptivas.

---

## 8. Operaciones de umbral

### 8.1 `VisionTools.threshold_binary(surface, threshold)`

**Propósito:** aplica un umbral binario fijo a una representación en escala de grises de la superficie. Cada píxel con luminancia ≥ `threshold` se vuelve blanco (255, 255, 255). Cada píxel por debajo se vuelve negro (0, 0, 0). Esto separa la imagen en dos clases y es la operación fundacional de todo análisis de imagen binaria.

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `surface` | `pygame.Surface` | RGB/RGBA, cualquier tamaño | Superficie fuente |
| `threshold` | `int` | `[0, 255]` | Valor de corte de intensidad |

**Salidas:** nueva `pygame.Surface` de tamaño idéntico. Binaria: los píxeles son blanco puro o negro puro. RGB, sin alfa.

**Tubería interna:**
```
surface → arreglo en escala de grises (fórmula de luminancia: 0.299R + 0.587G + 0.114B)
       → cv2.threshold(arr, threshold, 255, cv2.THRESH_BINARY)
       → arreglo binario uint8
       → superficie RGB (replica la escala de grises en los 3 canales)
```

**Restricciones:**

- `threshold` fuera de `[0, 255]` lanza `ValueError`.
- La salida siempre es RGB binaria (no escala de grises de un solo canal).
- No modifica la entrada.

**Dependencias:** `numpy`, `opencv-python`

**Ejemplo de uso:**

```python
from src.framework.processing.vision_tools import VisionTools

# Segmentar una capa de fondo — identificar regiones brillantes:
mask = VisionTools.threshold_binary(self.background_surface, threshold=128)

# Contar cajas de regiones brillantes:
bright_boxes = VisionTools.bounding_boxes_from_mask(mask)
if len(bright_boxes) > 3:
    event_bus.emit("SHOW_MESSAGE", text="¡Se detectaron muchas zonas brillantes!", duration=2.0)
```

---

### 8.2 `VisionTools.threshold_otsu(surface)`

**Propósito:** aplica el método de umbralización automática de Otsu. En vez de exigir un valor de umbral manual, el método de Otsu analiza el histograma y encuentra el umbral que minimiza la varianza de intensidad intra-clase (equivalentemente, maximiza la varianza inter-clase). Esto demuestra la toma de decisiones adaptativa basada en estadísticas de la imagen.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `surface` | `pygame.Surface` | RGB/RGBA, cualquier tamaño |

**Salidas:** una `tuple` de dos valores:

| Índice | Tipo | Descripción |
|---|---|---|
| `[0]` | `pygame.Surface` | Superficie de máscara binaria (igual que la salida de `threshold_binary`) |
| `[1]` | `int` | El valor de umbral de Otsu calculado (para la documentación del estudiante) |

**Tubería interna:**
```
surface → arreglo en escala de grises
       → cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
       → (arreglo_binario, valor_de_umbral_calculado)
       → return (surface, int(threshold_value))
```

**Restricciones:**

- Necesita que la superficie tenga variación tonal significativa. Una superficie uniforme producirá un umbral arbitrario; se registra un aviso.
- La superficie de salida es RGB binaria.
- No modifica la entrada.

**Dependencias:** `numpy`, `opencv-python`

**Ejemplo de uso:**

```python
mask, otsu_t = VisionTools.threshold_otsu(self.terrain_surface)
print(f"Umbral de Otsu: {otsu_t}")  # Para la documentación del README
regions = VisionTools.analyze_regions(mask)
```

---

## 9. Operaciones morfológicas

Todas las operaciones morfológicas necesitan una **superficie de máscara binaria** como entrada (salida de `threshold_binary` o `threshold_otsu`). Usan un elemento estructurante cuadrado de tamaño `kernel_size × kernel_size`.

### 9.1 `VisionTools.morphological_erode(surface, kernel_size)`

**Propósito:** aplica erosión morfológica a una máscara binaria. La erosión encoge las regiones blancas eliminando píxeles en sus bordes. Un píxel se conserva blanco sólo si todos los píxeles dentro del elemento estructurante también son blancos. Esto elimina pequeñas manchas de ruido y separa regiones débilmente conectadas.

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `surface` | `pygame.Surface` | Máscara binaria (RGB o escala de grises) | Máscara binaria fuente |
| `kernel_size` | `int` | `≥ 1`, se recomienda impar | Longitud de lado del elemento estructurante cuadrado |

**Salidas:** nueva `pygame.Surface` de tamaño idéntico. Máscara binaria tras la erosión.

**Dependencias:** `opencv-python` (`cv2.erode`)

**Ejemplo de uso:**

```python
mask = VisionTools.threshold_binary(bg_surface, 100)
eroded = VisionTools.morphological_erode(mask, kernel_size=3)
# Píxeles aislados pequeños eliminados de la máscara
```

---

### 9.2 `VisionTools.morphological_dilate(surface, kernel_size)`

**Propósito:** aplica dilatación morfológica a una máscara binaria. La dilatación hace crecer las regiones blancas añadiendo píxeles a sus bordes. Un píxel se vuelve blanco si cualquier píxel dentro del elemento estructurante es blanco. Esto rellena pequeños huecos y conecta regiones cercanas.

**Entradas/Salidas:** misma estructura que `morphological_erode`.

**Dependencias:** `opencv-python` (`cv2.dilate`)

---

### 9.3 `VisionTools.morphological_open(surface, kernel_size)`

**Propósito:** aplica apertura morfológica (erosión seguida de dilatación). La apertura elimina objetos pequeños preservando la forma y el tamaño de los objetos más grandes. Útil para eliminar ruido en máscaras binarias.

**Definición matemática:** `open(A, B) = dilate(erode(A, B), B)`

**Entradas/Salidas:** misma estructura que `morphological_erode`.

**Dependencias:** `opencv-python` (`cv2.MORPH_OPEN`)

---

### 9.4 `VisionTools.morphological_close(surface, kernel_size)`

**Propósito:** aplica cierre morfológico (dilatación seguida de erosión). El cierre rellena pequeños huecos dentro de las regiones y conecta regiones cercanas preservando el tamaño general de los objetos.

**Definición matemática:** `close(A, B) = erode(dilate(A, B), B)`

**Entradas/Salidas:** misma estructura que `morphological_erode`.

**Dependencias:** `opencv-python` (`cv2.MORPH_CLOSE`)

---

### 9.5 Operaciones morfológicas — tabla de rendimiento

| Operación | Kernel 3×3 | Kernel 7×7 | Kernel 15×15 |
|---|---|---|---|
| Erosión | < 0.5ms | < 1ms | ~2ms |
| Dilatación | < 0.5ms | < 1ms | ~2ms |
| Apertura | < 1ms | ~2ms | ~4ms |
| Cierre | < 1ms | ~2ms | ~4ms |

Todos los tiempos son para una superficie de 320×224.

---

## 10. Componentes conectados

### 10.1 `VisionTools.connected_components(mask_surface)`

**Propósito:** etiqueta todas las regiones conectadas en una máscara binaria. Cada grupo conectado distinto de píxeles blancos recibe una etiqueta entera única. El fondo (píxeles negros) siempre es la etiqueta 0. Es la operación fundacional para identificar objetos distintos en una imagen segmentada.

**Conectividad:** 8-conectada (los vecinos diagonales están conectados).

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `mask_surface` | `pygame.Surface` | Máscara binaria (salida de una operación de umbral o morfología) |

**Salidas:** `ComponentResult` (ver Sección 6.1):
- `label_array`: `np.ndarray int32` de forma `(H, W)` — cada píxel contiene su etiqueta de componente
- `num_components`: total de componentes de primer plano distintos
- `component_sizes`: `{label_id: conteo_de_píxeles}` para todas las etiquetas
- `label_surface`: superficie coloreada por código, para depuración visual (cada componente de un color distinto)

**Tubería interna:**
```
mask_surface → arreglo binario uint8 en escala de grises
             → cv2.connectedComponentsWithStats(arr, connectivity=8)
             → (num_labels, label_array, stats, centroids)
             → construir ComponentResult
             → generar label_surface coloreada por código
```

**Restricciones:**

- La entrada debe ser una superficie binaria (blanco/negro). Se emite un aviso si se detectan valores no binarios.
- Máximo de componentes soportados: 32.767 (límite de OpenCV).
- No modifica la entrada.

**Dependencias:** `numpy`, `opencv-python`

**Ejemplo de uso:**

```python
mask = VisionTools.threshold_binary(self.ground_surface, 140)
result = VisionTools.connected_components(mask)

print(f"Se encontraron {result.num_components} regiones")
# Depuración visual:
surface.blit(result.label_surface, (0, 0))
```

---

### 10.2 `VisionTools.filter_components_by_area(result, min_area, max_area)`

**Propósito:** filtra un `ComponentResult` para conservar sólo los componentes cuya área en píxeles cae dentro de `[min_area, max_area]`. Devuelve un nuevo `ComponentResult` con sólo los componentes que califican, y una nueva `label_surface` que refleja el filtro.

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `result` | `ComponentResult` | De `connected_components()` | Resultado de entrada a filtrar |
| `min_area` | `int` | `≥ 0` | Área mínima de componente en píxeles |
| `max_area` | `int` | `> min_area` | Área máxima de componente en píxeles |

**Salidas:** nuevo `ComponentResult` sólo con los componentes que califican. Las etiquetas **no se renumeran** — se preservan los ID de etiqueta originales para permitir referencia cruzada con el `label_array` original.

**Ejemplo de uso:**

```python
result = VisionTools.connected_components(mask)
# Conservar sólo regiones de tamaño medio (ni ruido ni fondo):
filtered = VisionTools.filter_components_by_area(result, min_area=50, max_area=2000)
```

---

## 11. Análisis de regiones

### 11.1 `VisionTools.analyze_regions(mask_surface)`

**Propósito:** extrae propiedades cuantitativas de cada región conectada en una máscara binaria. Devuelve una lista de objetos `RegionInfo`, uno por componente de primer plano, ordenados por área (la más grande primero). Es el puente entre una máscara visual y datos numéricos que pueden dirigir la lógica del juego.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `mask_surface` | `pygame.Surface` | Superficie de máscara binaria |

**Salidas:** `list[RegionInfo]`, ordenada por área descendente. Lista vacía si no se encuentran regiones de primer plano.

**Campos de `RegionInfo`** (ver Sección 6.1 para la definición completa):
- `label`, `area`, `centroid`, `bounding_rect`, `eccentricity`, `solidity`, `perimeter`

**Tubería interna:**
```
mask_surface → arreglo binario → cv2.connectedComponentsWithStats
            → skimage.measure.regionprops (para excentricidad, solidez, perímetro)
            → construir list[RegionInfo]
            → ordenar por área descendente
```

**Dependencias:** `numpy`, `opencv-python`, `scikit-image` (`skimage.measure.regionprops`)

**Ejemplo de uso:**

```python
regions = VisionTools.analyze_regions(mask)

for region in regions:
    print(f"Área: {region.area}, Centroide: {region.centroid}")

    # Generar una entidad en el centroide de cada región grande:
    if region.area > 500:
        cx, cy = int(region.centroid[0]), int(region.centroid[1])
        spawn_position = pygame.Vector2(cx, cy)
        new_entity = MyCustomEntity(spawn_position)
        self.entities.append(new_entity)
```

---

### 11.2 `VisionTools.largest_region(mask_surface)`

**Propósito:** método de conveniencia. Devuelve el `RegionInfo` de la única región conectada más grande en la máscara, o `None` si no existen regiones de primer plano.

**Entradas/Salidas:** igual que `analyze_regions` pero devuelve un único `RegionInfo` o `None`.

**Ejemplo de uso:**

```python
largest = VisionTools.largest_region(mask)
if largest:
    rect = largest.bounding_rect
    pygame.draw.rect(surface, (255, 0, 0), rect, 2)
```

---

## 12. Segmentación watershed

### 12.1 `VisionTools.watershed_segment(surface)`

**Propósito:** aplica segmentación watershed para identificar regiones distintas separadas por líneas de cresta. El algoritmo watershed trata la imagen como una superficie topográfica (intensidad = elevación) y la inunda desde mínimos marcados. Las líneas de cresta entre los frentes de inundación forman los bordes de segmento.

Esta operación produce una segmentación más rica que la umbralización binaria — puede separar regiones que se tocan o se superponen y que la umbralización fusionaría.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `surface` | `pygame.Surface` | Superficie fuente (RGB/RGBA, cualquier tamaño) |

**Salidas:** nueva `pygame.Surface` de tamaño idéntico. Una superposición de etiquetas coloreada por código donde cada segmento se rellena con un color único. Está pensada para **visualización** — no para procesamiento binario posterior.

Además, devuelve una tupla: `(label_surface, label_array)` donde `label_array` es el `np.ndarray int32` de etiquetas de componente.

**Tubería interna:**
```
surface → escala de grises → desenfoque (gaussiano, sigma=1.0 interno)
        → transformada de distancia (cv2.distanceTransform)
        → máscara de primer plano seguro (umbral al 70% de la distancia máxima)
        → región desconocida (dilate - sure_fg)
        → componentes conectados sobre sure_fg → marcadores
        → cv2.watershed(original_bgr, marcadores)
        → colorear cada etiqueta → devolver label_surface
```

**Restricciones:**

- Watershed es computacionalmente costoso. Usar en subsuperficies o a frecuencia reducida (cada 10+ fotogramas).
- La `label_surface` de salida usa 8 colores de tono distinto para visualizar las etiquetas. Si existen más de 8 segmentos, los colores se repiten.
- No modifica la entrada.

**Dependencias:** `numpy`, `opencv-python`

**Rendimiento:** ~8–15ms para una superficie de 320×224. Debe limitarse por fotograma o precalcularse.

**Ejemplo de uso:**

```python
# Precalcular al cargar el escenario:
label_surface, label_array = VisionTools.watershed_segment(self.background_surface)
self.segment_overlay = label_surface
self.segment_overlay.set_alpha(120)

# Dibujar cada fotograma (sin recalcular por fotograma):
surface.blit(self.segment_overlay, (0, 0))
```

---

## 13. Extracción de características

La extracción de características convierte una región de superficie en un vector numérico compacto (el "vector de características") que se puede usar como entrada de un clasificador en la Unidad IX.

### 13.1 `VisionTools.extract_features(surface, method='hog')`

**Propósito:** calcula un vector de características de una superficie usando el método especificado. Es el punto de integración principal entre VisionTools (Unidad VIII) y PatternRecognitionTools (Unidad IX).

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `surface` | `pygame.Surface` | RGB/RGBA, cualquier tamaño | Superficie fuente |
| `method` | `str` | `'hog'`, `'lbp'`, `'color_hist'`, `'combined'` | Método de extracción de características |

**Salidas:** `np.ndarray` de forma `(n,)` — un vector de características 1D. La longitud `n` depende del método.

| Método | Longitud de salida | Descripción |
|---|---|---|
| `'hog'` | Variable (depende del tamaño de superficie y los parámetros de HOG) | Histograma de gradientes orientados |
| `'lbp'` | 256 | Histograma de patrones binarios locales |
| `'color_hist'` | `bins * 3` (por defecto: 256 × 3 = 768) | Histograma de color por canal |
| `'combined'` | HOG + LBP + color_hist concatenados | Todas las características combinadas |

**Restricciones:**

- La superficie debe ser de al menos 8×8 píxeles para que HOG produzca características significativas.
- La superficie se redimensiona internamente a un tamaño canónico (32×32) antes de la extracción, para garantizar una longitud de vector consistente sin importar el tamaño de entrada. Este redimensionado es interno y no afecta a la superficie de entrada.
- No modifica la entrada.

**Dependencias:** `numpy`, `scikit-image` (`hog`, `local_binary_pattern`), `opencv-python` (redimensionado)

**Ejemplo de uso:**

```python
# Extraer características HOG de una región de 32×32 alrededor del jugador:
player_region = screen_surface.subsurface(pygame.Rect(
    player.rect.centerx - 16,
    player.rect.centery - 16,
    32, 32
))
features = VisionTools.extract_features(player_region, method='hog')
# features ya está listo para PatternRecognitionTools.classify()
```

---

### 13.2 `VisionTools.extract_hog(surface)`

**Propósito:** extrae características de Histograma de Gradientes Orientados (HOG). HOG captura la distribución de orientaciones de gradiente locales — un descriptor de forma robusto a cambios de iluminación y pequeñas distorsiones geométricas.

**Parámetros de HOG (fijos para consistencia entre todos los escenarios):**

| Parámetro | Valor |
|---|---|
| Orientaciones | 8 |
| Píxeles por celda | 8×8 |
| Celdas por bloque | 2×2 |
| Normalización de bloque | L2-Hys |
| Tamaño de entrada (canónico) | 32×32 |

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `surface` | `pygame.Surface` | Superficie fuente (redimensionada internamente a 32×32) |

**Salidas:** `np.ndarray` de forma `(n,)`. Para el tamaño canónico 32×32: `n = 4 * 4 * 2 * 2 * 8 = 512` dimensiones.

**Dependencias:** `scikit-image` (`skimage.feature.hog`), `opencv-python` (redimensionado)

---

### 13.3 `VisionTools.extract_lbp(surface)`

**Propósito:** extrae el histograma de Patrones Binarios Locales (LBP). LBP describe la textura comparando cada píxel con sus 8 vecinos y codificando el patrón como un número binario. El histograma de todos los códigos LBP describe el carácter de textura de la región.

**Parámetros de LBP:**

| Parámetro | Valor |
|---|---|
| Radio | 1 |
| Número de vecinos | 8 |
| Método | `'uniform'` (26 patrones uniformes + 1 no uniforme = 27 bins) |
| Salida | Histograma de 256 bins (bins estándar para `uniform` con radio 1, n_points 8) |

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `surface` | `pygame.Surface` | Superficie fuente (redimensionada internamente a 32×32) |

**Salidas:** `np.ndarray` de forma `(256,)` — histograma normalizado (suma = 1.0).

**Dependencias:** `scikit-image` (`skimage.feature.local_binary_pattern`), `numpy`

---

### 13.4 `VisionTools.extract_color_histogram(surface, bins=256)`

**Propósito:** extrae un histograma de color por canal concatenado. Calcula la distribución de frecuencia de los valores de intensidad para cada canal R, G, B por separado y los concatena en un único vector. Este descriptor captura la distribución de color general de la región.

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `surface` | `pygame.Surface` | RGB/RGBA | Superficie fuente |
| `bins` | `int` | `[4, 256]` | Número de bins de histograma por canal |

**Salidas:** `np.ndarray` de forma `(bins * 3,)` — normalizado (suma por canal = 1.0).

**Dependencias:** `numpy`

---

## 14. Cajas envolventes y contornos

### 14.1 `VisionTools.find_contours(mask_surface)`

**Propósito:** encuentra los bordes de todas las regiones de primer plano en una máscara binaria. Devuelve los contornos como una lista de arreglos de NumPy, donde cada arreglo contiene las coordenadas de píxel (x, y) de los puntos de contorno de una región.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `mask_surface` | `pygame.Surface` | Superficie de máscara binaria |

**Salidas:** `list[np.ndarray]` — cada elemento es un arreglo de forma `(N, 1, 2)` en formato de contorno de OpenCV, que representa las coordenadas (x, y) de los puntos de contorno.

**Dependencias:** `opencv-python` (`cv2.findContours`)

**Ejemplo de uso:**

```python
mask = VisionTools.threshold_binary(self.terrain_surface, 120)
contours = VisionTools.find_contours(mask)

# Dibujar todos los contornos en la superficie:
for contour in contours:
    for point in contour:
        x, y = point[0]
        pygame.draw.circle(surface, (255, 255, 0), (x, y), 1)
```

---

### 14.2 `VisionTools.bounding_boxes_from_mask(mask_surface)`

**Propósito:** extrae una lista de cajas envolventes `pygame.Rect`, una por región de primer plano conectada en la máscara. Esto convierte la salida geométrica de la segmentación directamente en rectángulos compatibles con colisión/renderizado de Pygame.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `mask_surface` | `pygame.Surface` | Superficie de máscara binaria |

**Salidas:** `list[pygame.Rect]`, uno por región de primer plano. Los rects están en coordenadas de píxel que coinciden con las dimensiones de mask_surface.

**Dependencias:** `numpy`, `opencv-python`

**Ejemplo de uso:**

```python
mask = VisionTools.threshold_binary(screen_copy, 150)
boxes = VisionTools.bounding_boxes_from_mask(mask)

# Dibujar cajas de depuración:
for rect in boxes:
    pygame.draw.rect(surface, (0, 255, 0), rect, 1)

# Usar como zonas de disparo:
for box in boxes:
    if box.colliderect(player.rect):
        event_bus.emit("SHOW_MESSAGE", text="¡Contacto con la región!", duration=1.0)
```

---

## 15. Validación de imagen

### `_validate_surface(surface)` — interno

| Comprobación | Excepción |
|---|---|
| Entrada `None` | `TypeError("VisionTools: surface cannot be None")` |
| No es `pygame.Surface` | `TypeError(f"VisionTools: expected pygame.Surface, got {type(surface)}")` |
| Dimensiones cero | `ValueError("VisionTools: surface has zero dimensions")` |

### `_validate_mask(surface)` — interno

Comprobación adicional para métodos que necesitan una máscara binaria:

| Comprobación | Acción |
|---|---|
| Valores de píxel fuera de {0, 255} | Se registra un aviso; la operación continúa (la entrada no binaria se procesa pero los resultados pueden ser inesperados) |

---

## 16. Restricciones de rendimiento

| Operación | Superficie 320×224 | Recomendación |
|---|---|---|
| `threshold_binary` | < 0.5ms | Seguro cada fotograma |
| `threshold_otsu` | < 1ms | Seguro cada fotograma |
| `morphological_erode/dilate` (k=3) | < 0.5ms | Seguro cada fotograma |
| `morphological_open/close` (k=3) | < 1ms | Seguro cada fotograma |
| `connected_components` | ~1.5ms | Cada 3 fotogramas |
| `analyze_regions` | ~2ms | Cada 5 fotogramas |
| `watershed_segment` | ~12ms | Cada 15 fotogramas o precalculado |
| `extract_hog` (canónico 32×32) | < 1ms | Seguro cada fotograma |
| `extract_lbp` (canónico 32×32) | < 0.5ms | Seguro cada fotograma |
| `find_contours` | < 1ms | Cada 3 fotogramas |
| `bounding_boxes_from_mask` | < 0.5ms | Seguro cada fotograma |

---

## 17. Correspondencia con la Unidad VIII

| Tema de la Unidad VIII | Método de VisionTools | Observable en el juego |
|---|---|---|
| Umbral binario | `threshold_binary()` | La máscara binaria dirige la generación de entidades o zonas de disparo |
| Método de Otsu | `threshold_otsu()` | Umbral adaptativo — el estudiante registra el valor calculado |
| Erosión morfológica | `morphological_erode()` | Eliminación de ruido de la máscara |
| Dilatación morfológica | `morphological_dilate()` | Relleno de huecos en la máscara |
| Apertura | `morphological_open()` | Eliminación de artefactos |
| Cierre | `morphological_close()` | Relleno de huecos |
| Componentes conectados | `connected_components()` | Etiquetar y contar regiones distintas |
| Análisis de regiones | `analyze_regions()` | Centroide, área, métricas de forma por región |
| Watershed | `watershed_segment()` | Superposición multi-región coloreada por código |
| Extracción de características | `extract_features()` | Vector de características listo para clasificación |

---

## 18. Correspondencia con la evaluación

| Evaluación | Unidad | Uso requerido de VisionTools | Evidencia |
|---|---|---|---|
| Examen práctico II | VIII | El estudiante aplica umbral + morfología + análisis de regiones | Demo en marcha + README |
| Entrega de Escenario 2 | VIII | Al menos un resultado de segmentación dirige el comportamiento del juego | Revisión de código + oral |
| Entrega de Escenario 3 | VIII+IX | La extracción de características alimenta un clasificador | Tubería demostrada en vivo |
| Presentación final | VIII | El estudiante explica matemáticamente el método de Otsu | Oral + demo |

---

## 19. Entregables del profesorado

1. **`src/framework/processing/vision_tools.py`** — Implementación completa, documentada y probada.
2. **`tests/test_vision_tools.py`** — Pruebas unitarias con salida visual PNG en `tests/output/vision/`.
3. **Escena demo (ver Documento 15)** — Demo interactiva de la Unidad VIII donde los estudiantes ajustan deslizadores de umbral y observan la salida de segmentación en tiempo real.
4. **Recorrido guiado de la tubería** — Una subescena comentada de Stage 0 donde se demuestra paso a paso la tubería completa (filtro → umbral → morfología → análisis de regiones).

---

## 20. Reutilización por parte de los estudiantes

Los estudiantes llaman a métodos de `VisionTools` para:

1. Segmentar regiones del contenido visual de su escenario.
2. Contar o ubicar regiones para determinar dónde deben generarse entidades o dónde deben dispararse eventos.
3. Extraer vectores de características para clasificación en tuberías de la Unidad IX.
4. Mostrar superposiciones de segmentación para depuración o visualización académica.

Los estudiantes no producen **ningún algoritmo de segmentación**. Producen **lógica de juego dirigida por los resultados de la segmentación**.

---

## 21. Evidencia de aprendizaje

Un estudiante ha demostrado el aprendizaje de la Unidad VIII cuando puede:

1. **Explicar** por qué eligió un valor de umbral específico (o por qué el método de Otsu era apropiado).
2. **Predecir** qué le hará a su máscara una operación morfológica antes de ejecutarla.
3. **Mostrar** un objeto `RegionInfo` en su README con el área, centroide y caja envolvente de una región de su escenario.
4. **Demostrar** un comportamiento de juego distinto en dos estados de escenario diferentes porque cambió el resultado de la segmentación.
5. **Documentar** la dimensionalidad del vector de características y qué representa cada grupo de valores.

---

## 22. Restricciones

| Restricción | Alcance |
|---|---|
| Los estudiantes nunca importan `cv2`, `scipy`, `skimage` | Todos los ficheros de estudiante |
| Los estudiantes nunca llaman a `cv2.threshold()`, `cv2.connectedComponents()`, `skimage.feature.hog()` directamente | Todos los ficheros de estudiante |
| `VisionTools` nunca llama a `EventBus`, `InputManager`, `AudioManager` | Aislamiento de procesamiento |
| `VisionTools` nunca modifica el estado de entidades | Interfaz basada en valores de retorno |
| Watershed no se usa cada fotograma sin limitación | Restricción de rendimiento |

---

## 23. Extensiones futuras

| Extensión | Descripción | Unidad objetivo |
|---|---|---|
| `optical_flow(surface_a, surface_b)` | Flujo óptico denso entre fotogramas | Unidad IX |
| `skeleton(mask_surface)` | Esqueletización morfológica | Unidad VIII |
| `convex_hull(mask_surface)` | Envolvente convexa de regiones de primer plano | Unidad VIII |
| `texture_segmentation(surface, method)` | Segmentación dirigida por textura basada en LBP | Unidad VIII |
| `depth_from_stereo(left, right)` | Mapa de disparidad estéreo | Fuera del alcance del curso |

---
## 🔗 Documentos relacionados

- [[11_FILTER_TOOLS_SPEC.md|Especificación de FilterTools]]
- [[13_PATTERN_RECOGNITION_SPEC.md|Especificación de reconocimiento de patrones]]

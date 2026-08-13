---
document_id: "LOI-FILTER-011"
title: "Legacy of InFest — Especificación de FilterTools"
aliases: ["Especificación de FilterTools", "Filter Tools Spec"]
tags: ["filter", "processing", "imagen"]
description: "Subsistema de procesamiento de imágenes de la Unidad VII"
source: "docs/11_FILTER_TOOLS_SPEC.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación de FilterTools

**ID del documento:** LOI-FILTER-011
**Versión:** 1.1.0
**Estado:** Oficial
**Compatibilidad:** Requiere `03_ARCHITECTURE.md`, `10_LIBRARIES_AND_DEPENDENCIES.md`
**Audiencia:** Profesor, ayudantes de cátedra, asistentes de programación con IA

> **AUD-455.** Traduce el documento completo (tenía el cuerpo en inglés y un
> resumen condensado en español al final que remitía «al documento original
> en inglés»; el Apéndice A que sigue a ese resumen ya estaba en español y no
> se toca). Corrige la ruta del módulo: es `src/framework/processing/filter_tools.py`,
> no `framework/processing/filter_tools.py` — falta el prefijo `src/` en las
> siete apariciones del documento. Verificado contra el fichero real: los
> nueve kernels de `get_standard_kernel` (§8.4) coinciden exactamente con
> `_STANDARD_KERNELS` en el código.

---

## 1. Visión general

`FilterTools` es el subsistema de procesamiento de imágenes del framework académico de Legacy of InFest. Encapsula todas las operaciones de procesamiento digital de imágenes que enseña la **Unidad VII** del programa del curso: análisis de histograma, ajuste de brillo y contraste, convolución, desenfoque gaussiano, detección de bordes de Sobel y detección de bordes de Canny.

Este subsistema es enteramente propiedad del profesorado y lo mantiene el profesorado. Los estudiantes interactúan con él exclusivamente a través de su API pública. Los estudiantes nunca importan `scipy`, `opencv-python` ni `scikit-image` directamente. Toda la complejidad de las bibliotecas de terceros queda oculta detrás de la interfaz de `FilterTools`.

El módulo está en:

```
src/framework/processing/filter_tools.py
```

---

## 2. Propósito académico

`FilterTools` existe para hacer que los conceptos de la Unidad VII sean **ejecutables y observables** dentro del entorno de juego en marcha. En vez de procesar imágenes abstractas en un notebook, los estudiantes aplican estas operaciones a superficies de juego reales — fondos, sprites, regiones de pantalla — y observan los resultados en tiempo real.

### 2.1 Objetivos de aprendizaje que soporta

| Objetivo | Mecanismo de FilterTools |
|---|---|
| Entender los histogramas como distribuciones de frecuencia de intensidades de píxel | `compute_histogram()` devuelve arreglos de frecuencia por canal |
| Aplicar manipulación de brillo como una transformación escalar | `adjust_brightness()` escala los valores de píxel uniformemente |
| Aplicar estiramiento de contraste vía manipulación de histograma | `adjust_contrast()` expande/comprime el rango de intensidad |
| Implementar la convolución como una operación kernel-superficie | `apply_kernel()` aplica una matriz de kernel arbitraria |
| Entender el desenfoque gaussiano como una convolución separable | `gaussian_blur()` usa un valor sigma parametrizado |
| Detectar bordes usando la magnitud del gradiente | `sobel_edge()` devuelve una superficie de magnitud de gradiente |
| Aplicar detección de bordes multi-etapa | `canny_edge()` aplica la tubería completa de Canny |

### 2.2 Principio de diseño

Todas las funciones de `FilterTools` son **funciones puras**: reciben una `pygame.Surface` y parámetros, y devuelven una nueva `pygame.Surface`. No mantienen estado, no modifican la superficie de entrada, y no emiten eventos ni llaman a ningún sistema del motor. Esto las hace seguras de usar en cualquier contexto y fáciles de probar de forma aislada.

---

## 3. Ubicación en el framework

```
src/framework/
└── processing/
    └── filter_tools.py          ← Este módulo
```

### 3.1 Posición en la jerarquía de dependencias

```
Escenarios (código de estudiante)
    ↓
src/framework/processing/filter_tools.py   ← Los estudiantes llaman a esto
    ↓
numpy, scipy, opencv-python                ← FilterTools llama a esto
    ↓
(Hardware / SO)
```

Los estudiantes están posicionados **por encima** de `filter_tools.py`. Lo llaman. Nunca van más allá.

---

## 4. Integración con la arquitectura

### 4.1 Cómo se conecta FilterTools al framework

`FilterTools` es un módulo utilitario sin estado. Se integra con el framework a través de los siguientes puntos de contacto:

| Punto de integración | Descripción |
|---|---|
| `src/framework/processing/color_tools.py` | `ColorTools.surface_to_array()` y `array_to_surface()` se usan internamente para conectar superficies de Pygame y arreglos de NumPy |
| Escenas de escenario (código de estudiante) | Los estudiantes llaman a métodos de `FilterTools` desde el `update()` o `draw()` de su escenario |
| `src/engine/utils/asset_loader.py` | Las superficies cargadas pueden pasarse a `FilterTools` para preprocesamiento durante la inicialización del escenario |
| Suite de pruebas unitarias (`tests/test_filter_tools.py`) | Cada método tiene una prueba unitaria aislada que guarda la salida visual como PNG para verificación académica |

### 4.2 Lo que FilterTools NO hace

| Acción prohibida | Razón |
|---|---|
| No llama a `EventBus` | Es un módulo de cómputo puro |
| No llama a `InputManager` | Sin lógica de interacción |
| No llama a `AudioManager` | Sin acoplamiento de audio |
| No accede al gestor de escenas | Sin conocimiento de escenas |
| No lee datos TMX | Sin acoplamiento de mapas |
| No modifica las superficies de entrada in situ | Todas las operaciones devuelven superficies nuevas |

---

## 5. Dependencias

| Biblioteca | Importación | Se usa para |
|---|---|---|
| `numpy` | `import numpy as np` | Representación en arreglo de datos de píxel, operaciones vectorizadas |
| `scipy.ndimage` | `from scipy.ndimage import convolve, gaussian_filter` | Convolución y desenfoque gaussiano |
| `cv2` (opencv-python) | `import cv2` | Sobel, Canny, operaciones de espacio de color |
| `pygame` | `import pygame` | Entrada/salida de superficies, puente `surfarray` |

**Los estudiantes nunca importan nada de lo anterior.** Todas las importaciones viven dentro de `filter_tools.py` (algunas, como `scipy`/`cv2`, están importadas de forma perezosa dentro de cada método, no al principio del fichero).

---

## 6. Diagrama de clase

```
FilterTools
│
├── [Histograma]
│   ├── compute_histogram(surface) → dict
│   └── histogram_equalize(surface) → Surface
│
├── [Brillo]
│   └── adjust_brightness(surface, factor) → Surface
│
├── [Contraste]
│   ├── adjust_contrast(surface, factor) → Surface
│   └── stretch_contrast(surface) → Surface
│
├── [Convolución]
│   ├── apply_kernel(surface, kernel) → Surface
│   └── get_standard_kernel(name) → np.ndarray
│
├── [Desenfoque gaussiano]
│   └── gaussian_blur(surface, sigma) → Surface
│
├── [Detección de bordes]
│   ├── sobel_edge(surface) → Surface
│   └── canny_edge(surface, low_threshold, high_threshold) → Surface
│
└── [Utilidades internas — privadas]
    ├── _surface_to_float_array(surface) → np.ndarray
    ├── _float_array_to_surface(array) → Surface
    ├── _to_opencv(surface) → np.ndarray
    ├── _from_opencv(array) → Surface
    └── _validate_surface(surface) → None
```

Todos los métodos públicos son **class methods** (decorados con `@classmethod`). `FilterTools` nunca se instancia. Es un espacio de nombres de operaciones.

---

## 7. Clase FilterTools

### 7.1 Responsabilidades

`FilterTools` es responsable de:

1. Aceptar objetos `pygame.Surface` como entrada.
2. Convertir superficies al formato de arreglo NumPy adecuado para la operación.
3. Aplicar la operación matemática usando la biblioteca adecuada.
4. Convertir el resultado de vuelta a una `pygame.Surface`.
5. Devolver la nueva superficie a quien la llamó.
6. Validar todas las entradas y lanzar excepciones descriptivas ante un mal uso.

`FilterTools` **no** es responsable de:

- Decidir cuándo aplicar filtros (eso es responsabilidad del escenario)
- Cachear superficies procesadas (eso es responsabilidad de `AssetLoader`)
- Programar actualizaciones de filtro a tasas de fotogramas reducidas (eso es responsabilidad del escenario)

---

## 8. API pública

### 8.1 Operaciones de histograma

#### `FilterTools.compute_histogram(surface)`

**Propósito:** calcula el histograma de frecuencia por canal de las intensidades de píxel de una superficie. Devuelve la distribución de valores R, G, B (y opcionalmente A) en todos los píxeles. Se usa para analizar el carácter tonal de una imagen — una herramienta diagnóstica fundamental de la Unidad VII.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `surface` | `pygame.Surface` | La superficie fuente. Cualquier tamaño. RGB o RGBA. |

**Salidas:**

| Clave | Tipo | Forma | Descripción |
|---|---|---|---|
| `'r'` | `np.ndarray` | `(256,)` | Conteo de frecuencia por nivel de intensidad del canal Rojo |
| `'g'` | `np.ndarray` | `(256,)` | Conteo de frecuencia por nivel de intensidad del canal Verde |
| `'b'` | `np.ndarray` | `(256,)` | Conteo de frecuencia por nivel de intensidad del canal Azul |
| `'luminance'` | `np.ndarray` | `(256,)` | Conteo de frecuencia por intensidad de luminancia en escala de grises |
| `'total_pixels'` | `int` | escalar | Conteo total de píxeles (ancho × alto) |

Devuelve un `dict` con las claves anteriores.

**Restricciones:**

- La superficie de entrada debe ser de al menos 1×1 píxel.
- La superficie debe ser convertible a formato RGB o RGBA.
- Esta función no modifica la superficie de entrada.

**Dependencias:** `numpy`, `pygame.surfarray`

**Ejemplo de uso:**

```python
# En un escenario de estudiante — calcular el histograma de una capa de fondo:
from src.framework.processing.filter_tools import FilterTools

hist = FilterTools.compute_histogram(self.background_surface)

# Comprobar la luminancia promedio:
avg_luminance = sum(i * hist['luminance'][i] for i in range(256)) / hist['total_pixels']

if avg_luminance < 80:
    event_bus.emit("SHOW_MESSAGE", text="La escena está muy oscura.", duration=2.0)
```

---

#### `FilterTools.histogram_equalize(surface)`

**Propósito:** aplica ecualización de histograma para mejorar el contraste redistribuyendo las intensidades de píxel para que cubran uniformemente el rango completo 0–255. Demuestra la relación entre la forma del histograma y la calidad de imagen percibida.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `surface` | `pygame.Surface` | Superficie fuente. RGB o RGBA. |

**Salidas:** una nueva `pygame.Surface` del mismo tamaño con luminancia ecualizada. Los canales de color se ecualizan de forma independiente para preservar las relaciones de tono (ecualización por canal).

**Restricciones:**

- Se aplica a superficies en escala de grises o en color.
- No modifica la superficie de entrada.
- Computacionalmente costosa en superficies grandes — usar en subsuperficies o a frecuencia reducida.

**Dependencias:** `numpy` únicamente.

> **AUD-455.** Esta ficha decía `opencv-python` (`cv2.equalizeHist`). El
> código real no importa `cv2` en este método: calcula el histograma y el CDF
> por canal a mano con `numpy` (`np.histogram`, `cumsum`, `np.ma.masked_equal`)
> — es la implementación explícita, no la de la biblioteca, a propósito:
> `histogram_equalize` es contenido de la Unidad VII, igual que `sobel_edge_propio`
> del Apéndice A. Verificado contra `src/framework/processing/filter_tools.py`.

**Ejemplo de uso:**

```python
# Preprocesar una baldosa de fondo oscura durante la inicialización del escenario:
equalized_bg = FilterTools.histogram_equalize(raw_background_surface)
self.background_surface = equalized_bg
```

---

### 8.2 Operaciones de brillo

#### `FilterTools.adjust_brightness(surface, factor)`

**Propósito:** multiplica todos los valores de canal de píxel por `factor`. Un valor de `1.0` es identidad. Valores por encima de `1.0` aclaran. Valores por debajo de `1.0` oscurecen. Un valor de `0.0` produce negro. Esta operación modela la multiplicación escalar de vectores de píxel — un concepto de la Unidad VII.

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `surface` | `pygame.Surface` | Cualquier tamaño, RGB/RGBA | Superficie fuente |
| `factor` | `float` | `[0.0, 4.0]` | Multiplicador de brillo |

**Salidas:** nueva `pygame.Surface` de tamaño idéntico. Valores de píxel saturados a `[0, 255]`.

**Restricciones:**

- `factor` fuera de `[0.0, 4.0]` lanza `ValueError`.
- El canal alfa se preserva sin modificar si la superficie tiene alfa.
- No modifica la superficie de entrada.

**Dependencias:** `numpy`, `pygame.surfarray`

**Nota de implementación interna (para asistentes de IA):**

```
arr = surfarray.array3d(surface).astype(float32)
arr = clip(arr * factor, 0, 255).astype(uint8)
result = surfarray.make_surface(arr)
si surface tiene alfa:
    result.set_alpha(surface.get_alpha())
return result
```

**Ejemplo de uso:**

```python
# Oscurecimiento de pantalla según la salud en un escenario de estudiante:
health_ratio = player.current_health / 5.0
dimmed = FilterTools.adjust_brightness(self.internal_surface_copy, factor=health_ratio)
surface.blit(dimmed, (0, 0))
```

---

### 8.3 Operaciones de contraste

#### `FilterTools.adjust_contrast(surface, factor)`

**Propósito:** aplica escalado lineal de contraste alrededor del punto medio (128). Un `factor` de `1.0` es identidad. Valores por encima de `1.0` aumentan el contraste (oscurecen más los oscuros, aclaran más los claros). Valores por debajo de `1.0` reducen el contraste (aplanan hacia el gris). Modela la transformación afín de píxel: `out = (in - 128) * factor + 128`.

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `surface` | `pygame.Surface` | Cualquier tamaño, RGB/RGBA | Superficie fuente |
| `factor` | `float` | `[0.0, 4.0]` | Multiplicador de contraste |

**Salidas:** nueva `pygame.Surface` de tamaño idéntico. Valores saturados a `[0, 255]`.

**Restricciones:**

- `factor` fuera de `[0.0, 4.0]` lanza `ValueError`.
- Alfa preservado si está presente.
- No modifica la entrada.

**Dependencias:** `numpy`, `pygame.surfarray`

**Ejemplo de uso:**

```python
# Modo visual de alto contraste disparado por un evento de escenario:
high_contrast_bg = FilterTools.adjust_contrast(self.background_surface, factor=2.5)
surface.blit(high_contrast_bg, camera_offset)
```

---

#### `FilterTools.stretch_contrast(surface)`

**Propósito:** realiza estiramiento de contraste min-max. Encuentra el valor mínimo y máximo real de píxel en la superficie y los remapea linealmente a 0 y 255. A diferencia de `adjust_contrast()`, esto es adaptativo — analiza la superficie antes de transformarla.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `surface` | `pygame.Surface` | Cualquier tamaño, RGB/RGBA |

**Salidas:** nueva `pygame.Surface` con contraste de rango completo. Cada canal se estira de forma independiente.

**Restricciones:**

- Si min == max (superficie uniforme), devuelve la superficie de entrada sin cambios y registra un aviso.
- No modifica la entrada.

**Dependencias:** `numpy`, `pygame.surfarray`

**Ejemplo de uso:**

```python
# Estirar una hoja de sprites de bajo contraste para claridad visual en modo depuración:
stretched = FilterTools.stretch_contrast(sprite_surface)
```

---

### 8.4 Operaciones de convolución

#### `FilterTools.apply_kernel(surface, kernel)`

**Propósito:** aplica un kernel de convolución arbitrario a la superficie. Es la forma generalizada de todos los filtros espaciales lineales. El kernel es un arreglo NumPy 2D (cuadrado, de tamaño impar). La operación es la convolución 2D discreta:

```
salida(x, y) = Σ Σ kernel(i, j) * entrada(x+i, y+j)
```

Se aplica de forma independiente a cada canal RGB.

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `surface` | `pygame.Surface` | Cualquier tamaño, RGB/RGBA | Superficie fuente |
| `kernel` | `np.ndarray` | Forma `(n, n)`, `n` impar, `n ≥ 3` | Kernel de convolución |

**Salidas:** nueva `pygame.Surface` de tamaño idéntico. Valores saturados a `[0, 255]`.

**Restricciones:**

- El kernel debe ser cuadrado: `kernel.shape[0] == kernel.shape[1]`.
- Las dimensiones del kernel deben ser impares: `kernel.shape[0] % 2 == 1`.
- Tamaño mínimo de kernel: 3×3. Tamaño máximo: 15×15 (restricción de rendimiento).
- No se exige que los valores del kernel sumen 1 (los kernels sin normalizar son válidos para detección de bordes).
- Manejo de borde: `mode='reflect'` (refleja los píxeles en los bordes).
- Lanza `ValueError` si la forma del kernel es inválida.

**Dependencias:** `numpy`, `scipy.ndimage.convolve`

**Ejemplo de uso:**

```python
import numpy as np
from src.framework.processing.filter_tools import FilterTools

# Kernel de realce (Unidad VII — convolución personalizada):
sharpen_kernel = np.array([
    [ 0, -1,  0],
    [-1,  5, -1],
    [ 0, -1,  0]
], dtype=np.float32)

sharpened = FilterTools.apply_kernel(self.background_surface, sharpen_kernel)
```

---

#### `FilterTools.get_standard_kernel(name)`

**Propósito:** devuelve un kernel de convolución predefinido y académicamente estándar por nombre. Da a los estudiantes definiciones de kernel correctas sin exigirles construirlas a mano. Cubre todos los kernels que se discuten en la Unidad VII.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `name` | `str` | Identificador de kernel (ver tabla abajo) |

**Kernels disponibles:**

| Nombre | Tamaño | Descripción | Tema académico |
|---|---|---|---|
| `'identity'` | 3×3 | Kernel identidad (no hace nada) | Línea base de comparación |
| `'sharpen'` | 3×3 | Realce basado en Laplaciano | Convolución |
| `'box_blur'` | 3×3 | Desenfoque promedio uniforme | Convolución |
| `'box_blur_5'` | 5×5 | Desenfoque uniforme más amplio | Convolución |
| `'edge_laplacian'` | 3×3 | Detección de bordes por Laplaciano | Detección de bordes |
| `'emboss'` | 3×3 | Efecto de relieve | Convolución |
| `'ridge'` | 3×3 | Detección de cresta/valle | Detección de bordes |
| `'sobel_x'` | 3×3 | Gradiente horizontal de Sobel | Sobel |
| `'sobel_y'` | 3×3 | Gradiente vertical de Sobel | Sobel |

**Salidas:** `np.ndarray` de la forma adecuada y dtype `float32`.

**Restricciones:**

- Lanza `KeyError` con la lista de nombres válidos si `name` no se reconoce.

**Dependencias:** `numpy`

**Ejemplo de uso:**

```python
kernel = FilterTools.get_standard_kernel('sharpen')
sharpened = FilterTools.apply_kernel(background, kernel)
```

---

### 8.5 Desenfoque gaussiano

#### `FilterTools.gaussian_blur(surface, sigma)`

**Propósito:** aplica desenfoque gaussiano a una superficie. El desenfoque se implementa como una convolución separable con un kernel gaussiano parametrizado por `sigma` (desviación estándar). Valores de `sigma` más altos producen un desenfoque más fuerte. Esto demuestra la función gaussiana como un kernel de ponderación espacial y su propiedad de separabilidad.

**Definición matemática:**

```
G(x, y) = (1 / 2πσ²) * exp(-(x² + y²) / 2σ²)
```

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `surface` | `pygame.Surface` | Cualquier tamaño, RGB/RGBA | Superficie fuente |
| `sigma` | `float` | `(0.0, 10.0]` | Desviación estándar de la gaussiana |

**Salidas:** nueva `pygame.Surface` de tamaño idéntico, desenfocada según el kernel gaussiano.

**Restricciones:**

- `sigma ≤ 0.0` lanza `ValueError`.
- `sigma > 10.0` lanza `ValueError` (protección de rendimiento — para desenfoque fuerte, aplicar iterativamente).
- Manejo de borde: `mode='reflect'`.
- Canal alfa preservado si está presente.
- Se aplica a cada canal RGB de forma independiente.

**Dependencias:** `numpy`, `scipy.ndimage.gaussian_filter`

**Nota de rendimiento:** para `sigma > 3.0`, el radio efectivo del kernel es grande. En superficies mayores a 320×224 píxeles, esto puede superar el presupuesto de 2ms por fotograma para uso en tiempo real. Aplicar a subsuperficies o a frecuencia reducida.

**Ejemplo de uso:**

```python
# Aplicar desenfoque a una capa de fondo para simular profundidad de campo:
blurred_far_bg = FilterTools.gaussian_blur(self.far_background, sigma=1.8)
surface.blit(blurred_far_bg, far_bg_offset)
```

---

### 8.6 Detección de bordes

#### `FilterTools.sobel_edge(surface)`

**Propósito:** aplica el operador de Sobel para detectar bordes calculando la magnitud del gradiente en cada píxel. El gradiente en las direcciones X e Y se calcula por separado usando los kernels de Sobel, y luego se combina como la magnitud euclidiana. Devuelve una superficie en **escala de grises** donde los píxeles brillantes representan bordes fuertes.

**Definición matemática:**

```
Gx = kernel_sobel_x ⊗ I
Gy = kernel_sobel_y ⊗ I
|G| = sqrt(Gx² + Gy²)
```

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `surface` | `pygame.Surface` | Superficie fuente. RGB o RGBA. |

**Salidas:** nueva `pygame.Surface` de tamaño idéntico. **Escala de grises** (los tres canales iguales). Blanco = borde fuerte. Negro = sin borde. El alfa no se preserva (la salida siempre es RGB).

**Restricciones:**

- La entrada se convierte a escala de grises internamente antes de aplicar Sobel. La información de color se descarta para el cálculo.
- La salida siempre es una superficie RGB (sin alfa), apta para mezclar sobre la escena.
- No modifica la entrada.

**Dependencias:** `numpy`, `opencv-python` (`cv2.Sobel`, `cv2.convertScaleAbs`)

**Ejemplo de uso:**

```python
# Renderizar una superposición de detección de bordes sobre la capa de terreno:
edge_map = FilterTools.sobel_edge(self.terrain_surface)
edge_map.set_alpha(140)  # Superposición semitransparente
surface.blit(edge_map, camera_offset)
```

---

#### `FilterTools.canny_edge(surface, low_threshold, high_threshold)`

**Propósito:** aplica el algoritmo de detección de bordes multi-etapa de Canny. Canny usa suavizado gaussiano, gradientes de Sobel, supresión no máxima y doble umbral con histéresis para producir bordes limpios y delgados. Devuelve una superficie binaria (blanco y negro).

**La tubería de Canny (interna):**

```
1. Convertir a escala de grises
2. Aplicar desenfoque gaussiano (sigma ≈ 1.4 — interno, fijo)
3. Calcular gradientes de Sobel (Gx, Gy)
4. Supresión no máxima a lo largo de la dirección del gradiente
5. Doble umbral: píxeles por encima de high_threshold → borde fuerte
                 píxeles entre low y high → borde débil (se conserva si toca uno fuerte)
                 píxeles por debajo de low_threshold → rechazado
6. Seguimiento de bordes por histéresis
```

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `surface` | `pygame.Surface` | RGB/RGBA, cualquier tamaño | Superficie fuente |
| `low_threshold` | `int` | `[1, 254]`, `< high_threshold` | Umbral de histéresis inferior |
| `high_threshold` | `int` | `[2, 255]`, `> low_threshold` | Umbral de histéresis superior |

**Pares de umbral recomendados:**

| Efecto | Bajo | Alto |
|---|---|---|
| Muy sensible (muchos bordes) | 20 | 60 |
| Equilibrado (por defecto) | 50 | 150 |
| Estricto (sólo bordes fuertes) | 100 | 200 |

**Salidas:** nueva `pygame.Surface` de tamaño idéntico. **Escala de grises binaria**: los píxeles son blancos (borde) o negros (sin borde). Alfa no preservado.

**Restricciones:**

- `low_threshold >= high_threshold` lanza `ValueError`.
- Ambos umbrales deben estar en el rango `[1, 255]`.
- La entrada se convierte a escala de grises internamente.
- La salida es RGB (no RGBA).

**Dependencias:** `numpy`, `opencv-python` (`cv2.Canny`)

**Ejemplo de uso:**

```python
# Detección de bordes de Canny aplicada a la región de un sprite enemigo:
enemy_region = self.stage_surface.subsurface(enemy.rect)
edges = FilterTools.canny_edge(enemy_region, low_threshold=50, high_threshold=150)
edges.set_alpha(180)
surface.blit(edges, enemy.rect.topleft)
```

---

## 9. Estándares de kernel

Todos los kernels de Legacy of InFest siguen estos estándares:

### 9.1 Formato

| Propiedad | Estándar |
|---|---|
| Tipo de dato | `np.float32` |
| Forma | Cuadrada: `(n, n)` |
| Dimensión | Impar: `n ∈ {3, 5, 7, 9, 11, 13, 15}` |
| Normalización | Opcional. Kernels normalizados (suma = 1.0) para desenfoque. Sin normalizar para detección. |
| Orientación | Convención NumPy por filas |

### 9.2 Definiciones de kernel estándar

**Identidad (3×3):**
```
[[0, 0, 0],
 [0, 1, 0],
 [0, 0, 0]]
```

**Desenfoque de caja (3×3):**
```
[[1/9, 1/9, 1/9],
 [1/9, 1/9, 1/9],
 [1/9, 1/9, 1/9]]
```

**Realce (3×3):**
```
[[ 0, -1,  0],
 [-1,  5, -1],
 [ 0, -1,  0]]
```

**Sobel X (3×3):**
```
[[-1,  0,  1],
 [-2,  0,  2],
 [-1,  0,  1]]
```

**Sobel Y (3×3):**
```
[[-1, -2, -1],
 [ 0,  0,  0],
 [ 1,  2,  1]]
```

**Borde Laplaciano (3×3):**
```
[[ 0,  1,  0],
 [ 1, -4,  1],
 [ 0,  1,  0]]
```

---

## 10. Estándares de formato de imagen

### 10.1 Requisitos de la superficie de entrada

| Propiedad | Valor requerido |
|---|---|
| Formato | `pygame.Surface` |
| Modo de píxel | RGB (24 bits) o RGBA (32 bits) |
| Tamaño mínimo | 1×1 píxel |
| Tamaño máximo | 1920×1080 (techo de rendimiento) |
| Profundidad de color | 8 bits por canal |

### 10.2 Formato de arreglo interno

| Etapa | Formato | Forma |
|---|---|---|
| Superficie de Pygame | `pygame.Surface` | — |
| Extracción con surfarray | `np.ndarray`, `uint8` | `(W, H, 3)` |
| Transpuesto para OpenCV | `np.ndarray`, `uint8` | `(H, W, 3)` |
| Cómputo en flotante | `np.ndarray`, `float32` | `(H, W, 3)` o `(H, W)` |
| Saturación y conversión del resultado | `np.ndarray`, `uint8` | `(W, H, 3)` |
| Reconstrucción con surfarray | `pygame.Surface` | — |

**La transposición de ejes entre Pygame y OpenCV es obligatoria y siempre se aplica dentro de `FilterTools`.** Los estudiantes nunca se topan con esta complejidad.

### 10.3 Garantía de la superficie de salida

Todos los métodos de `FilterTools` garantizan:

- La superficie de salida tiene las **mismas dimensiones** que la de entrada.
- La superficie de salida es un **objeto nuevo** — no comparte memoria con la de entrada.
- La profundidad de píxel de salida es **RGB de 24 bits**, salvo que se documente lo contrario (p. ej., la detección de bordes siempre devuelve RGB).

---

## 11. Validación de entrada

Todos los métodos públicos llaman a `_validate_surface(surface)` antes de procesar:

### `_validate_surface(surface)` — interno

| Comprobación | Excepción lanzada |
|---|---|
| `surface` es `None` | `TypeError("Surface cannot be None")` |
| `surface` no es `pygame.Surface` | `TypeError(f"Expected pygame.Surface, got {type(surface)}")` |
| El tamaño de la superficie es `(0, 0)` | `ValueError("Surface has zero dimensions")` |
| Superficie no bloqueada (durante operaciones de surfarray) | Gestionado internamente — la superficie nunca queda bloqueada |

Validación específica por parámetro:

| Método | Parámetro | Validación |
|---|---|---|
| `adjust_brightness` | `factor` | `0.0 ≤ factor ≤ 4.0` |
| `adjust_contrast` | `factor` | `0.0 ≤ factor ≤ 4.0` |
| `apply_kernel` | `kernel` | Cuadrado, impar, 3–15 |
| `gaussian_blur` | `sigma` | `0.0 < sigma ≤ 10.0` |
| `canny_edge` | umbrales | `1 ≤ low < high ≤ 255` |

---

## 12. Manejo de errores

`FilterTools` lanza excepciones descriptivas. Nunca devuelve `None` en silencio. Nunca registra y sigue adelante ante una entrada incorrecta.

| Excepción | Cuándo se lanza | Patrón del mensaje |
|---|---|---|
| `TypeError` | Tipo de argumento incorrecto | `"FilterTools.{method}: expected {type}, got {actual_type}"` |
| `ValueError` | Parámetro fuera de rango | `"FilterTools.{method}: {param} must be in [{min}, {max}], got {value}"` |
| `KeyError` | Nombre de kernel desconocido en `get_standard_kernel` | `"Unknown kernel '{name}'. Valid names: {list}"` |
| `RuntimeError` | Fallo interno de procesamiento (p. ej., error de OpenCV) | `"FilterTools.{method}: processing failed — {cv2_error_message}"` |

Un estudiante que recibe una excepción de `FilterTools` puede identificar de inmediato qué pasó de forma incorrecta. El mensaje de excepción siempre incluye el nombre del método y el valor inválido.

---

## 13. Restricciones de rendimiento

### 13.1 Presupuesto de tiempo

El presupuesto de fotograma del bucle de juego completo a 60 FPS es de **16.67ms**. Las operaciones de filtro consumen una parte de ese presupuesto.

| Operación | Tiempo típico (superficie 320×224) | Recomendación |
|---|---|---|
| `compute_histogram` | < 0.5ms | Seguro cada fotograma |
| `adjust_brightness` | < 0.5ms | Seguro cada fotograma |
| `adjust_contrast` | < 0.5ms | Seguro cada fotograma |
| `stretch_contrast` | < 1.0ms | Seguro cada fotograma |
| `apply_kernel` (3×3) | < 1.5ms | Seguro cada fotograma |
| `apply_kernel` (7×7) | ~3ms | Cada 3 fotogramas |
| `apply_kernel` (15×15) | ~8ms | Cada 10 fotogramas o precalculado |
| `gaussian_blur` (σ=1.0) | < 1ms | Seguro cada fotograma |
| `gaussian_blur` (σ=3.0) | ~2.5ms | Cada 3 fotogramas |
| `gaussian_blur` (σ=5.0) | ~5ms | Cada 8 fotogramas o precalculado |
| `sobel_edge` | ~2ms | Cada 3 fotogramas |
| `canny_edge` | ~3ms | Cada 5 fotogramas |

### 13.2 Estrategia de subsuperficie

Se espera que los estudiantes apliquen los filtros costosos a **subsuperficies** en vez de a la pantalla completa. Una subsuperficie se crea con `pygame.Surface.subsurface(rect)`.

```
# En vez de:
filtered = FilterTools.canny_edge(full_320x224_surface, 50, 150)  # ~3ms

# Preferir:
region = full_surface.subsurface(pygame.Rect(0, 0, 160, 112))     # Un cuarto de la superficie
filtered_region = FilterTools.canny_edge(region, 50, 150)         # ~0.8ms
```

### 13.3 Actualizaciones limitadas por fotograma

Para operaciones costosas que no necesitan precisión por fotograma, los estudiantes usan un contador de fotogramas:

```
# Concepto — actualizar el resultado del filtro cada 5 fotogramas:
if self.frame_count % 5 == 0:
    self.cached_edge_map = FilterTools.sobel_edge(self.background_surface)
self.frame_count += 1
surface.blit(self.cached_edge_map, (0, 0))
```

---

## 14. Correspondencia con la Unidad VII

| Tema de la Unidad VII | Método de FilterTools | Observable en el juego |
|---|---|---|
| Histograma | `compute_histogram()` | La salida numérica dirige la lógica del juego |
| Ecualización de histograma | `histogram_equalize()` | Mejora de calidad visual en superficies oscuras |
| Brillo | `adjust_brightness()` | La pantalla se atenúa/aclara según la salud o el tiempo |
| Contraste | `adjust_contrast()` | Modo visual de alto/bajo contraste |
| Estiramiento de contraste | `stretch_contrast()` | Un sprite de bajo contraste se vuelve visualmente claro |
| Convolución | `apply_kernel()` | Kernel personalizado aplicado al fondo |
| Desenfoque gaussiano | `gaussian_blur()` | Desenfoque de fondo que simula profundidad o niebla |
| Sobel | `sobel_edge()` | Superposición de bordes renderizada sobre terreno o enemigos |
| Canny | `canny_edge()` | Mapa de bordes binario que impulsa un efecto visual |

---

## 15. Correspondencia con la evaluación

| Evaluación | Unidad | Uso requerido de FilterTools | Evidencia |
|---|---|---|---|
| Examen práctico I | VII | El estudiante aplica al menos 2 operaciones de filtro distintas en su escenario | Demo del escenario en marcha + README |
| Entrega de Escenario 1 | VII | Al menos un filtro cambia el comportamiento del juego (no sólo lo visual) | README + revisión de código |
| Entrega de Escenario 2 | VII | Tubería de filtros con al menos una operación basada en kernel | Demo + explicación |
| Presentación final | VII | El estudiante explica en vivo la base matemática de un filtro | Explicación oral |

---

## 16. Entregables del profesorado

El profesorado entrega lo siguiente como parte de `FilterTools`:

1. **`src/framework/processing/filter_tools.py`** — Implementación completa, documentada y probada.
2. **`tests/test_filter_tools.py`** — Suite de pruebas unitarias. Cada prueba guarda un PNG de salida en `tests/output/filter/` para verificación visual.
3. **Stage 0, Zona F** — Demuestra `adjust_brightness`, `gaussian_blur` y `sobel_edge` en el contexto de un escenario en marcha.
4. **Escena demo (ver Documento 15)** — Una escena interactiva donde los estudiantes pueden ajustar los parámetros del filtro en tiempo real con controles de teclado.
5. **Tarjeta de referencia de kernels** — Un PDF de una página que muestra todos los kernels estándar con su efecto visual sobre una imagen de referencia.

---

## 17. Reutilización por parte de los estudiantes

Los estudiantes heredan la API completa de `FilterTools`. La reutilizan al:

1. Importar `FilterTools` desde `src.framework.processing.filter_tools`.
2. Pasar objetos `pygame.Surface` (sus fondos, sprites o regiones de pantalla) a los métodos de `FilterTools`.
3. Usar la superficie devuelta como superposición visual, reemplazo, o entrada para procesamiento adicional.
4. Usar la salida de `compute_histogram()` para tomar decisiones de lógica de juego.

Los estudiantes escriben **cero código de procesamiento de imágenes**. Escriben lógica de juego que usa los resultados del procesamiento de imágenes.

---

## 18. Evidencia de aprendizaje

Un estudiante ha demostrado el aprendizaje de la Unidad VII cuando puede:

1. **Explicar** la operación de convolución con sus propias palabras, usando el kernel de su escenario como ejemplo.
2. **Predecir** qué le hará su filtro a una superficie dada antes de ejecutarlo.
3. **Justificar** los valores de kernel que eligió para su efecto.
4. **Mostrar** en su escenario en marcha dónde el resultado del filtro cambia un comportamiento observable del juego.
5. **Describir** por qué aplicó el filtro con la frecuencia que eligió (cada fotograma, cada N fotogramas, precalculado).

---

## 19. Restricciones

| Restricción | Alcance |
|---|---|
| Los estudiantes nunca importan `scipy`, `cv2`, `skimage` ni `numpy` | Todos los ficheros de escenario de estudiante |
| Los estudiantes nunca llaman a `pygame.surfarray` directamente | Todos los ficheros de escenario de estudiante |
| Los estudiantes nunca llaman a `cv2.Canny()`, `cv2.Sobel()` ni `scipy.ndimage.convolve()` directamente | Todos los ficheros de escenario de estudiante |
| Los métodos de `FilterTools` nunca se llaman desde `engine/` | El motor no depende del framework |
| `FilterTools` nunca llama a `EventBus`, `InputManager` ni `AudioManager` | Aislamiento de procesamiento |
| Ningún método de FilterTools tiene efectos secundarios | Todas las salidas vía valor de retorno |

---

## 20. Extensiones futuras

Las siguientes extensiones están identificadas para posibles semestres futuros. **No están implementadas en la versión actual** y se documentan aquí sólo como marcadores de posición para la hoja de ruta del profesorado.

| Extensión | Descripción | Unidad objetivo |
|---|---|---|
| `motion_blur(surface, direction, amount)` | Desenfoque de movimiento direccional para sprites rápidos | Unidad VII |
| `chromatic_aberration(surface, offset)` | Desplazamiento de canal RGB para efecto de glitch visual | Unidad VII |
| `barrel_distortion(surface, coefficient)` | Efecto de distorsión de lente | Unidad VII |
| `apply_kernel_to_sprite(entity, kernel)` | Aplicar el filtro a la superficie de una entidad concreta | Unidad VII |
| `compute_optical_flow(surface_a, surface_b)` | Flujo óptico denso entre dos fotogramas | Unidad IX |

---
## 🔗 Documentos relacionados

- [[12_VISION_TOOLS_SPEC.md|Especificación de VisionTools]]
- [[13_PATTERN_RECOGNITION_SPEC.md|Especificación de reconocimiento de patrones]]

---

## Apéndice A — Sobel y Canny escritos a mano (F2.3)

### Por qué hay dos versiones de cada uno

| Función | Implementación | Para qué sirve |
|---|---|---|
| `sobel_edge` | `cv2.Sobel` | Producción. Rápida. |
| `sobel_edge_propio` | `src.framework.processing.edge_detection` | **Docencia.** Cada paso a la vista. |
| `canny_edge` | `cv2.Canny` | Producción. Rápida. |
| `canny_edge_propio` | `src.framework.processing.edge_detection` | **Docencia.** Los cinco pasos separados. |

La auditoría de julio de 2026 señaló el problema: en las Unidades VII y VIII
**Sobel y Canny son el contenido**, no una herramienta. Quien sólo ve
`cv2.Canny(gray, 50, 150)` aprende una API. La distancia entre «sé que existe
`cv2.Canny`» y «sé por qué la supresión no máxima adelgaza el borde» es la
asignatura entera.

Las dos versiones conviven a propósito. Comparar tu implementación con la de
referencia es parte de aprender — y descubrir que la tuya es cincuenta veces
más lenta también.

### Los pasos, y qué hace cada uno

**Sobel** (`edge_detection.sobel`)

1. `a_gris` — luminancia con los coeficientes ITU-R BT.601. Devuelve
   **float32**, no uint8: los pasos siguientes restan y dividen, y hacerlo en
   enteros de 8 bits desborda en silencio.
2. `convolucionar` con `KERNEL_X` y `KERNEL_Y` — la derivada en cada dirección.
   El borde se **replica**; rellenar con ceros inventaría un contorno en el
   marco de la imagen y Sobel detectaría el marco.
3. Magnitud: `hypot(gx, gy)`.

**Canny** (`edge_detection.canny`)

1. `suavizar` — gaussiana separable. Se empieza suavizando porque el gradiente
   amplifica el ruido: derivar una imagen ruidosa da bordes por todas partes.
2. `gradiente` — magnitud y dirección.
3. `supresion_no_maxima` — cada píxel se compara con sus dos vecinos **en la
   dirección del gradiente** y sobrevive sólo si es el máximo local. Es el paso
   que hace que Canny dé líneas y no manchas.
4. Doble umbral — por encima del alto, borde seguro; entre los dos, candidato.
5. `histeresis` — un candidato se acepta **sólo si toca a un borde seguro**.
   Resuelve el dilema de un umbral único: perder bordes tenues o aceptar ruido.

### Resultados medidos

Sobre una imagen de 240×180 con formas geométricas:

| | Coincidencia con OpenCV | Tiempo propio | Tiempo OpenCV | Factor |
|---|---|---|---|---|
| Sobel | 100 % | 1,72 ms | 0,10 ms | 17× |
| Canny | 98,3 % | 3,73 ms | 0,074 ms | 50× |

La coincidencia se comprueba en cada ejecución de la suite
(`tests/test_edge_detection.py`): OpenCV es el oráculo. Y hay una prueba que
verifica que la versión propia **sea más lenta** — si dejara de serlo, o está
mal o alguien cambió la referencia, y en los dos casos conviene enterarse.

### Ejercicios sugeridos

1. Cambia `KERNEL_X` por el de Prewitt (`[[-1,0,1],[-1,0,1],[-1,0,1]]`) y
   observa la diferencia en los bordes diagonales.
2. Salta la supresión no máxima en `canny` y mira el grosor del resultado.
3. Iguala `umbral_bajo` y `umbral_alto`: la histéresis deja de existir. ¿Qué
   se pierde?
4. Mide cuánto tarda `convolucionar` con un núcleo de 3×3, 5×5 y 9×9. ¿Crece
   como esperabas?

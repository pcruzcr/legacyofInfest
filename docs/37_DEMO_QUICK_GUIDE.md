# Legacy of InFest — Guía Rápida de Demos Académicas

**Document ID:** LOI-DEMO-QUICK-037  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** Estudiantes (referencia rápida para usar las 10 demos)

---

## 1. Acceso

Menú principal → **Academic Demos** → Seleccionar demo con `↑`/`↓` + `ENTER`

## 2. Controles Universales

| Tecla | Acción |
|---|---|
| `TAB` | Siguiente modo de operación |
| `←` `→` | Ajustar parámetro principal |
| `↑` `↓` | Ajustar parámetro secundario |
| `ESPACIO` | Cambiar superficie de origen |
| `F` | Congelar/descongelar superficie |
| `S` | Guardar PNG en `tests/output/demo/` |
| `R` | Reiniciar parámetros |
| `ESC` | Volver al menú de demos |

## 3. Resumen de las 10 Demos

### 3.1 Vector Lab — Unidad II

| Modo | Descripción |
|---|---|
| FREE MOVE | Dos puntos movibles; vector AB en vivo |
| CHASE | Persecución con `vec2_normalize()` |
| ORBIT | Punto orbita; ángulo del dot product |
| DISTANCE CHECK | Distancia con indicador de umbral |

Controles: `←→` mueve Player, `WASD` mueve Enemy, `N` toggle vector normalizado.

### 3.2 Transform Lab — Unidad II/III

| Modo | Descripción |
|---|---|
| TRANSLATE | Traslación con flechas |
| ROTATE | Rotación, matriz con seno/coseno |
| SCALE | Escalamiento X/Y |
| SHEAR | Deformación horizontal/vertical |
| COMPOSITE | Traslación+rotación vs rotación+traslación |

Controles: `←→` parámetro primario, `↑↓` secundario, `N` toggle matriz 3×3.

### 3.3 Curve Editor — Unidad III

| Modo | Descripción |
|---|---|
| BEZIER_QUAD | Bézier cuadrática (3 puntos) |
| BEZIER_CUBIC | Bézier cúbica (4 puntos) |
| BEZIER_HIGH | Bézier de alto grado |
| CATMULL_ROM | Spline que pasa por todos los puntos |
| BSPLINE | B-Spline de aproximación |
| DE_CASTELJAU | Animación paso a paso del algoritmo |

Controles: Mouse arrastra puntos, `+`/`-` agrega/elimina puntos, `D` toggle De Casteljau.

### 3.4 Interpolation Lab — Unidad III/IV

| Modo | Descripción |
|---|---|
| LERP | Interpolación lineal A→B con slider `t` |
| EASING CURVES | Gráfica de 10 funciones de easing |
| KEYFRAME ANIM | Animación multi-keyframe con easing |

Controles: `←→` ajusta `t`, `↑↓` cambia easing, `ESPACIO` auto-animación.

### 3.5 Color Theory — Unidad V

| Modo | Descripción |
|---|---|
| RGB EXPLORER | Sliders R/G/B, color en vivo, hex |
| HSV EXPLORER | H/S/V con conversión paso a paso |
| HSL EXPLORER | H/S/L con conversión paso a paso |
| CMYK EXPLORER | C/M/Y/K con preview RGB |
| ALPHA BLEND | Mezcla 2 capas con slider α y fórmula |
| CHALLENGE | Adivina el color objetivo con RGB |

Controles: `←→` ajusta canal, `↑↓` cambia canal, `SHIFT` toggle algoritmo.

### 3.6 Noise Lab — Unidad V/VIII

| Modo | Descripción |
|---|---|
| VALUE NOISE | Ruido de valor (bloquecito) |
| PERLIN NOISE | Ruido Perlin (suave) |
| FRACTAL NOISE | Multi-octava con persistencia/lacunarity |

Controles: `↑↓` selecciona parámetro, `←→` ajusta, `ESPACIO` randomiza semilla.

### 3.7 Collision Lab — Unidad VI

| Modo | Descripción |
|---|---|
| NO COLLISION | El jugador atraviesa todo |
| Y-FIRST | Resuelve Y primero (bug wall-climb) |
| X-FIRST | Resuelve X primero (correcto) |

Controles: `←→` mover, `ESPACIO`/`↑` saltar, `B` demo automática del bug.

### 3.8 Filter Demo — Unidad VII

| Modo | Descripción | Parámetros |
|---|---|---|
| HISTOGRAM | Barras R/G/B/Lum por canal | Threshold |
| BRIGHTNESS | `ajustar_brillo(factor)` | factor 0.0–4.0 |
| CONTRAST | `ajustar_contraste(factor)` | factor 0.0–4.0 |
| STRETCH | `estirar_contraste()` | — |
| KERNEL | `aplicar_kernel(kernel)` | Tipo (sharpen, blur, edge, etc.) |
| GAUSSIAN | `gaussian_blur(sigma)` | sigma 0.1–5.0 |
| SOBEL | `sobel_edge()` | — |
| CANNY | `canny_edge(low, high)` | low 0–255, high 0–255 |
| EQUALIZE | `histogram_equalize()` | — |

### 3.9 Vision Demo — Unidad VIII

| Modo | Descripción | Parámetros |
|---|---|---|
| THRESHOLD | Máscara binaria | threshold 0–255 |
| OTSU | Umbral automático Otsu | — |
| ERODE | Erosión | kernel_size 1–15 |
| DILATE | Dilatación | kernel_size 1–15 |
| OPEN | Apertura morfológica | kernel_size |
| CLOSE | Cierre morfológico | kernel_size |
| COMPONENTS | Componentes conectados | threshold |
| REGIONS | Análisis de regiones | threshold |
| WATERSHED | Segmentación watershed | — |
| FEATURES | Extracción de características | Método (HOG/LBP/color) |

### 3.10 Pattern Demo — Unidad IX

| Modo | Descripción |
|---|---|
| INFERENCE | Clasificación en tiempo real del área seleccionada |
| FEATURE_COMPARE | Vector de características vs muestra más cercana |
| CLASS_GRID | Grid 4×4 de muestras de entrenamiento |
| CONFUSION | Matriz de confusión del modelo cargado |
| PIPELINE | Pipeline visual paso a paso (filtro→visión→features→clasificar) |

Controles: `WASD` mueve rect de análisis, `+`/`-` cambia tamaño, `M` cambia método de特征, `L` carga modelo del estudiante.

## 4. Preparación para Exámenes

### Examen Práctico II (Unidades VII y VIII)

1. El profesor da una imagen objetivo (PNG guardado desde la demo)
2. Tienes 90 min para reproducir el resultado usando los controles de la demo
3. Documenta los parámetros exactos (sigma, threshold, kernel)
4. Guarda tu resultado con `S` y preséntalo como evidencia

### Examen Práctico III (Unidad IX)

1. El profesor da un dataset (`.npz`)
2. Entrenas un clasificador con hiperparámetros específicos
3. Cargas tu modelo en Pattern Demo con `L`
4. Capturas: matriz de confusión + inferencia en modo INFERENCE

## 5. Consejos

- Usa `F` para congelar la superficie y comparar resultados lado a lado
- La tecla `S` guarda PNGs en `tests/output/demo/` — úsalos para tu README
- `ESPACIO` cambia entre 5 superficies de origen (player, fondo, tileset, live capture, enemigo)
- Si una demo se pone lenta, cambia a una superficie más pequeña o reduce la frecuencia de actualización
- Los valores en amarillo indican que cambiaron en los últimos 0.3 segundos

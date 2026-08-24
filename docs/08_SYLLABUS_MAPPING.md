---
document_id: "LOI-SYLLABUS-008"
title: "Legacy of InFest — Mapeo del programa del curso"
aliases: ["Mapeo del programa del curso", "Syllabus Mapping"]
tags: ["silabo", "mapeo", "academico"]
description: "Mapeo de componente del framework a unidad del programa"
source: "docs/08_SYLLABUS_MAPPING.md"
date_processed: "2026-08-13"
---

# Legacy of InFest — Mapeo del programa del curso

**ID del documento:** LOI-SYLLABUS-008
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes de cátedra, estudiantes

> **AUD-455.** Traduce el documento (cuerpo en inglés, resumen condensado en
> español al final que remitía «al documento original en inglés»). Corrige:
> la ruta de módulo, que carecía del prefijo `src/` en todas sus apariciones;
> `classify_region(features, model)` en §10.2, que **no existe** en
> `VisionTools` ni en `PatternRecognitionTools` (verificado por AST) — la
> clasificación real es `PatternRecognitionTools.classify()`, ver
> `13_PATTERN_RECOGNITION_SPEC.md`; `engine/utils/spritesheet.py` en §5.2 y
> §7.2, retirado en AUD-098 — la carga de hojas de sprites real es
> `AssetLoader.load_sprite_sheet()` en `src/engine/utils/asset_loader.py`;
> y la referencia a `77_SYLLABUS_ALIGNMENT_AUDIT.md` en §12, un documento
> que no existe en este repositorio.

---

## 1. Visión general

Este documento mapea cada tema del programa del curso a su componente correspondiente del framework, el entregable del estudiante, la demostración en Stage 0, y los criterios de evaluación. Es la referencia autoritativa para calificar y para que los estudiantes decidan cómo implementar sus características académicas en sus escenarios.

Cada unidad del curso corresponde a un bloque de contenido académico. El framework da la infraestructura para aplicar cada tema. Los estudiantes deben implementar al menos una característica académica por unidad asignada a su escenario, documentarla en el README de su escenario, y demostrarla durante la presentación final.

---

## 2. Unidad I — Introducción a gráficas por computadora

### 2.1 Temas

- Historia y contexto de las gráficas por computadora
- Gráficos raster frente a vectoriales
- Tecnología de pantalla y cuadrículas de píxel
- El bucle de juego como sistema gráfico en tiempo real
- Tasa de fotogramas, delta time, y coherencia temporal

### 2.2 Componente del framework

| Componente | Fichero | Descripción |
|---|---|---|
| Bucle de la aplicación | `src/engine/core/app.py` | Implementa el bucle de juego con delta time |
| Reloj | `src/engine/core/clock.py` | `DeltaClock` gestiona la coherencia temporal |
| Superficie interna | `src/engine/core/app.py` | Búfer raster de 800×600 escalado a la pantalla |
| Escalado de pantalla | `src/engine/core/app.py` | Blit a escala entera a la ventana del SO |

### 2.3 Entregable del estudiante

Los estudiantes no implementan los conceptos de la Unidad I directamente en un escenario. La Unidad I la demuestra implícitamente el framework mismo. Se espera que los estudiantes documenten en el README de su escenario:

- La resolución interna usada (800×600)
- La tasa de fotogramas objetivo (60 FPS)
- Una explicación de cómo se usa `dt` (delta time) en al menos una entidad de su escenario

### 2.4 Demostración en Stage 0

Stage 0 sirve como la demostración de la Unidad I. Su existencia como un juego corriendo a 60 FPS estables, con render interno escalado a una pantalla moderna, es la demostración. La superposición de depuración (F1) muestra el contador de FPS actual.

### 2.5 Criterios de evaluación

| Criterio | Peso | Estándar |
|---|---|---|
| El escenario corre a 60 FPS estables | Aprobado/Reprobado | Sin caídas de fotogramas por debajo de 50 FPS en jugabilidad normal |
| Delta time aplicado a todo el movimiento | Aprobado/Reprobado | Presente el patrón `velocity * dt` |
| El README explica el bucle de juego | 10% | Descripción correcta del ciclo update/draw |

---

## 3. Unidad II — Sistemas de coordenadas, vectores, matrices, transformaciones

### 3.1 Temas

- Sistema de coordenadas cartesiano 2D
- Coordenadas de espacio de pantalla frente a espacio de mundo
- Aritmética vectorial (suma, resta, escalado, producto punto, normalización)
- Matrices de traslación y rotación
- Coordenadas homogéneas
- Transformación de cajas envolventes

### 3.2 Componente del framework

| Componente | Fichero | Descripción |
|---|---|---|
| Transformación mundo/pantalla | `src/framework/stage/camera.py` | `world_to_screen()` aplica el desplazamiento de cámara |
| Utilidades de vector | `src/engine/utils/math_utils.py` | `vec2_normalize`, `vec2_dot`, `vec2_distance` |
| Transformación de hitbox | `src/framework/entities/base_entity.py` | Transformación de rect local → mundo |
| Ángulo de proyectil (atan2) | `src/framework/entities/enemy_shooter.py` | Vector del disparador al jugador |
| Vector de retroceso del jugador | `src/framework/entities/player.py` | Vector de dirección desde la fuente de daño |

### 3.3 Entregable del estudiante

**Obligatorio:** al menos una entidad personalizada cuyo movimiento o comportamiento use aritmética vectorial explícita.

Ejemplos:
- Un enemigo que normaliza el vector hacia el jugador para moverse a velocidad constante sin importar la dirección
- Un proyectil que usa un vector de dirección calculado en vez de movimiento horizontal/vertical fijo en código
- Una zona de disparo que calcula la distancia al jugador con `vec2_distance` y escala un efecto según la proximidad

**Documentación obligatoria en el README:**
- La operación vectorial usada, expresada matemáticamente
- Qué función utilitaria del framework se usó
- Una captura o GIF mostrando el comportamiento

### 3.4 Demostración en Stage 0

- Zona E: el cálculo del ángulo `atan2` del disparador se muestra explícitamente en el mensaje de tutorial y en la superposición de depuración (dibuja una línea del disparador al jugador).
- Zona B: vector de retroceso del jugador calculado desde la posición de la fuente de daño.
- Modo depuración: todos los rects mostrados son rects en espacio local transformados a espacio de mundo.

### 3.5 Criterios de evaluación

| Criterio | Peso | Estándar |
|---|---|---|
| Normalización de vector correcta | 25% | La entidad se mueve a velocidad constante hacia el objetivo |
| Transformación de espacio local a mundo | 25% | Hitbox/hurtbox posicionadas correctamente en el mundo |
| Documentación matemática en el README | 30% | Fórmula escrita, no sólo descrita |
| Demo funcional en el escenario | 20% | Característica observable y funcional |

---

## 4. Unidad III — Curvas de Bézier, polinomios de Bernstein, B-Splines, NURBS, trayectorias

### 4.1 Temas

- Curvas paramétricas
- Polinomios base de Bernstein
- Algoritmo de de Casteljau
- Curvas de Bézier (grado 2 y 3)
- Funciones base de B-Spline y vectores de nudos
- NURBS (B-Splines racionales no uniformes)
- Parametrización de trayectorias y re-parametrización por longitud de arco

### 4.2 Componente del framework

| Componente | Fichero | Descripción |
|---|---|---|
| Cálculo de Bézier | `src/framework/processing/curve_tools.py` | `bezier(control_points, n_samples)` |
| Cálculo de B-Spline | `src/framework/processing/curve_tools.py` | `b_spline(points, degree, n)` |
| Cálculo de NURBS | `src/framework/processing/curve_tools.py` | `nurbs(points, weights, knots, degree, n)` |
| Muestreo de trayectoria | `src/framework/processing/curve_tools.py` | `sample_path(points, t)` |
| Catmull-Rom | `src/framework/processing/curve_tools.py` | `catmull_rom(points, n)` |
| Trayectoria Bézier de enemigo volador | `src/framework/entities/enemy_flying.py` | Usa `bezier()` para la ruta de patrulla |

### 4.3 Entregable del estudiante

**Obligatorio:** al menos una entidad o efecto ambiental que use una curva de `curve_tools.py`.

Ejemplos:
- Un enemigo volador cuya ruta sea un B-Spline por 5+ puntos de referencia definidos en el TMX
- Un proyectil que siga un spline Catmull-Rom en vez de una línea recta
- Un objeto ambiental (péndulo oscilante, plataforma oscilante) cuya posición se calcule desde un segmento de Bézier
- Un rastro visual (estela de luz) que dibuje los puntos muestreados de una curva NURBS

**Obligatorio:** el README del escenario debe incluir:
- Un gráfico o diagrama de la curva (dibujado a mano o generado)
- Los puntos de control usados
- El tipo de curva (Bézier, B-Spline, NURBS, Catmull-Rom) y su grado
- Una explicación de qué representa `t` en el contexto de la entidad

### 4.4 Demostración en Stage 0

- Zona D: Flying_02 usa una ruta Bézier de grado 3 por 4 puntos de referencia.
- Modo depuración (F1): renderiza la ruta muestreada como una serie de puntos, y el polígono de control como líneas finas.
- Mensaje de tutorial de la Zona D: explica la relación entre los puntos de control y la curva.

### 4.5 Criterios de evaluación

| Criterio | Peso | Estándar |
|---|---|---|
| Curva correctamente implementada | 30% | La entidad sigue la curva matemática (verificado contra la salida esperada) |
| Tipo de curva correcto para el grado | 20% | El grado coincide con el conteo de puntos de control o el vector de nudos |
| El comportamiento visual coincide con la documentación | 20% | La demo coincide con la descripción del README |
| Explicación matemática escrita | 30% | Base de Bernstein o vector de nudos correctamente descritos |

---

## 5. Unidad IV — Objetos, escenas, capas, sprites, búferes

### 5.1 Temas

- Conceptos de grafo de escena
- Arquitectura de renderizado por capas
- El sprite como quad texturizado
- Animación de sprites (ciclo de fotogramas)
- Doble búfer
- Ordenamiento en Z y llamadas de dibujo

### 5.2 Componente del framework

| Componente | Fichero | Descripción |
|---|---|---|
| Gestión de escenas | `src/engine/scene/scene_manager.py` | Pila de escenas, push/pop/replace |
| Pila de capas | TMX `BG_Far`, `BG_Mid`, etc. | Capas de renderizado ordenadas |
| Animación de sprites | `src/engine/utils/asset_loader.py` | `AssetLoader.load_sprite_sheet()`, ciclo de fotogramas |
| Doble búfer | `src/engine/core/app.py` | Blit de la superficie interna a la ventana |
| Orden de dibujo | `BaseEntity.layer` | Propiedad de orden en Z de las entidades |

### 5.3 Entregable del estudiante

**Obligatorio:** el escenario del estudiante debe usar correctamente un mínimo de tres capas de baldosas TMX (sin contar colisión y objetos). Al menos una entidad debe tener un sprite animado multi-fotograma creado por el estudiante o adaptado de la biblioteca de recursos.

**Documentación obligatoria en el README:**
- Un diagrama o tabla de la pila de capas usada en el escenario
- Una explicación de cómo funciona el ciclo de renderizado de doble búfer
- El conteo de fotogramas y FPS de al menos una animación propia

### 5.4 Demostración en Stage 0

- Todas las zonas: tres capas de fondo (BG_Far, BG_Mid, BG_Near) se desplazan a tasas de parallax distintas.
- Zona G: la animación del sprite de la antorcha demuestra una animación de objeto en bucle de 4 fotogramas.
- El modo depuración muestra los límites de capa como contornos coloreados.

### 5.5 Criterios de evaluación

| Criterio | Peso | Estándar |
|---|---|---|
| Mínimo 3 capas de baldosas presentes | Aprobado/Reprobado | El TMX tiene BG_Far, BG_Mid, Terrain como mínimo |
| El parallax se desplaza a las tasas correctas | 25% | Confirmación visual de profundidad |
| Sprite animado propio funcional | 35% | Los fotogramas ciclan a los FPS correctos |
| Arquitectura de capas documentada | 40% | El diagrama del README coincide con el TMX |

---

## 6. Unidad V — RGB, HSV, HSL, CMYK, transparencia, mezcla alfa, iluminación

### 6.1 Temas

- Modelo de color RGB y su representación en bytes
- Modelo de color HSV (Matiz, Saturación, Valor)
- Modelo de color HSL (Matiz, Saturación, Luminosidad)
- Modelo de color CMYK
- Canal alfa y transparencia
- Ecuaciones de mezcla alfa
- Mezcla aditiva y multiplicativa
- Iluminación 2D simulada

### 6.2 Componente del framework

| Componente | Fichero | Descripción |
|---|---|---|
| Conversiones de color | `src/framework/processing/color_tools.py` | `rgb_to_hsv`, `hsv_to_rgb`, `rgb_to_hsl`, etc. |
| Mezcla alfa | `src/framework/processing/color_tools.py` | `alpha_blend(src, dst, alpha)` |
| Aplicación de tinte | `src/framework/processing/color_tools.py` | `apply_tint(surface, color)` |
| Superficie a arreglo | `src/framework/processing/color_tools.py` | `surface_to_array()`, `array_to_surface()` |
| Alfa de Pygame | `pygame.Surface.set_alpha()` | Transparencia directa de superficie |

### 6.3 Entregable del estudiante

**Obligatorio:** al menos un efecto visual en el escenario del estudiante que demuestre una transformación de espacio de color o una operación de mezcla alfa aplicada a una superficie o entidad.

Ejemplos:
- Un tinte basado en salud: a medida que baja la salud del jugador, el tinte de pantalla pasa de neutral a rojo usando manipulación en HSV
- Una superposición de ciclo día/noche usando mezcla alfa (una superficie oscura mezclada sobre la escena)
- Un enemigo que cambia de fase de color (rotando el matiz en espacio HSV) como visual de "transición de fase"
- Un coleccionable que cicla valores de luminosidad en espacio HSL para crear un pulso de "brillo"

**Documentación obligatoria en el README:**
- El/los espacio(s) de color usado(s) y por qué se eligió ese espacio
- La fórmula matemática de la transformación aplicada
- Capturas de antes/después

### 6.4 Demostración en Stage 0

- Stage 0 no implementa un efecto de color directamente, pero el modo depuración renderiza superposiciones de hitbox y hurtbox usando colores translúcidos mezclados con alfa (demostrando `alpha_blend`).
- Zona F: el parpadeo de invencibilidad demuestra la alternancia de `set_alpha()`.

### 6.5 Criterios de evaluación

| Criterio | Peso | Estándar |
|---|---|---|
| Espacio de color correcto usado | 25% | HSV para rotación de matiz, HSL para luminosidad, etc. |
| Fórmula matemáticamente válida | 25% | Sin errores de fórmula (saturación, normalización de rango) |
| Efecto visual claramente observable | 30% | El efecto es visible y se comporta como se documenta |
| Fórmula y justificación en el README | 20% | Explica por qué ese espacio de color, no sólo qué es |

---

## 7. Unidad VI — Texturas, animación, interpolación, colisiones, interacción

### 7.1 Temas

- Fundamentos del mapeo de texturas
- La animación como selección de textura paramétrica en el tiempo
- Interpolación lineal (lerp)
- Funciones de easing (cuadrática, cúbica, seno)
- Detección de colisión AABB
- Patrones de eventos de interacción

### 7.2 Componente del framework

| Componente | Fichero | Descripción |
|---|---|---|
| Animación de sprites | `src/engine/utils/asset_loader.py` | Animación basada en fotogramas |
| Interpolación | `src/engine/utils/math_utils.py` | `lerp`, `ease_in_quad`, `ease_out_quad` |
| Colisión AABB | `src/framework/entities/player.py` | Resolución por eje separado |
| Eventos de interacción | `src/engine/core/event_bus.py` | Modelo de interacción publicación/suscripción |
| Lerp de cámara | `src/framework/stage/camera.py` | Seguimiento suave vía lerp |

### 7.3 Entregable del estudiante

**Obligatorio:** al menos un movimiento de entidad o animación de UI en el escenario que use una función de easing de `math_utils.py` (no sólo interpolación lineal).

Ejemplos:
- Una plataforma que se mueve entre dos posiciones usando `ease_in_out_quad` para desaceleración suave
- Un enemigo que se acerca al jugador usando `ease_in_cubic` (inicio lento, acercamiento rápido)
- Una animación de rebote de coleccionable usando `ease_out_bounce`
- Una animación de apertura de puerta cronometrada con easing

**Obligatorio:** al menos una interacción de colisión personalizada más allá de pared/suelo estándar (p. ej., una zona de disparo, un peligro que rebota, un bloque movible).

### 7.4 Demostración en Stage 0

- El seguimiento de cámara usa `lerp` para un movimiento de viewport suave.
- El banner de pantalla entra/sale deslizándose usando `ease_out_quad` y `ease_in_quad`.
- La activación de checkpoint usa lerp de alfa para el efecto de brillo de activación.

### 7.5 Criterios de evaluación

| Criterio | Peso | Estándar |
|---|---|---|
| Función de easing aplicada | 30% | No es `lerp` plano; usa una curva |
| Visualmente distinguible de lo lineal | 20% | El observador puede ver aceleración/desaceleración |
| Evento de interacción personalizado implementado | 30% | Más allá de la colisión estándar de suelo/pared |
| El README explica la matemática del easing | 20% | Descripción matemática correcta |

---

## 8. Unidad VII — Histograma, brillo, contraste, convolución, desenfoque gaussiano, Sobel, Canny

### 8.1 Temas

- Histogramas de imagen y su interpretación
- Ajuste de brillo y contraste
- La convolución como operación matemática
- Kernel de desenfoque gaussiano
- Operador de detección de bordes de Sobel
- Detección de bordes multi-etapa de Canny

### 8.2 Componente del framework

| Componente | Fichero | Descripción |
|---|---|---|
| Histograma | `src/framework/processing/filter_tools.py` | `compute_histogram(surface)` |
| Brillo | `src/framework/processing/filter_tools.py` | `adjust_brightness(surface, factor)` |
| Contraste | `src/framework/processing/filter_tools.py` | `adjust_contrast(surface, factor)` |
| Convolución | `src/framework/processing/filter_tools.py` | `apply_kernel(surface, kernel)` |
| Desenfoque gaussiano | `src/framework/processing/filter_tools.py` | `gaussian_blur(surface, sigma)` |
| Sobel | `src/framework/processing/filter_tools.py` | `sobel_edge(surface)` |
| Canny | `src/framework/processing/filter_tools.py` | `canny_edge(surface, low, high)` |

### 8.3 Entregable del estudiante

**Obligatorio:** al menos una aplicación en tiempo real o semi-real de un filtro de `filter_tools.py` a una superficie o capa de fondo.

Nota de rendimiento: la convolución de superficie completa cada fotograma a 60 FPS es computacionalmente costosa. Se espera que los estudiantes apliquen filtros con inteligencia (p. ej., actualizar cada 5 fotogramas, aplicar a una subsuperficie pequeña, precalcular para elementos estáticos).

Ejemplos:
- Aplicar detección de bordes de Sobel a una capa de baldosas de fondo y renderizar el mapa de bordes como superposición visual secundaria (p. ej., para la estética de un escenario "mundo digital")
- Aplicar desenfoque gaussiano a las capas de fondo detrás de un elemento de niebla semitransparente
- Calcular el histograma de brillo de la pantalla actual y usarlo para disparar un "evento de oscuridad" (reproducir un SFX de alarma) cuando el brillo promedio cae por debajo de un umbral
- Aplicar un mapa de bordes de Canny a un sprite enemigo y usar los datos de bordes para un efecto de renderizado de contorno estilizado

**Documentación obligatoria en el README:**
- Qué filtro se aplicó
- La matriz de kernel usada (si es convolución)
- La estrategia de actualización por fotograma (con qué frecuencia se aplica)
- Captura de antes/después de la superficie filtrada

### 8.4 Demostración en Stage 0

Stage 0 no aplica filtros en tiempo real (demuestra los sistemas centrales de jugabilidad). Sin embargo, el módulo `filter_tools.py` viene con pruebas unitarias ejecutables en `tests/test_filter_tools.py` que producen ficheros de salida visual demostrando cada filtro. Se espera que los estudiantes ejecuten estas pruebas y examinen la salida como parte de su estudio de la Unidad VII.

### 8.5 Criterios de evaluación

| Criterio | Peso | Estándar |
|---|---|---|
| Filtro aplicado al tipo de superficie correcto | 25% | Aplicado a `pygame.Surface`, convertido vía `surface_to_array` |
| Filtro matemáticamente correcto | 30% | Valores de kernel correctos; la salida coincide con el comportamiento esperado |
| Aplicación consciente del rendimiento | 20% | No aplicado cada fotograma a toda la pantalla sin justificación |
| Explicación de kernel + estrategia en el README | 25% | Kernel mostrado como matriz; frecuencia de actualización explicada |

---

## 9. Unidad VIII — Segmentación, umbral, regiones, morfología, watershed, extracción de características

### 9.1 Temas

- Umbralización binaria
- Umbral automático de Otsu
- Análisis de regiones conectadas
- Operaciones morfológicas (erosión, dilatación, apertura, cierre)
- Algoritmo de segmentación watershed
- HOG (Histograma de Gradientes Orientados)
- LBP (Patrones Binarios Locales)

### 9.2 Componente del framework

| Componente | Fichero | Descripción |
|---|---|---|
| Umbral binario | `src/framework/processing/vision_tools.py` | `threshold_binary(surface, thresh)` |
| Umbral de Otsu | `src/framework/processing/vision_tools.py` | `threshold_otsu(surface)` |
| Erosión morfológica | `src/framework/processing/vision_tools.py` | `morphological_erode(surface, k)` |
| Dilatación morfológica | `src/framework/processing/vision_tools.py` | `morphological_dilate(surface, k)` |
| Watershed | `src/framework/processing/vision_tools.py` | `watershed_segment(surface)` |
| Extracción de características | `src/framework/processing/vision_tools.py` | `extract_features(surface)` |

### 9.3 Entregable del estudiante

**Obligatorio:** al menos una aplicación de una operación de segmentación o morfología a una superficie, usada para dirigir el comportamiento del juego (no puramente visual).

Ejemplos:
- Aplicar umbral de Otsu a la pantalla actual; contar el número de píxeles oscuros; si supera un umbral, disparar un evento (mecánica de "luces apagadas")
- Aplicar erosión al canal alfa de un sprite para crear un efecto de muerte "disolviéndose"
- Usar segmentación watershed sobre una superficie de fondo para identificar y resaltar "zonas" distintas — renderizar los bordes de zona como superposición visual
- Extraer características HOG de una región del tileset y usar el vector de características como entrada de un clasificador en tiempo de ejecución

### 9.4 Demostración en Stage 0

Las pruebas unitarias en `tests/test_vision_tools.py` demuestran cada función con imágenes de salida guardadas. Los estudiantes deben ejecutar y estudiar estas pruebas.

### 9.5 Criterios de evaluación

| Criterio | Peso | Estándar |
|---|---|---|
| Función correcta de vision_tools | 25% | La herramienta correcta para la tarea correcta |
| La salida dirige el comportamiento del juego | 35% | El resultado de segmentación cambia el estado, no sólo se muestra |
| Manejo de casos límite | 20% | Qué pasa en superficies negras/blancas/uniformes |
| Explicación en el README | 20% | Algoritmo explicado, no sólo nombrado |

---

## 10. Unidad IX — Reconocimiento de patrones, clasificación, visualización, sistemas interactivos, visión por computadora

### 10.1 Temas

- Espacios de características y clasificación
- k Vecinos Más Cercanos (k-NN)
- Árboles de decisión y bosques aleatorios
- Entrenamiento e inferencia de modelos con scikit-learn
- Bucles de visión por computadora en tiempo real
- Sistemas interactivos dirigidos por el estado visual

### 10.2 Componente del framework

| Componente | Fichero | Descripción |
|---|---|---|
| Extracción de características | `src/framework/processing/vision_tools.py` | `extract_features(surface)` |
| Clasificación | `src/framework/processing/pattern_recognition_tools.py` | `PatternRecognitionTools.classify(features, model)` |
| Integración de scikit-learn | `pyproject.toml` | `scikit-learn` como dependencia obligatoria |
| Integración de OpenCV | `pyproject.toml` | `opencv-python` disponible |

### 10.3 Entregable del estudiante

**Obligatorio:** al menos un sistema en Stage 3 (el escenario final del estudiante) que aplique un clasificador entrenado a datos visuales del juego y use el resultado de clasificación para dirigir el comportamiento del juego.

Ésta es la característica académica de cierre del curso. Debe integrar conceptos de todas las unidades anteriores.

Ejemplos:
- Entrenar un clasificador k-NN fuera de línea sobre vectores de características de sprites (HOG o LBP). En tiempo de ejecución, clasificar sprites nuevos y generar distintos tipos de enemigo según la clasificación.
- Entrenar un árbol de decisión sobre características de histograma de pantalla. En tiempo de ejecución, clasificar el "ánimo" de la pantalla actual (clara/oscura/con mucho rojo) y cambiar la BGM y la iluminación en consecuencia.
- Usar OpenCV para procesar una pequeña región de pantalla (p. ej., alrededor del jugador) y detectar un patrón visual que dispare un evento de juego.
- Implementar un reconocedor de gestos en tiempo real usando el historial de entrada como vector de características, clasificando patrones de movimiento en acciones de jugador nombradas más allá del conjunto de control estándar.

**Documentación obligatoria en el README:**
- Descripción del dataset (qué se usó para entrenar el clasificador)
- Definición y dimensionalidad del vector de características
- Tipo de clasificador e hiperparámetros
- Precisión de entrenamiento y de prueba
- Cómo la salida de clasificación cambia el comportamiento del juego

### 10.4 Demostración en Stage 0

No se demuestra directamente en Stage 0. La Unidad IX se demuestra en `tests/test_pattern_recognition_tools.py`, que incluye un pequeño ejemplo de k-NN sobre datos de sprite generados.

### 10.5 Criterios de evaluación

| Criterio | Peso | Estándar |
|---|---|---|
| Clasificador entrenado y serializado | 20% | Modelo cargable en tiempo de ejecución |
| Características correctamente extraídas | 20% | Dimensionalidad correcta, sin fuga de datos |
| La clasificación dirige el comportamiento | 30% | Respuesta de juego distinta para cada clase |
| Precisión documentada | 15% | Precisión de entrenamiento y de prueba reportadas |
| Explicación de cierre en el README | 15% | Sistema de extremo a extremo descrito con claridad |

---

## 11. Tabla de mapeo consolidada

| Unidad | Resumen de tema | Módulo del framework | Escenario del estudiante | Zona de Stage 0 |
|---|---|---|---|---|
| I | Bucle de juego, raster, delta time | `app.py`, `clock.py` | Todos los escenarios (implícito) | Todo Stage 0 |
| II | Vectores, matrices, transformaciones | `math_utils.py`, `camera.py`, `base_entity.py` | Stage 1 o 2 | Zona E (atan2), superposición de depuración |
| III | Bézier, B-Spline, NURBS, trayectorias | `curve_tools.py`, `enemy_flying.py` | Stage 1 o 2 | Zona D (Flying_02) |
| IV | Escenas, capas, sprites, búferes | `scene_manager.py`, `asset_loader.py` | Todos los escenarios | Todas las zonas |
| V | Espacios de color, alfa, iluminación | `color_tools.py` | Stage 1 o 2 | Superposiciones de depuración |
| VI | Animación, interpolación, colisión | `math_utils.py`, `player.py`, `camera.py` | Stage 1 o 2 | Cámara, banner, checkpoint |
| VII | Filtros, convolución, bordes | `filter_tools.py` | Stage 2 o 3 | Pruebas unitarias |
| VIII | Segmentación, morfología, características | `vision_tools.py` | Stage 2 o 3 | Pruebas unitarias |
| IX | Clasificación, visión por computadora | `pattern_recognition_tools.py`, scikit-learn | Stage 3 | Pruebas unitarias |

---

## 12. Asignación de hito a unidad

Las etiquetas «Stage 1», «Stage 2» y «Stage 3» usadas en este y otros documentos del framework **no** se refieren a tres escenarios distintos asignados a un mismo estudiante. Según el programa oficial, Legacy of InFest es un **proyecto individual**: cada estudiante elige exactamente **un** Escenario o Jefe en la Clase 1 (ver `21_COURSE_SCHEDULE.md`) y desarrolla esa única entrega a través de tres hitos acumulativos de completitud, cada uno correspondiente a una Evaluación Práctica oficial:

| Etiqueta interna (heredada) | Nombre oficial | Clase | Unidades acumuladas demostradas |
|---|---|---|---|
| «Stage 1» | Evaluación Práctica I – Prototipo Funcional | Clase 5 | II, III, IV, V |
| «Stage 2» | Evaluación Práctica II – Vertical Slice | Clase 8 | + VI, VII |
| «Stage 3» | Evaluación Práctica III – Integración Final | Clase 11 | + VIII, IX |

El único Escenario o Jefe asignado a un estudiante debe demostrar las Unidades II–V para la Evaluación Práctica I, sumar las Unidades VI–VII para la Evaluación Práctica II, y sumar las Unidades VIII–IX para la Evaluación Práctica III — todo dentro de la **misma** pieza de trabajo, elaborada progresivamente. La Unidad I es fundacional y se demuestra implícitamente desde el inicio (ver la Sección 2 de este documento).

---
## 🔗 Documentos relacionados

- [[14_PROFESSOR_DELIVERABLE_MATRIX.md|Matriz de entregables del profesorado]]
- [[21_COURSE_SCHEDULE.md|Calendario del curso]]

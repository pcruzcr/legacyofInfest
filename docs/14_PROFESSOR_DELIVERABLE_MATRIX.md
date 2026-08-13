---
document_id: "LOI-DELIVERABLE-014"
title: "Legacy of InFest — Matriz de entregables del profesorado"
aliases: ["Matriz de entregables del profesorado", "Professor Deliverable Matrix"]
tags: ["entregable", "academico", "matriz"]
description: "Trazabilidad completa del programa al framework y a la evaluación"
source: "docs/14_PROFESSOR_DELIVERABLE_MATRIX.md"
date_processed: "2026-08-13"
---

# Legacy of InFest — Matriz de entregables del profesorado

**ID del documento:** LOI-MATRIX-014
**Versión:** 1.1.0
**Estado:** Oficial
**Compatibilidad:** Todos los documentos LOI
**Audiencia:** Profesor, ayudantes de cátedra, comité académico universitario

> **AUD-455.** Traduce el documento. Corrige la ruta de módulo, que
> carecía del prefijo `src/` en las tablas de §3–§11 (§13 y §14 ya lo
> tenían, de una corrección AUD-150 anterior); quita cuatro referencias a
> `77_SYLLABUS_ALIGNMENT_AUDIT.md`, que no existe en este repositorio
> (§12, §13, §14); y corrige §11.1: `extract_hog()`, `extract_lbp()` y
> `extract_color_histogram()` **no existen** en `PatternRecognitionTools`
> — viven en `VisionTools` (ver `13_PATTERN_RECOGNITION_SPEC.md` §7 y
> `12_VISION_TOOLS_SPEC.md` §13).

<!-- cita-historica -->
> **Corrección AUD-150 — nombres que este documento daba por existentes.**
> Comprobados uno por uno contra el código. Ninguno rompe nada al jugar; todos
> engañan a quien lea el documento para programar.
>
> * `SpriteSheet` y `AnimationController` **no existen como clases.** La carga de hojas la hace `AssetLoader`, y la animación vive dentro de cada entidad (`_advance_animation`, `_sprite_frames`). La rúbrica sigue siendo válida —lo que se evalúa es que el estudiante anime su entidad—; lo que hay que leer distinto es dónde mirar el código.
> * `OneWay_` no es un prefijo de nada. Las plataformas atravesables se declaran con el tipo «Platform» en la capa `Collision`.
<!-- /cita-historica -->

## 1. Visión general

Este documento da trazabilidad completa entre el programa del curso y el framework de Legacy of InFest. Para cada tema de cada unidad del curso, define qué entrega el profesorado, qué produce el estudiante, qué componente del framework se usa, qué bibliotecas participan, dónde aparece el concepto en Stage 0, qué debe demostrar un escenario de estudiante, y cómo se evalúa.

Esta matriz es la referencia autoritativa para:
- Diseñar instrumentos de evaluación
- Revisar entregas de escenario de estudiante
- Auditar la completitud del framework
- Alinear el contenido del curso con los entregables de software

---

## 2. Guía de lectura

Cada sección de unidad contiene una **tabla de entregables** que cubre cada tema, seguida de un **resumen de evidencia de aprendizaje** para la unidad como un todo.

| Columna | Significado |
|---|---|
| **Tema** | Nombre exacto del tema del programa |
| **Entrega el profesorado** | Qué existe antes de que el estudiante empiece |
| **Entrega el estudiante** | Qué debe producir el estudiante |
| **Componente del framework** | Módulo en `src/engine/` o `src/framework/` que lo lleva |
| **Bibliotecas** | Bibliotecas de terceros involucradas (ocultas a los estudiantes) |
| **Ejemplo en Stage 0** | Dónde se demuestra en el escenario del profesorado |
| **Escenario del estudiante** | Qué escenario se espera que lo demuestre |
| **Evaluación** | Qué instrumento calificado lo cubre |
| **Referencia de documento** | Qué documento de especificación lo cubre en detalle |

---

## 3. Unidad I — Introducción a gráficas por computadora

### 3.1 Tabla de entregables

| Tema | Entrega el profesorado | Entrega el estudiante | Componente del framework | Bibliotecas | Ejemplo en Stage 0 | Escenario del estudiante | Evaluación | Referencia |
|---|---|---|---|---|---|---|---|---|
| Historia de CG / raster frente a vectorial | Diapositivas de clase + el framework como sistema raster en marcha | Sección del README explicando la elección de resolución interna | `src/engine/core/app.py` (superficie interna) | `pygame-ce` | Todo Stage 0 corriendo | Todos los escenarios | Examen I (teoría) | `03_ARCHITECTURE.md` |
| Tecnología de pantalla y cuadrículas de píxel | Constantes de `settings.py` (`INTERNAL_WIDTH`, `INTERNAL_HEIGHT`, `TILE_SIZE`) | El README documenta la cuadrícula de baldosas usada en el TMX | `src/engine/core/settings.py` | `pygame-ce` | La superposición de depuración muestra la cuadrícula de píxeles (F1) | Todos los escenarios | Examen I | `03_ARCHITECTURE.md` §2.1 |
| El bucle de juego como sistema gráfico en tiempo real | Bucle principal `App.run()` con delta time | El README explica el ciclo update/draw en su escenario | `src/engine/core/app.py`, `src/engine/core/clock.py` | `pygame-ce` | Escenario en marcha — 60 FPS observables | Todos los escenarios | Examen I + README del escenario | `03_ARCHITECTURE.md` §5 |
| Tasa de fotogramas, delta time, coherencia temporal | `DeltaClock.tick()` devolviendo `dt` | Todo el movimiento de entidad usa `velocity * dt`; documentado | `src/engine/core/clock.py` | `pygame-ce` | Todas las entidades de Stage 0 se mueven correctamente a cualquier FPS | Todos los escenarios | Revisión de código | `03_ARCHITECTURE.md` §2.1 |
| Sistemas de coordenadas (introducción al espacio de pantalla) | `Camera.world_to_screen()` y `Camera.screen_to_world()` | El escenario usa el desplazamiento de cámara correctamente en todo el dibujo de entidades | `src/framework/stage/camera.py` | `pygame-ce` | Todas las entidades de Stage 0 se dibujan en las posiciones de pantalla correctas | Todos los escenarios | Revisión de código | `03_ARCHITECTURE.md` §2.8 |

### 3.2 Evidencia de aprendizaje — Unidad I

Un estudiante demuestra dominio de la Unidad I cuando su escenario:
- Corre de forma estable a 60 FPS en la máquina de desarrollo del curso.
- Aplica `dt` a todos los movimientos basados en velocidad (cero valores de píxel-por-fotograma fijos en código).
- Documenta el bucle de juego, la tasa de fotogramas, y el sistema de coordenadas en el README de su escenario.

---

## 4. Unidad II — Sistemas de coordenadas, vectores, matrices, transformaciones

### 4.1 Tabla de entregables

| Tema | Entrega el profesorado | Entrega el estudiante | Componente del framework | Bibliotecas | Ejemplo en Stage 0 | Escenario del estudiante | Evaluación | Referencia |
|---|---|---|---|---|---|---|---|---|
| Sistema de coordenadas cartesiano 2D | Explicación de coordenadas de mundo frente a pantalla en el doc de arquitectura; `Camera.world_to_screen()` | El README del escenario explica espacio de mundo frente a espacio de pantalla | `src/framework/stage/camera.py` | `pygame-ce` | El modo depuración muestra coordenadas | Stage 1 | Examen I + README | `03_ARCHITECTURE.md` §2.8 |
| Aritmética vectorial | `math_utils.py`: `vec2_normalize`, `vec2_dot`, `vec2_distance`, `vec2_length` | Al menos una entidad propia usa matemática vectorial explícita para movimiento | `src/engine/utils/math_utils.py` | `pygame-ce`, `numpy` | Cálculo de atan2 del disparador de la Zona E | Stage 1 | Práctica I | `03_ARCHITECTURE.md` §2.6 |
| Matrices de traslación y rotación | Transformación de hitbox del jugador (local → mundo, documentada en la especificación del jugador) | El README documenta la transformación local→mundo de su hitbox propia | `src/framework/entities/base_entity.py` | `pygame-ce` | Modo depuración: hitboxes en posiciones de mundo correctas | Stage 1 | Revisión de código + README | `04_PLAYER_SPEC.md` §12 |
| Coordenadas homogéneas | Documentadas en la especificación del jugador §13.4 como ilustración de matriz | El estudiante documenta la forma matricial de la traslación de su entidad | `src/framework/entities/base_entity.py` | `numpy` | Comentarios de fuente de Stage 0 | Stage 1 | Examen I (teoría) | `04_PLAYER_SPEC.md` §13.4 |
| Normalización de vector para movimiento | `vec2_normalize()` en math_utils | Una entidad propia se mueve hacia el objetivo a velocidad constante usando normalización | `src/engine/utils/math_utils.py` | `numpy` | Vector de dirección del retroceso del jugador | Stage 1 | Práctica I | `03_ARCHITECTURE.md` §2.6 |
| Producto punto y distancia | `vec2_dot()`, `vec2_distance()` | Un rango de detección propio usa el cálculo de distancia | `src/engine/utils/math_utils.py` | `numpy` | Zona de detección de enemigo | Stage 1 | Práctica I | `05_ENEMY_SPEC.md` §10.1 |
| Transformación de cajas envolventes | `_update_rects()` en BaseEntity | La entidad propia del estudiante actualiza correctamente hitbox/hurtbox en espacio de mundo | `src/framework/entities/base_entity.py` | `pygame-ce` | Todas las entidades de Stage 0 | Stage 1 | Revisión de código | `04_PLAYER_SPEC.md` §10, §11 |

### 4.2 Evidencia de aprendizaje — Unidad II

Un estudiante demuestra dominio de la Unidad II cuando puede:
- Escribir la matriz de traslación del desplazamiento de hitbox de su entidad en su README.
- Mostrar una entidad propia usando `vec2_normalize()` para persecución a velocidad constante.
- Explicar verbalmente la diferencia entre coordenadas de espacio de mundo y de pantalla en la presentación final.

---

## 5. Unidad III — Curvas de Bézier, B-Splines, NURBS, trayectorias

### 5.1 Tabla de entregables

| Tema | Entrega el profesorado | Entrega el estudiante | Componente del framework | Bibliotecas | Ejemplo en Stage 0 | Escenario del estudiante | Evaluación | Referencia |
|---|---|---|---|---|---|---|---|---|
| Curvas paramétricas | Módulo `CurveTools` con todas las funciones de curva | Al menos una entidad o efecto sigue una ruta paramétrica calculada | `src/framework/processing/curve_tools.py` | `numpy` | Zona D Flying_02 (ruta Bézier) | Stage 1 | Práctica I + README | `03_ARCHITECTURE.md` §2.9 |
| Polinomios base de Bernstein | `CurveTools.bezier()` implementa la base de Bernstein | El README incluye la fórmula de Bernstein y los puntos de control del estudiante | `src/framework/processing/curve_tools.py` | `numpy` | El modo depuración de la Zona D muestra el polígono de control | Stage 1 | Examen I (teoría) + README | `03_ARCHITECTURE.md` §2.9 |
| Algoritmo de de Casteljau | Implementado dentro de `bezier()` | No se exige implementarlo — se exige explicarlo en el README | `src/framework/processing/curve_tools.py` | `numpy` | Comentarios de fuente de Stage 0 | Stage 1 | README | `03_ARCHITECTURE.md` §2.9 |
| Curvas B-Spline | `CurveTools.b_spline()` | El estudiante demuestra una ruta B-Spline (≥ 5 puntos de control) | `src/framework/processing/curve_tools.py` | `numpy` | No está en Stage 0 — primer uso del estudiante | Stage 1 o 2 | Entrega de escenario | `03_ARCHITECTURE.md` §2.9 |
| NURBS | `CurveTools.nurbs()` | Avanzado opcional: el estudiante demuestra NURBS con pesos propios | `src/framework/processing/curve_tools.py` | `numpy` | No está en Stage 0 | Stage 2 (opcional) | Bono | `03_ARCHITECTURE.md` §2.9 |
| Splines Catmull-Rom | `CurveTools.catmull_rom()` | El estudiante puede usarlo para interpolación suave entre puntos de referencia | `src/framework/processing/curve_tools.py` | `numpy` | No está en Stage 0 | Stage 1 | Entrega de escenario | `03_ARCHITECTURE.md` §2.9 |
| Parametrización de trayectoria | `CurveTools.sample_path(path, t)` | La entidad avanza por la ruta usando `t` dirigido por velocidad | `src/framework/processing/curve_tools.py` | `numpy` | Zona D: recorrido de ruta de Flying_02 | Stage 1 | Revisión de código | `03_ARCHITECTURE.md` §2.9 |

### 5.2 Evidencia de aprendizaje — Unidad III

Un estudiante demuestra dominio de la Unidad III cuando puede:
- Presentar un diagrama de sus puntos de control y la curva resultante.
- Explicar qué representa `t` en su implementación de recorrido de ruta.
- Describir por escrito la diferencia entre Bézier, B-Spline, y Catmull-Rom para su caso de uso específico.

---

## 6. Unidad IV — Objetos, escenas, capas, sprites, búferes

### 6.1 Tabla de entregables

| Tema | Entrega el profesorado | Entrega el estudiante | Componente del framework | Bibliotecas | Ejemplo en Stage 0 | Escenario del estudiante | Evaluación | Referencia |
|---|---|---|---|---|---|---|---|---|
| Conceptos de grafo de escena | `SceneManager` con push/pop/replace | El escenario del estudiante implementa `BaseScene` correctamente con `on_enter`, `update`, `draw` | `src/engine/scene/scene_manager.py`, `src/engine/scene/base_scene.py` | `pygame-ce` | Todas las escenas del flujo del juego | Todos los escenarios | Revisión de código | `03_ARCHITECTURE.md` §2.2 |
| Renderizado por capas | Sistema de capas TMX (de BG_Far a FG_Overlay) | El mapa TMX tiene todas las capas obligatorias; el parallax es observable visualmente | `src/framework/stage/stage_loader.py`, `pyscroll` | `pygame-ce`, `pyscroll`, `pytmx` | Todas las zonas: desplazamiento de parallax | Todos los escenarios | Revisión de TMX + demo | `06_TMX_SPEC.md` §3 |
| El sprite como quad texturizado | `AssetLoader` (AUD-150: no hay ninguna clase de hoja de sprites) | Al menos un sprite animado propio creado por el estudiante | `src/engine/utils/asset_loader.py` | `pygame-ce` | Sprites del jugador y enemigos | Todos los escenarios | Revisión de código | `03_ARCHITECTURE.md` §2.6 |
| Animación de sprites | La animación vive en cada entidad, no en un controlador aparte | La entidad propia tiene animación multi-fotograma con los FPS correctos | `src/framework/entities/base_entity.py` + jugador/enemigo | `pygame-ce` | Todas las entidades animadas de Stage 0 | Todos los escenarios | Revisión de código | `04_PLAYER_SPEC.md` §9 |
| Doble búfer | `App.internal_surface` con blit a la ventana | El README explica el doble búfer (interno → ventana) | `src/engine/core/app.py` | `pygame-ce` | Todo Stage 0 | Todos los escenarios (README) | README | `03_ARCHITECTURE.md` §4.1 |
| Ordenamiento en Z / llamadas de dibujo | Propiedad `BaseEntity.layer`; grupo de pyscroll | Los valores de capa de la entidad producen un orden de profundidad visual correcto | `src/framework/entities/base_entity.py`, `pyscroll` | `pygame-ce` | Entidades de Stage 0 a las profundidades correctas | Todos los escenarios | Revisión visual | `03_ARCHITECTURE.md` §2.7 |
| Ciclo de vida del objeto | `BaseEntity.is_active`, `is_visible` | Las entidades propias fijan correctamente `is_active = False` al morir | `src/framework/entities/base_entity.py` | `pygame-ce` | Muerte de enemigo en Stage 0 | Todos los escenarios | Revisión de código | `03_ARCHITECTURE.md` §2.7 |

### 6.2 Evidencia de aprendizaje — Unidad IV

Un estudiante demuestra dominio de la Unidad IV cuando su escenario:
- Tiene una pila de capas TMX correcta con parallax visible.
- Tiene al menos un sprite animado propio con conteo de fotogramas y FPS documentados.
- Incluye un diagrama en el README del orden de renderizado de capas.

---

## 7. Unidad V — RGB, HSV, HSL, CMYK, transparencia, mezcla alfa, iluminación

### 7.1 Tabla de entregables

| Tema | Entrega el profesorado | Entrega el estudiante | Componente del framework | Bibliotecas | Ejemplo en Stage 0 | Escenario del estudiante | Evaluación | Referencia |
|---|---|---|---|---|---|---|---|---|
| Modelo de color RGB | `ColorTools.surface_to_array()` devuelve un ndarray RGB | El estudiante documenta un valor RGB de su escenario y explica cada canal | `src/framework/processing/color_tools.py` | `numpy`, `pygame-ce` | Modo depuración: inspector de píxeles | Stage 1 | Examen I (teoría) + README | `03_ARCHITECTURE.md` §2.9 |
| Modelo de color HSV | `ColorTools.rgb_to_hsv()`, `hsv_to_rgb()` | El estudiante aplica manipulación HSV (p. ej., rotación de matiz, cambio de saturación) | `src/framework/processing/color_tools.py` | `numpy` | No está en Stage 0 — primer uso del estudiante | Stage 1 | Práctica I | `03_ARCHITECTURE.md` §2.9 |
| Modelo de color HSL | `ColorTools.rgb_to_hsl()`, `hsl_to_rgb()` | El estudiante aplica ajuste de luminosidad vía HSL | `src/framework/processing/color_tools.py` | `numpy` | No está en Stage 0 | Stage 1 | Entrega de escenario | `03_ARCHITECTURE.md` §2.9 |
| Modelo de color CMYK | `ColorTools.rgb_to_cmyk()`, `cmyk_to_rgb()` | El estudiante convierte una paleta de sprite a CMYK y documenta los valores | `src/framework/processing/color_tools.py` | `numpy` | No está en Stage 0 | Stage 1 (ejercicio teórico) | README | `03_ARCHITECTURE.md` §2.9 |
| Canal alfa y transparencia | `pygame.Surface.set_alpha()`, `ColorTools.alpha_blend()` | Al menos un efecto visual usa transparencia alfa | `src/framework/processing/color_tools.py` | `pygame-ce`, `numpy` | Superposiciones de depuración (semitransparentes) | Stage 1 | Revisión de código | `03_ARCHITECTURE.md` §2.9 |
| Ecuación de mezcla alfa | `ColorTools.alpha_blend()` | El estudiante documenta la fórmula de mezcla en el README: `out = src * α + dst * (1-α)` | `src/framework/processing/color_tools.py` | `numpy` | Parpadeo de invencibilidad | Stage 1 | README | `03_ARCHITECTURE.md` §2.9 |
| Iluminación 2D simulada | `ColorTools.apply_tint()` + `adjust_brightness()` | El estudiante crea un efecto de luz direccional o ambiental usando tinte de color | `src/framework/processing/color_tools.py`, `src/framework/processing/filter_tools.py` | `numpy`, `pygame-ce` | No está en Stage 0 | Stage 1 o 2 | Entrega de escenario | `11_FILTER_TOOLS_SPEC.md` §8.2 |

### 7.2 Evidencia de aprendizaje — Unidad V

Un estudiante demuestra dominio de la Unidad V cuando puede:
- Convertir a mano un píxel muestreado de su escenario entre RGB, HSV, y HSL (mostrado en el README).
- Mostrar un efecto visual dirigido por una operación de espacio de color.
- Explicar la fórmula de mezcla alfa y cómo se aplica en su escenario.

---

## 8. Unidad VI — Texturas, animación, interpolación, colisiones, interacción

### 8.1 Tabla de entregables

| Tema | Entrega el profesorado | Entrega el estudiante | Componente del framework | Bibliotecas | Ejemplo en Stage 0 | Escenario del estudiante | Evaluación | Referencia |
|---|---|---|---|---|---|---|---|---|
| Mapeo de texturas | `AssetLoader.load_image()` | Las entidades del estudiante usan texturas del tamaño correcto (restricción de 16 colores) | `src/engine/utils/asset_loader.py` | `pygame-ce` | Todas las entidades con sprite | Todos los escenarios | Revisión de recursos | `03_ARCHITECTURE.md` §2.6 |
| Animación basada en fotogramas | `_advance_animation` y `_sprite_frames` en cada entidad | Animación de entidad propia con conteo de fotogramas, FPS, y modo de bucle documentados | `src/framework/entities/base_entity.py` | `pygame-ce` | Animaciones del jugador y enemigos | Todos los escenarios | Revisión de código | `04_PLAYER_SPEC.md` §9 |
| Interpolación lineal | `math_utils.lerp()` | Al menos un valor dirigido por lerp (seguimiento de cámara, movimiento de plataforma, desvanecido) | `src/engine/utils/math_utils.py` | — | El seguimiento de cámara usa lerp | Stage 1 o 2 | Revisión de código | `03_ARCHITECTURE.md` §2.6 |
| Funciones de easing | Funciones `math_utils.ease_*` (implementación propia, sin `pytweening` — ver `10_LIBRARIES_AND_DEPENDENCIES.md`) | Al menos una entidad o UI usa una función de easing (no lerp plano) | `src/engine/utils/math_utils.py` | — | Deslizamiento del banner de pantalla (ease_out_quad) | Stage 1 o 2 | Práctica I | `03_ARCHITECTURE.md` §2.6 |
| Detección de colisión AABB | Resolución de colisión del jugador y enemigos en el motor | La entidad propia del estudiante resuelve colisión AABB correctamente | `src/framework/entities/player.py`, `src/framework/entities/enemy_base.py` | `pygame-ce` | Todas las interacciones de Zona A–F | Todos los escenarios | Revisión de código | `04_PLAYER_SPEC.md` §4.3 |
| Eventos de interacción | Sistema publicación/suscripción de `EventBus` | Una zona de disparo propia emite un evento; otra entidad se suscribe | `src/engine/core/event_bus.py` | — | Checkpoint → HUD; Disparador → proyectil | Stage 1 o 2 | Revisión de código | `03_ARCHITECTURE.md` §2.1 |
| Plataformas de un solo sentido | Objetos de tipo «Platform» en la capa `Collision` (AUD-150: no hay ningún prefijo especial en los nombres) | El estudiante diseña una zona de escenario con plataformas de un solo sentido | Capa TMX `Collision`, `src/framework/stage/stage_loader.py` | `pygame-ce`, `pytmx` | Plataforma de un solo sentido de la Zona E | Stage 1 o 2 | Revisión de TMX | `06_TMX_SPEC.md` §9.2 |

### 8.2 Evidencia de aprendizaje — Unidad VI

Un estudiante demuestra dominio de la Unidad VI cuando:
- Su entidad propia usa `ease_out_quad` (o equivalente) y la desaceleración visual es observable.
- Su escenario tiene una interacción funcional de EventBus entre dos entidades.
- Su colisión AABB se resuelve sin atravesar paredes a 60 FPS.

---

## 9. Unidad VII — Histograma, brillo, contraste, convolución, desenfoque gaussiano, Sobel, Canny

### 9.1 Tabla de entregables

| Tema | Entrega el profesorado | Entrega el estudiante | Componente del framework | Bibliotecas | Ejemplo en Stage 0 | Escenario del estudiante | Evaluación | Referencia |
|---|---|---|---|---|---|---|---|---|
| Histograma | `FilterTools.compute_histogram()` | El estudiante usa la salida del histograma para disparar un evento de juego; documenta la forma del histograma | `src/framework/processing/filter_tools.py` | `numpy`, `pygame-ce` | Prueba unitaria + Zona F (demo) | Stage 2 | Práctica II | `11_FILTER_TOOLS_SPEC.md` §8.1 |
| Ecualización de histograma | `FilterTools.histogram_equalize()` | El estudiante aplica ecualización a una superficie y muestra antes/después en el README | `src/framework/processing/filter_tools.py` | `numpy` únicamente (AUD-455: no usa `opencv-python` — CDF calculado a mano, ver `11_FILTER_TOOLS_SPEC.md` §8.1) | Escena demo | Stage 2 | Entrega de escenario | `11_FILTER_TOOLS_SPEC.md` §8.1 |
| Ajuste de brillo | `FilterTools.adjust_brightness()` | El estudiante crea un efecto de brillo basado en salud o tiempo | `src/framework/processing/filter_tools.py` | `numpy` | Zona F (demostrado) | Stage 2 | Revisión de código | `11_FILTER_TOOLS_SPEC.md` §8.2 |
| Ajuste de contraste | `FilterTools.adjust_contrast()` | El estudiante crea un alternador de modo visual basado en contraste | `src/framework/processing/filter_tools.py` | `numpy` | Escena demo | Stage 2 | Entrega de escenario | `11_FILTER_TOOLS_SPEC.md` §8.3 |
| Convolución | `FilterTools.apply_kernel()`, `get_standard_kernel()` | El estudiante aplica un kernel propio o estándar y documenta la matriz de kernel | `src/framework/processing/filter_tools.py` | `scipy.ndimage`, `numpy` | Prueba unitaria | Stage 2 | Práctica II | `11_FILTER_TOOLS_SPEC.md` §8.4 |
| Desenfoque gaussiano | `FilterTools.gaussian_blur()` | El estudiante aplica desenfoque a un fondo o región de sprite con sigma documentado | `src/framework/processing/filter_tools.py` | `scipy.ndimage`, `numpy` | Escena demo (sigma interactivo) | Stage 2 | Revisión de código | `11_FILTER_TOOLS_SPEC.md` §8.5 |
| Detección de bordes de Sobel | `FilterTools.sobel_edge()` | El estudiante aplica Sobel y usa el mapa de bordes como superposición visual | `src/framework/processing/filter_tools.py` | `opencv-python`, `numpy` | Escena demo | Stage 2 | Práctica II | `11_FILTER_TOOLS_SPEC.md` §8.6 |
| Detección de bordes de Canny | `FilterTools.canny_edge()` | El estudiante aplica Canny con umbrales documentados; muestra el resultado en el README | `src/framework/processing/filter_tools.py` | `opencv-python`, `numpy` | Escena demo | Stage 2 | Entrega de escenario | `11_FILTER_TOOLS_SPEC.md` §8.6 |

### 9.2 Evidencia de aprendizaje — Unidad VII

Un estudiante demuestra dominio de la Unidad VII cuando puede:
- Escribir la definición matemática de la convolución y hacerla coincidir con el kernel que aplicó.
- Mostrar el histograma de una superficie de su escenario y explicar qué revela.
- Demostrar un mapa de bordes de Sobel y explicar por qué ciertos bordes aparecen más fuertes.
- Justificar sus umbrales de Canny y explicar la histéresis con sus propias palabras.

---

## 10. Unidad VIII — Umbral, Otsu, morfología, componentes conectados, watershed, análisis de regiones, extracción de características

### 10.1 Tabla de entregables

| Tema | Entrega el profesorado | Entrega el estudiante | Componente del framework | Bibliotecas | Ejemplo en Stage 0 | Escenario del estudiante | Evaluación | Referencia |
|---|---|---|---|---|---|---|---|---|
| Umbralización binaria | `VisionTools.threshold_binary()` | El estudiante aplica umbral a una superficie del escenario; documenta el valor de umbral | `src/framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Escena demo | Stage 2 o 3 | Práctica II | `12_VISION_TOOLS_SPEC.md` §8.1 |
| Método de Otsu | `VisionTools.threshold_otsu()` | El estudiante aplica Otsu y documenta el umbral calculado | `src/framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Escena demo | Stage 2 o 3 | Práctica II | `12_VISION_TOOLS_SPEC.md` §8.2 |
| Erosión morfológica | `VisionTools.morphological_erode()` | El estudiante aplica erosión tras el umbral; muestra eliminación de ruido | `src/framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Escena demo | Stage 2 o 3 | Revisión de código | `12_VISION_TOOLS_SPEC.md` §9.1 |
| Dilatación morfológica | `VisionTools.morphological_dilate()` | El estudiante aplica dilatación; muestra relleno de huecos | `src/framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Escena demo | Stage 2 o 3 | Revisión de código | `12_VISION_TOOLS_SPEC.md` §9.2 |
| Apertura y cierre | `VisionTools.morphological_open()`, `morphological_close()` | El estudiante documenta la secuencia (erosión→dilatación o viceversa) | `src/framework/processing/vision_tools.py` | `opencv-python` | Escena demo | Stage 3 | Entrega de escenario | `12_VISION_TOOLS_SPEC.md` §9.3, §9.4 |
| Componentes conectados | `VisionTools.connected_components()` | El estudiante cuenta regiones distintas; usa el conteo de regiones para dirigir la lógica del juego | `src/framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Escena demo | Stage 3 | Práctica II | `12_VISION_TOOLS_SPEC.md` §10.1 |
| Análisis de regiones | `VisionTools.analyze_regions()` | El estudiante documenta un objeto `RegionInfo` (área, centroide, caja envolvente) | `src/framework/processing/vision_tools.py` | `scikit-image`, `opencv-python` | Escena demo | Stage 3 | README + Práctica II | `12_VISION_TOOLS_SPEC.md` §11.1 |
| Segmentación watershed | `VisionTools.watershed_segment()` | El estudiante aplica watershed y muestra la superposición de segmento coloreada por código en el escenario | `src/framework/processing/vision_tools.py` | `opencv-python`, `numpy` | Escena demo | Stage 3 | Entrega de escenario | `12_VISION_TOOLS_SPEC.md` §12.1 |
| Extracción de características (HOG, LBP) | `VisionTools.extract_hog()`, `extract_lbp()`, `extract_color_histogram()` | El estudiante extrae características y documenta la dimensionalidad del vector | `src/framework/processing/vision_tools.py` | `scikit-image`, `numpy` | Escena demo | Stage 3 | Práctica II + III | `12_VISION_TOOLS_SPEC.md` §13 |

### 10.2 Evidencia de aprendizaje — Unidad VIII

Un estudiante demuestra dominio de la Unidad VIII cuando:
- Su README contiene una impresión real de `RegionInfo` de su escenario.
- Muestra una comparación de antes/después de operaciones morfológicas.
- Explica el criterio de Otsu (maximizar la varianza inter-clase) en su presentación.
- Demuestra que la salida de segmentación cambia el comportamiento del juego en al menos dos casos.

---

## 11. Unidad IX — Reconocimiento de patrones, clasificación, visión por computadora, aplicaciones interactivas, aprendizaje automático

### 11.1 Tabla de entregables

| Tema | Entrega el profesorado | Entrega el estudiante | Componente del framework | Bibliotecas | Ejemplo en Stage 0 | Escenario del estudiante | Evaluación | Referencia |
|---|---|---|---|---|---|---|---|---|
| Descriptor HOG | `VisionTools.extract_hog()` | El README del estudiante documenta los parámetros de HOG y la longitud del vector | `src/framework/processing/vision_tools.py` | `scikit-image`, `numpy` | Escena demo | Stage 3 | README + Práctica III | `12_VISION_TOOLS_SPEC.md` §13.2 |
| Descriptor LBP | `VisionTools.extract_lbp()` | El estudiante usa LBP y documenta la interpretación del patrón de textura | `src/framework/processing/vision_tools.py` | `scikit-image`, `numpy` | Escena demo | Stage 3 | README | `12_VISION_TOOLS_SPEC.md` §13.3 |
| Descriptor de histograma de color | `VisionTools.extract_color_histogram()` | El estudiante muestra cómo la distribución de color distingue sus clases | `src/framework/processing/vision_tools.py` | `numpy` | Escena demo | Stage 3 | README | `12_VISION_TOOLS_SPEC.md` §13.4 |
| Construcción de dataset | Script `tools/build_dataset.py` (provisto por el profesorado) | El estudiante construye un dataset `.npz` etiquetado (≥ 3 clases, ≥ 30 muestras/clase) | Script de construcción + `student_assets/datasets/` | `numpy`, `scikit-image` | Dataset de muestra provisto | Stage 3 | Entrega de dataset | `13_PATTERN_RECOGNITION_SPEC.md` §8 |
| Clasificación k-NN | `PatternRecognitionTools.train(..., 'knn')` | El estudiante entrena, evalúa, y documenta un modelo k-NN | `src/framework/processing/pattern_recognition_tools.py` | `scikit-learn` | Escena demo | Stage 3 | Práctica III | `13_PATTERN_RECOGNITION_SPEC.md` §14.1 |
| Árbol de decisión | `PatternRecognitionTools.train(..., 'tree')` | El estudiante entrena un árbol; documenta la profundidad y el criterio de división | `src/framework/processing/pattern_recognition_tools.py` | `scikit-learn` | Escena demo | Stage 3 | Práctica III | `13_PATTERN_RECOGNITION_SPEC.md` §14.2 |
| Bosque aleatorio | `PatternRecognitionTools.train(..., 'forest')` | El estudiante compara bosque frente a árbol único sobre su dataset | `src/framework/processing/pattern_recognition_tools.py` | `scikit-learn` | Escena demo | Stage 3 | Entrega de escenario | `13_PATTERN_RECOGNITION_SPEC.md` §14.3 |
| SVM | `PatternRecognitionTools.train(..., 'svm')` | Opcional: el estudiante aplica SVM y lo compara con otros clasificadores | `src/framework/processing/pattern_recognition_tools.py` | `scikit-learn` | Escena demo | Stage 3 (opcional) | Bono | `13_PATTERN_RECOGNITION_SPEC.md` §14.4 |
| Tubería de entrenamiento de modelo | Flujo `train()` + `evaluate()` | El estudiante documenta la precisión de entrenamiento, de prueba, y la matriz de confusión | `src/framework/processing/pattern_recognition_tools.py` | `scikit-learn`, `numpy` | Plantilla de notebook | Stage 3 | Práctica III | `13_PATTERN_RECOGNITION_SPEC.md` §9, §10 |
| Serialización de modelo | `save_model()` / `load_model()` | Fichero `.pkl` en `student_assets/models/`; cargado en `on_enter()` | `src/framework/processing/pattern_recognition_tools.py` | `joblib` | — | Stage 3 | Revisión de código | `13_PATTERN_RECOGNITION_SPEC.md` §11 |
| Inferencia en tiempo de ejecución | `predict()` en el bucle de juego | El resultado de clasificación cambia el comportamiento observable del juego | `src/framework/processing/pattern_recognition_tools.py` | `scikit-learn`, `numpy` | Escena demo | Stage 3 | Demo en vivo | `13_PATTERN_RECOGNITION_SPEC.md` §13.3 |
| Aplicación interactiva | Tubería completa: Filter → Vision → Pattern → Comportamiento | Stage 3 es una aplicación de ML interactiva completa | Todos los módulos de procesamiento | Todas las bibliotecas | Escena demo | Stage 3 | Presentación final | `13_PATTERN_RECOGNITION_SPEC.md` |

### 11.2 Evidencia de aprendizaje — Unidad IX

Un estudiante demuestra dominio de la Unidad IX cuando puede:
- Presentar un `EvaluationResult` completo con precisión ≥ 70%.
- Mostrar en vivo en su Stage 3 que dos entradas visuales distintas producen salidas de clasificación y comportamientos de juego distintos.
- Explicar matemáticamente cómo k-NN encuentra los vecinos más cercanos (fórmula de distancia, selección de k).
- Comparar dos tipos de clasificador sobre su dataset y explicar el compromiso.

---

## 12. Resumen de instrumentos de evaluación

La tabla siguiente da los seis instrumentos **oficiales** y su ponderación **oficial**, según los define el programa del curso. La programación completa clase por clase está en `21_COURSE_SCHEDULE.md`.

| Instrumento | Porcentaje | Unidades cubiertas | Clase | Formato |
|---|---|---|---|---|
| **Quices** | 15% | Distribuido: I–II, III, V, VIII | Clases 2, 4, 6, 9 | Comprobaciones cortas escritas/conceptuales |
| **Prácticas de laboratorio** | 20% | Distribuido: II, V, VIII | Clases 3, 6, 9 | Ejercicios de laboratorio de Python individuales y prácticos |
| **Evaluación Práctica I – Prototipo Funcional** | 15% | II, III, IV, V | Clase 5 | Entrega de Escenario/Jefe — coordenadas, transformaciones, escenario básico, interacción inicial |
| **Evaluación Práctica II – Vertical Slice** | 15% | III, IV, V, VI | Clase 8 | Entrega de Escenario/Jefe — curvas, escenas, color/transparencia, texturas/animación |
| **Evaluación Práctica III – Integración Final** | 15% | VII, VIII, IX | Clase 11 | Entrega de Escenario/Jefe — procesamiento de imágenes, segmentación, reconocimiento de patrones, integración completa |
| **Proyecto Integrador Invenio Fest** | 20% | I–IX (aplicado) | Clase 12 | Presentación grupal interdisciplinaria; este curso califica sólo la contribución gráfica/visual |
| **Total** | **100%** | | | |

Cada Evaluación Práctica es una entrega del **mismo Escenario o Jefe único** que el estudiante eligió individualmente en la Clase 1 — no un escenario distinto por punto de control. Ver `08_SYLLABUS_MAPPING.md` §12 para el mapeo completo de hito a unidad.

---

## 13. Lista de verificación pre-semestre del profesorado

Los siguientes elementos deben entregarse antes de que empiece el curso:

| Entregable | Objetivo de estado | Documento |
|---|---|---|
| `src/engine/` completamente implementado y probado | Antes de la Clase 1 | `03_ARCHITECTURE.md` |
| `src/framework/entities/` completamente implementado y probado | Antes de la Clase 1 | `04_PLAYER_SPEC.md`, `05_ENEMY_SPEC.md` |
| `src/framework/processing/filter_tools.py` completamente implementado | Antes de la Clase 8 | `11_FILTER_TOOLS_SPEC.md` |
| `src/framework/processing/vision_tools.py` completamente implementado | Antes de la Clase 9 | `12_VISION_TOOLS_SPEC.md` |
| `src/framework/processing/pattern_recognition_tools.py` completamente implementado | Antes de la Clase 10 | `13_PATTERN_RECOGNITION_SPEC.md` |
| `src/stages/stage0/` completamente implementado | Antes de la Clase 1 | `07_STAGE0_DESIGN.md` |
| Escenas demo (Unidades VII, VIII, IX) implementadas | Antes de las Clases 8, 9, 10 respectivamente | `15_ACADEMIC_DEMO_SCENES.md` |
| Todas las pruebas unitarias pasando | Continuo | Todos los docs de especificación |
| `tools/build_dataset.py` disponible | Antes de la Clase 10 | `13_PATTERN_RECOGNITION_SPEC.md` §20 |
| Plantilla de notebook de entrenamiento disponible | Antes de la Clase 10 | `13_PATTERN_RECOGNITION_SPEC.md` §20 |
| `assets/datasets/sample_dataset.npz` disponible | Antes de la Clase 10 | `13_PATTERN_RECOGNITION_SPEC.md` §8 |
| `student_templates/stage_template/` y `student_templates/boss_template/` disponibles | Antes de la Clase 1 | Este documento, §1 |

---

## 14. Lista de verificación de entregables del estudiante (por Evaluación Práctica)

Las listas de verificación de abajo aplican al **único Escenario o Jefe asignado individualmente** a cada estudiante en la Clase 1 — **no** son tres escenarios distintos. "14.1 / 14.2 / 14.3" son los tres puntos de control acumulativos de completitud de esa única entrega, nombrados según los instrumentos oficiales Evaluación Práctica I/II/III.

### 14.1 Lista de verificación de la Evaluación Práctica I — Prototipo Funcional (Clase 5)

| Elemento | Unidades | Obligatorio |
|---|---|---|
| `<entrega>.tmx` — TMX válido con todas las capas obligatorias (sólo Escenarios) | I, IV | Obligatorio |
| `<entrega>.py` — subclase correcta de `BaseScene` (Escenario) o `BossBase` (Jefe) | I, IV | Obligatorio |
| Al menos una entidad propia que use matemática vectorial | II | Obligatorio |
| Al menos una entidad que siga una ruta de curva | III | Obligatorio |
| Operación de espacio de color aplicada a una superficie | V | Obligatorio |
| `README.md` — todos los conceptos académicos documentados | I–V | Obligatorio |

### 14.2 Lista de verificación de la Evaluación Práctica II — Vertical Slice (Clase 8)

| Elemento | Unidades | Obligatorio |
|---|---|---|
| Se mantienen todos los requisitos de la Evaluación Práctica I | I–V | Obligatorio |
| Función de easing usada en movimiento o animación | VI | Obligatorio |
| `FilterTools.compute_histogram()` usado para dirigir lógica | VII | Obligatorio |
| `FilterTools.adjust_brightness()` o `adjust_contrast()` aplicado | VII | Obligatorio |
| `FilterTools.apply_kernel()` o `gaussian_blur()` aplicado | VII | Obligatorio |
| Al menos un resultado de detección de bordes (Sobel o Canny) | VII | Obligatorio |
| README: matriz de kernel, filtro aplicado, capturas de antes/después | VI, VII | Obligatorio |

### 14.3 Lista de verificación de la Evaluación Práctica III — Integración Final (Clase 11)

| Elemento | Unidades | Obligatorio |
|---|---|---|
| Se mantienen todos los requisitos de la Evaluación Práctica I y II | I–VII | Obligatorio |
| `VisionTools.threshold_binary()` o `threshold_otsu()` aplicado | VIII | Obligatorio |
| Al menos una operación morfológica aplicada | VIII | Obligatorio |
| `VisionTools.connected_components()` o `analyze_regions()` usado | VIII | Obligatorio |
| `VisionTools.extract_features()` produce características de entrenamiento | VIII, IX | Obligatorio |
| Dataset etiquetado en `assets/datasets/` o la carpeta de entrega del estudiante | IX | Obligatorio |
| Modelo entrenado en la carpeta de entrega del estudiante (`.pkl`) | IX | Obligatorio |
| `EvaluationResult` con precisión ≥ 70% en el README | IX | Obligatorio |
| El clasificador corre en tiempo de ejecución; el resultado cambia el comportamiento del juego | IX | Obligatorio |
| README: documentación completa de la tubería de entrenamiento | IX | Obligatorio |

---
## 🔗 Documentos relacionados

- [[08_SYLLABUS_MAPPING.md|Mapeo del programa del curso]]
- [[27_ACADEMIC_RUBRICS.md|Rúbricas académicas]]

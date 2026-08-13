---
document_id: "LOI-SYLLABUS-028B"
title: "Programa de muestra — Legacy of InFest: prácticas de desarrollo de videojuegos"
aliases: ["Programa de muestra", "Sample Syllabus"]
tags: ["silabo", "muestra", "academico"]
description: "Programa de curso de muestra"
source: "docs/78_SAMPLE_SYLLABUS.md"
date_processed: "2026-08-13"
---

# Programa de muestra — Legacy of InFest: prácticas de desarrollo de videojuegos

**Curso:** CS 4XXX / GDD 4XXX — Desarrollo de videojuegos y procesamiento digital de imágenes
**Profesor(a):** [Nombre]
**Periodo:** [Semestre]
**Prerrequisitos:** CS 2XXX (Programación orientada a objetos) o equivalente
**Créditos:** 3-4 (varía según la institución)

> **AUD-455.** Traduce el documento. Es una **plantilla de muestra** para
> que otros profesores adapten, no una descripción literal de la API de
> este repositorio — de ahí los corchetes `[Nombre]`/`[Semestre]`. Aun así,
> dos de sus temas semanales citan operaciones que `VisionTools` y
> `PatternRecognitionTools` **no implementan** en este código
> (transformada de Hough, esquinas de Harris, K-means, PCA, template
> matching — ver `12_VISION_TOOLS_SPEC.md` y `13_PATTERN_RECOGNITION_SPEC.md`
> para la API real: umbralización/Otsu/morfología/watershed/HOG/LBP en
> Vision, y k-NN/árbol/bosque/SVM en Pattern Recognition). Se deja como
> nota aquí en vez de reescribir el programa: quien lo adopte debe ajustar
> las Semanas 12 y 13 a las operaciones que el framework sí ofrece.

---

## Descripción del curso

Los estudiantes construyen un videojuego 2D completo de acción y plataformas usando el framework Legacy of InFest, aplicando conceptos de álgebra lineal, gráficas por computadora, procesamiento digital de imágenes, y reconocimiento de patrones. El curso está basado en proyectos: los estudiantes diseñan niveles, programan IA de enemigos, crean jefes, e integran tuberías de procesamiento para efectos visuales.

---

## Objetivos de aprendizaje

Al final de este curso, los estudiantes podrán:

1. Aplicar matemática vectorial al movimiento y la colisión del juego
2. Implementar curvas de Bézier e interpolación para animación
3. Manipular espacios de color y mezcla alfa
4. Usar detección y resolución de colisión AABB
5. Aplicar kernels de convolución (desenfoque, realce, detección de bordes)
6. Implementar segmentación de imágenes y extracción de características
7. Construir tuberías de reconocimiento de patrones
8. Diseñar e implementar un encuentro de jefe multi-fase
9. Crear un escenario de juego completo y jugable, con enemigos y coleccionables
10. Usar herramientas de diseño de nivel basadas en TMX

---

## Materiales requeridos

- Python 3.11+
- Framework Legacy of InFest (GitHub Classroom)
- Editor de mapas Tiled (https://www.mapeditor.org/)
- Cuenta de Git + GitHub

---

## Calendario semanal

### Unidad I: Fundamentos (Semanas 1-2)

| Semana | Tema | Laboratorio | Entrega |
|------|-------|-----|------------|
| 1 | Introducción al curso, Python, Pygame, configuración del framework | Recorrido por el motor Legacy | Bifurcar el repo, ejecutar Stage 0 |
| 2 | Bucle de juego, manejo de entrada, gestión de escenas | Explorar el menú de demos | Crear una escena de prueba |

### Unidad II: Vectores y transformaciones (Semanas 3-4)

| Semana | Tema | Laboratorio | Entrega |
|------|-------|-----|------------|
| 3 | Aritmética vectorial, normalización, producto punto | VectorLabScene | Maquetación TMX de Stage 1 |
| 4 | Transformaciones 2D (traslación, rotación, escala) | TransformLabScene | Colocar enemigos en el TMX |

### Unidad III: Curvas e interpolación (Semanas 5-6)

| Semana | Tema | Laboratorio | Entrega |
|------|-------|-----|------------|
| 5 | Curvas de Bézier, algoritmo de de Casteljau | CurveEditorScene | Rutas de patrulla de enemigos |
| 6 | Interpolación, funciones de easing | InterpolationLabScene | Movimiento de cámara |

### Unidad IV: Colisión (Semana 7)

| Semana | Tema | Laboratorio | Entrega |
|------|-------|-----|------------|
| 7 | Detección y resolución de colisión AABB | CollisionLabScene | Peligros y disparadores |

### Unidad V: Color y ruido (Semanas 8-9)

| Semana | Tema | Laboratorio | Entrega |
|------|-------|-----|------------|
| 8 | Espacios de color RGB/HSV/HSL/CMYK | ColorTheoryScene | Daño codificado por color |
| 9 | Generación de ruido procedural | NoiseLabScene | Decoración de terreno |

### Unidad VI: Procesamiento digital de imágenes (Semanas 10-11)

| Semana | Tema | Laboratorio | Entrega |
|------|-------|-----|------------|
| 10 | Histogramas, brillo, contraste | FilterDemoScene | Efectos de post-procesamiento |
| 11 | Convolución, detección de bordes de Sobel y Canny | FilterDemoScene | Brillo de bordes, estilo pictórico |

### Unidad VII: Visión y segmentación (Semana 12)

| Semana | Tema | Laboratorio | Entrega |
|------|-------|-----|------------|
| 12 | Umbralización, Otsu, morfología, componentes conectados | VisionDemoScene | Detección de telegrafiado de jefe |

### Unidad VIII: Reconocimiento de patrones (Semana 13)

| Semana | Tema | Laboratorio | Entrega |
|------|-------|-----|------------|
| 13 | k-NN, árbol de decisión, bosque aleatorio, SVM | PatternDemoScene | Clasificación de regiones |

### Unidad IX: Diseño de jefes (Semanas 14-15)

| Semana | Tema | Laboratorio | Entrega |
|------|-------|-----|------------|
| 14 | Máquinas de estado de jefe, fases, telegrafiado | Análisis del Boss Venado | Prototipo de jefe |
| 15 | Pulido de jefe, eventos, logros | Pruebas de juego | Entrega final del jefe |

### Semana de finales

| Semana | Tema |
|------|-------|
| 16 | Muestra de proyectos, revisión entre pares, entregas finales |

---

## Rúbrica de calificación

| Componente | Peso | Detalles |
|-----------|--------|---------|
| Escenario 1 (TMX) | 15% | Terreno, enemigos, coleccionables, checkpoints |
| Escenario 2 (TMX) | 15% | Terreno avanzado, peligros, clima |
| Jefe | 25% | 2+ fases, 2+ patrones de ataque, telegrafiado |
| Laboratorios (10) | 20% | 2% cada uno, basado en completitud |
| Proyecto de procesamiento | 15% | Tubería usando FilterTools/VisionTools |
| Participación | 10% | Revisión entre pares, pruebas de juego, revisión de código |

**Escala:** 90-100% A, 80-89% B, 70-79% C, 60-69% D, <60% F

---

## Política de entregas tardías

- Entregas dentro de las 24h del plazo: -10%
- 24-48h: -25%
- 48h+: no se aceptan sin arreglo previo

---

## Integridad académica

Todo el trabajo debe ser propio. Se puede discutir conceptos con compañeros de clase, pero no se puede compartir código ni ficheros TMX. Los scripts de detección de plagio comparan las entregas de los estudiantes por similitud estructural.

---

## Lista de entregables

- [ ] Recorrido de Stage 0 (comprobación de comprensión)
- [ ] TMX de Stage 1 (terreno + enemigos)
- [ ] TMX de Stage 2 (peligros + clima)
- [ ] Fichero Python del jefe (clase que hereda de BossBase)
- [ ] TMX del jefe (mapa de la arena)
- [ ] 10 checkpoints de laboratorio (capturas F2-F10)
- [ ] Demo de tubería de procesamiento (PipelineBuilder o script)
- [ ] Revisión entre pares (2 compañeros de clase)
- [ ] Entrega final del repositorio

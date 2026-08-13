---
document_id: "LOI-CLASS-034"
title: "Materiales de clase — Diapositivas y guiones de codificación en vivo"
aliases: ["Materiales de clase", "Class Materials"]
tags: ["clase", "materiales", "academico"]
description: "Materiales y recursos de clase"
source: "docs/34_CLASS_MATERIALS.md"
date_processed: "2026-08-13"
---

# Materiales de clase — Diapositivas y guiones de codificación en vivo

> **AUD-455.** Traduce el documento (cuerpo en inglés, resumen condensado
> en español al final). El documento organiza los materiales por
> «semana» (16 semanas); el calendario oficial vigente
> (`21_COURSE_SCHEDULE.md`) es un trimestre de 11 clases de 4 horas. Se
> deja la numeración de semana original sin remapear a clase — inventar
> esa correspondencia sin una fuente que la confirme sería peor que
> dejarla explícita como pendiente. Quien programe las sesiones debe
> adaptar esta lista al calendario de 11 clases.

Este documento indexa todo el material de presentación y codificación en vivo dirigido al profesorado.
Los ficheros marcados con ✅ existen en el repositorio. Los marcados con ❌ están planeados pero aún no creados.

## Unidad I: Introducción (Semana 1)
- ❌ `slides/u01_intro.md` — Visión general del curso, arquitectura del motor, bucle de juego
- ❌ `live_code/u01_create_window.py` — Configuración mínima de una ventana de pygame
- ❌ `exercise/u01_setup_environment.md` — Guía de configuración del entorno de desarrollo

## Unidad II: Vectores y transformaciones (Semanas 2-3)
- ❌ `slides/u02_vectors.md` — Matemática vectorial, normalización, producto punto, transformaciones
- ✅ `live_code/u02_vector_class.py` — Implementar Vector2 desde cero (`docs/34_LIVE_CODE_u02_vector_class.py`)
- ❌ `exercise/u02_vector_chase.md` — Implementar comportamiento de persecución de NPC
- ❌ `slides/u02_transforms.md` — Matrices de traslación, rotación, escala, cizalladura

## Unidad III: Curvas e interpolación (Semanas 4-5)
- ❌ `slides/u03_curves.md` — Bézier, Catmull-Rom, B-spline, NURBS
- ❌ `live_code/u03_de_casteljau.py` — Implementar el algoritmo de de Casteljau
- ❌ `exercise/u03_curve_path.md` — Construir una ruta de patrulla suave
- ❌ `slides/u03_interpolation.md` — Lerp, funciones de easing, fotogramas clave

## Unidad IV: POO y máquinas de estado (Semanas 6-7)
- ❌ `slides/u04_inheritance.md` — Subclase de BossBase, patrones de sobrescritura
- ❌ `live_code/u04_boss_template.py` — Crear un jefe desde cero
- ❌ `slides/u04_state_machines.md` — Estados del jugador: idle, walk, jump, attack
- ❌ `exercise/u04_state_machine.md` — Añadir un estado nuevo al jugador

## Unidad V: Espacios de color (Semana 8)
- ❌ `slides/u05_color.md` — RGB, HSV, HSL, CMYK, mezcla alfa
- ❌ `live_code/u05_rgb_to_hsv.py` — Implementar conversión de color
- ❌ `exercise/u05_color_match.md` — Desafío de emparejamiento de color

## Unidad VI: Detección de colisión (Semana 9)
- ❌ `slides/u06_collision.md` — AABB, círculo, SAT, hash espacial
- ❌ `live_code/u06_aabb_collision.py` — Prueba de solape AABB
- ❌ `exercise/u06_collision_resolve.md` — Resolver la penetración de colisión

## Unidad VII: Procesamiento de imágenes (Semanas 10-11)
- ❌ `slides/u07_filters.md` — Kernels de convolución, desenfoque, realce, detección de bordes
- ✅ `live_code/u07_convolution.py` — Implementación manual de convolución (`docs/34_LIVE_CODE_u07_convolution.py`)
- ❌ `exercise/u07_filter_chain.md` — Construir una tubería de procesamiento
- ❌ `slides/u07_histogram.md` — Ecualización y estiramiento de histograma

## Unidad VIII: Visión por computadora (Semanas 12-14)
- ❌ `slides/u08_vision.md` — Umbralización, morfología, componentes, watershed
- ❌ `live_code/u08_otsu.py` — Implementar la umbralización de Otsu
- ❌ `exercise/u08_object_detection.md` — Detectar y etiquetar objetos
- ❌ `live_code/u08_feature_extraction.py` — HOG, LBP, histogramas de color

## Proyecto final (Semanas 15-16)
- ❌ `slides/u09_final_project.md` — Integración, requisitos de entrega
- ❌ `exercise/u09_zone_design.md` — Lista de verificación de entrega de zona completa

## Formato de entrega

Cada fichero `slides/uXX_*.md` sigue esta estructura:
1. Objetivos de aprendizaje (3-5 elementos)
2. Conceptos clave con diagramas (ASCII)
3. Fragmentos de código mostrando el uso del framework
4. Errores comunes
5. Actividad en clase

Cada script de `live_code/` es un fichero Python mínimo e independiente que
el profesorado puede ejecutar durante la clase para demostrar un concepto
interactivamente.

Cada documento de `exercise/` es una hoja de una página para trabajo grupal en clase.

> **Nota:** sólo 2 de los 23 ficheros referenciados existen actualmente
> (`docs/34_LIVE_CODE_u02_vector_class.py` y `docs/34_LIVE_CODE_u07_convolution.py`).
> Los 21 ficheros restantes son entradas de marcador de posición que deben
> crearse antes de la sesión de clase correspondiente.

---
## 🔗 Documentos relacionados

- [[21_COURSE_SCHEDULE.md|Calendario del curso]]

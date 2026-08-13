---
document_id: "LOI-ENTREGABLES-ENTREGABLES"
title: "Entregables — guía de entregables"
aliases: ["Entregables", "entregables"]
tags: ["entregable", "asignacion"]
description: "Documento de entregables: entregables"
source: "docs/entregables/entregables.md"
date_processed: "2026-08-13"
---

# Entregables — guía de entregables

> **AUD-455.** Traduce el documento: tenía el cuerpo completo en inglés
> seguido de una traducción íntegra y redundante al español. Se conserva
> sólo la versión en español, sin duplicación.

**Curso:** Legacy of InFest
**Referencia:** `36_STUDENT_MANUAL.md`, `26_STUDENT_TEMPLATE_SPEC.md`, `14_PROFESSOR_DELIVERABLE_MATRIX.md`

## Estructura general

Cada entregable debe incluir un `README.md` colocado en `src/stages/<student_id>/` con:

```yaml
---
assignment_type: stage | boss
assignment_name: "Tu Título"
assignment_id: "stage1_2_name"
zone: 1 | 2 | 3 | final
student_name: "Tu Nombre"
units_demonstrated: [II, III, IV, V]
evaluation_milestone: "Evaluación Práctica I" | "Evaluación Práctica II" | "Evaluación Práctica III"
---
```

### Secciones requeridas del README

1. **Contexto narrativo** — describe el escenario académico
2. **Conceptos académicos demostrados** — una subsección por unidad
3. **Cómo ejecutar** — instrucciones para lanzar el entregable
4. **Capturas de pantalla** — antes/después para operaciones de FilterTools/VisionTools

## Entregables por evaluación

### Evaluación Práctica I (Clase 5)
- [ ] `<entrega>.tmx` con las 8 capas requeridas
- [ ] `<entrega>.py` — subclase de `BaseScene` o `BossBase`
- [ ] Entidad propia usando matemática vectorial
- [ ] Entidad siguiendo una trayectoria curva
- [ ] Operación de espacio de color sobre una superficie
- [ ] `README.md` con conceptos académicos documentados

### Evaluación Práctica II (Clase 8)
- [ ] Todos los entregables de Eval I mantenidos
- [ ] Función de easing usada en movimiento o animación
- [ ] `FilterTools.compute_histogram()` impulsa la lógica del juego
- [ ] `adjust_brightness()` o `adjust_contrast()` aplicado
- [ ] `apply_kernel()` o `gaussian_blur()` aplicado
- [ ] Resultado de detección de bordes (Sobel o Canny)
- [ ] README: matriz de kernel, capturas antes/después

### Evaluación Práctica III (Clase 11)
- [ ] Todos los entregables de Eval I + II mantenidos
- [ ] `threshold_binary()` o `threshold_otsu()` aplicado
- [ ] Operación morfológica aplicada
- [ ] `connected_components()` o `analyze_regions()` usado
- [ ] `extract_features()` produce características de entrenamiento
- [ ] Dataset etiquetado en `assets/datasets/`
- [ ] Modelo entrenado (`.pkl`) en la carpeta de la entrega
- [ ] `EvaluationResult` con precisión ≥70% en el README
- [ ] El clasificador se ejecuta en tiempo de ejecución; la salida cambia el comportamiento del juego en ≥2 formas
- [ ] README: documentación completa de la tubería de entrenamiento

## Plantillas

- **Plantilla de escenario:** `student_templates/stage_template/stage_template.py` + `stage_template.tmx`
- **Plantilla de jefe:** `student_templates/boss_template/boss_template.py` + plantilla de README

## Reglas de entrega

- Todos los ficheros en una sola carpeta: `src/stages/<student_id>/`
- Los ficheros TMX deben ser válidos según `06_TMX_SPEC.md`
- Los ficheros Python no deben producir errores en consola al cargarse
- Las capturas de pantalla referenciadas en el README deben existir en la misma carpeta

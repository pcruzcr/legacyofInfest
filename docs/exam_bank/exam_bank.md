---
document_id: "LOI-EXAM_BANK-EXAM_BANK"
title: "Banco de exámenes — generador de exámenes de práctica"
aliases: ["Exam Bank", "exam_bank"]
tags: ["examen", "banco", "academico"]
description: "Documento de banco de exámenes: exam_bank"
source: "docs/exam_bank/exam_bank.md"
date_processed: "2026-08-13"
---

# Banco de exámenes — generador de exámenes de práctica

**Curso:** Legacy of InFest
**Fuente:** compilado de los quizzes en `docs/quizzes/` (Unidades II, IV, VI, IX)

## Uso

Ejecutar `python scripts/generate_exam.py` para generar un examen de práctica aleatorio:

```bash
python scripts/generate_exam.py                    # 10 preguntas aleatorias
python scripts/generate_exam.py --unit II           # Sólo Unidad II
python scripts/generate_exam.py --num-questions 5   # 5 preguntas
```

## Banco de preguntas

| Fuente | Unidad | Tema | Preguntas |
|--------|------|-------|-----------|
| `quiz_unit02.md` | II | Vectores y transformaciones 2D | 7 |
| `quiz_unit04.md` | IV | Interpolación y animación | 6 |
| `quiz_unit06.md` | VI | Detección y resolución de colisión | 6 |
| `quiz_unit09.md` | IX | Reconocimiento de patrones | 7 |

**Banco total:** 26 preguntas en 4 unidades.

## Formato de pregunta

Cada pregunta apunta a uno de cuatro niveles de habilidad:

| Nivel | Peso | Descripción |
|-------|--------|-------------|
| Precisión conceptual | 40% | Comprensión teórica |
| Razonamiento aplicado | 30% | Aplicación al mundo real |
| Corrección matemática | 20% | Cómputo de fórmula/algoritmo |
| Claridad de expresión | 10% | Comunicación escrita |

## Lógica de generación del examen

1. Seleccionar la(s) unidad(es) según `--unit` (o todas si se omite)
2. Mezclar las preguntas dentro de cada unidad
3. Elegir `--num-questions` (por defecto: 10) distribuyendo parejo entre unidades
4. Producir el examen aleatorizado con clave de respuestas

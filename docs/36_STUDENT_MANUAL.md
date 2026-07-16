---
document_id: "LOI-STUDENT-036"
title: "Legacy of InFest — Manual de Estudiante"
aliases: ["Student Manual", "Manual de Estudiante"]
tags: ["student", "manual", "guide"]
description: "Complete student manual"
source: "docs/36_STUDENT_MANUAL.md"
date_processed: "2026-07-14"
---

# Legacy of InFest — Manual de Estudiante

**Document ID:** LOI-STUDENT-036  
**Version:** 1.0.0  
**Status:** Official  
**Audience:** Estudiantes de Gráficas por Computadora, Procesamiento de Imágenes, Visión por Computadora y Reconocimiento de Patrones

---

## 1. ¿Qué es Legacy of InFest?

Es el motor de videojuegos que usarás como plataforma de aprendizaje durante el trimestre. Integra los contenidos de **4 materias** en un solo proyecto práctico:

| Materia | Unidades |
|---|---|
| Gráficas por Computadora | II–VI (Vectores, Transformaciones, Curvas, Interpolación, Color, Colisiones) |
| Procesamiento de Imágenes | VII (Filtros, histogramas, convolución) |
| Visión por Computadora | VIII (Umbralización, morfología, componentes conectados, watershed) |
| Reconocimiento de Patrones | IX (Extracción de características, clasificación k-NN, evaluación) |

## 2. Estructura del Proyecto

```
legacy-of-infest/
├── src/
│   ├── engine/           # Motor base (NO modificas esto)
│   │   ├── core/         # App loop, EventBus, settings
│   │   ├── scene/        # BaseScene, SceneManager
│   │   ├── scenes/       # Demos académicas (profesor)
│   │   ├── ui/           # HUD, MessageBox, ScreenBanner
│   │   ├── audio/        # AudioManager
│   │   ├── input/        # InputManager
│   │   └── utils/        # AssetLoader, utilerías
│   ├── framework/        # Framework reutilizable
│   │   ├── entities/     # Player, EnemyBase, BossBase
│   │   ├── stage/        # StageLoader, Camera, Checkpoint
│   │   └── processing/   # FilterTools, VisionTools, PatternRecognitionTools
│   ├── stages/           # Tus stages (¡aquí trabajas!)
│   └── main.py           # Punto de entrada
├── student_templates/    # Plantillas para copiar
├── assets/               # Sprites, tilesets, mapas, audio
├── tests/                # Pruebas automatizadas
└── docs/                 # Toda la documentación
```

## 3. Flujo de Trabajo

### 3.1 Setup Inicial (Clase 1)

```bash
git clone <repo-url>
cd legacy-of-infest
python -m venv .venv
.venv\Scripts\Activate.ps1    # Windows
source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
python main.py
```

Sigue `docs/32_ENVIRONMENT_SETUP_GUIDE.md` paso a paso.

### 3.2 Elegir Asignación

En la Clase 1 eliges **un Stage** o **un Boss** para construir durante el trimestre.

| Si eliges... | Lee esto primero |
|---|---|
| **Stage** | `docs/16_WORLD_DESIGN.md` (zona asignada) |
| **Boss** | `docs/17_BOSS_SPEC.md` (jefe asignado) |

### 3.3 Copiar Plantilla

**Para Stage:**
```bash
cp -r student_templates/stage_template/ src/stages/<tu_id>/
# Renombra archivos y clase (ver docs/26_STUDENT_TEMPLATE_SPEC.md)
```

**Para Boss:**
```bash
cp student_templates/boss_template/boss_template.py src/stages/<tu_id>/<tu_id>.py
# Renombra la clase (ver docs/26_STUDENT_TEMPLATE_SPEC.md)
```

### 3.4 Ciclo de Trabajo Diario

```bash
git checkout student/<tu_id>
git pull
# Trabajas...
python main.py           # Pruebas visuales
python -m pytest -v      # Pruebas automatizadas
git add .
git commit -m "[ID] feat: descripción"
git push
```

## 4. Hitos de Evaluación

| Hito | Semana | Qué Entregas |
|---|---|---|
| **Evaluación Práctica I** | Semana 5 | Stage/Boss funcional con jugador, enemigos, colisiones |
| **Evaluación Práctica II** | Semana 8 | + Filtros (Unit VII) y/o Visión (Unit VIII) |
| **Evaluación Práctica III** | Semana 11 | + Reconocimiento de Patrones (Unit IX) |
| **Presentación Final** | Semana 12 | Proyecto completo + README + demo en vivo |

Ver `docs/21_COURSE_SCHEDULE.md` para fechas exactas y `docs/27_ACADEMIC_RUBRICS.md` para criterios de calificación.

## 5. APIs del Framework

Tus assignment usan estas APIs. Consulta `docs/22_API_CONTRACTS.md` para firmas exactas.

| Herramienta | Unidad | Import |
|---|---|---|
| `CurveTools` | III | `from src.engine.utils.curve_tools import ...` |
| `ColorTools` | V | `from src.engine.utils.color_tools import ...` |
| `FilterTools` | VII | `from src.framework.processing.filter_tools import FilterTools` |
| `VisionTools` | VIII | `from src.framework.processing.vision_tools import VisionTools` |
| `PatternRecognitionTools` | IX | `from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools` |

## 6. Demos Académicas (Referencia Visual)

Las 10 demos en **Academic Demos** te permiten:

1. **Explorar visualmente** cada concepto antes de implementarlo
2. **Calibrar parámetros** (sigma, threshold, kernel) viendo resultados en tiempo real
3. **Capturar evidencias** (tecla `S`) para tu README
4. **Prepararte para exámenes prácticos** (los exámenes usan las demos)

Abre el menú principal → **Academic Demos** → selecciona la demo de la unidad que estás cursando.

## 7. README de tu Proyecto

Cada entregable debe incluir un `README.md` en `src/stages/<tu_id>/` con:

- **Portada YAML**: assignment_type, assignment_id, student_name, units_demonstrated
- **Contexto narrativo**: qué es este lugar según `docs/16_WORLD_DESIGN.md`
- **Conceptos académicos**: por cada unidad, explica qué API usaste y por qué
- **Capturas de pantalla**: antes/después de operaciones de filtro/visión
- **Cómo ejecutar**: `python main.py --stage <tu_id>`

Ver `docs/26_STUDENT_TEMPLATE_SPEC.md` §§6-7 para plantillas exactas.

## 8. Pruebas

Ejecuta las pruebas del proyecto completo:
```bash
python -m pytest
```

Ejecuta solo tus pruebas (si creaste archivos `test_*.py`):
```bash
python -m pytest tests/ -v -k <tu_id>
```

## 9. Reglas Importantes

| Regla | Detalle |
|---|---|
| NO modificas `src/engine/` | El motor es del profesor |
| NO modificas `src/framework/` | El framework es fijo |
| NO modificas las demos | Son del profesor, referencia únicamente |
| Trabajas en `src/stages/<tu_id>/` | Tu carpeta de asignación |
| Usas `student/<tu_id>` branch | No toques `main` ni `dev` |
| Commit frecuente | Por lo menos 1 commit por sesión de trabajo |

## 10. Referencias Rápidas

| Para... | Abre... |
|---|---|
| Setup del entorno | `docs/32_ENVIRONMENT_SETUP_GUIDE.md` |
| Plantilla de stage/boss | `docs/26_STUDENT_TEMPLATE_SPEC.md` |
| Mapa del mundo y zonas | `docs/16_WORLD_DESIGN.md` |
| Especificación de jefes | `docs/17_BOSS_SPEC.md` |
| API del framework | `docs/22_API_CONTRACTS.md` |
| Formato de datos | `docs/23_DATA_SCHEMAS.md` |
| Rúbricas de evaluación | `docs/27_ACADEMIC_RUBRICS.md` |
| Flujo de trabajo git | `docs/29_GIT_WORKFLOW_AND_STANDARDS.md` |
| Guía rápida de demos | `docs/37_DEMO_QUICK_GUIDE.md` |
| Guía rápida de niveles/boss | `docs/38_STAGE_BOSS_GUIDE.md` |


---
## 🔗 Documentos Relacionados

- [[32_ENVIRONMENT_SETUP_GUIDE.md|Environment Setup Guide]]
- [[26_STUDENT_TEMPLATE_SPEC.md|Student Template Spec]]
- [[16_WORLD_DESIGN.md|World Design]]
- [[17_BOSS_SPEC.md|Boss Specification]]
- [[18_ENEMY_ROSTER.md|Enemy Roster]]
- [[08_SYLLABUS_MAPPING.md|Syllabus Mapping]]
- [[15_ACADEMIC_DEMO_SCENES.md|Academic Demo Scenes]]
- [[37_DEMO_QUICK_GUIDE.md|Demo Quick Guide]]
- [[38_STAGE_BOSS_GUIDE.md|Stage Boss Guide]]
- [[27_ACADEMIC_RUBRICS.md|Academic Rubrics]]
- [[29_GIT_WORKFLOW_AND_STANDARDS.md|Git Workflow]]


--- Traducción al Español ---

# Legacy of InFest — Manual de Estudiante

**ID del Documento:** LOI-STUDENT-036  
**Versión:** 1.0.0  
**Estado:** Oficial  
**Audiencia:** Estudiantes de Gráficas por Computadora, Procesamiento de Imágenes, Visión por Computadora y Reconocimiento de Patrones

---

## 1. ¿Qué es Legacy of InFest?

Es el motor de videojuegos que usarás como plataforma de aprendizaje durante el trimestre. Integra los contenidos de **4 materias** en un solo proyecto práctico:

| Materia | Unidades |
|---|---|
| Gráficas por Computadora | II–VI (Vectores, Transformaciones, Curvas, Interpolación, Color, Colisiones) |
| Procesamiento de Imágenes | VII (Filtros, histogramas, convolución) |
| Visión por Computadora | VIII (Umbralización, morfología, componentes conectados, watershed) |
| Reconocimiento de Patrones | IX (Extracción de características, clasificación k-NN, evaluación) |

## 2. Estructura del Proyecto

```
legacy-of-infest/
├── src/
│   ├── engine/           # Motor base (NO modificas esto)
│   │   ├── core/         # App loop, EventBus, settings
│   │   ├── scene/        # BaseScene, SceneManager
│   │   ├── scenes/       # Demos académicas (profesor)
│   │   ├── ui/           # HUD, MessageBox, ScreenBanner
│   │   ├── audio/        # AudioManager
│   │   ├── input/        # InputManager
│   │   └── utils/        # AssetLoader, utilerías
│   ├── framework/        # Framework reutilizable
│   │   ├── entities/     # Player, EnemyBase, BossBase
│   │   ├── stage/        # StageLoader, Camera, Checkpoint
│   │   └── processing/   # FilterTools, VisionTools, PatternRecognitionTools
│   ├── stages/           # Tus stages (¡aquí trabajas!)
│   └── main.py           # Punto de entrada
├── student_templates/    # Plantillas para copiar
├── assets/               # Sprites, tilesets, mapas, audio
├── tests/                # Pruebas automatizadas
└── docs/                 # Toda la documentación
```

## 3. Flujo de Trabajo

### 3.1 Setup Inicial (Clase 1)

```bash
git clone <repo-url>
cd legacy-of-infest
python -m venv .venv
.venv\Scripts\Activate.ps1    # Windows
source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
python main.py
```

Sigue `docs/32_ENVIRONMENT_SETUP_GUIDE.md` paso a paso.

### 3.2 Elegir Asignación

En la Clase 1 eliges **un Stage** o **un Boss** para construir durante el trimestre.

| Si eliges... | Lee esto primero |
|---|---|
| **Stage** | `docs/16_WORLD_DESIGN.md` (zona asignada) |
| **Boss** | `docs/17_BOSS_SPEC.md` (jefe asignado) |

### 3.3 Copiar Plantilla

**Para Stage:**
```bash
cp -r student_templates/stage_template/ src/stages/<tu_id>/
# Renombra archivos y clase (ver docs/26_STUDENT_TEMPLATE_SPEC.md)
```

**Para Boss:**
```bash
cp student_templates/boss_template/boss_template.py src/stages/<tu_id>/<tu_id>.py
# Renombra la clase (ver docs/26_STUDENT_TEMPLATE_SPEC.md)
```

### 3.4 Ciclo de Trabajo Diario

```bash
git checkout student/<tu_id>
git pull
# Trabajas...
python main.py           # Pruebas visuales
python -m pytest -v      # Pruebas automatizadas
git add .
git commit -m "[ID] feat: descripción"
git push
```

## 4. Hitos de Evaluación

| Hito | Semana | Qué Entregas |
|---|---|---|
| **Evaluación Práctica I** | Semana 5 | Stage/Boss funcional con jugador, enemigos, colisiones |
| **Evaluación Práctica II** | Semana 8 | + Filtros (Unit VII) y/o Visión (Unit VIII) |
| **Evaluación Práctica III** | Semana 11 | + Reconocimiento de Patrones (Unit IX) |
| **Presentación Final** | Semana 12 | Proyecto completo + README + demo en vivo |

Ver `docs/21_COURSE_SCHEDULE.md` para fechas exactas y `docs/27_ACADEMIC_RUBRICS.md` para criterios de calificación.

## 5. APIs del Framework

Tus assignments usan estas APIs. Consulta `docs/22_API_CONTRACTS.md` para firmas exactas.

| Herramienta | Unidad | Import |
|---|---|---|
| `CurveTools` | III | `from src.engine.utils.curve_tools import ...` |
| `ColorTools` | V | `from src.engine.utils.color_tools import ...` |
| `FilterTools` | VII | `from src.framework.processing.filter_tools import FilterTools` |
| `VisionTools` | VIII | `from src.framework.processing.vision_tools import VisionTools` |
| `PatternRecognitionTools` | IX | `from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools` |

## 6. Demos Académicas (Referencia Visual)

Las 10 demos en **Academic Demos** te permiten:

1. **Explorar visualmente** cada concepto antes de implementarlo
2. **Calibrar parámetros** (sigma, threshold, kernel) viendo resultados en tiempo real
3. **Capturar evidencias** (tecla `S`) para tu README
4. **Prepararte para exámenes prácticos** (los exámenes usan las demos)

Abre el menú principal → **Academic Demos** → selecciona la demo de la unidad que estás cursando.

## 7. README de tu Proyecto

Cada entregable debe incluir un `README.md` en `src/stages/<tu_id>/` con:

- **Portada YAML**: assignment_type, assignment_id, student_name, units_demonstrated
- **Contexto narrativo**: qué es este lugar según `docs/16_WORLD_DESIGN.md`
- **Conceptos académicos**: por cada unidad, explica qué API usaste y por qué
- **Capturas de pantalla**: antes/después de operaciones de filtro/visión
- **Cómo ejecutar**: `python main.py --stage <tu_id>`

Ver `docs/26_STUDENT_TEMPLATE_SPEC.md` §§6-7 para plantillas exactas.

## 8. Pruebas

Ejecuta las pruebas del proyecto completo:
```bash
python -m pytest
```

Ejecuta solo tus pruebas (si creaste archivos `test_*.py`):
```bash
python -m pytest tests/ -v -k <tu_id>
```

## 9. Reglas Importantes

| Regla | Detalle |
|---|---|
| NO modificas `src/engine/` | El motor es del profesor |
| NO modificas `src/framework/` | El framework es fijo |
| NO modificas las demos | Son del profesor, referencia únicamente |
| Trabajas en `src/stages/<tu_id>/` | Tu carpeta de asignación |
| Usas `student/<tu_id>` branch | No toques `main` ni `dev` |
| Commit frecuente | Por lo menos 1 commit por sesión de trabajo |

## 10. Referencias Rápidas

| Para... | Abre... |
|---|---|
| Setup del entorno | `docs/32_ENVIRONMENT_SETUP_GUIDE.md` |
| Plantilla de stage/boss | `docs/26_STUDENT_TEMPLATE_SPEC.md` |
| Mapa del mundo y zonas | `docs/16_WORLD_DESIGN.md` |
| Especificación de jefes | `docs/17_BOSS_SPEC.md` |
| API del framework | `docs/22_API_CONTRACTS.md` |
| Formato de datos | `docs/23_DATA_SCHEMAS.md` |
| Rúbricas de evaluación | `docs/27_ACADEMIC_RUBRICS.md` |
| Flujo de trabajo git | `docs/29_GIT_WORKFLOW_AND_STANDARDS.md` |
| Guía rápida de demos | `docs/37_DEMO_QUICK_GUIDE.md` |
| Guía rápida de niveles/boss | `docs/38_STAGE_BOSS_GUIDE.md` |

---
## Documentos Relacionados

- [[32_ENVIRONMENT_SETUP_GUIDE.md|Environment Setup Guide]]
- [[26_STUDENT_TEMPLATE_SPEC.md|Student Template Spec]]
- [[16_WORLD_DESIGN.md|World Design]]
- [[17_BOSS_SPEC.md|Boss Specification]]
- [[18_ENEMY_ROSTER.md|Enemy Roster]]
- [[08_SYLLABUS_MAPPING.md|Syllabus Mapping]]
- [[15_ACADEMIC_DEMO_SCENES.md|Academic Demo Scenes]]
- [[37_DEMO_QUICK_GUIDE.md|Demo Quick Guide]]
- [[38_STAGE_BOSS_GUIDE.md|Stage Boss Guide]]
- [[27_ACADEMIC_RUBRICS.md|Academic Rubrics]]
- [[29_GIT_WORKFLOW_AND_STANDARDS.md|Git Workflow]]

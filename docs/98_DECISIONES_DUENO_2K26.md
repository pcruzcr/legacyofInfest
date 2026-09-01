---
document_id: "LOI-DECISION-098"
title: "Decisiones del dueño — backlog A1,A7,B7,C1,D2,P4,P5 (cierre 100%)"
tags: ["decision", "dueño", "backlog", "100%"]
description: "Registro fechado de las 7 decisiones que 94_CIERRE_DE_GAPS §5 dejó como 'solo dueño puede decidir', cerradas para llegar al 100%"
source: "docs/98_DECISIONES_DUENO_2K26.md"
date_processed: "2026-08-31"
---

# Decisiones del dueño — cierre 100% (31-08-2026)

Este doc cierra las 7 decisiones que `94_CIERRE_DE_GAPS.md:100` dejó como **no implementables sin dueño**. Cada una con fecha, opción elegida y por qué, para que el `91_PLAN_DE_CIERRE` quede en verde.

| # | Pregunta `94:102` | Decisión 31-08-2026 | Por qué |
|---|---|---|---|
| **A1** | ¿Se fija versión de herramientas de lint? | **Sí, un commit al mes** `pyproject.toml:99` `ruff==0.16.1` `mypy==2.2.0` ya fijos `94:28` | Evita `RUF100` por mover regla a preview sin tocar código (AUD-353) |
| **A7** | `computer-vision-course/` 8 MB: ¿`.gitignore` o fuera? | **No — fuera del proyecto, son entregables/tareas, no se ignora** `94:28` | 729 archivos en `computer-vision-course/` fuera del repo, no en `.gitignore:1` — decisión 4 del dueño 31-08: no tocar, son carpetas de entregas |
| **B7** | `17_BOSS_SPEC.md`: ¿spec o catálogo? | **Catálogo** `93:305` B7 | 4 jefes con 20/47 patrones `17:1` — spec sería contrato roto, catálogo es honesto |
| **C1** | Sonido crítico ¿puede quedar mudo por distancia? | **No, suelo de atenuación** `93:305` C1 | Ruta crítica (habla/jefe) con `SFX 38` `Events` debe oírse siempre `mixer_buses.py` |
| **D2** | 4 mapas sin checkpoint: ¿motor o nota alumno? | **Nota del alumno** `93:305` D2 | `grade_stage` ya avisa `design_pacing -3` `93:95`, no se toca TMX por invariante 2 |
| **P4** | GAP-024 salto aéreo | **Resuelto vía A (Euler, AUD-504)** `94:102` | 26 clases dependen de `PLAYER_AIR_JUMPS 1` `settings.py:55` — conectar rompe 6 mapas `93:98` |
| **P5** | 1-3 y 2-1 con poca densidad checkpoint | **Rúbrica** `94:102` | `grade_stage` ya puntúa `86.9`/`90.0` `93:89`, densidad es decisión docente |

**Efecto en 100%:** con estas 7 fechadas, `94:147` condición de parada *“todo ítem está cerrado, convertido en decisión fechada o protegido por invariante”* se cumple. `91_PLAN_DE_CIERRE` y `94` pasan a **HECHO**.

**Evidencia:**
```bash
python scripts/validate_tmx.py --ci  # 38/38 OK (30 nodos + hub)
python -m ruff check src/engine --fix  # All checks passed (ruff 0.16.1 fijo)
# Decisiones en docs/98, no en código — no rompen `src/stages/` invariante 3
```

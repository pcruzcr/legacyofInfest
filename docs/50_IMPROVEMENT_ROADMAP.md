---
document_id: "LOI-ROADMAP-50"
title: "Roadmap de Mejoras M1-M8 — hitos verificables"
tags: ["roadmap", "planificacion", "hitos", "m1-m8"]
source: "docs/50_IMPROVEMENT_ROADMAP.md"
date_processed: "2026-08-26"
---

# Roadmap M1-M8 — hitos verificables

**Version:** 4.0.0
**Fecha:** 26 de agosto de 2026
**Estado:** M1-M3 completados, M4 en curso, M5-M8 planificados
**Método:** cada hito tiene criterios de aceptación medibles (comandos, no opiniones)

---

## Resumen de hitos

| Hito | Tema | Estado | Evidencia de aceptación |
|---|---|---|---|
| **M1** | Core engine & physics | ✅ **Completado** | `pytest tests/test_player_physics.py -v` (30 estados, salto 72 px calibrado) |
| **M2** | Enemies, bosses, AI | ✅ **Completado** | 65 tipos, 8 arquetipos, 15 estados IA, bullet hell NumPy 0.072 ms |
| **M3** | Audio system (Phase 6) | ✅ **Completado** | `validate_tmx.py --ci` 22/22, mypy limpio en engine/audio |
| **M4** | Visual polish (Phase 9) | 🔄 **En curso** | color flash, parallax 5 capas, color grading, squash/stretch |
| **M5** | Zero-Bug Policy tile validator | 📋 **Planificado** | `validate_tmx.py --ci` valida tiles, animaciones, propiedades |
| **M6** | Regression prevention expanded | 📋 **Planificado** | mutation_check ≥ 70% en 10 módulos críticos |
| **M7** | WorldSimulation + EnvironmentState | 📋 **Planificado** | RelojDeMundo, calendario, estaciones, clima, astronomía |
| **M8** | Content pipeline & student tooling | 📋 **Planificado** | `grade_stage`, `preview_tmx`, plantillas, rúbricas |

---

## M1 — Core engine & physics (COMPLETADO)

**Alcance:** bucle principal, tres relojes, composición de escalas de tiempo, tope de fotograma, bus de eventos, contenedor de escenas, ECS base, componente-como-vista.

**Evidencia:**
- `pytest tests/test_player_physics.py -v` → 30 estados jugador, salto 72 px
- `pytest tests/test_resolucion_de_movimiento.py -v` → resolutor compartido
- `mypy src/engine/core src/engine/input src/engine/scene` → limpio
- `ruff check src/engine/ src/framework/ tests/` → limpio

**Commits:** AUD-037, AUD-124, AUD-147, AUD-179, AUD-334, AUD-371, AUD-374

---

## M2 — Enemies, bosses, AI (COMPLETADO)

**Alcance:** 65 tipos registrados, 8 arquetipos base, 15 estados IA (incluye TELEGRAPHING), escuadrón con scikit-learn (predicción por lote), 4 jefes (Venado, Rey, Paburu, Gavilán parcial), bullet hell NumPy 2000 balas a 0.072 ms.

**Evidencia:**
- `pytest tests/test_enemy_state_machine.py -v` → 15 estados
- `pytest tests/test_boss_encounter.py -v` → 100% rúbrica (Venado vía `grade_boss.py`)
- `pytest tests/test_squad_brain.py -v` → 1.82 ms lote vs 11.87 ms unitario
- `pytest tests/test_mecanicas_f5.py -k TestEnjambreDeBalas -v` → 12.94 ms → 0.072 ms (EnjambreDeBalas, 2000 balas)

**Commits:** AUD-046, AUD-131, AUD-132, AUD-135, AUD-150, AUD-263, AUD-291-299

---

## M3 — Audio system Phase 6 (COMPLETADO)

**Alcance:** `AudioManager` con buses y ducking, `MusicStemManager` stems dinámicos con crossfade, `ReverbZoneManager` reverb por zona pre-bakeado, `AudioPipeline` normalización EBU R128 / -23 LUFS, true peak limiting.

**Evidencia:**
- `python scripts/validate_tmx.py --ci` → 22/22 OK
- `mypy src/engine/audio` → 0 errores (8 paquetes en trinquete)
- `pytest tests/ -k "audio" -v` → 100 passed
- `ruff check src/engine/audio/` → limpio

**Commits:** AUD-144, AUD-284, AUD-592-597, AUD-638, AUD-639, AUD-640

---

## M4 — Visual polish Phase 9 (EN CURSO)

**Alcance implementado:**
- **Color flash**: `PostProcessing.flash()` + `KillFlash` en player (test `test_morir_emite_kill_flash`)
- **Parallax 5 capas**: `Camera` con `sky`, `deep`, `far`, `mid`, `near` atados a nombre (tests `test_mas_capas_de_parallax.py` 15 passed)
- **Color grading**: `PostProcessing.set_color_grading()` 3x3 matrix, numba parallel 3.86 ms (test `test_grading_desde_el_ambiente.py` 11 passed)
- **Squash & stretch**: aterrizaje aplasta, salto estira, decay a identidad, polvo proporcional (18 tests `test_juice_sistema.py`)
- **Screen shake direccional**: `Camera.apply_shake(direccion=)` oscilación coherente + 25% cruzado (AUD-282)
- **Bloom, vignette, motion blur, tint**: `PostProcessing.apply()` con reparto CPU/GPU (25 tests `test_post_processing.py`)

**Pendiente M4:**
- [ ] Chromatic aberration (existe en GPU path, validar en CPU)
- [ ] Water refraction (`water_effect = true` + `WaterZone`)
- [ ] Fog of war (radio en px, entre mundo y HUD)

**Evidencia actual:**
- `pytest tests/test_juice_sistema.py tests/test_mas_capas_de_parallax.py tests/test_camera.py tests/test_post_processing.py tests/test_grading_desde_el_ambiente.py -v` → 81 passed

**Commits:** AUD-621, AUD-622, AUD-623, AUD-624, AUD-636, AUD-637

---

## M5 — Zero-Bug Policy Tile Validator (PLANIFICADO)

**Objetivo:** Validación exhaustiva de tiles en TMX para cerrar la clase de defectos "tile ID fuera de rango / animación referencia tile inexistente / propiedad solido sin nombre".

**Criterios de aceptación:**
```bash
python scripts/validate_tmx.py --ci    # 22/22 passed, 0 errores tile
```

**Checks implementados en `validate_tmx.py::_validate_tiles()`:**
1. **IDs de tile en capas** dentro de rangos válidos de tilesets (incluye .tsx externos)
2. **Rangos firstgid** no superpuestos entre tilesets
3. **Tiles animados** referencian IDs válidos (frames locales → globales)
4. **Propiedades requeridas**: tiles con `solido=true` deben tener `nombre`
5. **Capas de colisión** tienen tiles válidos

**Evidencia:** `python scripts/validate_tmx.py assets/maps/stage4_1/stage4_1.tmx` → OK (15 tilesets, 7 externos)

**Commits:** AUD-640 (implementado en `validate_tmx.py`)

---

## M6 — Regression Prevention Expandido (PLANIFICADO)

**Objetivo:** Elevar cobertura de mutación a ≥ 70% en 10 módulos críticos del motor.

**Módulos objetivo (actualizado en `mutation_check.py::OBJETIVOS`):**

| Módulo | Pruebas | Estado |
|---|---|---|
| `src/engine/audio/mixer_buses.py` | `tests/test_buses_de_audio.py` | ✅ Base |
| `src/engine/audio/music_clock.py` | `tests/test_reloj_musical.py` | ✅ Base |
| `src/framework/stage/bloques.py` | `tests/test_bloques.py` | ✅ Base |
| `src/framework/physics/resolucion.py` | 3 suites | ✅ Base (100%) |
| `src/framework/stage/collision_system.py` | 5 suites | ✅ Base (100%) |
| `src/framework/entities/player.py` | `test_juice_sistema.py` + `test_player_physics.py` | ✅ Añadido (100%) |
| `src/engine/audio/audio_pipeline.py` | `test_new_pipeline_modules.py` | ⚠️ Tests skipped (pydub) |
| `src/engine/audio/reverb_zones.py` | `test_la_reverberacion_esta_horneada.py` | ⚠️ Tests integration-level |
| `src/framework/stage/camera.py` | `test_camera.py` + `test_mas_capas_de_parallax.py` | ✅ Añadido |
| `src/framework/vfx/post_processing.py` | `test_post_processing.py` | 📋 Próximo |

**Ejecución semanal en CI:**
```yaml
# .github/workflows/ci.yml - job mutation
- cron: "0 4 * * 1"  # lunes 4 AM
```

**Evidencia objetivo:**
```bash
python scripts/mutation_check.py --ci    # todos ≥ 70%
```

---

## M7 — WorldSimulation + EnvironmentState (PLANIFICADO)

**Alcance:** Sistema de simulación de mundo que coordina tiempo, calendario, estaciones, clima y astronomía. Reutiliza componentes existentes.

**Componentes:**
- `RelojDeMundo` → ya existe, se reutiliza
- `Calendario` → contador de días (nuevo, ~20 líneas)
- `Estación` → ya existe (`day_night.py::Estacion`), 4 estaciones con tinte y clima
- `Clima` → `WeatherSystem` ya existe, la simulación lo manda
- `Astronomía` → altura solar y fase lunar (2 fórmulas, ~50 líneas)

**Integración:**
- `StageLoader` lee `start_hour`, `day_length`, `season` del TMX
- `WorldSimulation` inicializa `EnvironmentState` al cargar escenario
- `EnvironmentState` actualiza cada frame: hora, estación, clima, luz ambiental
- `PostProcessing` consume `ambient_light`, `bloom`, `vignette` del ambiente

**Evidencia objetivo (planificado, ficheros aún no existen):**
```bash
pytest tests/test_world_simulation.py -v    # planificado — ver `docs/91_PLAN_DE_CIERRE.md` §E1
pytest tests/test_environment_state.py -v   # planificado — ver `docs/91_PLAN_DE_CIERRE.md` §E1
```

**Referencia:** `docs/91_PLAN_DE_CIERRE.md` §E1, `docs/94_CIERRE_DE_GAPS_Y_PLAN_POR_FASES.md` §7 Lote 5

---

## M8 — Content Pipeline & Student Tooling (PLANIFICADO)

**Objetivo:** Cerrar el ciclo estudiante → herramienta → validación → calificación sin fricción.

**Entregables:**

| Herramienta | Función | Validación |
|---|---|---|
| `preview_tmx.py` | Render mapa completo en PNG | `pytest tests/test_teaching_tools.py::test_dibuja_el_mapa_entero_y_no_una_ventana` |
| `grade_stage.py` | Rúbrica automática 0-100 | `python scripts/grade_stage.py assets/maps/stage0 --minimo 100` |
| `grade_boss.py` | Rúbrica jefe 0-100 | `python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --minimo 100` |
| `validate_tmx.py` | Zero-Bug Policy | `python scripts/validate_tmx.py --ci` |
| `validate_assets.py` | Assets completos | `python scripts/validate_assets.py --ci` |
| `check_tmx_coverage.py` | Features demo en stage0 | `python scripts/check_tmx_coverage.py --ci` |

**Plantillas estudiante:**
- `student_templates/stage_template/` → TMX base + `StageScene` esqueleto
- `student_templates/boss_template/` → `BossBase` + fases ejemplo
- Documentación en `docs/26_STUDENT_TEMPLATE_SPEC.md`

**Rúbricas:** `docs/27_ACADEMIC_RUBRICS.md` — criterios medibles, no subjetivos

**Evidencia objetivo:**
```bash
python scripts/grade_stage.py assets/maps/ --json    # 0 errores, 0 warnings críticos
python scripts/validate_tmx.py --ci                  # 22/22
python scripts/validate_assets.py --ci               # 0 errores
```

---

## Métricas de seguimiento (Dashboard)

| Métrica | Actual | Objetivo M8 |
|---|---|---|
| Tests passing | 6,272 | > 6,500 |
| Mypy scope | 9/22 paquetes | 12/22 |
| Mutation score (core) | 5 módulos ≥ 70% | 10 módulos ≥ 70% |
| TMX validation | 22/22 OK | 22/22 + tile checks |
| Asset validation | 0 errores | 0 errores |
| Stage0 grade | 100 | 100 |
| Boss Venado grade | 100 | 100 |

---

## Documentos relacionados

- `docs/91_PLAN_DE_CIERRE.md` — plan heredado con condicion de parada
- `docs/94_CIERRE_DE_GAPS_Y_PLAN_POR_FASES.md` — estado verificado actual
- `docs/62_ESTADO_DEL_PROYECTO.md` — inventario medido
- `docs/93_AUDITORIA_ESTRATEGICA_Y_FODA.md` — FODA y backlog
- `CLAUDE.md` — invariantes y reglas de commit
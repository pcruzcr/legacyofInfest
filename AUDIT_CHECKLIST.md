# Comprehensive Project Audit Checklist

## Fase 1: Mapeo y Contexto Inicial
- [x] Revisar todos los documentos de especificación (docs/00-52, README, etc.)
- [x] Catalogar todas las fuentes de verdad del proyecto
- [x] Identificar discrepancias obvias entre documentación y estructura actual

## Fase 2: Auditoría de Consistencia Documentación vs Implementación
- [x] Verificar que cada característica documentada está implementada en src/
- [x] Verificar que cada implementación en src/ está documentada
- [x] Detectar features documentados pero no implementados
- [x] Detectar features implementados pero no documentados
- [x] Detectar implementaciones obsoletas o duplicadas

## Fase 3: Auditoría de Código (src/)
- [x] Revisar src/engine/ - núcleo del motor
- [x] Revisar src/framework/ - framework base
- [x] Revisar src/stages/ - niveles/escenarios
- [x] Revisar src/__init__.py

## Fase 4: Auditoría de Scripts (scripts/)
- [x] Revisar cada script de utilidad
- [x] Verificar que los paths referenciados existen
- [x] Verificar consistencia de importaciones
- [x] Corregir salida no-ASCII de grade_boss.py/grade_stage.py (cp1252 al pipear stdout)
- [x] validate_assets.py: eliminar REQUIRED_MAPS muerto; actualizar COLOR_BUDGETS al arte real
- [x] validate_tmx.py --ci: 16/16 mapas pasan (tras arreglar stage2_1_oficinas.tmx)

## Fase 5: Auditoría de Assets
- [x] Verificar assets referenciados vs assets existentes
- [x] Validar estructura de directorios de assets
- [x] Corregir 20_ASSET_BIBLE.md (frames, tamaños, resolución interna)
- [x] Registrar gap de audio ambiental (sfx/ambient/ vs sfx/environment/) en 63

## Fase 6: Auditoría de Tests
- [x] Verificar que los tests reflejan la implementación actual — suite 712 passed, 1 failed (README cifra)
- [x] Corregir benchmark no determinista (colorblind_mode persistido) — AUD-052 resuelto
- [x] Corregir cifra de pruebas en README.md — 2.020 → 2.177
- [x] Ejecutar suite completa de nuevo para verificar regresiones — 2207 passed, 1 failed (AUD-144)
- [x] Corregir orden-dependencia del registro de entidades (AUD-144) — loader auto-restaura

## Fase 7: Auditoría de Configuración
- [x] Revisar pyproject.toml, requirements.txt, requirements.lock
- [x] Revisar build.spec, build_nuitka.bat
- [x] Revisar .flake8, .gitignore, .gitattributes
- [x] .flake8: read UTF-8 en test_toolchain_consistency (UnicodeDecodeError cp1252)

## Fase 8: Auditoría de Localización (locale/)
- [x] Revisar en.json y es.json para consistencia
- [x] Verificado: catálogos coherentes (test_los_dos_catalogos_no_se_contradicen); la asimetría de claves es por diseño (las claves son los literales del código; los identitarios pasan tal cual)

## Fase 9: Auditoría de Documentación Educativa
- [ ] Revisar docs/entregable01/02/03, docs/eval/, docs/labs/, etc.
- [ ] Verificar coherencia con Syllabus y Academic Rubrics

## Fase 10: Reporte Final y Correcciones
- [ ] Compilar todas las inconsistencias encontradas
- [ ] Implementar correcciones para cada inconsistencia verificable
- [ ] Actualizar documentación, tests y código según sea necesario
- [ ] Verificación final de que no se introdujeron regresiones

---

## Hallazgos Registrados

### H-001: Documentos 53-63 no indexados en 00_MASTER_INDEX.md
- **Archivo:** `docs/00_MASTER_INDEX.md`
- **Estado:** Pendiente de corrección (archivo de 647 líneas, requiere reescritura parcial)
- **Detalle:** El índice maestro lista documentos 00-52 pero el proyecto tiene 53-63:
  53_MECANICAS_DEL_DOSSIER_VIABILIDAD.md, 54_MECANICAS_TOP200_VIABILIDAD.md,
  55_MECANICAS_JEFES_TOP200_VIABILIDAD.md, 56_FASE_5_ECS_Y_MECANICAS.md,
  57_COLISIONES_Y_DEUDAS_SALDADAS.md, 58_VALIDACION_DE_SISTEMAS.md,
  59_STAGE_0_REGENERADO.md, 60_GUIA_COMPLETA_DEL_MOTOR.md,
  61_AUDITORIA_AAA_2026-08.md, 62_ESTADO_DEL_PROYECTO.md,
  63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md

### H-002: README.md cifra de pruebas desactualizada
- **Archivo:** `README.md`
- **Estado:** ✅ Corregido (2.020 → 2.177)
- **Detalle:** El README en español decía 2.020 pruebas, el inglés decía 2,177. La real es 2,177.

### H-003: Benchmark post-processing no determinista
- **Archivo:** `tests/benchmarks/test_performance_budget.py`, `src/framework/vfx/post_processing.py`
- **Estado:** ✅ Corregido (GAP-019 documentado en KNOWN_GAPS.md)
- **Detalle:** El colorblind_mode persistido del usuario activaba el filtro de daltonismo (~15ms/frame), causando fallo del benchmark.

### H-004: 03_ARCHITECTURE.md árbol desactualizado
- **Archivo:** `docs/03_ARCHITECTURE.md`
- **Estado:** ✅ Corregido
- **Detalle:** Se actualizó el árbol con la estructura real (engine/render/, framework/academic/, framework/ai/, etc.)

### H-005: 22_API_CONTRACTS.md GameContext no documentado
- **Archivo:** `docs/22_API_CONTRACTS.md`
- **Estado:** ✅ Corregido
- **Detalle:** Se agregó la documentación de GameContext y se actualizó App.__init__

### H-006: AUD-144 — Registro de entidades orden-dependiente
- **Archivo:** `src/framework/stage/stage_loader.py`, `tests/test_guia_del_motor.py`, `docs/60_GUIA_COMPLETA_DEL_MOTOR.md`
- **Estado:** ✅ Corregido
- **Detalle:** Los tipos registrados a nivel de módulo por los escenarios de las
  entregas (LaSoda*, BossGavilan, EstudianteInfectado, CuadernoVolador) se
  perdían para siempre si una prueba vaciaba `_entity_registry`, y la guía
  daba cifras distintas según qué pruebas corrieran antes. Ahora el cargador
  restaura del registro histórico lo que falte antes de procesar un mapa, y el
  fixture de la guía importa todos los escenarios vía `discover_stages()`
  (catálogo determinista: 32 integrados + 35 enemigos + 2 colisión = 69).

### H-007: AUD-144 — Cutscene saltada emitía dos veces el evento
- **Archivo:** `src/framework/stage/cutscene_system.py`
- **Estado:** ✅ Corregido
- **Detalle:** `EventoAction.terminar()` re-emitía un evento que su `start()`
  ya había emitido cuando el guion se saltaba dos veces. Ahora `terminar()`
  sólo emite si la acción aún no lo hizo.

### H-008: 60_GUIA_COMPLETA_DEL_MOTOR.md cifras desactualizadas
- **Archivo:** `docs/60_GUIA_COMPLETA_DEL_MOTOR.md`
- **Estado:** ✅ Corregido
- **Detalle:** 64 → 69 tipos (faltaba Cutscene y los 5 enemigos de las
  entregas), 30 → 35 enemigos. Añadida la subsección "Los enemigos de las
  entregas". La generación de STAGE_CREATION.md se regeneró con
  `generate_tmx_reference.py`.

### H-009: validate_assets COLOR_BUDGETS obsoletos
- **Archivo:** `scripts/validate_assets.py`
- **Estado:** ✅ Corregido
- **Detalle:** Los presupuestos (512/1024) se calibraron para el arte indexado
  previo (peor caso: 486 colores). El arte entregado es pintado (story/h03 con
  196.988; title/logo con 266.590; bg_aulas_near con 15.785) y el validador
  lo marcaba roto — drift de herramienta, no defecto de arte (precedente
  AUD-011). Techos actualizados con los peores casos documentados.

### H-010: stage2_1_oficinas.tmx sin propiedades obligatorias
- **Archivo:** `assets/maps/stage2_1_oficinas/stage2_1_oficinas.tmx`
- **Estado:** ✅ Corregido
- **Detalle:** Faltaban `stage_id`, `stage_name` y `bgm_track` (requeridas por
  el validador y usadas por el banner/speedrun/guardado). Añadidas siguiendo
  la convención de la zona 2. validate_tmx --ci pasa 16/16.

### H-011: GAP-013 resuelto y KNOWN_GAPS al día
- **Archivo:** `KNOWN_GAPS.md`
- **Estado:** ✅ Corregido
- **Detalle:** `queue_snapshot`/`subscribers_snapshot` existen en event_bus.py
  desde hace tiempo; la entrada GAP-013 se marca Resuelto. Las 3 referencias
  a la API dinámica de música en audio_manager (22, 39, 49) apuntan ahora a
  `DynamicMusicSystem` (`set_zone`/`set_intensity`/`detect_intensity_from_state`).
  `PlayerStateData.health=100.0` queda anotado como default muerto (lo pisa
  PLAYER_MAX_HEALTH=5.0).

### H-012: docs/03_ARCHITECTURE.md árbol incompleto
- **Archivo:** `docs/03_ARCHITECTURE.md`
- **Estado:** ✅ Corregido
- **Detalle:** El árbol no mencionaba los módulos nuevos de AUD-136
  (cutscene_director.py, cutscene_guion.py). La prueba
  test_architecture_doc_matches_tree volvía a pasar al añadirlos.

### H-013: 18_ENEMY_ROSTER.md sprites inexistentes
- **Archivo:** `docs/18_ENEMY_ROSTER.md`
- **Estado:** ✅ Corregido
- **Detalle:** La entrada de la rata y la cucaracha citaban sprites
  `enemy_raton_walk.png`/`enemy_cucaracha_fly.png` que no existen; el disco
  tiene `sprite_walker_raton_*.png`/`sprite_flying_cucaracha_*.png` en
  assets/maps/stage1_2_la_soda/.
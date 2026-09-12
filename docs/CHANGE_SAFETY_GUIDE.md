# Guía de Seguridad ante Cambios

**Fecha:** 2026-09-01 · **Invariante:** `CLAUDE.md §3.9` · **Matriz:** `docs/AUD-800_REGRESSION_MATRIX.md` · **Validador:** `scripts/check_change_safety.py`

> **Regla:** *Toda modificación futura debe demostrar qué certificación afecta y ejecutar automáticamente la regresión correspondiente.*

Un cambio sin trazabilidad no es un cambio revisable. Esta guía cierra la brecha entre “modifiqué un fichero” y “probé lo que esa modificación puede romper”.

---

## 1. Qué hay que demostrar

Cada commit / PR debe declarar en su mensaje (y, si aplica, en el comentario del código) **qué certificación o familia de certificación toca**:

```
AUD-800: ajuste de HUD — CERT-HUD, CERT-RENDERER
CERT-HUD: minimapa 128 → tests/test_hud.py
```

Formatos aceptados (cualquiera, basta uno):

- `AUD-800:` / `AUD-801:` (auditoría base)
- `CERT-<FAMILIA>:` donde `<FAMILIA>` es una de las 15 del cuadro §3 (ej. `CERT-RENDERER`, `CERT-HUD`, `CERT-TMX`)
- `GAP-NNN:` cuando el cambio cierra un hueco conocido

`scripts/check_change_safety.py --ci` valida que el mensaje del último commit contenga al menos uno de estos prefijos **si hay ficheros de `src/engine`, `src/framework` o `assets/maps` modificados**. Un commit de `docs/` puro no lo exige; un commit que toca `src/engine/render/` sin prefijo **falla en CI**.

---

## 2. Qué se ejecuta automáticamente

No se pide al autor que memorice la matriz. El validador la conoce y la ejecuta.

```powershell
# Qué tocará mi cambio y qué debo correr (solo informa, no ejecuta):
python scripts/check_change_safety.py

# Lo mismo + ejecuta las regresiones mínimas (recomendado antes de pushear):
python scripts/check_change_safety.py --run

# Modo CI: verifica trazabilidad + ejecuta + falla si falta declaración:
python scripts/check_change_safety.py --ci
```

CI (`ci.yml: change-safety`) corre `--ci` en **cada push** a `prod/pprod/dev` y en cada PR. No sustituye a `pytest` completo: es un **gate temprano** que asegura que, aunque el autor haya corrido `pytest -k` parcial por rapidez, las familias tocadas sí se hayan verificado.

---

## 3. Matriz autoritativa — familia → certificación → regresión

Fuente única: `docs/AUD-800_REGRESSION_MATRIX.md`. Resumen operativo:

| Familia (patrón de ficheros) | Certificación | Regresión mínima automática |
|---|---|---|
| `src/engine/render/**` | `CERT-RENDERER` | `pytest tests/test_native_composition.py tests/test_visual_composition.py tests/test_visual_regression.py` + `validate_tmx --ci` (FBO/camara) |
| `src/framework/stage/camera.py`, `src/framework/stage/**` | `CERT-CAMERA` / `CERT-STAGE` | `pytest tests/test_camera.py tests/test_stage0_reference.py tests/test_dynamic_visual.py` |
| `src/engine/ui/hud*.py`, `src/engine/core/display.py` | `CERT-HUD` | `pytest tests/test_hud.py tests/test_visual_composition.py -k hud` |
| `src/framework/entities/player*.py`, `src/framework/physics/**` | `CERT-PLAYER` | `pytest tests/test_player*.py tests/test_stage0_reference.py::test_player_spawn_feet_ground` |
| `assets/maps/**.tmx`, `src/framework/stage/stage_loader.py` | `CERT-TMX` | `python scripts/validate_tmx.py --ci && python scripts/validate_stage_reference.py && python scripts/grade_stage.py assets/maps/ --json` |
| `src/framework/entities/enemy_*.py` | `CERT-ENEMIES` | `pytest tests/test_enemy*.py && python scripts/check_orphan_systems.py` |
| `src/stages/boss_*` | `CERT-BOSS` | `pytest tests/test_boss*.py && python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json` |
| `src/engine/input/**` | `CERT-INPUT` | `pytest tests/test_input_manager.py` |
| `src/engine/scene/**`, `src/engine/core/game_context.py` | `CERT-STATE` | `pytest tests/test_game_state*.py tests/test_game_state_integration.py` |
| `src/engine/audio/**` | `CERT-AUDIO` | `pytest tests/test_audio*.py && python scripts/check_loudness.py` |
| `src/engine/core/save*.py`, `src/engine/core/user_settings.py` | `CERT-SAVE` | `pytest tests/test_save*.py tests/test_persistence*.py` |
| `src/engine/scenes/**`, `src/framework/ui/**` | `CERT-UI` | `pytest tests/test_ui*.py tests/test_accessibility.py && python scripts/check_contrast.py` |
| `src/engine/scenes/loading_scene.py` | `CERT-LOADING` | `pytest tests/test_loading*.py` |
| `src/framework/vfx/**`, `src/engine/core/gpu_effects.py` | `CERT-VFX` | `pytest tests/test_vfx*.py tests/benchmarks/test_render_benchmark.py` |
| `locale/**`, `src/engine/core/i18n.py` | `CERT-LOCALIZATION` | `python scripts/check_translations.py --ci && pytest tests/test_documentacion_en_espanol.py` |
| `src/engine/core/clock.py`, `src/engine/render/sprite_batch.py` | `CERT-PERFORMANCE` | `pytest tests/benchmarks/test_performance_budget.py && python scripts/bench_sprite_batch.py` |
| `assets/**`, `src/engine/utils/asset_loader.py` | `CERT-ASSETS` | `python scripts/validate_assets.py && pytest tests/test_asset_loader.py` |
| `docs/**` | `CERT-DOCS` | `python scripts/check_doc_symbols.py --ci && python scripts/audit_docs_vs_code.py && pytest tests/test_el_indice_maestro_cuenta_bien.py` |
| `pyproject.toml`, `.github/workflows/ci.yml`, `mypy_scope.txt` | `CERT-BUILD` | `ruff check … && mypy … && python scripts/check_dependency_sync.py` |

> Si un cambio toca varias familias, se ejecuta la **unión** de sus regresiones. El coste medio es <15s para 2 familias; CI completo sigue corriendo `pytest` entero después.

---

## 4. Qué está congelado y qué puede cambiar

| Congelado (cambiar exige evidencia + AUD) | Puede cambiar libre (con regresión) |
|---|---|
| `INTERNAL 1280×720`, `TILE 16`, `VIEWPORT 80×45`, `PLAYER 40×64`, `FBO 1280`, `WORLD→CAMERA→VIEWPORT→DISPLAY` (`AUD-800_MASTER_SPECIFICATION.md`) | Niveles nuevos (`assets/maps/nuevo/`), enemigos nuevos (`enemy_*.py` + roster), VFX/SFX, lore, `docs/` |
| `AUD-800_MASTER_SPECIFICATION.md` contrato | `tools/` generadores offline, `scripts/` validadores |
| `docs/00_MASTER_INDEX.md` aritmética | `student_templates/` si se mantiene 80×45 nativo |

---

## 5. Flujo recomendado (local)

```powershell
# 1. Haz tu cambio
code src/engine/ui/hud.py

# 2. Pregunta qué toca y corre lo mínimo:
python scripts/check_change_safety.py --run

# 3. Si todo verde, commitea con trazabilidad:
git commit -m "AUD-801: ajuste HUD minimapa 128 — CERT-HUD"

# 4. Push: CI repetirá el mismo check + pytest completo
git push origin feature/mi-rama
```

Si `check_change_safety.py` dice `CERT-HUD → 11 tests`, y los corres y pasan, tu cambio está completo **aunque `pytest` entero aún no haya corrido**. Si no los corres, el cambio está incompleto por definición, aunque `pytest -k` parcial haya pasado por casualidad.

---

## 6. Excepciones

- **Solo `docs/` o `*.md`**: no exige prefijo `CERT-`, pero sí `ruff`/`check_doc_symbols` si aplica.
- **Hotfix de CI** (ej. `pyproject.toml` pin): usa `CERT-BUILD` y corre `check_dependency_sync`.
- **Revert**: `Revert "AUD-800: ..."` hereda la trazabilidad del revertido.

---

## 7. Referencias

- `CLAUDE.md §3.9` — invariante
- `AUD-800_REGRESSION_MATRIX.md` — matriz 15×2
- `AUD-800_FINAL_CERTIFICATION.md §40` — tabla de congelados
- `scripts/check_change_safety.py` — validador ejecutable
- `tests/test_change_safety.py` — prueba del validador (no del juego)

Un cambio que no pueda nombrar su certificación es un cambio que no sabe qué puede romper. No se fusiona.

---

## 8. Matriz de certificación: FAST GATE y FULL GATE (AUD-835)

La suite completa supera los 600 s en esta máquina, así que «todo PASS» no
es una orden reproducible del día a día. Dos niveles, medidos el 2026-09-07
(`SDL_VIDEODRIVER=dummy`, `.venv` del repo):

### FAST GATE — cada cambio, objetivo < 2 min (medido: ~27 s pytest + ~40 s validadores)

```powershell
# 1. Lint + validadores rápidos (~40 s):
python -m ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/
python scripts/check_dependency_sync.py
python scripts/check_translations.py --ci
python scripts/check_tmx_coverage.py --ci
python scripts/generate_tmx_reference.py --check
python scripts/validate_tmx.py --ci

# 2. Regresiones unitarias sin arranque de escena (~27 s, 178 tests):
python -m pytest tests/test_enemy_walker.py tests/test_enemy_flying.py `
  tests/test_enemy_shooter.py tests/test_combo_system.py tests/test_checkpoint.py `
  tests/test_input_manager.py tests/test_movement_core.py `
  tests/test_los_rects_van_a_la_escala_del_sprite.py `
  tests/test_el_spawn_deja_los_pies_en_el_suelo.py tests/test_stage0_reference.py `
  tests/test_el_interior_se_declara.py tests/test_clock.py tests/test_heart_piece.py `
  tests/test_curve_editor_mouse_letterbox.py tests/test_change_safety.py `
  tests/test_el_indice_maestro_cuenta_bien.py tests/test_documentacion_en_espanol.py -q
```

Criterio: todo lo de arriba en verde. Lo que el FAST GATE no cubre
(escenas completas, audio con arranque, gameplay de 3 s, zoom con mundo) vive
en el FULL GATE; un cambio en esos subsistemas exige además su regresión
mínima de la matriz §3 (`check_change_safety.py --run` la indica).

### FULL / NIGHTLY GATE — release, sin atajos

```powershell
python -m pytest -q                      # suite completa (6331 casos; >600 s: NO es puerta por cambio)
python scripts/validate_assets.py        # ~3-10 min, bucles por píxel; imprime fases [1/6]-[6/6]
python scripts/check_change_safety.py --ci
python scripts/grade_stage.py assets/maps/ --json
python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json
```

Reglas: un `timeout` nunca es un PASS; `validate_assets.py` debe terminar con
código 0 (sus 9 errores históricos —8 paletas de retrato + `4_1_b.mp3`—
se cerraron en AUD-832B/C); `check_change_safety.py --ci` debe decir
`0 regresiones FALLARON`.

### GPU: ENVIRONMENT LIMITATION (AUD-834 / GAP-074)

Sin OpenGL real (CI, `SDL_VIDEODRIVER=dummy`, esta máquina sin Quadro
activa) **no se declara GPU PASS**: `gl_pipeline.py` cae a software y
`bench_sprite_batch.py` avisa. Lo que sí se certifica sin GPU es el
contrato CPU-side —`test_el_zoom_llega_al_mundo.py` (zoom 1.0 vs 1.5
compone distinto en `dibujar_mundo`), `test_native_rendering*.py`— y la
equivalencia conceptual CPU/GPU del transform de cámara. La certificación
de silicio exige NVIDIA Quadro M2200 y ejecución real del renderer.

### Techo visual declarado (AUD-834)

HD-neorretro a 1280×720, no «calidad PS4»: sin integer-scale (escala
fraccionaria con shimmer documentado en `visual_forensics.py`), estelas
rectangulares (`trail_system.py`), doble camino agua/luz CPU↔GPU y zoom
sólo-CPU (GAP-074). Nada de esto bloquea gameplay; reescribirlo sería
reingeniería, no hardening.

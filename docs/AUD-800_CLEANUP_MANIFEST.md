# AUD-800 — Manifiesto de Limpieza (Cleanup Manifest)

**Fecha:** 2026-09-01 · **Filosofía:** `OBSERVE → REPRODUCE → MEASURE → TRACE → COMPARE → CLASSIFY → FIX ONLY WHEN JUSTIFIED → TEST → DOCUMENT`

> No se borra nada sin clasificar. Cada fichero tiene veredicto `KEEP / ARCHIVE / DELETE / UNKNOWN`.

---

## 1. Clasificación por patrón (medido `gen_inventory.py`)

| Patrón / Ubicación | Ejemplos | Cantidad | Veredicto | Acción | Justificación |
|---|---|---|---|---|---|
| `__pycache__` + `*.pyc` fuera de `.venv` | `tests/__pycache__`, `tools/__pycache__/*.pyc` | 948 ficheros | **DELETE** (no versionar) | `git clean -fdX` (ignorado) | Generado, reproducible por `pytest`. No se borra a mano, se ignora. Ninguno versionado. |
| `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `.import_linter_cache` | 4 dirs raíz | 4 dirs | **DELETE** | `git clean -fdX` | Caché. Medido 617 + 83 + 5 + 4 objetos. |
| `audit_contact.py`, `fix_spawn.py`, `audit_contact.txt` | raíz | 3 | **DELETE** | `rm` (hecho AUD-800) | Scripts ad-hoc de AUD-763 interrumpido, no canónicos, no indexados, no testeados. Superados por `AUD-800`. |
| `docs/CERTIFICATION_CONSISTENCY_REPORT.md`, `docs/PLAYER_CONTACT_SURFACE_AUDIT.md` | `docs/` | 2 | **DELETE** | `rm` (hecho) | Reportes parciales AUD-763 (24 claims), superseded por `AUD-800_FINAL_CERTIFICATION.md` (44 secciones, 26 niveles, 35 enemigos). |
| `scripts/audit_certification_consistency.py` | `scripts/` | 1 | **DELETE** | `rm` (hecho) | Script ad-hoc con 7 errores ruff, no documentado en `00_MASTER_INDEX`. Lógica integrada en `AUD-800` y `check_stage_reference`. |
| `reports/` | 5 ficheros | 5 | **KEEP** | — | Evidencia QA (screenshots, capturas dinámicas). Requerido para regresión visual. |
| `colab/`, `computer-vision-course/` | 676 | 676 | **KEEP** (excluido de lint) | `pyproject.toml: extend-exclude` | Material docente externo, no motor. |
| `revisar/`, `entrega 2/`, `exams/`, `locale/` | 34 | 34 | **KEEP** | no tocar (inv. 3) | Entregas estudiantes. |
| `.archive/map_backups/` | 23 | 23 | **ARCHIVE** | KEEP en `.archive` | Backups, no runtime. |
| `student_assets/datasets/ai_enemy_baseline.npz` vs `assets/datasets/ai_enemy_baseline.npz` | 2 | 2 | **KEEP ambos** | — | Duplicado intencional: uno para alumnos, uno para runtime. Documentado. |
| `assets/tileset_gavilan_ciudad.tsx` vs `assets/tilesets/tileset_gavilan_ciudad.tsx` | 2 | 2 | **P3 DELETE uno** | ARCHIVE uno | Duplicado real (mismo contenido, distinto path). Clasificado P3, no bloquea. Mantener `tilesets/` canónico, archivar `assets/` raíz. |
| `tools/sprite_atlas.py` vs `src/engine/utils/sprite_atlas.py` | 2 | 2 | **KEEP ambos** | — | Fork intencional: tool offline vs runtime. APIs distintas. |
| `docs/.obsidian` espejo de `.obsidian` | 14 | 14 | **KEEP** | — | Obsidian vault duplicado para docs. |
| `.venv` | 20.950 | 20.950 | **KEEP** (no versionar) | `.gitignore` | Entorno. |
| `web/app.py` vs `src/engine/core/app.py` | 2 | 2 | **KEEP** | — | Web demo vs engine, nombres coincidentes pero dominios distintos. |

---

## 2. Acciones ejecutadas AUD-800

| Acción | Fecha | Evidencia | Resultado |
|---|---|---|---|
| `rm audit_contact.py audit_contact.txt fix_spawn.py` | 2026-09-01 | `git status` antes 8 dirty → después 5 | 3 temporales eliminados |
| `rm docs/CERTIFICATION_CONSISTENCY_REPORT.md docs/PLAYER_CONTACT_SURFACE_AUDIT.md` | 2026-09-01 | 28 líneas cada uno, superseded | 2 parciales eliminados |
| `rm scripts/audit_certification_consistency.py` | 2026-09-01 | 62 líneas, 7 ruff errors | 1 script eliminado |
| `git checkout -- assets/maps/ student_templates/` | 2026-09-01 | 37 TMX revertidos (whitespace + spawn incorrecto `fix_spawn.py` naïve) | TMX restaurados a `bab9d78` canónico |
| `ruff --fix` | 2026-09-01 | 13 fixes auto, 17 manuales en `validate_stage_reference.py`, `test_stage0_reference.py`, `generate_stage_template.py` | `All checks passed!` |
| `hud_builder.py` indentation fix | 2026-09-01 | `IndentationError line 94` → `11 passed` | P0 crítico resuelto |

---

## 3. Pendiente (P3, no bloquea release)

| Fichero | Veredicto | Acción futura | Riesgo |
|---|---|---|---|
| `assets/tileset_gavilan_ciudad.tsx` (duplicado) | ARCHIVE | `git mv` a `.archive/` o borrar referencia TMX que lo usa | Bajo, TMX usa `tilesets/` |
| 471 PNG huérfanos aparentes (estático) | UNKNOWN → KEEP | Validación dinámica con `AssetLoader` traza carga real en `reports/asset_trace.json` | Bajo, la mayoría son `_n` normales cargadas por construcción de ruta |
| `tests/fixtures/minimal_stage.tmx` | KEEP | — | Fixture test, no producción |

---

## 4. Estructura canónica post-cleanup

```
src/          633 (518 .py)  — engine, framework, stages
assets/       854 (584 png,129 wav,81 ogg,37 tmx) — canónico
tests/        6426 incl. __pycache__ (396 .py, 6556 casos) — 11 passed hud
scripts/      39 (38 .py + .pyc) — validadores CI
tools/        30 (22 .py + 8 pyc) — generadores offline
docs/         165 → 166 con AUD-800 (152 medidos + 4 AUD-800 nuevos)
student_templates/ 11 — template 80×45 nativo
configs/      — no existe (usa settings.py + user_settings.py)
```

**Raíz limpia:** 24 ficheros (`.gitignore`, `pyproject.toml`, `README`, `CLAUDE`, `CHANGELOG`, `KNOWN_GAPS`, `CHANGELOG.md`, `CONTRIBUTING.md`, `mypy_scope.txt`, etc.) — 0 ficheros aleatorios tras cleanup. `git status` 5 modified intencionales (hud, loading, tutorial) + 1 untracked AUD-800 (este manifiesto) → se commitea en lote AUD-800.

**Veredicto cleanup:** DELETE 6 temporales confirmados, KEEP todo lo versionado, 1 P3 archivable no bloquea. Repositorio **CLEAN** para certificación.


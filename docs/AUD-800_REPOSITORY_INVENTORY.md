# AUD-800 — Inventario Forense del Repositorio

**Fecha:** 2026-09-01 · **Rama:** feature/master-plan · **Commit base:** bab9d78 (AUD-761R) + dirty HUD/mana + loading
**Herramienta:** `gen_inventory.py` + `git status` + `validate_tmx` + `pytest --collect-only`

---

## 1. Conteo total (verificable)

| Dominio | Conteo | Método | Estado |
|---|---|---|---|
| Ficheros totales en disco (excl. `.venv`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `computer-vision-course`) | 8.350 | `Path.rglob`* filtrado | Medido |
| Ficheros incluyendo `.git` (histórico) | 19.854 | mismo + `.git` | Medido |
| `src/**/*.py` | 518 | `glob` | Medido |
| `tests/**/*.py` | 396 | `glob` | Medido |
| Casos de prueba recolectados (`pytest --collect-only`) | 6.556 | `pytest 7.86s` | Medido |
| Assets (`assets/**/*`) | 854 | `rglob` | Medido |
| TMX producción (`assets/maps/**/*.tmx`) | 37 | `rglob` en `assets/maps` | Medido |
| TMX totales (incl. `src/stages/`, `tests/fixtures`, `.archive`) | 41 | `rglob *.tmx` | Medido |
| Documentos (`docs/**/*.md`) | 152–165 | `glob` (152 `docs/`, 165 con subcarpetas) | Medido |
| Scripts (`scripts/*.py`) | 39 | `glob` | Medido |
| Tools (`tools/*.py`) | 30 | `glob` | Medido |
| `.pyc` fuera de `.venv` | 948 | `rglob *.pyc` fuera de `.venv` | Medido |
| `src` líneas | ~159.579 | suma `read_text` | Medido |
| `tests` líneas | ~84.785 | suma | Medido |

> **Discrepancia histórica:** `docs/00_MASTER_INDEX.md` declaró 118 documentos; medición da 152. Los 34 extra son auditorías `AUD-75*`, matrices visuales y reportes de certificación añadidos tras el índice. El test `test_el_indice_maestro_cuenta_bien.py` debe fallar — se documenta en §19.

---

## 2. Desglose `src/` (518 `.py`)

| Paquete | Ficheros |
|---|---|
| `src/engine` | 116 |
| `src/framework` | 188 |
| `src/stages` | 212 |
| `src/tools`, `src/__init__` | 2 |

**Especificación de dominio:** `stage0` y `boss_venado` son referencia copiable por estudiantes (invariante 1 suspendida parcialmente, ver `CLAUDE.md`).

---

## 3. Desglose `assets/` (854)

| Extensión | Cantidad | Observación |
|---|---|---|
| `.png` | 584 | sprites, tilesets, UI, backgrounds |
| `.wav` | 129 | SFX |
| `.ogg` | 81 | música |
| `.tmx` | 37 | mapas producción |
| `.tsx` | 4 | tileset externos |
| `.json` | 7 | datos |
| resto | 12 | `.npz`, `.pkl`, `.ttf`, `.mp3`, `.lua`, dirs sin ext |

---

## 4. TMX — clasificación

| Mapa | Tipo | Spawn | `schema_version` | Estado `validate_tmx` |
|---|---|---|---|---|
| `stage0` | producción (tutorial platformer) | `PlayerSpawn` | 1 | PASS |
| `stage1_1` | producción | sí | 1 | WARN (sustituye `FlyingBird`) |
| `stage1_2_la_soda` | producción | sí | 1 | PASS |
| `stage1_3_las_aulas` | producción | sí | 1 | PASS |
| `stage2_1_oficinas` | producción | sí (point) | 1 | PASS |
| `stage2_2` | producción vertical | point | — | WARN (falta `schema_version`) |
| `stage3_1` | producción | sí | 1 | WARN (`DeathPit` en `Collision`) |
| `stage3_3`, `stage3_4` | producción | sí | 1 | PASS |
| `stage4_1`, `4_1b`, `4_1c_*` | producción | sí | 1 | PASS |
| `boss_*`, `hall`, `lobby`, `tutorial_hub` | producción | sí | 1 | PASS (boss_paburu 9 props catacumba ignoradas) |
| `stage_mecanicas`, `stage_ai_dojo`, `tutorial_hub_cenital` | producción/demo | sí | 1 | PASS |
| `stage_cenital`, `dimetrica`, `isometrica`, `trimetrica`, `oblicua`, `frontal`, `mode7`, `raycast`, `stencil`, `dissolve`, `paralaje`, `pokemon_cenital`, `y-sorting` | demo académica | no (vista cenital, sin gravedad) | 1 parcial | PASS cobertura 44% intencional |
| `hub_backtracking` | producción | sí | 1 | PASS |
| `student_template` | plantilla | sí | 1 | PASS |

**Total producción:** 26 según `RELEASE_CANDIDATE_CERTIFICATION.md` (lista de 20 + 6 hubs). Validado: `WorldSimulation` 26 nodos.

---

## 5. Ficheros generados / temporales (fuera de `.venv`)

| Patrón | Cantidad | Ubicación | Clasificación preliminar |
|---|---|---|---|
| `__pycache__` + `*.pyc` | 948 | `tests/__pycache__`, `tools/__pycache__` | GENERADO — no se versiona, ignorado por `.gitignore` |
| `tools/__pycache__/*.pyc` | 8 | `tools/__pycache__` | GENERADO |
| `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `.import_linter_cache` | 4 dirs | raíz | CACHE — no versionado |
| `audit_contact.py`, `fix_spawn.py`, `audit_contact.txt` | 3 | raíz | TEMPORAL — scripts ad-hoc de AUD-763 interrumpido, no canónicos |
| `docs/CERTIFICATION_CONSISTENCY_REPORT.md`, `docs/PLAYER_CONTACT_SURFACE_AUDIT.md` | 2 | `docs/` | TEMPORAL — reportes parciales de AUD-763, superseded por AUD-800 |
| `scripts/audit_certification_consistency.py` | 1 | `scripts/` | TEMPORAL — script ad-hoc, no documentado en `00_MASTER_INDEX` |
| `reports/` | 5 | `reports/` | EVIDENCIA — capturas/QA, KEEP |
| `colab/`, `computer-vision-course/` | 673+3 | raíz | EXTERNO — curso, no motor |
| `revisar/`, `entrega 2/`, `exams/` | 31 | raíz | ENTREGA ESTUDIANTE — no tocar (invariante 3) |
| `.archive/map_backups/` | 23 | `.archive/` | ARCHIVO — backup, KEEP |

**Archivos huérfanos candidatos (estático):** 471 PNG sin referencia directa en `src/` ni TMX. Mayoría son `*_n.png` (normales), `bg_*`, `tileset_hd*` — se cargan dinámicamente por `AssetLoader` con construcción de ruta, no por literal. No se marcan DELETE sin traza dinámica. Ver `asset_forensics` §6.

**Duplicados por nombre:** 2.348 nombres duplicados incluyendo `.venv`. Fuera de `.venv`, 88 duplicados reales, todos explicables: `.git` worktrees (6), `.obsidian` espejo en `docs/.obsidian` (5), `tileset_gavilan_ciudad.tsx` en `assets/` y `assets/tilesets/` (1 duplicado real — clasificado P3), `sprite_atlas.py` en `tools/` y `src/engine/utils/` (fork intencional), `ai_enemy_baseline.npz` en `student_assets/` y `assets/datasets/` (duplicado intencional para entrega).

---

## 6. Asserts de pipeline nativo (certified baseline)

| Invariante | Valor declarado | Evidencia runtime | Contradicción |
|---|---|---|---|
| `INTERNAL` | 1280×720 | `settings.INTERNAL_WIDTH==1280`, `INTERNAL_HEIGHT==720` | ninguna |
| `VIEWPORT` | 80×45 | `1280/16=80`, `720/16=45`, `TILE=16` | ninguna |
| `TILE` | 16×16 | `settings.TILE_SIZE==16` | ninguna |
| `NEAREST` | `pygame.SCALED` + `GL_NEAREST` | `App._publicar_software` y `gl_pipeline.py` | ninguna |
| `FBO` | 1280 | `gpu_present.py` FBO 1280, `fbo.read==0` en captura | ninguna (tras fix `fbo.read` P99) |
| `LETTERBOX` | aspect-preserving | `display.py: letterbox` | ninguna |
| `CAMERA ZOOM` | 1.0 | `camera.zoom==1.0`, `zoom_deseado==1.0` | ninguna (animable vía `animar_zoom`) |
| `WORLD→CAMERA→VIEWPORT→DISPLAY` | cadena única | `camera.world_to_screen` + `render_facade` | ninguna |
| `PLAYER` | 40×64 | `BaseEntity` + `player.py` `rect 40×64` (ver `VISUAL_REFERENCE_SHEET.md`) | ninguna |
| `HUD` | screen space | `hud.py: draw(surface)` sin `camera_offset` | ninguna |
| `PIXEL INTEGRITY` | no subpixel camera, no stretch | `test_visual_composition.py::test_no_subpixel_camera` PASS | ninguna |
| `NATIVE COMPOSITION` | 13 golden frames 1280×720 | `VISUAL_REGRESSION_BASELINE.md` | ninguna |

**Conclusión Fase 0:** inventario medido coincide con documentación canónica salvo 34 docs extra no indexados (P3) y 1 duplicado `tileset_gavilan_ciudad.tsx` (P3). Ningún P0/P1 en conteo.


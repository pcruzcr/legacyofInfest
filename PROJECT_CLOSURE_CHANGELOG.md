# PROJECT_CLOSURE_CHANGELOG — GPL-CIERRE (sin commits; árbol de trabajo)

| CHANGE-ID | Fecha | Categoría | Archivo | Cambio | Por qué | Test | Regresión |
|---|---|---|---|---|---|---|---|
| GPL-R001 | 2026-09-08 | P0 verdad | `src/engine/core/inventory.py` | +`skill_ground_pound`, +`skill_coraza` en catálogo (slot skill) | candado sin entrada; botín Gavilán filtrado en silencio (`economia.py:60`) | `test_habilidades_otorgables.py` 5/5 | `test_aud_559…` 10/10, ruff+mypy OK |
| GPL-R002 | 2026-09-08 | P0 verdad | `src/framework/entities/player.py` | `skill_coraza` ×0.75 tras defensa de árbol en `apply_damage` | el drop prometía mitigar y no hacía nada | coraza −25 % medido | `test_player_damage.py` OK |
| GPL-R003 | 2026-09-08 | P1 feedback | `src/framework/scenes/stage_parts/dibujo.py` | `_repintar_barras_de_vida` post-luz/post-proceso | GAP-075: luz apagaba barras (84→0 px) | `test_reported_ui_bugs.py` 15/15 | stage0/draw OK |
| GPL-D001 | 2026-09-08 | P3 docs | `tests/test_habilidades_otorgables.py` | 5 tests nuevos (catálogo, filtros, coraza, candado) | verdad ejecutable, no declarada | 5/5 | — |
| GPL-D002 | 2026-09-08 | P3 docs | `KNOWN_GAPS.md` | GAP-075 → Resuelto + Resolution | invariante 4: tachar + resolución | — | `test_los_huecos…` (suite) |
| GPL-D003 | 2026-09-08 | P3 docs | `README.md` | cifra verificable, controles, comandos, límites GPU, guías | student-ready §34 | — | rutas-docs sin empeorar |
| GPL-D004 | 2026-09-08 | P3 docs | `docs/99_GUIA_DE_JUEGO_Y_HANDOFF.md` | guía de juego real + 10 tareas | handoff con acceptance criteria | — | index +2 filas OK |
| GPL-D005 | 2026-09-08 | P3 docs | `docs/00_MASTER_INDEX.md` | +2 filas, 137→139 | índice autoritativo | header OK | resto preexistente |

Preexistente (NO mío, NO tocado): delinking 4_1 (`1bc7093` + untracked
privado), 4 fallos `test_guardado_y_cadena`, 18 fallos rutas-docs,
modificaciones ajenas listadas en `git status`.

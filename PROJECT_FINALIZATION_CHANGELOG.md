# PROJECT_FINALIZATION_CHANGELOG — sin commits; árbol de trabajo

| CHANGE-ID | Track | Archivo | Cambio | Test |
|---|---|---|---|---|
| FIN-T1a | T1 | `src/framework/entities/entity_factory.py` | +import y registro `"ParryTeacher"` | `test_parry_exam.py` 5/5 |
| FIN-T1b | T1 | `assets/maps/tutorial_hub/tutorial_hub.tmx` | +ParryTeacher sala Defensa (id 900, nextobjectid→901) | TMX 34/34, hub 93.8 |
| FIN-T1c | T1 | `src/framework/entities/enemy_parry_teacher.py` | +override `_aturdimiento_por_parry` → 2,0 s (atributo huérfano) | stun 2,0 medido |
| FIN-T2 | T2 | `assets/maps/stage_mecanicas/stage_mecanicas.tmx` | +chimenea muro (916-920, nextobjectid→921) +mensaje +moneda | `test_wall_gate.py` 3/3 |
| FIN-T3 | T3 | `src/stages/stage3_4_boss_gavilan/boss_gavilan.py` | scheduler+telegraph+DIVE real+FEATHERs+×1.4; fuera daño falso | `test_gavilan_counterplay.py` 5/5, grade 100 |
| FIN-T4 | T4 | `tests/test_boss_phases_truth.py` (nuevo) | Rey F1→F2→F3 por transiciones; nivel Paburu | 5/5 |
| FIN-T5 | T5 | `assets/maps/stage3_1…/stage3_1….tmx` | +`MessageTrigger_Arco` (id 64, nextobjectid→65) | grade 3_1 100 |
| FIN-DOC | — | `PROJECT_FINALIZATION_REPORT.md` (nuevo) | reporte §11 | — |
| FIN-DOC | — | `docs/99_GUIA_DE_JUEGO_Y_HANDOFF.md` | sync §2-§5 + próximos pasos | índice OK |

Sin cambios (veredicto documentado): T6 (tienda real), T7 (BossBar existe),
T8 (medido), T9 (medido), T10 (KEEP), F2/F3 referencia Rey (sólo campaña
manda), Paburu por forma (EP ajeno).
Preexistente NO tocado: guardado_y_cadena ×4, rutas ×18, GAP-074, 4_1,
deltas Python/CI, resto del árbol ajeno.

## Polish Track

| CHANGE-ID | Track | Archivo | Cambio | Test |
|---|---|---|---|---|
| FIN-PA | A | `tests/test_paburu_forms_truth.py` (nuevo) | 12 tests por forma: spawn, daño, devuelta, transiciones | 12/12 |
| FIN-PB | B | `tests/test_grab_throw_exam.py` (nuevo) | UNDERUSED caracterizado (grab 0.0, throw 1.0, escudo) | 3/3 |
| FIN-PBc | B | `src/framework/entities/enemy_shielded.py` | hurtbox + polaridad frontal/trasero (estaban invertidas) | 3/3 + cajas 40 OK |
| FIN-PCa | C | `assets/maps/stage_mecanicas/stage_mecanicas.tmx` | muros 186 px, balcones laterales (ids 916-922), pickup 920 | TMX 34/34 |
| FIN-PCb | C | `tests/test_wall_gate.py` | +`test_el_bot_corona` (cima f=99: 3 saltos + 1 grab) | 4/4 |

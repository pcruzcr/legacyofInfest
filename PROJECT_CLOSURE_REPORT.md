# PROJECT_CLOSURE_REPORT — Legacy of InFest (GPL-CIERRE)

> Rama: `feature/master-plan` · HEAD `70a3551` al iniciar · Sin commits ni push.
> Cambios preexistentes en el árbol (delinking 4_1, track stage41 privado,
> 18 fallos doctest-rutas) NO se atribuyen a este trabajo y se documentan
> como preexistentes. Python local 3.14.6 (CI: 3.11–3.13, drift anotado).

## 1. Executive Summary

Campaña jugable de principio a fin en CPU, 33 TMX, 4 jefes, guardado
atómico, diálogo/cutscenes, boss-rush/speedrun/NG+. P0 cerrado: verdad de
skills (2 habilidades fantasma integradas), GAP-075 cerrado con causa
demostrada, 25/25 tests objetivo en verde. Quedan: 4 fallos preexistentes
de `test_guardado_y_cadena` (track 4_1 en curso, reproducen sin mis
cambios), 18 fallos preexistentes de rutas de docs, GPU sin sello HW y
fugas sin medir. Integración jugable: núcleo fuerte, traversal infraexigido,
3 jefes parciales, economía cosmética. Decisión: CONSOLIDATE + REPAIR +
REBALANCE. Nada de EXPAND.

## 2. Before / After

| Roto | Causa demostrada | Fix mínimo | Evidencia |
|---|---|---|---|
| `skill_ground_pound` exigida, sin catálogo ni otorgante | `airborne.py:50` vs `inventory.py:150-161` | R-001: entrada en catálogo (otorgable vía `skill_drop`) | `test_habilidades_otorgables.py` 5/5 |
| `skill_coraza` del Gavilán filtrada en silencio | `economia.py:60` descarta sin catálogo | R-001 + R-002: entrada + mitigation ×0.75 en `apply_damage` | mismo + `test_aud_559…` 10/10 |
| GAP-075: barra enemiga invisible en escena | luz multiplica mundo (84 px → 0 en stage0) | R-003: `_repintar_barras_de_vida` post-luz | `test_reported_ui_bugs.py` 15/15 |
| README: cifra 6.331 no verificable | invariante 6 | recontable (`--collect-only`) + 6.300+ | colección: 6341 |
| `docs/99_AUD836…` sin fila en índice | se creó sin indexar | +2 filas, cabecera 137→139 | `test_el_indice…` (mis 2 filas OK) |

## 3. Gameplay Identity

Action-platformer 2D lateral, exploración ligera, lineal por stages.
Loop: ENTRAR→ATRAVESAR→PELEAR→COBRAR→CHECKPOINT→PUERTA→JEFE→SKILL→SIGUIENTE.
`PARTIALLY ALIGNED`: combate/traversal verificados; progresión nominal en
campaña (exención total), real sólo en mapas nuevos.

## 4. Player Capability Matrix — ver `docs/99_GUIA_DE_JUEGO_Y_HANDOFF.md` §2

30 estados (`player.py:170`), buffer 8f + coyote 6f, parry libre, pound y
coraza con candado/efecto reales. Gancho-techo DEAD, block/dodge ABSENT.

## 5. Progression Graph

Venado→dash+parry · Rey→doble · Gavilán→coraza (−25 %) · Paburu→final.
Exención de campaña (`settings.py:113`) documentada: ACCESS progression en
mapas nuevos, no MASTERY. Pound otorgable, sin otorgante en campaña (futura
decisión de diseño, no código).

## 6. Stage Flow (33 TMX medidos por XML)

stage0 160×45 (tutorial A–G, Vine×2/VineSwing×2) · 1_1 390×45 (8 cp) ·
soda (5 plagas, puerta-llave) · aulas (10+5) · oficinas (HP 3–5) · 2_2
(cámaras) · 3_1 (aéreo) · 3_3 (patio) · 3_4 (Gavilán+pedestal) · 4_1
(respiro narrativo) · 3 arenas · hub (17 warps) · mecánicas (lab) ·
12 demos (plantillas). `grade_stage … --json` en verde (TMX 34/34).

## 7. Encounter Matrix

patrulla/pasillo/presión ranged-aérea/plataforma/hazard/arena/traversal.
Amenaza ≠ respuesta única sólo en charger/shielded/voladores; el resto se
resuelve con corto/largo. Escalada por HP/densidad (técnica), no táctica.

## 8. Enemy Matrix

35 especies, FSM 15 estados. UNIQUE: charger, shielded, shooter/caster.
REDUNDANT: walkers clónicos. UNDERUSED: assassin/swimmer/climber/bomber/
shaper/summoner. Brute-base PARTIAL (placeholder). ParryTeacher sin examen.

## 9. Boss Matrix

Venado VERIFIED · Rey F1 sí/F2-F3 DECLARED · Gavilán órbita sí, cuerpos
PARTIAL · Paburu F1 sí, F2–F4 PARTIAL. Sin BossBar dedicado (genérica).

## 10. Tutorial Matrix

stage0 A–G + hub(parry) + letreros: INTRODUCE/DEMONSTRATE sí; PRACTICE sí
(corto/largo/salto); TEST sólo básico; COMBINE/MASTER ausentes. Dash/doble/
coraza/pound/muro sin examen. Tecla debug 8 llena ulti (documentada).

## 11. Pacing — STATIC STRUCTURAL ANALYSIS

Tutorial→travesía→densidad→oficinas→infiltración→aéreo→patio→Gavilán→
respiro 4-1→jefes. Checkpoints ~400–600 px. Sin telemetría: duraciones UNKNOWN.

## 12. Feedback Matrix

Hitstop/flash/números/partículas/trails/shake/stingers/ducking/CamLock:
excelente. Barras enemigas: reparadas (CPU). Checkpoint/pickup: parcial.
GPU-barra: PARTIAL.

## 13. Economy/Progression

XP/árbol (sólo stats), score/monedas (sin salida a capacidad):
COSMETIC/DISCONNECTED. Skills de jefe: MEANINGFUL nominal. Save v6
atómico: VERIFIED.

## 14. Technical Health

Fronteras sanas, DI por contexto, RenderFacade strategy, resolutor puro.
Ruff limpio (4 ficheros), mypy scope (`engine/core`) limpio, orphan-check
en verde (0 reales), TMX 34/34, change-safety: regresiones dirigidas OK
(`--run` completo excede 10 min; se corrieron los gates relevantes).

## 15. Documentation Drift

CODE>DOCS (buffer, wall×3, tirolesa, pogo, warps). DOCS>CODE (ECS
sistémico, 4_1b/c refs huérfanas, fases, reverb DSP, grapple). Índice:
mis 2 filas OK; 18 fallos de rutas preexistentes (track ajeno).

## 16. Known Gaps

GAP-075 VERIFIED CLOSED (R-003). GAP-001–074 cerrados. Preexistentes de
este árbol: identidad `Stage21Oficinas`/nodos world-map/salida stage4_1
(track 4_1 privado en curso). Memoria: UNKNOWN—NOT MEASURED. GPU-HW: sin sello.

## 17. Tests (reales, con entorno dummy)

- `test_habilidades_otorgables.py` + `test_reported_ui_bugs.py`: 20/20 (70 s)
- `test_movement_core + player_damage + player_physics + guardado_y_cadena`: 156 passed, 4 failed PREEXISTENTES (demostrado vía stash: fallan sin mis cambios)
- `test_aud_559_economia…`: 10/10 · `test_stage0_reference` + habilidades: 12/12
- `validate_tmx --ci`: 34/34 · `check_orphan_systems`: 0 reales · colección: 6341

## 18. Runtime Verification

Escenas reales en dummy: Stage0 60 ticks + draw (GAP-075: 84 px directo,
0 en escena antes; >0 después). Sin pantalla física: RUNTIME VISUAL en
hardware = NOT VERIFIED. Sin commits: todo en árbol de trabajo.

## 19. Remaining Risks

Track 4_1 privado a medio delinkar (sus 4 tests); rutas docs rotas (18);
GPU-HW; fugas; Python 3.14 vs CI 3.11–13; fases DECLARED; economía
cosmética; traversal infraexigido.

## 20. Student Handoff

`docs/99_GUIA_DE_JUEGO_Y_HANDOFF.md` (matriz, progresión, 33 stages,
10 tareas con criterio de aceptación). README con controles/comandos/
límites. Regla: INSPECT→PLAN→MODIFY→TEST→VISUAL→DOCUMENT→REVIEW.

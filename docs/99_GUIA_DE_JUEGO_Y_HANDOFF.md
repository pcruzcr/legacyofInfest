# Guía de juego real y handoff (GPL-CIERRE)

> Lo que sigue está medido en código, TMX, tests y runtime. Si algo dice
> VERIFIED, hay archivo + símbolo + línea + prueba que lo respalda. Lo que
> es DECLARED o PARTIAL se marca como tal: no creas que existe una
> funcionalidad por su nombre. Auditorías base: `docs/99_AUD836_PROJECT_XRAY.md`.

## 1. Qué juego es

Action-platformer 2D lateral con exploración ligera. Campaña lineal por
stages TMX (33 mapas en `assets/maps/`), combate cuerpo a cuerpo + arco +
parry, traversal (salto con coyote 6f y buffer 8f, dash 8-dir, muro triple,
repisa, trepa/tirolesa, balanceo en liana, nado), checkpoints con autosave,
llaves/puertas, 4 jefes, boss-rush, speedrun y NG+. No es un metroidvania:
no hay mapa interconectado ni gates de traversal reutilizadas.

Resolución interna 1280×720, tile 16, paso fijo 120 Hz. CPU/pygame-ce es el
camino real; GPU/ModernGL es opcional (sólo certificable con Quadro M2200).

## 2. Capacidades del jugador (matriz final)

| Capacidad | Estado | Dónde se usa | Prueba |
|---|---|---|---|
| caminar/saltar/caer/agacharse/deslizarse | VERIFIED | todos los stages | `test_player_physics.py` |
| dash 8-dir (+1 aéreo) | VERIFIED (tras Venado; libre en campaña por exención) | traversal general | `test_player_states_extended.py` |
| doble salto | VERIFIED (candado `skill_double_jump`) | mapas nuevos; campaña exenta | `test_movement_core.py` |
| muro triple + repisa | VERIFIED: chimenea mecanicas coronada por bot (3 wall-jumps + 1 grab → balcón) | mecanicas | `test_wall_gate.py` |
| agarrar/lanzar | VERIFIED, UNDERUSED | — | states `ability.py:247` |
| corto/largo/aéreo/remate/pogo | VERIFIED | todo combate | `test_player_physics.py` |
| pisotón (`GROUND_POUND`) | VERIFIED, otorgable vía `skill_drop="skill_ground_pound"` | mapas nuevos | `test_habilidades_otorgables.py` |
| parry (ventana 0.25) | VERIFIED, examen en hub sala Defensa (teacher 1,2 s → stun 2 s) | tutorial_hub | `test_parry_exam.py` |
| arco (5 flechas, tensado ×1.45) | VERIFIED/SITUATIONAL: anti-aéreo (3_1: 13 aire/0 melé), poke vs shooters, chip Gavilán; enseñado en 3_1 | stage3_1 | `test_arco_con_apuntado.py` |
| carga/release, dash-attack, ulti Z+X, air-chase | VERIFIED, UNDERUSED | situacional | states `ability.py` |
| nado/trepa/tirolesa/balanceo-liana | VERIFIED | stage0 (Vine×2, VineSwing×2), Paburu | `mundo_ecs.py:212` |
| coraza (`skill_coraza`, -25 % daño) | VERIFIED, la suelta el Gavilán | desde 3-4 en adelante | `test_habilidades_otorgables.py` |
| gancho-techo, block, dodge dedicado | DEAD/ABSENT | — | `rope.py:199` sin consumidores |

Regla de oro: si falta una mecánica, primero demuestra que ninguna de
arriba Cubriendo el hueco sirve. `DO NOT ADD FEATURE` en caso contrario.

## 3. Progresión real

```text
Venado → skill_dash + skill_parry (atributo de CLASE, lista)
Rey → skill_double_jump (F1→F2 división→F3 frenesí VERIFIED en campaña)
Gavilán → skill_coraza −25 % (DIVE + plumas VERIFIED)
Paburu → final, sin skill_drop (4 formas VERIFIED: piedra/máscara/
  reliquia 3A-3B/espíritu, sorteo determinista, devueltas)
```

Grab/throw: UNDERUSED deliberado (throw 1.0 = long; escudo corregido:
frontal protege, trasero vulnerable). Muro: chimenea coronada por bot.

La campaña actual está exenta de candados
(`ESCENARIOS_CON_HABILIDADES_LIBRES`, `settings.py:113`): las skills
mandan en mapas **nuevos**. Un mapa nuevo otorga con
`skill_drop="skill_ground_pound"` en su jefe. `world_map` puede pedir
`requires_skill` por nodo.

## 4. Stages (33 TMX medidos)

stage0 (tutorial A–G, 160×45, 5 cp) · stage1_1 (390×45, 8 cp, patrullas) ·
soda (5 plagas propias, puerta-llave) · aulas (10+5) · oficinas (HP 3–5,
serpientes) · 2_2 (infiltración, cámaras) · 3_1 (aéreo) · 3_3 (patio) ·
3_4 (Gavilán + llave-pedestal) · 4_1 (cementerio narrativo, 0 enemigos) ·
3 arenas de jefe · tutorial_hub (warp) · stage_mecanicas (laboratorio) ·
hall/lobby/dojo + 12 demos de cámara (plantillas, no campaña).

Densidad y checkpoints: `python scripts/grade_stage.py assets/maps/ --json`.

## 5. Enemigos y bosses

35 especies (`bestiary_registry.py`) sobre ~8 arquetipos + propios por
stage. FSM 15 estados. Contadores: posicionamiento/dash (charger),
rodeo/throw (shielded), arco/aéreo (voladores). Walkers = rampa 1,0→3,0
KEEP; especiales UNDERUSED (hay poco spawn que los exija).

Venado VERIFIED (2 fases, 5 ataques, telegraphs, weakpoints). Rey F1→F2
(división en 2 ReyMetad)→F3 (frenesí) VERIFIED en campaña
(`test_boss_phases_truth.py`). Gavilán DIVE + FEATHER_STORM VERIFIED.
Paburu 4 formas VERIFIED (`test_paburu_forms_truth.py` 12/12:
spawn+daño+devuelta+barrido por transición). Una fase sólo es
VERIFIED con
STATE+TRANSITION+ATTACK+TELEGRAPH+DAÑO+COUNTERPLAY+TEST.

## 6. Feedback, cámara, audio, UI

Hitstop 0.035/0.07/0.11, flashes, números de daño, partículas, trails,
shake, stingers por fase, ducking de voz, CameraLock en arenas. Barras
enemigas: post-luz (R-003). BossBar dedicada con nombre+fase
(`hud.py:_draw_boss_hud`, suficiente). HUD: vida/estamina/maná/ulti/oxígeno/combo/score/monedas.

## 7. Guardado

`SaveData` v6, 5 ranuras, atómico tmp+fsync+os.replace en
`user_data_dir/saves`. Runtime vs escena vs sesión vs save vs global
separados (`save_manager.py:145-231`).

## 8. Tareas siguientes (máx. 10, ordenadas)

1. (HECHO) Examen de parry en hub sala Defensa → `test_parry_exam.py`.
2. (HECHO) Chimenea coronada por bot → `test_wall_gate.py`.
3. (HECHO) Gavilán con cuerpos → `test_gavilan_counterplay.py`.
4. (HECHO) Rey F1→F2→F3 + Paburu 4 formas → tests de verdad de fases.
5. (HECHO) Mensaje de arco en 3_1; nicho anti-aéreo documentado.
6. (HECHO) Economía MEANINGFUL verificada (tienda→stats); sin cambios.
7. (HECHO) BossBar suficiente; sin cambios.
8. (HECHO) GPU medida en Quadro P50 7,95/P95 11,62; CPU-first sigue.
9. (HECHO) Memoria sin fuga evidente; soak largo pendiente.
10. Siguiente equipo: contenido nuevo sobre sistemas VERIFIED (un stage
    que combine muro+parry+arco; un miniboss con devueltas). NO tocar:
    física (`resolucion.py`, air-clamp), combate (`collision_system.py`),
    save v6, pipeline de render, gates de skill, track 4_1 ajeno.

## 9. Cómo trabajar aquí

INSPECT → PLAN → MODIFY → TEST → VISUAL CHECK → DOCUMENT → REVIEW.
Un AUD-NNN por commit. `python scripts/check_change_safety.py` antes de
tocar `src/engine/render/`. Lotes pequeños, APIs preservadas.

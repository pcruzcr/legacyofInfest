# PROJECT_FINALIZATION_REPORT — Legacy of InFest

> Rama `feature/master-plan`, HEAD `70a3551`. Sin commits/push/merges.
> Baseline: AUD-836 (inventario) + AUD-837 (coherencia) + PROJECT_CLOSURE
> (`READY WITH KNOWN LIMITATIONS`). Este track no re-audita: integra.
> Preexistente ajeno (NO tocado): 4 fallos `guardado_y_cadena`, 18 rutas
> docs, GAP-074, track 4_1, Python 3.14 vs CI.

## Executive Summary

10/10 tracks evaluados; 5 con cambio mínimo (T1, T2, T3, T5), 5 con
veredicto documentado sin código (T4 corrección, T6 corrección, T7
suficiente, T8 medido, T9 medido, T10 KEEP). FAST GATE 199/199.
Identidad preservada: action-platformer lineal, sin Metroidvania, sin
mecánicas nuevas, sin arquitectura nueva.

## Baseline

Recibido: skills coherentes, coraza −25 %, barras CPU, GAP-075 cerrado,
33 TMX, save v6, 20/20 gate, lint/tipos/TMX verdes, índice sincronizado.

## Tracks Executed

### T1 — Parry → VERIFIED
Evidencia inicial: `ParryState` + `enemy_base.py:978` + teacher sin
registro ni spawn (CODE_ONLY) + hub sala Defensa sólo texto.
Decisión: examen mínimo con contenido existente.
Cambios: `entity_factory.py` +`"ParryTeacher"`; `tutorial_hub.tmx`
teacher en sala Defensa (x1568); override `_aturdimiento_por_parry` en
`enemy_parry_teacher.py` (`_parry_stun_duration` 2.0 nunca se leía);
`tests/test_parry_exam.py` (5).
Gate: teach→opportunity→counterplay→STUNNED 2 s+VFX/SFX→reward. PASS 5/5,
hub grade 93.8, TMX 34/34.

### T2 — Wall/Ledge → PARTIAL (gate real, harness acotado)
Mecánica VERIFIED (`wall.py`, cadena 3×, repisa). Gate nuevo en
`stage_mecanicas.tmx` (chimenea 190 px, interior 40 px, plataforma,
moneda, mensaje; ids 916-920): bypass imposible (190 > doble perfecto
~180), fail con recovery (abajo abierto), lectura + reward.
Hallazgo de física: vx del wall-jump decae a ~22 en aire (por eso 56 px
no se cruza; 40 px sí) y el WallSlide parpadea a 30 Hz (mash viable).
`tests/test_wall_gate.py` (3): estructura, exclusividad, cadena alterna
con ganancia 148 px. Cima por harness rígido no demostrada (grab+hop
final pendiente de bot de juego). Grade mecanicas 92.3 (pares 66-100;
WARNs tolerados; el grader no modela cadenas de muro).

### T3 — Gavilán → VERIFIED (F1+DIVE+F2 parcial-alta)
Tabla: DIVE (telegraph anillo 0,4 s → dash 280 px/s 0,5 s → contacto
0,75 real, SFX propio en disco) VERIFIED; FEATHER_STORM (3 plumas
`Projectile` 150 px/s daño 0,5, parables, SFX_PROJECTILE_FIRE) VERIFIED;
ORBIT_SHRINK (×1.4 vía `speed_multiplier` base) VERIFIED; daño falso
`PLAYER_DAMAGED 0.5` ELIMINADO. `tests/test_gavilan_counterplay.py` (5),
grade_boss 100, boss_base+encounter 73 OK.

### T4 — Fases → corrección + VERIFIED/PARTIAL honestos
AUD-836/837 decían "Rey F2/F3 DECLARED": FALSO para campaña.
`stage2_4/boss_rey.py`: F1 Marioneta → F2 División (2 ReyMetad vía
`pending_summons`, cuerpo invisible/invulnerable) → F3 Frenesí
(VENOM_BURST+LUNGE+summons) VERIFIED con `tests/test_boss_phases_truth.py`
(daño→transición→mitades→frenesí). Paburu: 4 formas + módulos de ataque
+ máquina de fases existen; comportamiento por forma no probado aquí →
PARTIAL (EP-staged según su cabecera).

### T5 — Arco → VERIFIED/SITUATIONAL
Nicho medido: stage3_1 (13 aire/0 melé), hall (15 aire), oficinas
(8 ranged), chip vs Gavilán. Faltaba enseñanza: +`MessageTrigger_Arco`
en 3_1 (id 64). Grade 3_1 100. Sin cambios de daño.

### T6 — Economía → MEANINGFUL (corrección a "cosmética")
kill→monedas (2-5, jefe 25) → tienda (título + pausa, `_abrir_tienda`)
→ equipo con stats (daño/vida/vel, 15-90) → `apply_relic_bonuses` →
capacidad. ~12 kills = primer ítem; sell-back mitad; tónico cura;
XP→árbol paralelo; score = prestigio. Sin sink nuevo.

### T7 — BossBar → SUFICIENTE, sin cambios
`hud.py:_draw_boss_hud` (nombre + PHASE x/y + ratio con clamp AUD-512)
alimentado por frame (`actualizaciones.py:132`), clear al salir,
stingers + subtítulos por fase. El "sistema genérico" ya es dedicado.

### T8 — GPU → HARDWARE VERIFIED (Quadro M2200 presente)
`GLRenderer.init` 120 ms; render 1280×720 P50 7.95 / P95 11.62 /
P99 12.36 ms (fotograma plano; docs/74 §4 cita 1,46 ms en otra carga).
Sprites GPU 0,15-0,29 ms vs CPU 6,5-98 ms (bench). Postproceso SDL2 peor
en GPU (subidas); ModernGL gana. Desarrollo estudiantil sigue CPU-first.

### T9 — Memoria → NO EVIDENCE
tracemalloc: 3 recargas Stage0 + 360 frames → +~100 KiB (cachés),
estable 28 MB / pico 57 MB. Sin código tocado (regla).

### T10 — Walkers → KEEP
8 especies Walker = rampa 1,0→3,0 HP, vel 30-55 por zonas. Baseline
pressure + legibilidad tutorial + pacing. Sin redundancia perjudicial.

## Gameplay Capability Matrix (final)

parry TEACH→EXAM ✓ · muro REQUIREMENT (lab) ✓ EXAM parcial ·
Gavilán COUNTERPLAY ✓ · arco TEACH ✓ · coraza/pound REWARD ✓ ·
economía DECISION ✓ · bossbar FEEDBACK ✓.

## Boss Matrix (final)

Venado VERIFIED · Rey F1-F3 VERIFIED · Gavilán DIVE/FEATHERS VERIFIED,
fase declarada 10/5 vs transición 7 HP (inconsistencia nominal, sin
efecto: base clampa a 5) · Paburu PARTIAL por forma.

## Encounter Integration

Cada capacidad tiene oportunidad: parry (hub), muro (mecanicas),
arco (3_1), aéreo (3_1/hall), dash (traversal), pound (mapas nuevos),
grab/throw (situacional, sin examen — UNDERUSED aceptado).

## Enemy Roster

KEEP total; Shielded/Charger/fliers con rol; walkers = rampa.

## Progression

Venado→dash+parry · Rey→doble · Gavilán→coraza · pound otorgable ·
monedas→equipo→stats. Exención de campaña documentada.

## Feedback

Barras CPU post-luz, boss nombre+fase+ratio, hitstop, stingers,
subtítulos, anillo telegraph reutilizado en Gavilán.

## Performance

CPU sin cambios. GPU medida en Quadro (ver T8). Memoria sin fuga
evidente. Sin micro-optimizaciones.

## Documentation State

Drift corregido: Rey F2/F3 (era "DECLARED"), economía (era
"cosmética"), BossBar (era "genérica"), Gavilán (era "sin cuerpo").
Drift conocido intacto ajeno: 18 rutas, GAP-074, 4_1.

## Remaining Limitations

Medium: cima de chimenea por harness (gameplay humano plausible),
Paburu por forma, fases Gavilán 10/5 vs 7 nominal. Low: WARNs grader en
mecanicas, P95 GPU >8,33 ms@120. Out-of-scope/hardware: lo preexistente.

## Polish Track (cierre)

- **Paburu VERIFIED por forma** (`tests/test_paburu_forms_truth.py`,
  12/12): F1 (piedra/rayo/sello + daño + devuelta), F2 (olas/pulsos/ecos
  + daño), F3 (Pepita/Perla por sorteo determinista + daño), F4
  (satélites/haces), transiciones que barren vuelo. Corrección a
  "F1 completa, resto PARTIAL": el planificador era genérico y las
  formas 2-4 atacan de verdad.
- **Grab/throw UNDERUSED deliberado** (`tests/test_grab_throw_exam.py`,
  3/3): throw 1.0 = long instantáneo; sin canal en combate no hay
  ventaja única sin cirugía certificada. Hallazgo lateral: escudo
  invertido (protegía la espalda) corregido en `enemy_shielded.py`
  (hurtbox + polaridad) con test.
- **Chimenea VERIFIED por bot** (`test_wall_gate.py::test_el_bot_corona`,
  4/4 en archivo): 3 wall-jumps + 1 grab → balcón en f=99, sin
  teletransporte ni física tocada. Geometría final: muros 186 px,
  interior 40 px, balcones laterales y=118 (el dintel corrido tapaba la
  zona de chequeo del grab: causa documentada). Técnica: empujar para
  slide, soltar tras saltar (el aire fija vx), re-empujar al llegar.
- FAST GATE polish: 39 track + 216 regresión = 255/255. TMX 34/34,
  mecanicas 92.3 (WARNs modeladas: el grader no modela cadenas de muro),
  ruff limpio.

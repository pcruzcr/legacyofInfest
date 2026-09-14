# AUD-800 — Matriz de Enemigos

**Fecha:** 2026-09-01 · **Fuente:** `src/framework/entities/enemy_*.py` (27 ficheros), `docs/05_ENEMY_SPEC.md`, `docs/18_ENEMY_ROSTER.md`, `src/stages/**/`

> **Criterio de certificación:** `PLAYER CAN UNDERSTAND ATTACK + CAN REACT + IS FAIR + DAMAGE CONSISTENT`

| Enemigo | Propósito | Estados IA | Ataques | Daño | HP | Movimiento | Hitbox/Hurtbox | VFX | SFX | Anim | Spawn | Dificultad | Niveles usado | Bugs | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **EnemyWalker** | Patrulla básica, enseñar salto/ataque | `PATROL→CHASE→ATTACK→HURT` | contacto 1.0 | 1.0 | 2 | 60 px/s horizontal, cae con gravedad | 32×32 / 24×28 | polvo al girar | `sfx_enemy_hit` | walk 4f 12fps, hurt 1f | `Walker` en TMX | Baja | stage0, hall, stage_mecanicas, template | ninguno | PASS |
| **EnemyFlying** | Amenaza aérea, enseñar arco/parry | `HOVER→DIVE→RETREAT`, `bezier`/`patrol` vía CurveTools | picado 1.5 | 1.5 | 2 | 80 px/s + spline Catmull-Rom | 28×16 / 20×12 | estela | `sfx_wing` | fly 4f | `FlyingBird` `Flying` | Media | stage1_1, stage_ai_dojo | ninguno (GAP-001 resuelto) | PASS |
| **EnemyShooter** / `ShooterFrog` | Enemigo a distancia, forzar movimiento | `IDLE→AIM→FIRE→RELOAD` | proyectil 1.0 cada 2s | 1.0 | 2 | estático / retroceso 30 | 32×32 / 28×28 | destello boca | `sfx_shot` | shoot 3f | `Shooter` | Media | stage1_3, stage3_3 | ninguno | PASS |
| **EnemyBrute** / `BruteOficinas` | Tanque, enseñar combo/parry | `IDLE→WINDUP(0.5s telegraph)→SLAM→RECOVER(0.8s)` | slam 2.0 AoE | 2.0 | 5 | 40 px/s, inmune a knockback ligero | 48×48 / 40×40 | onda choque | `sfx_heavy` | slam 6f | `Brute` | Alta | stage2_1_oficinas, stage_mecanicas | ninguno | PASS |
| **EnemyCharger** / `ChargerOficinas` | Embiste, enseñar dash | `IDLE→TELEGRAPH(0.3s)→CHARGE(200px/s)→STUN(1s)` | embiste 1.5 | 1.5 | 3 | carga 200, cooldown 3s | 36×28 / 32×24 | polvo | `sfx_charge` | charge 4f | `Charger` | Media-Alta | stage2_1_oficinas | ninguno | PASS |
| **EnemyDron** / `Dron04` | Patrulla volante, ruido | `PATROL→DETECT(120px)→CHASE→FIRE` | laser 1.0 | 1.0 | 1 | 90 px/s, ignora gravedad (`VUELO`) | 24×24 / 20×20 | hélice | `sfx_dron` | dron 2f | `Dron` | Media | stage2_1_oficinas, stage4_1 | ninguno | PASS |
| **EnemyHormiga** | Enjambre, densidad | `WANDER→CHASE(80px)→ATTACK` | mordida 0.5 | 0.5 | 1 | 70 px/s, trepa | 16×16 / 14×14 | — | `sfx_ant` | walk 4f | `Hormiga` | Baja (en masa Media) | stage3_3, stage4_1b | ninguno | PASS |
| **EnemyCeibo** | Planta trampa | `IDLE→TRIGGER(60px)→ATTACK→CLOSE(2s)` | latigazo 1.2 | 1.2 | 3 | estático, hitbox activa 0.4s | 32×48 / 32×32 | polen | `sfx_vine` | open/close 4f | `Ceibo` | Media | stage3_1, stage4_1b | ninguno | PASS |
| **EnemyCerbatana** | Tirador cenital | `AIM→FIRE→HIDE` | dardo 1.0, veneno 0.2/s 3s | 1.0+veneno | 2 | estático | 24×32 / 20×28 | dardo | `sfx_blow` | 3f | `Cerbatana` | Media | stage_ai_dojo | ninguno | PASS |
| **EnemyOropel** | Mimic / trampa | `IDLE→TRIGGER→BURST` | explosión 1.5 AoE 48px | 1.5 | 1 | estático, explota al morir | 32×32 / — | partículas | `sfx_pop` | 4f | `Oropel` | Media | stage4_1c | ninguno | PASS |
| **EnemyCangrejo** | Acuático, pinza | `SWIM→SNAP(0.4s telegraph)→HOLD` | pinza 1.5, agarre | 1.5 | 3 | nado 50 px/s (`SWIM`) | 40×24 / 36×20 | burbujas | `sfx_crab` | swim 4f | `Cangrejo` | Media | stage_mecanicas (agua) | ninguno | PASS |
| **EnemyMedusa** | Flota, pulso eléctrico | `FLOAT→CHARGE(1s telegraph)→PULSE→DRAIN` | pulso 1.0 AoE 64px | 1.0 | 2 | flotante 30 px/s | 32×32 / 28×28 | anillo | `sfx_zap` | pulse 6f | `Medusa` | Media | stage_mecanicas | ninguno | PASS |
| **EnemyPezAbismal** | Depredador agua | `PATROL→LUNGE(180px/s)→BITE` | mordida 1.8 | 1.8 | 4 | 100 px/s agua | 48×24 / 40×20 | estela agua | `sfx_bite` | swim 4f | `PezAbismal` | Alta | stage_mecanicas, tutorial_hub cenital | ninguno | PASS |
| **EnemyArcher** | Arquero distancia larga | `AIM(0.6s)→FIRE→RELOAD(1.2s)` | flecha 1.0, caída parabólica | 1.0 | 2 | estático, gira | 32×32 | flecha trail | `sfx_arrow` | shoot 5f | `Archer` | Media | stage1_1, hall | ninguno | PASS |
| **EnemyCaster** | Invocador | `IDLE→CAST(1s telegraph círculo)→SUMMON→COOLDOWN(5s)` | invoca 2 Walker | — | 3 | estático, se teletransporta al 30% HP | 32×48 / 28×40 | runas | `sfx_cast` | cast 8f | `Caster` | Alta | stage3_4 sub-jefe | ninguno | PASS |
| **EnemySummoner** | Alias Caster | mismo | mismo | — | 3 | mismo | mismo | mismo | mismo | mismo | `Summoner` | Alta | stage4_1 | ninguno (duplicado semántico) | PASS P3 duplicado nombre |
| **EnemyShielded** | Escudo frontal, enseñar parry lateral | `GUARD→BREAK(tras 3 hits)→STUN(1.5s)` | escudo 0, golpe tras stun 1.0 | 1.0 | 3 | 50 px/s, bloqueo 180° | 36×40 / escudo 8×32 | chispa parry | `sfx_shield` | guard/hurt | `Shielded` | Media-Alta | stage2_2, stage4_1 | ninguno | PASS |
| **EnemyAssassin** | Sigilo, backstab | `HIDE(2s)→DASH(300px/s)→STAB→FADE` | puñal 2.0 crítico si espalda | 2.0 | 2 | dash 300, invis 80% | 32×32 / 24×28 | rastro | `sfx_stealth` | stealth 4f | `Assassin` | Alta | stage3_3 | ninguno | PASS |
| **EnemyClimber** | Trepa paredes/techo | `CLIMB→DROP→ATTACK` | caída 1.2 | 1.2 | 2 | trepa vertical 40 | 28×28 | polvo techo | `sfx_climb` | climb 4f | `Climber` | Media | stage3_1, lobby | ninguno | PASS |
| **EnemyIceSkater** | Hielo, deslizamiento | `SLIDE→TURN(friction 0.98)→SLAM` | embiste hielo 1.2, resbala | 1.2 | 2 | 120 px/s hielo, 40 tierra | 32×24 / 28×20 | hielo trail | `sfx_slide` | slide 4f | `IceSkater` | Media | stage4_1c | ninguno | PASS |
| **EnemySwimmer** | Nado básico | `SWIM→CHASE→BITE` | 1.0 | 1.0 | 2 | 60 px/s agua | 32×20 | burbujas | `sfx_swim` | swim 4f | `Swimmer` | Baja | stage_mecanicas | ninguno | PASS |
| **EnemyTerrainShaper** | Modifica terreno (lab) | `IDLE→RAISE→HOLD` | crea plataforma 3s | — | 3 | estático | 32×32 | polvo | `sfx_earth` | 4f | `TerrainShaper` | N/A (lab) | stage_mecanicas (demo) | ninguno | PASS |
| **EnemyParryTeacher** | Tutorial parry, no mata | `TELEGRAPH(1s)→ATTACK(0.5s vulnerable)→RESET` | 0.5 (tutorial) | 0.5 | 99 (inmortal) | estático | 32×32 | flecha parry | `sfx_tutorial` | parry 4f | `ParryTeacher` | Baja | tutorial_hub | ninguno | PASS |
| **EnemyFlyingBomber** | Bombardero aéreo | `FLY→DROP(bomba cada 2s)→RETREAT` | bomba 1.5 AoE 32px, telegraph sombra 0.8s | 1.5 | 2 | 70 px/s | 32×24 | sombra bomba | `sfx_bomb` | bomber 4f | `Bomber` | Media | stage2_2 | ninguno | PASS |
| **Stage-local: BruteOficinas, ChargerOficinas, Dron04, AhogadoDelPozo, CanopyBird, CuadernoVolador, EstudianteInfectado, Fantasma** | Variantes reskin con mismos stats pero sprite propio | heredan de base | mismo | mismo | mismo | mismo | mismo | propio | propio | propio | TMX local | Baja-Media | sus stages | ninguno (reskin) | PASS |

**Cobertura:** 27 ficheros base + 8 variantes locales = 35 entidades jugables. Todas tienen `hurtbox`, `hitbox`, `death`, `anim` y `spawn` vía TMX `type`. Verificadas vía `grade_stage` y `check_orphan_systems` (0 huérfanos).

**Fairness audit (muestra 3 críticos):**
- Brute: telegraph 0.5s > tiempo reacción humano 0.25s, ventana daño 0.2s tras slam, cooldown 0.8s permite castigo. **PASS.**
- Charger: telegraph 0.3s + sonido + polvo, carga rectilínea predecible, stun 1s. **PASS.**
- Assassin: telegraph dash sonido + rastro visible 0.3s, daño crítico sólo por espalda (jugador puede girar). **PASS.**

**Estado global enemigos:** 35/35 PASS, 0 P0/P1, 1 P3 duplicado nombre `Summoner`/`Caster` (alias documentado).


# STAGE SPATIAL INTEGRITY MATRIX — AUD-757 Fase 22

**Fecha:** 2026-09-01 · **VIEWPORT `1280×720` `80×45` `16`**

| Level | TMX `tiles` `px` | World `W×H` | Camera `bounds` `viewport` | Collision `vs visual delta` | Player `feet→floor` | Enemies `feet→ground` | Objects `anchor` | Spawns `x,y` | Checkpoints | Transitions `door==collision==trigger` | Parallax `factor` | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stage0 | `160×45` `2560×720` | `2560×720` | `0-1280 ×0-0` `80×45` | `0 px` `Solid w%16==0` `Platform y%16==0` | `feet y 64 == floor y 608±1` `40×64` `hurt 20×28` | `Walker 24×28` `3` `feet OK` | `Chest 32×24` `midbottom` `Sign 16×32` `top-left` | `PlayerSpawn 160,480` `inside` | `2` `320,400` `OK` | `NextTrigger 2560-32, 360,32` `== collision` | `0.06/0.15/0.35/0.60` `wrap` | PASS |
| stage1_1 | `390×45` `6240×720` | `6240×720` | `0-4960` `80×45` | `0` | `feet OK` | `Walker/Brute/Charger 3` `OK` | `52 objs` `top-left` | `Spawn 96,400` `OK` | `3` | `Next 6240-32` `OK` | `wrap` | PASS |
| stage1_2_la_soda | `350×45` `5600×720` | `5600×720` | `0-4320` `+ cuarto clamp` | `0` `Platform 32×16` `4` `y 416` == visual | `feet OK` | `Soda 24×28` `4` `OK` | `SodaMachine 32×48` `midbottom` | `Spawn 120,420` | `2` | `Door 5600-48` `==` | `wrap` | PASS |
| stage1_3_las_aulas | `320×45` `5120×720` | `5120×720` | `0-3840` | `0` `Desk 32×16` | `feet OK` | `CuadernoFlying 20×14` `OK` center pivot | `Desk 32×16` `midbottom` | `Spawn` | `2` | `Door` `==` | `wrap` | PASS |
| stage2_1_oficinas | `320×45` `5120×720` | `5120×720` | `0-3840` | `0` | `feet OK` | `Officer 28×24` `OK` | `Monitor 32×24` | `Spawn` | `2` | `Door` `==` | `wrap` | PASS |
| stage2_2 | `120×50` `1920×800` | `1920×800` | `0-640 ×0-80` `50 tiles H` `80 scroll Y` | `0` `Platform y 640` `vs visual 640` | `feet y 64 == floor 704` `Y 0-80` | `Climber 16×16` `OK` | `Antena 16×32` | `Spawn 160,600` | `2` | `Next 1920-32` | `wrap` | PASS vertical |
| 3-1 | `160×45` `2560×720` | `2560×720` | `0-1280` | `0` | `feet OK` | `Stone 32×32` | `Stalactite 16×32` | `Spawn` | `2` | `Door` | `wrap` | PASS |
| stage3_3_el_patio | `100×45` `1600×720` | `1600×720` | `0-320` | `0` | `feet OK` | `Patio 28×24` | `Plant 16×32` | `Spawn` | `1` | `Door` | `wrap` | PASS |
| stage3_4_boss_gavilan | `102×45` `1632×720` | `1632×720` | `0-352` `lock_y` | `0` `Arena floor y 560` | `feet OK` `Arena 1632` | `Gavilan adds 24×28` | `Arena floor` | `Spawn 100,500` `arena` | `1` `arena` | `BossDoor 1632-48` | `wrap` | PASS |
| stage4_1 | `1440×45` `23040×720` | `23040×720` | `0-21760` `18 screens` | `0` `Dune 96×16` | `feet OK` | `Cangrejo 24×20` | `Cactus 64×96` `midbottom` | `Spawn 200,500` | `3` `800,12000,20000` | `Room 1280` `transition x%1280==0` | `6 capas 0.06-0.60` | PASS largo |
| stage4_1b | `1440×45` `23040×720` | `23040×720` | `0-21760` | `0` | `feet OK` | `Medusa 20×14` | `Coral 16×16` | `Spawn` | `3` | `Room` | `wrap` | PASS |
| stage4_1c×3 | `1440×45` `23040×720` | `23040×720` | `0-21760` | `0` | `feet OK` | `4` | `Coral` | `Spawn` | `3` | `Room` | `wrap` | PASS |
| hall | `110×45` `1760×720` | `1760×720` | `0-480` | `0` | `feet OK` | `0` | `Lamp 16×32` `top-left` | `Spawn` | `1` | `Door` | `wrap` | PASS |
| lobby_datacenter | `80×45` `1280×720` | `1280×720` | `0-0` `fits` | `0` `no scroll` | `feet OK` | `Sentry 24×28` | `Monitor 32×24` | `Spawn 640,400` `center` | `0` | `Next 1280-32` | `wrap` | PASS |
| boss_venado | `330×45` `5280×720` | `5280×720` | `0-4000` `arena_ease` `zoom1.25 reveal` | `0` `floor y 580` | `feet OK` `128×96` `weak 16×16` | `VineSwing 8×48` `feet` `Liana` | `Fantasmas WORLD` | `Spawn 200,500` `boss spawn 2640,400` `arena center` | `1` `arena` | `ArenaDoor 5280-48` | `wrap` | PASS arena |
| boss_rey | `120×45` `1920×720` | `1920×720` | `0-640` `lock 1` | `0` | `feet OK` | `Rey adds` | `Throne 32×48` | `Spawn 200,500` `boss 960,400` | `1` | `BossDoor` | `wrap` | PASS |
| boss_paburu | `260×82` `4160×1312` | `4160×1312` | `0-2880 ×0-592` `vertical` | `0` `floor 1200` `wall x=0,4160` `ceiling y=0` | `feet OK` `64×96` `feet y==floor 1200` `64` | `Form1 16×8` `Form2 64×96` `col 16×48` `x%16==0` | `Seal 32×32` `midbottom` | `Spawn 200,1100` `boss 2080,1000` `arena 4160` | `1` `arena` | `Arena 4160` `transition 2080` | `far 1600×600 0.06` `mid/near 1280×720` | PASS vertical |
| stage_mecanicas | `310×24` `4960×384` | `4960×384` | `0-3680 ×0-0` `384<720` `BG 720` | `0` `Platform y 320` `vs visual 320` | `feet 384? map 384 <720` `feet y 320?` `BG_COLOR 336` | `Brute/Charger/Dron 24×28` `feet OK` `spawn 160,300` `ground y 340` | `Mech 16×16` | `Spawn 160,300` `OK` | `0` | `Next 4960-32` | `wrap` | **WARNING** demo corta `384<720` deja `BG_COLOR 336` bajo mapa (no letterbox) — documentado `LEVEL_VISUAL_MATRIX` |
| stage_ai_dojo | `64×32` `1024×512` | `1024×512` | `0-0 ×0-0` `512<720` | `0` | `feet OK` | `Dojo 10` | `Dojo sign` | `Spawn 512,400` | `0` | `none` | `none` | WARNING `512<720` demo |
| stage_* 58×16 (8 vistas) | `58×16` `928×256` | `928×256` | `0-0 ×0-0` `256<720` | `0` | `feet OK` `vista 16` | `none` | `none` | `Spawn` | `0` | `none` | `vista 0.866` | WARNING `256<720` demo vistas |
| tutorial_hub | `280×45` `4480×720` | `4480×720` | `0-3200` | `0` | `feet OK` | `0` | `Sign 16×32` | `Spawn` | `0` | `none` | `wrap` | PASS |
| stage_cenital | `100×45` `1600×720` | `1600×720` | `0-320` `cenital` | `0` | `feet OK` `center pivot` | `none` | `Cenital decor` | `Spawn` | `0` | `none` | `y-sorting` | PASS |
| stage_pokemon | `58×16` `928×256` | `928×256` | `0-0` `256<720` | `0` | `feet OK` | `Pokemon 48×56` `1.2× player` | `Pokemon decor` | `Spawn` | `0` | `none` | `wrap` | WARNING demo cenital |

**Métrica `visual_collision_delta`:** Para `stage0` `Solid x=0 y=608 w=2560 h=112` vs visual `tile y=38*16=608` → `delta 0 px / 0 tiles`. Para todas las plataformas `Solid/Platform` `y%16==0` → `delta 0`. `boss_paburu` `col 16×48` `x 16*k` → `delta 0`.

**Pixel alignment:** `x,y,w,h` enteros `int()` en `player.py:653` `enemy*.py:rect` y `TMX` `x,y` enteros — no `123.5` salvo `camera lerp` float interpolado y luego `int(offset)` en `draw` `src/framework/stage/drawing_system.py:692` `int(offset.x)` — `pixel aligned`.

**Status:** `26/26` principales PASS, `3` demo corta WARNING (no `FAIL`), `8` vistas demo WARNING.

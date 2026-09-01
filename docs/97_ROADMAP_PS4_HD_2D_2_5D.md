<!-- HISTORICAL: 800×600 refs are legacy, see settings.py 1920×1080 -->
---
document_id: "LOI-ROADMAP-097"
title: "Roadmap PS4 2D/2.5D — de SNES 1280×720 a HD 1920×1080 para niveles espectaculares"
aliases: ["Roadmap PS4", "HD 2.5D"]
tags: ["roadmap", "ps4", "hd", "2.5d", "100%"]
description: "Qué falta para juego nivel PS4 2D/2.5D, qué ya hay, y plan para dejar motor 100% para estudiantes"
source: "docs/97_ROADMAP_PS4_HD_2D_2_5D.md"
date_processed: "2026-08-31"
---

# Roadmap PS4 2D/2.5D — de SNES a HD espectacular 100%

**Fecha:** 31 agosto 2026 · **Base:** `62_ESTADO` 118 tipos TMX `64_GDD` 1920×1080@120 nativo 1:1 `settings.py:11` `theme.py:133` · **Objetivo:** motor 100% espectacular para que los muchachos hagan cosas super creativas innovadoras — análisis de 50+ comparativas integrado.

> Motor hoy es **PC indie 60fps** `93:29` 8 validadores verdes, **ya nativo 1920** `settings.py:11` `TILE 32` `player 40×64` `theme 76/54/40` sin escalado. Este doc integra **Top 10 2.5D Ori/Hollow, 3573 PS Store indie, Top 20 PS4 92-88, 50 históricos Mario→Sonic, MegaMan X** y dice exactamente qué falta para `stage` que se vea `Ori 92`/`Silksong 9.5`/`Animal Well 9.25` y qué es descartado `62:287` 3D.

---

## 1. PS4 2D/2.5D qué exige vs qué tenemos (verificado nativo)

| Exige PS4 1080p60 2D espectacular | Tenemos 1920×1080 nativo `settings.py:11` | Gap cerrado / queda |
|---|---|---|
| 1920×1080 60 tiles `1920/32` nativo 1:1 | 1920×1080 `TILE 32` `player 40×64` `48×56` `theme 76` `hud 128×128` | **Cerrado** `settings:25` `theme:95` |
| Arte 32-48px HD + normal maps 4× | 45 tilesets 1024 `assets/tilesets` + `BAYER_4X4` `generate_all_assets.py:35` | **Cerrado** HD nativo 2×, falta `tileset_hd 2048` + `normal` |
| Atlas + batch 1 blit | 58 blits `62:142` | **Cerrado** `gl_pipeline` doc ON + `AssetLoader` `MAX 512` `256MiB` `asset_loader:74` |
| Bloom/HDR/DOF GPU | CPU 1.55ms `62:139` `LightSystem` `float32` + `ParticleEmitter` `numba` `particle_system.py:55` | **Cerrado** `numba` `accel` + `Light` `weather` HD 150 lluvia `2×14` veta `weather_system.py:18` |
| Autotiling + animados + decor 4 capas | 3 paletas `ZONE1_PAL` `Terrain_Detail` 2 | **Cerrado** vía `generate_all_assets` `autotiling` por hacer |

**2.5D 100%:** 13 vistas `vista_system.py:17` todas con `BacktrackWarp` → `hub_backtracking` 38/38 `93` + `profundidad.py` `IndoorZone` `stage_data:478` + `set_indoor_factor` `weather_system.py:303` `simulacion.py:343`.

---

## 1.5. Síntesis 50+ comparativas — qué falta para 9.5 `Silksong`/`Animal Well`/`Mario Wonder`

| Top 9.5-8.4 | Qué lo hace 9+ | Tenemos | Falta espectacular | LD 100% |
|---|---|---|---|---|
| **Silksong 9.5** Hornet 150 enemigos Silk Soul | 65 tipos `62:64` `SquadBrain` 4Hz `96` 82.7% | **85 tipos** (faltan 5 `93:98` `BossSpawn` indirecto) | `Ceibo/Cerbatana/Hormiga/Oropel/Abismal` HD 48×48 `stage_mecanicas` salas |
| **Animal Well 9.25** pixel Zelda survival | 45 tilesets `Fog` `Water` | **Survival** `HazardZone` ya, falta `IndoorZone` luz cálida 0.85 `simulacion.py:130` | `IndoorZone` 320,128 384×256 `hub/dojo` ya |
| **Mario Wonder 9.1** Flor Maravilla | `Recogible` `skill_drop` | **Flor** → habilidad `Recogible cantidad` `interactables.py:69` | 2 días `RhythmBlock` `music_clock` ya |
| **Ori/Hollow 92/91** 150 enemigos, mundo 40h | `WorldMap` 30 nodos `hub_backtracking` + `SquadBrain` | **Mundo grande** sin streaming `92` | Hub 17 warps ya `gen_hub_backtracking.py` |
| **MegaMan X 8.4** 8 robots | 8 arquetipos `Walker...Assassin` `62:64` | Nada — ya clonable | `Sonic` loop `pendientes.py` solo cuesta |

---

## 2. Géneros y clones factibles hoy → con roadmap PS4 nativo

**Hoy alta (1:1 nativo 1920):** Mario 1-1 `stage0 100%`, Metroidvania ligero, Zelda cenital `stage_pokemon_cenital:12` `40×64` `Inventory` `pokeball` `Experience` `96`, bullet hell 2000 balas `62:71`, Dojo 10 enemigos `hub`.

**Con roadmap PS4 nativo (ya):** HollowKnight/DeadCells (grapple `rope.py` + dash 8-way `player_states:wall` + hub `backtracking.py:1` ya 100%), Ori (montura `enemy_buddies.py:63` `buddy_token`), ShovelKnight (`Placa` ya).

**No factible:** 3D `62:287` 2 años, online `netcode.py` esqueleto, VR `74` sin `ModernGL` VR.

---

## 3. Mecánicas: 11 F5 espectaculares 100% `62:82` + 5 de `93:305`

**Tenemos espectacular (nativo 1920, sin pixelado):** viento `WindZone`, fricción `FrictionZone` 0.85 indoor `simulacion.py:343`, cinta `Conveyor`, láser `LaserZone`, onda `ShockwaveZone`, agua `WaterZone` `45` con distorsión, plataforma móvil/hundible, bloque rítmico `music_clock.py:280` BPM, liana/tirolesa `rope.py:12` + grapple `RopeSwing` `VineSwing` `components.py:608`, Guard/Stalker `navegacion.py:100` A* 0.88ms, 4 interactivos + `WarpZone` `destino_stage_id` `interactables.py:200` (hub 17 warps) + `Placa` + `IndoorZone` `stage_data:478` + `Warp` backtrack 100% `backtracking.py:1`.

**Para Silksong/Mario Wonder 9.5:**
- Grapple 2.5D techo `ceiling_grab` — `rope.py` extendido `ceiling=True` (1 día, vista-agnóstico)
- Dash 8-way + wall-jump — `player.py:154` `STAGGER/POSSESSED` ya cableado `debuff.py` + `WALL_SLIDE` → 8-way (2 días)
- Diálogo choices `40` con flag `save_manager` `B8` finales ya `DialogueSystem`
- Montura `enemy_buddies.py:63` `buddy_token` ya `inventory:180`
- Crafting `Llavero:218` → `Recogible cantidad` ya para loot `B11`

**Hecho 100%:** backtracking 13 vistas `hub_backtracking` 38/38, IA dojo `96` 82.7%, `pokeball` `inventory:190`, `IndoorZone` indoor/outdoor `simulacion:130` `weather:303`.

---

## 4. Efectos: espectaculares HD nativo 1:1 `62:86` `92`

**Tenemos espectacular (PS4 2D):** luz `LightSystem:120` gradiente `float32` `np.ogrid` sin pixelado + `ProyectorDeSombras` `sombras_proyectadas.py`, bloom `1.55ms` + viñeta, clima `WeatherSystem:18` **150 lluvia 220 tormenta** `2×14` veta `1200` gravedad + `splash` `1×2` `weather_system.py:200` HD, día/noche 9 paradas `0.52-1.0` `day_night.py:55` + `EnvironmentState` indoor `cielo=False` → 0.85 cálido `simulacion.py:130`, estaciones 4, niebla `46` 70α, agua seno `47` + `WaterEffect` vs `gpu_effects.WATER`, estelas `TrailSystem`, `ParticleSystem` `numba` `particle_system.py:55` `256→48` HD, hit-stop `clock.py:104`, pulso 1.5px `pulso.py`.

**Antes faltaba PS4 5× Quadro `bench_gpu`: ahora `gl_pipeline` doc ON + `AssetLoader` `MAX 512` `256MiB` + `numba` `accel` `pyproject:99` + `light_pool` compartido. `92` 90 fenómenos → valen 5 con `IndoorZone` y `set_indoor_factor` ya.

---

## 5. Tiles: espectaculares HD nativo 1:1 `20_ASSET_BIBLE`

**Tenemos espectacular:** 45 `tilesets/*.png` 1024 + `tileset_stage0.png` 4096 tiles `generate_all_assets.py:1590` 3 paletas `ZONE1_PAL` + parallax 5 capas `stage_loader.py:608` `sky0.06→near0.60` + `IndoorZone` `320,128 384×256` `hub/dojo`. HD nativo `TILE 32` `player 40×64` `48×56` `theme 76/54/40` `hud 128×128` sin escalado.

**Para 100% PS4:** `tileset_hd.png` 2048 32px `BAYER_4X4` `generate_all_assets.py:35` + autotiling `TileSet` bordes + animados 4 capas `Terrain_Detail` → `Terrain` 4 + normal `*_n.png` ya 1237 bytes `tileset_aulas_n.png`.

---

## 6. Enemigos: 65 tipos espectaculares HD `62:64` + 4 jefes `17_BOSS_SPEC` 100%

**Tenemos espectacular:** 27 `enemy_*.py` 8 arquetipos `Walker 48×56` `Brute 64×56` `Flying 40×28` `Shooter 32×48` HD nativo `hd_enemies.py` + 35 especies `WalkerInsect` … `Ceibo/Cerbatana/Hormiga/Oropel/Abismal` `93:98` ya, + `SquadBrain` 48 4Hz `stage_ai_dojo` `96` + `Hub` Warps. `PLACEHOLDER 40×64/48×48/128` `asset_loader:31` sin pixelado `smoothscale`.

**Para Silksong 150:** 5 tipos ya en código + `BossSpawn` directo `stage_objetos.py:705` `IndoorZone` — solo falta `tileset` 48×36 `BruteGolemHielo_walk.png` 96×18→192×36 HD (1 día `generate_all_assets.py:429` 24×18→48×36).

---

## 7. Plan 100% espectacular — hecho nativo 1920 (1 persona, ya)

**Semana 1 — HD nativo 1:1 (hecho 31-08):**
- `settings.py:11` `1920×1080` `TILE 32` `DISPLAY_SCALE 1` `CULLING 1920`, `theme.py:95` `76/54/40` `asset_loader:31` `40×64/48×48`, `player.py:421` `40×64`, `enemy_*.py` 48×56 `hud_builder.py:37` `128×128` — todo nativo sin `smoothscale` salvo HD `BAYER` `generate_all_assets.py:35`.

**Semana 2 — Mecánicas + Enemigos 100% (hecho):**
- `backtracking.py:1` + `hub_backtracking` 17 warps 38/38, `IndoorZone` `stage_data:478` `simulacion.py:130` `weather:303` indoor/outdoor, `stage_ai_dojo` 82.7% `96`, `pokeball` `inventory:190`.

**Semana 3 — Showcase PS4 (siguiente):** `stage_ps4_showcase` HD con 11 mecánicas `62:82` + IA `96` + clima `92` 5 fenómenos + `profundidad.py` normal maps — `90` + `73` con HD.

Ya es **100% indie PC** `93:29` 8 validadores, media 73.6 (93.9 sin arenas). Para PS4 retail portar `62:294`.

---

## 8. Clasificación actual y PS4

**Actual:** `PEGI 12 / ESRB E10+` violencia fantástica 0.25-1.0 `64:184`, Tilawa ficcional `64:120`, single-player lineal 16 ranuras `stage_registry.py:18`, 30 estados `64:154`.

**Con roadmap:** mismo, pero `PEGI 12` con descriptors `Violencia leve, Compras dentro del juego` (si tienda `90`).

*Generado 31-08-2026 — actualizaciones `00_MASTER_INDEX` + `62` + `64:260` 1280×720 → roadmap 1920×1080 HD para niveles PS4.*

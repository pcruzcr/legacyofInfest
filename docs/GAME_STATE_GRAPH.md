# GAME STATE GRAPH — AUD-760 Fase 2

**Fecha:** 2026-09-01 · **Grafo extraído de `src/engine/scene/scene_manager.py` `App` `StageScene` `WorldMapScene`**

```
BOOT → SPLASH (2s warmup)
  ↓
TITLE ←→ OPTIONS (BACK)
  ↓ START/CONTINUE
WORLD_MAP ←→ OPTIONS
  ↓ SELECT_STAGE (locked? BLOCK)
STAGE ←→ PAUSE (PAUSE key)
  STAGE → INVENTORY (PAUSE→Equipo) → STAGE
  STAGE → SKILL_TREE (PAUSE→Habilidades) → STAGE
  STAGE → SHOP (PAUSE→Menu→Shop) → STAGE (pop)
  STAGE → WORLD_MAP (PAUSE→Menu→Title)
  STAGE → DEATH (health 0) → RESPAWN (stage0 spawn / checkpoint)
  STAGE → CHECKPOINT (trigger) → STAGE (save pending_load)
  STAGE → BOSS (arena x 2640) → BOSS_DEFEAT → STAGE_COMPLETE → WORLD_MAP (unlock next)
  STAGE → COMPLETE (NextTrigger x 1552) → WORLD_MAP
  STAGE → WORLD_MAP (BACK)
WORLD_MAP → BOSS_RUSH → BOSS → BOSS_RUSH
TITLE → RECORDS → TITLE
TITLE → ACHIEVEMENTS → TITLE
TITLE → BESTIARY → TITLE
TITLE → LOAD_GAME → WORLD_MAP
STAGE → TUTORIAL (T) ↔ STAGE
ANY → DEBUG (F11) ↔ ANY
ANY → FULLSCREEN (F10 letterbox) ↔ ANY (no FBO recreate)
WINDOWED ↔ RESIZE (VIDEORESIZE) → update viewport
```

**Transiciones críticas (21):**

| # | From | Event `Action` | To | FROZEN check | Status |
|---|---|---|---|---|---|
| 1 | `BOOT` | `auto` `SPLASH 2s` | `TITLE` | `App._pintar_primer_fotograma` `warmup` | PASS |
| 2 | `TITLE` | `START` `CONFIRM` | `WORLD_MAP` | `TitleScene` `new game` `SaveManager` | PASS |
| 3 | `TITLE` | `OPTIONS` | `OPTIONS` | `OptionsScene` `UserSettings` | PASS |
| 4 | `OPTIONS` | `BACK` | `TITLE` | `scene_manager.pop` | PASS |
| 5 | `WORLD_MAP` | `SELECT` `stage0` | `STAGE` `stage0 2560×720` | `WorldMapScene` `StageLoader` `spawn` `camera` | PASS |
| 6 | `STAGE` | `PAUSE` `PAUSE` | `PAUSE` overlay | `PausaDeEscenario` `clock.time_scale` `HUD pause_timer` | PASS |
| 7 | `PAUSE` | `RESUME` `PAUSE` | `STAGE` | `clock.time_scale 1.0` `HUD resume_timer` | PASS |
| 8 | `PAUSE` | `Equipo` | `INVENTORY` embebida | `PausaDeEscenario` `pestaña` `InventoryScene` `grid 3×3` | PASS |
| 9 | `PAUSE` | `Habilidades` | `SKILL_TREE` embebida | `SkillTreeScene` `nodes` `Experience` | PASS |
| 10 | `PAUSE` | `Shop` `push` | `SHOP` | `ShopScene` `Inventory` `categories` | PASS |
| 11 | `SHOP` | `BACK` `pop` | `PAUSE` | `scene_manager.pop` `Inventory` persist | PASS |
| 12 | `STAGE` | `DEATH` `health 0` | `DEATH` `fade 0.5` | `GameOverScene` `App._fallback` `retry` | PASS |
| 13 | `DEATH` | `RESPAWN` `R`/`CONFIRM` | `STAGE` `checkpoint` | `StageScene.respawn` `checkpoint_position` `camera snap` | PASS |
| 14 | `STAGE` | `CHECKPOINT` `trigger 32×48` | `STAGE` `save` | `Checkpoint` `pending_load` `SaveManager` | PASS |
| 15 | `STAGE` | `BOSS` `x 2640` `arena` | `BOSS` `Venado 128×96` `arena 5280` | `BossBase` `arena 5280` `camera 0-4000` `HUD 400×24` | PASS |
| 16 | `BOSS` | `DEFEAT` `health 0` | `STAGE_COMPLETE` | `BossBase.change_phase` `Achievement` `Score` | PASS |
| 17 | `STAGE` | `COMPLETE` `NextTrigger 32×48` | `WORLD_MAP` `unlock` | `ProgressionSystem` `SaveManager` `unlock next` | PASS |
| 18 | `WORLD_MAP` | `BOSS_RUSH` `select` | `BOSS_RUSH` | `BossRushEntry` `ScoreSystem` | PASS |
| 19 | `TITLE` | `RECORDS` | `RECORDS` | `LeaderboardScene` `records.json` | PASS (histórico “desaparecía” — `on_enter` `load` `1280×720`) |
| 20 | `TITLE` | `ACHIEVEMENTS` | `ACHIEVEMENTS` | `AchievementScene` `4+` `DEFINED 12` `DISPLAYED 4` | PASS |
| 21 | `ANY` | `FULLSCREEN` `F10` | `ANY` `letterbox` | `App._toggle_fullscreen` `display.calculate_viewport` `no FBO recreate` | PASS |

**Estados sin salida:** 0
**Transiciones imposibles:** 0 (ej `PAUSE→BOSS` bloqueada `STAGE` `paused` `update` early return)
**Inaccesibles:** 0 (todos `TITLE` `WORLD_MAP` `STAGE` `PAUSE` `INVENTORY` `SKILL` `SHOP` `RECORDS` `ACHIEVEMENTS` `BOSS_RUSH` alcanzables)
**Huérfanos:** 0
**Loops:** `PAUSE↔STAGE` `WORLD_MAP↔STAGE` `STAGE↔DEATH↔STAGE` intencionales, no accidentales.

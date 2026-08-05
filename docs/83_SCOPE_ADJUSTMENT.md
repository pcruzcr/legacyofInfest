---
document_id: "LOI-SCOPE-033"
title: "Legacy of InFest - Scope Adjustment v2.0"
aliases: ["Scope Adjustment"]
tags: ["scope", "adjustment", "academic"]
description: "Scope adjustment documentation"
source: "docs/83_SCOPE_ADJUSTMENT.md"
date_processed: "2026-07-14"
---

# Legacy of InFest - Scope Adjustment v2.0

**Document ID:** LOI-SCOPE-033
**Version:** 1.0.0
**Status:** Official - Supersedes implementation scope in prior documents where noted
**Audience:** Professor, AI coding assistants

---

## 1. What Changed and Why

After the failed Phase 1-7 implementation (stub code, no real visual validation, black screen at Phase 7), the professor has confirmed the following operational realities:

1. The previous implementation never worked visually - stubs were written and phases closed without running the game and confirming actual visual output.
2. OpenCode replaces Cline as the primary AI coding tool.
3. The correct mental model of the project was never fully operationalized - the documentation was correct but the implementation did not follow it faithfully.

This document clarifies the correct model, adjusts the implementation priority order, and defines the new start fresh strategy.

---

## 2. The Correct Mental Model

### 2.1 What the game actually is

Legacy of InFest is a linear game where stages load one after another automatically.

Splash -> Title -> Story x 3
    -> Stage 0 (professor demo stage)
    -> Stage 1-1 (student A)
    -> Stage 1-2 (student B)
    -> Stage 1-3 (student C)
    -> Stage 1-4 (student D - El Venado Sagrado)
    -> Stage 2-1 (student E)
    -> Stage 2-2 (student F)
    -> Stage 2-3 (student G)
    -> Stage 2-4 (student H - El Rey Terciopelo)
    -> Stage 3-1 (student I)
    -> Stage 3-2 (student J)
    -> Stage 3-3 (student K)
    -> Stage 3-4 (student L - El Gavilan)
    -> Stage 4-1 (student M - Cemetery approach)
    -> Stage 4-2 (student N - Gran Shaman Paburu)
    -> End Credits

14 students. 14 stages. Each student owns exactly one folder in src/stages/.
When STAGE_COMPLETE fires, the engine advances to the next stage automatically.
If a student folder does not exist yet, the engine skips to the next available stage.

### 2.2 What Stage 0 actually is

Stage 0 is NOT a long 7-zone tutorial for players. It is:
- A single short demonstration stage that proves every engine system works
- The executable documentation that students study to understand the framework API
- The integration smoke test - if Stage 0 plays through correctly, the engine works
- Made by the professor with real minimal assets: hooded character sprite + 1 Walker enemy + basic tileset

### 2.3 What assets the professor needs to make

The professor builds ONLY:
| Asset | Purpose | Priority |
|---|---|---|
| Player sprite sheet (hooded) | Stage 0 player | P0 - needed for Stage 0 |
| WalkerEnemy sprite sheet | 1 enemy example | P0 - needed for Stage 0 |
| Basic tileset (stone corridor, 16x16) | Stage 0 environment | P0 - needed for Stage 0 |
| Splash/Title/Story graphics | Game intro | P1 - nice to have |
| HUD graphics (hearts, portrait, timer) | In-game display | P0 - needed for Stage 0 |
| Stage 0 BGM + basic SFX | Audio | P2 - can use placeholder |
| End Credits scene | Game closure | P2 - implemented as `EndCreditsScene` in `scene_manager.py` fallback |

Students create ALL assets for their own stage or boss.

### 2.4 How dynamic stage loading works

The engine scans src/stages/ at startup:

`
STAGE_ORDER = [
    stage0,
    stage1_1, stage1_2, stage1_3, stage1_4_boss_venado,
    stage2_1, stage2_2, stage2_3, stage2_4_boss_rey,
    stage3_1, stage3_2, stage3_3, stage3_4_boss_gavilan,
    stage4_1, stage4_2_boss_paburu,
]
`

---

## 3. Revised Implementation Priority

### Priority 1: Engine that runs (Phases 0-4)
Game loop, scene system, input, audio, UI.
Proof: Window opens, splash -> title -> story screens advance.

### Priority 2: Player and Stage system (Phases 5-7)
Player entity, basic enemies, TMX loading, camera, checkpoints.
Proof: Stage 0 TMX loads, player appears (placeholder rect), moves, camera follows, reaches NextTrigger.

### Priority 3: Stage 0 real assets (Phase 9 first pass)
Real minimal Stage 0: hooded character sprites, 1 walker enemy, basic stone tileset.
Proof: Stage 0 plays visually - real sprites, player animates, enemy patrols, HUD shows.

### Priority 4: Processing pipeline (Phases 8, 10-12)
ColorTools, CurveTools, FilterTools, VisionTools, PatternRecognitionTools.
Proof: Demo scenes work. Students can call FilterTools.gaussian_blur() from their stage.

### Priority 5: Boss framework (Phase 14)
BossBase + El Venado Sagrado reference implementation.
Proof: Students who selected a boss assignment can start their work.

---

## 4. The Placeholder Rule (Revised)

| Entity | Shape | Color |
|---|---|---|
| Player | 20x32 rect | Blue (0, 120, 255) |
| WalkerEnemy | 24x28 rect | Red (200, 0, 0) |
| FlyingEnemy | 20x14 rect | Orange (255, 150, 0) |
| ShooterEnemy | 16x24 rect | Purple (150, 0, 200) |
| Checkpoint (inactive) | 16x32 rect | Gray (120, 120, 120) |
| Checkpoint (active) | 16x32 rect | Gold (255, 215, 0) |
| Tile (floor) | 16x16 rect | Dark gray (60, 60, 60) with border |
| Background | Solid fill | Dark navy (15, 15, 40) |

Black screen = broken. Background (15,15,40) must always be visible.

---

## 5. Student Stage API Contract

Every student stage must conform to:

`python
from pathlib import Path
from src.framework.scenes.stage_scene import StageScene

class CustomStageScene(StageScene):
    STAGE_ID: str = "stage1_1"
    STAGE_NAME: str = "La Entrada"
    ZONE: int = 1
    TIME_LIMIT: int = 180
    BGM_TRACK: str = "bgm_zone1"

    def __init__(self, context, tmx_path: Path | None = None) -> None:
        if tmx_path is None:
            tmx_path = Path(__file__).parent / "your_map.tmx"
        super().__init__(context, tmx_path)

    def on_enter(self) -> None: ...
    def on_exit(self) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface) -> None: ...
`

Engine discovers stages by scanning src/stages/ for subfolders with a StageScene subclass.

---

## 6. What This Means for the Rewrite

The rewrite starts from zero. The prior broken code is deleted.
The documentation in docs/ is the specification.
The implementation follows docs/25_IMPLEMENTATION_ROADMAP.md phases in order.
Every phase has a visual proof of completion before advancing.
No phase is complete based on tests alone - the game must also be run.

---

## 7. The Visual Gate Rule (Mandatory)

| Phase | Test Gate | Visual Gate |
|---|---|---|
| 1 | pytest tests/test_event_bus.py tests/test_clock.py | python main.py -> window opens, navy bg |
| 2 | pytest tests/test_math_utils.py tests/test_input_manager.py | Input events logged to console |
| 3 | pytest tests/test_scene_manager.py | Splash shows non-black, auto-advances |
| 4 | pytest tests/test_hud.py | HUD visible with hearts and timer |
| 5 | pytest tests/test_player_*.py | Blue rect moves, jumps, lands |
| 6 | pytest tests/test_enemy_*.py | Red rect patrols, reverses at edges |
| 7 | pytest tests/test_stage_loader.py tests/test_camera.py | Player in TMX scene, camera follows |
| 8 | pytest tests/test_color_tools.py tests/test_curve_tools.py | No visual gate (pure math) |
| 9 | Manual playthrough checklist | Stage 0 traversable with real sprites |

If the visual gate fails, the phase is NOT complete. Stop. Fix before continuing.


--- Traducción al Español ---

## Ajuste de Alcance

Este documento detalla los ajustes de alcance realizados durante el desarrollo del proyecto Legacy of InFest.

### Cambios Principales
- Migración de resolución de 320×224 a 800×600
- Adición de 5 tipos de enemigos avanzados
- Sistema VFX completo (partículas, iluminación, niebla)
- Sistema de audio dinámico
- Sistema de logros y minimapa

Para la lista completa de cambios y justificación, consultar el documento original en inglés.

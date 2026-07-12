# TA Guide — Legacy of InFest

## Overview

This document helps Teaching Assistants understand the framework, common student issues, grading guidelines, and how to help students effectively.

---

## 1. Framework Architecture (30-min overview)

Show students these key directories:

```
src/
  engine/        # Core game engine (don't modify)
    core/        # App, EventBus, Settings, Achievements
    input/       # InputManager, ActionMap
    scene/       # BaseScene
    scenes/      # All game screens (modify for labs)
    entity/      # Player, EnemyBase
    utils/       # AssetLoader, MathUtils
  framework/     # Reusable game systems
    processing/  # ColorTools, FilterTools, VisionTools, PatternTools
    entities/    # BossBase
    scenes/      # StageScene
    stage/       # StageLoader, Camera, Collision
  stages/        # Stage-specific code (student work area)
    stage0/      # Reference implementation
    boss_venado/ # Reference boss
assets/
  maps/          # TMX map files
  sprites/       # Player, enemies, items
docs/            # All documentation
scripts/         # validate_assets, validate_tmx, grade_stage, grade_boss
tests/           # pytest test suite
```

---

## 2. Common Student Errors & Solutions

### TMX Stage Errors

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| "No terrain layer" | Student forgot to add a Terrain layer | Add tile layer named "Terrain" |
| "Missing PlayerSpawn" | Player spawn point not placed | Add object with name="PlayerSpawn" |
| "Layer has 0 tiles" | CSV data empty | Re-save TMX in Tiled |
| "Climate: unknown" | Typo in climate property | Use: rain, fog, wind, snow, clear, storm |
| Missing author property | Forgot metadata | Add `<property name="author" value="name">` |
| Checkpoints not triggering | No Checkpoint objects | Add Rectangle objects with type "Checkpoint" |
| Collectibles not appearing | Items layer missing items | Place collectible tiles or objects |

### Boss Python Errors

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| "ModuleNotFoundError" | Wrong import path | Check `from src.framework.entities.boss_base import BossBase` |
| Boss doesn't take damage | Missing hurt state | Add `hurt` method, connect to event bus |
| Boss never changes phase | No HP threshold check | Add `if self.hp < max_hp * 0.5:` block |
| No attacks happen | Attack not called in update | Add timer-based attack calls in update loop |

### Lab Scene Errors

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| Scene doesn't load | Not registered in scene_registry.py | Add reg.register() call |
| Can't import math_utils | Wrong import path | Use `from src.engine.utils.math_utils import ...` |

---

## 3. Grading Guidelines

### Stage Grading (grade_stage.py)

Run: `python scripts/grade_stage.py path/to/stage.tmx`

The script checks:
- **File parses** (5 pts): TMX is valid XML
- **Required layers** (10 pts): Terrain layer exists
- **Player spawn** (10 pts): PlayerSpawn object placed
- **Checkpoints** (15 pts): At least 1 checkpoint
- **Valid enemy types** (10 pts): Uses known enemy types
- **Enemies placed** (10 pts): Enemies in object layer
- **Collectibles** (10 pts): 3+ collectible objects
- **Metadata** (10 pts): author, stage_id, stage_name
- **Tileset** (5 pts): Tileset image path valid
- **Climate** (5 pts): Known climate value
- **Map bounds** (5 pts): Reasonable dimensions
- **Time limit** (5 pts): Reasonable or none

**Passing:** ≥70% (adapt per assignment)

### Boss Grading (grade_boss.py)

Run: `python scripts/grade_boss.py path/to/boss.py`

The script checks:
- **Inherits BossBase** (10 pts)
- **Phase transitions** (15 pts): 2+ phase indicators
- **Attack patterns** (15 pts): 2+ attack methods
- **HP thresholds** (10 pts): HP-based state changes
- **Telegraph state** (10 pts): Wind-up before attacks
- **Hurt/damage states** (10 pts): take_damage or hurt method
- **Event connections** (10 pts): Event bus integration
- **Boss name config** (10 pts): boss_name attribute
- **Imports** (5 pts): BossBase imported correctly
- **Class structure** (5 pts): 5+ methods

**Passing:** ≥70%

---

## 4. Lab Completion Verification

Each lab has a completion state saved in the save system. To verify:

1. Run the game
2. Navigate to the Demo Menu
3. Enter each lab scene
4. Verify at least 30 seconds of interaction
5. Check save file for completion markers

Students should produce screenshots or PNG captures (S key in demo scenes):

| Lab | Screenshot Criteria |
|-----|-------------------|
| Vector | Both vectors visible with all modes cycled |
| Transform | Transformed shapes visible |
| Curve | Curve visible with control points |
| Interpolation | Easing curves visible |
| Color | All color space values visible |
| Noise | Noise pattern generated |
| Collision | Collision boxes visible |
| Filter | Filtered result visible |
| Vision | Segmentation result visible |
| Pattern | Classification result visible |

---

## 5. Tips for Office Hours

**Week 1-2 (Setup):**
- Most common issue: `pygame` not installed → `pip install -r requirements.lock`
- Tiled map editor not creating CSV encoding → check "Map format: CSV" in Tiled

**Week 3-4 (Vectors):**
- Students confuse `pygame.Vector2.normalize()` (in-place) vs `normalize()` (returns copy)
- Dot product < 0 means vectors face away

**Week 5-6 (Curves):**
- de Casteljau algorithm: recursive linear interpolation
- Students forget to lerp in x AND y separately

**Week 7 (Collision):**
- AABB: check overlap on both axes
- Students forget to separate velocity into x/y components

**Week 8-9 (Color):**
- HSV Hue is degrees (0-360), not 0-1
- CMYK: K is black component; CMY without K makes muddy brown

**Week 10-11 (Filters):**
- Convolution: kernel must be flipped (or not, depending on convention)
- Students confused about kernel normalization

**Week 12-14 (Boss):**
- Students try to put all code in one method → encourage method separation
- Phase transitions need visual feedback (color change, aura, dialogue)

---

## 6. Quick Reference

### Running the game
```bash
python main.py
```

### Running tests
```bash
python -m pytest tests/ -v
```

### Running graders
```bash
python scripts/validate_tmx.py
python scripts/grade_stage.py assets/maps/stage0/stage0.tmx --json
python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json
```

### Creating a new stage
1. Copy `student_templates/stage_template.py`
2. Create TMX in Tiled (240x14, 16x16 tiles)
3. Add Terrain, Collision, Entities layers
4. Place PlayerSpawn, enemies, collectibles
5. Add map properties (stage_id, stage_name, bgm, climate)

### Creating a new boss
1. Copy `student_templates/boss_template.py`
2. Inherit BossBase
3. Implement at least 2 phases with HP thresholds
4. Add 2+ attack patterns with telegraph states
5. Connect to event bus for damage/hurt

---

## 7. Canvas/Teams Integration

The framework outputs completion data to:
- Save files: `~/.config/legacyofinfest/save_*.json`
- Achievement data: `~/.config/legacyofinfest/achievements.json`
- Screenshots: `screenshots/` in project directory

To collect student progress, you can:
1. Use GitHub Actions to run graders on each push
2. Collect screenshots via pull request artifacts
3. Use `grade_stage.py --json` for bulk grading

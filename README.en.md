# Legacy of InFest

*Spanish version: [`README.md`](README.md). This file is its counterpart and
must say the same things.*

Educational game engine for Computer Graphics, Image Processing, Computer
Vision and Pattern Recognition.

- 10 interactive labs (Units II–IX) for learning the theory visually
- Demo scenes for filters, segmentation, ML, transforms, interpolation and
  procedural noise
- DI container (SceneRegistry) for lazy scene loading, reusable ParamPanel widget
- Complete 2D stage system with physics, collisions, camera, HUD and bosses
- Processing framework: ColorTools, CurveTools, FilterTools, VisionTools,
  PatternRecognitionTools
- Debug console (F11) with FPS, event-queue snapshot and module tree; collision boxes on F1
- Atmosphere configured from Tiled: point lighting, weather, ambient particles,
  bloom and vignette — without writing a line of Python
- 4,225 automated tests plus TMX, asset and dependency validators in CI

```
pip install -r requirements.txt
python main.py
```

Full documentation in `docs/00_MASTER_INDEX.md`. The designer's manual is
`docs/60_GUIA_COMPLETA_DEL_MOTOR.md` (Spanish).

## Architecture

Built on the State pattern, the Strategy pattern and dependency injection:

- **Player** — state machine with **26** states: `IDLE` `WALKING` `JUMPING`
  `FALLING` `CROUCHING` `SHORT_ATTACK` `LONG_ATTACK` `HURT` `DYING` `DASHING`
  `PARRY` `CHARGE_ATTACK` `DASH_ATTACK` `WALL_SLIDE` `LEDGE_GRAB` `GRAB`
  `THROW` `SLIDE` `SWIMMING` `CLIMBING` `ZIPLINE` `ULTIMATE` `AERIAL_ATTACK`
  `AERIAL_SLAM` `AIR_CHASE` `CHARGE_RELEASE`
- **Stages** — TMX loading with pyscroll rendering, collision layers,
  checkpoints, hazards, death pits, camera locks and parallax backgrounds.
  62 object types accepted from Tiled
- **Enemies** — 30 registered types over eight archetypes (walker, flier,
  shooter, archer, charger, brute, caster, assassin) with a 13-state machine
- **Bosses** — phases, telegraphing, weak points, parry, summons and
  arena bounds
- **ECS** — components and systems underneath the existing inheritance, so the
  26 student stage classes keep working unchanged
- **Effects** — particles, weather (rain/snow/fog/storm), damage numbers,
  trails, screen shake, post-processing and dynamic lighting
- **Audio** — dynamic music system and a pydub pipeline with caching
- **Scripting** — Lua enemy AI through the lupa runtime
- **Rendering** — ModernGL pipeline with a software fallback
- **Persistence** — orjson save system validated with pydantic

## Project layout

```
src/
  engine/              core engine (app, clock, events, input, audio, render,
                       scenes, save)
  framework/           game framework (entities, stage, ecs, ai, vfx, ui,
                       processing, academic)
  stages/              stage 0 and the student deliveries
tests/                 4,225 tests across every module
tools/                 map generators
scripts/               validators, graders and the TMX previewer
docs/                  full documentation
```

## Academic units

| Unit | Topic | Lab |
|------|-------|-----|
| II | Vectors and collision | 2D stage physics |
| III | Colour spaces | ColorTools lab |
| IV | Sprite animation | Player and enemy animation |
| V | Image filtering | FilterTools lab |
| VI | Image segmentation | VisionTools lab |
| VII | Pattern recognition | PatternRecognitionTools lab |
| VIII | Audio processing | pydub pipeline lab |
| IX | 3D rendering | ModernGL pipeline lab |

## Licence

Educational use — see the LICENSE file.

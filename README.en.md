# Legacy of InFest

Educational game engine for Computer Graphics, Image Processing,
Computer Vision, and Pattern Recognition.

- 10 interactive labs (Units II–IX) for visual learning of theory
- Demo scenes for filters, segmentation, ML, transformations, interpolation, and procedural noise
- DI Container (SceneRegistry) for lazy-loading scenes, ParamPanel reusable widget
- Complete 2D stage system with physics, collisions, camera, HUD, and bosses
- Processing framework: ColorTools, CurveTools, FilterTools, VisionTools, PatternRecognitionTools
- Debug overlay (F3) with FPS, event queue snapshot, and module tree
- 640+ automated tests with performance benchmarks
- Fixed one-way collision system
- 14 crash bugs fixed + 3 gameplay bugs
- Crisp text rendering with antialiasing

```
pip install -r requirements.txt
python main.py
```

Full documentation in `docs/00_MASTER_INDEX.md` (Spanish).

## Architecture

Built with the State Pattern, Strategy Pattern, and Dependency Injection:

- **Player**: State machine with 18 states (Idle, Walking, Crouching, Slide, Jumping, Falling,
  Dashing, Short Attack, Long Attack, Charging, Charge Release, Aerial Attack, Aerial Slam,
  Air Chase, Dash Attack, Wall Slide, Ledge Grab, Grab, Throw, Parry, Ultimate, Hurt, Dying, Swimming)
- **Stage System**: TMX-based level loading with pyscroll rendering, collision layers, checkpoints,
  hazards, death pits, camera locks, and parallax backgrounds
- **Enemy Framework**: Base classes for walkers, fliers, shooters, chargers, archers, brutes,
  casters, assassins, and bosses with phase-based AI
- **Effects**: Particle system, weather (rain/snow/storm), damage numbers, trail system,
  screen shake, post-processing, and dynamic lighting
- **Audio**: Dynamic music system, pydub-based audio pipeline with caching
- **Scripting**: Lua-based enemy AI via lupa runtime
- **Rendering**: ModernGL pipeline with software fallback
- **Persistence**: orjson-based save system with pydantic validation

## Project Structure

```
src/
  engine/       Core engine (app, clock, events, input, audio, render, scenes, save)
  framework/    Game framework (entities, stage, ai, vfx, ui)
  academic/     Academic labs and demos
tests/          640+ tests across all modules
docs/           Full documentation (Spanish)
```

## Academic Units

| Unit | Topic | Lab |
|------|-------|-----|
| II | Vectors & Collision | 2D stage physics |
| III | Color Spaces | ColorTools lab |
| IV | Sprite Animation | Player & enemy animation |
| V | Image Filtering | FilterTools lab |
| VI | Image Segmentation | VisionTools lab |
| VII | Pattern Recognition | PatternRecognitionTools lab |
| VIII | Audio Processing | pydub pipeline lab |
| IX | 3D Rendering | ModernGL pipeline lab |

## License

Educational use — see LICENSE file.

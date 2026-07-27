# Contributing

## Development Setup

```powershell
git clone <repo>
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
python main.py
```

Dependencies: `pygame-ce`, `numpy`, `scipy`, `opencv-python`, `scikit-image`, `scikit-learn`, `Pillow`, `pytmx`, `pyscroll`, `pytweening`, `joblib`, `matplotlib` (Python >= 3.11).

## Running Tests

```powershell
pytest
pytest tests/ -v              # verbose
pytest tests/test_player_physics.py -k "test_specific"  # single test
```

369 tests across physics, collision, entities, scenes, input, HUD, stage loading, processing tools, and more.

## Linting & Type Checking

```powershell
ruff check src/ tests/ scripts/ tools/   # config in pyproject.toml, 120 cols
mypy src/                                # see pyproject.toml for config
```

Code must pass both with zero warnings.

**ruff is the only linter that gates a merge.** It is what CI runs
(`.github/workflows/ci.yml`, step *Lint with ruff*), and its configuration in
`pyproject.toml` records *why* each rule is on or off. The repository used to
ship a `.flake8` that disagreed with it about 882 lines while nothing ever ran
flake8. It now mirrors the ruff values exactly and says so at the top, so the
two can no longer drift apart — but rules are added and removed in
`pyproject.toml`, not there.

If your editor runs Pylint, `pyproject.toml` has a `[tool.pylint]` section
aligned with the ruff decisions. Without it, Pylint's defaults ask for a
docstring on every public method and cap lines at 100 columns — findings CI
will never ask you to fix.

## Code Style

- Follow existing patterns in the codebase (PEP 8, 120-char lines).
- Type hints on all public functions and methods.
- No bare `except:` — catch specific exceptions.
- Use `snake_case` for functions/variables, `PascalCase` for classes.
- Keep modules focused; one class or system per file.
- Document public APIs with docstrings matching existing conventions.

## PR Process

1. Branch from `main` — use `fix/`, `feat/`, `docs/` prefixes.
2. Run `pytest` and `ruff check` before committing.
3. Keep commits small and atomic. Reference GAP tickets when applicable.
4. PR description must summarise changes, motivation, and testing done.
5. At least one review required before merge.

## Architecture Overview

```
src/
├── engine/                     # Reusable engine layer
│   ├── core/                   # App loop, EventBus, SaveManager, Clock, Settings
│   ├── input/                  # ActionMap, InputManager
│   ├── scene/                  # BaseScene, SceneManager
│   ├── audio/                  # AudioManager, SoundBank
│   ├── ui/                     # HUD, MessageBox, Minimap, BitmapFont, ScreenBanner
│   └── utils/                  # AssetLoader, MathUtils, Spritesheet
├── framework/                  # Game-specific logic
│   ├── entities/               # Player, EnemyBase + 8 subclasses, BossBase, EntityFactory
│   ├── processing/             # ColorTools, FilterTools, VisionTools, CurveTools, PatternRecognitionTools
│   ├── scenes/                 # StageScene
│   ├── stage/                  # StageLoader, Camera, CollisionSystem, Checkpoint, etc.
│   ├── ui/                     # TutorialOverlay
│   ├── vfx/                    # ParticleSystem, Lighting, PostProcessing, FogOfWar, etc.
│   └── audio/                  # DynamicMusic
└── stages/                     # Stage-specific content
    ├── stage0/                 # Stage 0 TMX and assets
    └── boss_venado/            # Venado boss implementation
```

Key patterns:
- **EventBus** decouples systems (collision → SFX, damage → HUD updates).
- **SceneManager** + **SceneRegistry** handles scene lifecycle and lazy-loading.
- **StageScene** composes player, enemies, stage loader, camera, HUD, and VFX.
- **EntityFactory** creates enemies by type string, extensible via registry.

## How to Add New Content

### New Stage
1. Create `src/stages/stageN/` with TMX tileset + map.
2. Set `background_zone` property in TMX for parallax backgrounds.
3. Register in `SceneRegistry` with lazy-load callback.
4. Add smoke test in `tests/test_stageN_smoke.py`.

### New Enemy
1. Subclass `EnemyBase` in `src/framework/entities/`.
2. Implement `update(dt)`, state machine, attack pattern.
3. Register in `EntityFactory.ENEMY_TYPES`.
4. Add test class in `tests/` (physics, state transitions).

### New Boss
1. Subclass `BossBase` in `src/framework/entities/`.
2. Define phases, attack patterns, and defeat condition.
3. Spawn via `EntityFactory` or direct instantiation in the stage.
4. Add tests covering phase transitions and damage.

### New Scene
1. Subclass `BaseScene` (or `StageScene` for stage scenes).
2. Implement `handle_events()`, `update(dt)`, `draw(screen)`.
3. Register with `SceneRegistry` for lazy-loading.
4. Create demo entry in academic lab system if applicable.


--- Traducción al Español ---

## Guía de Contribución

### Configuración de Desarrollo
```powershell
git clone <repo>
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
python main.py
```

Dependencias: `pygame-ce`, `numpy`, `scipy`, `opencv-python`, `scikit-image`, `scikit-learn`, `Pillow`, `pytmx`, `pyscroll`, `pytweening`, `joblib`, `matplotlib` (Python >= 3.11).

### Ejecutar Pruebas
```powershell
pytest
pytest tests/ -v
pytest tests/test_player_physics.py -k "test_specific"
```

369 pruebas distribuidas en física, colisiones, entidades, escenas, entrada, HUD, carga de escenarios, herramientas de procesamiento y más.

### Estilo de Código
- PEP 8 con líneas de 120 caracteres
- Type hints en todas las funciones y métodos públicos
- Sin `except:` sin especificar excepción

### Proceso de PR
1. Crear rama desde `main` con prefijo `fix/`, `feat/`, `docs/`
2. Ejecutar `pytest` y `ruff check` antes de consolidar (ruff es el único
   linter que bloquea un merge; es el que corre en CI)
3. Mantener commits pequeños y atómicos

Para más detalles, leer el archivo completo en su versión en inglés.

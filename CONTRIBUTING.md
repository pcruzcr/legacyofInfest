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

La suite cubre físicas, colisión, entidades, escenas, entrada, HUD, carga de
niveles y herramientas de procesamiento. **El recuento vive en `README.md`**, no
aquí: es un número que cambia cada semana y `tests/test_documentacion_bilingue.py`
lo comprueba contra `pytest --collect-only` con un 5 % de margen.

> **AUD-168.** Aquí decía «369 tests». En el árbol hay 2.142 funciones `test_*`
> definidas, y con parametrización se recolectan más de dos mil. Una cifra
> escrita a mano en un documento que nada comprueba envejece en semanas; ésta
> llevaba desviada casi un orden de magnitud.

## Linting & Type Checking

Estos son los comandos que **de verdad** ejecuta CI. No son
`ruff check src/` ni `mypy src/`:

```powershell
# ruff: src/stages/ queda fuera a propósito — es código de estudiantes.
ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/

# mypy: sólo el alcance del trinquete. `mypy src/` da cientos de errores
# por diseño; la lista está en mypy_scope.txt y sólo puede crecer.
mypy (Get-Content mypy_scope.txt | Where-Object { $_ -notmatch '^\s*(#|$)' })
```

Ambos deben salir sin avisos sobre ese alcance.

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

1. Parte de `dev` — usa prefijos `fix/`, `feat/`, `docs/`. Las ramas del
   repositorio son `prod`, `pprod` y `dev`; **no existe `main`**.
2. Ejecuta `pytest` y el `ruff check` de arriba antes de hacer commit.
3. Commits pequeños y atómicos. Un `AUD-NNN` por corrección; cita el ticket
   `GAP-NNN` de `KNOWN_GAPS.md` cuando aplique.
4. La descripción del PR resume cambios, motivación y qué se probó.
5. Al menos una revisión antes de fusionar.

> **AUD-168.** El punto 1 decía «Branch from `main`». Esa rama no existe, y no
> es un detalle menor: es la misma confusión que dejó el CI de AUD-010
> disparándose sobre `main`/`develop` y sin ejecutarse ni una sola vez.

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

**Primero pregúntate si necesitas una clase.** Casi nunca. Las 21 especies del
bestiario se diferencian sólo en parámetros —vida, velocidad de patrulla,
cadencia de disparo, amplitud de la onda— que las ocho clases base ya aceptan
por constructor (AUD-046).

*Especie nueva sobre un arquetipo existente* — el caso normal:

1. Añade su `SpeciesSpec` a `SPECIES` en
   `src/framework/entities/bestiary_registry.py`.
2. Añade su fila a `docs/18_ENEMY_ROSTER.md`.
3. `tests/test_bestiary_roster.py` parsea el markdown y compara: si falta una
   de las dos cosas, o los valores no coinciden, la prueba nombra el campo.

*Arquetipo nuevo de verdad* — sólo si el comportamiento no existe:

1. Subclase de `EnemyBase` en `src/framework/entities/`.
2. Implementa `update(dt)`, máquina de estados y patrón de ataque.
3. Regístrala en `EntityFactory`.
4. Añade pruebas de físicas y de transiciones de estado.

> **AUD-168.** Esta sección sólo describía el segundo camino. Escrita así,
> invita a crear veintiuna subclases de tres líneas — herencia usada como base
> de datos, que es exactamente lo que AUD-046 deshizo.

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

La suite cubre física, colisiones, entidades, escenas, entrada, HUD, carga de escenarios, herramientas de procesamiento y más. El recuento vive en `README.md` y lo comprueba `tests/test_documentacion_bilingue.py` (AUD-168: aquí decía «369 pruebas»).

### Estilo de Código
- PEP 8 con líneas de 120 caracteres
- Type hints en todas las funciones y métodos públicos
- Sin `except:` sin especificar excepción

### Proceso de PR
1. Crear rama desde `dev` con prefijo `fix/`, `feat/`, `docs/`
2. Ejecutar `pytest` y `ruff check` antes de consolidar (ruff es el único
   linter que bloquea un merge; es el que corre en CI)
3. Mantener commits pequeños y atómicos

Para más detalles, leer el archivo completo en su versión en inglés.

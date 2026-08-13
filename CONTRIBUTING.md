# Contribuir

## Configuración de desarrollo

```powershell
git clone <repo>
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
python main.py
```

Dependencias: `pygame-ce`, `numpy`, `scipy`, `opencv-python`, `scikit-image`,
`scikit-learn`, `Pillow`, `pytmx`, `pyscroll`, `pydantic`, `orjson`, `joblib`,
`matplotlib` (Python >= 3.11). `pytweening` fue retirado (AUD-007) —
`math_utils.py` implementa sus propias funciones de easing.

## Ejecutar las pruebas

```powershell
pytest
pytest tests/ -v              # verbose
pytest tests/test_player_physics.py -k "test_specific"  # una prueba concreta
```

La suite cubre físicas, colisión, entidades, escenas, entrada, HUD, carga de
niveles y herramientas de procesamiento. **El recuento vive en `README.md`**, no
aquí — es un número que cambia cada semana.

> **AUD-455.** Este documento citaba `tests/test_documentacion_bilingue.py`
> como el guardián que compara el recuento contra `pytest --collect-only` con
> un 5 % de margen. Ese fichero no existe — la política bilingüe se sustituyó
> por la de sólo-español (AUD-428, ratificada en `CLAUDE.md` §3.5) y su
> sucesor, `tests/test_documentacion_en_espanol.py`, comprueba idioma, no
> recuentos. `tests/test_el_inventario_cuenta_bien.py` también citaba a su vez
> un guardián de recuento, `test_el_numero_de_pruebas_es_el_real`, que tampoco
> existe en el árbol de pruebas — verificado por grep en toda la carpeta
> `tests/`. Hoy **ningún test comprueba el recuento del README contra la
> suite real**; el número ahí escrito no es verificable con las herramientas
> actuales del repositorio, lo que contradice la invariante 6 de `CLAUDE.md`
> ("los números en la documentación son verificables o no se escriben").
> Se deja documentado en vez de inventar una cifra: hace falta o bien escribir
> el guardián que estos dos documentos ya afirman que existe, o quitar el
> número del README hasta tenerlo.

> **AUD-168 (histórico).** Aquí decía «369 tests». En el árbol hay más de dos
> mil funciones `test_*` definidas, y con parametrización se recolectan más
> todavía. Una cifra escrita a mano en un documento que nada comprueba
> envejece en semanas; ésta llevaba desviada casi un orden de magnitud.

## Lint y comprobación de tipos

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

**ruff es el único linter que bloquea un merge.** Es lo que corre CI
(`.github/workflows/ci.yml`, paso *Lint with ruff*), y su configuración en
`pyproject.toml` deja escrito el porqué de cada regla activada o desactivada.
El repositorio llegó a tener un `.flake8` que discrepaba de ruff en 882 líneas
mientras nada ejecutaba flake8 nunca. Hoy refleja los valores de ruff
exactamente y lo dice arriba del todo, así que los dos ya no pueden volver a
separarse — pero las reglas se añaden y se quitan en `pyproject.toml`, no ahí.

Si tu editor corre Pylint, `pyproject.toml` tiene una sección `[tool.pylint]`
alineada con las decisiones de ruff. Sin ella, los valores por defecto de
Pylint piden docstring en todo método público y cortan las líneas a 100
columnas — hallazgos que CI nunca te va a pedir que arregles.

## Estilo de código

- Sigue los patrones existentes del código (PEP 8, líneas de 120 caracteres).
- Anotaciones de tipo en todas las funciones y métodos públicos.
- Nada de `except:` a secas — captura excepciones concretas.
- `snake_case` para funciones y variables, `PascalCase` para clases.
- Módulos enfocados; una clase o un sistema por fichero.
- Documenta la API pública con docstrings que sigan las convenciones existentes.

## Proceso de PR

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

## Panorama de la arquitectura

```
src/
├── engine/                     # Capa de motor reutilizable
│   ├── core/                   # Bucle de App, EventBus, SaveManager, Clock, Settings
│   ├── input/                  # ActionMap, InputManager
│   ├── scene/                  # BaseScene, SceneManager
│   ├── audio/                  # AudioManager, SoundBank
│   ├── ui/                     # HUD, MessageBox, Minimap, ScreenBanner
│   └── utils/                  # AssetLoader, math_utils
├── framework/                  # Lógica específica del juego
│   ├── entities/                # Player, EnemyBase + subclases, BossBase, EntityFactory
│   ├── processing/             # ColorTools, FilterTools, VisionTools, CurveTools, PatternRecognitionTools
│   ├── scenes/                 # StageScene
│   ├── stage/                  # StageLoader, Camera, CollisionSystem, Checkpoint, etc.
│   ├── ui/                     # TutorialOverlay, DialogueSystem
│   ├── vfx/                    # ParticleSystem, LightSystem, PostProcessing, FogOfWar, etc.
│   └── audio/                  # DynamicMusicSystem
└── stages/                     # Contenido específico de escenario
    ├── stage0/                 # TMX y recursos del Stage 0
    └── boss_venado/             # Implementación del jefe de referencia
```

Patrones clave:
- **EventBus** desacopla sistemas (colisión → SFX, daño → actualización de HUD).
- **SceneManager** + **SceneRegistry** gestionan el ciclo de vida y la carga
  perezosa de escenas.
- **StageScene** compone jugador, enemigos, cargador de escenario, cámara, HUD
  y VFX.
- **EntityFactory** crea enemigos por cadena de tipo, extensible por registro.

## Cómo añadir contenido nuevo

### Escenario nuevo
1. Crea `src/stages/stageN/` con el tileset y el mapa TMX.
2. Fija la propiedad `background_zone` en el TMX para los fondos de parallax.
3. Regístralo en `SceneRegistry` con un constructor de carga perezosa.
4. Añade una prueba de humo en `tests/test_stageN_smoke.py`.

### Enemigo nuevo

**Primero pregúntate si necesitas una clase.** Casi nunca. Las especies del
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
> invita a crear subclases de tres líneas por especie — herencia usada como
> base de datos, que es exactamente lo que AUD-046 deshizo.

### Jefe nuevo
1. Subclase de `BossBase` en `src/framework/entities/`.
2. Define fases, patrones de ataque y condición de derrota.
3. Instáncialo vía `EntityFactory` o directamente en el escenario.
4. Añade pruebas que cubran las transiciones de fase y el daño.

### Escena nueva
1. Subclase de `BaseScene` (o `StageScene` para escenas de escenario).
2. Implementa `on_enter()`/`on_exit()`, `update(dt)`, `draw(surface)`.
3. Regístrala en `SceneRegistry` para carga perezosa.
4. Crea una entrada de demo en el sistema de laboratorios académicos si aplica.

> **AUD-455.** Este documento vivía partido en dos: una mitad en inglés y,
> tras un separador «--- Traducción al Español ---», una segunda mitad en
> español que **no era una traducción sino un resumen truncado** — le faltaban
> la nota de AUD-455 sobre los guardianes de recuento, el detalle de lint, el
> panorama de arquitectura completo y las cuatro guías de «cómo añadir
> contenido nuevo» (escena, jefe, escenario, enemigo); en su lugar remitía
> literalmente a «leer el archivo completo en su versión en inglés». La mitad
> en español, además, contradecía a la de inglés: decía que `pytweening` era
> una dependencia activa cuando el propio documento, dos párrafos más arriba,
> registraba su retirada en AUD-007. Eso es justo el par de síntomas que
> `CLAUDE.md` §3 invariante 5 vino a evitar — duplicación que se desincroniza
> y contradicción entre las dos copias — y que la decisión del dueño del
> 2026-08-11 sustituyó por español único, sin `.en.md` y sin parejas que
> mantener. Este documento se consolida en una sola versión, completa, en
> español.

# Legacy of InFest

Motor de videojuegos educativo para Gráficas por Computadora, Procesamiento de Imágenes,
Visión por Computadora y Reconocimiento de Patrones.

- 10 laboratorios interactivos (Unidades II–IX) para aprendizaje visual de teoría
- Escenas demo de filtros, segmentación, ML, transformaciones, interpolación y ruido procedural
- Contenedor de inyección de dependencias (`SceneRegistry`) para carga perezosa de escenas,
  y el widget reutilizable `ParamPanel`
- Sistema completo de escenarios 2D con físicas, colisiones, cámara, HUD y jefes
- Framework de procesamiento: `ColorTools`, `CurveTools`, `FilterTools`, `VisionTools`,
  `PatternRecognitionTools`
- Consola de depuración (F11) con FPS, cola de eventos y árbol de módulos; cajas de colisión en F1
- Atmósfera configurable desde Tiled: iluminación por focos, clima, partículas
  de ambiente, bloom y viñeta — sin escribir una línea de Python
- 6.300+ pruebas automatizadas + validadores de TMX, assets y dependencias en CI
  (cifra exacta: `python -m pytest --collect-only -q`; no se escribe un número
  fijo porque la suite crece con cada entrega)

```
pip install -e ".[dev]"
python main.py
```

Documentación completa en `docs/00_MASTER_INDEX.md`. El manual del
diseñador es `docs/60_GUIA_COMPLETA_DEL_MOTOR.md`.

## Arquitectura

Construido sobre el patrón Estado, el patrón Estrategia e inyección de
dependencias:

- **Jugador** — máquina de estados con **30** estados: `IDLE` `WALKING` `JUMPING`
  `FALLING` `CROUCHING` `SHORT_ATTACK` `LONG_ATTACK` `HURT` `DYING` `DASHING`
  `PARRY` `CHARGE_ATTACK` `DASH_ATTACK` `WALL_SLIDE` `LEDGE_GRAB` `GRAB`
  `THROW` `SLIDE` `SWIMMING` `SWIM_ATTACK` `CLIMBING` `ZIPLINE` `ULTIMATE` `AERIAL_ATTACK`
  `AERIAL_SLAM` `GROUND_POUND` `AIR_CHASE` `STAGGER` `POSSESSED` `CHARGE_RELEASE`
- **Escenarios** — carga de TMX con dibujado por pyscroll, capas de colisión,
  puntos de control, zonas de peligro, fosos, bloqueos de cámara y fondos con
  parallax. **108 tipos de objeto** aceptados desde Tiled en ejecución (51
  integrados del framework + 55 del registro en la capa `Objects` —106—
  más `Solid` y `Platform` de la capa `Collision`; medido con
  `scripts/check_tmx_coverage.py --ci`)
- **Enemigos** — 55 tipos registrados sobre ocho arquetipos base (caminante, volador,
  tirador, arquero, embestidor, bruto, hechicero, asesino) con una máquina de
  15 estados
- **Jefes** — fases, telegrafiado, puntos débiles, parry, invocaciones y
  límites de arena
- **ECS** — componentes y sistemas por debajo de la herencia existente, de modo
  que las clases de escenario de los estudiantes siguen funcionando sin tocarlas
- **Efectos** — partículas, clima (lluvia, nieve, niebla, tormenta), números de
  daño, estelas, sacudida de pantalla, post-procesado e iluminación dinámica
- **Audio** — sistema de música dinámica y una tubería con pydub y caché
- **Guion** — IA de enemigos en Lua a través del intérprete lupa
- **Dibujado** — tubería de ModernGL con repliegue por software
- **Persistencia** — guardado con orjson validado con pydantic

## Estructura del proyecto

```
src/
  engine/              núcleo del motor (app, reloj, eventos, entrada, audio,
                       dibujado, escenas, guardado)
  framework/           framework de juego (entidades, escenario, ecs, ia, vfx,
                       ui, procesamiento, académico)
  stages/              el escenario 0 y las entregas de los estudiantes
tests/                 pruebas automatizadas sobre todos los módulos
                     (recontar con `python -m pytest --collect-only -q`)
tools/                 generadores de mapas
scripts/               validadores, calificadores y el previsualizador de TMX
docs/                  documentación completa
```

## Unidades académicas

Ver `docs/08_SYLLABUS_MAPPING.md` para la trazabilidad completa (tema exacto,
componente del framework, entregable, evidencia de aprendizaje) de cada unidad.

| Unidad | Tema | Laboratorio |
|--------|------|-------------|
| II | Coordenadas, vectores, matrices, transformaciones | VectorLabScene, TransformLabScene |
| III | Curvas de Bézier, B-Spline, NURBS, trayectorias | CurveEditorScene, `CurveTools` |
| IV | Objetos, escenas, capas, sprites, búferes | Sistema de escenario TMX |
| V | RGB, HSV, HSL, CMYK, transparencia, iluminación | ColorTheoryScene, `ColorTools` |
| VI | Texturas, animación, interpolación, colisión | CollisionLabScene, `math_utils` |
| VII | Histograma, contraste, convolución, Sobel, Canny | FilterDemoScene, `FilterTools` |
| VIII | Umbral, morfología, componentes, watershed | VisionDemoScene, `VisionTools` |
| IX | Reconocimiento de patrones, clasificación | PatternDemoScene, `PatternRecognitionTools` |

## Licencia

Uso educativo — véase el fichero LICENSE.

## Controles

Teclado: A/D moverse, W/ESPACIO saltar, S agacharse, Z ataque corto,
X ataque largo, C/G agarrar, F/V arco, SHIFT dash, Q/R tiempo-bala.
Mando y ratón también funcionan (`src/engine/input/action_map.py`).
Reasignables desde la escena de controles (se guardan en `keybindings.json`).

## Comandos de estudiante

```
pip install -e ".[dev]"          # instalación completa recomendada
python main.py                   # jugar (añade --stage stage0 para un nivel)
python main.py --help            # todas las opciones (--stage, --boss, --debug, --semilla)
pytest tests/test_habilidades_otorgables.py -q   # ejemplo: un archivo
pytest tests/ -k "collision"     # ejemplo: por patrón
ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/
python scripts/validate_tmx.py --ci
python scripts/grade_stage.py assets/maps/ --json
```

Sin pantalla: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYGAME_HIDE_SUPPORT_PROMPT=1`.

## Límites conocidos (GPU y rendimiento)

El juego corre en CPU/pygame-ce (1280×720, 120 Hz paso fijo). La ruta
GPU/ModernGL es opcional y sólo se certifica con NVIDIA Quadro M2200;
sin esa tarjeta cae a software. Sin medición no se declara ausencia de
fugas: véase `KNOWN_GAPS.md`.

## Guías

- Qué puede hacer cada rol: `docs/88_QUE_PUEDE_HACER_CADA_ROL.md`
- Juego real, capacidades y tareas para continuar: `docs/99_GUIA_DE_JUEGO_Y_HANDOFF.md`
- Crear escenarios/enemigos/jefes: `docs/STAGE_CREATION.md`,
  `docs/ENEMY_CREATION.md`, `docs/BOSS_CREATION.md`
- Diseñar niveles: `docs/66_GUIA_DE_LEVEL_DESIGN.md`
- Flujo de trabajo: inspeccionar → planificar → modificar → probar →
  comprobar en pantalla → documentar → revisar. Nunca modificar código
  sin su prueba (`CONTRIBUTING.md`, `docs/CHANGE_SAFETY_GUIDE.md`).

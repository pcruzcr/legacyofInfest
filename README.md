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
- 6.190 pruebas automatizadas + validadores de TMX, assets y dependencias en CI

```
pip install -r requirements.txt
python main.py
```

Documentación completa en `docs/00_MASTER_INDEX.md`. El manual del
diseñador es `docs/60_GUIA_COMPLETA_DEL_MOTOR.md`.

## Arquitectura

Construido sobre el patrón Estado, el patrón Estrategia e inyección de
dependencias:

- **Jugador** — máquina de estados con **26** estados: `IDLE` `WALKING` `JUMPING`
  `FALLING` `CROUCHING` `SHORT_ATTACK` `LONG_ATTACK` `HURT` `DYING` `DASHING`
  `PARRY` `CHARGE_ATTACK` `DASH_ATTACK` `WALL_SLIDE` `LEDGE_GRAB` `GRAB`
  `THROW` `SLIDE` `SWIMMING` `CLIMBING` `ZIPLINE` `ULTIMATE` `AERIAL_ATTACK`
  `AERIAL_SLAM` `AIR_CHASE` `CHARGE_RELEASE`
- **Escenarios** — carga de TMX con dibujado por pyscroll, capas de colisión,
  puntos de control, zonas de peligro, fosos, bloqueos de cámara y fondos con
  parallax. **78 tipos de objeto** aceptados desde Tiled en ejecución (39
  integrados del framework y 37 del registro una vez descubiertos los
  escenarios, más `Solid` y `Platform` en la capa `Collision`)
- **Enemigos** — 30 tipos registrados sobre ocho arquetipos (caminante, volador,
  tirador, arquero, embestidor, bruto, hechicero, asesino) con una máquina de
  13 estados
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
tests/                 6.190 pruebas sobre todos los módulos
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

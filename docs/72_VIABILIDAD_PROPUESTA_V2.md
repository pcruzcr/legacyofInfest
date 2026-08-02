---
document_id: "LOI-VIABILIDAD-72"
title: "Viabilidad de la propuesta V2, contrastada contra el código"
tags: ["roadmap", "viabilidad", "arquitectura", "medicion"]
source: "docs/72_VIABILIDAD_PROPUESTA_V2.md"
date_processed: "2026-08-02"
---

# Viabilidad de la propuesta V2

**Fecha:** 2 de agosto de 2026 · **Método:** cada afirmación de la propuesta se
ejecutó contra el árbol actual antes de opinar sobre ella.

El resultado corto: **de los seis bloques, dos ya están implementados, uno
contradice una decisión razonada por escrito, dos son parcialmente ciertos y
uno es correcto y vale la pena**. Tres afirmaciones concretas son falsas hoy —
lo eran cuando se escribieron, y el código las resolvió después.

---

## Tabla de veredictos

| # | Propuesta | Estado medido | Viabilidad |
|---|---|---|---|
| 1 | Re-arquitectura multi-motor | Premisa **no confirmada**: 0 ciclos reales | **Baja** — rompe las 26 entregas |
| 2 | Optimización gráfica | `SurfacePool` **ya existe y se usa** | Media (sólo falta `SpriteBatch`) |
| 3 | Reloj musical F6 | **Ya implementado** (AUD-137) | — nada que hacer |
| 4 | i18n con `gettext` | **Ya hay i18n**; `gettext` está descartado por escrito | **Contradice** una decisión razonada |
| 5 | Calificador ciego a las mecánicas | **Correcto y confirmado** | **Alta** — es lo que más vale |
| 6 | Contenido huérfano | 2 de 3 afirmaciones **falsas hoy** | Alta para lo que queda |

---

## 1. Re-arquitectura hacia multi-motor

### «Existe un acoplamiento cíclico entre `engine/` y `framework/`»

**No se confirma.** El análisis de importaciones de los 446 ficheros
(iteración 2 de la auditoría) midió:

- **0 ciclos reales** de importación (Tarjan sobre el grafo de módulos). Los
  cuatro ciclos aparentes están rotos con importación diferida o bajo
  `TYPE_CHECKING`, que es la forma correcta.
- **0 infracciones** de las cuatro reglas de capas: núcleo ↛ framework,
  `framework/processing` ↛ engine, escenario ↛ escenario, y engine/framework ↛
  `stages` (con una única excepción declarada, el jefe de referencia).

Las reglas las vigila `tests/test_layering.py` en cada CI. La premisa de que el
acoplamiento «impide probar piezas de forma aislada» no está respaldada por
ninguna medición del repositorio.

### «Dividir en paquetes instalables por pip (`loi-math`, `loi-physics`…)»

**Viabilidad baja, riesgo alto.** Las 26 clases de escenario de estudiantes
importan rutas `src.framework.*` y `src.engine.*`. Cambiar el nombre de los
paquetes rompe **todas** a la vez, y la invariante 2 dice que deben seguir
funcionando sin tocar una línea. No es una mejora que se pueda hacer sin
romper el material del curso, y el beneficio —poder instalar el motor por
partes— no lo pide ningún caso de uso del temario.

Si algún día se hace, el orden seguro es: crear los paquetes nuevos como
*alias* que reexporten desde las rutas actuales, migrar el motor, y dejar las
rutas viejas vivas durante al menos un semestre completo.

### «`stage_scene.py` ha crecido hasta superar las 1.500 líneas»

**Medido: 1.490 líneas.** No las supera, y el margen no es casualidad:
`tests/test_particion_de_stage_scene.py` fija un presupuesto de 1.500 y falla
si se cruza.

La descomposición **ya ocurrió**: los subsistemas viven en
`src/framework/stage/` —`collision_system`, `drawing_system`, `hazard_system`,
`interactable_system`, `progression_system`, `cutscene_system`…— y `StageScene`
los compone por mixins, con pruebas que vigilan el MRO. Lo que no ocurrió es
que el fichero adelgazara: la partición pasó y el monolito siguió creciendo.
Eso queda registrado, abierto y medido, en **GAP-015**.

**Viabilidad: media.** Seguir extrayendo controladores es sano y no rompe
entregas mientras `StageScene` conserve su API pública. Es trabajo incremental,
no una re-arquitectura.

### «Migrar a `ServiceContainer`; eliminar lambdas `_emit`»

- `ServiceContainer` **no existe** en el árbol.
- Lambdas `_emit` en entidades: **0**. Ya no hay ninguna.

`GameContext` mide **67 líneas** y recibe todos sus managers por constructor;
ya no es el objeto-dios de 400+ líneas que describía GAP-016, que por eso se
cerró. La inyección de dependencias que la propuesta pide, en la práctica, ya
está hecha por constructor.

---

## 2. Optimización del rendimiento gráfico

| Pieza | Estado |
|---|---|
| **`SurfacePool`** | **Ya implementado**: `src/engine/utils/surface_pool.py`, usado en `player.py`, `enemy_base.py`, `enemy_shooter.py` y `tutorial_overlay.py` |
| **Post-procesado en GPU** | `src/engine/render/gl_pipeline.py` existe, con `scripts/bench_gpu_postproc.py` para medirlo. `moderngl` es extra opcional con guarda `try/except ImportError`. **No está cableado en `app.py`** |
| **`SpriteBatch`** | **No existe** |

**«El motor se limita a unos 800 sprites simultáneos»**: ese número no aparece
en ninguna medición del repositorio. Lo que sí hay es
`tests/benchmarks/test_render_benchmark.py`, que mide 1.000 y 2.000 sprites, y
un `baseline_v1.json` con el que comparar.

**Viabilidad: media y sin riesgo para las entregas.** Un `SpriteBatch` es
aditivo: no cambia el API que usan los escenarios. El orden correcto es medir
primero con los benchmarks que ya existen y fijar el objetivo contra
`baseline_v1.json`, en vez de partir de un número que nadie ha medido.

---

## 3. Reloj musical (fase F6)

**Ya está implementado.** `src/engine/audio/music_clock.py`, 240 líneas,
cabecera «AUD-137 (F6) — el reloj musical: pulsos, compases, posición de la
música»:

```python
class RelojMusical:
    def __init__(self, bpm: float = 120.0, compas: int = 4, ...)
    # se alimenta de quien sepa la posición real de la pista,
    # vía `posicion_musica()`
```

Y la mecánica rítmica **ya se sincroniza con él**: `RhythmBlock` acepta una
propiedad `patron` (por ejemplo `"x.x."`), y cuando está presente **manda la
música y los segundos dejan de contar** — exactamente lo que la propuesta pide.
Las propiedades `bpm`, `compas`, `desfase` y `desfase_audio` son declarables
desde Tiled.

El módulo puntúa **72 %** en la comprobación de mutación, por encima del umbral
de 70.

La afirmación de que las mecánicas rítmicas «usan temporizadores independientes
que terminan desfasándose» sólo es cierta si el diseñador **no** pone `patron`,
que es el modo por segundos y está documentado como tal.

**Nada que hacer.** Lo que sí falta es que `docs/STAGE_CREATION.md` explique
cuándo usar `patron` en vez de segundos, cosa que AUD-182 acaba de dejar
publicada.

---

## 4. Localización y documentación

### «Implementar un sistema basado en `gettext`»

**Ya hay sistema de i18n, y `gettext` está descartado con razones escritas.**
`src/engine/core/i18n.py` §F3.1 lleva por título «por qué no se usa `gettext`»,
y su primer argumento es el que manda en este proyecto:

> el flujo de trabajo exige herramientas externas … en un curso «instala las
> herramientas GNU gettext» es una barrera real

Los catálogos son `locale/es.json` y `locale/en.json`, y
`scripts/check_translations.py --ci` los valida en cada CI (ahora mismo:
«Catálogos en orden»).

Migrar a `gettext` es exactamente el tipo de cambio que `CLAUDE.md` §6 advierte:
una decisión deliberada que parece un defecto desde fuera. **Antes de tocarla
hay que rebatir el argumento escrito**, no ignorarlo.

Lo que sí queda por comprobar es la cifra de «300 cadenas codificadas a fuego»:
no se ha medido cuántas cadenas de UI pasan por `i18n` y cuántas están
incrustadas. **Eso sí es una tarea útil y barata**, y es el paso previo a
cualquier decisión.

### «Traducir los 12 manuales que los estudiantes consultan»

**Ésta es la parte buena de la propuesta.** Hay 95 documentos y **un solo par
bilingüe**. La invariante 5 no dice «no traducir»: dice *bilingüe donde hay
lector*, y un manual que un estudiante hispanohablante necesita para su tarea
tiene lector por definición.

**Viabilidad: alta**, con una condición: cada documento traducido entra en el
guardián `tests/test_documentacion_bilingue.py`, que es lo que impide que los
dos lados se desincronicen. Traducir sin ese enganche crea el problema que la
política existe para evitar.

---

## 5. Herramientas de calificación

**Correcto, confirmado, y es lo más valioso de toda la propuesta.**

Medido en la iteración 6: cuatro mapas puntúan **0 de 12** en
`design_completable`. Tres son arenas de jefe y el grader ya lo avisa. El
cuarto es `stage_mecanicas.tmx`, el nivel escaparate del motor, con **11
objetos de movilidad** (4 `RhythmBlock`, 2 `MovingPlatform`, 1 `Spring`, 1
`SinkingPlatform`, 1 `Conveyor`, 1 `WindZone`, 1 `WaterZone`).

El analizador no modela ninguno, y lo dice su propio docstring:

> «no modela dash, salto de pared ni plataformas móviles, así que puede
> declarar *inalcanzable* algo que un jugador experto alcanza»

Un alumno que resuelva un tramo con un resorte pierde 12 puntos por usar el
motor que el curso le enseña.

**Viabilidad: alta.** Dos caminos, y conviene hacer el barato ya:

1. **Barato:** una propiedad de mapa que declare «este nivel no se resuelve
   sólo saltando», igual que ya se hace con las arenas de jefe.
2. **De fondo:** dar a `Spring`, `Zipline`, `Vine` y `MovingPlatform` una
   envolvente propia en el grafo de alcanzabilidad.

**Es un cambio de rúbrica: cambia notas.** Por eso no se ha aplicado — §9 del
protocolo manda que lo decida quien mantiene el temario.

La segunda parte —integrar densidad de enemigos y peligros en la rúbrica— es
viable: `scripts/difficulty_curve.py` ya calcula ese índice por escenario. Sería
conectar dos herramientas que ya existen.

---

## 6. Contenido y sistemas huérfanos

| Afirmación | Medición |
|---|---|
| «10 de 30 enemigos no aparecen en ningún mapa» | **Falsa hoy: 0 de 30.** Los 30 tipos registrados —8 arquetipos, 21 especies y `BossVenado`— aparecen en algún TMX. El Bestiario es completable |
| «La niebla de guerra no la activa nada» | **Falsa:** `fog_of_war` se declara en `stage_mecanicas.tmx`, y `check_tmx_coverage.py --ci` exige que toda propiedad de mapa esté demostrada en algún mapa |
| «El efecto de agua avanzado está invisible» | **Falsa:** hay una `WaterZone` en `stage_mecanicas.tmx` |
| «El modo Boss Rush no lo activa ningún menú» | **Cierta.** `src/framework/stage/boss_rush_mode.py` existe y está probado, y **nadie lo instancia**: la única mención en la interfaz es una etiqueta `"BOSS RUSH"` en la tabla de récords, que muestra `--:--.--` |

**Viabilidad: alta** para lo único que queda. Dar entrada al Boss Rush es
añadir una opción de menú y cablearla, sin tocar el modo en sí. La tabla de
récords ya le reserva sitio.

---

## Qué haría, y en qué orden

1. **Declarar `stage_mecanicas` fuera de la métrica de ruta a pie** (punto 5,
   opción barata). Deja de penalizar a quien usa el motor. Horas de trabajo.
2. **Dar entrada al Boss Rush desde el menú** (punto 6). El sistema ya está
   hecho y probado.
3. **Medir cuántas cadenas de UI no pasan por `i18n`** (punto 4). Barato, y sin
   ese número no se puede decidir nada.
4. **Traducir los manuales del estudiante**, enganchándolos al guardián
   bilingüe (punto 4).
5. **Modelar las mecánicas de movilidad en el grafo de alcanzabilidad**
   (punto 5, de fondo). Es el arreglo que de verdad resuelve el problema.
6. **`SpriteBatch`, midiendo antes contra `baseline_v1.json`** (punto 2).

Y **no haría**, salvo que aparezca un argumento nuevo: la división en paquetes
pip (rompe las 26 entregas para resolver un acoplamiento que no se ha medido) ni
la migración a `gettext` (contradice una decisión razonada y añade una
dependencia de herramientas externas a un curso).

---

## Documentos relacionados

- `docs/71_REVISION_DE_JUEGO.md` — la revisión que midió los puntos 5 y 6
- `docs/70_INFORME_DE_AUDITORIA_VIVO.md` — iteraciones y evidencia
- `KNOWN_GAPS.md` — GAP-015, el monolito, abierto y medido
- `CLAUDE.md` — las invariantes que acotan la viabilidad

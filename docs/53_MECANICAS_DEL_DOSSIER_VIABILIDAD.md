# Las mecánicas del dossier frente a nuestro motor

**Fuente analizada:** dossier GDD de 49 niveles históricos (Top 200).
**Motor:** Legacy of InFest v1.x — pygame-ce 2.5.7, plataformas 2D de ejes.
**Fecha:** 31 de julio de 2026.

> **Continuado en `54_MECANICAS_TOP200_VIABILIDAD.md`.** Este documento analizó
> los primeros 49 niveles; después llegó el Top 200 completo (193 niveles
> únicos). Ninguna conclusión de aquí cambió, pero aparecieron 17 mecánicas más
> —once de ellas de dos días o menos—. Para el análisis vigente, ir al 54.

Este documento no opina sobre si las mecánicas son buenas. Están todas
probadas por la historia. Responde a otra cosa: **cuáles se pueden usar hoy en
nuestro motor, cuáles cuestan una tarde, cuáles son un proyecto de curso, y
cuáles no van a entrar nunca** — con la razón técnica en cada caso, verificada
contra el código y no contra la documentación.

---

## Antes que nada: el 70 % del dossier no es de mecánicas

Vale la pena decirlo primero porque cambia cómo se usa el documento.

De las cinco secciones que trae cada análisis, **tres no dependen del motor en
absoluto**:

| Sección del dossier | ¿Depende del motor? |
|---|---|
| 2. Onboarding y lectura cero | No. Es colocación de objetos en el mapa. |
| 4. Curva de *pacing* | No. Es ritmo: dónde va la tensión y dónde el alivio. |
| 5. Gestión de riesgo y recompensa | No. Es dónde pones el botín y dónde el castigo. |
| 3. Ergonomía y *affordances* | A medias. La claridad visual es arte; las restricciones físicas sí son motor. |
| 1. Arquitectura espacial | A medias. La topología sí; la dimensionalidad no. |

El primer Goomba de Mario está colocado donde está para que sea **inevitable**.
Eso se hace en Tiled, en cualquier motor, hoy mismo. El contraste de las
paredes blancas de Portal frente al metal gris es una decisión de arte que
comunica una regla. Los micro-bucles de tensión y alivio son la estructura de
un nivel, no una característica de un programa.

Y esto conecta con algo que ya tenemos: `scripts/grade_stage.py` puntúa
`design_completable`, `design_geometry` y `design_pacing` — 30 de 130 puntos,
casi una cuarta parte de la nota — que es exactamente lo que el dossier
describe en sus secciones 4 y 5. **El dossier es material de clase para la
parte de la rúbrica que más cuesta a los estudiantes**, y para eso no hace
falta tocar una línea de código.

Dicho eso, vamos a las mecánicas.

---

## A. Se pueden usar hoy, sin tocar el motor (24 mecánicas)

Todo lo de esta tabla existe, está probado y se activa desde Tiled o con dos
líneas en el escenario del estudiante. La columna «cómo» es literal.

| Mecánica del dossier | De dónde sale | Cómo se usa hoy |
|---|---|---|
| Muerte por caída al abismo | Mario 1-1, Celeste, Sonic | Objeto `DeathPit` |
| Púas y zonas letales | Mega Man 2, Celeste | Objeto `HazardZone` con `damage` |
| Reintento instantáneo sin fricción | Celeste, Katana ZERO, Inside | `Checkpoint` + respawn ya cablado |
| **Llaves de color y puertas bloqueadas** | DOOM E1M1, Super Metroid, RE2 | `Key` + `LockedDoor` con `key_id` (F4.1) |
| **Jaulas y celdas que se abren** | Silent Hill 2, RE2 | `Cage` con `key_id` |
| **Cofres y botín** | Spelunky 2, Zelda, Dead Cells | `Chest` con `contenido` |
| **Emboscadas y eventos guionizados** | Half-Life, RE4 (la turba) | `EventTrigger` con `una_vez` |
| Plataformas atravesables desde abajo | Mario, Celeste, Hollow Knight | `Platform` en la capa `Collision` |
| Cámara fija por pantalla o por eje | Celeste, arenas de jefe | `CameraLock` con `lock_x` / `lock_y` |
| Oscuridad como guía y como amenaza | DOOM, Inside, RE2, BioShock | `ambient_light` + objetos `Light` con `flicker` |
| Luz parpadeante de emergencia | Half-Life, BioShock | `Light` con `flicker_speed` / `flicker_amount` |
| Clima que tiñe la escena | Silent Hill 2, Hollow Knight | `climate` (7 valores) + capa de color |
| Partículas de ambiente por zona | Ori, Hollow Knight | `ambient_fx` + `ambient_fx_rate` |
| Ciclo día/noche y estaciones | Zelda BOTW | `start_hour`, `day_length`, `season` |
| Fondos en paralaje multicapa | Sonic, DKC, Ori | Capas `BG_Far` / `BG_Mid` / `BG_Near` |
| **Combate a distancia** | Mega Man, Cuphead, Contra | Arco del jugador (F4.2) + enemigos `Shooter` / `Archer` |
| **Ataque cargado y supermedidor** | Cuphead (super), Ikaruga | `ChargingState` + `special_meter` → ultimate |
| **Dash aéreo limitado** | Celeste, Hades, Hollow Knight | `DashingState` |
| **Deslizarse por la pared y agarrarse al borde** | Celeste, Hollow Knight | `WallSlideState`, `LedgeGrabState` |
| **Parry / desvío de proyectil** | Cuphead, Katana ZERO, Sekiro | `ParryState` |
| **Coger objetos y lanzarlos** | Half-Life 2 (gravity gun), RE4 | `GrabState` + `ThrowState` + `Recogible` (F4.1) |
| Jefes por fases con telegrafiado y castigo | Cuphead, Dark Souls, Ori | `BossBase` + `BossPhase` + `AttackScheduler` |
| Vuelo por patrón (seno, Bézier, ruta, picado) | Cuphead, Ikaruga, Galaga | `flight_strategies`: 5 estrategias |
| Límite de tiempo por nivel | Mario, arcade clásico | `time_limit` |

Dos añadidos que merecen mención aparte, porque los trajo una entrega y no el
motor:

- **Cono de visión y detección por sigilo** (Inside, Metal Gear, RE2): César
  Ubáu lo implementó en `stage2_2/camara_seguridad.py` con álgebra vectorial
  pura. Está ahí, funciona y se puede reutilizar.
- **Patrulla sobre curva B-Spline** (Braid, patrones de arcade): también suyo,
  en `patrulla_bspline.py`.

**Conclusión de la sección A:** un estudiante puede reproducir hoy, sin
programar nada, la estructura de DOOM E1M1 (bucle de llaves de color), la de
RE2 (nexo central con tres alas bloqueadas), la de Mario 1-1 (enseñar por
colocación) y la de Celeste (pantalla, muerte, reintento). Son cuatro de los
niveles más citados del dossier.

---

## B. Cuestan entre una tarde y dos días (11 mecánicas)

Aquí hay que escribir código, pero poco y localizado. Ninguna toca el núcleo.
Son los mejores candidatos para tareas cortas de la fase 2.

| Mecánica | Qué falta exactamente | Coste |
|---|---|---|
| **Resortes y rebotes** | Un tipo TMX que invierta `velocity.y` al tocarlo. El estado aéreo ya existe. | 1 h |
| **Pogo (ataque abajo que rebota)** | `AerialSlamState` ya existe; sólo falta que al impactar devuelva impulso hacia arriba. | 2 h |
| **Puertas cronometradas** | `EventTrigger` ya dispara; falta un `Cerradura` con temporizador que se cierre sola. | 3 h |
| **Interruptores que cambian el mundo** | `EventTrigger` emite al bus y nadie escucha. Falta el receptor. | 3 h |
| **Inundación que sube** (Ori, Ginso Tree) | Un `HazardZone` cuyo `rect` suba con el tiempo. | 3 h |
| **Medidor de estamina** | El patrón ya está resuelto: es otro `special_meter`. Consumir en dash/escalada. | 4 h |
| **Escaleras, lianas y cuerdas** | Un estado nuevo + un tipo TMX. Sin colisión, sólo movimiento vertical libre. | 1 día |
| **Empujar bloques** | Un `Recogible` sólido que arrastre en vez de desaparecer. | 1 día |
| **Bloques destructibles** | Hay que mutar `collision_rects` en caliente. La lista se construye una vez al cargar; hay que hacerla mutable y avisar al dibujado. | 1 día |
| **Plataformas móviles** | El colisionador compara contra rects **estáticos**. Hay que moverlos y, sobre todo, **arrastrar al jugador que va encima** — que es la parte que siempre se olvida y produce el bug de «me quedo flotando». | 1–2 días |
| **Cintas transportadoras** | Igual que las móviles pero sólo con velocidad horizontal aplicada al que pisa. Sale casi gratis después de las móviles. | +3 h |

Nota sobre las dos últimas: **son la carencia más visible del motor frente al
dossier**. Mega Man 2 (Metal Man), Sonic, Donkey Kong Country y Portal
dependen de superficies que se mueven, y hoy no tenemos ninguna. Si sólo se
puede hacer una cosa de esta sección, es ésta.

---

## C. Son un proyecto de curso, no una tarea (9 mecánicas)

Se pueden hacer, y varias serían excelentes proyectos de fase 2 o de práctica
final. Ninguna es imposible; todas cuestan semanas y hay que diseñarlas antes
de escribirlas.

### C.1 — Nado y oxígeno · **hay un hallazgo aquí**

Inside (bosque sumergido), BioShock y Ori dependen de esto. Y resulta que
`SwimmingState` **ya existe en el motor, escrito y completo**, en
`src/framework/entities/states/swim.py`.

Comprobado por análisis del árbol de sintaxis sobre todo `src/`:

```
estados alcanzables: AerialAttackState, AerialSlamState, ChargeReleaseState,
  ChargingState, CrouchingState, DashAttackState, DashingState, DyingState,
  FallingState, GrabState, HurtState, IdleState, JumpingState,
  LedgeGrabState, LongAttackState, ParryState, ShortAttackState, SlideState,
  ThrowState, UltimateState, WalkingState, WallSlideState

HUÉRFANOS: SwimmingState   ← cero transiciones. Nadie puede entrar.
```

Es **exactamente el mismo defecto que el ultimate** que arreglamos esta semana:
un sistema correcto, probado en aislamiento, al que no llega ningún camino. Y
por la misma razón: falta la pieza que lo conecta con el mundo. Aquí serían dos
cosas —un tipo `WaterZone` en el TMX y la transición al entrar en él— y
`SwimmingState` empezaría a usarse tal cual está.

A favor de la documentación de este proyecto, hay que decir que **ya lo sabía**.
`docs/45_SWIMMING_SPEC.md`, línea 59, dice literalmente:

> **Missing:** No dedicated water zone detection; depends on stage collision
> system to trigger state change

El especificador de nado tiene una tabla de física completa —gravedad 0,3×,
velocidad vertical máxima ±80 px/s, salto de nado −120 px/s— y una nota
diciendo que nada dispara el estado. Estuvo escrito y en el repositorio desde
el 14 de julio. No hacía falta encontrarlo: hacía falta leerlo.

**Coste real: medio día, no semanas.** Está en esta sección sólo porque el
oxígeno, la flotabilidad y las criaturas acuáticas sí son trabajo de verdad.

### C.2 — Las otras ocho

| Mecánica | De dónde | Por qué cuesta | Veredicto |
|---|---|---|---|
| **Pendientes y momento cinético** | Sonic, Green Hill | El colisionador es AABB puro contra rectángulos alineados a los ejes. Las rampas exigen otro resolutor: normales de superficie, proyección de velocidad, deslizamiento. Toca el núcleo del jugador y de todos los enemigos. | El cambio más caro de toda la lista. Yo no lo haría en v1. |
| **Generación procedural** | Spelunky 2, Dead Cells, Hades | El cargador lee un TMX de disco. Pero `StageData` es un `dataclass`: se puede construir en memoria sin fichero. La generación en sí es el proyecto. | Muy buen proyecto final. La puerta ya está abierta. |
| **Gancho / *bash* sobre proyectiles** | Ori, Hollow Knight | Estado nuevo + selección de objetivo + pausa de tiempo + reorientación. La parte difícil es que se sienta bien. | Proyecto de un estudiante fuerte. |
| **Rebobinado temporal** | Braid | Historial de estado del mundo por fotograma. Acotado al jugador es factible; con enemigos y proyectiles crece rápido. | Proyecto ambicioso y muy vistoso. |
| **Dos líneas temporales conmutables** | Titanfall 2 | Dos juegos de capas de colisión que se intercambian con un botón. El cargador ya lee varias capas: es más diseño que motor. | Más barato de lo que parece. Recomendado. |
| **Gravedad invertida** | Castlevania SOTN | `gravity_multiplier` existe y admite negativo. Hay que revisar animaciones, salto y cámara. | Media tarde de prueba, una semana de pulido. |
| **Polaridad de color** | Ikaruga | Una propiedad en entidad y en proyectil, y una regla de colisión que la mire. | Sorprendentemente barato para lo original que es. |
| **Roguelike con permadeath** | Spelunky, Dead Cells, Hades | El `SaveManager` y los checkpoints están construidos para lo contrario. Pero eso es una decisión de reglas, no una limitación técnica. | Factible; requiere decidir qué persiste. |

---

## D. No van a entrar en este motor (5 familias)

No por falta de tiempo. Por lo que el motor **es**.

| Mecánica | De dónde | Por qué no |
|---|---|---|
| **Todo lo tridimensional** | DOOM, Half-Life, Metroid Prime, Halo, Super Mario 64, Galaxy, Dark Souls, Elden Ring, Bloodborne, God of War, TLOU, Arkham, BioShock, BOTW, RE4 | Nuestro motor dibuja capas de tiles 2D con `pyscroll` y resuelve colisiones con rectángulos alineados a los ejes. No hay cámara 3D, ni profundidad, ni mallas. Son **19 de los 49 niveles del dossier**: casi el 40 %. |
| **Portales con conservación de momento** | Portal | Exige recolocar al jugador conservando el vector de velocidad a través de una superficie arbitraria, y renderizar recursivamente lo que se ve al otro lado. Ninguna de las dos cosas tiene sentido en un motor de tiles. |
| **Gravedad radial de 360°** | Super Mario Galaxy | La gravedad es un escalar sobre el eje Y. Radial significa que «abajo» es un vector distinto en cada punto, y eso reescribe la física, la cámara y las animaciones. |
| **Cooperativo local asimétrico** | It Takes Two | El `InputManager` es de un jugador y la cámara sigue a uno. No es imposible —es un motor, no una piedra— pero es otro juego, no una mecánica. |
| **Vehículos con suspensión** | Halo (Warthog) | Física de cuerpos rígidos con ruedas. Fuera de alcance. |

**Sobre el 40 % en 3D:** no es un fracaso del motor. El dossier es de los
mejores niveles de la historia, y buena parte de la historia de los videojuegos
es tridimensional. Lo importante es que las **lecciones de diseño** de esos
niveles sí se transfieren: el bucle de atajos de Dark Souls es el mismo bucle
de atajos que se puede construir en 2D con `LockedDoor`, y la turba de RE4
funciona igual en un plano que en tres dimensiones. Lo que no se transfiere es
la cámara.

---

## Resumen en una tabla

| Categoría | Mecánicas | Qué significa |
|---|---|---|
| **A — hoy, sin código** | 24 | Se activan desde Tiled. Un estudiante las usa esta semana. |
| **B — una tarde o dos días** | 11 | Tareas cortas de fase 2. Las plataformas móviles son la prioritaria. |
| **C — proyecto de curso** | 9 | Buenos temas para práctica final. Una (`SwimmingState`) está a medio día. |
| **D — fuera de alcance** | 5 familias | Por dimensionalidad, no por esfuerzo. |

---

## Tres recomendaciones concretas

**1. Conectar `SwimmingState`.** Está escrito, probado y es inalcanzable. Es el
cuarto sistema huérfano de este tipo que aparece este mes —la iluminación que
no iluminaba, las demos que dibujaban en una esquina, el ultimate que nadie
podía cargar, y ahora el nado—. Medio día, y abre los niveles submarinos de
Inside y BioShock como material de clase.

**2. Plataformas móviles y cintas.** Es la única carencia de la sección B que
bloquea niveles enteros del dossier: Mega Man 2, Sonic y Donkey Kong Country
dependen de superficies que se mueven. Uno o dos días, y hay que hacer bien la
parte de arrastrar al pasajero.

**3. Usar el dossier como material de la rúbrica de diseño, no de código.**
Los 30 puntos de `design_completable`, `design_geometry` y `design_pacing` son
lo que más está costando al grupo —cinco de diez entregas tienen plataformas
sin ruta desde el spawn, cinco tienen tramos demasiado largos entre
checkpoints—. Las secciones 4 y 5 de cada análisis del dossier explican
exactamente eso, con ejemplos que los estudiantes ya conocen de haberlos
jugado. Es el uso más rentable del documento y no cuesta nada.

---

## Cómo se comprobó esto

Nada de este documento sale de la documentación del proyecto, que ya nos ha
mentido antes. Todo sale del código:

```bash
# Tipos de objeto que el motor entiende de verdad
python -c "from src.framework.stage.tmx_diagnostics import BUILTIN_OBJECT_TYPES; print(BUILTIN_OBJECT_TYPES)"

# Propiedades de mapa que el cargador lee de verdad
grep -o 'props\.get("[a-z_]*"' src/framework/stage/stage_loader.py | sort -u

# Estados del jugador a los que existe una transición (análisis AST de todo src/)
# — es como se encontró que SwimmingState está huérfano
```

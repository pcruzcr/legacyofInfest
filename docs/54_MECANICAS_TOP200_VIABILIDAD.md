# El Top 200 completo frente a nuestro motor

**Fuente analizada:** `mecanicas level.md` — dossier GDD completo del Top 200.
**Motor:** Legacy of InFest v1.x — plataformas 2D de ejes, pygame-ce 2.5.7.
**Fecha:** 31 de julio de 2026.
**Antecedente:** `53_MECANICAS_DEL_DOSSIER_VIABILIDAD.md`, que analizó los
primeros 49 niveles. Este documento es el superconjunto y lo sustituye.

---

## Lo primero: qué hay realmente en el fichero

Antes de analizar nada conviene decir qué se recibió, porque el recuento no
coincide con el título.

```
bloques «# Análisis…»  : 244
duplicados exactos     :  50
niveles únicos         : 193
juegos distintos       :  72
```

Diez cabeceras «# Dossier Técnico GDD», y dos de ellas están repetidas: el
tramo 26–50 y el tramo 101–125 aparecen dos veces. Los 50 bloques duplicados
salen de ahí. **No es un problema** —para analizar mecánicas da igual—, pero si
el documento se va a repartir a los estudiantes conviene limpiarlo, porque a
quien lo lea de arriba abajo le va a parecer que se ha perdido.

### El reparto que de verdad importa

| Grupo | Niveles | % |
|---|---|---|
| **Plataformas 2D** — nuestro género exacto | 57 | 30 % |
| 2D pero cenital o isométrico (Hotline Miami, Zelda ALTTP, Chrono Trigger, MGS1, Hades) | 14 | 7 % |
| 3D y otros | 122 | 63 % |

Los 57 de la primera fila son el material aprovechable directo, y vienen de 22
juegos: Celeste y Hollow Knight con 8 niveles cada uno, Castlevania con 7 entre
las tres entregas, Mega Man 2 e Inside con 4, Mario con 9 entre las tres
entregas, Sonic con 4, Cuphead con 3.

**Los 14 cenitales merecen un párrafo aparte**, porque es fácil confundirlos
con «2D, luego sirve». Hotline Miami, A Link to the Past y el Metal Gear Solid
original son bidimensionales, sí, pero **de planta**: no hay gravedad, no hay
salto, el eje Y es profundidad y no altura. Nuestro motor tiene una máquina de
estados construida sobre suelo, aire y caída. Un modo cenital no es una
mecánica que se añade: es un segundo motor.

---

## Lo que cambia respecto al análisis anterior

El documento 53 analizó 49 niveles y clasificó 24 mecánicas usables hoy, 11
baratas, 9 caras y 5 imposibles. Con los 193 completos, **ninguna de esas
conclusiones cambia**, pero aparecen **17 mecánicas nuevas** que no estaban en
la primera muestra. Y la sorpresa es que casi todas son baratas.

Van agrupadas por lo que cuestan de verdad.

---

## A. Nuevas y prácticamente gratis (7)

Estas siete salen de piezas que el motor **ya tiene** y que sólo hay que
conectar de otra manera. Ninguna pasa de media jornada.

### A.1 — Tiempo bala / cámara lenta
*Max Payne (Roscoe Street, Ragna Rock, Funhouse), Katana ZERO, Hotline Miami.*

`Clock` ya tiene `time_scale`, y ya se usa para el *hit-stop* del combate:

```python
self.time_scale: float = 1.0
self._dt = raw_dt * self.time_scale
```

El reloj ya distingue el `dt` escalado (simulación) del real (interfaz), que es
justo la separación que el tiempo bala necesita para que el menú no se
ralentice con el juego. **Poner `time_scale = 0.3` mientras se mantiene un
botón es literalmente eso.** Media hora de trabajo, y es una de las mecánicas
más vistosas de la lista.

### A.2 — Muerte instantánea recíproca
*Hotline Miami (los cinco capítulos), Katana ZERO.*

No es motor, es configuración: `max_health = 1` en el jugador y en los
enemigos. La regla de que un solo impacto mata en ambas direcciones ya funciona
con el sistema de daño existente. **Cero código.**

### A.3 — Warp zones / teletransporte
*Super Mario Bros. World 1-2.*

Un `EventTrigger` (F4.1) que, al dispararse, cambia `player.position`. El
disparador ya existe y ya emite al bus; falta el suscriptor. **Una tarde.**

### A.4 — Viento direccional que altera la física
*Mega Man 2 (Air Man), Celeste (Golden Ridge), Hollow Knight (Kingdom's Edge).*

Un `HazardZone` hace hoy exactamente lo necesario —detecta que el jugador está
dentro de un rectángulo— pero sólo sabe restar vida:

```python
@dataclass
class HazardZone:
    rect: pygame.Rect
    damage: float = 0.25
```

Una zona que en vez de daño aplique una aceleración constante es el mismo
dataclass con dos campos más. **Media jornada, y desbloquea tres niveles
clásicos del dossier.**

### A.5 — Suelo con fricción distinta
*Mega Man 2 (cintas), Hollow Knight (la miel de The Hive), hielo en general.*

Mismo patrón que A.4: una propiedad por zona que multiplique la aceleración
horizontal. **Media jornada**, y se puede hacer a la vez que el viento porque
es la misma pieza.

### A.6 — Enemigos con trayectoria sinusoidal desde los márgenes
*Castlevania NES (las Medusa Heads de la Torre del Reloj).*

`flight_strategies.SineFlight` ya existe y hace exactamente esto. **Ya se puede
usar hoy**, sólo faltaba que alguien se diera cuenta.

### A.7 — Doble salto y planeo
*Symphony of the Night (Royal Chapel), Super Mario World.*

`settings.PLAYER_AIR_JUMPS = 1` — **el doble salto ya está.** El planeo con capa
sería un estado nuevo, pero el salto aéreo funciona hoy.

---

## B. Nuevas y baratas: entre media jornada y dos días (7)

| Mecánica | De dónde | Qué falta | Coste |
|---|---|---|---|
| **Haces láser letales temporizados** | MGS (almacén nuclear), Mega Man 2 (Quick Man), Celeste (Mirror Temple) | Un `HazardZone` alargado con ciclo de encendido. La zona ya existe; falta el temporizador. | 3 h |
| **Plataformas que se hunden al pisarlas** | Cuphead (Perilous Piers) | Un rect que baja tras N segundos de contacto. Requiere la misma pieza que las plataformas móviles. | 4 h |
| **Bloques que aparecen y desaparecen a compás** | Mega Man 2 (Wily 1), Celeste (bloques de cassette) | Meter y sacar rects de `collision_rects` con un temporizador. | 4 h |
| **Parada temporal / congelar enemigos** | Mega Man 2 (*Time Stopper* en Quick Man) | Un flag que salte el `update` de los enemigos. El bucle ya los recorre. | 4 h |
| **Scroll forzado que empuja y mata** | SMB3 (Airship), Cuphead, Ori (Ginso), Celeste (pantallas de persecución) | La `Camera` sabe seguir y sabe bloquearse; falta que avance sola y que el borde izquierdo sea letal. | 1 día |
| **Perseguidor implacable que no se puede matar** | RE3 (Nemesis), Celeste (el conserje del Cap. 3), Spelunky (el fantasma) | `ChaseFlight` ya persigue. Falta que sea invulnerable y que persista entre pantallas. | 1 día |
| **Estado de alerta por sigilo** | MGS (Tank Hangar), Inside (la granja) | El cono de visión ya existe: lo escribió César en `stage2_2/camara_seguridad.py`. Falta la máquina de tres estados —normal, alerta, evasión— y que los enemigos reaccionen. | 1–2 días |

Sobre el sigilo: es la mecánica **con mejor relación entre lo que cuesta y lo
que enseña**. El cono de visión es álgebra vectorial pura —Unidad II del
temario— y ya hay una implementación de un estudiante que se puede leer en
clase.

---

## C. Nuevas y caras: proyecto de curso (3)

| Mecánica | De dónde | Por qué cuesta |
|---|---|---|
| **Oxígeno bajo el agua con cuenta atrás** | Sonic (Labyrinth), Sonic 2 (Chemical Plant), SMB3 (Water Land), Inside (bosque sumergido) | Ver la sección siguiente. La parte de nado ya está escrita; el oxígeno, las burbujas y las corrientes son el trabajo. |
| **Vuelo libre de 360° con inercia** | Celeste (la pluma dorada del Cap. 6) | Un estado que ignora la gravedad y acelera en cualquier dirección, con frenado propio. Es un estado nuevo completo, y lo difícil es que se sienta bien. |
| **Vagoneta / avance automático sobre raíl** | DKC (Mine Cart Carnage), FFVII (la moto) | Scroll forzado + el jugador montado en algo que se mueve solo. Se abarata mucho si antes se han hecho las plataformas móviles y el scroll forzado. |

---

## El nado vuelve a aparecer, y ahora con cuatro niveles detrás

En el documento 53 encontré que `SwimmingState` **está escrito, completo y
tiene cero transiciones**: nadie puede entrar. Verificado por análisis del
árbol de sintaxis sobre todo `src/`.

Con la muestra de 49 niveles había **un** nivel acuático. Con los 193 hay
**cuatro**: Sonic Labyrinth Zone, Sonic 2 Chemical Plant, Super Mario Bros. 3
Water Land e Inside Submerged Forest. Y tres de ellos giran sobre lo mismo —la
cuenta atrás de oxígeno—, que es la parte que no está escrita.

Y `docs/45_SWIMMING_SPEC.md`, línea 59, lo dice desde el 14 de julio:

> **Missing:** No dedicated water zone detection; depends on stage collision
> system to trigger state change

Sigue siendo la corrección de mejor relación coste/beneficio de todo el
análisis: **medio día** para conectar el estado que ya existe.

---

## Lo que sigue sin poder entrar (y ahora es más del doble)

| Familia | Niveles del dossier | Por qué no |
|---|---|---|
| **3D en todas sus formas** | 122 de 193 — **el 63 %** | Dibujamos capas de tiles 2D con `pyscroll` y resolvemos colisiones con rectángulos alineados a los ejes. Bloodborne, God of War, The Last of Us, Halo, BioShock, Uncharted, Arkham, Portal 2, DOOM Eternal, Elden Ring, Metroid Prime, Mario 64 y Odyssey. |
| **2D cenital** | 14 | Hotline Miami, A Link to the Past, Chrono Trigger, MGS1, Hades. Sin gravedad ni salto: el eje Y es profundidad. Sería un segundo motor. |
| **Controles de tanque con cámara fija** | Resident Evil clásico, Silent Hill | Depende de una cámara prerrenderizada que cambia de plano. No tiene equivalente en scroll lateral. |
| **Pendientes con momento cinético** | Sonic (4 niveles) | Nuestro colisionador es AABB puro. Las rampas exigen normales de superficie y proyección de velocidad. Toca el núcleo del jugador y de los 30 enemigos. Sigue siendo lo más caro de la lista. |

**El 63 % en 3D no es un fracaso.** El Top 200 de la historia del medio es
mayoritariamente tridimensional porque el medio lo es. Lo importante es que las
**lecciones** sí cruzan: el bucle de atajos de Dark Souls es el mismo bucle que
se construye en 2D con `LockedDoor`, la turba de RE4 funciona igual en un plano
que en tres dimensiones, y el vestíbulo central de RE2 con tres alas bloqueadas
es reproducible hoy en Tiled sin escribir una línea. Lo que no cruza es la
cámara.

---

## Resumen

| | Documento 53 (49 niveles) | Este (193 niveles) |
|---|---|---|
| Usables hoy sin código | 24 | 24 **+ 3** = 27 |
| Media jornada o menos | — | **+ 4** |
| Entre un día y dos | 11 | 11 **+ 7** = 18 |
| Proyecto de curso | 9 | 9 **+ 3** = 12 |
| Fuera de alcance | 5 familias | 4 familias, 136 niveles |

**Lo que hay que quedarse:** cuadruplicar la muestra no descubrió ninguna
barrera nueva. Descubrió **17 mecánicas más, y once de ellas cuestan dos días o
menos** — porque salen de piezas que ya tenemos usadas de otra forma:
`time_scale` para el tiempo bala, `HazardZone` para el viento y los láseres,
`SineFlight` para las Medusa Heads, `ChaseFlight` para el perseguidor, el cono
de visión de un estudiante para el sigilo.

Eso dice algo bueno del motor: **las piezas están bien elegidas.** Lo que falla
una y otra vez no es que falten piezas, es que las que hay no están conectadas
—el nado, el ultimate, la iluminación, las demos—. El patrón se repite tanto
que ya es la lección principal del semestre.

---

## Cuatro recomendaciones, por orden de rentabilidad

1. **Tiempo bala** — media hora. `time_scale` ya existe y ya se usa. Es lo más
   espectacular por lo que cuesta, y da tres niveles del dossier (Max Payne,
   Katana ZERO).
2. **Conectar `SwimmingState`** — medio día. Está escrito, es inalcanzable, la
   especificación ya lo admitía, y ahora hay cuatro niveles que lo piden.
3. **Zonas con efecto físico** (viento, fricción, láseres temporizados) — un
   día para las tres, porque comparten pieza. Desbloquean Air Man, Golden
   Ridge, Quick Man, Mirror Temple y The Hive.
4. **Plataformas móviles** — sigue siendo la carencia estructural. Uno o dos
   días, y abarata después los bloques rítmicos, las plataformas que se hunden
   y la vagoneta.

Y la de siempre, que no cuesta nada: **usar las secciones 4 y 5 de cada
análisis como material de clase.** Onboarding, pacing y riesgo/recompensa no
dependen del motor y son exactamente los 30 puntos de `design_pacing`,
`design_geometry` y `design_completable` donde el grupo está perdiendo más
nota. Con 193 análisis hay ejemplo para cada semana del curso.

---

## Cómo se comprobó

```bash
# Recuento real del fichero, duplicados incluidos
grep -c "^# Análisis" "mecanicas level.md"        # 244 bloques, 193 únicos

# Que time_scale existe y ya se usa
grep -n "time_scale" src/engine/core/clock.py

# Que el doble salto existe
grep -n "PLAYER_AIR_JUMPS" src/engine/core/settings.py

# Que HazardZone sólo sabe hacer daño
grep -n "class HazardZone" -A 6 src/framework/stage/stage_loader.py

# Que SwimmingState no tiene ninguna transición de entrada
#   (análisis AST de todas las llamadas a _change_state_instance en src/)
```

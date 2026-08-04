# Fase 5 — ECS por debajo, y las mecánicas del Top 200

**Fecha:** 31 de julio de 2026
**Antecedentes:** `53_`, `54_` (mecánicas de nivel) y `55_` (mecánicas de jefe).

---

## La decisión que gobierna todo lo demás

Antes de escribir una línea se midió el acoplamiento:

```
clases de estudiantes que heredan de la jerarquía : 26
líneas de código de estudiantes                   : 18.054
líneas de pruebas                                 : 21.588
accesos a `rect` / `position` en el motor         : 255
reasignaciones de `rect` / `position` en entregas :  14
```

Una migración a ECS «pura» rompe las 26 clases. Acababan de entregarlas,
presentarlas y ser calificadas. **Ninguna mejora arquitectónica vale eso.**

Así que el ECS va **debajo** de la jerarquía, no en su lugar: la estructura
nueva crece alrededor de la vieja y la sostiene. `BaseEntity`, `EnemyBase`,
`BossBase` y `StageScene` siguen siendo exactamente lo que eran para quien los
hereda; por dentro, sus datos viven en componentes que cualquier sistema puede
leer.

---

## Qué se añadió

### El núcleo (`src/framework/ecs/`)

| Fichero | Qué hace |
|---|---|
| `world.py` | El almacén: `tipo → {entidad: componente}`. Identificadores que nunca se reutilizan, bajas diferidas, consultas que empiezan por el componente más raro. |
| `components.py` | Los datos, sin comportamiento. 17 componentes. |
| `systems.py` | El comportamiento, sin datos. 11 sistemas. |
| `scheduler.py` | El orden de un fotograma, en una lista con nombre y motivo. |
| `bridge.py` | El puente con la jerarquía. |
| `bullet_swarm.py` | Arrays de NumPy para los miles de proyectiles. |

### El puente, y los tres intentos que hicieron falta

`rect` y `position` tenían que seguir funcionando con mutación en el sitio
—`self.rect.centerx = 40`, 115 veces en las entregas— **y** llegar a los
componentes. Se probaron tres formas y se midieron las tres:

| Forma | Coste de `.rect` | Fotograma del prólogo |
|---|---|---|
| Propiedad que lee el componente | 404 ns | 21,4 ms |
| Atributo + `__setattr__` vigilante | — | 34,6 ms |
| **Atributo normal, componente como vista** | **66 ns** | **9,4 ms** |

La tercera ganó y es la que está. El dueño tiene `rect` y `position` como
atributos normales —lectura idéntica a antes de la fase 5— y es el **componente
`Transform` el que hace la indirección**, leyendo del dueño. Se paga donde es
barato: los sistemas recorren decenas de entidades, no cientos de veces por
fotograma.

De regalo resuelve el caso que motivó todo: si un estudiante reasigna
`self.rect = otro`, la vista lo ve al instante, porque nunca guardó una copia
que pudiera quedarse vieja.

### El benchmark que casi hace deshacer el diseño

Midiendo el coste salieron, con el mismo código y la misma máquina: **27,29 ms,
21,36, 34,58, 30,89**. Con esa varianza se llegó a concluir que la fase 5
costaba un **63 %** del fotograma.

El perfilador dijo otra cosa: **1,449 s en `builtins.compile`**, 445
compilaciones, 671 `marshal.loads`, 1.245 aperturas de fichero. El predictor de
IA y la iluminación importan scipy y llvmlite de forma perezosa, y esas
importaciones caían **dentro de la ventana medida**. Se estaba cronometrando el
arranque de una biblioteca científica.

Con 400 fotogramas de calentamiento y la mediana de nueve tandas:

```
sin fase 5 : 9,07 ms
con fase 5 : 9,42 ms      → 4 %, dentro del ruido
```

Queda fijado en `tests/test_ecs.py::TestElCosteDelPuente`, con la historia
escrita, porque **un benchmark sin calentamiento suficiente miente en la
dirección que confirma lo que uno teme**.

---

## Las mecánicas, y de dónde sale cada una

Once tipos nuevos de Tiled. Todos usables sin escribir código.

| Tipo TMX | Mecánica | De dónde |
|---|---|---|
| `WindZone` | Viento que empuja | Mega Man 2 (Air Man), Celeste (Golden Ridge) |
| `FrictionZone` | Hielo, miel, agarre distinto | Hollow Knight (The Hive) |
| `Conveyor` | Cinta transportadora | Mega Man 2 (Metal Man) |
| `LaserZone` | Láser con ciclo y aviso | MGS, Mega Man 2 (Quick Man), Celeste (Mirror Temple) |
| `ShockwaveZone` | Onda periódica con refugio | Inside (la mina) |
| `WaterZone` | Agua, nado y oxígeno | Sonic (Labyrinth), SMB3, Inside |
| `MovingPlatform` | Plataforma móvil **con arrastre** | Mega Man 2, Sonic, DKC |
| `RhythmBlock` | Bloque que aparece a compás | Mega Man 2 (Wily 1), Celeste (cassette) |
| `SinkingPlatform` | Se hunde al pisarla | Cuphead (Perilous Piers) |
| `Guard` | Cono de visión y alerta | MGS (Tank Hangar), Inside |
| `Stalker` | Perseguidor invulnerable | RE3 (Nemesis), Celeste, Metroid Dread |

Y en código:

* **Tiempo bala** (`TiempoBala`) — Max Payne, Katana ZERO. `Clock.time_scale` ya
  existía para el *hit-stop*; era media hora de trabajo.
* **Scroll forzado** (`ScrollForzado`) — SMB3 Airship, Cuphead, Ori, Terraria.
* **Bullet hell** (`EnjambreDeBalas`) — Ikaruga, Enter the Gungeon.
* **Parry del jefe** (`BossAttack.parriable`) — Sekiro, Katana ZERO, MGR.
* **Fase invulnerable y escalado** (`BossPhase.invulnerable`, `.escala`) — Nosk,
  Baby Bowser, Mega Satan.
* **Teletransporte** (`BossBase.teletransportar`) — Death, Agahnim.

> ⚠️ **«En código» no quería decir «en el juego» (AUD-243, `GAP-032`).**
>
> Medidas una por una con `grep` sobre `src/`, cinco de las siete **no las
> invoca nadie**. No fallan: simplemente no ocurren, y no hay ningún error que
> lo diga.
>
> | Mecánica | ¿La usa el juego? |
> |---|---|
> | Parry del jefe | **Sí**, desde AUD-243 |
> | Fase invulnerable | **Sí** (`boss_base.py:208`) |
> | **Scroll forzado** | **Sí**, desde AUD-249 — objeto `ScrollZone` en Tiled |
> | Tiempo bala | No — se construye y no se vuelve a tocar |
> | Bullet hell | No — 0 usos fuera de su módulo |
> | Escalado de fase | No — `escala_de_fase` sólo se define |
> | Teletransporte | No — 0 usos |
>
> **No diseñes un nivel que dependa de las cuatro que faltan.** El detalle y el
> camino de resolución de cada una están en `GAP-032` de `KNOWN_GAPS.md`.

### Scroll forzado: cómo se pone (AUD-249)

Un objeto de tipo `ScrollZone` en la capa de objetos. **Su rectángulo es el
disparador, no la zona de muerte**: el jugador lo pisa una vez y a partir de
ahí manda la cámara. Quien mata es el borde izquierdo de la pantalla.

| Propiedad | Por defecto | Qué hace |
|---|---|---|
| `velocidad_x` | 40 | px/s de la cámara. Negativo = hacia la izquierda |
| `velocidad_y` | 0 | px/s vertical, para una subida tipo Ori |
| `margen_de_gracia` | 24 | px que se puede rebasar el borde antes de morir |
| `parar_en_x` | — | la cámara se detiene ahí; sin ella, hasta el final |

El margen de gracia existe porque sin él la muerte ocurre cuando el sprite aún
se ve, y eso se lee como injusticia aunque sea correcto.

### Dos detalles que casi siempre se olvidan, y aquí no

**El arrastre de plataformas.** Sin él, el jugador se queda clavado en el aire
mientras la plataforma se va, y parece un fallo de colisión cuando es un sistema
que falta. Corre **entre** el movimiento de la plataforma y la resolución de
colisiones; al revés, el pasajero pasa un fotograma hundido y sale expulsado al
siguiente.

**El margen del sensor de pasajero.** Cero no vale: tras resolver la colisión el
pasajero queda apoyado, con su borde inferior exactamente en el superior de la
plataforma, y un `colliderect` de rectángulos que sólo se tocan da `False`.

---

## El nado, cuarto sistema huérfano del mes

`SwimmingState` estaba escrito, completo y probado. Un análisis del árbol de
sintaxis sobre todo `src/` demostró que tenía **cero transiciones de entrada**:
nadie podía nadar.

Y `docs/45_SWIMMING_SPEC.md`, línea 59, lo decía desde el 14 de julio:

> **Missing:** No dedicated water zone detection; depends on stage collision
> system to trigger state change

Es el cuarto de la misma forma en un mes —la iluminación que no iluminaba un
píxel, las trece demos que dibujaban en una esquina, el ultimate cuyo medidor
nadie incrementaba— y siempre igual: código correcto, probado en aislamiento, al
que no llega ningún camino desde el juego.

Ya llega. `ZonaDeAgua` + `ControlDeNado`, con oxígeno y aviso.

---

## Bullet hell: por qué NO es ECS, con números

| balas | objeto por bala | enjambre NumPy | factor |
|---|---|---|---|
| 500 | 3,96 ms | 0,148 ms | 27× |
| 1000 | 5,48 ms | 0,092 ms | 59× |
| 2000 | **12,94 ms** | 0,072 ms | 180× |
| 3000 | 10,44 ms | 0,073 ms | 143× |

*(presupuesto a 60 fps: 16,667 ms)*

A dos mil balas, un objeto por bala se come el **78 % del fotograma** sin haber
dibujado nada. El enjambre gasta el 0,4 %, y apenas sube al triplicar la cuenta
porque el coste ya no está en las balas sino en la llamada a NumPy: tiempo fijo,
no por bala.

**La regla del motor, dicha corta:**

* Pocas entidades, cada una distinta → componentes y sistemas.
* Muchas entidades, todas iguales → arrays paralelos.

Un jefe es lo primero. Sus balas son lo segundo. Tener las dos formas y saber
cuándo toca cada una es mejor lección que aplicar una sola a todo.

---

## Verificación

```
las 14 entregas cargan y dibujan ........................ 14/14
pruebas nuevas .......................................... 120
  tests/test_ecs.py ..................................... 44
  tests/test_mecanicas_f5.py ............................ 35
  (el resto, repartidas en las suites existentes)
ruff sobre motor, framework, pruebas y scripts ......... limpio
coste de fotograma frente a antes de la fase 5 ......... +4 % (ruido)
```

**Verificación por mutación** — cinco mutaciones, cinco detectadas:

| Mutación | Pruebas en rojo |
|---|---|
| El puente devuelve copias de `rect` | 1 |
| El arrastre de plataformas no arrastra | 1 |
| El nado no cambia el estado del jugador | 2 |
| Se puede desviar durante la ventana de castigo | 1 |
| El enjambre no consume las balas que impactan | 1 |

---

## Lo que queda declarado como deuda

1. **El jugador no es una entidad ECS.** `StageScene._mundo_ecs_paso` llama a
   los sistemas a mano y en orden explícito en vez de usar el `Planificador`,
   porque el jugador es una fachada y tendría que entrar y salir del mundo cada
   fotograma. Cuando lo sea, esa función se sustituye por
   `planificador.ejecutar(mundo, dt)` y desaparece.
2. **`Salud` está duplicada** con `current_health` de `EnemyBase`, y se
   sincroniza. El día que ninguna entrega dependa de `current_health`, el
   componente pasa a ser la única verdad.
3. **Ninguna entrega usa todavía las mecánicas nuevas.** Están en el motor y en
   la guía del estudiante; lo que falta es un escenario de referencia que las
   enseñe, que es material de la Práctica II.

Las tres son decisiones tomadas con su motivo escrito, no descuidos.

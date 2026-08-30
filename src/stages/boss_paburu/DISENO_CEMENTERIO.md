# Stage 4-1b — El Cementerio Sagrado (corredor propio)

Diseño previo al TMX. Ninguna medida de acá es estimada: todas salen de las
constantes del motor y están comprobadas.

---

## 1. Las reglas físicas — medidas, no supuestas

```
velocidad de caminata      90 px/s
velocidad EN EL AIRE       45 px/s   ← la mitad (framework/entities/states/airborne.py:52)
tiempo en el aire          0.95 s
tamaño del jugador         20 × 32 px
```

De ahí sale lo único que importa para trazar geometría:

| Movimiento | Alcance real | En tiles de 16 |
|---|---|---|
| Altura, salto simple | 90 px | 5.6 |
| Altura, doble salto | 180 px | 11.3 |
| **Horizontal, salto simple** | **43 px** | **2.7** |
| Horizontal, doble salto | ~81 px | 5.1 |

**El número que rompe niveles es el horizontal.** La intuición dice 86 px
—velocidad de suelo por tiempo de vuelo— y la realidad es la mitad, porque el
aire no conserva la velocidad. Cuatro de las diez entregas del grupo tienen
repechos imposibles por diseñar contra el número equivocado.

### Reglas de trazado

| Regla | Valor | Por qué |
|---|---|---|
| Hueco máximo cómodo | **32 px** (2 tiles) | 75 % del alcance; deja margen de error |
| Hueco máximo exigente | 43 px (2.7 tiles) | Al límite: solo donde el fallo no mate |
| Repecho de un salto | **64 px** (4 tiles) | 80 % de la altura |
| Repecho con doble salto | 144 px (9 tiles) | Solo si ya se enseñó el doble salto |
| Separación entre checkpoints | **≤ 400 px** | Cinco de diez entregas perdieron nota acá |

---

## 2. Alcance, y una advertencia

El profesor pidió un **corredor pequeño** que conecte con su 4-1 largo. Lo que
describiste —cementerio abierto, lago con nado, plataformas difíciles,
enemigos como trampolín— es un nivel completo.

La propuesta de acá busca las dos cosas: **1600 × 608 px (100 × 38 tiles)**.
Es la mitad de largo que el stage2_2 de César (120 × 50) y sigue siendo un
corredor, pero con densidad suficiente para tus cuatro ideas.

Si el profesor quiere algo más corto, la sección que se recorta primero es el
lago —está bloqueada de todos modos— y el nivel sigue teniendo sentido.

---

## 3. El recorrido, sección por sección

```
 x=0                400               800              1200            1600
 │                   │                 │                 │                │
 ├── A ──────────────┼─── B ───────────┼─── C ───────────┼─── D ─────────┤
 │  ENTRADA          │  LAS TUMBAS     │  EL POZO        │  EL CÍRCULO   │
 │  aprender         │  combate        │  el lago        │  la trampa    │
 │                   │                 │                 │                │
 CP1                 CP2               CP3               (sin CP)
```

### A · La entrada (x 0–400) — enseñar sin decir nada

Llano, sin enemigos los primeros 200 px. Un `MessageTrigger_Once` con una
línea de lore. Al final, **un hueco de 32 px** sobre una fosa poco profunda:
el jugador aprende a saltar donde fallar no cuesta nada.

Un `Light` con parpadeo cada 150 px marca el camino. La luz es la guía.

`Checkpoint 1` al final de la sección.

### B · Las tumbas (x 400–800) — el combate

Aquí van tus esqueletos y murciélagos:

| Enemigo | Tipo del motor | Dónde |
|---|---|---|
| Esqueleto | `Walker` | Suelo, entre lápidas, con `patrol_length` corto |
| Murciélago | `Flying` con `flight_mode="sine"` | Sobre el camino, obliga a agacharse o cronometrar |

**Máximo 3 tipos de enemigo por stage** (regla del curso). Con `Walker` y
`Flying` quedan dos; el tercero se reserva para la sección D.

Plataformas a **64 px** de altura — un salto simple — con lápidas caídas como
suelo. Ninguna sin ruta de vuelta.

`Checkpoint 2`.

### C · El pozo (x 800–1200) — la bifurcación

Tu idea del lago, con las dos rutas que planteaste.

**Ruta baja — nadar.** Un `WaterZone` de 300 px de ancho. Dentro, un enemigo
que persigue. Si nadás lento, te alcanza.

> **Bloqueada hoy.** `WaterZone` no existe en esta versión del motor y
> `SwimmingState` está escrito pero huérfano — cero transiciones de entrada.
> El profesor dice que ya lo corrigió en su rama. **Se traza el hueco ahora y
> se llena de agua cuando llegue.** Mientras tanto es una fosa mortal, y la
> sección se recorre por arriba.

**Ruta alta — las plataformas.** Cuatro salientes sobre el agua, separadas
**40 px** cada una: dentro del alcance de 43, pero al límite. Ahí sí se
justifica, porque fallar te tira al agua y no te mata.

Y aquí entra tu idea de Mario: **un murciélago patrullando entre la plataforma
2 y la 3**, en un hueco de 70 px que **no se puede cruzar de un salto**. Hay
que rebotar sobre él. Es el momento de enseñanza del nivel: el enemigo deja de
ser obstáculo y pasa a ser plataforma.

`Checkpoint 3` al salir del pozo, antes de la trampa.

### D · El círculo (x 1200–1600) — la emboscada

Un claro abierto y sospechosamente vacío. Marcas grabadas en el suelo —las
mismas del sello— que el jugador ya vio en la pelea anterior si jugó 4-2.

**El disparador NO está al final**, como pediste: está a x=1400, con 200 px de
espacio por delante. Al cruzarlo:

1. Se apagan los cuencos de fuego. Medio segundo de negro.
2. **Suena el stinger** — el sonido raro.
3. Aparecen dos muros de piedra: uno en x=1340 y otro en x=1600. La cámara se
   bloquea con `CameraLock`.
4. Paburu emerge del centro del círculo.

El jugador queda encerrado en 260 px de arena con el jefe. **Sin checkpoint
dentro**: si muere, vuelve al CP3 y tiene que volver a entrar.

---

## 4. Qué se puede construir hoy

| Pieza | Estado | Cómo |
|---|---|---|
| Geometría, tumbas, luces | **Hoy** | TMX + `Light` + `climate` |
| Esqueletos y murciélagos | **Hoy** | `Walker` y `Flying` |
| Checkpoints y mensajes | **Hoy** | `Checkpoint`, `MessageTrigger_Once` |
| **Cerrar la sala** | **Hoy** | Añadir rects a `stage.collision_rects` en caliente. **Verificado**: el jugador frena contra un muro creado a mitad de partida. |
| Aparición de Paburu | **Hoy** | Lo controla la escena, igual que la intro |
| **Rebote sobre enemigos** | **Hoy, desde la escena** | El motor no lo trae. Se detecta que el jugador cae sobre la cabeza de un enemigo y se le da impulso. Mismo patrón que el punto débil. |
| Nado y el que jala | **Bloqueado** | `WaterZone` no existe. Esperar la rama del profesor. |

---

## 5. Riesgos, y cómo los evitamos

**Ruta rota desde el spawn.** Es el fallo más repetido del grupo. Antes de dar
el TMX por bueno, se recorre programáticamente: desde el `PlayerSpawn`, ¿se
llega al final respetando 32 px de hueco y 64 px de repecho? Si no, se marca
dónde se corta.

**El pozo sin agua es una fosa mortal.** Mientras el nado no exista, hay que
asegurar que la ruta alta sea completable sola. Si depende del rebote sobre el
murciélago y el murciélago está en el otro extremo de su patrulla, el jugador
queda esperando. Hay que acotar su recorrido.

**El encierro puede volverse injusto.** 260 px es poco para esquivar al
`EL SELLO`, que ocupa 224 px de ancho. Al construirlo hay que medir si hay
dónde ponerse, o ampliar la cámara final.

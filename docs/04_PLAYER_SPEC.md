---
document_id: "LOI-PLAYER-004"
title: "Legacy of InFest — Especificación del jugador"
aliases: ["Especificación del jugador", "Player Specification"]
tags: ["jugador", "fisica", "estados", "combate"]
description: "El personaje jugable: controles, física, salud, daño, ataques, estados y cajas"
source: "docs/04_PLAYER_SPEC.md"
date_processed: "2026-08-11"
---

# Legacy of InFest — Especificación del jugador

**Identificador:** LOI-PLAYER-004
**Versión:** 2.0.0
**Estado:** Oficial
**Público:** profesorado, personal de apoyo, estudiantes y asistentes de código

---

## 1. Concepto

El personaje jugable es una figura encapuchada de identidad indeterminada. La
capucha no es una elección estética: es un recurso narrativo. El personaje no
revela deliberadamente si es Jhon o Jin, los dos protagonistas del universo de
Legacy of InFest. Esa ambigüedad sirve al contexto tutorial del escenario 0: el
personaje es el avatar del jugador y del estudiante, no un personaje de la
historia en sentido pleno.

El diseño visual tiene que comunicar:

- **agilidad** — silueta esbelta, animación fluida;
- **misterio** — capucha profunda, cara nunca visible;
- **autenticidad de la época SNES** — paleta limitada y silueta legible a
  16×16 y 32×32.

El personaje **no es personalizable**. Los estudiantes no lo modifican: es un
recurso compartido del framework.

---

## 2. Para qué sirve

**2.1 Ancla de interacción.** Es el agente por el que estudiantes y jugadores
tocan todos los sistemas del escenario. Los puntos de control los alcanza él,
los enemigos reaccionan a él, el HUD refleja su estado y las demostraciones del
escenario 0 se disparan por su proximidad o su acción.

**2.2 Referencia de máquina de estados.** Su autómata es el ejemplo más
completo de gestión de estados del framework. Es el que se estudia antes de
escribir una entidad propia.

**2.3 Portador de conceptos académicos.** Su movimiento, su física y su
animación encarnan conceptos de las Unidades II a VI: aritmética vectorial,
matrices de transformación, interpolación de fotogramas, detección de
colisiones, animación de sprites y mezcla alfa.

---

## 3. Controles

Todo pasa por el `InputManager`. El jugador **nunca** consulta pygame
directamente.

| Acción | Teclado | Mando |
|---|---|---|
| Caminar a la izquierda | ← · A | Cruceta izquierda · stick izquierdo |
| Caminar a la derecha | → · D | Cruceta derecha · stick derecho |
| Saltar | Espacio · W · ↑ | A (Xbox) · Cruz (PS) |
| Agacharse | ↓ · S | Cruceta abajo · stick abajo |
| Ataque corto | Z · J | X (Xbox) · Cuadrado (PS) |
| Ataque largo | X · K | Y (Xbox) · Triángulo (PS) |

**Reglas:**

- Saltar exige estar apoyado **o dentro de la ventana de *coyote time***
  (§4.2). No es lo mismo, y la diferencia se nota al jugar.
- Los dos ataques funcionan andando, quieto o agachado.
- El ataque largo agachado hace un barrido bajo.
- No se puede cambiar de dirección durante la animación de ataque.
- **La pulsación de salto se guarda 8 fotogramas** (§4.2).

> **Corregido el 2026-08-11 (AUD-432).** Este apartado decía «saltar sólo está
> disponible estando apoyado» y «sin buffer de salto más allá de 4 fotogramas».
> Lo primero **contradice a la propia §4.2** de este documento, que explica el
> *coyote time*; lo segundo era un número obsoleto — la ventana la lleva
> `InputManager.VENTANA_DE_BUFFER` y son **8**.

---

## 4. Movimiento

### 4.1 Horizontal

Velocidad constante, sin rampa de aceleración ni de frenado. Mantiene el modelo
simple y fiel a la época (la referencia es *Super Castlevania IV*).

Y **no es la misma en el suelo que en el aire**:

| Propiedad | Valor | Unidad |
|---|---|---|
| Velocidad en suelo | 90,0 | px/s |
| Control aéreo | 45,0 (`walk_speed * 0.5`) | px/s |
| Dirección | −1 (izquierda) o +1 (derecha) | — |
| Orientación | `facing_direction: int` | — |

La velocidad **se asigna, no se acumula**; el `dt` se aplica después, cuando el
resolutor integra la posición:

```
en suelo:  velocity.x = direccion * PLAYER_WALK_SPEED          # 90 px/s
en el aire: velocity.x = direccion * PLAYER_WALK_SPEED * 0.5   # 45 px/s
```

**La inercia que se conserva (AUD-204).** Las dos asignaciones sólo ocurren
mientras se **mantiene** una dirección. `AirborneState` deja `velocity.x`
intacta cuando `move_x == 0`, así que **soltar la dirección después de
despegar conserva los 90 px/s de la carrera** en vez de bajar a los 45 del
control aéreo. Mantener la tecla hacia delante es la opción **más lenta**.

No es una rareza de la especificación: está medido.
`tests/playtest/jump_bench.py` corre el `Player` real sobre huecos sintéticos —
manteniendo la dirección se cruzan **3 baldosas**; soltándola, **5**. Quien
diseña niveles necesita el primer número, no el segundo.

**Bloqueo al agacharse.** En `CROUCHING` la velocidad horizontal se fuerza a 0.

### 4.2 Vertical

La gravedad se aplica siempre. El jugador está apoyado cuando su borde inferior
descansa sobre un rectángulo de colisión.

| Propiedad | Valor | Unidad |
|---|---|---|
| Gravedad | 800,0 | px/s² |
| Impulso de salto | −380,0 | px/s |
| Caída máxima | 500,0 | px/s |
| *Coyote time* | 6 | fotogramas |
| Buffer de salto | 8 | fotogramas |

```
velocity.y += GRAVITY * dt
velocity.y = acotar(velocity.y, -INF, MAX_FALL_SPEED)
position.y += velocity.y * dt
```

**Coyote time.** Se puede saltar hasta 6 fotogramas después de haber dejado el
borde de una plataforma.

**Buffer de salto.** Si se pulsa saltar hasta 8 fotogramas **antes** de
aterrizar, el salto sale al tocar suelo en vez de perderse. Desde AUD-373 la
ventana vive en `InputManager` y sirve para **todas** las acciones, no sólo
para el salto: `pulsada_en_buffer(accion)` y `consumir_buffer(accion)`.

Las dos concesiones juntas son lo que hace que el personaje responda: una
perdona llegar tarde y la otra llegar pronto.

**Corte del salto.** Si se suelta el botón mientras se asciende
(`velocity.y < 0`), la velocidad vertical se multiplica por 0,5 ese fotograma.
Da altura de salto variable.

**Salto aéreo: la constante está, la mecánica no (GAP-024).**
`PLAYER_AIR_JUMPS = 1` existe en `settings.py` y `_can_jump()` tiene una rama
para él, pero **ningún salto en el aire llega a dispararse**: la pulsación se
guarda en el buffer y se gasta al aterrizar, y la rama aérea de `_can_jump()`
sólo se alcanza desde los estados de suelo. El alcance medido no cambia por
pulsar saltar en el aire.

No diseñes niveles contando con doble salto, y no trates
`max_gap_with_air_jump` de `level_metrics.py` como una distancia alcanzable.

### 4.3 Resolución de colisiones

Por **ejes separados**: primero el horizontal, después el vertical.

**Horizontal:** se mueve `position.x`, se busca solape y, si lo hay, se empuja
al borde y se pone `velocity.x = 0`. Los roces de 2 px o menos se ignoran: sin
esa tolerancia, el suelo y el techo bloquearían el avance lateral.

**Vertical:** se mueve `position.y` y, según de dónde se venga:

- **desde arriba** (`velocity.y >= 0` y el borde inferior anterior estaba sobre
  la baldosa): aterriza, `velocity.y = 0`, `is_grounded = True`;
- **desde abajo** (`velocity.y < 0` y el borde superior anterior estaba bajo la
  baldosa): se golpea la cabeza y `velocity.y = 0`.

Desde AUD-396 el aterrizaje admite **restitución**: con un material que la
declare, parte de la velocidad se devuelve en vez de anularse. Con `ROCA` —el
material por defecto de todos los mapas— vale 0 y el comportamiento es el de
siempre.

### 4.4 Plataformas de un sentido

Las que el TMX marca como `Platform` se atraviesan desde abajo y por los lados.
Sólo resuelven colisión cuando el jugador cae y su borde inferior del fotograma
anterior estaba por encima del borde superior de la plataforma.

---

## 5. Salud

### 5.1 Corazones

| Propiedad | Valor |
|---|---|
| Salud máxima | 5,0 corazones |
| Salud inicial | 5,0 corazones |
| Salud mínima | 0,0 |
| Tipo | flotante (admite fracciones) |

### 5.2 Cómo se dibujan

Cada icono del HUD toma uno de cinco aspectos según lo que le quede:

| Estado | Umbral |
|---|---|
| Lleno | ≥ 1,0 |
| Tres cuartos | ≥ 0,75 |
| Medio | ≥ 0,50 |
| Un cuarto | ≥ 0,25 |
| Vacío | 0,0 |

Se dibujan de izquierda a derecha y **se vacía primero el de la derecha**.

### 5.3 Invencibilidad

Tras recibir daño hay un periodo breve en el que no se recibe más.

| Dificultad | Duración |
|---|---|
| Fácil | 2,0 s |
| Normal | **1,5 s** |
| Difícil | 1,0 s |

El sprite parpadea: la opacidad alterna cada 6 fotogramas.

> **Corregido el 2026-08-11 (AUD-432).** Este documento daba «1,5 segundos»
> como constante del motor. Es el valor de **normal**: sale de
> `get_config().invincibility_duration` y el jugador la elige en el menú. Lo
> mismo pasa con el retroceso y con el daño recibido (§6). Calibrar un peligro
> contra 1,5 s es calibrarlo sólo para una de las tres dificultades.

---

## 6. Daño

### 6.1 Los tres niveles

| Nivel | Corazones | De dónde viene |
|---|---|---|
| Ligero | 0,25 | Roce de proyectil, enemigo débil |
| Medio | 0,50 | Contacto normal, proyectil corriente |
| Fuerte | 1,00 | Enemigo fuerte, zona de peligro, golpe de jefe |

Estos valores se **multiplican** por la dificultad: ×0,5 en fácil, ×1,0 en
normal y ×1,5 en difícil.

### 6.2 Cómo se aplica

Cuando la **caja de daño** del jugador (§11) solapa con la **caja de golpe** de
un enemigo o con un rectángulo de peligro:

1. Si `invincibility_timer > 0`, no pasa nada.
2. Si el estado es `DYING`, tampoco.
3. Se resta de `current_health` la cantidad **que llega como argumento** a
   `apply_damage(cantidad, origen)`, multiplicada por la dificultad. El jugador
   **no** guarda un campo con el daño del último golpe (AUD-150).
4. Se acota `current_health` a `[0,0, MAX_HEALTH]`.
5. Se arranca el temporizador de invencibilidad.
6. Se emite `PLAYER_DAMAGED` con la cantidad y el origen.
7. Se pasa al estado `HURT`.
8. Se aplica el retroceso.
9. Si la salud llega a 0, se emite `PLAYER_DIED`.

### 6.3 Retroceso

| Propiedad | Valor en normal |
|---|---|
| Horizontal | 150,0 px/s, alejándose del origen |
| Vertical | −200,0 px/s, hacia arriba |
| Duración | 0,3 s |

Los dos primeros se multiplican por la dificultad: ×0,7 en fácil, ×1,0 en
normal, ×1,3 en difícil.

Mientras dura, **la entrada del jugador se ignora**.

### 6.4 Muerte

Al llegar a 0: se emite `PLAYER_DIED`, se pasa a `DYING`, se reproduce la
animación y, al terminarla, `SceneManager` empuja la escena de fin de partida.

---

## 7. Ataques

### 7.1 Ataque corto (puños)

| Propiedad | Valor |
|---|---|
| Alcance | 20 px por delante |
| Anchura | 12 px |
| Altura | 16 px |
| Daño | 0,50 corazones |
| Fotogramas activos | 3 (los 2–4 de 6) |
| Enfriamiento | 0 — se puede encadenar |
| *Hitstop* | 2 fotogramas |

La caja se posiciona según `facing_direction`. Agachado, baja para acompañar la
postura.

### 7.2 Ataque largo (palo)

| Propiedad | Valor |
|---|---|
| Alcance | 36 px por delante |
| Anchura | 36 px |
| Altura | 20 px |
| Daño | 1,00 corazón |
| Fotogramas activos | 4 (los 4–7 de 10) |
| Enfriamiento | 4 fotogramas |
| *Hitstop* | 4 fotogramas |

El arco barre ligeramente hacia arriba en el fotograma 4, horizontal en el 5 y
el 6, y hacia abajo en el 7. Agachado, el arco es todo bajo: altura 12 px a
ras de suelo.

### 7.3 *Hitstop*

Cuando un ataque conecta:

1. `DeltaClock.time_scale` baja a **0,15** durante el *hitstop*: todo el tiempo
   de juego —física, animaciones, IA— va al 15 %.
2. Dura `fotogramas / 60` segundos: **2** en el corto, **4** en el largo.
3. Después vuelve a 1,0.
4. Se llama a `apply_hit()` del enemigo.
5. **La caja del jugador se consume**: sólo un enemigo por golpe recibe daño.
6. Sólo el primer impacto dispara la ralentización; los demás del mismo
   fotograma reciben daño sin volver a activarla.

El temporizador decrece **al margen de `time_scale`**, para que la
ralentización dure los fotogramas de pantalla previstos y no se ralentice a sí
misma.

---

## 8. Estados

El jugador se gobierna por una máquina de estados finitos: sólo uno activo a la
vez. El enumerado `PlayerState` declara **26**.

> **Corregido el 2026-08-11 (AUD-432).** Este documento decía **19**, dos
> veces, y su tabla listaba diecinueve. Los siete que faltaban —`CLIMBING`,
> `ZIPLINE`, `ULTIMATE`, `AERIAL_ATTACK`, `AERIAL_SLAM`, `AIR_CHASE`,
> `CHARGE_RELEASE`— son mecánicas construidas que ningún estudiante podía saber
> que existían leyendo esto.

### 8.1 La tabla

| Estado | Se entra | Se sale | Entrada aceptada |
|---|---|---|---|
| `IDLE` | Apoyado y sin entrada | Movimiento o ataque | Toda |
| `WALKING` | Apoyado con dirección | Sin dirección, salto o ataque | Toda |
| `JUMPING` | Salto estando apoyado o en *coyote* | Velocidad vertical ≤ 0 | Mover, atacar |
| `FALLING` | Cayendo y sin apoyo | Al tocar suelo | Mover, atacar |
| `CROUCHING` | Abajo estando apoyado | Al soltar abajo | Los dos ataques |
| `SHORT_ATTACK` | Ataque corto | Fin de la animación | Ninguna |
| `LONG_ATTACK` | Ataque largo | Fin de animación y enfriamiento | Ninguna |
| `HURT` | Al recibir daño | Fin del retroceso | Ninguna |
| `DYING` | Salud a 0 | Fin de la animación | Ninguna |
| `DASHING` | Dash | A los 0,15 s | Ninguna |
| `PARRY` | Ataque y agacharse a la vez | A los 0,2 s | Ninguna |
| `CHARGE_ATTACK` | Mantener el ataque largo | Al soltarlo | Parry |
| `CHARGE_RELEASE` | Soltar la carga | Fin de la animación | Ninguna |
| `DASH_ATTACK` | Atacar durante el dash | Fin de la animación | Ninguna |
| `WALL_SLIDE` | Tocar pared cayendo, con dirección hacia ella | Separarse o aterrizar | Saltar, atacar |
| `LEDGE_GRAB` | Llegar al borde deslizando por la pared | Subir o soltarse | Saltar |
| `GRAB` | Ataque largo agachado | Al conectar | Atacar (lanzar) |
| `THROW` | Atacar mientras se agarra | Fin de la animación | Ninguna |
| `SLIDE` | Agacharse con carrera | Fin del temporizador o soltar | Ninguna |
| `SWIMMING` | Entrar en zona de agua | Salir del agua | Mover, saltar |
| `CLIMBING` | Agarrarse a una liana | Soltarse o llegar arriba | Mover, saltar |
| `ZIPLINE` | Engancharse a una tirolesa | Llegar al final o soltarse | Saltar |
| `ULTIMATE` | Medidor lleno y activación | Fin de la animación | Ninguna |
| `AERIAL_ATTACK` | Atacar en el aire | Fin de la animación | Ninguna |
| `AERIAL_SLAM` | Ataque hacia abajo en el aire | Al tocar suelo | Ninguna |
| `AIR_CHASE` | Persecución aérea tras un impacto | Fin del temporizador | Mover |

La implementación está repartida por familias en
`src/framework/entities/states/`: `grounded.py`, `airborne.py`, `attack.py`,
`ability.py`, `damage.py`, `rope.py`, `swim.py` y `wall.py`.

### 8.2 Las transiciones más comunes

```
           [IDLE] ←──── se suelta la dirección ────→ [WALKING]
              │                                          │
         salto │                                         │ salto
              ▼                                          ▼
          [JUMPING] ──── al llegar al pico ────────→ [FALLING]
                                                         │
                                              al aterrizar│
                                                         ▼
                                                      [IDLE]

  [IDLE] [WALKING] [CROUCHING] [JUMPING] [FALLING] ─ dash ─→ [DASHING]
  [DASHING] ─ fin del temporizador ─→ [IDLE] si hay suelo, [FALLING] si no

  cualquier estado salvo DYING ─ daño ─→ [HURT] ─ fin del retroceso ─→ [IDLE]
  cualquier estado ─ salud 0 ─→ [DYING] ─ fin de animación ─→ (PLAYER_DIED)
```

---

## 9. Animaciones

Hojas horizontales en `assets/sprites/player/`.

| Animación | Fichero | Fotogramas | FPS | Bucle |
|---|---|---|---|---|
| Reposo | `player_idle.png` | 4 | 8 | Sí |
| Andar | `player_walk.png` | 8 | 12 | Sí |
| Salto | `player_jump.png` | 3 | 12 | No |
| Caída | `player_fall.png` | 2 | 8 | Sí |
| Agachado | `player_crouch.png` | 2 | 8 | No |
| Ataque corto | `player_short_attack.png` | 6 | 18 | No |
| Ataque largo | `player_long_attack.png` | 10 | 16 | No |
| Daño | `player_hurt.png` | 4 | 12 | No |
| Dash | `player_walk.png` | 4 | 12 | No |
| Muerte | `player_die.png` | 8 | 10 | No |

**Reglas:**

- Al entrar en una animación sin bucle, el contador vuelve a 0.
- Al llegar al último fotograma de una sin bucle, se mantiene hasta salir.
- Todas se voltean según `facing_direction`; las hojas miran a la derecha.
- Durante la invencibilidad, la opacidad alterna cada 6 fotogramas.
- Fotograma de 32×32 px. Las cajas son más pequeñas (§10 y §11).

---

## 10. Cajas de golpe

Son las zonas con las que el jugador hace daño. **Sólo están activas** durante
los fotogramas activos de la animación.

### 10.1 Ataque corto

| Propiedad | Valor |
|---|---|
| Desplazamiento X | 8 px hacia donde mira, desde el centro |
| Desplazamiento Y | −4 px |
| Anchura | 20 px |
| Altura | 16 px |
| Fotogramas activos | 2, 3 y 4 de 6 |

Agachado, el desplazamiento Y pasa a +8 px.

### 10.2 Ataque largo

La caja se mueve entre fotogramas para simular el arco:

| Fotograma | Desp. X | Desp. Y | Anchura | Altura |
|---|---|---|---|---|
| 4 | 12 px | −10 px | 36 px | 20 px |
| 5 | 18 px | −4 px | 36 px | 20 px |
| 6 | 18 px | 0 px | 36 px | 20 px |
| 7 | 12 px | +6 px | 36 px | 20 px |

Agachado: todos los desplazamientos Y suben 12 px y la altura baja a 12 px.

---

## 11. Caja de daño

Es la zona por la que el jugador **recibe**. Siempre activa, salvo durante la
invencibilidad y en `DYING`.

### 11.1 De pie

| Propiedad | Valor |
|---|---|
| Desplazamiento X | 6 px desde el borde izquierdo del sprite |
| Desplazamiento Y | 4 px desde el borde superior |
| Anchura | 20 px |
| Altura | 28 px |

Es **más pequeña que el sprite** a propósito: permite los roces visuales que
dan la sensación de la época.

### 11.2 Agachado

| Propiedad | Valor |
|---|---|
| Desplazamiento X | 6 px |
| Desplazamiento Y | 14 px |
| Anchura | 20 px |
| Altura | 18 px |

Agacharse deja pasar por encima los proyectiles altos.

### 11.3 Durante los ataques

Dimensiones normales. **No** hay vulnerabilidad extra al atacar, a diferencia
de otros juegos de acción.

---

## 12. Restricciones

| Restricción | Motivo |
|---|---|
| Los estudiantes no heredan de `Player` | Es un recurso compartido del framework |
| No se toca `_health` directamente | Usa `apply_damage()` y la propiedad `current_health` |
| No se puentea la máquina de estados | No asignes `player._state` desde el escenario |
| No se sustituyen los sprites del jugador | Coherencia visual entre escenarios |
| No se reconfigura el `InputManager` desde el escenario | La entrada es un sistema global |
| No se reposiciona `rect` a mano | Usa `player.set_spawn(posicion)` |

---

## 13. Ejemplos

### 13.1 Crear al jugador

```python
from src.framework.entities.player import Player

# En Stage.on_enter():
player = Player(spawn_position=stage_data.spawn_point)
self.entities.append(player)
self.camera.follow(player)
self.hud.bind_player(player)
```

### 13.2 Consultar la salud

```python
# Bien: por la propiedad
if player.current_health <= 1.0:
    self.event_bus.emit("SHOW_MESSAGE", text="¡Cuidado: poca vida!", duration=3.0)
```

### 13.3 Escuchar los eventos del jugador

```python
from src.engine.core.event_bus import EventBus

class MiDisparador(BaseEntity):
    def __init__(self, bus: EventBus):
        super().__init__()
        self._bus = bus
        bus.subscribe("PLAYER_DAMAGED", self._al_recibir_dano)

    def _al_recibir_dano(self, amount, source):
        if amount >= 1.0:
            self.activar_efecto_de_dano_fuerte()

    def on_destroy(self):
        self._bus.unsubscribe("PLAYER_DAMAGED", self._al_recibir_dano)
```

El bus se **recibe**, no se toma de un global: es lo que permite probar la
entidad sola, y lo que evita que una prueba emita en un bus y escuche en otro
(AUD-019).

### 13.4 Concepto académico — transformación de la caja (Unidad II)

Las cajas se definen en espacio **local** (relativo al origen del sprite) y se
transforman a espacio de mundo cada fotograma con una traslación:

```
origen_mundo = player.position + desplazamiento_local
```

En forma matricial, con coordenadas homogéneas 2D:

```
[1  0  tx] [local_x]   [mundo_x]
[0  1  ty] [local_y] = [mundo_y]
[0  0   1] [   1   ]   [   1   ]
```

Donde `tx, ty` son `player.position`. Se espera que reconozcas este patrón y lo
documentes en el README de tu escenario al implementar las cajas de tus
entidades.

---

## 🔗 Documentos relacionados

- [[45_SWIMMING_SPEC.md|Especificación del nado]]
- [[09_HUD_SPEC.md|Especificación del HUD]]
- [[03_ARCHITECTURE.md|Arquitectura]]
- [[06_TMX_SPEC.md|Especificación TMX]]

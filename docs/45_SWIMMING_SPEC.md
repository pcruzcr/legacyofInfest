---
document_id: "LOI-SWIMMING-045"
title: "Legacy of InFest — Especificación de la mecánica de natación"
aliases: ["Especificación de natación", "Swimming Spec"]
tags: ["natacion", "mecanica", "jugador"]
description: "Mecánica de natación"
source: "docs/45_SWIMMING_SPEC.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación de la mecánica de natación

**ID del documento:** LOI-SWIMMING-045
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento completo (antes en inglés). Verificado
> contra `src/framework/entities/states/swim.py`: el modificador de
> gravedad (×0.3), el periodo de burbujas (0.3s) y el máximo de un salto en
> el agua coinciden exactamente con el código.

> **AUD-528 (2026-08-18) — nado omnidireccional real.** El modelo de §2 de
> más abajo describía gravedad constante (×0.3) más **un único** impulso de
> salto que se recargaba sólo al tocar fondo (AUD-526). Jugado sin soltar
> ninguna tecla: el jugador se hundía sin parar y se quedaba posado en el
> lecho — indistinguible de caminar, reportado como "camina sobre el
> agua". Pedido explícito del dueño: nado libre en las cuatro direcciones,
> salto como impulso **continuo** (mantener la tecla empuja mientras se
> mantiene), estilo Super Mario Bros. El eje vertical ahora se mueve con
> el mismo lenguaje que ya usaba el horizontal — aceleración mientras se
> mantiene la tecla, freno suave al soltarla — con un peso residual muy
> por debajo de la gravedad real para que flotar en el sitio siga sin ser
> gratis. La tabla de §2 queda reescrita para reflejarlo.

---

## 1. Visión general

Nadar es un estado del jugador (`SwimmingState` en `src/framework/entities/states/swim.py`) que se activa cuando el jugador entra en zonas de agua. Da flotabilidad y movimiento omnidireccional continuo — mantener salto (o arriba) empuja hacia la superficie, mantener agachar empuja hacia el fondo, y soltar cualquiera de las dos frena suavemente en vez de dejar caer en picado. Se emiten burbujas mientras se nada, como retroalimentación visual.

---

## 2. Física

| Propiedad | Valor |
|----------|-------|
| Empuje vertical (salto o arriba mantenidos) | 90 px/s² hacia arriba |
| Empuje vertical (agachar mantenido) | 90 px/s² hacia abajo |
| Velocidad vertical máxima con empuje | ±100 px/s |
| Freno al soltar el eje vertical | multiplicador ×0.88/fotograma |
| Peso residual sin tecla vertical | ×0.05 de la gravedad real |
| Velocidad vertical máxima sin empuje | −100 px/s (subir), +60 px/s (hundirse) |
| Aceleración horizontal | 60 px/s² |
| Velocidad horizontal máxima | ±120 px/s |
| Desaceleración horizontal | multiplicador ×0.9/fotograma |
| Velocidad de expulsión a la superficie | −200 px/s |
| Periodo de emisión de burbujas | 0.3 s |

---

## 3. Transiciones de estado

- **Entrada:** `ControlDeNado` (`src/framework/stage/level_mechanics.py`, corre cada fotograma desde `StageScene.update()`) comprueba `en_agua(mundo, jugador.rect)`; si el jugador se solapa con una `ZonaDeAgua` y no estaba ya nadando, el estado pasa a `SWIMMING`. La velocidad vertical se pone a cero al entrar; la horizontal se reduce a la mitad. **Mientras siga dentro del agua, la autoridad es continua (AUD-573):** si la máquina de tierra llega a pisar el estado (`IDLE`/`WALKING`/`JUMPING`...) con el jugador aún sumergido, `ControlDeNado` lo devuelve a `SWIMMING` ese mismo fotograma — los estados de `_ESTADOS_SUBMARINOS` se respetan.
- **Salida:** `ControlDeNado` es la única autoridad para salir del agua — cuando `en_agua()` deja de encontrar una `ZonaDeAgua` (la salida real, no un umbral aproximado), decide a qué estado pasa:
  - **Expulsión en superficie:** si el jugador subía (`velocity.y < 0`) al salir, se le expulsa hacia arriba a −200 px/s hacia `JUMPING` — el «pop» de romper la superficie nadando.
  - **Caída normal:** si no, pasa a `FALLING` sin más.
- **Aterrizaje:** tocar el suelo pasa a `IDLE`. (Dentro del agua esto ya no ocurre: el aterrizaje en un lecho sumergido queda absorbido por la autoridad continua de la entrada — se sigue nadando, AUD-573.)

> **AUD-572 (2026-08-19).** Hasta esta fecha, la salida por arriba la decidía
> `SwimmingState` con su propio criterio: una `_surface_y` fija al **entrar**
> (`player.y − 16`), y expulsión en cuanto el jugador subía 24px por encima de
> *esa* referencia — sin comprobar si de verdad había salido de la
> `ZonaDeAgua`. Funcionaba en una piscina pequeña con superficie real
> (`stage_mecanicas`), pero en un nivel "sumergido de principio a fin" sin
> ningún punto real de salida (4-1b, `docs/niveles/13b_STAGE_4_1B.md`), nadar
> hacia arriba un poco disparaba la expulsión en pleno abismo una y otra vez
> — jugado, se reportó como *«sigue saltando, no se siente como un nivel de
> nada»*. El criterio se movió a `ControlDeNado._salir`, que ya tenía la
> detección real de salida (`en_agua()`) y sólo le faltaba decidir *cómo*
> salir.

> **AUD-573 (2026-08-19) — la autoridad del agua es continua, y el agua no
> tiene gravedad de tierra.** Tres defectos que hacían que el nado se
> sintiera roto en 4-1b (reporte: «el personaje no nada», reproducido en
> simulación): (1) el salto con buffer de `Player.update` se disparaba para
> cualquier estado con `is_grounded` — posado en el lecho sumergido,
> pulsar salto daba un salto de tierra firme en pleno abismo; el buffer
> ahora excluye `SWIMMING` y `SWIM_ATTACK`. (2) `ControlDeNado` sólo
> actuaba en el flanco de entrada: si la máquina de tierra ponía
> `IDLE`/`WALKING` con el jugador ya sumergido, nadie lo devolvía a nadar;
> ahora **refuerza** `SwimmingState` cada fotograma mientras `en_agua()`
> devuelva zona (respetando `_ESTADOS_SUBMARINOS`: `SWIMMING`,
> `SWIM_ATTACK`, `HURT`, `DYING`, `CLIMBING`, `ZIPLINE`, `GRAB`, `THROW`).
> (3) `_apply_physics` sumaba la **gravedad completa del perfil** al eje Y
> que el nado ya gestiona (incluido su peso residual de ×0.05): sin teclas,
> el jugador se hundía a ~113 px/s en vez de flotar, y el empuje no podía
> despegar del lecho contra la colisión; el integrador ahora deja el eje Y
> a los estados acuáticos. Medido tras el arreglo: sin input, la velocidad
> vertical converge a ~5.6 px/s (flotar); con salto mantenido, el jugador
> despega del lecho y nada hacia la superficie en `SWIMMING` de principio
> a fin. Ver `tests/test_mecanicas_f5.py` (TestNado) y
> `tests/test_stage4_1b.py::TestElJugadorNadaNoCaminaPorElLecho`.

> **AUD-575 (2026-08-19) — superficie real y oxígeno activo.** El 4-1b
> rediseñado (`docs/niveles/13b_STAGE_4_1B.md` §2) ya no es "sumergido de
> principio a fin": su `WaterZone` arranca en la fila 11 de 38, con once
> filas de aire con estalactitas por encima. La salida por arriba (§3) dejó
> de ser teoría: emerger es de verdad salir de la `ZonaDeAgua`. Con
> superficie, el ahogamiento vuelve a ser el contrapeso del buceo (GAP-071
> resuelto, ver §4.1): el nivel reactiva `dano_por_segundo=1.0` en su
> `__init__` y la lectura del aire es `ControlDeNado.en_agua` (property que
> expone `_estaba_dentro`, la misma fuente que decide las transiciones — no
> una segunda opinión que pueda desincronizarse).

---

## 4. Partículas de burbujas

Un temporizador de burbujas genera partículas visuales de burbuja a intervalos regulares mientras se nada. Implementado en línea en `SwimmingState.update()`: cada 0.3 s el estado emite `Events.VFX_BUBBLE` en la posición del jugador; `StageScene` se suscribe y genera `HitEffects.BUBBLE` desde el emisor `"bubble"`.

---

## 4.1 Oxígeno y ahogamiento (GAP-071 resuelto, AUD-575)

`ControlDeNado` lleva el reloj de aire de cada inmersión. El módulo siempre
lo declaró (`docstring` de `level_mechanics.py`); GAP-071 era que **nadie
mostraba el aviso** y el jugador se ahogaba sin haber podido saberlo.

| Propiedad | Valor |
|----------|-------|
| `aire_maximo` | 30 s de inmersión continua |
| `dano_por_segundo` | 1.0 — **configurable por nivel**: `Stage4_1B.__init__` lo reactiva; el resto del juego hereda el 0.0 de fábrica (AUD-572) |
| `umbral_aviso` | 10 s — `avisando` es `True` mientras `0 < aire <= 10` |
| Recuperación fuera del agua | 8×/s (`ControlDeNado._recuperar_aire`, sólo si `en_agua` es `False`) |
| `en_agua` | property → `_estaba_dentro`, la decisión de cada fotograma (AUD-575) |
| Consumidor del aviso | `src/engine/ui/hud.py` — `set_oxigeno(ratio, avisando)` dibuja la barra de oxígeno bajo la estamina (sólo mientras `ratio >= 0`, es decir, sumergido) y parpadea + pulsa `Events.SFX_TIMER_ALERT_PULSE` en el tramo bajo (AUD-553, mismo lenguaje que el cronómetro). La escena la alimenta en `_update_hud_ui` (`actualizaciones.py`). Ver `tests/test_oxigeno_del_hud.py` |

El oxígeno es **por inmersión, no por nivel**: cada vez que se sale del
agua el aire vuelve a 30 s. Bucear toda la mina de una tirada es la
decisión de riesgo; emerger a respirar en las galerías altas y los andenes
secos, la decisión segura — la alternancia de agua y áreas secas del
rediseño (AUD-575) existe para que la segunda sea posible.

---

## 5. Estado de implementación

**Fichero:** `src/framework/entities/states/swim.py` (el estado) y
`src/framework/stage/level_mechanics.py` (`ControlDeNado`, quien decide
cuándo entrar y salir — ver AUD-572 arriba)
**Clase:** `SwimmingState(PlayerStateBase)` con `PlayerState.SWIMMING`
**Estado:** ✅ Completo — física de natación, flotabilidad, temporizador de
burbujas, expulsión en superficie por geometría real (AUD-572), detección de
zona de agua dedicada (`en_agua()`, `ControlDeNado`), oxígeno y ahogamiento
con aviso de HUD (AUD-575, GAP-071 resuelto)

---
## 🔗 Documentos relacionados

- [[04_PLAYER_SPEC.md|Especificación del jugador]]
- [[47_WATER_EFFECT.md|Especificación del efecto de agua]]

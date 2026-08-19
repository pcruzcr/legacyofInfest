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

- **Entrada:** `ControlDeNado` (`src/framework/stage/level_mechanics.py`, corre cada fotograma desde `StageScene.update()`) comprueba `en_agua(mundo, jugador.rect)`; si el jugador se solapa con una `ZonaDeAgua` y no estaba ya nadando, el estado pasa a `SWIMMING`. La velocidad vertical se pone a cero al entrar; la horizontal se reduce a la mitad.
- **Salida:** `ControlDeNado` es la única autoridad para salir del agua — cuando `en_agua()` deja de encontrar una `ZonaDeAgua` (la salida real, no un umbral aproximado), decide a qué estado pasa:
  - **Expulsión en superficie:** si el jugador subía (`velocity.y < 0`) al salir, se le expulsa hacia arriba a −200 px/s hacia `JUMPING` — el «pop» de romper la superficie nadando.
  - **Caída normal:** si no, pasa a `FALLING` sin más.
- **Aterrizaje:** tocar el suelo pasa a `IDLE`.

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

---

## 4. Partículas de burbujas

Un temporizador de burbujas genera partículas visuales de burbuja a intervalos regulares mientras se nada. Implementado en línea en `SwimmingState.update()`: cada 0.3 s el estado emite `Events.VFX_BUBBLE` en la posición del jugador; `StageScene` se suscribe y genera `HitEffects.BUBBLE` desde el emisor `"bubble"`.

---

## 5. Estado de implementación

**Fichero:** `src/framework/entities/states/swim.py` (el estado) y
`src/framework/stage/level_mechanics.py` (`ControlDeNado`, quien decide
cuándo entrar y salir — ver AUD-572 arriba)
**Clase:** `SwimmingState(PlayerStateBase)` con `PlayerState.SWIMMING`
**Estado:** ✅ Completo — física de natación, flotabilidad, temporizador de
burbujas, expulsión en superficie por geometría real (AUD-572), detección de
zona de agua dedicada (`en_agua()`, `ControlDeNado`)

---
## 🔗 Documentos relacionados

- [[04_PLAYER_SPEC.md|Especificación del jugador]]
- [[47_WATER_EFFECT.md|Especificación del efecto de agua]]

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

- **Entrada:** el jugador se solapa con una zona de agua → el estado pasa a `SWIMMING`. La velocidad vertical se pone a cero al entrar; la horizontal se reduce a la mitad.
- **Salida:** el jugador sale de la zona de agua → transición al estado de suelo/aire correspondiente.
- **Y de superficie:** se registra al entrar (`player.y − 16`), se usa para los efectos visuales de superficie.
- **Expulsión en superficie:** si el jugador sube por encima de `surface_y − 8` px, se le expulsa hacia arriba a −200 px/s hacia `JUMPING`.
- **Aterrizaje:** tocar el suelo pasa a `IDLE`.

---

## 4. Partículas de burbujas

Un temporizador de burbujas genera partículas visuales de burbuja a intervalos regulares mientras se nada. Implementado en línea en `SwimmingState.update()`: cada 0.3 s el estado emite `Events.VFX_BUBBLE` en la posición del jugador; `StageScene` se suscribe y genera `HitEffects.BUBBLE` desde el emisor `"bubble"`.

---

## 5. Estado de implementación

**Fichero:** `src/framework/entities/states/swim.py`
**Clase:** `SwimmingState(PlayerStateBase)` con `PlayerState.SWIMMING`
**Estado:** ✅ Completo — física de natación, flotabilidad, temporizador de burbujas, expulsión en superficie
**Falta:** sin detección dedicada de zona de agua; depende del sistema de colisión del escenario para disparar el cambio de estado

---
## 🔗 Documentos relacionados

- [[04_PLAYER_SPEC.md|Especificación del jugador]]
- [[47_WATER_EFFECT.md|Especificación del efecto de agua]]

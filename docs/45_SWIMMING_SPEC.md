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

---

## 1. Visión general

Nadar es un estado del jugador (`SwimmingState` en `src/framework/entities/states/swim.py`) que se activa cuando el jugador entra en zonas de agua. Da flotabilidad, gravedad reducida, movimiento horizontal más lento y la mecánica de salto nadando. Se emiten burbujas mientras se nada, como retroalimentación visual.

---

## 2. Física

| Propiedad | Valor |
|----------|-------|
| Modificador de gravedad | ×0.3 de lo normal |
| Velocidad vertical máxima | −60 px/s (subir), +120 px/s (hundirse) |
| Aceleración horizontal | 60 px/s² |
| Velocidad horizontal máxima | ±120 px/s |
| Desaceleración horizontal | multiplicador ×0.9/fotograma |
| Velocidad de salto nadando | −120 px/s |
| Saltos nadando máximos | 1 |
| Buceo agachado | +200 px/s² |
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

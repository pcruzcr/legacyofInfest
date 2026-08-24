---
document_id: "LOI-BOSSRUSH-044"
title: "Legacy of InFest — Especificación del modo Boss Rush"
aliases: ["Especificación del modo Boss Rush", "Boss Rush Mode"]
tags: ["boss", "rush", "modo", "juego"]
description: "Modo de jefes consecutivos"
source: "docs/44_BOSS_RUSH_MODE.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación del modo Boss Rush

**ID del documento:** LOI-BOSSRUSH-044
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento (el cuerpo técnico ya estaba en español
> y bien mantenido, con historial honesto de AUD-232/261; sólo §1–§3 y el
> resumen final seguían en inglés).

---

## 1. Visión general

El modo Boss Rush (`src/framework/stage/boss_rush_mode.py`) es el diseño de una sucesión de jefes consecutivos con arrastre de vida y puntuación.

**Lo que hay hoy (AUD-261), medido:** elegir BOSS RUSH desde la pantalla de título encadena los cuatro jefes uno tras otro, la vida se arrastra entre combates con una curación parcial declarada (`CURACION_ENTRE_COMBATES`), se cuentan los golpes recibidos, y la puntuación se calcula por combate a partir del tiempo y el daño recibido — ver §4.

**Historia, conservada a propósito.** Entre AUD-232 y AUD-261 este párrafo decía: «Eso es todo lo que hay. La vida *no* persiste entre combates, no se calcula puntuación y no se cuentan los golpes.» Antes de AUD-232 decía «✅ Completo — lógica de la sucesión, puntuación, arrastre de vida», y las tres versiones eran falsas. La del medio era la honesta, y fue la que hizo posible el arreglo: nombraba lo que faltaba en vez de afirmar que ya estaba.

---

## 2. Arquitectura

### 2.1 `BossRushStage`
Representa un combate de jefe:
- `boss_id`, `boss_name` — identificación
- `scene_builder` — función que crea la escena del jefe
- `phase_count` — complejidad de fases del jefe
- `defeated`, `time`, `hits_taken` — estado en tiempo de ejecución

### 2.2 `BossRushMode`
- `add_stage(stage)` — añade a la sucesión
- `start()` — reinicia todos los combates, activa el modo
- `get_current_stage()` — el combate actual
- `advance_to_next()` — marca el actual como derrotado, aplica la puntuación, pasa al siguiente
- `record_hit()` — seguimiento de penalización
- `is_complete()` — todos los jefes derrotados

---

## 3. Puntuación

Por jefe: `max(0, 1000 − int(tiempo * 10)) − golpes_recibidos * 50`
- Terminar más rápido = puntuación más alta
- Cada golpe recibido resta 50 puntos

---

## 4. Implementation Status

**File:** `src/framework/stage/boss_rush_mode.py`

**Status (AUD-232, medido):** ⚠️ **Parcial.** La lógica del módulo está escrita y
probada en aislamiento, pero el juego no la conduce.

| Pieza | Estado real | Por qué |
|---|---|---|
| Entrada desde el menú | ✅ | AUD-191 la añadió; AUD-201 arregló que dejara la pantalla en negro |
| Los cuatro jefes seguidos | ✅ | lo encadena la cola de escenarios del `SceneManager` |
| Arrastre de vida y de medidor | ✅ | AUD-261. `salud_arrastrada` y `medidor_arrastrado` son API pública; `StageScene` los escribe al caer el jefe y los aplica al entrar en el siguiente |
| Curación entre combates | ✅ | `CURACION_ENTRE_COMBATES`, una constante con nombre. El arrastre puro deja al jugador sin vida en el tercer jefe, y nadie ha jugado esto lo bastante para calibrar otra cosa |
| Puntuación | ✅ | AUD-261. `acreditar_combate()` la aplica: premia ir rápido y castiga cada golpe recibido |
| Recuento de golpes | ✅ | AUD-261. `record_hit()` la llama el manejador de `PLAYER_DAMAGED`, sólo con el modo activo |
| Superposición de interfaz | ❌ | rótulos de jefe, marcador en pantalla, pantallas intermedias. Es lo único que queda |

`context.boss_rush` lo **lee** `StageScene`, que es la única que sabe cuándo
empieza un combate, cuándo el jugador recibe un golpe y cuándo cae el jefe.

**GAP-030 queda cerrado.** La tabla anterior marcaba en ❌ las tres filas que la
versión de antes daba por «✅ Complete», y `tests/test_modos_que_no_se_veian.py`
estaba escrito para **fallar el día que alguien las conectara**. Falló, y por
eso esta tabla está actualizada: la prueba hizo imposible cerrar el hueco sin
tocar el documento.


---
## 🔗 Documentos relacionados

- [[43_SPEEDRUN_MODE.md|Modo speedrun]]
- [[17_BOSS_SPEC.md|Catálogo de jefes]]

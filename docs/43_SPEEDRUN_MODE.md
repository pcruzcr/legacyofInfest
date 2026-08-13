---
document_id: "LOI-SPEEDRUN-043"
title: "Legacy of InFest — Especificación del modo speedrun"
aliases: ["Especificación del modo speedrun", "Speedrun Mode"]
tags: ["speedrun", "modo", "juego"]
description: "Temporizador de speedrun + datos fantasma"
source: "docs/43_SPEEDRUN_MODE.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación del modo speedrun

**ID del documento:** LOI-SPEEDRUN-043
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento y corrige el conteo de líneas: decía
> 118 en `speedrun_mode.py`; hoy tiene 399, con métodos que no estaban
> documentados (`get_splits()`, las propiedades `global_time`/`running`, y
> en `GhostData` el muestreo interpolado `posicion_en(segundos)` y
> `grabar_si_toca` en vez de un `record` que graba cada fotograma sin más).

---

## 1. Visión general

El modo speedrun (`src/framework/stage/speedrun_mode.py`) da un temporizador global con parciales por escenario y grabación de datos fantasma. La clase central es `SpeedrunTimer` (no `SpeedrunMode`). Una clase compañera, `GhostData`, graba fotogramas de posición del jugador para la repetición fantasma.

---

## 2. Arquitectura

### 2.1 `SpeedrunTimer`
- `start()` — reinicia el temporizador y los parciales
- `stop()` / `reset()` — pausa o reinicio completo
- `update(dt)` — acumula tiempo mientras corre
- `start_stage(stage_id)` — señala la entrada a un escenario
- `split(stage_id)` — registra un tiempo parcial
- `get_formatted_time(t=None)` — cadena en formato `M:SS` (o `t` si se pasa uno)
- `get_splits()` — lista de los parciales registrados
- `global_time` (propiedad) — tiempo total acumulado
- `running` (propiedad) — si el temporizador está corriendo
- `save(path)` / `load(path)` — persistencia JSON

### 2.2 `GhostData`
- `grabar_si_toca(dt, x, y, state)` — graba un fotograma sólo cuando corresponde según la cadencia de muestreo, no en cada llamada
- `posicion_en(segundos)` — interpola la posición grabada en un instante dado, para reproducir el fantasma independientemente del framerate de la partida original
- `record(x, y, state)` / `get_frame(index)` — grabación y lectura fotograma a fotograma, de más bajo nivel
- `duracion` (propiedad), `frame_count` (propiedad)
- `clear()` / `save(path)` / `load(path)` — gestión del ciclo de vida

---

## 3. Persistencia

Los parciales del temporizador y los datos fantasma se guardan en `saves/speedrun.json` como arreglos JSON. Formato:
```json
{
  "global_time": 123.45,
  "splits": [{"stage_id": "stage0", "time": 45.2}, ...]
}
```

---

## 4. Estado de implementación

**Fichero:** `src/framework/stage/speedrun_mode.py` (399 líneas)
**Nombre de la clase:** `SpeedrunTimer`
**Estado:** ✅ Completo — temporizador con parciales, grabación y reproducción de datos fantasma con muestreo interpolado, guardado/carga en JSON

---
## 🔗 Documentos relacionados

- [[44_BOSS_RUSH_MODE.md|Modo Boss Rush]]
- [[09_HUD_SPEC.md|Especificación del HUD]]

---
document_id: "LOI-CUTSCENE-042"
title: "Legacy of InFest — Especificación del sistema de escenas cinemáticas"
aliases: ["Especificación de cinemáticas", "Cutscene System"]
tags: ["cinematica", "sistema", "guion"]
description: "Sistema de escenas cinemáticas guionizadas"
source: "docs/42_CUTSCENE_SYSTEM.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación del sistema de escenas cinemáticas

**ID del documento:** LOI-CUTSCENE-042
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento y lo actualiza a fondo: decía que
> `cutscene_system.py` tenía 178 líneas y 5 tipos de acción; hoy tiene 562
> líneas y **11 tipos de acción** concretos. Le faltaban por completo dos
> módulos hermanos que existen y no son opcionales:
> `cutscene_director.py` (191 líneas) — escenas declaradas directamente en el
> TMX (AUD-136) — y `cutscene_guion.py` (242 líneas) — un mini-lenguaje de
> texto plano, una orden por línea, que se traduce a la lista de acciones.

---

## 1. Visión general

Hay tres piezas, no una:

| Módulo | Qué hace |
|---|---|
| `src/framework/stage/cutscene_system.py` | Las acciones y `CutsceneScript`: reproducción secuencial, una acción a la vez |
| `src/framework/stage/cutscene_director.py` | `CutsceneDirector` — conecta escenas cinemáticas declaradas como propiedades de un objeto `Cutscene` en el TMX con el sistema de arriba |
| `src/framework/stage/cutscene_guion.py` | `analizar_guion` — convierte un guion en texto plano (una orden por línea) en la lista de acciones que ejecuta `CutsceneScript` |

Las acciones se ejecutan en orden; cada una informa cuándo termina antes de que empiece la siguiente. Las cinemáticas son del profesorado — los estudiantes las disparan vía la API de guion, pero no modifican el sistema.

---

## 2. Tipos de acción (`cutscene_system.py`)

### 2.1 `CutsceneAction` (base)
Interfaz abstracta: `start()`, `update(dt) → bool`, `draw(surface)`.

### 2.2 `WaitAction`
Pausa una duración fija en segundos. Sirve para temporizar entre acciones.

### 2.3 `FadeAction`
Funde la pantalla a/desde negro durante una duración. Usa una capa de alfa por píxel.

### 2.4 `CameraMoveAction`
Interpola el desplazamiento de cámara hacia un `(x, y)` objetivo durante una duración. Interpolación lineal.

### 2.5 `DialogueAction`
Muestra una caja de texto con nombre de quien habla opcional, espera ENTER/ESPACIO o a que expire la duración. Caja anclada abajo, 60px de alto, 20px de margen.

### 2.6 `MoverEntidadAction`
Mueve una entidad del escenario a una posición objetivo durante una duración.

### 2.7 `EventoAction`
Emite un evento del EventBus con nombre y datos configurables.

### 2.8 `SonidoAction`
Reproduce un efecto de sonido con nombre.

### 2.9 `TemblorAction`
Sacude la cámara — amplitud y duración configurables.

### 2.10 `EsperarEventoAction`
Bloquea hasta que se emite un evento concreto, con un tope de 10 segundos para no colgar la cinemática si el evento nunca llega.

### 2.11 `DialogoArbolAction`
Muestra un árbol de diálogo completo (ver `40_DIALOGUE_SYSTEM.md`) dentro de la cinemática — con retrato animado, lip-sync y voice si el nodo los declara.

### 2.12 `AccionParalela`
Ejecuta varias acciones a la vez en vez de en secuencia — por ejemplo, mover una entidad mientras suena un efecto.

---

## 3. `CutsceneScript`

Una lista secuencial de objetos `CutsceneAction`:
- `add_action(action)` — añade al guion
- `start(callback)` — empieza la ejecución con una función de fin opcional
- `update(dt)` — avanza la acción actual; pasa a la siguiente al terminar
- `draw(surface)` — dibuja todas las acciones activas desde el índice actual en adelante

---

## 4. El mini-lenguaje de guion (`cutscene_guion.py`)

Una orden por línea, con `#` para comentarios, `+` al principio para marcar una acción como paralela con la anterior, y `.` para dejar una coordenada sin especificar (usa la actual). Palabras clave: `esperar`, `camara`, `mover`, `dialogo`, `evento`, `sonido`, `temblor`, `fundido`, `esperar_evento`. `analizar_guion(texto)` traduce ese texto a la lista de `CutsceneAction` que ejecuta `CutsceneScript`.

---

## 5. `CutsceneDirector` (`cutscene_director.py`, AUD-136)

Conecta objetos `Cutscene` del TMX con el sistema de arriba, sin que el escenario tenga que escribir Python para cada cinemática:

- `reproduzir_texto(guion)` — analiza y reproduce un guion directamente
- `bloquea()` — si la cinemática actual congela al jugador
- `update(dt, jugador_rect, saltar)` — avanza la cinemática activa
- `saltar()` — ejecuta las acciones finales de golpe (no las cancela)
- `draw`, `reset()`

---

## 6. Flujo de ejecución

```
start() → action[0].start()
  ↓
bucle update():
  → action[N].update(dt)
  → si termina: action[N+1].start()
  → si no quedan más acciones: se llama a callback(), active=false
```

---

## 7. Estado de implementación

**Ficheros:** `cutscene_system.py` (562 líneas), `cutscene_director.py` (191 líneas), `cutscene_guion.py` (242 líneas)
**Estado:** ✅ Completo — 11 tipos de acción, mini-lenguaje de guion, cinemáticas declaradas en TMX, reproducción secuencial y paralela, callback al terminar

---
## 🔗 Documentos relacionados

- [[40_DIALOGUE_SYSTEM.md|Sistema de diálogo]]
- [[48_SCREEN_TRANSITIONS.md|Transiciones de pantalla]]

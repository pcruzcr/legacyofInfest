---
document_id: "LOI-DIALOGUE-040"
title: "Legacy of InFest — Especificación del sistema de diálogo"
aliases: ["Especificación del sistema de diálogo", "Dialogue System"]
tags: ["dialogo", "sistema", "ui"]
description: "Diálogo ramificado con retratos"
source: "docs/40_DIALOGUE_SYSTEM.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación del sistema de diálogo

**ID del documento:** LOI-DIALOGUE-040
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento y corrige el estado de implementación:
> decía que `dialogue_system.py` tenía 175 líneas y ningún renderizador
> dedicado; hoy tiene 546 líneas, con paginación real de texto
> (`paginas()`, `pagina_actual()`) y carga de árboles desde datos JSON
> (`DialogueTree.desde_datos()`, ficheros en `data/dialogues/<stage_id>.json`,
> AUD-244) — ninguna de las dos cosas existía cuando se escribió la versión
> anterior de este documento.

---

## 1. Visión general

El sistema de diálogo da árboles de diálogo ramificados con retratos de quien habla, etiquetas de nombre y avance por elecciones. Soporta varios PNJ, acciones guionizadas (dar objetos, fijar variables) y es del profesorado (`src/framework/ui/dialogue_system.py`). Los estudiantes no modifican el sistema de diálogo, pero pueden disparar árboles de diálogo a través del EventBus.

---

## 2. Arquitectura

### 2.1 `DialogueNode`
Cada nodo contiene:
- `node_id` — identificador único
- `speaker` — nombre a mostrar
- `text` — texto del diálogo (se revela carácter a carácter)
- `portrait` — nombre de fichero de retrato de `assets/sprites/portraits/` (48×48 por frame; tira horizontal N×48 si `portrait_frames>1`)
- `portrait_frames` — 1 (estático, defecto) o N (tira N frames: 0 idle boca cerrada, 1-2 habla, N-1 parpadeo). Ej. `4` + `portrait_fps:8`
- `portrait_fps` — velocidad de la tira (8 por defecto)
- `portrait_talking` — `null` (auto = anima mientras escribe), `true`/`false` fuerza
- `portrait_emotion` — variante opcional (no usado en la lógica, reservado para `maya_enfado.png`)
- `voice` — `sfx_voz_*` opcional que hace ducking de música al entrar al nodo
- `choices` — lista opcional de tuplas `(texto_a_mostrar, siguiente_node_id)`
- `on_enter` / `on_exit` — cadenas de acción guionizada

### 2.2 `DialogueTree`
Una colección de nodos con un punto de entrada `start_node`. Pueden coexistir varios árboles; el sistema carga uno a la vez.

**`DialogueTree.desde_datos(datos: dict)`** construye un árbol desde un diccionario — la vía real para los árboles de un escenario, que se guardan como JSON en `data/dialogues/<stage_id>.json` (AUD-244). Escribir el árbol a mano en Python (instanciando `DialogueNode` uno por uno) sigue siendo posible y es como se documentaba originalmente aquí, pero ya no es la única forma de verlo — antes de AUD-244 no había otra, lo que llevó a que un estudiante concluyera (en su propio código) que el sistema "no servía".

### 2.3 `DialogueSystem`
Gestiona el estado activo, la animación de progreso de texto (30 caracteres/s por defecto, `_velocidad`), la selección de elecciones con `MOVE_UP`/`MOVE_DOWN`, el avance con `CONFIRM`/`CANCEL`, y la **paginación** del texto cuando no cabe en el cuadro (`paginas`/`pagina_actual`, dos `@property` — no `paginas()`/`pagina_actual()`, no son invocables — y `confirmar()`, que sí es un método y avanza de página antes de avanzar de nodo).

> **AUD-455.** `paginas` y `pagina_actual` son propiedades, no métodos —
> verificado contra `src/framework/ui/dialogue_system.py`.

### 2.4 Acciones guionizadas
Formato: `accion:argumento`
- `give_item:item_id` — emite `ITEM_COLLECTED`
- `set_flag:flag_name` — emite `FLAG_SET`
- `complete_objective:id` — emite `OBJECTIVE_REQUESTED` (GAP-047)

### 2.5 Retrato animado (mejora 2026-08-26)
`DialogueSystem` cachea la tira `portrait` como `N` frames de `48×48` y elige frame por `anim_time*fps + text_progress*0.8`. Mientras `not _full_text_visible` hace lip-sync ciclando `0..N-1`; en reposo queda `0` + parpadeo cada ~3 s (cierra ojos `0.12s` usando último frame). Si el archivo no existe o no es tira, genera placeholder con boca (0 cerrada/1 media/2 abierta/3 blink) y mantiene compatibilidad 1-frame. Escalado por `text_scale` y marco `Theme.BORDER` + brillo `ACCENT_DIM` al hablar.

---

## 3. Maqueta visual

Caja de diálogo: 20px de margen, `110*escala` de alto, anclada abajo, `Theme.SURFACE` redondeado con sombra `Theme.SHADOW`, filo `ACCENT_DIM` arriba. Retrato `48*escala` en `(box.x+16, box.y+8)` con marco `BORDER` y sombra; brillo `ACCENT_DIM` cuando habla + boca animada. Nombre en ficha `Theme.ACCENT` centrada (`dibuja_ficha`), texto `Theme.TEXT` envuelto por píxeles (`dividir_en_lineas` + `FlujoDeTexto` cache `id(nodo),pagina,escala,ancho`), elecciones como chips `ACCENT/SURFACE_RAISED` con flecha. Pista `[ENTER] p/n` si pagina. Todo escala con `text_scale`.

---

## 4. Controles

| Acción | Efecto |
|--------|--------|
| MOVE_DOWN | Elección siguiente |
| MOVE_UP | Elección anterior |
| CONFIRM | Selecciona la elección / avanza de página o de nodo |
| CANCEL | Termina el diálogo en un nodo sin ramificar |

---

## 5. Estado de implementación

**Fichero:** `src/framework/ui/dialogue_system.py` (546→~680 líneas)
**Estado:** ✅ Completo + retrato animado — diálogo ramificado con retratos en tira N frames, lip-sync ligado a typewriter (`anim_time*fps + text_progress`), parpadeo `0.12s/3s`, voice por nodo, cache de frames escalados y fallback placeholder. JSON `portrait_frames/portrait_fps/voice` retrocompatibles (1 frame = estático).
**Assets:** `assets/sprites/portraits/{eco,jhon,jill,venado,rey_terciopelo,gavilan,paburu,narrador}.png` tira `192×48` (4 frames) generados por `tools/generate_all_assets.py::_gen_dialogue_portraits`; ejemplo vivo `data/dialogues/stage4_1.json` (4 árboles con `portrait_frames:4`).
**Historia:** AUD-127 encontró el sistema completo y **nunca abierto** — `Stage0._check_dialogue_triggers` buscaba un campo `dialogue_tree_id` que `MessageTrigger` no tenía, así que la condición nunca se cumplía. AUD-128 encontró además el desbordamiento de texto que corrige la paginación actual.

---
## 🔗 Documentos relacionados

- [[42_CUTSCENE_SYSTEM.md|Sistema de escenas cinemáticas]]
- [[09_HUD_SPEC.md|Especificación del HUD]]

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
- `portrait` — nombre de fichero de retrato opcional, 48×48, de `assets/sprites/portraits/`
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

---

## 3. Maqueta visual

Caja de diálogo: 20px de margen desde los bordes de pantalla, 100px de alto, anclada abajo (alto de pantalla − 110). Fondo negro a 200 de alfa. El retrato se dibuja en (30, box_y + 10) a 48×48; el nombre de quien habla en X+56 en dorado (#FFDC96); el texto en gris claro (#DCDCDC) debajo del nombre. Las elecciones se dibujan en box_y + 60 con resalte amarillo en la selección. La pista de continuar "[ENTER]" se muestra en los nodos hoja.

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

**Fichero:** `src/framework/ui/dialogue_system.py` (546 líneas)
**Estado:** ✅ Completo — diálogo ramificado con retratos, paginación de texto y carga desde datos JSON
**Historia:** AUD-127 encontró el sistema completo y **nunca abierto** — `Stage0._check_dialogue_triggers` buscaba un campo `dialogue_tree_id` que `MessageTrigger` no tenía, así que la condición nunca se cumplía. AUD-128 encontró además el desbordamiento de texto que corrige la paginación actual.

---
## 🔗 Documentos relacionados

- [[42_CUTSCENE_SYSTEM.md|Sistema de escenas cinemáticas]]
- [[09_HUD_SPEC.md|Especificación del HUD]]

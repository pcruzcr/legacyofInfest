---
document_id: "LOI-TRANSITION-048"
title: "Legacy of InFest — Especificación de transiciones de pantalla"
aliases: ["Especificación de transiciones de pantalla", "Screen Transitions"]
tags: ["transicion", "pantalla", "vfx"]
description: "Transiciones de fundido/barrido/deslizamiento/círculo"
source: "docs/48_SCREEN_TRANSITIONS.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación de transiciones de pantalla

**ID del documento:** LOI-TRANSITIONS-048
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento (el cuerpo ya tenía las correcciones
> AUD-168 en español; sólo §2–§4 y el resumen final seguían en inglés).
> Actualiza el conteo de líneas de `transition_manager.py`: decía 164, hoy
> tiene 208.

---

## 1. Visión general

El sistema de transiciones de pantalla da efectos visuales entre cambios de escena.

> **AUD-168.** Este documento describía dos capas, y la de abajo —un módulo
> `src/engine/scene/transitions.py` con cuatro clases de efecto— **fue retirada
> en AUD-111** por ser código muerto: cinco clases, cero usos en todo el
> repositorio, ni siquiera en pruebas, compitiendo por el nombre con el
> controlador que `SceneManager` sí instancia. El documento se quedó
> describiendo la arquitectura anterior, con recuento de líneas incluido.

Hoy hay **una sola capa**: `src/engine/scenes/transition_manager.py`, un
controlador con cuatro modos (fade, wipe, slide, circle) que se eligen por el
método que se llama — `start_fade_in`, `start_wipe`, `start_slide`,
`start_circle`. Las secciones 2.x de abajo describen esos modos, no clases
separadas.

---

## 2. Modos de transición

### 2.1 Fundido
Funde a/desde un color sólido (negro por defecto) durante una duración. Parámetros: booleano `fade_in`, tinte `color`.

### 2.2 Barrido
Barrido horizontal que revela la nueva escena. Dirección: `left_to_right` / `right_to_left`. Necesita una instantánea de la superficie anterior.

### 2.3 Deslizamiento
Desliza la escena anterior hacia fuera en una dirección (`left`, `right`, `up`, `down`) para revelar la nueva escena debajo.

### 2.4 Círculo
Barrido circular que se expande o se contrae, centrado en la pantalla.

---

## 3. `TransitionManager`

Un único controlador que envuelve todos los modos de transición con una API unificada.

| Método | Duración | Detalles |
|--------|----------|---------|
| `start_fade_out(dur)` | 0.35s | Funde a negro |
| `start_fade_in(dur)` | 0.35s | Funde desde negro |
| `start_wipe(dir, dur)` | 0.4s | Revelado por barrido |
| `start_slide(dir, dur)` | 0.4s | Deslizamiento hacia fuera |
| `start_circle(expanding, dur)` | 0.4s | Barrido circular |

El método `update(dt)` conduce la animación; `draw(surface)` dibuja la capa. Las propiedades `active` y `finished` informan del estado.

---

## 4. Uso

Lo llama `SceneManager` antes/después de cambiar de escena:
```python
tm.start_fade_out()
# ... cambio de escena ...
tm.start_fade_in()
```

---

## 5. Estado de implementación

**Ficheros:**
- `src/engine/scenes/transition_manager.py` (208 líneas) — el controlador, con
  los cuatro modos dentro

**Estado:** ✅ Completo — transiciones de fundido, barrido, deslizamiento y círculo

> **AUD-168.** Esta lista incluía un segundo fichero «(199 lines) — 4
> transition effect classes» que llevaba retirado desde AUD-111. Un recuento de
> líneas es exactamente la clase de dato que hace creer que alguien lo miró.

---
## 🔗 Documentos relacionados

- [[42_CUTSCENE_SYSTEM.md|Sistema de escenas cinemáticas]]
- [[46_FOG_OF_WAR.md|Especificación de la niebla de guerra]]

---
document_id: "LOI-FOG-046"
title: "Legacy of InFest — Especificación de la niebla de guerra"
aliases: ["Especificación de la niebla de guerra", "Fog of War"]
tags: ["niebla", "guerra", "vfx", "visibilidad"]
description: "Capa de niebla de guerra"
source: "docs/46_FOG_OF_WAR.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación de la niebla de guerra

**ID del documento:** LOI-FOG-046
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento completo (antes en inglés). Actualiza
> el conteo de líneas: decía 133 en `fog_of_war.py`; hoy tiene 184.

---

## 1. Visión general

La niebla de guerra (`src/framework/vfx/fog_of_war.py`) es una capa negra de pantalla completa con agujeros de alfa revelados alrededor de las posiciones del jugador y los enemigos. Oculta las áreas sin explorar y revela el mapa gradualmente según se mueve el jugador. La capa se dibuja en espacio de pantalla y se mueve con la cámara.

---

## 2. Arquitectura

### 2.1 `FogOfWar`
- **Capa:** una `Surface` de pantalla completa a alfa (0, 0, 0, 220)
- **Máscara:** un disco de degradado radial (`_construir_mascara`) volcado en cada posición revelada. Se construye en el constructor y **se reconstruye sólo cuando cambia el perfil de respiración** (AUD-338) — la misma fase dibuja la misma máscara
- **Composición:** la `máscara` se resta de la `capa` vía `BLEND_RGBA_SUB`, creando agujeros transparentes de borde suave

El pico de la máscara es el alfa **actual** del velo (220 en reposo), no 255, a propósito: `BLEND_RGBA_SUB` satura en cero, así que cualquier alfa por encima del propio velo revelaría exactamente igual y se perdería el primer tramo del degradado por el recorte. Igualarlos mete toda la caída dentro del rango visible. Cuando el velo respira, la máscara se reconstruye con el nuevo pico para que el perfil se mantenga exacto.

### 2.2 Parámetros
- `radius` — radio de revelado, 80px por defecto
- `hardness` — 0.6 por defecto. Fracción del radio que queda revelada **por completo**; el resto, `1 - hardness`, es la banda donde vuelve el velo, siguiendo un smoothstep (`3t² - 2t³`) que llega a cero con pendiente cero en ambas costuras. `hardness = 1.0` reproduce el disco de borde duro de la v1.0.0; `hardness = 0.0` se desvanece desde el mismo centro. Los valores se recortan a [0, 1].
- `animado` — `True` por defecto (AUD-338). Con `False`, el velo es la capa estática de la v1.0.0. En la fase cero (`t = 0`, sin ninguna llamada a `update()` todavía) el velo animado dibuja **exactamente** el estático, así que las pruebas y el código que nunca llaman a `update()` no ven ningún cambio
- `velocidad` — 0.15 por defecto. Ciclos de respiración por segundo: una inhalación y exhalación completas cada ~6.7 s. Se recorta a `>= 0` (0 congela el velo)
- `pulso` — 3.0 por defecto. Cuántos píxeles se hincha y encoge el radio del agujero alrededor de `radius`, en seno. Se recorta para que el agujero nunca pueda encoger a cero (un agujero que desaparece un instante es un parpadeo, no una respiración)
- `pulso_del_velo` — 6.0 por defecto. Cuántas unidades de alfa se oscurece y aclara el velo, **en antifase** con el radio: el velo se oscurece mientras los agujeros encogen (inhalar) y se aclara mientras crecen (exhalar). El resultado se recorta a [0, 255]

Alfa de la máscara medido a lo largo de un radio (`radius = 80`), muestreado en fracciones del radio — reproducible con `_hole_mask` y `pygame.surfarray.pixels_alpha`:

| hardness | 0.0 | 0.25 | 0.50 | 0.60 | 0.75 | 0.90 | 0.99 |
|---|---|---|---|---|---|---|---|
| 0.0 | 220 | 185 | 110 | 77 | 34 | 6 | 0 |
| 0.6 (por defecto) | 220 | 220 | 220 | 220 | 150 | 34 | 0 |
| 1.0 | 220 | 220 | 220 | 220 | 220 | 220 | 220 |

---

## 3. API

| Método | Descripción |
|--------|-------------|
| `clear()` | Reinicia todas las áreas reveladas |
| `reveal(x, y)` | Añade un punto de revelado en coordenadas de mundo |
| `reveal_all(points)` | Añade varios puntos de revelado a la vez |
| `update(dt)` | Avanza el reloj de respiración (AUD-338). Sin llamarlo, el velo se queda en fase cero — el comportamiento estático |
| `draw(surface, offset)` | Dibuja la capa de niebla, transformando los puntos de mundo a pantalla; reconstruye la máscara sólo cuando cambió el perfil de respiración |

---

## 4. Estado de implementación

**Fichero:** `src/framework/vfx/fog_of_war.py` (184 líneas)
**Estado:** ✅ Completo — capa en espacio de pantalla con agujeros de alfa de borde suave (AUD-198)
**Falta:** sin revelado permanente (las áreas exploradas vuelven a quedar negras fuera de pantalla). `draw()` recorre cada punto revelado y ese conjunto no tiene tope: medido a 320×180 con `radius = 80`, el coste es lineal, unos 2.7 µs por punto — 0.55 ms con 100 puntos, 6.65 ms con 2000, 10.73 ms con 4000. Un jugador en movimiento añade más o menos un punto por fotograma, así que la capa se come un tercio del presupuesto de 60 fps tras medio minuto caminando. Se sigue por separado; AUD-198 no lo resuelve.
**Nota:** ningún TMX declara todavía la propiedad de mapa `fog_of_war`, así que ningún escenario entregado enciende hoy la capa.

---
## 🔗 Documentos relacionados

- [[47_WATER_EFFECT.md|Especificación del efecto de agua]]
- [[48_SCREEN_TRANSITIONS.md|Especificación de transiciones de pantalla]]

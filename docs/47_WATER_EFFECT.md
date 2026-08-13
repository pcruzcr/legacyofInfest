---
document_id: "LOI-WATER-047"
title: "Legacy of InFest — Especificación del efecto de agua"
aliases: ["Especificación del efecto de agua", "Water Effect"]
tags: ["agua", "efecto", "vfx"]
description: "VFX de agua"
source: "docs/47_WATER_EFFECT.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación del efecto de agua

**ID del documento:** LOI-WATER-047
**Versión:** 1.1.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, estudiantes, asistentes de código

> **AUD-455.** Traduce el documento completo (antes en inglés, salvo el
> párrafo de AUD-240 que ya estaba en español). Actualiza el conteo de
> líneas: decía 50 en `water_effect.py`; hoy tiene 67.

---

## 1. Visión general

El efecto de agua (`src/framework/vfx/water_effect.py`) es una capa visual animada que dibuja ondulaciones senoidales con mezcla de alfa. Da un efecto de distorsión apropiado para escenas bajo el agua, piscinas y charcos de lluvia.

---

## 2. Arquitectura

### 2.1 `WaterEffect`
- **Capa:** una `Surface` de alfa por píxel a la resolución de pantalla
- **Animación:** cada línea de barrido (cada 2px de Y) calcula un desplazamiento de onda senoidal: `sin(y * frequency + time) * amplitude`
- **Mezcla:** `BLEND_RGBA_ADD` para un aspecto luminoso del agua
- **Tinte de color:** azul (40, 80, 160) a alfa 100 por defecto

---

## 3. Parámetros

| Parámetro | Por defecto | Descripción |
|-----------|---------|-------------|
| `speed` | 1.5 | Multiplicador de velocidad de la animación de onda |
| `amplitude` | 4 | Desplazamiento horizontal máximo de la onda (px) |
| `frequency` | 0.04 | Frecuencia de la onda (ciclos por píxel) |
| `alpha` | 100 | Transparencia de la capa (0–255) |
| `tint` | (40, 80, 160) | Color RGB de la capa de agua |

Todo ajustable vía `set_params()` — **y desde el mapa** (AUD-240).

Hasta AUD-240 esta frase describía sólo la API: `StageScene` construía un
`WaterEffect()` con los valores por defecto y nunca llamaba a `set_params`, así
que los cinco mandos eran inalcanzables desde el contenido y toda el agua del
juego ondulaba igual. Ahora el escenario los declara como propiedades del mapa:

| Propiedad del mapa | Rango | Por defecto |
|---|---|---|
| `water_speed` | 0 – 8 | 1.5 |
| `water_amplitude` | 0 – 16 px | 4 |
| `water_frequency` | 0 – 1 | 0.04 |
| `water_alpha` | 0 – 255 | 100 |
| `water_tint` | nombre de la paleta de luces o `#rrggbb` | (40, 80, 160) |

Los valores fuera de rango se recortan en vez de abortar la carga, como el resto
del cargador: un mapa mal escrito se ve raro, no deja al estudiante sin nivel.
Un mapa que no declare nada se ve exactamente igual que antes.

---

## 4. Estado de implementación

**Fichero:** `src/framework/vfx/water_effect.py` (67 líneas)
**Estado:** ✅ Completo — agua animada con ondas senoidales y parámetros configurables
**Falta:** sin refracción/distorsión del contenido subyacente; sin reflejos de superficie

---
## 🔗 Documentos relacionados

- [[45_SWIMMING_SPEC.md|Especificación de la mecánica de natación]]
- [[46_FOG_OF_WAR.md|Especificación de la niebla de guerra]]

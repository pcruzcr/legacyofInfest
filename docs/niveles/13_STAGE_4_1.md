---
document_id: "LOI-LVL-4-1"
title: "Nivel 4-1 — La Entrada al Cementerio"
aliases: ["Stage 4-1", "La Entrada al Cementerio"]
tags: ["level", "zona-final", "atmospheric"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/13_STAGE_4_1.md"
---

# NIVEL 4-1 — LA ENTRADA AL CEMENTERIO

**Entregable:** profesorado (no se asigna a estudiantes) · **Zona:** Final — El Cementerio Sagrado · **Tipo:** Travesía atmosférica (sin enemigos)

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★☆☆☆ (2/5) — **atmosférica**: el miedo es el desafío |
| Tamaño mínimo | **1600 × 608 px** (100 × 38 tiles) |
| Tamaño de referencia | ~400 px de recorrido en el diseño canónico |
| Tipos de enemigo | **0 — regla de oro: prohibido añadir** |
| Enemigos mínimos | 0 |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `Portal`, 1 `HazardZone`, 1 visión especial |
| Día/noche | `dusk` 19:00 → 23:00, `day_length` 900 s *(sugerido)* |
| Clima | Libre (sugerencia: niebla baja que nunca tapa los peligros del suelo) |
| Concepto académico | Unidad V (tinte espectral) + Unidad VIII (visión de umbral) |
| Límite de tiempo | Sin límite (pacing atmosférico) |

## Reglas obligatorias

1. **Sin enemigos.** Si el nivel aburre, se arregla con más marcas ocultas, no
   con serpientes. La tensión ya está: es el silencio antes del juez.
2. **Visión espectral obligatoria** (Unidad VIII): con el botón de ataque largo
   se filtra la pantalla en umbral y se revelan marcas ocultas en las losas
   (3 s). Es la mecánica protagonista.
3. **Los cuencos de fuego son plataformas y luz**: cerca = más brillo; lejos =
   oscuridad. El brillo por proximidad es la mecánica de la Unidad V.
4. **Las grietas pulsantes** (HazardZone 0.25 periódico) son los únicos peligros
   y deben leerse con anticipación (pulso visible).
5. **Los ecos de los espíritus vencidos** (venado, Rey, Gavilán) aparecen como
   siluetas en BG_Mid: storytelling ambiental, no entidades.

## Día/noche (sugerido)

- `start_hour`: `dusk` (19:00) — el cementerio se ve por última vez de día agonizante.
- `day_length`: 900 s → termina a las **23:00** (noche) — prepara el clímax.
- *(Sugerido por la guía; el canon no lo fija: si el profesor decide otra hora,
  debe mantener la regla del reloj continuo con el 4-2.)*

## Enemigos

Ninguno. El único "contenido" son:

| Elemento | Cantidad | Nota |
|---|---|---|
| Cuencos de fuego | 3+ | Plataformas OneWay + luz por proximidad |
| Grietas pulsantes | 2+ | HazardZone 0.25 periódico |
| Marcas ocultas | 5+ | Solo visibles con la visión espectral |
| Ecos de espíritus | 3 | Siluetas BG_Mid (venado, Rey, Gavilán) |
| Coleccionables | 0 (o 3 discretos) | Mejor sin coleccionables: el silencio es el premio |

## Mapa sugerido

```
 19:00 ── OCASO → NOCHE ─────► 23:00
 SPAWN ─[fuego]──[fuego]──[grieta]──[fuego]──[grieta]──[fuego]── PORTAL
   │  ecos en BG_Mid: venado · serpiente · halcón
   │  las losas ocultan marcas: visión espectral (ataque largo)
   └── sin enemigos: la atmósfera ES el desafío
```

## Checklist de cierre

- [ ] Sin enemigos (regla de oro)
- [ ] Visión espectral funcionando con marcas ocultas
- [ ] Cuencos con luz por proximidad; grietas pulsantes legibles
- [ ] `start_hour = "dusk"` y `day_length = 900` (sugerido)
- [ ] `validate_tmx.py --ci` en verde

---
document_id: "LOI-LVL-3-2"
title: "Nivel 3-2 — El Hall"
aliases: ["Stage 3-2", "El Hall"]
tags: ["level", "entregable-3", "zona-3"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/10_STAGE_3_2.md"
---

# NIVEL 3-2 — EL HALL

**Entregable:** 3 (Evaluación Práctica III) · **Zona:** 3 — Sede Heredia · **Tipo:** Travesía + combate interior

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★★★☆ (4/5) |
| Tamaño mínimo | **1600 × 608 px** (100 × 38 tiles) |
| Tamaño de referencia | 1088 × 608 px (68 × 38, implementado — con balcones añade metros verticales) |
| Tipos de enemigo | 3 (obligatorios) |
| Enemigos mínimos | 10 (de referencia: 13) |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `Portal`, 5 coleccionables |
| Día/noche | 05:00 → 08:00, `day_length` 1200 s |
| Clima | Libre (sugerencia: columnas de polvo en los haces de luz de las claraboyas) |
| Concepto académico | Unidad VIII (watershed: tres zonas del hall con spawns distintos) + Unidad IV (5 capas) |
| Límite de tiempo | 170 s |

## Reglas obligatorias

1. **El reloj continúa del 3-1**: `start_hour = 05:00` y `day_length = 1200` s → termina a las **08:00 (amanecer)**.
2. **El AMANECER es la mecánica del nivel**: el jugador entra en la oscuridad más fría y sale con luz cálida entrando por las claraboyas (transición visible de la Unidad V/VI).
3. **Tres zonas del watershed obligatorias** (entrada / centro / balcones): cada zona activa sus propios spawns — el jugador debe leer la zona.
4. Los balcones son plataformas sólidas accesibles por dos escaleras.
5. Los techos son indestructibles: los proyectiles rebotan (usarlo en el diseño de los tiradores).
6. Las claraboyas marcan la posición del jugador (luz sobre él): el nivel debe jugar con eso.

## Día/noche (obligatorio)

- `start_hour`: `05:00` — continúa el reloj del 3-1 (terminó a las 05:00).
- `day_length`: 1200 s (~170 s × 24 / 3.5 h) → termina a las **08:00**: el amanecer es el clímax visual del nivel.

## Enemigos (composición sugerida)

| Tipo | Cantidad mín. | Cantidad ref. | Rol en el nivel |
|---|---|---|---|
| `WalkerPalom` | 4 | 5 | Suelo: lentas, hitbox grande, ocupan el carril |
| `FlyingHalcon` | 5 | 6 | Aéreas: patrullan desde la altura del techo |
| `ShooterBuitre` | 2 | 2 | Balcones: fuego de fondo desde lo alto |

Total mínimo **10 enemigos**. Distribución por zonas del watershed: entrada
(2 palomas + 2 halcones), centro (1 paloma + 2 halcones + 1 buitre), balcones
(2 palomas + 2 halcones + 1 buitre).

## Objetos y elementos

| Elemento | Cantidad | Nota |
|---|---|---|
| `PlayerSpawn` | 1 | Entrada del hall |
| `Checkpoint` | 1 | En el centro (cambio de zona del watershed, obligatorio) |
| `Portal` | 1 | → 3-3 |
| `MessageTrigger` | 1 | Presenta las zonas (Unidad VIII) |
| Coleccionables | ≥ 5 | En los balcones (recompensan la subida) |
| `OneWay`/escaleras | 2 | Acceso a los balcones |
| `FG_Overlay` | libre | Vigas y claraboyas |

## Mapa sugerido (canónico del Entregable 1)

```
 05:00 ── AMANECER ──────────► 08:00
            [balcón IZQ: buitre + halcones]        [balcón DER: buitre + halcones]
               ▲ escalera                             ▲ escalera
 SPAWN ─[P][H]──[P]──[CHECKPOINT]──[H][P]──[H][B]────────── PORTAL
   zona entrada      zona central                zona balcones
   (2P+2H)           (1P+2H+1B)                  (2P+2H+1B)
   claraboya 1        claraboya 2                claraboya 3
```

## Checklist de cierre

- [ ] Tamaño ≥ 1600×608 px (o 1088×608 con balcones jugables)
- [ ] 3 tipos, ≥ 10 enemigos, spawns por zona del watershed
- [ ] `start_hour = 05:00` y `day_length = 1200` (amanecer visible)
- [ ] Claraboyas que marcan posición; techos que rebotan proyectiles
- [ ] `validate_tmx.py --ci` y `grade_stage.py` en verde

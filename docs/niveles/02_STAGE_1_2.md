---
document_id: "LOI-LVL-1-2"
title: "Nivel 1-2 — La Soda"
aliases: ["Stage 1-2", "La Soda"]
tags: ["level", "entregable-1", "zona-1"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/02_STAGE_1_2.md"
---

# NIVEL 1-2 — LA SODA

**Entregable:** 1 (Evaluación Práctica I) · **Zona:** 1 — Universidad Invenio · **Tipo:** Travesía + combate interior

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★☆☆☆ (2/5) |
| Tamaño mínimo | **1600 × 608 px** (100 × 38 tiles) |
| Tamaño de referencia | 768 × 608 px (48 × 38 tiles, implementado) |
| Tipos de enemigo | 2 mínimos / 3 máximos |
| Enemigos mínimos | 6 (de referencia: 10) |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `Portal`, 5 coleccionables, 1 `HazardZone` |
| Día/noche | 14:00 → 18:00, `day_length` 900 s |
| Clima | Libre (sugerencia: aire quieto con polvo en los haces de luz) |
| Concepto académico | Unidad V (iluminación por color: cocina cálida vs. sala fría) |
| Límite de tiempo | 150 s |

## Reglas obligatorias

1. **El reloj continúa del 1-1**: `start_hour = 14:00` (tarde) y `day_length = 900` s para terminar a las **18:00**.
2. **Es el nivel que introduce el `HazardZone`** (bandejas lanzadas, daño 0.25): debe estar señalizado y en un tramo sin caminantes.
3. **Dos pisos obligatorios**: nivel bajo (mesas) y entrepiso (estantería de cocina) conectados por plataforma de un sentido.
4. La iluminación por color es la materia del nivel: zona cálida (cocina, tinte HSL cálido) vs. zona fría (sala) — debe leerse a primera vista.
5. El tirador (cocinero) es la primera amenaza de "tercer carril": su tramo queda despejado.

## Día/noche (obligatorio)

- `start_hour`: `14:00` — continúa el reloj del 1-1 (que terminó a las 14:00).
- `day_length`: 900 s → termina a las **18:00** (tarde dorada, luz ámbar baja).

## Enemigos (composición sugerida)

| Tipo | Cantidad mín. | Cantidad ref. | Rol en el nivel |
|---|---|---|---|
| `WalkerRaton` (caminante rápido) | 3 | 4 | Ritmo del suelo: patrulla entre mesas, más rápido que el insecto del 1-1 |
| `FlyingCucaracha` (volador errático) | 3 | 5 | Ocupa el aire de la sala; vuelo en senoide |
| `ShooterCocinero` (tirador) | 0–1 | 1 | Fondo: lanza comida desde detrás del mostrador |

Total mínimo **6 enemigos**. Si se usan 2 tipos, la cantidad mínima sube a 8
(se compensa la variedad con densidad).

## Objetos y elementos

| Elemento | Cantidad | Nota |
|---|---|---|
| `PlayerSpawn` | 1 | Entrada, izquierda |
| `Checkpoint` | 1–2 | Tras la sala principal (obligatorio) |
| `Portal` | 1 | Derecha, salida al campus |
| `HazardZone` | 1+ | Zona de bandejas del mostrador |
| `MessageTrigger` | 1 | Presenta la iluminación por color (Unidad V) |
| Coleccionables | ≥ 5 | En bandejas y estanterías del entrepiso |
| `Platform` | 1+ | Plataforma de acceso al entrepiso |

## Mapa sugerido (canónico del Entregable 1)

```
 14:00 ── TARDE ───────────► 18:00
 entrada                [entrepiso estanterías - Platform]
   │   mesas │  mesas │  ┌───┬─────┐
 SPAWN ─────[W][W]────[W][C][C][W]── [H] mostrador con HAZARD ─ [cocinero] ─ PORTAL
   │          │            │    sala fría (tinte azul)      cocina (tinte cálido)
 Checkpoint tras la sala   entrepiso con coleccionables
```

Leyenda: `[W]` ratón · `[C]` cucaracha · `[H]` hazard. El mapa implementado
(48×38) es la versión compacta: si el propio mapa es más ancho, mantener el
orden presentar→exigir.

## Checklist de cierre

- [ ] Tamaño ≥ 1600×608 px y suelo en y=480
- [ ] ≥ 6 enemigos, 2–3 tipos, cocinero en tramo despejado
- [ ] `start_hour = 14:00` y `day_length = 900`
- [ ] HazardZone señalizado; dos pisos con Platform
- [ ] `validate_tmx.py --ci` y `grade_stage.py` en verde

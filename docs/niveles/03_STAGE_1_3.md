---
document_id: "LOI-LVL-1-3"
title: "Nivel 1-3 — Las Aulas"
aliases: ["Stage 1-3", "Las Aulas"]
tags: ["level", "entregable-1", "zona-1"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/03_STAGE_1_3.md"
---

# NIVEL 1-3 — LAS AULAS

**Entregable:** 1 (Evaluación Práctica I) · **Zona:** 1 — Universidad Invenio · **Tipo:** Travesía + combate (examen de zona)

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★☆☆☆ (2/5, la más exigente de la Zona 1) |
| Tamaño mínimo | **2400 × 608 px** (150 × 38 tiles, 3 pantallas) |
| Tamaño de referencia | 3200 × 608 px (200 × 38 tiles, implementado) |
| Tipos de enemigo | 3 (obligatorios: suelo, aire y fondo) |
| Enemigos mínimos | 10 (de referencia: 10) |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `Portal`, 5 coleccionables, 1 `HazardZone` |
| Día/noche | 18:00 → 22:00, `day_length` 900 s |
| Clima | Libre (sugerencia: luz polvorienta del ocaso entrando por las ventanas) |
| Concepto académico | Unidad VIII (umbral: tiza brillante vs. sombra de raíces) + Unidad VI (puertas con ease) |
| Límite de tiempo | 150 s |

## Reglas obligatorias

1. **El reloj continúa del 1-2**: `start_hour = 18:00` (ocaso) y `day_length = 900` s → termina a las **22:00 (noche)**.
2. **Es el examen de la Zona 1**: aquí se combinan los tres carriles (suelo, aire, fondo) por primera vez, y solo en el último tercio.
3. **Tres salones laterales accesibles** (no-scroll): cada salón ofrece coleccionables o un peligro; al menos uno debe tener la solución alternativa.
4. **Mecánica de luz obligatoria** (Unidad VIII): zonas brillantes (polvo de tiza) y zonas oscuras (sombra de raíces) que cambian cómo se lee el nivel (ej.: las púas se ven solo a la luz o solo con la mecánica de umbral).
5. El checkpoint es un pizarrón con animación de tiza (debe activarse visiblemente).
6. Las puertas de los salones se abren con animación suave (ease_out_bounce) — ningún sistema oculto.

## Día/noche (obligatorio)

- `start_hour`: `18:00` — continúa el reloj del 1-2 (terminó a las 18:00).
- `day_length`: 900 s → el nivel **se oscurece durante la partida**: empieza en ocaso dorado y termina en noche. La transición visible es parte de la mecánica de luz.

## Enemigos (composición sugerida)

| Tipo | Cantidad mín. | Cantidad ref. | Rol en el nivel |
|---|---|---|---|
| `WalkerEstudiante` (caminante) | 5 | 5 | Patrulla corredor y salones; ritmo constante |
| `FlyingNotebook` (volador, Bézier) | 2 | 3 | Dentro de los salones: curvas que "corrigen" |
| `ShooterTiza` (tirador) | 2 | 2 | Extremos de los pizarrones: amenaza de fondo |

Total mínimo **10 enemigos**. Los 3 tipos son obligatorios: es el nivel que
demuestra que se dominan los tres arquetipos.

## Objetos y elementos

| Elemento | Cantidad | Nota |
|---|---|---|
| `PlayerSpawn` | 1 | Inicio del corredor |
| `Checkpoint` | 1 | El pizarrón checkpoint (obligatorio con animación) |
| `Portal` | 1 | Derecha → 1-4 |
| `HazardZone` | 1+ | Púas entre las raíces (visibles bajo la regla de luz) |
| `MessageTrigger` | 1 | Explica la mecánica de luz (Unidad VIII) |
| Coleccionables | ≥ 5 | Repartidos en los 3 salones |
| `OneWay` | 1+ | Umbrales de los salones |

## Mapa sugerido (canónico del Entregable 1)

```
 18:00 ── OCASO → NOCHE ──────► 22:00
   [SALÓN 1]     [SALÓN 2]          [SALÓN 3]
   ┌────────┐   ┌─────────┐        ┌─────────┐
   │ C×2, T  │   │ N×2, T  │        │ C, N    │   (T = tiza en pizarrón)
   │ colecc. │   │ easter  │        │ colecc. │
   └──╨──────┘   └──╨──────┘        └──╨──────┘
 SPAWN ───[E][E]──[E]──────[PIZARRÓN-CHECKPOINT]────[E][E][E]──[H púas]── PORTAL
          corredor con estudiantes          │        último tercio: los 3 carriles
   zona de luz (tiza) y sombra (raíces)     │
```

## Checklist de cierre

- [ ] Tamaño ≥ 2400×608 px
- [ ] 3 tipos de enemigo, ≥ 10 enemigos, combinación solo al final
- [ ] `start_hour = 18:00` y `day_length = 900` (se hace de noche en el nivel)
- [ ] Mecánica de luz Unidad VIII funcionando y explicada
- [ ] `validate_tmx.py --ci` y `grade_stage.py` en verde

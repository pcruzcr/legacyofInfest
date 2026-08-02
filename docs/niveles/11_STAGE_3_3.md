---
document_id: "LOI-LVL-3-3"
title: "Nivel 3-3 — El Patio"
aliases: ["Stage 3-3", "El Patio"]
tags: ["level", "entregable-3", "zona-3"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/11_STAGE_3_3.md"
---

# NIVEL 3-3 — EL PATIO

**Entregable:** 3 (Evaluación Práctica III) · **Zona:** 3 — Sede Heredia · **Tipo:** Travesía + combate (examen de zona)

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★★★☆ (4/5) — el examen de la Zona 3 |
| Tamaño mínimo | **1600 × 608 px** (100 × 38 tiles) |
| Tamaño de referencia | 960 × 608 px (60 × 38, implementado — denso y corto) |
| Tipos de enemigo | 3 (obligatorios) |
| Enemigos mínimos | 10 (de referencia: 11) |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `Portal`, 5 coleccionables, 1 elemento curativo |
| Día/noche | 08:00 → 11:00, `day_length` 1200 s |
| Clima | Libre (sugerencia: nubes que pasan y cambian la agresividad aérea — mecánica viva de la Unidad VII) |
| Concepto académico | Unidad VII (gaussian_blur del cielo) + Unidad III (fuente en Catmull-Rom) |
| Límite de tiempo | 145 s (el más ajustado del juego) |

## Reglas obligatorias

1. **El reloj continúa del 3-2**: `start_hour = 08:00` y `day_length = 1200` s → termina a las **11:00**.
2. **Es el examen de la Zona 3**: fuego cruzado de quetzales desde los alféizares, halcones con detección a ancho completo, palomas que bloquean el carril.
3. **El brillo del cielo controla la agresividad aérea** (Unidad VII): cielo despejado = más voladores activos. Es mecánica, no decoración.
4. **La fuente cura 0.25** (una vez por activación): el jugador decide cuándo curarse — la tensión es de decisión.
5. Las jardineras son el único refugio (32 px, permiten agacharse).
6. Es un claustro: tres muros. El nivel se siente como una emboscada con paisaje.

## Día/noche (obligatorio)

- `start_hour`: `08:00` — continúa el reloj del 3-2 (terminó a las 08:00).
- `day_length`: 1200 s → termina a las **11:00**: mañana plena, luz blanca.

## Enemigos (composición sugerida)

| Tipo | Cantidad mín. | Cantidad ref. | Rol en el nivel |
|---|---|---|---|
| `WalkerPalom` | 3 | 3 | Suelo: ocupan el carril, bloquean la huida |
| `FlyingHalcon` | 4 | 5 | Detectan a ancho completo del patio |
| `ShooterQuetzal` | 3 | 3 | Alféizares: fuego cruzado sobre el centro |

Total mínimo **10 enemigos**.

## Objetos y elementos

| Elemento | Cantidad | Nota |
|---|---|---|
| `PlayerSpawn` | 1 | Entrada del patio |
| `Checkpoint` | 1 | A la entrada (obligatorio) |
| `Portal` | 1 | → 3-4 |
| Fuente curativa | 1 | Centro: OneWay + cura 0.25 por activación |
| Coleccionables | ≥ 5 | Tras las jardineras y el borde de la fuente |
| `OneWay` | 3+ | Jardineras (32 px) |

## Mapa sugerido (canónico del Entregable 1)

```
 08:00 ── MAÑANA ────────────► 11:00
     [Q]           [Q]             [Q]     ← alféizares (fuego cruzado)
 SPAWN ─[P]──[H]────[FUENTE]────[H][P]──[H]── PORTAL
   │ jardineras cubierta │            │
   [CP]  cielo despejado = halcones agresivos (Unidad VII)
   La fuente cura: la decisión de curarse es el examen
```

## Checklist de cierre

- [ ] Tamaño ≥ 1600×608 px
- [ ] 3 tipos, ≥ 10 enemigos, fuego cruzado real
- [ ] `start_hour = 08:00` y `day_length = 1200`
- [ ] Cielo controlando agresividad (Unidad VII) + fuente curativa
- [ ] `validate_tmx.py --ci` y `grade_stage.py` en verde

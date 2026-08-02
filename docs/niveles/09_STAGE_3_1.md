---
document_id: "LOI-LVL-3-1"
title: "Nivel 3-1 — La Entrada de Piedra"
aliases: ["Stage 3-1", "La Entrada de Piedra"]
tags: ["level", "entregable-3", "zona-3"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/09_STAGE_3_1.md"
---

# NIVEL 3-1 — LA ENTRADA DE PIEDRA

**Entregable:** 3 (Evaluación Práctica III) · **Zona:** 3 — Sede Heredia · **Tipo:** Travesía expuesta (el cielo es el techo)

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★★☆☆ (3/5) |
| Tamaño mínimo | **1600 × 224 px** (100 × 14 tiles) |
| Tamaño de referencia | 1600 × 224 px (100 × 14, implementado) |
| Tipos de enemigo | 2 mínimos / 3 máximos |
| Enemigos mínimos | 8 (de referencia: 10) |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `Portal`, 5 coleccionables |
| Día/noche | **22:00 (NOCHE)** → 05:00, `day_length` 500 s |
| Clima | Libre (sugerencia: niebla baja rasante que no oculta a los enemigos) |
| Concepto académico | Unidad VI (losas que se encienden al pisarlas) + Unidad V (HSL de la piedra) |
| Límite de tiempo | 160 s |

## Reglas obligatorias

1. **Es el nivel inicial de la Zona 3: declara dónde empieza la NOCHE.** `start_hour = "night"` (22:00) es obligatorio.
2. **Altura máxima del mapa: 224 px** — un pasillo al aire libre sin techos: los picados vienen del cielo y deben leerse (sombra antes del ataque).
3. **Las losas se encienden en secuencia al pisarlas** (Unidad VI): es la mecánica protagonista, no decoración.
4. Sin cobertura real: las jardineras son las únicas cubiertas (plataformas de un sentido).
5. **Los halcones nunca picotean en el mismo tramo que las garzas** (regla de lectura: se aprenden por separado).

## Día/noche (obligatorio)

- `start_hour`: `night` (22:00) — **el nivel inicial de la Zona 3 indica dónde inicia: NOCHE**.
- `day_length`: 500 s (~150 s × 24 / 7 h) → termina a las **05:00** (antes del alba, luz azul subiendo).
- La noche que se va debe notarse: el último tramo es más claro que el primero.

## Enemigos (composición sugerida)

| Tipo | Cantidad mín. | Cantidad ref. | Rol en el nivel |
|---|---|---|---|
| `WalkerGarza` | 3 | 4 | Falsa calma: patrulla el suelo con dignidad |
| `FlyingHalcon` | 3 | 4 | Picado desde la altura: anuncian con sombra |
| `ShooterQuetzal` | 0–2 | 2 | Sobre los arcos (fondo, el tercer carril) |

Total mínimo **8 enemigos**.

## Objetos y elementos

| Elemento | Cantidad | Nota |
|---|---|---|
| `PlayerSpawn` | 1 | Inicio del paseo |
| `Checkpoint` | 1 | Tras el primer tercio (obligatorio) |
| `Portal` | 1 | → 3-2 |
| `MessageTrigger` | 1 | Presenta las losas (Unidad VI) |
| Coleccionables | ≥ 5 | En las jardineras y bordes |
| `OneWay` | 2+ | Jardineras como cubierta |

## Mapa sugerido (canónico del Entregable 1)

```
 22:00 ── NOCHE → ALBA ──────► 05:00
   [arco]   [arco]     [arco]      [arco]
 SPAWN ───[Q]─────[CP]────[Q]────────────── PORTAL
   │ jardineras cubierta    │
   [G][G]  losas se encienden al pisar  [H][H]
   [H] halcón (picado con sombra) · [G] garza · [Q] quetzal en arco
   Regla: halcones y garzas en tramos separados
```

## Checklist de cierre

- [ ] Tamaño ≥ 1600×224 px (altura ≤ 224)
- [ ] ≥ 8 enemigos; halcones y garzas en tramos separados
- [ ] `start_hour = "night"` y `day_length = 500`
- [ ] Losas que se encienden funcionando (Unidad VI)
- [ ] `validate_tmx.py --ci` y `grade_stage.py` en verde

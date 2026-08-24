---
document_id: "LOI-LVL-2-1"
title: "Nivel 2-1 — Las Oficinas / La Planicie"
aliases: ["Stage 2-1", "Las Oficinas", "La Planicie"]
tags: ["level", "entregable-2", "zona-2"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/05_STAGE_2_1.md"
---

# NIVEL 2-1 — LAS OFICINAS / LA PLANICIE

**Entregable:** 2 (Evaluación Práctica II) · **Zona:** 2 — El Datacenter · **Tipo:** Travesía (re-baseline post-jefe)

> **Nota de realidad.** El mapa implementado en la ranura 2-1 es el de las
> oficinas (`stage2_1_oficinas.tmx`). El diseño canónico de `16_WORLD_DESIGN.md`
> coloca aquí la planicie abierta. Las reglas aplican a lo que el estudiante
> presente (oficinas o planicie), pero la **ficha de día/noche es fija**.

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★★☆☆ (3/5) |
| Tamaño mínimo | **1600 × 608 px** (100 × 38 tiles) |
| Tamaño de referencia | 3200 × 608 px (200 × 38, oficinas implementadas) |
| Tipos de enemigo | 2 mínimos / 3 máximos |
| Enemigos mínimos | 8 (de referencia: 12) |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `NextTrigger`, 5 coleccionables, 1 `HazardZone` |
| Día/noche | **17:00 (ATARDECER)** → 20:30, `day_length` 1000 s |
| Clima | Libre (sugerencia: calima térmica en la planicie / polvo dorado en las oficinas) |
| Concepto académico | Unidad VII (Canny como visión de cableado) + Unidad VIII (conteo de servidores) |
| Límite de tiempo | 150 s |

## Reglas obligatorias

1. **Es el nivel inicial de la Zona 2: declara dónde empieza el ATARDECER.** `start_hour = 17:00` es obligatorio.
2. **Primera vez que el foso es legal** (regla global §2.4.3): si hay foso, siempre con ruta segura alternativa.
3. **Los LED rojos parpadean sincronizados** como lenguaje de peligro (oficinas) o el alambre de púas a la rodilla obliga a agacharse (planicie).
4. Primer nivel tras el jefe 1-4: **la primera mitad es más amable que el final del 1-3** (regla de respiro de la curva).
5. El concepto de la Unidad VII (ver el cableado con Canny) debe estar implementado y ser visible.

## Día/noche (obligatorio)

- `start_hour`: `17:00` — **ATARDECER: el nivel inicial de la Zona 2 indica dónde inicia**.
- `day_length`: 1000 s (~150 s × 24 / 3.5 h) → termina a las **20:30** (noche entrando).
- El atardecer debe leerse en el color: la luz baja de ámbar a azul noche durante el nivel.

## Enemigos (composición sugerida)

### Variante OFICINAS (implementada)

| Tipo | Cantidad mín. | Cantidad ref. | Rol |
|---|---|---|---|
| `WalkerTerciopelo` | 5 | 7 | "Empleados del turno": patrullan entre cubículos |
| `ShooterVenomoLargo` | 2 | 3 | Largo alcance tras las particiones de vidrio |
| `FlyingTerciovolador` | 0–2 | 2 | Solo en el último tercio |

### Variante PLANICIE (canónica)

| Tipo | Cantidad mín. | Cantidad ref. | Rol |
|---|---|---|---|
| `WalkerSerpientePequena` | 5 | 6 | Patrulla rápida en campo abierto |
| `ShooterSerpienteArbol` | 2 | 3 | En postes de la cerca |
| `FlyingBoa` | 0–2 | 2 | Aérea en senoide |

Total mínimo **8 enemigos** en ambas variantes.

## Objetos y elementos

| Elemento | Cantidad | Nota |
|---|---|---|
| `PlayerSpawn` | 1 | Entrada desde la Zona 1 |
| `Checkpoint` | 1–2 | Mitad del recorrido y opcional pre-boss |
| `NextTrigger` | 1 | → 2-2 |
| `HazardZone` | 1+ | Grupos de serpientes (0.25) o rejillas de calor |
| `MessageTrigger` | 1 | Presenta la Unidad VII |
| Coleccionables | ≥ 5 | Tras las particiones / entre los postes |

## Mapa sugerido (variante oficinas, canónica del Entregable 1)

```
 17:00 ── ATARDECER ──────────► 20:30
 SPAWN ─[T]──[T]────[CHECKPOINT]──[T][V]──[H]──[T][T][V]──[S largo]── NEXTTRIGGER
   cubículos  │   particiones de vidrio (sin colisión)    │   LED rojos
              └── coleccionables tras las particiones      └── último tercio: 3 carriles
```

## Checklist de cierre

- [ ] Tamaño ≥ 1600×608 px
- [ ] ≥ 8 enemigos, 2–3 tipos; primera mitad más amable que el final del 1-3
- [ ] `start_hour = 17:00` (atardecer) y `day_length = 1000`
- [ ] Concepto Unidad VII visible (Canny / calima)
- [ ] `validate_tmx.py --ci` y `grade_stage.py` en verde

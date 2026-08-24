---
document_id: "LOI-LVL-2-3"
title: "Nivel 2-3 — Las Oficinas"
aliases: ["Stage 2-3", "Las Oficinas"]
tags: ["level", "entregable-2", "zona-2"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/07_STAGE_2_3.md"
---

# NIVEL 2-3 — LAS OFICINAS

**Entregable:** 2 (Evaluación Práctica II) · **Zona:** 2 — El Datacenter · **Tipo:** Travesía + combate (examen de zona)

> **Nota de realidad.** El diseño canónico coloca las oficinas en esta ranura;
> en el juego implementado las oficinas ocupan la ranura 2-1 (ver
> `05_STAGE_2_1.md`). Si el estudiante diseña este nivel como oficinas del
> datacenter, debe **cambiar el tema de la planicie/antenas** para no duplicar.

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★★★☆ (4/5) |
| Tamaño mínimo | **2400 × 608 px** (150 × 38 tiles, 3 pantallas) |
| Tipos de enemigo | 3 (obligatorios) |
| Enemigos mínimos | 10 (de referencia: 12) |
| Objetos mínimos | 1 `PlayerSpawn`, 2 `Checkpoint`, 1 `NextTrigger`, 5 coleccionables, 1 `HazardZone` |
| Día/noche | 23:30 → 02:30, `day_length` 1000 s |
| Clima | Libre (sugerencia: humo de cables, luz de LED roja pulsante) |
| Concepto académico | Unidad VII (Canny como visión de cableado) + Unidad VIII (conteo de servidores) |
| Límite de tiempo | 150 s |

## Reglas obligatorias

1. **El reloj continúa del 2-2**: `start_hour = 23:30` y `day_length = 1000` s → termina a las **02:30 (madrugada cerrada)**.
2. **Es el examen de la Zona 2**: los tres carriles se combinan; los 3 tipos son obligatorios.
3. **Dos checkpoints obligatorios**: mitad del mar de cubículos y puerta de la sala de servidores.
4. La mecánica de la Unidad VIII (contar servidores activos con componentes conectados) debe influir en el nivel (puntuación o densidad de peligro).
5. Las particiones de vidrio son visuales sin colisión (atraviesan): usarlo como diseño, no como accidente.
6. El último tramo (antes del NextTrigger al 2-4) es la combinación total: prepara al jefe.

## Día/noche (obligatorio)

- `start_hour`: `23:30` — continúa el reloj del 2-2 (terminó a las 23:30).
- `day_length`: 1000 s → termina a las **02:30**: madrugada cerrada, la luz más azul del juego.

## Enemigos (composición sugerida)

| Tipo | Cantidad mín. | Cantidad ref. | Rol en el nivel |
|---|---|---|---|
| `WalkerTerciopelo` | 6 | 7 | "Empleados del turno": patrulla agresiva entre cubículos |
| `ShooterVenomoLargo` | 2 | 3 | Largo alcance desde detrás de las particiones |
| `FlyingTerciovolador` | 2 | 2 | Sobre la altura de las particiones |

Total mínimo **10 enemigos**.

## Objetos y elementos

| Elemento | Cantidad | Nota |
|---|---|---|
| `PlayerSpawn` | 1 | Entrada del piso |
| `Checkpoint` | 2 | Mitad de cubículos + puerta de servidores (obligatorios) |
| `NextTrigger` | 1 | → 2-4 |
| `HazardZone` | 1+ | Donde se agrupan las serpientes (0.25) |
| `MessageTrigger` | 1 | Presenta el conteo de servidores (Unidad VIII) |
| Coleccionables | ≥ 5 | Tras las particiones y en los racks |
| `FG_Overlay` | libre | Cableado del techo |

## Mapa sugerido (canónico del Entregable 1)

```
 23:30 ── NOCHE CERRADA ─────► 02:30
 SPAWN ─[T][S][T]──[CP1]──[T][T][V]──[H]──[T][S][T][V]──[CP2]──[comb. total]── NEXTTRIGGER
   │        │       │        │                          │         │
 cubículos  particiones (sin colisión)   LED rojos      sala      examen: los 3 carriles
```
Leyenda: `[T]` terciopelo · `[S]` venomolargo · `[V]` terciovolador · `[H]` hazard.

## Checklist de cierre

- [ ] Tamaño ≥ 2400×608 px
- [ ] 3 tipos, ≥ 10 enemigos, combinación total solo al final
- [ ] `start_hour = 23:30` y `day_length = 1000`
- [ ] 2 checkpoints obligatorios; mecánica Unidad VIII viva
- [ ] `validate_tmx.py --ci` y `grade_stage.py` en verde

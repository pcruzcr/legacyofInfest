---
document_id: "LOI-LVL-2-2"
title: "Nivel 2-2 — Entrada y Antenas"
aliases: ["Stage 2-2", "Entrada y Antenas"]
tags: ["level", "entregable-2", "zona-2", "vertical"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/06_STAGE_2_2.md"
---

# NIVEL 2-2 — ENTRADA Y ANTENAS

**Entregable:** 2 (Evaluación Práctica II) · **Zona:** 2 — El Datacenter · **Tipo:** Travesía vertical (único con scroll vertical)

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★★☆☆ (3/5) |
| Tamaño mínimo | **1600 × 800 px** (100 × 50 tiles) |
| Tamaño de referencia | 1920 × 800 px (120 × 50 tiles, implementado) |
| Tipos de enemigo | 2 mínimos / 3 máximos |
| Enemigos mínimos | 8 (de referencia: 9) |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `Portal`, 5 coleccionables, 1 `CameraLock` |
| Día/noche | 20:30 → 23:30, `day_length` 1000 s |
| Clima | Libre (sugerencia: viento nocturno entre las antenas, luces de la ciudad a lo lejos) |
| Concepto académico | Unidad III (patrullas B-Spline alrededor de antenas) + Unidad IV (scroll vertical) |
| Límite de tiempo | 170 s |

## Reglas obligatorias

1. **El reloj continúa del 2-1**: `start_hour = 20:30` y `day_length = 1000` s → termina a las **23:30**.
2. **Sección vertical obligatoria** con `CameraLock` (lock_x=true, lock_y=false): la escalera de plataformas al menos **la mitad de la altura del mapa**.
3. **El castigo vertical es la caída**: los saltos de la escalera deben tener plataforma segura o daño, nunca vacío infinito.
4. La sección baja (estacionamiento/garita) es deliberadamente despejada: el precio de la sección vertical ya es alto.
5. Los voladores patrullan **alrededor de las antenas** (B-Spline/órbita): es la demostración de la Unidad III.

## Día/noche (obligatorio)

- `start_hour`: `20:30` — continúa el reloj del 2-1 (terminó a las 20:30).
- `day_length`: 1000 s → termina a las **23:30**: la noche cierra del todo durante el ascenso.

## Enemigos (composición sugerida)

| Tipo | Cantidad mín. | Cantidad ref. | Rol en el nivel |
|---|---|---|---|
| `WalkerGuardia` | 2 | 2 | Planta baja: patrulla la garita (despejado, presentación) |
| `FlyingBoa` o `FlyingTerciovolador` | 3 | 4 | Órbita alrededor de las antenas: 2 en base, 2 en azotea |
| `ShooterSerpienteArbol` o `ShooterVenomoLargo` | 2 | 3 | Cubre los dos saltos más largos de la escalera |

Total mínimo **8 enemigos**. Si se usan solo 2 tipos, el mínimo sube a 10.

## Objetos y elementos

| Elemento | Cantidad | Nota |
|---|---|---|
| `PlayerSpawn` | 1 | Estacionamiento, izquierda |
| `Checkpoint` | 1 | **Al pie de la escalera** (antes del bloque vertical, obligatorio) |
| `Portal` | 1 | Azotea → 2-3 |
| `CameraLock` | 1 | Al iniciar la escalera (lock_x=true) |
| `HazardZone` | 0–1 | Rejilla de calor de la azotea (opcional) |
| Coleccionables | ≥ 5 | Repartidos en la escalera (recompensan la altura) |
| `Platform` | 1+ | Plataformas de la escalera |

## Mapa sugerido (canónico del Entregable 1)

```
 20:30 ── NOCHE CAYENDO ────► 23:30
         [AZOTEA: antenas + voladores ×2 + tirador ×1] ── PORTAL
              ▲  escalera de plataformas (Platform)
              │  [CameraLock vertical aquí]
              │  tirador ×1 cubre el salto largo
              │  checkpoint al pie
 [garita]  [S]          [voladores ×2 orbitando antenas]
 SPAWN ────[guardia]───[guardia]─────────────────────► subir
          estacionamiento despejado (castigo = caída arriba)
```

## Checklist de cierre

- [ ] Tamaño ≥ 1600×800 px con sección vertical ≥ 50% de la altura
- [ ] ≥ 8 enemigos; voladores orbitando antenas (Unidad III)
- [ ] `start_hour = 20:30` y `day_length = 1000`
- [ ] CameraLock vertical + checkpoint al pie de la escalera
- [ ] `validate_tmx.py --ci` y `grade_stage.py` en verde

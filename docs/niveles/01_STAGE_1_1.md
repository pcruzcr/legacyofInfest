---
document_id: "LOI-LVL-1-1"
title: "Nivel 1-1 — La Entrada"
aliases: ["Stage 1-1", "La Entrada"]
tags: ["level", "entregable-1", "zona-1"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/01_STAGE_1_1.md"
---

# NIVEL 1-1 — LA ENTRADA

**Entregable:** 1 (Evaluación Práctica I) · **Zona:** 1 — Universidad Invenio · **Tipo:** Travesía de llegada

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★☆☆☆☆ (1/5) |
| Tamaño mínimo | **1600 × 608 px** (100 × 38 tiles, 2 pantallas) |
| Tamaño de referencia | 3840 × 640 px (240 × 40 tiles, implementado) |
| Tipos de enemigo | 2 mínimos / 3 máximos |
| Enemigos mínimos | 6 (de referencia: 11) |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `NextTrigger`, 5 coleccionables, 1 `MessageTrigger` |
| Día/noche | `morning` 10:00 → 14:00, `day_length` 900 s |
| Clima | Libre (sugerencia: niebla de montaña en el primer tercio) |
| Concepto académico | Unidad III (patrullas en Bézier) + Unidad VI (parallax) |
| Límite de tiempo | 180 s |

## Reglas obligatorias

1. **Es el nivel inicial de la Zona 1: declara dónde empieza el día.** `start_hour = "morning"` (10:00) es obligatorio.
2. **Sin fosos** (regla de zona): el castigo es el contacto con los enemigos. Las pendientes se suben con plataformas escalonadas.
3. **Primer encuentro presentado**: el primer caminante aparece en un tramo despejado y con su `MessageTrigger` (presenta el concepto de la unidad).
4. Las caídas de un solo sentido pueden existir (no se puede volver), pero nunca antes del primer checkpoint.
5. La canopea se dibuja como `FG_Overlay`: el bosque tapa al jugador, no a los enemigos.

## Día/noche (obligatorio)

- `start_hour`: `morning` (10:00) — **el nivel inicial indica dónde inicia**.
- `day_length`: 900 s (150 s estimados × 24 / 4 h) — termina a las **14:00**.
- El reloj corre visiblemente: la luz pasa de mañana a mediodía durante el nivel.

## Enemigos (composición sugerida)

| Tipo | Cantidad mín. | Cantidad ref. | Rol en el nivel |
|---|---|---|---|
| `WalkerInsect` (caminante) | 4 | 6 | Ritmo del suelo; patrulla el sendero y se da la vuelta en los bordes |
| `FlyingBird` (volador) | 2 | 3 | Ocupa el aire en los cruces de pantalla; ondas senoidales |
| `ShooterFrog` (tirador) | 0–1 | 2 | Solo en los tramos anchos; el primer tirador del juego debe estar sin otras amenazas |

Regla: el total mínimo es **6 enemigos**; si se usan 3 tipos, uno debe ser el
tercer carril (fondo) y su tramo debe quedar despejado de caminantes.

## Objetos y elementos

| Elemento | Cantidad | Nota |
|---|---|---|
| `PlayerSpawn` | 1 | Extremo izquierdo, fila 30 |
| `Checkpoint` | 1–2 | A la mitad (tras el tramo angosto) y opcional al final |
| `NextTrigger` | 1 | Extremo derecho → 1-2 |
| `MessageTrigger` | 1 | Antes del primer enemigo: presenta el concepto |
| Coleccionables | ≥ 5 | A lo largo del camino; 1-2 fuera de la ruta recta |
| `Terrain_Detail` | libre | Raíces y piedras decorativas |

## Mapa sugerido (canónico del Entregable 1)

```
10:00 ── DÍA ───────────────► 14:00
  x=48       160       288        528       736       992       1184     1472  1552
   │         │         │          │         │         │          │       │     │
 SPAWN ──A──[M]──B──[W]──C──[L]───D──[M]──E──[foso NO]─F──[V]────G──[tirolesa NO]──NEXTTRIGGER
   │         │  volador  │ liana   │   caminantes + rana            pájaros
  mensaje   primer      plataformas    llave/puerta        (sin fosos en Z1:
  (Message) caminante   de un sentido  (2ª solución)        alternativas de altura)
  Checkpoint tras C    Checkpoint en D
```

Leyenda: `[M]` mensaje · `[W]` walker · `[V]` volador · `[R]` rana. El nivel de
referencia implementado (240×40) es una versión extendida de este trazado.

## Checklist de cierre

- [ ] Tamaño ≥ 1600×608 px y suelo en y=480
- [ ] ≥ 6 enemigos, 2–3 tipos, primer encuentro despejado
- [ ] `start_hour = "morning"` y `day_length = 900`
- [ ] 1 PlayerSpawn, ≥ 1 Checkpoint, 1 NextTrigger, ≥ 5 coleccionables
- [ ] `validate_tmx.py --ci` y `grade_stage.py` en verde

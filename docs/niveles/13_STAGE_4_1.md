---
document_id: "LOI-LVL-4-1"
title: "Nivel 4-1 — La Entrada al Cementerio Sagrado"
aliases: ["Stage 4-1", "La Entrada al Cementerio Sagrado"]
tags: ["level", "zona-final", "atmospheric"]
description: "Ficha de nivel: dificultad, tamaño, secciones, día/noche y reglas obligatorias"
source: "docs/niveles/13_STAGE_4_1.md"
---

# NIVEL 4-1 — LA ENTRADA AL CEMENTERIO SAGRADO

**Entregable:** profesorado (no se asigna a estudiantes) · **Zona:** 4 —
El Cementerio Sagrado · **Tipo:** Travesía atmosférica (sin enemigos)

> **AUD-814 (2026-09-04).** Reconstrucción total desde cero: mapa, arte,
> audio, datos, lógica de fases y pruebas son nuevos. **AUD-815
> (2026-09-05).** Reconstrucción audiovisual: incendio por rayos con fin
> de lluvia y persecución, nubes sobre la luna, antorchas con templo de
> diez pasos, diálogos con retrato y voz, transiciones anticipadas.
> El diseño vive en `docs/STAGE_4_1_DESIGN.md`, la especificación técnica
> en `docs/STAGE_4_1_SPEC.md` y la certificación en
> `docs/STAGE_4_1_AUDIT.md`.

## 0. La promesa del nivel

Jhon y Jin atraviesan la memoria de los muertos en seis espacios reales:
cementerio a color, bosque del Venado en blanco y negro, osamentas de la
Serpiente en grises con tormenta, bosque talado del Halcón en ámbar
vintage, planicie nocturna de luna y camino verde hacia Paburu. Tres
espíritus se liberan por el camino; sólo con los tres libres Paburu puede
despertar. Cero enemigos: el terror es percepción, anticipación e
incertidumbre.

## 1. Geometría (contrato)

| Concepto | Valor |
|---|---|
| Mapa | `assets/maps/stage4_1/stage4_1.tmx`, 960×40 baldosas (15360×640 px) |
| Secciones | 6 × 160 columnas: F1 0–159 … F6 800–959 |
| Suelo | fila 32 (y = 512), sin fosos por construcción |
| Elevaciones | repiso F2 (col 288) + dos lomas F3 (cols 350 y 408) |
| Pendientes | 9 `Slope`: 6 rampas + 3 cimas llanas (patrón AUD-477) |
| Bases de seguridad | 3 `Solid` bajo las elevaciones (anti-caída al vacío) |
| Checkpoints | 7 (cols 12, 172, 332, 492, 652, 812, 932) |
| Capas | `BG_Far/Mid/Near`, `Terrain`, `Terrain_Detail`, `FG_Overlay`, `Collision`, `Objects` |
| Salida | `WarpZone` a `boss_paburu` con llave `paburu_despertado` (sin `NextTrigger`: la salida es causal, no automática) |

## 2. Reglas obligatorias

1. **Cero enemigos.** Las presencias son contornos sin colisión ni IA.
2. **Tres liberaciones o no hay despertar.** Llaves `espiritu_venado`,
   `espiritu_serpiente`, `espiritu_halcon` → llave `paburu_despertado`;
   banderas `stage4_1.*` persistidas en el save.
3. **El altar no libera sin diálogo.** Cada espíritu debe hablar primero
   (árboles `venado`, `serpiente`, `halcon` en
   `data/dialogues/stage4_1.json`).
4. **Todo el audio requerido existe.** Seis músicas `mus_stage41_f1..6`,
   seis ambientes `amb_stage41_f1..6`, seis efectos `s41_*`. Ningún
   `resolver()` puede devolver `None` para ellos (prueba dedicada).
5. **Las cimas se coronan saltando.** La cara empinada de una pendiente es
   un muro por diseño del motor; las rampas se suben caminando.
6. **Los protagonistas son Jhon y Jin.**

## 3. Día, clima y luz

Hora inicial 10:00, día largo (3600 s): la luz la manda cada fase, no el
reloj. F1 despejado, F2 lluvia, F3 tormenta, F4 lluvia, F5 despejado
nocturno (luna 0.45–0.75 sobre el suelo del motor), F6 niebla. Propiedad
`cielo=true` obligatoria: sin ella el motor cree que es interior y anula
el clima.

## 4. Easter egg

Dos lápidas cuidadas en la F1, con diálogo propio: M. Tilarán, el
campanero (col 44) y R. Arenal, la maestra (col 50).

## 5. Dificultad

Zona 4: tramos largos entre checkpoints por decisión (métrica, no regla).
Sin saltos de precisión salvo las cimas; el reto es atención y ritmo, no
combate. Peor hueco entre checkpoints medido por `grade_stage.py`.

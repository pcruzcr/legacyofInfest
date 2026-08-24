---
document_id: "LOI-CIERRE-94"
title: "Cierre de gaps y plan por fases — estado verificado del árbol"
tags: ["plan", "gaps", "cierre", "auditoria", "hoja-de-ruta"]
source: "docs/94_CIERRE_DE_GAPS_Y_PLAN_POR_FASES.md"
---

# Cierre de gaps y plan por fases

**Fecha:** 20 de agosto de 2026
**Método:** cada fila de este documento se verificó ejecutando el validador o
la suite correspondiente el mismo día; no sale de leer documentación. Donde no
ejecuté algo, lo digo.

---

## 0. Resumen ejecutivo

La auditoría más reciente (`docs/93`, 2026-08-19) describía una foto del árbol.
Después de ella el repo avanzó y **la mayoría de sus hallazgos ya están
resueltos en el árbol actual** (commits AUD-586, AUD-587, AUD-598, AUD-601).
Lo que sigue abierto se divide en tres frentes: trabajo de la rama activa
(zona 4), decisiones del dueño y un paquete de contenido barato.

Las tres fases de *higiene de suite* que este documento planifica **se
ejecutaron y quedaron en verde**:

| Ítem | Antes | Después | Evidencia |
|---|---|---|---|
| `test_el_mirador_de_la_fase_6.py` (fallo estable de 93 §11) | fallaba | **7 passed** | `pytest tests/test_el_mirador_de_la_fase_6.py` |
| `test_particion_de_stage_scene[senales]` (fallo estable) | fallaba (413 líneas) | **114 passed** — `senales.py` a 368, botín a `economia.py` | `pytest` partición + monedas + habilidades |
| `test_salida_de_consola[generate_all_assets]` (fallo estable) | fallaba (`UnicodeEncodeError`) | **50 passed** | `pytest tests/test_salida_de_consola.py` |

## 1. Estado de los validadores de CI (ejecutados hoy)

| Validador | Comando | Resultado |
|---|---|---|
| `validate_tmx.py --ci` | `python scripts/validate_tmx.py --ci` | **22/22 OK** |
| `validate_assets.py --ci` | `python scripts/validate_assets.py --ci` | **0 errores, 0 avisos** |
| `check_orphan_systems.py --ci` | `python scripts/check_orphan_systems.py --ci` | **verde** |
| `check_doc_symbols.py --ci` | `python scripts/check_doc_symbols.py --ci` | **469 símbolos citados, 0 sin existir** |
| `check_tmx_coverage.py --ci` | `python scripts/check_tmx_coverage.py --ci` | Cobertura correcta (74/74) |
| `check_translations.py --ci` | `python scripts/check_translations.py --ci` | Catálogos en orden (asimetría es/en es decisión) |

## 2. Hallazgos de `93` §6 — estado real

| ID | Hallazgo | Estado hoy |
|---|---|---|
| F1 | PNGs con perfil sRGB (iCCP) | ✅ Resuelto — `validate_assets` da 0 avisos |
| F2 | `professor_sample.pkl` con `pickle` | ✅ Resuelto (AUD-587): dataset con `np.load(allow_pickle=False)` |
| F3 | `grade_stage` suspendía arenas sin NextTrigger | ✅ Resuelto (AUD-586) |
| F4 | Checkpoints 2400–2688 px en 4-1 y variantes | Parcial: **4-1b a 7 por evento**; pendiente pacing de 4-1/4-1c |
| F5 | `computer-vision-course/` sin seguimiento | **Decisión del dueño** (A7) |
| F6 | Catálogos de traducción asimétricos | **Decisión del dueño** (español único desde AUD-455) |
| F7 | `1-1` registra tipos en función | Nota: usa `ShooterFrog`/`FlyingBird` (especies reales); aviso residual cosmético |
| F8 | `BossSpawn` sin uso directo | ✅ Documentado como indirecto (no es gap) |

---

## 3. Fases resueltas en este documento

### Fase H1 — salida de consola en Windows
`tools/generate_all_assets.py` imprimía `→` y moría con `UnicodeEncodeError`
en consola Windows. Se añadió junto a los imports el patrón del resto de
herramientas:

```python
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
```

### Fase H2 — la partición de `StageScene` (AUD-152) volvía a pinchar
`senales.py` rozaba su presupuesto (413 de 400 líneas). Se extrajo
`_soltar_botin`/`_BOTIN_TAM` a un mixin nuevo **`EconomiaDeEscenario`** en
`stage_parts/economia.py`. `senales.py` quedó en 368 y el presupuesto en
verde.

### Fase H3 — el mirador de la Fase 6 (GAP-064 punto 17)
`test_el_mirador_de_la_fase_6.py` quedó en verde (7): el guion cumple ya el
contrato de 2 movimientos de cámara + 1 espera + 2 fundidos.

---

## 4. GAPs formales que siguen abiertos en `KNOWN_GAPS.md`

Son 13. Todos tienen dueño o plan.

| GAP | Asunto | Estado |
|---|---|---|
| GAP-058 | `stage4_1`: arte final, diálogo, reverberación | rama activa |
| GAP-059 | Fase 1: anomalía de fondo, memoria espacial, capas sonoras | rama activa |
| GAP-060 | Fase 2: fricción sistémica, venado, progresión | rama activa |
| GAP-061 | Fase 3: viento/rayo/osamentas | rama activa |
| GAP-062 | Fase 4: sonido direccional, quietud | rama activa |
| GAP-063 | Fase 5: luna, eventos de oscuridad, navegación | rama activa |
| GAP-064 | Fase 6: silueta Paburu, despedida, despertar | **mirador parcial** (H3); resto rama activa |
| GAP-065 | `stage4_1` sistema: relación jugador↔escenario | rama activa |
| GAP-067 | stinger y risa de Paburu (placeholders) | audio de autor |
| GAP-068 | pistas `_combat` de `DynamicMusicSystem` | audio |
| GAP-070 | audio procedural con DSP en tiempo real | audio |
| GAP-072 | 4-1b blueprint 10/10 | **avanzado** (AUD-598/601); falta corriente vertical, música/luz por zona |

---

## 5. Decisiones que sólo puede tomar el dueño (no se implementan)

| # | Pregunta | Recomendación |
|---|---|---|
| A1 | ¿Se fija la versión de las herramientas de lint? | Sí, un commit al mes |
| A7 | `computer-vision-course/` (8 MB): ¿`.gitignore` o fuera? | `.gitignore` si sigue; sacar si es otro proyecto |
| B7 | `17_BOSS_SPEC.md`: ¿especificación o catálogo? | Catálogo |
| C1 | Un sonido crítico ¿puede quedar mudo por distancia? | No, suelo de atenuación en la ruta crítica |
| D2 | 4 mapas sin checkpoint: ¿motor o nota del alumno? | Nota del alumno |
| P4 | GAP-024 salto aéreo sin conectar (congelado) | Decisión docente: no se toca |
| P5 | `1-3` y `2-1` con poca densidad de checkpoint | Decisión docente (rúbrica) |

---

## 6. Contenido futuro (backlog barato, no bloquea)

De `93` §9 (B1–B12) y `90` §4:

- B1/B2/B4/B5: NG+, % de ítems por escenario, fogata TMX, piezas de corazón.
- `90` §4: la Planicie 2-1, jefes Gavilán/Terciopelo fases 2-3, el bestiario.

---

## 7. Plan por fases (orden de cierre)

### R-Z (contenido de la rama) · GAP-059…065 y F4 de 4-1/4-1c
Cerrar el cementerio GAP por GAP, cada uno con su antes/después. Después el
4-2 Paburu.

### R-C (audio) · GAP-067, 068, 070, C1
Placeholders de audio de autor y la pista por distancia.

### R-M (motor · GAP-072 restos)
Corriente vertical, música por zona y luz por zona en el 4-1b.

### R-D (decisiones)
Pase del dueño sobre la §5 para dejar `KNOWN_GAPS.md` sin entrada abierta sin
decisión fechada.

---

## 8. Cierre

Condición de parada (heredada de `91_PLAN_DE_CIERRE.md`):

> Todo ítem abierto está cerrado con su prueba, convertido en decisión fechada
> del dueño, o protegido por invariante.

```bash
python scripts/validate_tinx.py --ci    # 22/22
python scripts/validate_assets.py --ci  # 0 errores
python scripts/check_orphan_systems.py --ci   # verde
python scripts/check_doc_symbols.py --ci      # 0 símbolos fantasma
python scripts/check_tinx_coverage.py --ci    # 74/74
python scripts/check_translations.py --ci     # catálogos en orden
```

---

## Documentos relacionados

- `KNOWN_GAPS.md` — GAP-058..072
- `docs/91_PLAN_DE_CIERRE.md` — el plan heredado
- `docs/93_AUDITORIA_ESTRATEGICA_Y_FODA.md` — F1..F8 y B1..B12
- `docs/90_INVENTARIO_DE_LEVEL_DESIGN.md` — espacios abiertos
- `docs/89_AUDITORIA_MULTIDISCIPLINAR.md` §6 — P4/P5/P7
- `CLAUDE.md` §5 — invariantes y reglas de commit
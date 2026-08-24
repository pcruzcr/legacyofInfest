# Auditoría de juego — índice

> Generado por `scripts/generar_reporte_auditoria_juego.py`. Los números se
> miden en vivo de los TMX; la batería que los respalda vive en
> `tests/test_auditoria_juego/` (245 pruebas: 2 hallazgos reales como
> `xfail`, 11 skips documentados).

## Resumen ejecutivo

- **Niveles auditados:** 21 TMX (16 en campaña,
  5 laboratorios, 4 jefes).
- **Salidas alcanzables:** 10/16 con salida
  (2 marcadas inalcanzables por el analizador).
- **Falsos negativos del analizador estático** (no modela plataformas
  one-way ni mecánicas dinámicas): stage0, hall, stage_mecanicas,
  stage4_1c_a/b/c.
- **Hallazgos reales pendientes de decisión del dueño:**
  1. `stage2_1_oficinas`: **0 checkpoints en 3200 px** (gap 3048 px ≈ 33 s).
  2. `boss_paburu`: **NextTrigger fantasma en y=-64** (fuera del mapa).
- **Gaps de checkpoint > 1200 px por decisión documentada (AUD-516):**
  stage4_1, stage4_1b, stage4_1c_a/b/c.
- **Contenido incompleto:** jefe Gavilán (~45 % rúbrica, Fase 1 sola;
  ver GAP-058..065 y `docs/87_REPORTE_DE_LO_QUE_FALTA.md`).
- **Escenas UI/UX:** 35 escenas + 19 escenarios verificados con arnés de
  juego real. 7 menús no tienen datos en el estado inicial del arnés (0
  partidas / bestiario vacío / 0 logros / 0 puntuaciones / sin progreso /
  inventario vacío): los skips de la batería documentan el vacío.

## Documentos

| Fichero | Contenido |
|---|---|
| `00_indice.md` | Éste: resumen y mapa del reporte |
| `01_analisis_niveles.md` | Tabla de los 21 TMX + análisis por nivel |
| `02_analisis_escenas_ui_ux.md` | Las 35 escenas + 19 escenarios, uno por uno |
| `03_plan_de_mejora.md` | Prioridades y fases para mejorar el juego |
| `04_analisis_profundo.md` | Auditoría profunda (8 dimensiones del proyecto) |

## Cómo se midió

- `StageLoader.load()` + `analyse_stage()` (`src/framework/stage/level_metrics.py`,
  AUD-049): alcanzabilidad de la salida, repechos, gaps de checkpoint.
- Densidad de terreno: fracción de celdas sólidas de la capa `Terrain`.
- Arnés de escenas: ciclo de vida real (`awake/start/on_enter/update/draw/
  on_exit/destroy`), 60+ fotogramas por acción de menú, ocupación por
  muestreo jitter determinista (no se alinea con el contenido).
- Regla del repo respetada: **ningún cambio al juego; esto es auditoría.**

## Inconcluso (ver `03_plan_de_mejora.md`)

- `stage_mecanicas` (ver análisis en `01_analisis_niveles.md`)
- `hall` (ver análisis en `01_analisis_niveles.md`)
- `stage4_1c_a` (ver análisis en `01_analisis_niveles.md`)
- `stage4_1c_b` (ver análisis en `01_analisis_niveles.md`)
- `stage4_1c_c` (ver análisis en `01_analisis_niveles.md`)

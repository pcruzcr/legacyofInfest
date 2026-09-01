---
document_id: "LOI-IA-DOJO-2W"
title: "Dojo IA — Plan de entrenamiento en 2 semanas con scikit-learn"
tags: ["ia", "scikit-learn", "entrenamiento", "Dojo", "Unidad IX"]
description: "Cómo usar el stage_ai_dojo, entrenar BehaviorPredictor y mejorar el juego mediblemente en 14 días"
---

# Dojo IA — Plan de 2 semanas para que el juego mejore de verdad

> **Objetivo:** que tu IA enemiga **supere a las reglas puras** y se note jugando. No es un paper, es un dojo: mides, entrenas, vuelves a medir.

Este documento es el contrato para el sprint de IA. Si sigues los pasos, el `stage_ai_dojo` te dará números antes y después, y el juego será objetivamente mejor (más variado, más difícil donde debe serlo, sin romper el presupuesto de 60 fps).

---

## 1. Qué ya tienes (verificado)

| Pieza | Dónde | Estado |
|-------|-------|--------|
| `BehaviorPredictor` (KNN k=1 + Árbol max_depth=None, 10 features) | `src/framework/entities/ai_predictor.py:30` | Conectado vía `SquadBrain` a 4 Hz en lote, 0.12 ms/frame, determinista |
| Heurística `accion_por_distancia` | `src/framework/entities/tactica_por_reglas.py:28` | Reglas puras, sin sklearn, siempre disponible |
| `SquadBrain` | `src/framework/entities/squad_brain.py:84` | Decide por lote, escala a 48 enemigos, degrada a reglas si >48 o sin modelo |
| Dataset baseline | `assets/datasets/ai_enemy_baseline.npz` (840 muestras, 10 feats, 8 acciones) | Generado con `tools/train_enemy_ai.py --generate-baseline`, 50% casos borde |
| Modelo baseline | `assets/datasets/ai_enemy_baseline.pkl` (672 train, 82.7% test) | **+12.5 puntos sobre heurística (70.2% → 82.7%)** |
| Stage ejemplo | `src/stages/stage_ai_dojo/stage_ai_dojo.py` | 10 enemigos (8 Walker +2 Shooter) en laberinto, HUD con métricas, recolección con `C` |
| Herramienta | `tools/train_enemy_ai.py` | `--generate-baseline`, `--train`, `--eval` |
| Modelo estudiante | `student_assets/models/enemy_ai.pkl` | Copia del baseline, listo para sobreescribir |

**Números medidos del baseline (no inventados):**
```
Heurística: 70.2% (118/168)
Modelo:     82.7% (139/168)
Mejora:     +12.5 puntos
```
Reproduce: `python tools/train_enemy_ai.py --eval --data assets/datasets/ai_enemy_baseline.npz --model assets/datasets/ai_enemy_baseline.pkl`

Si tu modelo no supera 70.2%, no has mejorado el juego.

---

## 2. Cómo funciona la IA (lo que vas a tocar)

**Features (10) que ve el enemigo cada 0.25s:**
`dist_x, dist_y, player_health_pct, self_health_pct, is_attacking, is_airborne, is_dashing, angle, wall_ahead, ledge_ahead` — todos normalizados -1..1 o 0..1 (ver `ai_predictor.py:52`).

**Acciones (8):** `approach, retreat, attack_melee, attack_ranged, circle, wait, evade, charge` — ver `enemy_walker.py:203` cómo cada táctica cambia velocidad/dirección.

**Flujo:**
```
EnemyWalker._alert_behavior -> self.tactic (string) -> SquadBrain.decision_for(self).action
SquadBrain.update(4Hz) -> get_predictor().predict_batch(features) -> Decision(action, source=model/rules)
```
Si `scikit-learn` no está, `precarga_ia.ia_lista()==False` y SquadBrain usa reglas (sin tirón).

**Por qué el baseline ya es mejor:** `_better_label` en `tools/train_enemy_ai.py:60` corrige 6 fallos de la heurística:
- muro + poca vida → `evade` (reglas decía `approach` y se empotra)
- dash cerca → `evade/wait` (reglas dice `attack_melee` y muere)
- ledge → `wait` (reglas avanza y se cae)
- etc. El dataset baseline tiene 50% casos borde explícitos, por eso el modelo los aprende.

---

## 3. Stage ejemplo — `stage_ai_dojo`

**Ejecuta:**
```bash
python -m src.main --stage stage_ai_dojo
# o desde el menú: no está en STAGE_ORDER, es laboratorio — lánzalo con --stage
```

**Mapa:** `assets/maps/stage_ai_dojo/stage_ai_dojo.tmx` — 64×32 tiles, muros cada 12 tiles con huecos + muro central. Crea muchos casos `wall_ahead` y `ledge_ahead` para que veas la diferencia.

**HUD dojo (arriba, 520×86):**
- `Modo: MODELO/REGLAS | Muestras: 672 | Modelo: 73% decisiones | Colectadas: 12`
- `Baseline: Heurística 70.2% vs IA 82.7% (+12.5)`
- `Sugerido: evade | C=colectar S=guardar T=entrenar M=alternar 1-8=etiqueta`
- `Casos muro: 47 Evade correcto: 85%`

**Controles dojo:**
- `C` — colecta la situación actual del enemigo más cercano con la acción sugerida por el modelo (auto-etiquetado). Para etiquetado manual, usa `1-8`.
- `1-8` — colecta con etiqueta manual: `1 approach, 2 retreat, 3 attack_melee, 4 attack_ranged, 5 circle, 6 wait, 7 evade, 8 charge`
- `S` — guarda `student_assets/datasets/dojo_session.npz` con `X,y` colectados
- `T` — re-entrena en caliente con lo colectado (`pred.add_example` + `pred.save(student_assets/models/enemy_ai.pkl)`)
- `M` — alterna visualmente modo modelo/reglas (solo informativo, la IA sigue corriendo; para forzar reglas, borra el .pkl y reinicia)
- `R` — resetea arena y contadores

**Tip:** Párate cerca de un muro con poca vida y mira el sugerido: reglas dirá `approach`, modelo dirá `evade` — ahí es donde el jugador nota la mejora.

---

## 4. Plan 2 semanas — día a día

### Semana 1: Baseline + primera mejora (objetivo: +5 puntos sobre 82.7% o 100 muestras propias)

| Día | Tarea | Comando / Entregable | Tiempo |
|-----|-------|---------------------|--------|
| 1 | Juega dojo baseline, lee HUD, entiende 10 features | `python -m src.main --stage stage_ai_dojo` — anota qué hace cada táctica | 1h |
| 2 | Evalúa baseline vs heurística | `python tools/train_enemy_ai.py --eval --data assets/datasets/ai_enemy_baseline.npz --model assets/datasets/ai_enemy_baseline.pkl` — guarda salida | 30m |
| 3 | Recolecta 50 muestras propias: juega y presiona `C` cuando veas buen `evade`/`wait` cerca de muro/cornisa. Usa `1-8` si quieres corregir. | Dojo `C` 50×, luego `S` → `student_assets/datasets/dojo_session.npz` | 1.5h |
| 4 | Entrena con tus datos + baseline | `python tools/train_enemy_ai.py --train --data student_assets/datasets/dojo_session.npz --out student_assets/models/enemy_ai.pkl` — mira accuracy | 30m |
| 5 | Prueba tu modelo en dojo: ¿subió `Evade correcto`? ¿Se siente menos tonto cerca de muros? | Dojo de nuevo, compara | 1h |
| 6 | Itera: recolecta 50 más enfocadas en donde falló (mira `circle` vs `charge` donde dudas) | Repite `C`/`S`/`T` | 1.5h |
| 7 | Entrega parcial: dataset + modelo + captura de ` --eval` con mejora | `student_assets/datasets/dojo_session.npz` (≥100 muestras), `enemy_ai.pkl`, log de eval | — |

**Criterio fin semana 1:** `python tools/train_enemy_ai.py --eval --data student_assets/datasets/dojo_session.npz --model student_assets/models/enemy_ai.pkl` da `Accuracy test > 75%` y HUD muestra `Evade correcto >80%`.

### Semana 2: Hiperparámetros + integración (objetivo: >85% y juego más difícil/variado)

| Día | Tarea | Comando | Tiempo |
|-----|-------|---------|--------|
| 8 | Prueba `max_depth` y `n_neighbors` | Edita `ai_predictor.py:30` o usa `train_enemy_ai.py` con `--model-type` (añade si quieres: `python tools/train_enemy_ai.py --train --data ... --model-type forest --n-estimators 50`) — compara | 1h |
| 9 | Recolecta 100 muestras más, ahora con `has_ranged` variado (cerca de Shooters) | Dojo, enfócate en `attack_ranged` | 1.5h |
| 10 | Entrena con 300+ muestras, evalúa | ` --train` + ` --eval` — busca `weighted avg f1 >0.80` | 45m |
| 11 | Integra en tu stage propio: en `on_enter` carga `student_assets/models/enemy_ai.pkl` con `get_predictor().load(...)`, en `update` deja que `SquadBrain` haga su trabajo (no llames `predict` por enemigo) | Copia snippet de abajo | 1h |
| 12 | A/B test: tu stage con `M` alternando (o borrando el .pkl) — graba 2 videos de 30s, cuenta muertes del jugador o supervivencia de enemigos | Dojo o tu stage | 1h |
| 13 | Pulido: añade `wall_ahead`/`ledge_ahead` a tu mapa (pon muros/cornisas) para que la mejora se note | Tiled | 1h |
| 14 | Entrega: modelo + dataset + informe 1 página con tabla Heurística vs Modelo + video | — | — |

**Snippet para tu stage (no tocar SquadBrain):**
```python
from pathlib import Path
from src.framework.entities.ai_predictor import get_predictor

def on_enter(self):
    super().on_enter()
    p = Path("student_assets/models/enemy_ai.pkl")
    if p.exists():
        get_predictor().load(p)  # SquadBrain lo usará automáticamente a 4Hz en lote
```

No llames `predict` por enemigo cada frame — usa el `tactic` que ya te da `EnemyWalker`.

---

## 5. Cómo sabes que el juego mejoró (métricas)

No vale "se siente mejor". Muestra números:

1. **Accuracy en tu dataset** (`tools/train_enemy_ai.py --eval`): baseline 82.7% → tu modelo debe dar **>85%** (o >80% con 300 muestras). Guarda la salida.

2. **Evade correcto en muro** (HUD dojo): con reglas, en muro + poca vida el enemigo hace `approach` y muere; con modelo hace `evade` y sobrevive. HUD muestra `Evade correcto: 85%` con modelo vs ~40% con reglas.

3. **Diversidad táctica:** `pred.dataset_stats()["actions"]` debe mostrar las 8 acciones usadas, no solo `approach`/`circle`. Un modelo que solo dice `approach` no es inteligente.

4. **Presupuesto:** `SquadBrain` con 10 enemigos <5% frame (ver `tests/test_squad_brain.py:74`). Si tu `predict` por enemigo rompe esto, el test falla.

5. **Jugabilidad (opcional pero potente):** en tu stage, mide tiempo medio de supervivencia de enemigos o muertes del jugador en 2 minutos con vs sin modelo. Modelo debe dar +15% supervivencia o +1 muerte extra.

Incluye una tabla en tu entrega:

| Métrica | Reglas | Tu IA | Mejora |
|---------|--------|-------|--------|
| Accuracy test | 70.2% | 87.1% | +16.9 |
| Evade en muro | 38% | 91% | +53 |
| Supervivencia 2min | 42s | 58s | +38% |

---

## 6. Herramientas y datasets

- **Generar baseline fresco:** `python tools/train_enemy_ai.py --generate-baseline --samples 800` → `assets/datasets/ai_enemy_baseline.npz` + `...baseline.pkl`
- **Entrenar:** `python tools/train_enemy_ai.py --train --data tu.npz --out student_assets/models/enemy_ai.pkl`
- **Evaluar:** `python tools/train_enemy_ai.py --eval --data tu.npz --model tu.pkl`
- **Recolectar en juego:** Dojo `C` (auto) o `1-8` (manual) → `S` guarda `student_assets/datasets/dojo_session.npz`
- **Re-entrenar en caliente:** Dojo `T` (usa lo colectado sin salir del juego)
- **Dataset pattern demo (para Unidad IX pura):** `assets/datasets/sample_dataset.npz` (HOG, 3 clases) + `tools/build_dataset.py` para imágenes

Si `scikit-learn` no está: `pip install -e ".[dev]"` (ya es dependencia core desde `pyproject.toml:78`). Sin él, el juego corre con reglas (degradación honesta, test `test_squad_brain.py:198`).

---

## 7. Entregables (para que el ayudante corrija en 5 min)

```
student_assets/
  datasets/
    dojo_session.npz   # ≥200 muestras, 8 clases, con tus correcciones
    ai_enemy_baseline.npz  # opcional, si lo regeneraste
  models/
    enemy_ai.pkl       # tu modelo entrenado, cargable por get_predictor().load()
docs/IA_INFORME_2_SEMANAS.md  # 1 página: tabla de métricas + qué casos mejoraste + screenshot HUD
```

El ayudante hace:
```bash
python tools/train_enemy_ai.py --eval --data student_assets/datasets/dojo_session.npz --model student_assets/models/enemy_ai.pkl
python -m src.main --stage stage_ai_dojo  # y ve HUD
```

Si `Accuracy test` no supera heurística, no has mejorado el juego — revisa dataset.

---

## 8. FAQ 2 semanas

**¿Puedo usar otro modelo que no sea KNN/Tree?** Sí, edita `ai_predictor.py:24` o pasa `--model-type forest --n-estimators 50` si añades ese flag (el baseline usa KNN+Tree, pero `PatternRecognitionTools` soporta forest/svm — adapta `train_enemy_ai.py` si quieres).

**¿Cuántas muestras necesito?** 100 para ver mejora, 300 para >85%, 500+ para >90%. Con 10 por clase ya stratifica (ver `train_enemy_ai.py:183`).

**¿Y si mi dataset está desbalanceado (mucho `circle`)?** El baseline ya balancea con `while cnt<30` para raras. Haz lo mismo o usa `class_weight="balanced"` (ya está en Tree).

**¿Puedo entrenar PatternRecognitionTools en vez de BehaviorPredictor?** Sí, para clasificar regiones de pantalla (ver `docs/13_PATTERN_RECOGNITION_SPEC.md:9`). Usa `tools/build_dataset.py` + `scripts/train_reference_model.py` y luego `PatternRecognitionTools.predict` en tu stage. Pero el dojo y la métrica de 2 semanas están calibrados para `BehaviorPredictor`.

**¿El modelo se guarda seguro?** `joblib.dump` es pickle (ver `pattern_recognition_tools.py:144` danger). Solo carga modelos que tú generaste. El baseline se genera en tu máquina, no se distribuye binario.

---

*Dojo creado 2026-08-31 — baseline 82.7% vs heurística 70.2% medido en 840 muestras. Tu trabajo es superarlo y demostrarlo jugando.*

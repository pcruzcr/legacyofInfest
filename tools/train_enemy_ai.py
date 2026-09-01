#!/usr/bin/env python3
"""
Entrenamiento de IA enemiga en 2 semanas — BehaviorPredictor con scikit-learn

Uso rápido (el juego mejora en minutos):
    # 1. Generar dataset baseline (500 muestras, ya mejor que reglas puras)
    python tools/train_enemy_ai.py --generate-baseline

    # 2. Entrenar y guardar modelo estudiante
    python tools/train_enemy_ai.py --train \
    --data assets/datasets/ai_enemy_baseline.npz --out student_assets/models/enemy_ai.pkl  # noqa: E501

    # 3. Evaluar: compara reglas vs modelo en casos difíciles
    python tools/train_enemy_ai.py --eval \
    --data assets/datasets/ai_enemy_baseline.npz --model student_assets/models/enemy_ai.pkl  # noqa: E501

    # 4. Probar en juego:
    python -m src.main --stage stage_ai_dojo

Flujo estudiante (2 semanas):
    Semana 1: entiende baseline, juega dojo, recolecta 100 muestras propias con 'C' (corrige la IA), genera dataset
    Semana 2: entrena, itera hiperparámetros, mide mejora >10% en evaluación, entrega modelo + informe
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.entities.ai_predictor import BehaviorPredictor
from src.framework.entities.tactica_por_reglas import accion_por_distancia

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "dist_x", "dist_y", "player_health_pct", "self_health_pct",
    "player_is_attacking", "player_is_airborne", "player_is_dashing",
    "angle_to_player", "wall_ahead", "ledge_ahead",
]
ACTION_NAMES = [
    "approach", "retreat", "attack_melee", "attack_ranged",
    "circle", "wait", "evade", "charge",
]

def _heuristic_label(feat: list[float], has_ranged: bool = False) -> str:
    """Reglas puras (baseline) — lo que SquadBrain hacía antes de IA."""
    # Reconstruye dist/health desde features normalizados
    dx = feat[0] * 300.0
    dy = feat[1] * 200.0
    dist = (dx*dx + dy*dy)**0.5
    health_pct = feat[3]  # self_health_pct ya es 0..1
    player_health_pct = feat[2]
    return accion_por_distancia(dist, health_pct, player_health_pct, has_ranged)

def _better_label(feat: list[float], has_ranged: bool = False) -> str:
    """Etiqueta mejorada: corrige los fallos de la heurística en casos borde.
    
    Estos son los casos donde la IA entrenada debe superar a las reglas:
    - Pared delante + poca vida -> evade (reglas a veces dice approach)
    - Jugador en dash + cerca -> evade/wait (reglas dice attack_melee y muere)
    - Jugador en aire + enemigo con rango -> attack_ranged (reglas dice circle)
    - Vida alta + distancia media sin rango -> charge (reglas dice approach)
    """
    dx = feat[0] * 300.0
    dy = feat[1] * 200.0
    dist = (dx*dx + dy*dy)**0.5
    health_pct = feat[3]
    player_attacking = feat[4] > 0.5
    player_airborne = feat[5] > 0.5
    player_dashing = feat[6] > 0.5
    wall_ahead = feat[8] > 0.5
    ledge_ahead = feat[9] > 0.5

    # Caso 1: muro delante + poca vida -> evade siempre (mejor que approach)
    if wall_ahead and health_pct < 0.4 and dist < 100:
        return "evade"
    # Caso 2: jugador dashing cerca -> wait/evade, no atacar de frente
    if player_dashing and dist < 80:
        return "evade" if health_pct < 0.5 else "wait"
    # Caso 3: jugador en aire + tengo rango -> attack_ranged
    if player_airborne and has_ranged and dist < 150:
        return "attack_ranged"
    # Caso 4: cornisa delante -> wait/circle, no avanzar y caerse
    if ledge_ahead and dist < 120:
        return "wait"
    # Caso 5: jugador atacando cerca + poca vida enemiga -> retreat
    if player_attacking and dist < 50 and health_pct < 0.5:
        return "retreat"
    # Caso 6: vida alta + distancia media -> charge es mejor que approach
    if health_pct > 0.7 and 60 < dist < 140 and not has_ranged:
        return "charge"
    # Fallback a heurística base
    player_health_pct = feat[2]
    return accion_por_distancia(dist, health_pct, player_health_pct, has_ranged)

def _random_feat(rng: np.random.RandomState) -> list[float]:
    dx = rng.uniform(-250, 250)
    dy = rng.uniform(-150, 150)
    return [
        dx / 300.0, dy / 200.0,
        rng.uniform(0.1, 1.0), rng.uniform(0.1, 1.0),
        float(rng.choice([0, 1], p=[0.7, 0.3])),
        float(rng.choice([0, 1], p=[0.8, 0.2])),
        float(rng.choice([0, 1], p=[0.85, 0.15])),
        rng.uniform(-1.0, 1.0),
        float(rng.choice([0, 1], p=[0.7, 0.3])),
        float(rng.choice([0, 1], p=[0.85, 0.15])),
    ]

def _edge_feat(rng: np.random.RandomState, case: int) -> list[float]:
    # Genera un caso borde específico para que _better_label difiera de _heuristic
    if case == 0:  # muro + poca vida -> evade
        return [rng.uniform(-0.2, 0.2), rng.uniform(-0.1, 0.1), 0.5, rng.uniform(0.1, 0.35), 0, 0, 0, rng.uniform(-0.3, 0.3), 1.0, 0]
    if case == 1:  # dash cerca -> evade/wait
        return [rng.uniform(-0.2, 0.2), rng.uniform(-0.1, 0.1), 0.6, rng.uniform(0.2, 0.6), 0, 0, 1.0, rng.uniform(-0.5, 0.5), 0, 0]
    if case == 2:  # ledge -> wait
        return [rng.uniform(0.1, 0.3), rng.uniform(-0.1, 0.1), 0.7, 0.6, 0, 0, 0, 0, 0, 1.0]
    if case == 3:  # atacando cerca + poca vida -> retreat
        return [rng.uniform(-0.08, 0.08), rng.uniform(-0.05, 0.05), 0.5, rng.uniform(0.15, 0.35), 1.0, 0, 0, 0, 0, 0]
    if case == 4:  # vida alta media -> charge
        return [rng.uniform(0.2, 0.4), rng.uniform(-0.1, 0.1), 0.8, rng.uniform(0.75, 0.95), 0, 0, 0, 0, 0, 0]
    # airborne + rango -> attack_ranged (has_ranged True, pero como feature no lo distingue, usamos airborne)
    return [rng.uniform(0.2, 0.4), rng.uniform(-0.1, 0.1), 0.6, 0.8, 0, 1.0, 0, rng.uniform(-0.5, 0.5), 0, 0]

def generate_baseline(n_samples: int = 800, out: Path | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Genera dataset baseline: 50% aleatorio + 50% casos borde (donde mejor supera a heurística)."""
    rng = np.random.RandomState(42)
    X: list[list[float]] = []
    y: list[str] = []
    # 50% aleatorio con política mejorada
    n_random = n_samples // 2
    for _ in range(n_random):
        feat = _random_feat(rng)
        y.append(_better_label(feat, has_ranged=False))
        X.append(feat)
    # 50% casos borde explícitos
    n_edge = n_samples - n_random
    for i in range(n_edge):
        feat = _edge_feat(rng, i % 6)
        y.append(_better_label(feat, has_ranged=False))
        X.append(feat)
    # Garantizar >=30 por clase
    from collections import Counter as _C
    cnt = _C(y)
    for action in ACTION_NAMES:
        while cnt.get(action, 0) < 30:
            if action == "evade":
                feat = [0.1, 0.05, 0.5, 0.25, 0, 0, 0, 0.2, 1.0, 0]
            elif action == "retreat":
                feat = [0.08, 0, 0.5, 0.2, 1.0, 0, 0, 0, 0, 0]
            elif action == "wait":
                feat = [0.25, 0, 0.8, 0.6, 0, 0, 0, 0.3, 0, 1.0]
            elif action == "attack_ranged":
                feat = [0.35, 0, 0.6, 0.8, 0, 1.0, 0, 0.5, 0, 0]
            elif action == "attack_melee":
                feat = [0.08, 0, 0.6, 0.8, 0, 0, 0, 0, 0, 0]
            elif action == "approach":
                feat = [0.8, 0.2, 0.7, 0.7, 0, 0, 0, 0.5, 0, 0]
            elif action == "charge":
                feat = [0.3, 0, 0.8, 0.85, 0, 0, 0, 0, 0, 0]
            elif action == "circle":
                feat = [0.4, 0.2, 0.5, 0.5, 0, 0, 0, 1.0, 0, 0]
            else:
                feat = [rng.uniform(-0.3, 0.3) for _ in range(10)]
            X.append(feat)
            y.append(action)
            cnt[action] = cnt.get(action, 0) + 1
    # Shuffle
    idx = rng.permutation(len(X))
    X = [X[i] for i in idx]
    y = [y[i] for i in idx]
    X_arr = np.array(X, dtype=np.float32)
    y_arr = np.array(y, dtype=str)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        np.savez(str(out), X=X_arr, y=y_arr, feature_names=np.array(FEATURE_NAMES), action_names=np.array(ACTION_NAMES))
        print(f"Baseline dataset: {len(y_arr)} muestras -> {out} (X:{X_arr.shape}, y:{y_arr.shape})")
        uniq, counts = np.unique(y_arr, return_counts=True)
        for u, c in zip(uniq, counts, strict=False):
            print(f"  {u}: {c} ({c/len(y_arr)*100:.1f}%)")
    return X_arr, y_arr

def train_from_dataset(data_path: Path, out_path: Path, test_size: float = 0.2) -> None:
    """Entrena BehaviorPredictor desde NPZ y guarda modelo .pkl"""
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split

    data = np.load(str(data_path), allow_pickle=True)
    # Soporta dos formatos: nuestro NPZ (X,y) y sample_dataset (features/labels)
    if "X" in data:
        X = data["X"].astype(np.float32)
        y = data["y"].astype(str)
    elif "features" in data:
        X = data["features"].astype(np.float32)
        y = data["labels"].astype(str)
    else:
        raise ValueError(f"Dataset {data_path} no contiene X/y ni features/labels. Claves: {list(data.keys())}")

    print(f"Dataset: {X.shape[0]} muestras, {X.shape[1]} features, clases: {sorted(set(y))}")
    if X.shape[1] != 10:
        print(f"WARN: se esperaban 10 features (enemy AI), got {X.shape[1]}. ¿Es dataset de pattern_demo? Usará mapping.")

    # Split: stratify solo si cada clase tiene >=2 muestras (evita ValueError con clases raras)
    from collections import Counter as _Counter
    _counts = _Counter(y)
    _can_stratify = len(set(y)) > 1 and min(_counts.values()) >= 2
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y if _can_stratify else None)
    print(f"Split: train {len(y_train)}, test {len(y_test)} (stratify={_can_stratify})")

    # Entrenar predictor
    pred = BehaviorPredictor()
    # Alimentar como add_example haría, pero en lote para velocidad
    # Para compatibilidad, usamos directamente _X,_y y _train
    pred._X = [row.tolist() for row in X_train]
    pred._y = [pred.action_index(label) for label in y_train]
    pred._train()
    print(f"Entrenado: is_trained={pred.is_trained}, samples={len(pred._X)}")
    print(f"  Stats: {pred.dataset_stats()}")

    # Evaluar
    # Convertir y_test a índices para comparar con predict_batch (que devuelve nombres)
    # Necesitamos evaluar accuracy en test
    correct = 0
    # Usar predictor para predecir test
    preds = pred.predict_batch([row.tolist() for row in X_test])
    if preds is None:
        print("ERROR: modelo no entrenado, no puede predecir")
        sys.exit(1)
    for p, t in zip(preds, y_test, strict=False):
        if p == t:
            correct += 1
    acc = correct / len(y_test) if len(y_test) else 0
    print(f"Accuracy test: {acc:.3f} ({correct}/{len(y_test)})")

    # Comparar vs heurística pura en mismo test
    heur_correct = 0
    for row, true_label in zip(X_test, y_test, strict=False):
        feat = row.tolist()
        heur_label = _heuristic_label(feat, has_ranged=False)
        if heur_label == true_label:
            heur_correct += 1
    heur_acc = heur_correct / len(y_test) if len(y_test) else 0
    print(f"Heuristica (reglas) accuracy: {heur_acc:.3f} ({heur_correct}/{len(y_test)})")
    print(f"Mejora: {acc - heur_acc:+.3f} ({(acc - heur_acc)*100:+.1f} puntos)")
    if acc > heur_acc:
        print("OK El modelo MEJORA el juego vs reglas puras")
    else:
        print("WARN El modelo no mejora vs reglas - prueba mas datos o ajuste")

    # Reporte detallado
    try:
        print("\nReporte clasificación:")
        print(classification_report(y_test, preds, zero_division=0))
    except Exception:
        pass

    # Guardar
    pred.save(out_path)
    print(f"\nModelo guardado en {out_path}")
    print("Para usar en juego: python -m src.main --stage stage_ai_dojo")
    print("O copia a student_assets/models/enemy_ai.pkl (ya está ahi)")

def eval_model(data_path: Path, model_path: Path) -> None:
    """Evalúa un modelo guardado contra un dataset, compara vs reglas"""
    from sklearn.metrics import classification_report

    pred = BehaviorPredictor()
    if not pred.load(model_path):
        print(f"ERROR: no se pudo cargar modelo {model_path}")
        sys.exit(1)
    print(f"Modelo cargado: {model_path} -> trained={pred.is_trained}, samples={len(pred._X)}")
    data = np.load(str(data_path), allow_pickle=True)
    X = data["X"].astype(np.float32) if "X" in data else data["features"].astype(np.float32)
    y = data["y"].astype(str) if "y" in data else data["labels"].astype(str)
    preds = pred.predict_batch([row.tolist() for row in X])
    if preds is None:
        print("Modelo no entrenado")
        return
    acc = sum(1 for p,t in zip(preds, y, strict=False) if p==t) / len(y)
    print(f"Accuracy modelo en {data_path}: {acc:.3f}")
    # Heurística
    heur_preds = [_heuristic_label(row.tolist()) for row in X]
    heur_acc = sum(1 for p,t in zip(heur_preds, y, strict=False) if p==t) / len(y)
    print(f"Heurística accuracy: {heur_acc:.3f}")
    print(f"Mejora: {acc-heur_acc:+.3f}")
    print("\nReporte modelo:")
    print(classification_report(y, preds, zero_division=0))

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--generate-baseline", action="store_true", help="Genera assets/datasets/ai_enemy_baseline.npz (500 muestras)")
    p.add_argument("--train", action="store_true", help="Entrena desde --data y guarda en --out")
    p.add_argument("--eval", action="store_true", help="Evalúa --model contra --data")
    p.add_argument("--data", type=Path, default=Path("assets/datasets/ai_enemy_baseline.npz"), help="Ruta dataset .npz")
    p.add_argument("--out", type=Path, default=Path("student_assets/models/enemy_ai.pkl"), help="Ruta salida .pkl")
    p.add_argument("--model", type=Path, default=Path("student_assets/models/enemy_ai.pkl"), help="Ruta modelo para --eval")
    p.add_argument("--samples", type=int, default=500, help="Número muestras baseline")
    args = p.parse_args(argv)

    if args.generate_baseline:
        generate_baseline(n_samples=args.samples, out=args.data)
        # También entrenar automáticamente el baseline a pkl para que dojo funcione sin pasos extra
        baseline_pkl = Path("assets/datasets/ai_enemy_baseline.pkl")
        print("Entrenando modelo baseline para assets/datasets/ai_enemy_baseline.pkl ...")
        train_from_dataset(args.data, baseline_pkl)
        print("Baseline listo. Los estudiantes pueden partir de ahí y mejorar.")

    if args.train:
        if not args.data.exists():
            print(f"ERROR: dataset no existe: {args.data}")
            print("Ejecuta primero: python tools/train_enemy_ai.py --generate-baseline")
            return 1
        train_from_dataset(args.data, args.out)

    if args.eval:
        if not args.data.exists():
            print(f"ERROR: dataset no existe: {args.data}")
            return 1
        if not args.model.exists():
            print(f"ERROR: modelo no existe: {args.model}")
            return 1
        eval_model(args.data, args.model)

    if not (args.generate_baseline or args.train or args.eval):
        p.print_help()
        print("\nEjemplo flujo 2 semanas:")
        print("  python tools/train_enemy_ai.py --generate-baseline")
        print("  python tools/train_enemy_ai.py --train \
    --data assets/datasets/ai_enemy_baseline.npz --out student_assets/models/enemy_ai.pkl  # noqa: E501")
        print("  python tools/train_enemy_ai.py --eval \
    --data assets/datasets/ai_enemy_baseline.npz --model student_assets/models/enemy_ai.pkl  # noqa: E501")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

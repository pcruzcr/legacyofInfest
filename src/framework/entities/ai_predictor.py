"""
Module: ai_predictor
System: framework.entities
Academic Unit: Unit IX — Reconocimiento de patrones

Clasificador ligero que recomienda acciones tácticas a los enemigos.

Estado: **conectado** (AUD-050). Lo consume
`src.framework.entities.squad_brain.SquadBrain`, que agrupa a todos los enemigos
de la escena en un solo lote y reevalúa a 4 Hz. Ese envoltorio no es decorativo:
la inferencia individual cuesta 1,89 ms, así que una llamada por enemigo y
fotograma consumía el 102% del presupuesto a 60 fps con sólo 9 enemigos. El
módulo llevaba sin usarse porque su forma de uso obvia era inviable, no por
descuido. Véase el docstring de `squad_brain` para las mediciones.

No añadas llamadas a `predict()` en bucles por entidad. Usa `predict_batch`.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

logger = logging.getLogger(__name__)

class BehaviorPredictor:
    """Lightweight AI behavior predictor using sklearn.
    Classifies game state features to recommend enemy actions.
    Uses KNN + DecisionTree for adaptive behavior selection.
    """

    def __init__(self) -> None:
        # KNN con k=3 y distancia, robusto con ruido
        self._knn = KNeighborsClassifier(n_neighbors=3, weights="distance")
        # Árbol sin límite y balanceado para clases raras (evade/retreat)
        self._tree = DecisionTreeClassifier(max_depth=None, random_state=42, class_weight="balanced")
        self._trained = False
        self._X: list[list[float]] = []
        self._y: list[int] = []
        self._feature_names = [
            "dist_x", "dist_y", "player_health_pct", "self_health_pct",
            "player_is_attacking", "player_is_airborne", "player_is_dashing",
            "angle_to_player", "wall_ahead", "ledge_ahead",
        ]
        self._action_names = [
            "approach", "retreat", "attack_melee", "attack_ranged",
            "circle", "wait", "evade", "charge",
        ]

    def _extract_features(
        self,
        self_x: float, self_y: float,
        player_x: float, player_y: float,
        player_health: float, self_health: float,
        player_state: Any,
        wall_ahead: bool = False,
        ledge_ahead: bool = False,
    ) -> list[float]:
        dx = player_x - self_x
        dy = player_y - self_y
        dist = math.sqrt(dx * dx + dy * dy)
        angle = math.atan2(dy, dx) / math.pi if dist > 0 else 0.0  # normalizado -1..1 (antes -3.14..3.14 dominaba KNN)
        return [
            dx / 300.0,
            dy / 200.0,
            player_health / 5.0,
            self_health / 5.0,
            1.0 if player_state in ("SHORT_ATTACK", "LONG_ATTACK", "ULTIMATE") else 0.0,
            1.0 if player_state in ("JUMPING", "FALLING", "AERIAL_ATTACK") else 0.0,
            1.0 if player_state == "DASHING" else 0.0,
            angle,
            1.0 if wall_ahead else 0.0,
            1.0 if ledge_ahead else 0.0,
        ]

    def add_example(
        self,
        features: list[float],
        action: int,
    ) -> None:
        self._X.append(features)
        self._y.append(action)
        if len(self._X) > 200:
            self._X.pop(0)
            self._y.pop(0)
        if len(self._X) >= 10:
            self._train()

    def _train(self) -> None:
        try:
            X_arr = np.array(self._X, dtype=np.float32)
            y_arr = np.array(self._y)
            self._knn.fit(X_arr, y_arr)
            self._tree.fit(X_arr, y_arr)
            self._trained = True
        except (ValueError, np.linalg.LinAlgError) as e:
            logger.warning("ai_predictor: training failed: %s", e)
            self._trained = False

    # ── API pública usada por SquadBrain ───────────────────────

    @property
    def is_trained(self) -> bool:
        return self._trained and len(self._X) >= 5

    @property
    def action_names(self) -> tuple[str, ...]:
        return tuple(self._action_names)

    def action_index(self, name: str) -> int:
        """Índice de una acción por nombre; 0 ('approach') si es desconocida."""
        try:
            return self._action_names.index(name)
        except ValueError:
            return 0

    def extract_features(self, **kwargs: Any) -> list[float]:
        """Vector de características público (el interno tiene guion bajo)."""
        return self._extract_features(**kwargs)

    def predict_batch(self, rows: list[list[float]]) -> list[str] | None:
        """Predice para todas las filas en **una sola** llamada a sklearn.

        Devuelve `None` si el modelo aún no está entrenado, para que el llamante
        recurra a su política determinista en lugar de recibir acciones
        inventadas — devolver una acción aleatoria disfrazada de predicción es
        peor que admitir que no hay modelo.

        AUD-050: esto existe porque la sobrecarga de sklearn es por invocación,
        no por fila. Medido: 9 filas cuestan 1,82 ms en lote contra 11,87 ms una
        por una (7x); 30 filas, 2,57 ms contra 41,73 ms (16x).

        Usa el árbol (no KNN) para el lote: el árbol maneja mejor el desbalance
        de clases (evade/retreat con pocas muestras) y la lógica determinista
        de _better_label. KNN con k=1 se usa para predict() individual.
        """
        if not self.is_trained or not rows:
            return None
        try:
            import numpy as _np

            matrix = _np.asarray(rows, dtype=np.float32)
            # Árbol es más robusto para este dataset sintético; KNN queda para casos puntuales
            try:
                predictions = self._tree.predict(matrix)
            except Exception:
                predictions = self._knn.predict(matrix)
            return [
                self._action_names[int(p) % len(self._action_names)]
                for p in predictions
            ]
        except (ValueError, IndexError, np.linalg.LinAlgError) as exc:
            logger.warning("ai_predictor: predicción por lote falló: %s", exc)
            return None

    def predict(
        self,
        features: list[float],
    ) -> int:
        """Predicción individual. **Determinista.**

        AUD-050: antes elegía entre KNN y árbol con ``random.random() < 0.6``,
        de modo que el mismo estado de juego producía acciones distintas. Eso
        hace la IA imposible de probar y de depurar, y no aporta variedad
        interesante — sólo incoherencia. La variedad pertenece a los parámetros
        del comportamiento, no a qué modelo contesta.

        Preferir ``predict_batch`` en cualquier bucle sobre entidades: esta
        llamada cuesta ~1,9 ms.
        """
        if not self.is_trained:
            return -1
        try:
            return int(self._knn.predict([features])[0])
        except (ValueError, IndexError, np.linalg.LinAlgError) as e:
            logger.warning("ai_predictor: prediction failed: %s", e)
            return -1

    def predict_action_name(self, **kwargs: Any) -> str:
        features = self._extract_features(**kwargs)
        pred = self.predict(features)
        if pred < 0:
            return "approach"
        return self._action_names[pred % len(self._action_names)]

    def get_rule_based_action(
        self,
        dist: float,
        health_pct: float,
        player_health_pct: float,
        has_ranged: bool = False,
    ) -> str:
        # AUD-456 — la heurística vive en `tactica_por_reglas` para que la
        # reserva sea usable sin importar este módulo (que arrastra sklearn).
        # Esta firma se queda como punto de entrada pública.
        from src.framework.entities.tactica_por_reglas import accion_por_distancia

        return accion_por_distancia(
            dist=dist,
            health_pct=health_pct,
            player_health_pct=player_health_pct,
            has_ranged=has_ranged,
        )


    # ── Persistencia para entrenamiento por estudiantes (2 semanas) ──

    def save(self, path: str | Path) -> None:
        """Guarda el predictor entrenado a disco (joblib). Usado por tools/train_enemy_ai.py"""
        from pathlib import Path as _P

        import joblib

        p = _P(path)
        if p.suffix not in (".pkl", ".joblib"):
            raise ValueError(f"BehaviorPredictor.save: path debe terminar en .pkl/.joblib, got '{p.suffix}'")
        p.parent.mkdir(parents=True, exist_ok=True)
        # Guardamos solo lo necesario para rehidratar sin re-entrenar
        payload = {
            "X": self._X,
            "y": self._y,
            "knn": self._knn if self._trained else None,
            "tree": self._tree if self._trained else None,
            "trained": self._trained,
            "feature_names": self._feature_names,
            "action_names": self._action_names,
        }
        joblib.dump(payload, str(p))

    def load(self, path: str | Path) -> bool:
        """Carga un predictor previamente guardado. Devuelve True si tuvo éxito."""
        from pathlib import Path as _P

        import joblib

        p = _P(path)
        if not p.exists():
            return False
        try:
            payload = joblib.load(str(p))
            self._X = payload.get("X", [])
            self._y = payload.get("y", [])
            # Si el payload trae modelos ya entrenados, los restauramos
            if payload.get("trained") and payload.get("knn") is not None:
                self._knn = payload["knn"]
                self._tree = payload["tree"]
                self._trained = True
            else:
                # Re-entrenar desde X,y si no trae modelos (compatibilidad)
                if len(self._X) >= 10:
                    self._train()
            return True
        except Exception as e:
            logger.warning("BehaviorPredictor.load failed for %s: %s", p, e)
            return False

    def dataset_stats(self) -> dict[str, Any]:
        """Estadísticas para el HUD de stage_ai_dojo y la guía de 2 semanas."""
        from collections import Counter

        total = len(self._y)
        counts = Counter(self._y)
        # Mapear índices a nombres
        named = {self._action_names[k] if 0 <= k < len(self._action_names) else str(k): v for k, v in counts.items()}
        return {
            "samples": total,
            "trained": self._trained,
            "actions": named,
            "feature_names": list(self._feature_names),
        }


_global_predictor: BehaviorPredictor | None = None


def get_predictor() -> BehaviorPredictor:
    global _global_predictor
    if _global_predictor is None:
        _global_predictor = BehaviorPredictor()
        # Auto-cargar modelo del estudiante si existe (stage_ai_dojo / 2 semanas)
        # No se hace en precarga_ia para no bloquear; aquí es lazy y silencioso.
        for cand in [
            Path("student_assets/models/enemy_ai.pkl"),
            Path("student_assets/models/enemy_ai.joblib"),
            Path("assets/datasets/ai_enemy_baseline.pkl"),
        ]:
            if cand.exists():
                try:
                    if _global_predictor.load(cand):
                        logger.info("BehaviorPredictor: modelo estudiante cargado desde %s", cand)
                        break
                except Exception:
                    pass
    return _global_predictor


def load_student_model(path: str | Path | None = None) -> bool:
    """Fuerza recarga del modelo del estudiante. Usado por stage_ai_dojo al presionar T."""
    p = Path(path) if path else Path("student_assets/models/enemy_ai.pkl")
    if not p.exists():
        # fallback a baseline
        alt = Path("assets/datasets/ai_enemy_baseline.pkl")
        if alt.exists():
            p = alt
        else:
            return False
    pred = get_predictor()
    return pred.load(p)

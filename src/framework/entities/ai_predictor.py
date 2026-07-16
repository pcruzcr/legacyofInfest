from __future__ import annotations

import logging
import math
import random
from typing import Any

import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier


class BehaviorPredictor:
    """Lightweight AI behavior predictor using sklearn.
    Classifies game state features to recommend enemy actions.
    Uses KNN + DecisionTree for adaptive behavior selection.
    """

    def __init__(self) -> None:
        self._knn = KNeighborsClassifier(n_neighbors=3)
        self._tree = DecisionTreeClassifier(max_depth=5, random_state=42)
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
        angle = math.atan2(dy, dx) if dist > 0 else 0.0
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
            logging.warning("ai_predictor: training failed: %s", e)
            self._trained = False

    def predict(
        self,
        features: list[float],
    ) -> int:
        if not self._trained or len(self._X) < 5:
            return -1
        try:
            knn_pred = int(self._knn.predict([features])[0])
            tree_pred = int(self._tree.predict([features])[0])
            return knn_pred if random.random() < 0.6 else tree_pred
        except (ValueError, IndexError, np.linalg.LinAlgError) as e:
            logging.warning("ai_predictor: prediction failed: %s", e)
            return random.randint(0, len(self._action_names) - 1)

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
        if health_pct < 0.3 and dist < 60:
            return "evade"
        if dist < 40:
            return "attack_melee" if not has_ranged else "retreat"
        if dist < 120 and has_ranged:
            return "attack_ranged"
        if dist < 120:
            return "charge"
        if player_health_pct < 0.3 and dist < 150:
            return "attack_melee"
        if dist > 200:
            return "approach"
        return "circle"


_global_predictor: BehaviorPredictor | None = None


def get_predictor() -> BehaviorPredictor:
    global _global_predictor
    if _global_predictor is None:
        _global_predictor = BehaviorPredictor()
    return _global_predictor

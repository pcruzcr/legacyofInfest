"""
Module: pattern_recognition_tools
System: framework.processing
Academic Unit: Unit IX (Pattern Recognition and Machine Learning)
Description: PatternRecognitionTools class — feature extraction, model
training, evaluation, serialization, registry, and inference.
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from src.framework.processing.vision_tools import VisionTools

logger = logging.getLogger(__name__)


@dataclass
class TrainedModel:
    model_type: str
    estimator: Pipeline
    classes: list[str]
    feature_method: str
    feature_length: int
    training_accuracy: float
    metadata: dict = field(default_factory=dict)


@dataclass
class EvaluationResult:
    accuracy: float
    per_class_accuracy: dict[str, float]
    confusion_matrix: np.ndarray
    report: str


class PatternRecognitionTools:
    """Machine learning classification utilities."""

    _model_registry: dict[str, TrainedModel] = {}

    @classmethod
    def extract_hog(cls, surface) -> np.ndarray:
        return VisionTools.extract_hog(surface)

    @classmethod
    def extract_lbp(cls, surface) -> np.ndarray:
        return VisionTools.extract_lbp(surface)

    @classmethod
    def extract_color_histogram(cls, surface, bins: int = 256) -> np.ndarray:
        return VisionTools.extract_color_histogram(surface, bins)

    @classmethod
    def extract_combined(cls, surface) -> np.ndarray:
        return VisionTools.extract_features(surface, method="combined")

    @classmethod
    def train(
        cls,
        X: np.ndarray,
        y: np.ndarray,
        model_type: str,
        feature_method: str = "hog",
        **kwargs,
    ) -> TrainedModel:
        cls._validate_dataset(X, y)
        X = X.astype(np.float32)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        estimator = cls._build_model(model_type, **kwargs)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            estimator.fit(X_scaled, y)
        pipeline = Pipeline([("scaler", scaler), ("classifier", estimator)])
        train_acc = pipeline.score(X, y)
        classes = sorted(set(y))
        if isinstance(classes[0], np.integer):
            classes = [str(c) for c in classes]
        return TrainedModel(
            model_type=model_type,
            estimator=pipeline,
            classes=classes,
            feature_method=feature_method,
            feature_length=X.shape[1],
            training_accuracy=float(train_acc),
            metadata={"kwargs": kwargs},
        )

    @classmethod
    def evaluate(
        cls,
        model: TrainedModel,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> EvaluationResult:
        cls._validate_model(model)
        X_test = X_test.astype(np.float32)
        if X_test.shape[1] != model.feature_length:
            raise ValueError(
                f"PatternRecognitionTools.evaluate: feature length mismatch. "
                f"Expected {model.feature_length}, got {X_test.shape[1]}"
            )
        y_pred = model.estimator.predict(X_test)
        acc = float(np.mean(y_pred == y_test))
        report = classification_report(y_test, y_pred, output_dict=False, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)
        per_class: dict[str, float] = {}
        for i, cls_name in enumerate(model.classes):
            mask = y_test == cls_name
            if mask.sum() > 0:
                per_class[cls_name] = float(np.mean(y_pred[mask] == cls_name))
            else:
                per_class[cls_name] = 0.0
        return EvaluationResult(
            accuracy=acc,
            per_class_accuracy=per_class,
            confusion_matrix=cm,
            report=str(report),
        )

    @classmethod
    def save_model(cls, model: TrainedModel, path: str | Path) -> None:
        path = Path(path)
        if path.suffix != ".pkl":
            raise ValueError(
                f"PatternRecognitionTools.save_model: path must end in .pkl, got '{path.suffix}'"
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, str(path))

    @classmethod
    def load_model(cls, path: str | Path) -> TrainedModel:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"PatternRecognitionTools.load_model: file not found: {path}"
            )
        model = joblib.load(str(path))
        if not isinstance(model, TrainedModel):
            raise TypeError(
                f"PatternRecognitionTools.load_model: loaded object is not a TrainedModel, "
                f"got {type(model)}"
            )
        return model

    @classmethod
    def register_model(cls, name: str, model: TrainedModel) -> None:
        if name in cls._model_registry:
            logger.warning(
                f"PatternRecognitionTools.register_model: overwriting existing model '{name}'"
            )
        cls._model_registry[name] = model

    @classmethod
    def get_model(cls, name: str) -> TrainedModel:
        if name not in cls._model_registry:
            available = ", ".join(cls.list_models())
            raise KeyError(
                f"PatternRecognitionTools.get_model: model '{name}' not found. "
                f"Registered models: {available}"
            )
        return cls._model_registry[name]

    @classmethod
    def list_models(cls) -> list[str]:
        return list(cls._model_registry.keys())

    @classmethod
    def classify(cls, features: np.ndarray, model: TrainedModel) -> str:
        cls._validate_model(model)
        if features.ndim == 1:
            features = features.reshape(1, -1)
        if features.shape[1] != model.feature_length:
            raise ValueError(
                f"PatternRecognitionTools.classify: feature length mismatch. "
                f"Expected {model.feature_length}, got {features.shape[1]}"
            )
        pred = model.estimator.predict(features)
        return str(pred[0])

    @classmethod
    def classify_proba(cls, features: np.ndarray, model: TrainedModel) -> dict[str, float]:
        cls._validate_model(model)
        if model.model_type == "svm" and not model.estimator.named_steps["classifier"].probability:
            raise NotImplementedError(
                "PatternRecognitionTools.classify_proba: SVM was trained without probability=True. "
                "Set probability=True during train() to use probability estimation."
            )
        if features.ndim == 1:
            features = features.reshape(1, -1)
        proba = model.estimator.predict_proba(features)[0]
        return {str(cls_name): float(p) for cls_name, p in zip(model.classes, proba)}

    @classmethod
    def predict(
        cls,
        model: TrainedModel,
        surface,
        method: Literal["hog", "lbp", "color_hist", "combined"] = "hog",
    ) -> str:
        cls._validate_model(model)
        features = VisionTools.extract_features(surface, method=method)
        return cls.classify(features, model)

    @classmethod
    def _build_model(cls, model_type: str, **kwargs) -> object:
        if model_type == "knn":
            return KNeighborsClassifier(**kwargs)
        elif model_type == "tree":
            kw = {"random_state": 42, **kwargs}
            return DecisionTreeClassifier(**kw)
        elif model_type == "forest":
            kw = {"random_state": 42, **kwargs}
            return RandomForestClassifier(**kw)
        elif model_type == "svm":
            kw = {"random_state": 42, "probability": True, **kwargs}
            return SVC(**kw)
        else:
            raise ValueError(
                f"PatternRecognitionTools.train: unknown model_type '{model_type}'. "
                f"Use 'knn', 'tree', 'forest', or 'svm'."
            )

    @classmethod
    def _validate_features(cls, features: np.ndarray) -> None:
        if features is None:
            raise TypeError("PatternRecognitionTools: features cannot be None")
        if not isinstance(features, np.ndarray):
            raise TypeError(
                f"PatternRecognitionTools: expected np.ndarray, got {type(features)}"
            )

    @classmethod
    def _validate_model(cls, model: object) -> None:
        if not isinstance(model, TrainedModel):
            raise TypeError(
                f"PatternRecognitionTools: expected TrainedModel, got {type(model)}"
            )

    @classmethod
    def _validate_dataset(cls, X: np.ndarray, y: np.ndarray) -> None:
        if X is None or y is None:
            raise ValueError("PatternRecognitionTools.train: X and y cannot be None")
        if X.shape[0] < 10:
            raise ValueError(
                f"PatternRecognitionTools.train: need at least 10 samples, got {X.shape[0]}"
            )
        if X.shape[0] != y.shape[0]:
            raise ValueError(
                f"PatternRecognitionTools.train: X and y length mismatch: {X.shape[0]} vs {y.shape[0]}"
            )
        if len(set(y)) < 2:
            raise ValueError(
                f"PatternRecognitionTools.train: need at least 2 classes, got {len(set(y))}"
            )

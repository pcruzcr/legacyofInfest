"""
Module: pattern_recognition_tools
System: framework.processing
Academic Unit: Unit IX (Pattern Recognition and Machine Learning)
Description: PatternRecognitionTools class — feature extraction, model
training, evaluation, serialization, registry, inference, and
matplotlib-based training report generation (confusion matrix,
per-class accuracy, feature importance).
"""
from __future__ import annotations

import io
import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

import pygame

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
        method: str | None = None,
    ) -> str:
        cls._validate_model(model)
        method = method or model.feature_method
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

    @classmethod
    def generate_training_report(
        cls,
        model: TrainedModel,
        X_test: np.ndarray | None = None,
        y_test: np.ndarray | None = None,
        save_path: str | Path | None = None,
        figure_size: tuple[int, int] = (8, 6),
        dpi: int = 100,
    ) -> pygame.Surface | None:
        """Generate a matplotlib report figure: confusion matrix (if test data
        provided) and per-class accuracy bar chart. Renders to a pygame Surface.
        Optionally saves the figure to a PNG file at save_path.

        Returns a pygame Surface with the rendered figure, or None if matplotlib
        is not installed.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.ticker as mticker
        except ImportError:
            logger.warning("matplotlib not installed — training report unavailable")
            return None

        fig, axes = plt.subplots(1, 2 if X_test is not None else 1,
                                 figsize=figure_size, dpi=dpi)

        if X_test is not None and y_test is not None:
            y_pred = model.estimator.predict(X_test)
            cm = confusion_matrix(y_test, y_pred)
            ax_cm = axes[0]
            im = ax_cm.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
            ax_cm.figure.colorbar(im, ax=ax_cm)
            ax_cm.set(
                xticks=np.arange(len(model.classes)),
                yticks=np.arange(len(model.classes)),
                xticklabels=model.classes,
                yticklabels=model.classes,
                xlabel="Predicted",
                ylabel="True",
                title="Confusion Matrix",
            )
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax_cm.text(j, i, str(cm[i, j]),
                               ha="center", va="center",
                               color="white" if cm[i, j] > cm.max() / 2 else "black")
            ax_acc = axes[1]
        else:
            ax_acc = axes[0] if isinstance(axes, np.ndarray) else axes

        # Per-class accuracy bar chart
        eval_result = cls.evaluate(model, X_test, y_test) if X_test is not None else None
        if eval_result is not None:
            classes = list(eval_result.per_class_accuracy.keys())
            accs = list(eval_result.per_class_accuracy.values())
            colors = ["#4CAF50" if a >= 0.8 else "#FFC107" if a >= 0.5 else "#F44336"
                      for a in accs]
            bars = ax_acc.bar(classes, accs, color=colors)
            ax_acc.axhline(y=eval_result.accuracy, color="blue", linestyle="--",
                           label=f"Overall: {eval_result.accuracy:.2f}")
            ax_acc.set_ylim(0, 1.05)
            ax_acc.set_ylabel("Accuracy")
            ax_acc.set_title("Per-Class Accuracy")
            ax_acc.legend()
            for bar, acc in zip(bars, accs):
                ax_acc.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                            f"{acc:.2f}", ha="center", va="bottom", fontsize=8)
        else:
            ax_acc.text(0.5, 0.5, "No test data provided", ha="center", va="center",
                        transform=ax_acc.transAxes)

        plt.tight_layout()

        # Render to pygame surface
        buf = io.BytesIO()
        fig.savefig(buf, format="raw", dpi=dpi)
        buf.seek(0)
        w, h = fig.canvas.get_width_height()
        img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8).reshape((h, w, 4))
        # RGBA -> RGBX (pygame expects no alpha or converts)
        img_arr = img_arr[:, :, :3].copy()
        surf = pygame.image.frombuffer(img_arr.tobytes(), (w, h), "RGB")

        if save_path:
            fig.savefig(str(save_path), dpi=dpi, bbox_inches="tight")

        plt.close(fig)
        return surf

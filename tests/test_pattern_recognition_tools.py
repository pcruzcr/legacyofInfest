"""
Module: test_pattern_recognition_tools
System: tests
Description: Tests for PatternRecognitionTools: train, evaluate,
save/load, registry, classify, classify_proba, predict.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pygame

from src.framework.processing.pattern_recognition_tools import (
    EvaluationResult,
    PatternRecognitionTools,
    TrainedModel,
)
from src.framework.processing.vision_tools import VisionTools

SAMPLE_DATASET_PATH = Path("assets/datasets/sample_dataset.npz")
SAMPLE_MODEL_PATH = Path("assets/models/professor_sample.pkl")


def _ensure_sample_dataset() -> None:
    if SAMPLE_DATASET_PATH.exists():
        return
    rng = np.random.RandomState(42)
    n_per_class = 30
    X_list: list[np.ndarray] = []
    y_list: list[str] = []
    feature_dim = 288
    for label, center in [("dark_zone", 50), ("neutral", 128), ("light_zone", 200)]:
        for _ in range(n_per_class):
            features = rng.randn(feature_dim) * 10 + center
            X_list.append(features)
            y_list.append(label)
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=str)
    SAMPLE_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez(str(SAMPLE_DATASET_PATH), X=X, y=y)


def _ensure_sample_model() -> TrainedModel:
    if SAMPLE_MODEL_PATH.exists():
        return PatternRecognitionTools.load_model(SAMPLE_MODEL_PATH)
    data = np.load(str(SAMPLE_DATASET_PATH))
    X = data["X"].astype(np.float32)
    y = data["y"]
    model = PatternRecognitionTools.train(X, y, model_type="knn", n_neighbors=5)
    PatternRecognitionTools.save_model(model, SAMPLE_MODEL_PATH)
    return model


class TestTraining:
    def test_train_knn(self) -> None:
        X = np.random.randn(30, 10).astype(np.float32)
        y = np.array(["a"] * 15 + ["b"] * 15, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="knn", n_neighbors=3)
        assert isinstance(model, TrainedModel)
        assert model.model_type == "knn"
        assert model.feature_length == 10
        assert model.classes == ["a", "b"]
        assert 0.0 <= model.training_accuracy <= 1.0

    def test_train_tree(self) -> None:
        X = np.random.randn(20, 5).astype(np.float32)
        y = np.array(["x"] * 10 + ["y"] * 10, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="tree", max_depth=3)
        assert model.model_type == "tree"

    def test_train_forest(self) -> None:
        X = np.random.randn(20, 5).astype(np.float32)
        y = np.array(["x"] * 10 + ["y"] * 10, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="forest", n_estimators=10)
        assert model.model_type == "forest"

    def test_train_svm(self) -> None:
        X = np.random.randn(20, 5).astype(np.float32)
        y = np.array(["x"] * 10 + ["y"] * 10, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="svm", kernel="linear")
        assert model.model_type == "svm"

    def test_train_too_few_samples_raises(self) -> None:
        X = np.random.randn(5, 3).astype(np.float32)
        y = np.array(["a"] * 5, dtype=str)
        try:
            PatternRecognitionTools.train(X, y, model_type="knn")
            assert False
        except ValueError:
            pass

    def test_train_invalid_model_type_raises(self) -> None:
        X = np.random.randn(20, 3).astype(np.float32)
        y = np.array(["a"] * 10 + ["b"] * 10, dtype=str)
        try:
            PatternRecognitionTools.train(X, y, model_type="invalid")
            assert False
        except ValueError:
            pass


class TestEvaluate:
    def test_evaluate_returns_result(self) -> None:
        X = np.random.randn(40, 8).astype(np.float32)
        y = np.array(["a"] * 20 + ["b"] * 20, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="knn", n_neighbors=3)
        result = PatternRecognitionTools.evaluate(model, X, y)
        assert isinstance(result, EvaluationResult)
        assert 0.0 <= result.accuracy <= 1.0
        assert isinstance(result.per_class_accuracy, dict)
        assert isinstance(result.confusion_matrix, np.ndarray)
        assert isinstance(result.report, str)

    def test_evaluate_feature_mismatch_raises(self) -> None:
        X = np.random.randn(20, 5).astype(np.float32)
        y = np.array(["a"] * 10 + ["b"] * 10, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="knn")
        X_bad = np.random.randn(5, 8).astype(np.float32)
        try:
            PatternRecognitionTools.evaluate(model, X_bad, y[:5])
            assert False
        except ValueError:
            pass


class TestSerialization:
    def test_save_and_load(self) -> None:
        X = np.random.randn(20, 4).astype(np.float32)
        y = np.array(["a"] * 10 + ["b"] * 10, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="forest", n_estimators=5)
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            tmp_path = f.name
        try:
            PatternRecognitionTools.save_model(model, tmp_path)
            loaded = PatternRecognitionTools.load_model(tmp_path)
            assert isinstance(loaded, TrainedModel)
            assert loaded.model_type == "forest"
            assert loaded.feature_length == 4
        finally:
            os.unlink(tmp_path)

    def test_save_non_pkl_raises(self) -> None:
        X = np.random.randn(20, 4).astype(np.float32)
        y = np.array(["a"] * 10 + ["b"] * 10, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="knn")
        try:
            PatternRecognitionTools.save_model(model, "model.txt")
            assert False
        except ValueError:
            pass

    def test_load_nonexistent_raises(self) -> None:
        try:
            PatternRecognitionTools.load_model(Path("nonexistent.pkl"))
            assert False
        except FileNotFoundError:
            pass

    def test_sample_dataset_exists(self) -> None:
        _ensure_sample_dataset()
        assert SAMPLE_DATASET_PATH.exists()
        data = np.load(str(SAMPLE_DATASET_PATH))
        assert "X" in data and "y" in data
        assert data["X"].shape[0] == 90
        assert len(set(data["y"])) == 3

    def test_sample_model_exists(self) -> None:
        _ensure_sample_dataset()
        model = _ensure_sample_model()
        assert isinstance(model, TrainedModel)
        assert model.model_type == "knn"

    def test_sample_model_classifies(self) -> None:
        _ensure_sample_dataset()
        model = _ensure_sample_model()
        features = np.random.randn(288).astype(np.float32)
        label = PatternRecognitionTools.classify(features, model)
        assert isinstance(label, str)
        assert label in ["dark_zone", "neutral", "light_zone"]


class TestRegistry:
    def test_register_and_get(self) -> None:
        PatternRecognitionTools._model_registry.clear()
        X = np.random.randn(20, 3).astype(np.float32)
        y = np.array(["a"] * 10 + ["b"] * 10, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="knn")
        PatternRecognitionTools.register_model("test_model", model)
        retrieved = PatternRecognitionTools.get_model("test_model")
        assert retrieved is model

    def test_get_unknown_raises(self) -> None:
        PatternRecognitionTools._model_registry.clear()
        try:
            PatternRecognitionTools.get_model("nonexistent")
            assert False
        except KeyError:
            pass

    def test_list_models(self) -> None:
        PatternRecognitionTools._model_registry.clear()
        assert PatternRecognitionTools.list_models() == []


class TestClassify:
    def test_classify_returns_label(self) -> None:
        X = np.random.randn(20, 5).astype(np.float32)
        y = np.array(["class_a"] * 10 + ["class_b"] * 10, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="knn", n_neighbors=3)
        features = X[0]
        label = PatternRecognitionTools.classify(features, model)
        assert isinstance(label, str)

    def test_classify_feature_mismatch_raises(self) -> None:
        X = np.random.randn(20, 5).astype(np.float32)
        y = np.array(["a"] * 10 + ["b"] * 10, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="knn")
        bad_features = np.random.randn(8).astype(np.float32)
        try:
            PatternRecognitionTools.classify(bad_features, model)
            assert False
        except ValueError:
            pass


class TestClassifyProba:
    def test_classify_proba_knn(self) -> None:
        X = np.random.randn(30, 5).astype(np.float32)
        y = np.array(["a"] * 15 + ["b"] * 15, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="knn", n_neighbors=3)
        features = X[0]
        proba = PatternRecognitionTools.classify_proba(features, model)
        assert isinstance(proba, dict)
        assert abs(sum(proba.values()) - 1.0) < 0.01

    def test_classify_proba_tree(self) -> None:
        X = np.random.randn(30, 3).astype(np.float32)
        y = np.array(["a"] * 15 + ["b"] * 15, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="tree")
        proba = PatternRecognitionTools.classify_proba(X[0], model)
        assert isinstance(proba, dict)
        assert abs(sum(proba.values()) - 1.0) < 0.01


class TestPredict:
    def test_predict_returns_label(self) -> None:
        rng = np.random.RandomState(42)
        surfs: list[pygame.Surface] = []
        for _ in range(12):
            s = pygame.Surface((32, 32))
            s.fill((rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255)))
            surfs.append(s)
        X = np.array([VisionTools.extract_hog(s) for s in surfs], dtype=np.float32)
        y = np.array(["a"] * 6 + ["b"] * 6, dtype=str)
        model = PatternRecognitionTools.train(X, y, model_type="knn", n_neighbors=3)
        label = PatternRecognitionTools.predict(model, surfs[0], method="hog")
        assert isinstance(label, str)


class TestValidModel:
    def test_non_trained_model_raises(self) -> None:
        try:
            PatternRecognitionTools.classify(np.random.randn(5), "not_a_model")
            assert False
        except TypeError:
            pass

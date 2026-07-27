#!/usr/bin/env python3
"""Regenerate the reference pattern-recognition model from source data.

Why this script exists (AUD-038)
--------------------------------
``assets/models/professor_sample.pkl`` was committed as an opaque binary with no
way to reproduce it. That is three problems in one:

1. **Security.** ``joblib.load`` is ``pickle`` underneath, and unpickling
   executes arbitrary code. In a classroom the file gets copied between
   machines, emailed, and submitted as coursework — untrusted input by
   definition, loaded with full process privileges.
2. **Correctness.** The committed model was trained under scikit-learn 1.9.0.
   Loading it under any other version emitted ``InconsistentVersionWarning``
   ("may lead to breaking code or invalid results") — a warning the test suite
   was hiding behind ``filterwarnings = ["ignore::Warning"]`` (AUD-016). Nobody
   could tell whether its predictions were still valid.
3. **Reproducibility.** Nobody could retrain it, inspect what it learned, or
   fix it, because the inputs and hyperparameters were not recorded anywhere.

Shipping a training script plus a dataset fixes all three: the artefact becomes
derivable, version drift becomes a rebuild instead of a mystery, and the file
you load is one you generated on your own machine.

Usage
-----
    # Rebuild from an image directory (see tools/build_dataset.py for layout)
    python scripts/train_reference_model.py --data data/shapes/ --out assets/models/professor_sample.pkl

    # Rebuild from a prepared .npz feature file
    python scripts/train_reference_model.py --npz data/shapes.npz --out assets/models/professor_sample.pkl

    # Verify the committed model still agrees with a freshly trained one
    python scripts/train_reference_model.py --npz data/shapes.npz --verify assets/models/professor_sample.pkl
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

logger = logging.getLogger(__name__)

DEFAULT_MODEL_TYPE = "knn"
DEFAULT_FEATURE_METHOD = "hog"


def load_dataset(npz_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load features and labels from an .npz produced by tools/build_dataset.py."""
    with np.load(npz_path, allow_pickle=False) as data:
        return data["X"], data["y"]


def train(
    features: np.ndarray,
    labels: np.ndarray,
    model_type: str,
    feature_method: str,
):
    from src.framework.processing.pattern_recognition_tools import (
        PatternRecognitionTools,
    )

    logger.info(
        "Training %s on %d samples x %d features",
        model_type, features.shape[0], features.shape[1],
    )
    model = PatternRecognitionTools.train(
        features, labels, model_type=model_type, feature_method=feature_method,
    )
    logger.info("Training accuracy: %.4f", model.training_accuracy)
    return model


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--npz", type=Path, help="Prepared feature file (.npz)")
    source.add_argument("--data", type=Path, help="Image directory to featurise first")
    parser.add_argument("--out", type=Path, help="Where to write the trained model")
    parser.add_argument(
        "--verify", type=Path,
        help="Compare an existing model against a freshly trained one instead of writing",
    )
    parser.add_argument("--model-type", default=DEFAULT_MODEL_TYPE)
    parser.add_argument("--feature-method", default=DEFAULT_FEATURE_METHOD)
    args = parser.parse_args(argv)

    if args.out is None and args.verify is None:
        parser.error("one of --out or --verify is required")

    if args.data is not None:
        logger.info("Featurising images under %s", args.data)
        from tools.build_dataset import build_dataset

        features, labels = build_dataset(args.data, method=args.feature_method)
    else:
        if not args.npz.exists():
            logger.error("Dataset not found: %s", args.npz)
            logger.error("Build one first:  python tools/build_dataset.py --input <images/> --output %s", args.npz)
            return 1
        features, labels = load_dataset(args.npz)

    model = train(features, labels, args.model_type, args.feature_method)

    if args.verify is not None:
        from src.framework.processing.pattern_recognition_tools import (
            PatternRecognitionTools,
        )

        existing = PatternRecognitionTools.load_model(args.verify)
        drift = abs(existing.training_accuracy - model.training_accuracy)
        logger.info(
            "committed accuracy %.4f vs rebuilt %.4f (drift %.4f)",
            existing.training_accuracy, model.training_accuracy, drift,
        )
        if existing.classes != model.classes:
            logger.error(
                "Class labels differ: committed %s vs rebuilt %s",
                existing.classes, model.classes,
            )
            return 1
        if drift > 0.05:
            logger.error("Accuracy drift exceeds 5%% — the committed model is stale")
            return 1
        logger.info("Committed model is consistent with a fresh rebuild.")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    from src.framework.processing.pattern_recognition_tools import (
        PatternRecognitionTools,
    )

    PatternRecognitionTools.save_model(model, args.out)
    logger.info("Wrote %s", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

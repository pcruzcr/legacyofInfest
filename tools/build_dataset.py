#!/usr/bin/env python3
"""
build_dataset.py — Dataset builder for PatternRecognitionTools.

Extracts features from labeled image directories and saves as .npz.

Usage:
    python tools/build_dataset.py <input_dir> <output_path> [--method hog]

Input directory structure:
    input_dir/
        class_name_1/
            image1.png
            image2.png
        class_name_2/
            image1.png
            ...

Output:
    A .npz file with keys 'X' (features, float32) and 'y' (labels, str).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path for src/ imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pygame

from src.framework.processing.vision_tools import VisionTools


def build_dataset(
    input_dir: Path,
    output_path: Path,
    method: str = "hog",
) -> None:
    if not input_dir.exists():
        print(f"Error: input directory not found: {input_dir}")
        sys.exit(1)

    X: list[np.ndarray] = []
    y: list[str] = []

    class_dirs = sorted([d for d in input_dir.iterdir() if d.is_dir()])
    if not class_dirs:
        print(f"Error: no class subdirectories found in {input_dir}")
        sys.exit(1)

    for class_dir in class_dirs:
        label = class_dir.name
        image_files = sorted(class_dir.glob("*.png")) + sorted(class_dir.glob("*.jpg"))
        if not image_files:
            print(f"Warning: no images in {class_dir}, skipping")
            continue

        for img_path in image_files:
            try:
                surf = pygame.image.load(str(img_path)).convert_alpha()
                features = VisionTools.extract_features(surf, method=method)
                X.append(features)
                y.append(label)
            except Exception as e:
                print(f"Warning: could not process {img_path}: {e}")

    if not X:
        print("Error: no features extracted. Check your input directory and image files.")
        sys.exit(1)

    X_arr = np.array(X, dtype=np.float32)
    y_arr = np.array(y, dtype=str)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(str(output_path), X=X_arr, y=y_arr)
    print(f"Dataset saved: {output_path}")
    print(f"  Samples: {len(X_arr)}")
    print(f"  Features: {X_arr.shape[1]}")
    print(f"  Classes: {sorted(set(y))}")


def main() -> None:
    pygame.init()
    parser = argparse.ArgumentParser(description="Build a .npz dataset from labeled images.")
    parser.add_argument("input_dir", type=str, help="Directory with class subfolders")
    parser.add_argument("output_path", type=str, help="Output .npz file path")
    parser.add_argument("--method", type=str, default="hog",
                        choices=["hog", "lbp", "color_hist", "combined"],
                        help="Feature extraction method (default: hog)")
    args = parser.parse_args()
    build_dataset(Path(args.input_dir), Path(args.output_path), method=args.method)
    pygame.quit()


if __name__ == "__main__":
    main()

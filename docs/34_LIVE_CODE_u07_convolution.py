"""
Live Coding: Manual Convolution (Unit VII).

Professor runs this in lecture to demonstrate how convolution
kernels work at the pixel level.
"""
from __future__ import annotations

import numpy as np


def apply_kernel(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Manually apply convolution kernel to 2D image."""
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2
    padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode="edge")
    result = np.zeros_like(image)

    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            patch = padded[y:y + kh, x:x + kw]
            result[y, x] = np.sum(patch * kernel)

    return np.clip(result, 0, 255).astype(np.uint8)


# Standard kernels
IDENTITY = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]], dtype=np.float32)
SHARPEN = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
BOX_BLUR = np.ones((3, 3), dtype=np.float32) / 9.0
EDGE = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
EMBOSS = np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]], dtype=np.float32)


# ---- Lecture Demo ----
if __name__ == "__main__":
    # Create a simple test image (8x8 with a diagonal line)
    img = np.zeros((8, 8), dtype=np.uint8)
    for i in range(8):
        img[i, i] = 255

    print("Original:")
    print(img)

    for name, kernel in [
        ("Identity", IDENTITY),
        ("Sharpen", SHARPEN),
        ("Box Blur", BOX_BLUR),
        ("Edge Detect", EDGE),
        ("Emboss", EMBOSS),
    ]:
        result = apply_kernel(img, kernel)
        print(f"\n{name}:")
        print(result)

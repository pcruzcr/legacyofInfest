"""
Live Coding: Implement Vector2 from scratch (Unit II).

Professor runs this in lecture, filling in methods live.
Students follow along.
"""
from __future__ import annotations

import math


class Vector2:
    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2:
        return Vector2(self.x * scalar, self.y * scalar)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self) -> Vector2:
        """Return unit vector (length=1) in same direction."""
        ln = self.length()
        if ln == 0:
            return Vector2(0, 0)
        return Vector2(self.x / ln, self.y / ln)

    def dot(self, other: Vector2) -> float:
        return self.x * other.x + self.y * other.y

    def distance_to(self, other: Vector2) -> float:
        return (self - other).length()

    def __repr__(self) -> str:
        return f"Vector2({self.x:.2f}, {self.y:.2f})"


# ---- Lecture Demo ----
if __name__ == "__main__":
    a = Vector2(3, 4)
    b = Vector2(1, 2)

    print(f"a = {a}, b = {b}")
    print(f"a + b = {a + b}")
    print(f"a - b = {a - b}")
    print(f"a * 2 = {a * 2}")
    print(f"|a| = {a.length():.2f}")
    print(f"a normalized = {a.normalize()}")
    print(f"|a.normalize()| = {a.normalize().length():.2f}")
    print(f"a dot b = {a.dot(b):.2f}")
    print(f"distance(a, b) = {a.distance_to(b):.2f}")

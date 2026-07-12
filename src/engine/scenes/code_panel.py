"""
CodePanel — Overlay that shows the algorithm code running in a lab scene.

Toggle with C key. Shows source code of key algorithms while
the student manipulates parameters, bridging theory and practice.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.scenes.demo_common import COLOR_HIGHLIGHT


_CODE_EXAMPLES: dict[str, list[str]] = {
    "normalize": [
        "def normalize(v: Vector2) -> Vector2:",
        "    length = sqrt(v.x * v.x + v.y * v.y)",
        "    if length == 0:",
        "        return Vector2(0, 0)",
        "    return Vector2(v.x / length, v.y / length)",
    ],
    "dot_product": [
        "def dot(a: Vector2, b: Vector2) -> float:",
        "    return a.x * b.x + a.y * b.y",
        "",
        "# a dot b = |a| * |b| * cos(theta)",
    ],
    "distance": [
        "def distance(a: Vector2, b: Vector2) -> float:",
        "    dx = a.x - b.x",
        "    dy = a.y - b.y",
        "    return sqrt(dx * dx + dy * dy)",
    ],
    "lerp": [
        "def lerp(a: float, b: float, t: float) -> float:",
        "    return a + (b - a) * t",
    ],
    "bezier": [
        "def de_casteljau(points: list[Vector2], t: float) -> Vector2:",
        "    n = len(points)",
        "    work = points.copy()",
        "    for k in range(1, n):",
        "        for i in range(n - k):",
        "            work[i] = lerp(work[i], work[i+1], t)",
        "    return work[0]",
    ],
    "convolution": [
        "def apply_kernel(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:",
        "    kh, kw = kernel.shape",
        "    pad_h, pad_w = kh // 2, kw // 2",
        "    padded = np.pad(image, ((pad_h,pad_h), (pad_w,pad_w)), mode='edge')",
        "    result = np.zeros_like(image)",
        "    for y in range(image.shape[0]):",
        "        for x in range(image.shape[1]):",
        "            patch = padded[y:y+kh, x:x+kw]",
        "            result[y,x] = np.sum(patch * kernel)",
        "    return result",
    ],
    "sobel": [
        "def sobel_edge(image: np.ndarray) -> np.ndarray:",
        "    Gx = np.array([[-1,0,1],[-2,0,2],[-1,0,1]])",
        "    Gy = np.array([[-1,-2,-1],[0,0,0],[1,2,1]])",
        "    grad_x = apply_kernel(image, Gx)",
        "    grad_y = apply_kernel(image, Gy)",
        "    magnitude = sqrt(grad_x**2 + grad_y**2)",
        "    return magnitude.clip(0, 255).astype(np.uint8)",
    ],
    "rgb_to_hsv": [
        "def rgb_to_hsv(r: int, g: int, b: int) -> tuple[float,float,float]:",
        "    r, g, b = r/255, g/255, b/255",
        "    cmax, cmin = max(r,g,b), min(r,g,b)",
        "    delta = cmax - cmin",
        "    if delta == 0: h = 0.0",
        "    elif cmax == r: h = ((g-b)/delta) % 6",
        "    elif cmax == g: h = ((b-r)/delta) + 2",
        "    else: h = ((r-g)/delta) + 4",
        "    h = h * 60",
        "    s = delta / cmax if cmax > 0 else 0",
        "    v = cmax",
        "    return (h, s, v)",
    ],
    "gaussian_blur": [
        "def gaussian_kernel(sigma: float, size: int) -> np.ndarray:",
        "    ax = np.linspace(-(size-1)/2, (size-1)/2, size)",
        "    x, y = np.meshgrid(ax, ax)",
        "    kernel = exp(-(x*x + y*y) / (2*sigma*sigma))",
        "    return kernel / kernel.sum()",
    ],
    "threshold": [
        "def threshold_binary(image: np.ndarray, T: int) -> np.ndarray:",
        "    result = np.zeros_like(image)",
        "    result[image > T] = 255",
        "    return result",
    ],
}


class CodePanel:
    """Overlay that renders algorithm source code over a lab scene. Toggle with C key."""

    def __init__(self, code_key: str = "normalize", custom_lines: list[str] | None = None) -> None:
        """Initialize with a code key from _CODE_EXAMPLES or custom lines."""
        self._active: bool = False
        self._code_key: str = code_key
        self._custom_lines: list[str] | None = custom_lines

    @property
    def active(self) -> bool:
        """Whether the code panel is currently displayed."""
        return self._active

    def toggle(self) -> None:
        """Show or hide the code panel."""
        self._active = not self._active

    def set_code(self, key: str, lines: list[str] | None = None) -> None:
        """Switch which algorithm code to display."""
        self._code_key = key
        self._custom_lines = lines

    def draw(self, surface: pygame.Surface) -> None:
        """Render the code panel overlay onto the given surface."""
        if not self._active:
            return

        lines = self._custom_lines if self._custom_lines is not None else _CODE_EXAMPLES.get(self._code_key, ["# no code available"])

        overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))

        box_w = 380
        box_h = 40 + len(lines) * 14
        bx = (settings.INTERNAL_WIDTH - box_w) // 2
        by = (settings.INTERNAL_HEIGHT - box_h) // 2

        pygame.draw.rect(overlay, (15, 15, 40), (bx, by, box_w, box_h))
        pygame.draw.rect(overlay, COLOR_HIGHLIGHT, (bx, by, box_w, box_h), 1)

        font = pygame.font.Font(None, 12)
        title_font = pygame.font.Font(None, 14)

        title = title_font.render(f"Algorithm: {self._code_key.replace('_', ' ').title()}", True, COLOR_HIGHLIGHT)
        overlay.blit(title, (bx + 8, by + 6))

        for i, line in enumerate(lines):
            color = (120, 190, 120) if line.startswith("def ") or line.startswith("#") else (200, 200, 200)
            txt = font.render(f"  {line}", True, color)
            overlay.blit(txt, (bx + 8, by + 24 + i * 14))

        hint = font.render("  Press C to close", True, (100, 100, 140))
        overlay.blit(hint, (bx + 8, by + box_h - 16))

        surface.blit(overlay, (0, 0))


_PANEL: CodePanel | None = None


def get_code_panel() -> CodePanel:
    """Return the module-level singleton CodePanel instance."""
    global _PANEL
    if _PANEL is None:
        _PANEL = CodePanel()
    return _PANEL

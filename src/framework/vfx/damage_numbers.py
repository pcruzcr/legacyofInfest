from __future__ import annotations

import random

import pygame

from src.engine.core import settings
from src.engine.utils.surface_pool import get_pool


class DamageNumber:
    """Un número de daño que sube y se desvanece.

    AUD-158 — el desvanecimiento en bloque
    =======================================
    La superficie del texto se cachea por `(texto, crítico)` y se comparte
    entre todos los números iguales que haya en pantalla. Sobre esa superficie
    **compartida** se llamaba a `set_alpha()` en cada `draw`.

    El alfa es estado de la superficie, no del blit. Así que el último número
    en dibujarse imponía su transparencia a todos los demás: cuatro golpes de
    «5» seguidos se desvanecían de golpe cuando el más viejo se apagaba, en
    vez de uno detrás de otro. Comprobado antes de tocar nada: dibujar un
    número al 10 % de vida dejaba el alfa del otro, recién creado, en 25.

    La solución no es dejar de cachear —renderizar texto por fotograma es caro—
    sino no escribir en lo cacheado: el alfa se aplica sobre una copia que sale
    del `SurfacePool`, igual que el resto de los efectos del proyecto.
    """

    _font_cache: dict[int, pygame.font.Font] = {}
    _render_cache: dict[tuple[str, bool], pygame.Surface] = {}

    #: Tope del caché de texto renderizado.
    #:
    #: Es un atributo **de clase**: vive lo que el proceso y no lo vaciaba
    #: nadie. En la práctica el daño produce pocas cadenas distintas, pero
    #: «en la práctica» no es una cota, y basta un escenario que muestre daño
    #: con decimales para que crezca sin fin. Mismo criterio y mismo número que
    #: `LightSystem._MAX_CACHED_GRADIENTS`.
    _MAX_CACHE = 128

    @classmethod
    def clear_caches(cls) -> None:
        """Suelta el texto cacheado. La llama el arranque de escenario."""
        cls._render_cache.clear()

    def __init__(self, x: float, y: float, amount_text: str, is_critical: bool = False) -> None:
        self.x = x
        self.y = y
        self.amount_text = amount_text
        self.is_critical = is_critical
        self.life: float = 1.0
        self.max_life: float = 1.0
        self.vy: float = -60.0 - random.random() * 30.0
        self.vx: float = random.uniform(-20.0, 20.0)
        size = 18 if is_critical else 14
        font = self._font_cache.get(size)
        if font is None:
            font = pygame.font.Font(None, size)
            self._font_cache[size] = font
        color = (255, 220, 50) if is_critical else (255, 255, 200)
        cache_key = (amount_text, is_critical)
        surf = self._render_cache.get(cache_key)
        if surf is None:
            surf = font.render(amount_text, True, color)
            if len(self._render_cache) >= self._MAX_CACHE:
                # Se vacía entero en vez de desalojar el menos usado: llevar
                # un LRU aquí cuesta más de lo que ahorra, y llegar a 128
                # cadenas distintas de daño ya es un caso patológico.
                self._render_cache.clear()
            self._render_cache[cache_key] = surf
        self._surf = surf

    @property
    def alive(self) -> bool:
        return self.life > 0

    def update(self, dt: float) -> None:
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 120.0 * dt

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        alpha = int(min(255, (self.life / self.max_life) * 255))
        sx = int(self.x - camera_offset.x)
        sy = int(self.y - camera_offset.y)
        if sx < -50 or sx > settings.INTERNAL_WIDTH + 50 or sy < -50 or sy > settings.INTERNAL_HEIGHT + 50:
            return
        # AUD-158 — el alfa NO se escribe sobre `self._surf`.
        #
        # Esa superficie está cacheada y compartida por todos los números con
        # el mismo texto. `set_alpha` es estado de la superficie, así que el
        # último en dibujarse imponía su transparencia a los demás y cuatro
        # golpes seguidos se apagaban a la vez.
        ancho, alto = self._surf.get_size()
        if self.is_critical:
            escala = 1.0 + 0.3 * (1.0 - self.life / self.max_life)
            ancho, alto = int(ancho * escala), int(alto * escala)

        pool = get_pool()
        propia = pool.borrow(ancho, alto, pygame.SRCALPHA,
                             fill_color=(0, 0, 0, 0))
        if self.is_critical:
            pygame.transform.scale(self._surf, (ancho, alto), propia)
        else:
            propia.blit(self._surf, (0, 0))
        propia.set_alpha(alpha)
        surface.blit(propia, propia.get_rect(center=(sx, sy)))
        pool.return_surface(propia)


class DamageNumberManager:
    def __init__(self) -> None:
        self._numbers: list[DamageNumber] = []

    def add(self, x: float, y: float, text: str, is_critical: bool = False) -> None:
        self._numbers.append(DamageNumber(x, y, text, is_critical))

    def clear(self) -> None:
        self._numbers.clear()

    def update(self, dt: float) -> None:
        for n in self._numbers:
            n.update(dt)
        self._numbers = [n for n in self._numbers if n.alive]

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        for n in self._numbers:
            n.draw(surface, camera_offset)

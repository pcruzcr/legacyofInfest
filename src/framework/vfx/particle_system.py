from __future__ import annotations

import numpy as np
import pygame

# numba is an OPTIONAL accelerator here, not a hard requirement (AUD-006b).
#
# Unlike the scalar helpers in engine.utils.math_utils — where JIT compilation
# measured *slower* than plain Python and was removed — this kernel is a tight
# loop over N particle arrays, which is exactly the workload numba is good at.
# So we keep it, but degrade gracefully: without numba installed the game runs
# the vectorised NumPy path below instead of refusing to start.
try:
    import numba

    _HAS_NUMBA = True
except ImportError:  # pragma: no cover - exercised only on installs without numba
    numba = None  # type: ignore[assignment]
    _HAS_NUMBA = False


def _update_particles_py(
    x: np.ndarray, y: np.ndarray, vx: np.ndarray, vy: np.ndarray,
    life: np.ndarray, max_life: np.ndarray, alpha: np.ndarray,
    size: np.ndarray, gravity: np.ndarray, friction: np.ndarray, dt: float,
) -> None:
    """Vectorised NumPy fallback. Same semantics as the JIT kernel."""
    alive = life > 0
    if not alive.any():
        return
    life[alive] -= dt

    expired = alive & (life <= 0)
    alpha[expired] = 0

    live = alive & (life > 0)
    if not live.any():
        return
    # max_life is guaranteed > 0 for live particles by the emitter, but guard
    # anyway so a malformed config cannot produce a divide-by-zero warning.
    safe_max = np.where(max_life[live] > 0, max_life[live], 1.0)
    alpha[live] = np.clip((255.0 * life[live] / safe_max).astype(np.int32), 0, 255)
    vy[live] += gravity[live] * dt
    f = friction[live] ** dt
    vx[live] *= f
    vy[live] *= f
    x[live] += vx[live] * dt
    y[live] += vy[live] * dt


if _HAS_NUMBA:

    @numba.njit(cache=True, parallel=False)
    def _update_particles_njit(
        x: np.ndarray, y: np.ndarray, vx: np.ndarray, vy: np.ndarray,
        life: np.ndarray, max_life: np.ndarray, alpha: np.ndarray,
        size: np.ndarray, gravity: np.ndarray, friction: np.ndarray, dt: float,
    ) -> None:
        n = len(x)
        for i in numba.prange(n):
            if life[i] <= 0:
                continue
            life[i] -= dt
            if life[i] <= 0:
                alpha[i] = 0
                continue
            t = life[i] / max_life[i]
            alpha[i] = max(0, min(255, int(255 * t)))
            vy[i] += gravity[i] * dt
            f = friction[i] ** dt
            vx[i] *= f
            vy[i] *= f
            x[i] += vx[i] * dt
            y[i] += vy[i] * dt

else:
    _update_particles_njit = _update_particles_py


_warmed_up = False


def warmup() -> float:
    """Compila el núcleo JIT ahora, para que no se compile a mitad de partida.

    AUD-082 — el tirón de medio segundo en la pantalla de título
    -----------------------------------------------------------
    `@numba.njit` compila en la **primera llamada**, no al importar. Medido en
    `TitleScene`: mediana de 0,70 ms por fotograma y **un fotograma de 376 ms**
    —el primero en el que existe una partícula—. Son veintidós fotogramas
    perdidos de golpe, y justo en la primera pantalla que ve el jugador.

    `cache=True` guarda el resultado en `__pycache__`, así que en la mayoría de
    los equipos el tirón sólo ocurre la primera vez... salvo que la instalación
    sea de sólo lectura, o que el estudiante acabe de clonar el repositorio, o
    que cambie de versión de Python o de numba. Es decir: le pasa a todo el
    mundo al menos una vez, y a algunos siempre.

    Llamar a esto desde la pantalla de carga mueve el coste al único sitio
    donde una espera no es un defecto. Devuelve los segundos que costó, para
    que quien llame pueda registrarlo.

    Es idempotente: la segunda llamada no hace nada.
    """
    global _warmed_up
    if _warmed_up:
        return 0.0
    _warmed_up = True
    if not _HAS_NUMBA:
        return 0.0

    import time

    # Un array de una partícula basta: lo que se compila es la firma, no el
    # tamaño. Los tipos tienen que coincidir exactamente con los que usa
    # `ParticleEmitter`, o numba compilará una segunda especialización en
    # tiempo de juego y el tirón volverá.
    uno = np.ones(1, dtype=np.float32)
    inicio = time.perf_counter()
    _update_particles_njit(
        uno.copy(), uno.copy(), uno.copy(), uno.copy(),
        uno.copy(), uno.copy(), np.ones(1, dtype=np.int32),
        np.ones(1, dtype=np.int32), uno.copy(), uno.copy(), 1 / 60,
    )
    return time.perf_counter() - inicio


class BurstConfig:
    __slots__ = (
        "color",
        "count",
        "friction",
        "gravity",
        "lifetime",
        "size_max",
        "size_min",
        "speed",
        "spread",
    )

    def __init__(
        self, count: int, speed: float, lifetime: float,
        size: tuple[int, int], color: tuple[int, int, int],
        spread: float = 360.0, gravity: float = 0.0,
        friction: float = 1.0,
    ) -> None:
        self.count = count
        self.speed = speed
        self.lifetime = lifetime
        self.size_min, self.size_max = size
        self.color = color
        self.spread = spread
        self.gravity = gravity
        self.friction = friction


class ParticleEmitter:
    def __init__(self) -> None:
        self.x: np.ndarray = np.empty(0, dtype=np.float32)
        self.y: np.ndarray = np.empty(0, dtype=np.float32)
        self.vx: np.ndarray = np.empty(0, dtype=np.float32)
        self.vy: np.ndarray = np.empty(0, dtype=np.float32)
        self.life: np.ndarray = np.empty(0, dtype=np.float32)
        self.max_life: np.ndarray = np.empty(0, dtype=np.float32)
        self.alpha: np.ndarray = np.empty(0, dtype=np.int32)
        self.size: np.ndarray = np.empty(0, dtype=np.int32)
        self.gravity: np.ndarray = np.empty(0, dtype=np.float32)
        self.friction: np.ndarray = np.empty(0, dtype=np.float32)
        self._colors: list[tuple[int, int, int]] = []

    def _append_particles(
        self, count: int,
        x_val: float, y_val: float,
        vx_arr: np.ndarray, vy_arr: np.ndarray,
        sizes: np.ndarray, lives: np.ndarray,
        alphas: np.ndarray, gravities: np.ndarray,
        frictions: np.ndarray, color: tuple[int, int, int],
    ) -> None:
        self.x = np.concatenate([self.x, np.full(count, x_val, dtype=np.float32)])
        self.y = np.concatenate([self.y, np.full(count, y_val, dtype=np.float32)])
        self.vx = np.concatenate([self.vx, vx_arr])
        self.vy = np.concatenate([self.vy, vy_arr])
        self.life = np.concatenate([self.life, lives])
        self.max_life = np.concatenate([self.max_life, lives])
        self.alpha = np.concatenate([self.alpha, alphas])
        self.size = np.concatenate([self.size, sizes])
        self.gravity = np.concatenate([self.gravity, gravities])
        self.friction = np.concatenate([self.friction, frictions])
        self._colors.extend([color] * count)

    def emit(self, x: float, y: float, config: BurstConfig) -> None:
        n = config.count
        if n <= 0:
            return
        angles = np.random.uniform(0, config.spread, n)
        rad = np.radians(angles)
        spd = np.random.uniform(config.speed * 0.5, config.speed, n)
        vx_arr = np.cos(rad) * spd
        vy_arr = np.sin(rad) * spd
        sizes = np.random.randint(config.size_min, config.size_max + 1, n)
        lives = np.full(n, config.lifetime, dtype=np.float32)
        alphas = np.full(n, 255, dtype=np.int32)
        gravities = np.full(n, config.gravity, dtype=np.float32)
        frictions = np.full(n, config.friction, dtype=np.float32)
        self._append_particles(n, x, y, vx_arr.astype(np.float32), vy_arr.astype(np.float32),
                               sizes.astype(np.int32), lives, alphas, gravities, frictions, config.color)

    def emit_directed(
        self, x: float, y: float, angle: float, speed: float,
        count: int, lifetime: float, size: tuple[int, int],
        color: tuple[int, int, int], spread: float = 30.0,
        gravity: float = 0.0, friction: float = 1.0,
    ) -> None:
        if count <= 0:
            return
        angles = angle + np.random.uniform(-spread, spread, count)
        rad = np.radians(angles)
        spd = np.random.uniform(speed * 0.7, speed, count)
        vx_arr = np.cos(rad) * spd
        vy_arr = np.sin(rad) * spd
        sz = np.random.randint(size[0], size[1] + 1, count)
        lives = np.full(count, lifetime, dtype=np.float32)
        alphas = np.full(count, 255, dtype=np.int32)
        gravities = np.full(count, gravity, dtype=np.float32)
        frictions = np.full(count, friction, dtype=np.float32)
        self._append_particles(count, x, y, vx_arr.astype(np.float32), vy_arr.astype(np.float32),
                               sz.astype(np.int32), lives, alphas, gravities, frictions, color)

    def update(self, dt: float) -> None:
        if len(self.x) == 0:
            return
        _update_particles_njit(
            self.x, self.y, self.vx, self.vy,
            self.life, self.max_life, self.alpha,
            self.size, self.gravity, self.friction, dt,
        )
        alive = self.life > 0
        self.x = self.x[alive]
        self.y = self.y[alive]
        self.vx = self.vx[alive]
        self.vy = self.vy[alive]
        self.life = self.life[alive]
        self.max_life = self.max_life[alive]
        self.alpha = self.alpha[alive]
        self.size = self.size[alive]
        self.gravity = self.gravity[alive]
        self.friction = self.friction[alive]
        if len(self._colors) > 0:
            idx = np.where(alive)[0]
            self._colors = [self._colors[i] for i in idx]

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        ox = int(offset.x)
        oy = int(offset.y)
        for i in range(len(self.x)):
            if self.life[i] <= 0 or self.alpha[i] <= 0:
                continue
            sx = int(self.x[i]) - ox
            sy = int(self.y[i]) - oy
            c = (*self._colors[i], min(255, self.alpha[i]))
            sz = max(1, int(self.size[i]))
            pygame.draw.rect(surface, c, (sx - sz // 2, sy - sz // 2, sz, sz))

    def clear(self) -> None:
        self.x = np.empty(0, dtype=np.float32)
        self.y = np.empty(0, dtype=np.float32)
        self.vx = np.empty(0, dtype=np.float32)
        self.vy = np.empty(0, dtype=np.float32)
        self.life = np.empty(0, dtype=np.float32)
        self.max_life = np.empty(0, dtype=np.float32)
        self.alpha = np.empty(0, dtype=np.int32)
        self.size = np.empty(0, dtype=np.int32)
        self.gravity = np.empty(0, dtype=np.float32)
        self.friction = np.empty(0, dtype=np.float32)
        self._colors.clear()

    @property
    def count(self) -> int:
        return len(self.x)


class ParticleSystem:
    def __init__(self) -> None:
        self._emitters: dict[str, ParticleEmitter] = {}

    def get_emitter(self, name: str = "_default") -> ParticleEmitter:
        if name not in self._emitters:
            self._emitters[name] = ParticleEmitter()
        return self._emitters[name]

    def update(self, dt: float) -> None:
        for em in self._emitters.values():
            em.update(dt)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        for em in self._emitters.values():
            em.draw(surface, offset)

    def clear(self) -> None:
        self._emitters.clear()

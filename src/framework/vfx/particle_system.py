from __future__ import annotations

from typing import Any

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
    """Partículas en arreglos paralelos, con capacidad reservada.

    AUD-275 — por qué ya no se reasigna cada fotograma
    ---------------------------------------------------
    La versión anterior compactaba con máscara booleana::

        alive = self.life > 0
        self.x = self.x[alive]      # arreglo nuevo... diez veces
        self._colors = [self._colors[i] for i in idx]

    Diez asignaciones de arreglo **por emisor y por fotograma**, más una lista
    de Python reconstruida elemento a elemento —3.840 en regimen— y otras diez
    asignaciones por rafaga via `np.concatenate`. AUD-214 ya lo habia rozado
    («el color vive en una lista de tuplas, no en un array») y lo dejo porque
    entonces tocaba el dibujado.

    Ahora: capacidad reservada y un contador de vivas, que es exactamente el
    patron que `EnjambreDeBalas` usa en este mismo repositorio. Las ranuras
    vivas van **empaquetadas al principio**, asi que todo el trabajo se hace
    sobre `[:n]`.

    Lo que **no** cambia: `BurstConfig.color` sigue siendo una tupla, que es lo
    que ven los escenarios. Lo que se reordena es la representacion interna.
    """

    #: Capacidad inicial. 256 cubre las rafagas normales de impacto y muerte
    #: sin reservar de mas en los quince emisores que puede tener una escena.
    CAPACIDAD_INICIAL: int = 256

    #: Nombres de los diez arreglos escalares, en un solo sitio: tenerlos
    #: repetidos en reservar/crecer/compactar es como se acaba con uno que se
    #: olvida y una particula que conserva la velocidad de otra.
    _CAMPOS: tuple[tuple[str, object], ...] = (
        ("x", np.float32), ("y", np.float32),
        ("vx", np.float32), ("vy", np.float32),
        ("life", np.float32), ("max_life", np.float32),
        ("alpha", np.int32), ("size", np.int32),
        ("gravity", np.float32), ("friction", np.float32),
    )

    def __init__(self, capacidad: int = CAPACIDAD_INICIAL,
                 rng: Any = None) -> None:
        self._n: int = 0
        self._capacidad: int = 0
        #: AUD-386 — el azar de ESTE emisor, no el global de NumPy.
        #:
        #: Con el global compartido, añadir una tirada en un sitio desplazaba
        #: el resultado de todos los demás: una chispa más en el golpe movía la
        #: dispersión de la lluvia. Eso obliga a escribir tolerante cualquier
        #: prueba que toque partículas, y una prueba tolerante deja pasar las
        #: regresiones pequeñas — el coste que ya se pagó en AUD-359.
        #:
        #: Sin `rng` se deriva del global, que `azar.sembrar()` fija al
        #: arrancar (AUD-375/385): quien construya un emisor a secas —las
        #: entregas, `ParticleSystem.get_emitter`, media suite— hereda la
        #: reproducibilidad sin enterarse de que existe una semilla.
        from src.engine.core import azar

        self._rng = rng if rng is not None else azar.generador_numpy()
        self._reservar(max(1, capacidad))

    def _reservar(self, capacidad: int) -> None:
        """Crea los arreglos con la capacidad pedida, conservando lo vivo."""
        n = self._n
        for nombre, tipo in self._CAMPOS:
            nuevo = np.zeros(capacidad, dtype=tipo)
            if n:
                nuevo[:n] = getattr(self, nombre)[:n]
            setattr(self, nombre, nuevo)
        #: Color por particula. Arreglo y no lista de tuplas: la lista era lo
        #: que obligaba a un bucle de Python por fotograma al compactar.
        nuevas = np.zeros((capacidad, 3), dtype=np.uint8)
        if n:
            nuevas[:n] = self.colores[:n]
        self.colores = nuevas
        self._capacidad = capacidad

    def _crecer_para(self, extra: int) -> None:
        """Dobla la capacidad hasta que quepan `extra` particulas mas.

        Doblar y no crecer lo justo: con incrementos ajustados, una lluvia de
        rafagas pequenas reservaria memoria en casi todas. Doblando, el coste
        queda amortizado y en regimen no se reserva nunca.
        """
        if self._n + extra <= self._capacidad:
            return
        nueva = max(self._capacidad, 1)
        while self._n + extra > nueva:
            nueva *= 2
        self._reservar(nueva)

    def _append_particles(
        self, count: int,
        x_val: float, y_val: float,
        vx_arr: np.ndarray, vy_arr: np.ndarray,
        sizes: np.ndarray, lives: np.ndarray,
        alphas: np.ndarray, gravities: np.ndarray,
        frictions: np.ndarray, color: tuple[int, int, int],
    ) -> None:
        self._crecer_para(count)
        a, b = self._n, self._n + count
        self.x[a:b] = x_val
        self.y[a:b] = y_val
        self.vx[a:b] = vx_arr
        self.vy[a:b] = vy_arr
        self.life[a:b] = lives
        self.max_life[a:b] = lives
        self.alpha[a:b] = alphas
        self.size[a:b] = sizes
        self.gravity[a:b] = gravities
        self.friction[a:b] = frictions
        self.colores[a:b] = color
        self._n = b

    def emit(self, x: float, y: float, config: BurstConfig) -> None:
        n = config.count
        if n <= 0:
            return
        angles = self._rng.uniform(0, config.spread, n)
        rad = np.radians(angles)
        spd = self._rng.uniform(config.speed * 0.5, config.speed, n)
        vx_arr = np.cos(rad) * spd
        vy_arr = np.sin(rad) * spd
        sizes = self._rng.integers(config.size_min, config.size_max + 1, n)
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
        angles = angle + self._rng.uniform(-spread, spread, count)
        rad = np.radians(angles)
        spd = self._rng.uniform(speed * 0.7, speed, count)
        vx_arr = np.cos(rad) * spd
        vy_arr = np.sin(rad) * spd
        sz = self._rng.integers(size[0], size[1] + 1, count)
        lives = np.full(count, lifetime, dtype=np.float32)
        alphas = np.full(count, 255, dtype=np.int32)
        gravities = np.full(count, gravity, dtype=np.float32)
        frictions = np.full(count, friction, dtype=np.float32)
        self._append_particles(count, x, y, vx_arr.astype(np.float32), vy_arr.astype(np.float32),
                               sz.astype(np.int32), lives, alphas, gravities, frictions, color)

    def update(self, dt: float) -> None:
        """Avanza la fisica y compacta **en su sitio** (AUD-275).

        La compactacion usa un unico arreglo de indices y `np.take(..., out=)`,
        que escribe sobre el mismo buffer. Antes eran diez arreglos nuevos por
        fotograma mas una lista de Python de miles de elementos.

        Si no ha muerto ninguna, no se mueve nada: es el caso comun mientras
        una rafaga esta viva, y detectarlo cuesta una comparacion.
        """
        n = self._n
        if n == 0:
            return
        _update_particles_njit(
            self.x[:n], self.y[:n], self.vx[:n], self.vy[:n],
            self.life[:n], self.max_life[:n], self.alpha[:n],
            self.size[:n], self.gravity[:n], self.friction[:n], dt,
        )
        idx = np.flatnonzero(self.life[:n] > 0)
        k = int(idx.size)
        if k == n:
            return
        if k:
            for nombre, _tipo in self._CAMPOS:
                arr = getattr(self, nombre)
                np.take(arr[:n], idx, out=arr[:k])
            np.take(self.colores[:n], idx, axis=0, out=self.colores[:k])
        self._n = k

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Dibuja cada partícula viva como un cuadrado opaco.

        AUD-214 — el coste no estaba en pintar, estaba en leer los arrays
        ------------------------------------------------------------------
        `update` lleva desde AUD-006b siendo SoA con numpy, pero este bucle
        seguía haciendo lo contrario: `self.x[i]` sobre un `ndarray` devuelve
        un escalar de numpy —un objeto nuevo por acceso— y aquí había cinco
        accesos, tres conversiones a `int` y dos comparaciones por partícula.
        Medido en esta máquina con 2.008 partículas vivas y destino de
        800 × 600: **8,02 ms** de mediana, la mitad del fotograma a 60 fps.

        La solución no es dibujar de otra forma, es *leer* de otra forma:
        se filtran, desplazan y convierten los cuatro arrays de una sola
        pasada vectorizada y se bajan a listas de Python (`tolist()`), de modo
        que el bucle sólo toca enteros nativos. Medido igual: **3,11 ms**
        (2,6×). Con 508 partículas —una carga de combate realista— pasa de
        1,97 ms a 0,56 ms (3,5×).

        Dos decisiones que parecen mejorables y no lo son:

        * `Surface.fill` en vez de `pygame.draw.rect`. Para un rectángulo
          relleno sin borde son la misma operación, pero `fill` se salta el
          despacho del módulo `draw` y sale otro ~30 % más barato. Los
          píxeles son idénticos —incluido el canal alfa, el recorte por
          `set_clip` y los rectángulos que caen fuera— y eso lo comprueba
          `tests/test_dibujado_de_particulas.py` contra la implementación
          anterior, no contra una expectativa escrita a mano.
        * **No** se usa `Surface.blits()` con cuadrados cacheados, que era la
          vía obvia. Medida: sólo 4 % mejor que `fill` con 508 partículas y
          *peor* con 2.008. Y rompe el resultado: `blits` mezcla, mientras
          que `draw.rect` y `fill` escriben, así que sobre un destino con
          `SRCALPHA` el alfa de la partícula se pierde. Más rápido de mentira
          y distinto de verdad.

        AUD-275 cerró el cabo que este comentario dejaba abierto: el color ya
        **no** vive en una lista de tuplas de Python sino en un arreglo
        `(capacidad, 3)`, así que el bucle sólo toca enteros nativos.
        """
        n = self._n
        if n == 0:
            return
        idx = np.flatnonzero((self.life[:n] > 0) & (self.alpha[:n] > 0))
        if idx.size == 0:
            return

        # `astype(np.int32)` trunca hacia cero igual que `int()`, y `>> 1`
        # equivale a `// 2` porque el tamaño ya está acotado a >= 1. Sin esas
        # dos equivalencias el desplazamiento del cuadrado cambiaría un píxel.
        sz = np.maximum(1, self.size[idx])
        xs = (self.x[idx].astype(np.int32) - int(offset.x) - (sz >> 1)).tolist()
        ys = (self.y[idx].astype(np.int32) - int(offset.y) - (sz >> 1)).tolist()
        alphas = np.minimum(255, self.alpha[idx]).tolist()
        sizes = sz.tolist()

        # AUD-275: el color sale del arreglo, no de una lista de tuplas. Un
        # `tolist()` de una sola pasada deja el bucle tocando solo enteros
        # nativos, que es lo que AUD-214 buscaba y no pudo terminar.
        colores = self.colores[idx].tolist()
        fill = surface.fill
        for k in range(int(idx.size)):
            r, g, b = colores[k]
            s = sizes[k]
            fill((r, g, b, alphas[k]), (xs[k], ys[k], s, s))

    def clear(self) -> None:
        """Deja el emisor vacio **sin soltar los arreglos**.

        Reservar de nuevo en cada `clear()` desharia el trabajo de AUD-275: el
        sistema llama a `clear()` al cambiar de escena, y volver a la capacidad
        inicial obligaria a crecer otra vez desde cero en el primer combate.
        """
        self._n = 0

    @property
    def count(self) -> int:
        return self._n

    @property
    def capacidad(self) -> int:
        return self._capacidad


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

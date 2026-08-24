from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class TrailPoint:
    __slots__ = ("alpha", "surface", "x", "y")

    def __init__(self, x: float, y: float, surface: pygame.Surface, alpha: int = 180) -> None:
        self.x = x
        self.y = y
        self.alpha = alpha
        self.surface = surface


class TrailSystem:
    """Imágenes residuales que se desvanecen tras una entidad rápida.

    F1.4 — el intervalo de captura no se usaba
    ------------------------------------------
    `_capture_interval` valía 0,03 s y `_timer` acumulaba el tiempo, pero
    **nadie los comparaba nunca**. El resultado es que se capturaba una imagen
    en cada fotograma: medido, veinte fotogramas de dash producían veinte
    residuos separados por un fotograma cada uno. Eso no se ve como una estela
    de imágenes residuales, se ve como un borrón sólido, y cuesta veinte
    superficies nuevas y veinte `blit` por fotograma.

    Es el mismo patrón que el viento de la tormenta: un valor calculado y
    guardado que nadie lee.
    """

    #: Tope de residuos simultáneos. Con vida de 0,45 s e intervalo de 0,03 s
    #: el régimen es de unos 15; el tope protege de una caída de fotogramas.
    MAX_POINTS = 24

    def __init__(self) -> None:
        self._points: list[TrailPoint] = []
        self._capture_interval: float = 0.03
        self._timer: float = 0.0
        self._cache: dict[tuple[int, int, tuple[int, int, int, int]], pygame.Surface] = {}

    def capture(self, player: Player) -> None:
        """Guarda una imagen residual, si ya toca por intervalo."""
        if player.rect is None:
            return
        if self._timer < self._capture_interval:
            return
        self._timer = 0.0
        self._points.append(TrailPoint(
            player.position.x, player.position.y,
            self._capture_player_surface(player),
        ))
        if len(self._points) > self.MAX_POINTS:
            del self._points[:-self.MAX_POINTS]

    def capture_at(
        self,
        x: float,
        y: float,
        size: tuple[int, int],
        color: tuple[int, int, int, int],
    ) -> None:
        """Residuo para cualquier entidad, no sólo el jugador.

        Existe para que los jefes puedan dejar estela en sus embestidas sin
        tener que fingir ser un `Player`. `capture` sigue existiendo porque el
        jugador es el caso frecuente y merece una llamada corta.
        """
        if self._timer < self._capture_interval:
            return
        self._timer = 0.0
        self._points.append(TrailPoint(x, y, self._silueta(size, color)))
        if len(self._points) > self.MAX_POINTS:
            del self._points[:-self.MAX_POINTS]

    def _capture_player_surface(self, player: Player) -> pygame.Surface:
        """Silueta del jugador: azul intenso al hacer dash, pálida en el aire."""
        color = (100, 150, 255, 120) if player._dash_timer > 0 else (200, 200, 255, 80)
        return self._silueta((player.rect.width, player.rect.height), color)

    def _silueta(
        self, size: tuple[int, int], color: tuple[int, int, int, int],
    ) -> pygame.Surface:
        """Rectángulo de color, reutilizado entre capturas.

        Antes se creaba una `pygame.Surface` nueva en cada captura. Con captura
        por fotograma eran sesenta superficies por segundo, todas idénticas
        salvo el tamaño del sprite, que casi nunca cambia.
        """
        clave = (size[0], size[1], color)
        cacheada = self._cache.get(clave)
        if cacheada is None:
            cacheada = pygame.Surface(size, pygame.SRCALPHA)
            cacheada.fill(color)
            self._cache[clave] = cacheada
        return cacheada

    def update(self, dt: float) -> None:
        self._timer += dt
        for p in self._points:
            p.alpha -= int(400 * dt)
        self._points = [p for p in self._points if p.alpha > 0]

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        # AUD-329 — aquí no se usa `SpriteBatch`, y no es un pendiente.
        #
        # Los residuos comparten la superficie cacheada de `_silueta` y cada
        # uno pide su alfa con `set_alpha` en el momento de dibujar. El lote
        # leería **un solo** alfa para todas las órdenes: verificado con la
        # misma superficie y alfas 180 y 90, `blit` suelto pinta 77 y 38 y
        # `blits` agrupado pinta 77 y 77. Para agrupar sin romper el alfa
        # habría que copiar la superficie por residuo y por fotograma, que es
        # justo lo que F1.4a eliminó. El bucle está acotado por MAX_POINTS
        # (24), así que el lote no tiene qué ganar aquí.
        for p in self._points:
            if p.alpha <= 0:
                continue
            sx = int(p.x - offset.x)
            sy = int(p.y - offset.y)
            p.surface.set_alpha(p.alpha)
            surface.blit(p.surface, (sx, sy))

    def clear(self) -> None:
        self._points.clear()

"""
Module: fog_of_war
System: framework.vfx
Academic Unit: N/A
Description: Fog of war overlay — hides unexplored areas with
editable holes revealed by player/enemy positions.

AUD-111 — enchufado
===================
Este módulo estuvo escrito, documentado (`docs/46_FOG_OF_WAR.md`) y probado en
aislamiento durante meses, y **ninguna escena lo instanciaba**: un jugador no
podía llegar a él por ningún camino. Las pruebas lo mantenían verde y eso
escondía que nadie lo usaba — confirmaban que la pieza funciona, no que
estuviera enchufada.

Ahora lo enciende `StageScene` cuando el TMX declara la propiedad de mapa
`fog_of_war` con un radio en píxeles. Se dibuja **entre el mundo y la
iluminación**: después de la luz taparía los focos que definen lo que se ve, y
antes del mundo no taparía nada.

AUD-213 — el agujero tenía borde de sierra y `hardness` no existía
==================================================================
La máscara era ``pygame.draw.circle(..., alfa 255, radio)``: un disco sólido.
Restado del velo, daba un agujero que pasaba de revelado a opaco en un píxel,
con el escalonado del rasterizador a la vista. Medido sobre un radio de 40 px,
el brillo al 70 %, al 80 %, al 90 % y al 98 % del radio era el mismo número.

Y el constructor aceptaba `hardness`, lo guardaba en `self._hardness` y
**ningún otro sitio del repositorio lo leía**: un contrato anunciado en la
firma y en `docs/46_FOG_OF_WAR.md` que el módulo no cumplía.

Ahora la máscara es un disco degradado y `hardness` decide dónde empieza la
caída. La técnica es la de `LightSource.build_gradient`
(`src/framework/vfx/lighting.py`): campo de distancias con `np.ogrid` y el
alfa escrito de una vez con `surfarray`. Lo que **no** se copia de allí es la
caché de discos: aquélla existe porque un foco parpadeante reconstruye el suyo
cada fotograma (182 MB en diez segundos sin tope, está medido en ese fichero).
Aquí la máscara se construye una sola vez en el constructor y `draw()` la
reutiliza, así que una caché sólo añadiría piezas móviles sin ahorrar nada.
"""
from __future__ import annotations

import numpy as np
import pygame

from src.engine.core import settings


class FogOfWar:
    """Black overlay with alpha holes around revealed positions."""

    #: Opacidad del velo. La máscara se construye con este mismo pico y no con
    #: 255 a propósito: `draw()` la resta con `BLEND_RGBA_SUB`, que satura en
    #: cero, así que todo alfa por encima de 220 revelaría igual que 220 y el
    #: primer tramo del degradado se perdería en el recorte. Igualándolos, el
    #: perfil completo cae dentro del rango que se ve.
    _ALFA_DEL_VELO = 220

    def __init__(self, width: int = settings.INTERNAL_WIDTH, height: int = settings.INTERNAL_HEIGHT,
                 radius: int = 80, hardness: float = 0.6) -> None:
        self._width = width
        self._height = height
        self._radius = radius
        # Se sujeta a [0, 1] porque los valores llegan del TMX en el futuro y
        # un 1,5 daría una banda negativa que invierte el degradado.
        self._hardness = min(1.0, max(0.0, hardness))
        self._overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self._revealed: set[tuple[int, int]] = set()
        self._hole_mask = self._construir_mascara(radius, self._hardness)

    @classmethod
    def _construir_mascara(cls, radius: int, hardness: float) -> pygame.Surface:
        """Disco degradado: revelado en el núcleo, nulo en el borde.

        `hardness` es la fracción del radio que queda **completamente**
        revelada; el resto es la banda donde el velo vuelve. Con 1.0 no hay
        banda y sale el círculo duro de siempre, que es lo que hace que el
        parámetro tenga un extremo compatible con el comportamiento anterior.

        El perfil de la banda es un *smoothstep* (3t²−2t³) y no la rampa lineal
        de `lighting.py`. La razón es que aquí el degradado tiene dos costuras
        —donde acaba el núcleo y donde acaba el radio— y una rampa lineal deja
        la derivada rota en ambas: el ojo lee ese quiebre como un anillo
        (bandas de Mach) justo donde queríamos que no se viera nada. El
        smoothstep llega a cero con pendiente cero por los dos lados. En un
        foco de luz esa costura no molesta porque el disco se mezcla con
        `BLEND_RGBA_MAX` sobre otros focos; aquí se resta de un velo plano y
        queda a la vista.
        """
        lado = radius * 2
        mask = pygame.Surface((lado, lado), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))

        ys, xs = np.ogrid[:lado, :lado]
        dist = np.sqrt((xs - radius) ** 2 + (ys - radius) ** 2)
        nucleo = radius * hardness
        # El suelo de 1 px evita dividir por cero con hardness = 1.0.
        banda = max(1.0, radius - nucleo)
        t = np.clip((dist - nucleo) / banda, 0.0, 1.0)
        revelado = 1.0 - (t * t * (3.0 - 2.0 * t))
        revelado[dist > radius] = 0.0

        # Sólo se toca el alfa: el velo es negro y `BLEND_RGBA_SUB` sobre unos
        # canales de color que ya valen cero no tendría nada que restar.
        alfa = pygame.surfarray.pixels_alpha(mask)
        try:
            alfa[:] = (revelado * cls._ALFA_DEL_VELO).astype(np.uint8)
        finally:
            del alfa
        return mask

    def clear(self) -> None:
        self._revealed.clear()

    def reveal(self, x: float, y: float) -> None:
        self._revealed.add((int(x), int(y)))

    def reveal_all(self, points: list[tuple[float, float]]) -> None:
        for x, y in points:
            self._revealed.add((int(x), int(y)))

    def update(self, dt: float) -> None:
        """No-op placeholder for future fading."""

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        self._overlay.fill((0, 0, 0, self._ALFA_DEL_VELO))
        for x, y in self._revealed:
            sx = x - int(offset.x)
            sy = y - int(offset.y)
            self._overlay.blit(self._hole_mask,
                               (sx - self._radius, sy - self._radius),
                               special_flags=pygame.BLEND_RGBA_SUB)
        surface.blit(self._overlay, (0, 0))

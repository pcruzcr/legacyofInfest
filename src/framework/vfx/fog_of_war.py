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

AUD-338 — el velo respira
==========================
El velo estaba congelado: la máscara se construía una vez y el overlay era
idéntico en cada fotograma. Un jugador quieto miraba una foto. Ahora, con
`animado=True` (el valor por defecto), el radio de los agujeros y el alfa del
velo oscilan despacio en **antifase** —el velo oscurece mientras los agujeros
se encogen y se aclara mientras crecen—, que es el ciclo con el que un velo
parece vivo sin llamar la atención.

La reconstrucción sigue siendo la del comentario de AUD-213: la máscara vive
en `_hole_mask` y sólo se reconstruye cuando cambian (radio, alfa). Con
`animado=False` el módulo vuelve a ser el de siempre, y en `t = 0` ambas
animaciones están en su fase inicial, así que una prueba que no llame a
`update()` dibuja exactamente lo mismo que antes.
"""
from __future__ import annotations

import math

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
                 radius: int = 80, hardness: float = 0.6,
                 animado: bool = True, velocidad: float = 0.15,
                 pulso: float = 3.0, pulso_del_velo: float = 6.0) -> None:
        self._width = width
        self._height = height
        self._radius = radius
        # Se sujeta a [0, 1] porque los valores llegan del TMX en el futuro y
        # un 1,5 daría una banda negativa que invierte el degradado.
        self._hardness = min(1.0, max(0.0, hardness))
        # El pulso nunca puede comerse el radio entero: un agujero que llega a
        # cero "respira" para dejar de existir un instante, que es un parpadeo.
        self._pulso = min(pulso, radius - 1)
        self._pulso_del_velo = max(0.0, pulso_del_velo)
        self._velocidad = max(0.0, velocidad)
        self._animado = animado
        self._t = 0.0
        self._radio_actual = radius
        self._alfa_actual = self._ALFA_DEL_VELO
        self._overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self._revealed: set[tuple[int, int]] = set()
        self._hole_mask = self._construir_mascara(radius, self._hardness)

    @classmethod
    def _construir_mascara(cls, radius: int, hardness: float,
                           alfa_pico: int = 220) -> pygame.Surface:
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
            alfa[:] = (revelado * alfa_pico).astype(np.uint8)
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
        """Avanza el reloj de la animación (AUD-338).

        Antes era un no-op anunciando un "future fading" que no llegó; ahora
        es el corazón del respiro. Sin llamarlo, el velo se queda en su fase
        inicial, que coincide con el comportamiento de siempre.
        """
        self._t += dt

    def _fase(self) -> float:
        """Ángulo del ciclo de respiro. La fase cero es el velo estático."""
        return self._t * self._velocidad * math.tau

    def _perfil_de_respiro(self) -> tuple[int, int]:
        """(radio, alfa) del fotograma, o el par estático si no hay animación."""
        if not self._animado:
            return self._radius, self._ALFA_DEL_VELO
        fase = self._fase()
        # Antifase: el velo se oscurece mientras el agujero se encoge.
        radio = self._radius + round(math.sin(fase) * self._pulso)
        alfa = self._ALFA_DEL_VELO + round(math.sin(fase + math.pi) * self._pulso_del_velo)
        return radio, max(0, min(255, alfa))

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        radio, alfa = self._perfil_de_respiro()
        if (radio, alfa) != (self._radio_actual, self._alfa_actual):
            self._hole_mask = self._construir_mascara(radio, self._hardness, alfa)
            self._radio_actual, self._alfa_actual = radio, alfa
        self._overlay.fill((0, 0, 0, alfa))
        for x, y in self._revealed:
            sx = x - int(offset.x)
            sy = y - int(offset.y)
            self._overlay.blit(self._hole_mask,
                               (sx - radio, sy - radio),
                               special_flags=pygame.BLEND_RGBA_SUB)
        surface.blit(self._overlay, (0, 0))

"""Cielo procedural: el degradado sale del estado del mundo — AUD-426.

Por qué, y qué desbloquea
=========================
`docs/92` §4 lo pone en el Nivel 1 del catálogo, junto a las transiciones de
clima, y con una razón concreta: **desbloquea el crepúsculo de verdad**. Con
tres PNG por zona sólo hay tres cielos, así que la hora del día no puede
cambiarlos; el ciclo día/noche existe desde AUD-111 y lo único que hacía era
oscurecer una imagen fija de mediodía.

Un degradado calculado a partir de `EnvironmentState` sí puede: el color del
cénit y el del horizonte salen de la hora, la franja cálida del amanecer
aparece cuando el sol está bajo, y las nubes lo apagan cuando el clima las
trae. De paso quita PNG del repositorio.

Cómo no cuesta un fotograma
===========================
Un degradado de pantalla completa por fotograma sería absurdo: son 180 líneas
de `fill` a 60 Hz para una imagen que apenas cambia entre fotogramas
consecutivos. Se cachea, y la clave del caché es lo que de verdad lo mueve
—la hora redondeada a un decimal y la cobertura de nubes redondeada a dos—, no
el estado entero.

A un día de 240 s, una décima de hora son 100 ms: el cielo se recalcula unas
diez veces por segundo en el peor caso y ninguna vez cuando el mapa no tiene
ciclo de día y noche, que es la mayoría. Redondear es lo que convierte esto en
gratis; sin el redondeo, `hora` cambia cada fotograma y el caché no acierta
nunca.

Lo que **no** hace
==================
No dibuja sol, luna, estrellas ni nubes con forma. El catálogo los lista como
Nivel 2 y 3 —«cada uno es una condición sobre el estado y un dibujo»— y esto es
la infraestructura sobre la que se apoyan: quien quiera añadir un halo tiene ya
un cielo del que colgarlo y una `altura_solar` que consultar.
"""
from __future__ import annotations

from typing import Any

import pygame

__all__ = ["CieloProcedural"]

#: Colores del cénit y del horizonte por altura solar, de noche cerrada a
#: mediodía. La altura viene normalizada en [-1, 1] por `_altura_solar`.
#:
#: Los tres tramos no son decorativos: el salto de -0,1 a 0,1 es el crepúsculo,
#: donde el horizonte se vuelve naranja mientras el cénit sigue azul oscuro. Es
#: **esa diferencia entre las dos paradas** lo que se lee como amanecer, y lo
#: que un PNG fijo no puede dar.
_PARADAS: tuple[tuple[float, tuple[int, int, int], tuple[int, int, int]], ...] = (
    # altura   cénit                horizonte
    (-1.00, (6, 8, 20), (12, 14, 34)),        # noche cerrada
    (-0.20, (14, 18, 46), (44, 34, 68)),      # crepúsculo astronómico
    (0.00, (40, 56, 104), (214, 118, 66)),    # el sol en el horizonte
    (0.25, (72, 122, 186), (188, 176, 168)),  # media mañana
    (1.00, (92, 146, 214), (168, 194, 220)),  # mediodía
)

#: Cuánto apaga el cielo la cobertura total de nubes. 0,75 y no 1,0: un cielo
#: cubierto sigue teniendo luz, y llevarlo a gris plano borra la hora del día
#: —a mediodía y de madrugada se vería igual— que es justo lo que esto viene a
#: arreglar.
_APAGADO_POR_NUBES = 0.75

#: Color al que tiende el cielo cubierto.
_GRIS_DE_NUBES = (128, 132, 138)


def _mezclar(a: tuple[int, int, int], b: tuple[int, int, int],
             t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _colores_para(altura: float, nubes: float) -> tuple[tuple[int, int, int],
                                                        tuple[int, int, int]]:
    """Cénit y horizonte para una altura solar y una cobertura de nubes."""
    altura = max(-1.0, min(1.0, altura))
    cenit, horizonte = _PARADAS[-1][1], _PARADAS[-1][2]
    for i in range(len(_PARADAS) - 1):
        a0, c0, h0 = _PARADAS[i]
        a1, c1, h1 = _PARADAS[i + 1]
        if a0 <= altura <= a1:
            t = (altura - a0) / (a1 - a0) if a1 > a0 else 0.0
            cenit, horizonte = _mezclar(c0, c1, t), _mezclar(h0, h1, t)
            break
    if nubes > 0.0:
        peso = max(0.0, min(1.0, nubes)) * _APAGADO_POR_NUBES
        cenit = _mezclar(cenit, _GRIS_DE_NUBES, peso)
        horizonte = _mezclar(horizonte, _GRIS_DE_NUBES, peso)
    return cenit, horizonte


class CieloProcedural:
    """Dibuja el cielo y lo cachea. Una instancia por escena."""

    __slots__ = ("_clave", "_superficie")

    def __init__(self) -> None:
        self._clave: tuple[Any, ...] | None = None
        self._superficie: pygame.Surface | None = None

    def superficie(self, tamano: tuple[int, int], estado: Any) -> pygame.Surface:
        """El cielo para este estado, del caché si no ha cambiado nada.

        `estado` es un `EnvironmentState`; se aceptan dobles con `altura_solar`
        y `cobertura_nubes` porque es lo único que se consulta y así la prueba
        no necesita montar el mundo entero.
        """
        altura = float(getattr(estado, "altura_solar", 1.0))
        nubes = float(getattr(estado, "cobertura_nubes", 0.0))
        # El redondeo ES el caché: sin él, `altura_solar` cambia cada fotograma
        # y esto redibujaría 180 líneas sesenta veces por segundo.
        clave = (tamano, round(altura, 2), round(nubes, 2))
        if clave == self._clave and self._superficie is not None:
            return self._superficie

        cenit, horizonte = _colores_para(altura, nubes)
        ancho, alto = tamano
        lienzo = pygame.Surface((ancho, alto))
        for y in range(alto):
            t = y / max(1, alto - 1)
            pygame.draw.line(lienzo, _mezclar(cenit, horizonte, t),
                             (0, y), (ancho, y))
        self._clave = clave
        self._superficie = lienzo
        return lienzo

    def dibujar(self, destino: pygame.Surface, estado: Any) -> None:
        """Pinta el cielo en toda la superficie. Va **antes** que el parallax."""
        destino.blit(self.superficie(destino.get_size(), estado), (0, 0))

"""
Module: atmosfera
System: stage (student assignment — entrada_antenas)
Academic Unit: Unidad V — Espacios de color y transparencia

Efectos de color del Stage 2-2, resueltos con `ColorTools`.

Dos efectos, ambos observables en pantalla:

1. **Luces rojas intermitentes de las antenas.** El canal V de HSV se modula
   con una sinusoide; el matiz y la saturación no se tocan.
2. **Tinte atmosférico por altura.** La escena pasa de un tono cálido y
   polvoriento en el parqueo a uno frío y azulado en la azotea, interpolando
   **en HSV** entre los dos extremos.

Por qué HSV y no RGB
--------------------
HSV es una reparametrización cilíndrica del cubo RGB. Con
``M = max(R,G,B)`` y ``m = min(R,G,B)``::

    V = M
    S = (M - m) / M          (0 si M = 0)
    H = 60° · f(R,G,B)       según cuál canal sea el máximo

La propiedad que importa es que **V es un eje ortogonal a H y S**. Atenuar un
rojo en RGB obliga a escalar los tres canales de forma coordinada, y cualquier
descoordinación corrompe el matiz: el rojo se vuelve rosado o anaranjado según
qué canal se quede atrás. En HSV basta con mover V — el color sigue siendo
exactamente el mismo rojo, solo que más oscuro.

El parpadeo es entonces::

    V(t) = V_min + (V_max - V_min) · (1 + sin(2π f t)) / 2

La sinusoide se elige sobre una onda cuadrada a propósito: una luz de
advertencia real tiene inercia térmica en el filamento, así que sube y baja de
forma continua. Un parpadeo cuadrado se lee como un error de renderizado.

Interpolación de matiz por el arco corto
----------------------------------------
El matiz es un **ángulo**, no un escalar, así que interpolarlo linealmente es
incorrecto. Entre 30° (naranja cálido) y 210° (azul frío) el lerp directo
recorre 180° pasando por 120°, que es verde: la atmósfera del parqueo se
volvería verdosa a media escalada.

La corrección es tomar el arco corto::

    d = ((h₂ - h₁ + 180) mod 360) - 180
    h(t) = (h₁ + d·t) mod 360

Con ``d`` en [-180, 180], el recorrido es siempre el menor de los dos posibles.

Alfa por multiplicación aditiva en el halo
------------------------------------------
`ColorTools.apply_tint` internamente hace ``pygame.surfarray.array3d``, que
**descarta el canal alfa por píxel**: la superficie que devuelve es de 24 bits.
Un halo con degradado de transparencia perdería su desvanecido y saldría como
un cuadrado sólido.

Por eso el halo se construye como un degradado **de brillo sobre negro** y se
compone con ``BLEND_RGB_ADD``. En composición aditiva el negro suma cero, así
que las esquinas del cuadrado son invisibles sin necesitar alfa. Es además
físicamente correcto: la luz emitida se **suma** a lo que hay detrás, no lo
reemplaza.
"""
from __future__ import annotations

import math

import pygame

from src.framework.processing.color_tools import ColorTools

#: Color base de las luces de advertencia de las antenas, en RGB.
_ROJO_ADVERTENCIA: tuple[int, int, int] = (222, 48, 36)

#: Extremos del recorrido del canal V durante el parpadeo.
_V_MIN: float = 0.22
_V_MAX: float = 1.00

#: Frecuencia del parpadeo en Hz.
_FRECUENCIA: float = 0.85

#: Radio del halo en píxeles.
_RADIO_HALO: int = 34

#: Tonos de la atmósfera. Cálido y polvoriento a nivel de suelo; frío y
#: azulado a la altura de las antenas.
_TONO_SUELO: tuple[int, int, int] = (255, 186, 122)
_TONO_AZOTEA: tuple[int, int, int] = (146, 194, 255)

#: Cuánto se desatura el punto medio del degradado de altura. Los matices de
#: los dos extremos están a 180° exactos, así que sin esta caída el tránsito
#: pasa por magenta saturado. Ver `lerp_hsv`.
_CAIDA_SATURACION: float = 0.80

#: Opacidad del velo atmosférico. Deliberadamente baja: el efecto debe leerse
#: como aire, no como un filtro de fotografía, y la interfaz tiene que seguir
#: siendo legible por debajo.
#:
#: Bajada de 42 a 28 al repintar el parqueo en color: con el tileset gris
#: original 42 pasaba desapercibido, pero sobre un cielo azul saturado el velo
#: cálido lo viraba a verde azulado y ensuciaba toda la paleta. El efecto sigue
#: siendo medible y visible en el tránsito suelo→azotea.
_ALFA_VELO: int = 28


def lerp_hsv(
    rgb_a: tuple[int, int, int],
    rgb_b: tuple[int, int, int],
    t: float,
    caida_saturacion: float = 0.0,
) -> tuple[int, int, int]:
    """Interpola dos colores **en HSV**, tomando el arco corto del matiz.

    Args:
        rgb_a: color en t = 0.
        rgb_b: color en t = 1.
        t: parámetro de interpolación, se recorta a [0, 1].
        caida_saturacion: cuánto se desatura el punto medio, de 0 a 1.

    Returns:
        El color interpolado, de vuelta en RGB.

    Sobre el caso degenerado de 180°
    --------------------------------
    Cuando los dos matices están **exactamente** a 180° —naranja 29° y azul
    214°, que es justo este caso— los dos arcos miden lo mismo y la fórmula del
    arco corto no tiene forma de preferir uno. Elige el negativo, que recorre
    la zona magenta: a media escalada el velo salía en RGB(255, 134, 253).

    Forzar la dirección contraria no arregla nada, porque pasaría por el verde.
    El problema es que interpolar a saturación plena entre dos matices opuestos
    **siempre** atraviesa un color que no está en ninguno de los dos extremos.

    La solución correcta es física. La perspectiva atmosférica no conserva la
    pureza del color: el aire dispersa y **desatura** hacia el blanco conforme
    aumenta la distancia. Con ``caida_saturacion`` la saturación se deprime en
    el centro del recorrido::

        S(t) = lerp(S₁, S₂, t) · (1 - caida · sin(π t))

    El seno vale 0 en los extremos y 1 en el medio, así que los colores
    declarados se respetan exactamente y el tránsito pasa por una bruma pálida
    en lugar de por un magenta saturado. Es el mismo motivo por el que una
    montaña lejana se ve azul claro y no azul intenso.
    """
    t = max(0.0, min(1.0, t))
    h1, s1, v1 = ColorTools.rgb_to_hsv(*rgb_a)
    h2, s2, v2 = ColorTools.rgb_to_hsv(*rgb_b)

    # Arco corto: d queda en [-180, 180].
    d = ((h2 - h1 + 180.0) % 360.0) - 180.0
    h = (h1 + d * t) % 360.0

    s = (s1 + (s2 - s1) * t) * (1.0 - caida_saturacion * math.sin(math.pi * t))
    v = v1 + (v2 - v1) * t

    return ColorTools.hsv_to_rgb(h, max(0.0, min(1.0, s)), v)


class AtmosferaAntenas:
    """Parpadeo de las luces de antena y velo atmosférico por altura."""

    def __init__(
        self,
        posiciones_luces: list[tuple[float, float]],
        y_suelo: float,
        y_azotea: float,
    ) -> None:
        """
        Args:
            posiciones_luces: centros de las puntas de antena, en coordenadas
                de mundo.
            y_suelo: Y del nivel del parqueo. Tinte cálido.
            y_azotea: Y de la superficie de la azotea. Tinte frío.
        """
        self.posiciones_luces = [pygame.Vector2(p) for p in posiciones_luces]
        self.y_suelo = y_suelo
        self.y_azotea = y_azotea

        self._t = 0.0

        # Estado observable, para depuración y para el README.
        self.valores_v: list[float] = [0.0] * len(self.posiciones_luces)
        self.colores_luz: list[tuple[int, int, int]] = [
            _ROJO_ADVERTENCIA
        ] * len(self.posiciones_luces)
        self.color_velo: tuple[int, int, int] = _TONO_SUELO
        self.altura_normalizada: float = 0.0

        # Halo en blanco, construido una sola vez. `apply_tint` lo colorea
        # cada fotograma: multiplicar 34² px es barato, regenerar el degradado
        # no lo sería.
        self._halo_blanco = self._construir_halo(_RADIO_HALO)

    # ── Construcción del halo ───────────────────────────────────────

    @staticmethod
    def _construir_halo(radio: int) -> pygame.Surface:
        """Degradado radial de brillo sobre negro, en 24 bits.

        La caída es cuadrática (``(1 - d/r)²``) y no lineal porque la
        irradiancia de una fuente puntual decae con el cuadrado de la
        distancia. Un degradado lineal se ve como un disco con borde.
        """
        lado = radio * 2
        halo = pygame.Surface((lado, lado))
        halo.fill((0, 0, 0))
        centro = pygame.Vector2(radio, radio)
        for y in range(lado):
            for x in range(lado):
                d = centro.distance_to(pygame.Vector2(x + 0.5, y + 0.5))
                if d >= radio:
                    continue
                caida = (1.0 - d / radio) ** 2
                nivel = int(255 * caida)
                halo.set_at((x, y), (nivel, nivel, nivel))
        return halo

    # ── Ciclo de vida ───────────────────────────────────────────────

    def update(self, dt: float, y_jugador: float) -> None:
        """Avanza el parpadeo y recalcula el tinte según la altura."""
        self._t += dt

        # ── Parpadeo: solo se toca V ───────────────────────────────
        h, s, _ = ColorTools.rgb_to_hsv(*_ROJO_ADVERTENCIA)
        for i in range(len(self.posiciones_luces)):
            # Desfase por antena: tres luces sincronizadas se leen como un
            # efecto de pantalla; desfasadas, como tres balizas independientes.
            fase = 2.0 * math.pi * (_FRECUENCIA * self._t + i / 3.0)
            v = _V_MIN + (_V_MAX - _V_MIN) * (1.0 + math.sin(fase)) / 2.0
            self.valores_v[i] = v
            self.colores_luz[i] = ColorTools.hsv_to_rgb(h, s, v)

        # ── Velo atmosférico: interpolación en HSV por altura ──────
        span = self.y_suelo - self.y_azotea
        if span > 1e-6:
            self.altura_normalizada = max(
                0.0, min(1.0, (self.y_suelo - y_jugador) / span)
            )
        self.color_velo = lerp_hsv(
            _TONO_SUELO, _TONO_AZOTEA, self.altura_normalizada,
            caida_saturacion=_CAIDA_SATURACION,
        )

    # ── Dibujado ────────────────────────────────────────────────────

    def draw_velo(self, surface: pygame.Surface) -> None:
        """Velo atmosférico a pantalla completa."""
        w, h = surface.get_size()
        velo = pygame.Surface((w, h), pygame.SRCALPHA)
        velo.fill((*self.color_velo, _ALFA_VELO))
        surface.blit(velo, (0, 0))

    def draw_luces(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Halos de las luces de antena, en composición aditiva."""
        w, h = surface.get_size()
        for posicion, color in zip(self.posiciones_luces, self.colores_luz):
            centro = posicion - offset
            if (centro.x < -_RADIO_HALO or centro.x > w + _RADIO_HALO
                    or centro.y < -_RADIO_HALO or centro.y > h + _RADIO_HALO):
                continue

            # `apply_tint` multiplica canal a canal: blanco × color = color,
            # y negro × color = negro. El degradado se conserva.
            halo = ColorTools.apply_tint(self._halo_blanco, color)
            surface.blit(
                halo,
                (int(centro.x) - _RADIO_HALO, int(centro.y) - _RADIO_HALO),
                special_flags=pygame.BLEND_RGB_ADD,
            )

            # Núcleo saturado, para que la baliza tenga un punto duro y no
            # solo un halo difuso.
            pygame.draw.circle(surface, color, (int(centro.x), int(centro.y)), 3)

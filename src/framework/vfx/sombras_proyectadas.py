"""
Module: sombras_proyectadas
System: framework.vfx
Academic Unit: II (vectores) y IV (dibujado)

AUD-278 — la luz atravesaba las paredes.

El defecto
==========
`LightSystem.render` pegaba el degradado de cada foco sobre la máscara de
ambiente y ya está: la geometría del nivel **no participaba**. Una antorcha al
otro lado de un muro iluminaba igual que si el muro no existiera, y un pasillo
con una luz al fondo se veía entero aunque hubiera una columna en medio.

Se nota sobre todo de noche, que es cuando `ambient_light` baja y los focos son
lo único que hay: el jugador veía un halo perfectamente redondo pintado sobre
una pared maciza.

Cómo funciona
=============
Proyección de silueta, que es lo que hace cualquier motor 2D con luces. Desde
el foco, un rectángulo tapa una **cuña**: se toman sus dos esquinas extremas
—las que abarcan el mayor ángulo visto desde la luz— y se alargan hacia fuera
hasta salir del alcance. El cuadrilátero que queda entre las dos esquinas y sus
proyecciones es la sombra.

Es Unidad II en estado puro: todo son restas de vectores y un producto vectorial
para decidir qué esquina va a cada lado.

Por qué apagado por defecto
----------------------------
Porque cuesta: una proyección por foco y por obstáculo. El reporte 87 §11 lo
dejó anotado como «viable, con coste; hay que medirla antes de encenderla por
defecto», y eso es exactamente lo que se hace — la propiedad de mapa
`sombras_proyectadas` la enciende quien la quiera y quien no, no paga nada.

Lo que cuesta, medido
---------------------
Con focos de radio 160 sobre un mapa de 3.200 px, sumado al coste de dibujar
la luz:

| Focos | Obstáculos en el mapa | Sin tope | Con tope |
|---|---|---|---|
| 4 | 50 | +1,0 ms | +0,9 ms |
| 4 | 1.000 | +14,8 ms | **+4,9 ms** |
| 4 | 3.000 | +58,7 ms | **+6,8 ms** |
| 8 | 1.000 | +65,9 ms | **+20,7 ms** |
| 8 | 3.000 | +122,1 ms | **+24,7 ms** |

**El envolvente utilizable: hasta cuatro o cinco focos.** Con ocho, incluso con
tope, se come el fotograma. Un escenario nocturno de pasillo —dos antorchas y
una luna— cabe de sobra; una sala con doce lámparas, no.

**El cuello de botella es el relleno de polígonos, no la búsqueda.** La rejilla
de AUD-276 se usa para no recorrer los miles de rectángulos del mapa, y es la
estructura correcta, pero medida no cambia el resultado: lo que cuesta es
pintar una cuña por obstáculo. Conviene decirlo porque la primera versión de
este módulo afirmaba lo contrario y la medición no la respaldó.

De ahí sale `MAX_SOMBRAS_POR_FOCO`: sin tope, un escenario con muchas
plataformas y varias antorchas pasa de 16 ms de presupuesto a 122, y el juego
se arrastra sin que nadie sepa por qué.
"""
from __future__ import annotations

import pygame

from src.framework.stage.rejilla import RejillaEspacial

#: Cuántas sombras proyecta como mucho un foco. Medido: con 8 focos, 24
#: obstáculos cada uno salen ~4 ms, que cabe; 170 cada uno salen 122 ms, que no.
#:
#: Se recortan los **más lejanos**, que son los que proyectan la cuña más
#: estrecha y menos se notan. Recortar no es gratis —una sombra que falta es
#: una sombra que falta— pero es mejor que un fotograma de 122 ms, y sobre todo
#: es **acotado**: el diseñador sabe qué máximo está pagando.
MAX_SOMBRAS_POR_FOCO: int = 24


def silueta_de(foco: pygame.Vector2,
               rect: pygame.Rect) -> tuple[pygame.Vector2, pygame.Vector2] | None:
    """Las dos esquinas del rectángulo que forman su silueta desde `foco`.

    `None` si el foco está **dentro** del rectángulo: entonces no hay «detrás»,
    y proyectar daría un polígono del revés que oscurecería justo lo que
    debería iluminar.

    Se eligen por ángulo extremo: de las cuatro esquinas, las dos que abarcan
    el mayor arco visto desde la luz. Es la definición de silueta y evita el
    caso especial de mirar por qué cara del rectángulo entra el foco.
    """
    if rect.collidepoint(foco.x, foco.y):
        return None

    esquinas = [
        pygame.Vector2(rect.left, rect.top),
        pygame.Vector2(rect.right, rect.top),
        pygame.Vector2(rect.right, rect.bottom),
        pygame.Vector2(rect.left, rect.bottom),
    ]
    # Se compara cada par por el producto vectorial: si todas las demás
    # esquinas caen al mismo lado de la recta foco→esquina, esa esquina es un
    # extremo de la silueta.
    extremos: list[pygame.Vector2] = []
    for esquina in esquinas:
        direccion = esquina - foco
        lados = set()
        for otra in esquinas:
            if otra == esquina:
                continue
            cruz = direccion.x * (otra.y - foco.y) - direccion.y * (otra.x - foco.x)
            if abs(cruz) > 1e-6:
                lados.add(cruz > 0)
        if len(lados) <= 1:
            extremos.append(esquina)
    if len(extremos) < 2:
        return None
    return extremos[0], extremos[1]


def sombra_direccional(
    rect: pygame.Rect, direccion: float, largo: float,
) -> tuple[pygame.Vector2, ...]:
    """La sombra que proyecta `rect` con luz **paralela**: la del sol — AUD-403.

    Cierra el último consumidor de GAP-051. Todo este módulo proyecta desde un
    `foco`, o sea de forma **radial**, porque una antorcha está a dos metros. El
    sol no: sus rayos llegan paralelos, y una sombra radial con el foco muy
    lejos no es lo mismo que una paralela — es lo mismo *en el límite*, y para
    llegar a ese límite habría que poner el foco a millones de píxeles, con lo
    que la aritmética de coma flotante deja de valer mucho antes.

    Por eso el hueco decía que las sombras «proyectan desde un foco de luz, no
    desde el sol»: no era un descuido, era que faltaban las dos cosas —el dato
    (`azimut_solar`, AUD-399) y esta proyección—.

    `direccion` y `largo` salen tal cual de `EnvironmentState.direccion_de_sombra`.
    Devuelve el cuadrilátero de la sombra, o vacío si no hay ninguna que pintar:
    de noche, o con el sol justo encima.
    """
    if largo <= 0.0 or direccion == 0.0 or rect.height <= 0:
        return ()
    # Proporcional a la altura del objeto: lo que hace que una columna proyecte
    # más sombra que un escalón, que es de lo que se entera el ojo.
    desplazamiento = direccion * largo * rect.height
    return (
        pygame.Vector2(rect.left, rect.top),
        pygame.Vector2(rect.right, rect.top),
        pygame.Vector2(rect.right + desplazamiento, rect.bottom),
        pygame.Vector2(rect.left + desplazamiento, rect.bottom),
    )


class ProyectorDeSombras:
    """Oscurece lo que queda detrás de la geometría, foco a foco.

    Los obstáculos se indexan en una `RejillaEspacial` (AUD-276) la primera vez
    que se ven, y se reutiliza mientras la lista sea la misma: así no hay que
    recorrer los miles de rectángulos del mapa en cada foco y en cada
    fotograma.
    """

    def __init__(self) -> None:
        self._rejilla: RejillaEspacial | None = None
        self._indexados: list[pygame.Rect] | None = None

    def _cerca_del_foco(self, foco: pygame.Vector2, alcance: float,
                        obstaculos: list[pygame.Rect]) -> list[pygame.Rect]:
        """Sólo los obstáculos que pueden tapar algo de esta luz."""
        if self._indexados is not obstaculos:
            self._rejilla = RejillaEspacial(obstaculos)
            self._indexados = obstaculos
        zona = pygame.Rect(
            int(foco.x - alcance), int(foco.y - alcance),
            int(alcance * 2), int(alcance * 2),
        )
        assert self._rejilla is not None
        cerca = self._rejilla.cercanos(zona)
        if len(cerca) <= MAX_SOMBRAS_POR_FOCO:
            return cerca
        # Se quedan los más cercanos al foco: son los que proyectan la cuña más
        # ancha y los que el jugador nota. Ver la tabla del encabezado.
        cerca.sort(key=lambda r: (pygame.Vector2(r.center) - foco).length_squared())
        return cerca[:MAX_SOMBRAS_POR_FOCO]

    def proyectar(self, mascara: pygame.Surface, foco: pygame.Vector2,
                  alcance: float, obstaculos: list[pygame.Rect],
                  camera_offset: pygame.Vector2) -> None:
        """Pinta de negro la cuña que tapa cada obstáculo.

        Se pinta sobre la **máscara de luz**, antes de multiplicarla contra la
        escena: negro ahí significa «aquí no llega esta luz», que es
        exactamente lo que una sombra es. Pintar sobre la escena directamente
        daría una mancha negra encima del decorado en vez de ausencia de luz.
        """
        if alcance <= 0.0:
            return
        # El largo de la proyección: lo justo para salir del alcance por
        # cualquier lado. Alargar más no cambia el resultado y cuesta píxeles.
        largo = alcance * 2.0
        for rect in self._cerca_del_foco(foco, alcance, obstaculos):
            silueta = silueta_de(foco, rect)
            if silueta is None:
                continue
            a, b = silueta
            pa = a + (a - foco).normalize() * largo if (a - foco).length() else a
            pb = b + (b - foco).normalize() * largo if (b - foco).length() else b
            poligono = [
                (a.x - camera_offset.x, a.y - camera_offset.y),
                (b.x - camera_offset.x, b.y - camera_offset.y),
                (pb.x - camera_offset.x, pb.y - camera_offset.y),
                (pa.x - camera_offset.x, pa.y - camera_offset.y),
            ]
            pygame.draw.polygon(mascara, (0, 0, 0, 255), poligono)


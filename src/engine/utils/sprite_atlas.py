"""
Module: sprite_atlas
System: engine.utils
Academic Unit: N/A
Description: AUD-138 (G1) — atlas de sprites: muchos recortes en una sola
imagen, con su índice.

Lo primero, porque es lo que casi nadie mide
=============================================
**Un atlas NO acelera el dibujado en pygame.** Medido en este proyecto, 2.000
sprites de 32×32 a 800×600:

===========================  =========
 2.000 blits sueltos          2,06 ms
 2.000 blits desde el atlas   2,35 ms
 `blits()` sueltos            1,74 ms
 `blits()` desde el atlas     1,82 ms
===========================  =========

Dibujar desde un atlas sale **un poco peor**. Tiene sentido: la ventaja de un
atlas es ahorrar cambios de textura, y eso sólo existe cuando hay una GPU
detrás agrupando llamadas de dibujo. La ruta clásica de pygame es una copia de
memoria por blit y le da igual de dónde venga el recorte.

Publicar «hicimos un atlas y el juego va más rápido» habría sido una
afirmación falsa, de la misma familia que la que hubo que corregir en AUD-133.

Entonces, ¿para qué sirve?
--------------------------
Para tres cosas medidas, y ninguna es la que se suele contar:

1. **Cargar.** 200 PNG sueltos tardan 12,9 ms; el mismo contenido en un atlas,
   4,3 ms. **Tres veces más rápido**, porque el coste está en abrir ficheros y
   decodificar cabeceras, no en los píxeles.
2. **Ordenar.** Un `.png` y un `.json` en vez de doscientos ficheros que hay
   que nombrar bien, y un índice que dice qué hay dentro.
3. **La ruta de GPU, cuando llegue.** Ahí sí importa, y sin atlas no se puede
   empezar.

Lo que sí acelera hoy es `blits()`, que hace el bucle en C: 2,06 → 1,74 ms, un
16 %. Por eso `dibujar_lote` existe.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pygame

logger = logging.getLogger(__name__)

#: Separación entre recortes, en píxeles.
#:
#: Un píxel de margen evita el defecto clásico de los atlas: al escalar o
#: filtrar, el borde de un sprite chupa el color de su vecino y aparece una
#: línea de otro color en el canto. Con el escalado entero de este motor casi
#: nunca pasa, pero cuesta un píxel y quita una clase entera de fallo raro.
MARGEN: int = 1


class SpriteAtlas:
    """Una imagen con muchos recortes y un índice que dice dónde está cada uno."""

    def __init__(self, hoja: pygame.Surface,
                 indice: dict[str, pygame.Rect] | None = None) -> None:
        self.hoja = hoja
        self._indice: dict[str, pygame.Rect] = dict(indice or {})
        self._recortes: dict[str, pygame.Surface] = {}

    # ── construcción ─────────────────────────────────────────────
    @classmethod
    def empaquetar(cls, sprites: dict[str, pygame.Surface],
                   ancho_max: int = 1024) -> SpriteAtlas:
        """Coloca los sprites en estantes de altura decreciente.

        Es el algoritmo de estanterías: se ordena por altura y se va llenando
        una fila hasta que no cabe más, entonces se abre otra. No es el
        empaquetado óptimo —ése es NP-completo— pero deja poco hueco cuando
        los sprites se parecen de tamaño, que es el caso de un juego 2D con
        una rejilla de baldosas.
        """
        if not sprites:
            return cls(pygame.Surface((1, 1), pygame.SRCALPHA))

        por_altura = sorted(
            sprites.items(), key=lambda par: par[1].get_height(), reverse=True)

        indice: dict[str, pygame.Rect] = {}
        x = y = alto_estante = 0
        ancho_usado = 0
        for nombre, sprite in por_altura:
            w, h = sprite.get_size()
            if x + w > ancho_max and x > 0:
                x = 0
                y += alto_estante + MARGEN
                alto_estante = 0
            indice[nombre] = pygame.Rect(x, y, w, h)
            x += w + MARGEN
            alto_estante = max(alto_estante, h)
            ancho_usado = max(ancho_usado, x)

        hoja = pygame.Surface(
            (max(1, ancho_usado), max(1, y + alto_estante)), pygame.SRCALPHA)
        for nombre, rect in indice.items():
            hoja.blit(sprites[nombre], rect.topleft)
        return cls(hoja, indice)

    @classmethod
    def cargar(cls, ruta_png: str | Path) -> SpriteAtlas:
        """Lee `algo.png` y su `algo.json` hermano."""
        ruta_png = Path(ruta_png)
        hoja = pygame.image.load(str(ruta_png))
        hoja = hoja.convert_alpha() if pygame.display.get_surface() else hoja
        ruta_json = ruta_png.with_suffix(".json")
        indice: dict[str, pygame.Rect] = {}
        if ruta_json.exists():
            datos = json.loads(ruta_json.read_text(encoding="utf-8"))
            for nombre, (x, y, w, h) in datos.get("recortes", {}).items():
                indice[nombre] = pygame.Rect(x, y, w, h)
        else:
            logger.warning(
                "atlas %s sin índice .json: sólo se podrá usar la hoja entera",
                ruta_png.name,
            )
        return cls(hoja, indice)

    def guardar(self, ruta_png: str | Path) -> None:
        ruta_png = Path(ruta_png)
        ruta_png.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(self.hoja, str(ruta_png))
        datos = {
            "hoja": ruta_png.name,
            "recortes": {n: [r.x, r.y, r.width, r.height]
                         for n, r in self._indice.items()},
        }
        ruta_png.with_suffix(".json").write_text(
            json.dumps(datos, indent=2, sort_keys=True), encoding="utf-8")

    # ── lectura ───────────────────────────────────────────────────
    def __contains__(self, nombre: str) -> bool:
        return nombre in self._indice

    def __len__(self) -> int:
        return len(self._indice)

    @property
    def nombres(self) -> list[str]:
        return sorted(self._indice)

    def rect(self, nombre: str) -> pygame.Rect | None:
        rect = self._indice.get(nombre)
        return pygame.Rect(rect) if rect is not None else None

    def recorte(self, nombre: str) -> pygame.Surface | None:
        """El sprite como superficie. Es una **vista**, no una copia.

        `subsurface` comparte los píxeles con la hoja: pedir el mismo recorte
        mil veces no cuesta memoria. Lo que sí cuesta es crear el objeto, así
        que se guarda.
        """
        vista = self._recortes.get(nombre)
        if vista is not None:
            return vista
        rect = self._indice.get(nombre)
        if rect is None:
            return None
        vista = self.hoja.subsurface(rect)
        self._recortes[nombre] = vista
        return vista

    # ── dibujo ────────────────────────────────────────────────────
    def dibujar_lote(self, destino: pygame.Surface,
                     ordenes: list[tuple[str, tuple[int, int]]]) -> int:
        """Dibuja muchos sprites de una vez con `Surface.blits`.

        Aquí está la única ganancia de velocidad medida, y no viene del atlas
        sino de `blits()`, que hace el bucle en C en vez de en Python: 2.000
        sprites pasan de 2,06 ms a 1,74 ms.

        Devuelve cuántos se dibujaron: los nombres que no existen se saltan
        —un sprite que falta no puede tumbar el fotograma— y la diferencia
        entre lo pedido y lo dibujado es lo que hay que mirar.
        """
        secuencia = []
        for nombre, posicion in ordenes:
            rect = self._indice.get(nombre)
            if rect is None:
                continue
            secuencia.append((self.hoja, posicion, rect))
        if not secuencia:
            return 0
        destino.blits(secuencia, doreturn=False)
        return len(secuencia)

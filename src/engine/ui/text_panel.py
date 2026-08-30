"""Piezas de presentación para cuadros de texto (mensajes y diálogos).

AUD-611 — por qué existe este módulo
====================================
`MessageBox` y `DialogueSystem` dibujaban lo mismo dos veces y mal:

* **El texto se re-renderizaba en cada carácter** de la máquina de
  escribir (`MessageBox`) o en cada fotograma (`DialogueSystem`): treinta
  `font.render` por segundo de una cadena que crece, cuando el resultado
  son cuatro líneas fijas. Aquí se renderiza **una vez por mensaje** y la
  máquina de escribir recorta superficies ya hechas.
* **El ajuste de línea era por número de caracteres** en el cuadro de
  mensajes (`_MAX_CHARS_PER_LINE = 58`) mientras el de diálogo medía
  píxeles con la fuente real. Con una tipografía proporcional y la escala
  de accesibilidad, 58 caracteres no significan nada: aquí se mide
  siempre.
* **El aspecto**: rectángulo negro plano con borde de un píxel. Un panel
  moderno necesita sombra, esquinas redondeadas y jerarquía — nombre como
  ficha, opciones como chips — y las dos pantallas deben compartirlo.

Vive en `engine/ui` y no en `framework`: el framework puede importar al
motor, nunca al revés, y así los dos cuadros usan el mismo código sin
invertir la dependencia.
"""
from __future__ import annotations

import pygame

from src.engine.ui.theme import Theme


def dividir_en_lineas(
    texto: str, fuente: pygame.font.Font, ancho_max: int,
) -> list[str]:
    """Parte `texto` en líneas que caben en `ancho_max` píxeles.

    Mide con la fuente real — «iiii» y «MMMM» no ocupan lo mismo, y una
    estimación por caracteres se queda corta justo cuando más se la
    necesita (escala de accesibilidad al doble, AUD-128). Una palabra que
    no cabe entera desborda su línea: partirla la haría ilegible.
    """
    if not texto:
        return []
    lineas: list[str] = []
    for parrafo in texto.split("\n"):
        if not parrafo:
            lineas.append("")
            continue
        actual = ""
        for palabra in parrafo.split(" "):
            tentativa = f"{actual} {palabra}".strip()
            if actual and fuente.size(tentativa)[0] > ancho_max:
                lineas.append(actual)
                actual = palabra
            else:
                actual = tentativa
        if actual:
            lineas.append(actual)
    return lineas


class FlujoDeTexto:
    """Un bloque de texto envuelto y renderizado UNA vez.

    La máquina de escribir no re-renderiza: `dibujar(caracteres=n)` hace
    blit de las líneas completas que ya entren y recorta la última midiendo
    con la fuente (`size()` del prefijo, una llamada por fotograma y sólo
    mientras escribe). Coste típico: cuatro blits y cero `font.render`.
    """

    def __init__(self) -> None:
        self._texto: str = ""
        self._lineas: list[str] = []
        self._surfs: list[pygame.Surface] = []
        self._fuente: pygame.font.Font | None = None
        self._separacion: int = 3
        self._clave: tuple | None = None

    def preparar(
        self, texto: str, fuente: pygame.font.Font, ancho_max: int,
        separacion: int = 3, *,
        color: tuple[int, int, int] = Theme.TEXT,
    ) -> None:
        """Envuelve y renderiza si cambió el texto, la fuente o el ancho.

        La clave incluye `get_height()` de la fuente porque `theme.font`
        devuelve instancias cacheadas: con sólo `id(fuente)` un cambio de
        escala de accesibilidad no habría invalidado nada.
        """
        clave = (texto, id(fuente), fuente.get_height(), ancho_max)
        if self._clave == clave:
            return
        self._clave = clave
        self._texto = texto
        self._fuente = fuente
        self._separacion = separacion
        self._lineas = dividir_en_lineas(texto, fuente, ancho_max)
        self._surfs = [
            fuente.render(linea, True, color) for linea in self._lineas
        ]

    @property
    def vacio(self) -> bool:
        return not self._surfs

    @property
    def lineas(self) -> list[str]:
        """Las líneas ya envueltas — para paginar sin volver a medir."""
        return list(self._lineas)

    def caracteres_totales(self) -> int:
        return len(self._texto)

    def tamano(self) -> tuple[int, int]:
        """(ancho, alto) del bloque completo, separación incluida."""
        if not self._surfs:
            return (0, 0)
        alto = (sum(s.get_height() for s in self._surfs)
                + self._separacion * (len(self._surfs) - 1))
        return (max(s.get_width() for s in self._surfs), alto)

    def dibujar(
        self, surface: pygame.Surface, posicion: tuple[int, int],
        caracteres: int | None = None,
    ) -> None:
        """Blit del bloque; con `caracteres`, sólo ese prefijo.

        El corte de la línea en curso se mide con `fuente.size(prefijo)`:
        ancho REAL renderizado, no una estimación por caracteres.
        """
        if not self._surfs or self._fuente is None:
            return
        x, y = posicion
        restantes = (
            len(self._texto) if caracteres is None else max(0, caracteres)
        )
        for linea, surf in zip(self._lineas, self._surfs, strict=True):
            if restantes <= 0:
                break
            if restantes >= len(linea):
                surface.blit(surf, (x, y))
                restantes -= len(linea)
            else:
                prefijo = linea[:restantes]
                ancho = self._fuente.size(prefijo)[0]
                if ancho > 0:
                    surface.blit(
                        surf.subsurface(
                            (0, 0, ancho, surf.get_height())), (x, y))
                restantes = 0
                break
            y += surf.get_height() + self._separacion


#: Caché de cuerpos/sombras por (ancho, alto, radio, fondo). Los paneles
#: cambian de tamaño muy poco a menudo —el diálogo es fijo por escala y el
#: cuadro de mensajes sólo cuando cambia el texto—, así que reusar la
#: superficie elimina dos asignaciones por panel y por fotograma sin
#: retener nada que crezca sin tope: si el diccionario pasa de 32 entradas
#: se vacía entero (los paneles activos son como mucho un puñado).
_cache_de_paneles: dict[tuple, pygame.Surface] = {}
_CACHE_MAXIMA = 32


def _superficie_de_panel(
    ancho: int, alto: int, radio: int, color_cuerpo: tuple[int, int, int],
) -> pygame.Surface:
    clave = (ancho, alto, radio, color_cuerpo)
    cacheada = _cache_de_paneles.get(clave)
    if cacheada is not None:
        return cacheada
    if len(_cache_de_paneles) >= _CACHE_MAXIMA:
        _cache_de_paneles.clear()
    sombra = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    pygame.draw.rect(sombra, Theme.SHADOW, (0, 0, ancho, alto),
                     border_radius=radio)
    cuerpo = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    cuerpo.fill((*color_cuerpo, 242))
    pygame.draw.rect(cuerpo, (*color_cuerpo, 242),
                     (0, 0, ancho, alto), border_radius=radio)
    # La sombra viaja junto al cuerpo en una sola superficie compuesta: un
    # blit por fotograma en vez de dos.
    sombra.blit(cuerpo, (0, 0))
    _cache_de_paneles[clave] = sombra
    return sombra


def dibuja_panel(
    surface: pygame.Surface, rect: pygame.Rect, *,
    radio: int = Theme.RADIUS_L,
    elevado: bool = False,
) -> None:
    """Panel moderno: sombra desplazada, cuerpo redondeado opaco y borde.

    El cuerpo+sombra se componen UNA vez por tamaño y se reusan (ver
    `_superficie_de_panel`); por fotograma quedan un blit y el borde.
    """
    fondo = Theme.SURFACE_RAISED if elevado else Theme.SURFACE
    compuesta = _superficie_de_panel(rect.width, rect.height, radio,
                                      fondo)
    surface.blit(compuesta, (rect.x + 3, rect.y + 4))
    pygame.draw.rect(surface,
                     Theme.BORDER_STRONG if elevado else Theme.BORDER,
                     rect, 1, border_radius=radio)


def dibuja_ficha(
    surface: pygame.Surface, rect: pygame.Rect, texto_surf: pygame.Surface, *,
    fondo: tuple[int, int, int] = Theme.ACCENT,
) -> pygame.Vector2:
    """Ficha redondeada detrás de un texto (el nombre de quien habla).

    Devuelve la posición donde blitear `texto_surf` para que quede
    centrado dentro de la ficha.
    """
    chip = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(chip, (*fondo, 255),
                     (0, 0, rect.width, rect.height),
                     border_radius=max(3, rect.height // 2))
    surface.blit(chip, rect.topleft)
    return pygame.Vector2(
        rect.x + (rect.width - texto_surf.get_width()) // 2,
        rect.y + (rect.height - texto_surf.get_height()) // 2,
    )

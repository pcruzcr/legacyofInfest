"""La pestaña "Menú" de la pausa y su tira de pestañas — AUD-826.

Vivían como métodos de `DrawingSystem` y cada arreglo las hacía crecer con el
fichero, que tiene presupuesto de 850 líneas (`test_particion_de_drawing_system`).
El corte sigue la disciplina de AUD-352: el texto se movió verbatim y
`DrawingSystem._draw_pause_panel` sigue definido en su clase y delega aquí.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.ui.theme import Theme
from src.engine.ui.theme import font as fuente_del_tema


def dibujar_tira_de_pestanas(
    surface: pygame.Surface, tabs: tuple[str, ...], activa: int,
) -> None:
    # AUD-826 — era una franja de 20 px fijos pegada a `(0, 0)` con texto en
    # `y=1`: en 1280×720 ocupaba el 2,7 % de la pantalla y se veía igual de
    # pegada en los 26 stages porque este código es global. Ahora usa el alto
    # de barra del tema, respeta `MARGIN` en horizontal y centra el texto en
    # vertical con la tipografía del kit.
    if not tabs:
        return
    alto_franja = Theme.SPACE_XL
    fuente = fuente_del_tema(Theme.FONT_SMALL)
    pygame.draw.rect(
        surface, (10, 10, 16),
        (0, 0, settings.INTERNAL_WIDTH, alto_franja),
    )
    ancho_pestana = (settings.INTERNAL_WIDTH - Theme.MARGIN * 2) // len(tabs)
    for i, nombre in enumerate(tabs):
        es_activa = i == activa
        color = Theme.ACCENT if es_activa else Theme.TEXT_MUTED
        texto = fuente.render(nombre, True, color)
        cx = Theme.MARGIN + i * ancho_pestana + ancho_pestana // 2
        surface.blit(
            texto,
            (cx - texto.get_width() // 2,
             (alto_franja - texto.get_height()) // 2),
        )
        if es_activa:
            pygame.draw.rect(
                surface, Theme.ACCENT,
                (Theme.MARGIN + i * ancho_pestana,
                 alto_franja - 2, ancho_pestana, 2),
            )


def dibujar_menu_de_pausa(
    surface: pygame.Surface, seleccion: int, opciones: tuple[str, ...],
) -> None:
    # AUD-826 — fondo opaco más panel. El fondo es `Theme.BG`: antes iba
    # repetido a mano porque este código evitaba el paquete del tema; ahora
    # usa el token y las tres pestañas sólidas más esta se ven como una sola
    # aplicación.
    surface.fill(Theme.BG)
    # La lista era texto crudo sobre el fondo, con paso fijo de 30 y sin
    # panel: la única pestaña de la pausa sin marco. Ahora dibuja el panel
    # del kit (mismo `SURFACE`/`BORDER`/`RADIUS_L` que `draw_panel`) y el paso
    # sale de la métrica real de la fuente más `SPACE_S`, así que escala con
    # resolución y con `text_scale`.
    if not opciones:
        return
    fuente = fuente_del_tema(Theme.FONT_SMALL)
    textos = [
        fuente.render(
            f"> {opt}" if i == seleccion else f"  {opt}",
            True, Theme.ACCENT if i == seleccion else Theme.TEXT,
        )
        for i, opt in enumerate(opciones)
    ]
    paso = fuente.get_height() + Theme.SPACE_S
    ancho_panel = max(t.get_width() for t in textos) + Theme.SPACE_L * 2
    alto_panel = len(textos) * paso - Theme.SPACE_S + Theme.SPACE_L * 2
    panel = pygame.Rect(
        (settings.INTERNAL_WIDTH - ancho_panel) // 2,
        (settings.INTERNAL_HEIGHT - alto_panel) // 2,
        ancho_panel, alto_panel,
    )
    pygame.draw.rect(surface, Theme.SURFACE, panel,
                     border_radius=Theme.RADIUS_L)
    pygame.draw.rect(surface, Theme.BORDER, panel, 1,
                     border_radius=Theme.RADIUS_L)
    for i, text in enumerate(textos):
        fila_y = panel.y + Theme.SPACE_L + i * paso
        if i == seleccion:
            pygame.draw.rect(
                surface, Theme.SURFACE_RAISED,
                pygame.Rect(panel.x + Theme.SPACE_S, fila_y - Theme.SPACE_XS // 2,
                            panel.width - Theme.SPACE_S * 2,
                            text.get_height() + Theme.SPACE_XS),
                border_radius=Theme.RADIUS,
            )
        surface.blit(
            text,
            ((settings.INTERNAL_WIDTH - text.get_width()) // 2, fila_y),
        )

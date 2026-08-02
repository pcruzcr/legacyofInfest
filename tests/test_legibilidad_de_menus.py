"""
Module: test_legibilidad_de_menus
System: tests
Academic Unit: N/A

AUD-187 — en el bestiario y en los logros el texto se pisaba.

Qué se veía jugando
-------------------
En el menú de logros las filas iban pegadas, sin aire entre ellas, y en el
bestiario el nombre del enemigo se montaba encima de su descripción.

La causa es la misma en los dos sitios: **altos de fila escritos como número
fijo, con fuentes que no lo son**. El bestiario reservaba 48 px por ficha y
colocaba la descripción en `y + 22`, un 22 que daba por hecho el alto del
nombre. Medido: el nombre ocupa 22 px empezando en `y + 4`, así que termina en
26 y la descripción arranca en 22 — cuatro píxeles de solape antes de tocar
nada. Con la fuente ampliada por accesibilidad (`escalar_texto`, AUD-126) el
solape crece hasta hacer ilegible la ficha, que es justo lo contrario de lo que
esa opción persigue.

Lo que fija esta prueba
-----------------------
Que el hueco reservado para cada fila salga de la métrica real de la fuente y
no de un número escrito a mano. Se comprueba al tamaño normal y al máximo de
accesibilidad, porque el defecto sólo se nota de verdad en el segundo.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.ui.theme import Theme, font


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


#: Aire mínimo entre el texto de una fila y la siguiente. Por debajo de esto
#: las filas se leen como un bloque y el ojo no encuentra dónde empieza cada
#: una; no es una preferencia estética, es lo que separa una lista de una
#: mancha.
AIRE_MINIMO = 4


class TestElMenuDeLogros:
    def test_la_fila_deja_aire_para_su_texto(self) -> None:
        from src.engine.scenes.achievement_scene import alto_de_fila

        f = font(Theme.FONT_SMALL)
        assert alto_de_fila() >= f.get_linesize() + AIRE_MINIMO, (
            f"cada fila mide {alto_de_fila()} px y su texto ya ocupa "
            f"{f.get_linesize()}: las filas se tocan"
        )

    def test_sigue_dejando_aire_con_el_texto_ampliado(self, monkeypatch) -> None:
        """Con la ayuda de accesibilidad activada, que es cuando más importa."""
        import src.engine.ui.theme as tema
        from src.engine.scenes.achievement_scene import alto_de_fila

        monkeypatch.setattr(tema, "_escala_texto", 1.5, raising=False)
        f = font(Theme.FONT_SMALL)
        assert alto_de_fila() >= f.get_linesize() + AIRE_MINIMO


class TestElBestiario:
    def test_la_ficha_cabe_entera(self) -> None:
        """Nombre, descripción y estadísticas, sin que una pise a otra."""
        from src.engine.scenes.bestiary_scene import alto_de_ficha, y_de_la_descripcion

        nombre = font(Theme.FONT_SMALL)
        stats = font(Theme.FONT_TINY)

        assert y_de_la_descripcion() >= Theme.SPACE_XS + nombre.get_linesize(), (
            f"la descripción empieza en y+{y_de_la_descripcion()} y el nombre "
            f"termina en y+{Theme.SPACE_XS + nombre.get_linesize()}: se pisan"
        )
        necesario = y_de_la_descripcion() + stats.get_linesize()
        assert alto_de_ficha() >= necesario + AIRE_MINIMO, (
            f"la ficha reserva {alto_de_ficha()} px y su contenido necesita "
            f"{necesario}: la última línea se sale a la ficha siguiente"
        )

    def test_la_ficha_sigue_cabiendo_con_el_texto_ampliado(
        self, monkeypatch,
    ) -> None:
        import src.engine.ui.theme as tema
        from src.engine.scenes.bestiary_scene import alto_de_ficha, y_de_la_descripcion

        monkeypatch.setattr(tema, "_escala_texto", 1.5, raising=False)
        nombre = font(Theme.FONT_SMALL)
        stats = font(Theme.FONT_TINY)

        assert y_de_la_descripcion() >= Theme.SPACE_XS + nombre.get_linesize()
        assert alto_de_ficha() >= y_de_la_descripcion() + stats.get_linesize() + AIRE_MINIMO


class TestLaEscalaTipografica:
    def test_los_tamanos_van_de_menor_a_mayor(self) -> None:
        """Una escala que se cruza deja de ser jerarquía y pasa a ser ruido."""
        escala = [Theme.FONT_TINY, Theme.FONT_SMALL, Theme.FONT_BODY,
                  Theme.FONT_HEADING, Theme.FONT_TITLE]
        assert escala == sorted(escala), f"la escala no es creciente: {escala}"
        assert len(set(escala)) == len(escala), "hay dos escalones iguales"

    def test_el_cuerpo_es_legible_a_la_resolucion_del_juego(self) -> None:
        """El juego renderiza a 800x600. Por debajo de 16 px el cuerpo de texto
        se lee mal en esa superficie, y era una de las quejas al jugar."""
        from src.engine.core import settings

        assert settings.INTERNAL_HEIGHT == 600
        assert Theme.FONT_BODY >= 16, (
            f"el cuerpo de texto mide {Theme.FONT_BODY} px sobre 600 de alto"
        )

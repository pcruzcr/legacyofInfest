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



class TestElTamanoQueDeVerdadSeVe:
    """AUD-203 — `FONT_BODY = 20` no significaba 20 px en pantalla.

    La queja al jugar fue que el texto del juego «ni se nota» al lado del de la
    pantalla de Opciones. No era una impresión: `theme.font()` construía
    `pygame.font.Font(None, size)`, la tipografía por defecto de pygame, que
    entrega mucha menos tinta por punto pedido que cualquier TTF normal.

    Medido a escala 1.0x, alto de tinta real de «Salud»:

    ===============  ==============  ==========
    constante        por defecto     game.ttf
    ===============  ==============  ==========
    FONT_TITLE (38)  19 px           21 px
    FONT_BODY  (20)   9 px           12 px
    FONT_TINY  (15)   7 px            9 px
    ===============  ==============  ==========

    Los 9 px del cuerpo competían contra los **12 px** que pygame_gui dibuja en
    Opciones pidiendo 14. La pantalla de Opciones tenía la letra un 33 % más
    alta que el resto del juego pidiendo un tamaño casi la mitad.

    `game.ttf` —la tipografía propia, que la pantalla de título ya usaba— cierra
    el hueco y además ocupa menos ancho (−16 % en «CONTINUAR PARTIDA»), así que
    no descuadra ninguna maqueta.

    Por qué estas pruebas fijan la escala a mano
    --------------------------------------------
    `theme.font()` llama a `escalar_texto()`, que **lee la configuración del
    jugador**. En una máquina con la ayuda de accesibilidad al máximo, `font(20)`
    devuelve una fuente de 40 px. Sin fijar la escala, comparar `font(N)` contra
    `Font(None, N)` compara 40 contra 20 y pasa sin comprobar nada — pasó, y por
    eso está escrito aquí.
    """

    #: Lo que pygame_gui entrega en Opciones a su tamaño base de 14 px, a escala
    #: 1.0x. El resto del juego no puede quedar por debajo.
    TINTA_DE_PYGAME_GUI = 12

    @pytest.fixture(autouse=True)
    def _escala_fija(self, monkeypatch):
        """Escala 1.0x pase lo que pase en el `config.json` de quien ejecute."""
        from src.engine.core import user_settings
        from src.engine.ui.theme import clear_font_cache

        monkeypatch.setattr(
            user_settings, "preferencia",
            lambda nombre, defecto=None: 1.0 if nombre == "text_scale" else defecto,
        )
        clear_font_cache()
        yield
        clear_font_cache()

    @staticmethod
    def _tinta(fuente: pygame.font.Font) -> int:
        return fuente.render("Salud", True, (255, 255, 255)).get_bounding_rect().height

    def test_la_escala_de_prueba_es_la_normal(self) -> None:
        """Guarda de la guarda: si el ajuste no llega, lo demás no mide nada."""
        from src.engine.ui.theme import escalar_texto

        assert escalar_texto(Theme.FONT_BODY) == Theme.FONT_BODY

    def test_el_kit_no_usa_la_tipografia_por_defecto_de_pygame(self) -> None:
        """La más pequeña de las disponibles era justo la que se usaba."""
        from src.engine.ui.theme import font as fuente_del_kit

        del_kit = self._tinta(fuente_del_kit(Theme.FONT_BODY))
        por_defecto = self._tinta(pygame.font.Font(None, Theme.FONT_BODY))
        assert del_kit > por_defecto, (
            f"el cuerpo de texto mide {del_kit} px de tinta, lo mismo que la "
            f"tipografía por defecto de pygame ({por_defecto} px): el kit "
            f"sigue sin usar game.ttf"
        )

    def test_el_cuerpo_no_es_mas_pequeno_que_el_de_la_pantalla_de_opciones(
        self,
    ) -> None:
        """Que no vuelva a haber dos escalas de letra en el mismo juego."""
        from src.engine.ui.theme import font as fuente_del_kit

        alto = self._tinta(fuente_del_kit(Theme.FONT_BODY))
        assert alto >= self.TINTA_DE_PYGAME_GUI, (
            f"el cuerpo del juego mide {alto} px y el de pygame_gui "
            f"{self.TINTA_DE_PYGAME_GUI} px: el jugador ve dos escalas y la "
            f"del juego es la pequeña"
        )

    def test_el_arreglo_alcanza_a_toda_la_escala(self) -> None:
        """Los cinco escalones, no sólo el cuerpo."""
        from src.engine.ui.theme import font as fuente_del_kit

        for tamano in (Theme.FONT_TINY, Theme.FONT_SMALL, Theme.FONT_BODY,
                       Theme.FONT_HEADING, Theme.FONT_TITLE):
            assert self._tinta(fuente_del_kit(tamano)) > self._tinta(
                pygame.font.Font(None, tamano)
            ), f"el escalón de {tamano} px sigue en la tipografía por defecto"

    def test_la_tipografia_del_juego_no_desborda_las_maquetas(self) -> None:
        """Más alta pero no más ancha: por eso el cambio es seguro.

        Si algún día se cambia por una fuente ancha, esto avisa antes de que
        once etiquetas de Opciones se salgan de su rectángulo (AUD-160).
        """
        from src.engine.ui.theme import font as fuente_del_kit

        for texto in ("CONTINUAR PARTIDA", "MOVIMIENTO REDUCIDO (sacudida)",
                      "Pulsa Z para hablar"):
            ancho_kit = fuente_del_kit(Theme.FONT_BODY).size(texto)[0]
            ancho_viejo = pygame.font.Font(None, Theme.FONT_BODY).size(texto)[0]
            assert ancho_kit <= ancho_viejo * 1.05, (
                f"«{texto}» pasa de {ancho_viejo} a {ancho_kit} px de ancho"
            )

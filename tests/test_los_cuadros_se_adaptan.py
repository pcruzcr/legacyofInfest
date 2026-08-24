"""AUD-611 — los cuadros de texto se adaptan al texto y dejan de
re-renderizar en cada carácter.

Tres contratos nuevos, para los dos cuadros (`MessageBox` y el diálogo):

1. **Adaptación**: el alto del panel sale de las líneas envueltas, no de
   una constante de la maqueta de 224 px.
2. **Ajuste por píxeles**: la línea se parte midiendo con la fuente real;
   «iiiii…» y «MMMM…» no pueden cortarse en el mismo número de líneas.
3. **Render una vez**: la máquina de escribir recorta superficies ya
   hechas — `font.render` ocurre por LÍNEA, no por carácter ni por
   fotograma.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


class _FuenteContadora:
    """Proxy de fuente que cuenta `render` sin cambiar nada más."""

    def __init__(self, base: pygame.font.Font) -> None:
        self._base = base
        self.renders = 0

    def render(self, *args, **kwargs):
        self.renders += 1
        return self._base.render(*args, **kwargs)

    def size(self, texto):
        return self._base.size(texto)

    def get_height(self):
        return self._base.get_height()


# ── MessageBox ──────────────────────────────────────────────────────

class TestElCuadroSeAdapta:
    @staticmethod
    def _caja(event_bus):
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.message_box import MessageBox

        caja = MessageBox(EventBus())
        caja.event_bus = event_bus
        return caja

    def test_el_alto_crece_con_las_lineas(self, _video, event_bus) -> None:
        from src.engine.ui.message_box import MessageBox

        caja = MessageBox(event_bus)
        event_bus.emit("SHOW_MESSAGE", text="Corta.", duration=3.0)
        event_bus.dispatch()
        panel_corto = caja.rect_del_panel().height

        # Agota el aviso corto ANTES del siguiente, o irá a la cola.
        # Dos updates: uno completa la máquina de escribir, el siguiente
        # acumula el tiempo de auto-despedida.
        caja.update(10.0)
        caja.update(10.0)
        assert not caja.is_visible

        event_bus.emit(
            "SHOW_MESSAGE",
            text=("Una frase larguísima que a lo seguro no cabe en una sola "
                  "línea y necesita varias para contarse entera, porque los "
                  "avisos del escenario también cuentan cosas."),
            duration=3.0,
        )
        event_bus.dispatch()
        caja.update(10.0)

        assert caja.rect_del_panel().height > panel_corto

    def test_el_ancho_del_panel_no_pasa_del_interior(self, _video,
                                                     event_bus) -> None:
        from src.engine.core import settings
        from src.engine.ui.message_box import MessageBox

        caja = MessageBox(event_bus)
        event_bus.emit("SHOW_MESSAGE", text="x" * 400, duration=3.0)
        event_bus.dispatch()

        panel = caja.rect_del_panel()
        assert panel.width <= settings.INTERNAL_WIDTH - 2 * 24
        assert panel.right <= settings.INTERNAL_WIDTH
        assert panel.left >= 0

    def test_el_ajuste_es_por_pixeles_y_no_por_caracteres(
        self, _video, event_bus,
    ) -> None:
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.message_box import MessageBox
        from src.engine.ui.text_panel import dividir_en_lineas

        caja = MessageBox(EventBus())
        fuente = caja._font
        ancho = caja._ancho_util()
        # Mismo número de caracteres: las «M» ocupan el doble que las «i»,
        # así que deben salir MÁS líneas. El viejo corte a 58 caracteres
        # daba las mismas para los dos.
        lineas_i = dividir_en_lineas(" ".join(["iii"] * 60), fuente, ancho)
        lineas_m = dividir_en_lineas(" ".join(["MMM"] * 60), fuente, ancho)

        assert len(lineas_m) > len(lineas_i)

    def test_la_maquina_de_escribe_renderiza_por_linea(
        self, _video, event_bus,
    ) -> None:
        from src.engine.ui.message_box import MessageBox

        caja = MessageBox(event_bus)
        proxy = _FuenteContadora(caja._font)
        caja._font = proxy
        texto = ("Palabras suficientes para envolverse en tres o cuatro "
                 "líneas de verdad, con palabras de longitud variada para "
                 "que el ajuste trabaje: quijotesco, escalamontes, "
                 "desventuras, retamas y un largo etcétera que obligue a "
                 "cortar más de una vez. ") * 3
        event_bus.emit("SHOW_MESSAGE", text=texto, duration=3.0)
        event_bus.dispatch()

        esperado = proxy.renders          # una por línea envuelta
        assert esperado >= 2

        # Un segundo entero de máquina de escribir: cero renders nuevos.
        for _ in range(60):
            caja.update(1.0 / 60.0)
        assert proxy.renders == esperado, (
            f"la máquina de escribir re-renderizó: {proxy.renders} renders "
            f"para {esperado} líneas"
        )


# ── DialogueSystem ──────────────────────────────────────────────────

class TestElDialogoRenderizaPorPagina:
    @staticmethod
    def _sistema(monkeypatch):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))

        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.ui.text_panel import FlujoDeTexto
        from src.framework.ui.dialogue_system import (
            DialogueNode,
            DialogueSystem,
            DialogueTree,
        )

        preparadas: list[str] = []
        original = FlujoDeTexto.preparar

        def espia(self, texto, *a, **k):
            preparadas.append(texto)
            return original(self, texto, *a, **k)

        monkeypatch.setattr(FlujoDeTexto, "preparar", espia)

        ctx = GameContext(
            input_manager=None,  # type: ignore[arg-type]
            audio_manager=None,  # type: ignore[arg-type]
            scene_manager=None,  # type: ignore[arg-type]
            event_bus=EventBus(),
        )
        sistema = DialogueSystem(ctx)
        arbol = DialogueTree(
            tree_id="prueba",
            nodes={"inicio": DialogueNode(
                node_id="inicio", speaker="Eco",
                text="Primera página con suficiente texto para envolverse "
                     "en un par de líneas y seguir leyendo cómodamente.")},
            start_node="inicio",
        )
        return sistema, arbol, preparadas

    def test_dos_fotogramas_una_sola_preparacion(self, _video,
                                                 monkeypatch) -> None:
        sistema, arbol, preparadas = self._sistema(monkeypatch)
        sistema.start_dialogue(arbol)

        superficie = pygame.Surface((800, 600))
        sistema.draw(superficie)
        sistema.draw(superficie)
        sistema.draw(superficie)

        assert len(preparadas) == 1, (
            "cada fotograma re-envolvió la misma página: la paginación "
            "debería estar cacheada por (nodo, página, escala)"
        )

    def test_avanzar_de_pagina_prepara_otra(self, _video, monkeypatch) -> None:
        """Un texto de dos páginas: página 1 se prepara una vez, ENTER
        pasa a la página 2 y ésa se prepara exactamente una vez."""
        from src.framework.ui.dialogue_system import DialogueNode, DialogueTree

        sistema, _, preparadas = self._sistema(monkeypatch)
        texto_largo = (
            "Primera página con bastante texto para llenar más de una "
            "pantalla de líneas envueltas. ") * 8
        arbol = DialogueTree(
            tree_id="prueba",
            nodes={"inicio": DialogueNode(
                node_id="inicio", speaker="Eco", text=texto_largo)},
            start_node="inicio",
        )
        sistema.start_dialogue(arbol)
        superficie = pygame.Surface((800, 600))
        sistema._text_progress = float(sistema._caracteres_de_pagina())
        sistema._full_text_visible = True
        sistema.draw(superficie)
        assert sistema.paginas > 1, (
            "el texto de prueba debería ocupar más de una página"
        )

        preparadas_tras_pagina_1 = len(preparadas)
        sistema.confirmar()          # avanza de página
        sistema.draw(superficie)

        assert len(preparadas) == preparadas_tras_pagina_1 + 1

    def test_el_nombre_va_en_ficha_y_las_opciones_en_chips(
        self, _video, monkeypatch,
    ) -> None:
        """Comprobación de píxeles: alrededor del nombre hay color de
        acento (la ficha), no fondo del panel."""
        sistema, arbol, _ = self._sistema(monkeypatch)
        sistema.start_dialogue(arbol)
        sistema._text_progress = float(sistema._caracteres_de_pagina())
        sistema._full_text_visible = True

        superficie = pygame.Surface((800, 600))
        superficie.fill((255, 0, 255))   # imposible por el tema
        sistema.draw(superficie)

        # Busca al menos un píxel del ACCENT (255, 200, 90) en la franja
        # superior del cuadro: la ficha del nombre está pintada ahí.
        from src.engine.ui.theme import Theme

        franja = superficie.subsurface(pygame.Rect(
            20, 600 - int(110 * 1.0) - 10 + 6, 300, 24)).copy()
        encontrado = any(
            franja.get_at((x, y))[:3] == Theme.ACCENT[:3]
            for x in range(0, franja.get_width(), 3)
            for y in range(0, franja.get_height(), 3)
        )
        assert encontrado, (
            "no se encontró la ficha de acento detrás del nombre: el "
            "diálogo sigue dibujando el nombre suelto"
        )


class TestLaCacheDelPanel:
    def test_mismo_tamaño_reusa_la_superficie(self, _video) -> None:
        """Dos paneles del mismo tamaño no reasignan: misma superficie."""
        import gc

        from src.engine.ui import text_panel

        text_panel._cache_de_paneles.clear()
        destino = pygame.Surface((400, 300))
        rect = pygame.Rect(10, 10, 200, 60)
        text_panel.dibuja_panel(destino, rect)
        clave = next(iter(text_panel._cache_de_paneles))
        primera = text_panel._cache_de_paneles[clave]

        text_panel.dibuja_panel(destino, rect)
        gc.collect()

        assert text_panel._cache_de_paneles[clave] is primera

    def test_tamaños_distintos_no_colisionan(self, _video) -> None:
        from src.engine.ui import text_panel

        text_panel._cache_de_paneles.clear()
        destino = pygame.Surface((400, 300))
        text_panel.dibuja_panel(destino, pygame.Rect(0, 0, 100, 40))
        text_panel.dibuja_panel(destino, pygame.Rect(0, 0, 150, 50))

        assert len(text_panel._cache_de_paneles) == 2

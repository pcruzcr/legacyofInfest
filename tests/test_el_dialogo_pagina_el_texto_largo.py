"""AUD-269 — un diálogo largo se recortaba en silencio.

El defecto
==========
`DialogueSystem.draw` parte el texto en líneas y las dibuja hasta que se acaba
el cuadro:

    if y + self._font_text.get_height() > box.bottom - Theme.SPACE_S:
        break

Lo que no cabe **no se muestra nunca**. No hay aviso, ni flecha, ni forma de
seguir leyendo: el jugador ve media frase y pulsa ENTER, y el diálogo pasa al
nodo siguiente con la otra mitad sin leer. Un guionista que escriba un párrafo
en `data/dialogues/<stage>.json` no tiene manera de enterarse.

Es la misma familia que el resto de esta auditoría —algo que falla callándose—
sólo que aquí lo que se pierde es el texto del juego.

La corrección
-------------
El texto se **pagina**: se parte en tantas páginas como haga falta para el alto
del cuadro, y ENTER avanza de página antes de avanzar de nodo. La máquina de
escribir se reinicia en cada página, así que el ritmo de lectura no cambia.

El indicador `[ENTER]` ya existía; ahora dice `[ENTER] 1/3` cuando hay más de
una página, porque «hay más» es la información que faltaba.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.ui.dialogue_system import DialogueNode, DialogueSystem, DialogueTree


@pytest.fixture
def sistema(event_bus):
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    from src.engine.core.game_context import GameContext

    ctx = GameContext(
        input_manager=None,  # type: ignore[arg-type]
        audio_manager=None,  # type: ignore[arg-type]
        scene_manager=None,  # type: ignore[arg-type]
        event_bus=event_bus,
    )
    return DialogueSystem(ctx)


def _arbol(texto: str) -> DialogueTree:
    return DialogueTree(
        tree_id="prueba",
        nodes={"inicio": DialogueNode(node_id="inicio", speaker="Alguien",
                                      text=texto)},
        start_node="inicio",
    )


#: Un párrafo que no cabe en el cuadro ni de lejos.
#:
#: El cuadro son cinco líneas a escala 1,0 (medido: `_lineas_por_pagina()`), y
#: el ancho útil son casi setecientos píxeles, así que hace falta un párrafo
#: **largo de verdad** para desbordarlo. Ésa fue la primera versión de esta
#: prueba: un texto que parecía largo cabía en una página y la prueba pasaba
#: sin ejercitar nada.
LARGO = (
    "El bosque recuerda lo que la ciudad olvida, y lo recuerda despacio, como "
    "recuerdan las cosas que no tienen prisa. Cada raíz guarda un nombre y "
    "cada nombre pesa lo que pesó quien lo llevaba. Por eso el venado no "
    "ataca al que pasa: ataca al que vuelve. Y tú has vuelto tres veces, con "
    "las manos llenas de lo que no era tuyo, y el bosque lleva la cuenta "
    "aunque tú no la lleves. Mi abuela decía que las reliquias no se roban, "
    "se piden, y que lo que se pide se devuelve antes de que la luna cambie "
    "de cara. Nadie pidió nada aquella noche. Los que bajaron de la montaña "
    "traían cuerdas, no palabras, y se llevaron lo que llevaba mil años "
    "quieto en su sitio. Desde entonces el aire huele a esporas y los "
    "caminos que conocías de memoria te llevan a donde no querías ir. No es "
    "un castigo: es un recordatorio, y los recordatorios sólo duelen cuando "
    "uno sabe que se los merece. Si vas a seguir subiendo, sube sabiendo eso."
)


class TestElTextoLargoSePagina:
    def test_un_texto_largo_ocupa_varias_paginas(self, sistema) -> None:
        sistema.start_dialogue(_arbol(LARGO))

        assert sistema.paginas > 1, (
            "el texto entra en una sola página: o el cuadro creció o esta "
            "prueba dejó de medir lo que decía medir"
        )

    def test_un_texto_corto_ocupa_una(self, sistema) -> None:
        sistema.start_dialogue(_arbol("Hola."))

        assert sistema.paginas == 1

    def test_no_se_pierde_ni_una_palabra(self, sistema) -> None:
        """Lo que se paginó, sumado, tiene que ser el texto entero."""
        sistema.start_dialogue(_arbol(LARGO))

        junto = " ".join(" ".join(p) for p in sistema._paginas_de_texto())
        for palabra in LARGO.split():
            assert palabra in junto, f"se perdió «{palabra}» al paginar"

    def test_confirmar_avanza_de_pagina_antes_que_de_nodo(self, sistema) -> None:
        sistema.start_dialogue(_arbol(LARGO))
        sistema._full_text_visible = True

        sistema.confirmar()

        assert sistema.pagina_actual == 1
        assert sistema.active is True, "no puede cerrarse con texto por leer"

    def test_en_la_ultima_pagina_confirmar_cierra(self, sistema) -> None:
        sistema.start_dialogue(_arbol(LARGO))
        for _ in range(sistema.paginas):
            sistema._full_text_visible = True
            sistema.confirmar()

        assert sistema.active is False

    def test_cada_pagina_reinicia_la_maquina_de_escribir(self, sistema) -> None:
        """Si no, la página 2 aparecería entera de golpe."""
        sistema.start_dialogue(_arbol(LARGO))
        sistema._full_text_visible = True
        sistema.confirmar()

        assert sistema._text_progress == 0.0
        assert sistema._full_text_visible is False


class TestSeDibujaSinRomperse:
    def test_dibujar_cada_pagina_no_lanza(self, sistema) -> None:
        superficie = pygame.Surface((800, 600))
        sistema.start_dialogue(_arbol(LARGO))

        for _ in range(sistema.paginas):
            sistema.update(10.0)
            sistema.draw(superficie)
            sistema.confirmar()

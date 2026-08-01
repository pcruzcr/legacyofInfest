"""
AUD-111 — los dos únicos sistemas vivos del motor que no tenían red.

De dónde sale esto
==================
La validación de sistemas (`docs/58_`) contó las llamadas reales desde el motor
y encontró que el diálogo y las cutscenes **se usan** —`StageScene` los
instancia y los actualiza— y no tenían **una sola prueba propia**. Eran los dos
únicos así: todo lo demás vivo tenía pruebas, y todo lo demás sin pruebas estaba
muerto.

No estaban rotos: el arnés de humo los ejercita al arrancar cada escena, así que
un fallo de construcción se habría visto. Lo que no cubría nadie es su
**comportamiento**: que un árbol de diálogo avance por donde debe, que una
elección lleve al nodo correcto, que una cutscene ejecute sus acciones en orden
y llame a su callback al terminar.

Un cambio en cualquiera de las dos cosas sólo se descubría jugando.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.cutscene_system import (
    CutsceneScript,
    FadeAction,
    WaitAction,
)
from src.framework.ui.dialogue_system import (
    DialogueNode,
    DialogueSystem,
    DialogueTree,
)

FRAME = 1.0 / 60.0


def _lienzo() -> pygame.Surface:
    """Un lienzo del tamaño interno real del juego.

    La primera versión de estas pruebas usaba 320 × 224 —el tamaño de la
    ventana de pruebas— y el diálogo se dibujaba fuera: su caja va en
    `INTERNAL_HEIGHT - 110`, y `INTERNAL_HEIGHT` es **600**. La prueba decía
    «hay un diálogo activo y no se ve nada», y tenía razón sobre el lienzo
    equivocado.
    """
    from src.engine.core import settings

    s = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    s.fill((10, 20, 30))
    return s


@pytest.fixture(scope="module", autouse=True)
def _pg():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 224))
    yield


@pytest.fixture
def contexto():
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


def _arbol_simple() -> DialogueTree:
    return DialogueTree(
        tree_id="prueba",
        start_node="a",
        nodes={
            "a": DialogueNode("a", "Guía", "Primera frase."),
            "b": DialogueNode("b", "Guía", "Segunda frase."),
        },
    )


def _arbol_con_eleccion() -> DialogueTree:
    return DialogueTree(
        tree_id="rama",
        start_node="pregunta",
        nodes={
            "pregunta": DialogueNode(
                "pregunta", "Guía", "¿Por dónde vas?",
                choices=[("Izquierda", "izq"), ("Derecha", "der")],
            ),
            "izq": DialogueNode("izq", "Guía", "Hacia la izquierda."),
            "der": DialogueNode("der", "Guía", "Hacia la derecha."),
        },
    )


# ══════════════════════════════════════════════════════════════
# Diálogo
# ══════════════════════════════════════════════════════════════


class TestDialogo:
    def test_empieza_en_el_nodo_declarado(self, contexto):
        d = DialogueSystem(contexto)
        d.start_dialogue(_arbol_simple())
        assert d.active
        assert d._current_node.node_id == "a"

    def test_un_arbol_sin_su_nodo_inicial_no_deja_el_sistema_a_medias(self, contexto):
        """Un árbol mal construido no puede dejar el juego en diálogo vacío.

        Es el caso que un estudiante producirá primero: teclear mal el
        identificador del nodo de arranque. Si el sistema se quedara `active`
        con `_current_node = None`, el jugador perdería el control del juego sin
        nada en pantalla, que es la peor forma de fallar.
        """
        roto = DialogueTree(
            tree_id="roto", start_node="no_existe",
            nodes={"a": DialogueNode("a", "X", "Y")},
        )
        d = DialogueSystem(contexto)
        d.start_dialogue(roto)
        assert not (d.active and d._current_node is None), (
            "el sistema quedó activo sin nodo: el jugador pierde el control"
        )

    def test_terminar_el_dialogo_devuelve_el_control(self, contexto):
        d = DialogueSystem(contexto)
        d.start_dialogue(_arbol_simple())
        d.end_dialogue()
        assert not d.active

    def test_un_nodo_con_elecciones_las_ofrece(self, contexto):
        d = DialogueSystem(contexto)
        d.start_dialogue(_arbol_con_eleccion())
        assert len(d._current_node.choices) == 2

    def test_elegir_lleva_al_nodo_correcto(self, contexto):
        """Es la razón de ser de un árbol: que la rama importe."""
        d = DialogueSystem(contexto)
        d.start_dialogue(_arbol_con_eleccion())
        d._go_to_node("der")
        assert d._current_node.node_id == "der"
        assert d._current_node.text == "Hacia la derecha."

    def test_ir_a_un_nodo_inexistente_no_revienta(self, contexto):
        """Una rama con un identificador mal escrito no puede tumbar la partida."""
        d = DialogueSystem(contexto)
        d.start_dialogue(_arbol_simple())
        d._go_to_node("fantasma")
        # Lo que se exige no es un comportamiento concreto, sino que no lance y
        # que no deje el sistema activo apuntando a la nada.
        assert not (d.active and d._current_node is None)

    def test_dibujar_sin_dialogo_activo_no_pinta_nada(self, contexto):
        """El sistema se dibuja cada fotograma; inactivo tiene que ser invisible."""
        d = DialogueSystem(contexto)
        lienzo = _lienzo()
        lienzo.fill((10, 20, 30))
        antes = pygame.surfarray.array3d(lienzo).copy()
        d.draw(lienzo)
        assert (pygame.surfarray.array3d(lienzo) == antes).all(), (
            "el sistema de diálogo pinta con el diálogo cerrado"
        )

    def test_dibujar_un_dialogo_activo_si_pinta(self, contexto):
        d = DialogueSystem(contexto)
        d.start_dialogue(_arbol_simple())
        for _ in range(30):
            d.update(FRAME)
        lienzo = _lienzo()
        lienzo.fill((10, 20, 30))
        antes = pygame.surfarray.array3d(lienzo).copy()
        d.draw(lienzo)
        assert not (pygame.surfarray.array3d(lienzo) == antes).all(), (
            "hay un diálogo activo y no se ve nada en pantalla"
        )


# ══════════════════════════════════════════════════════════════
# Cutscenes
# ══════════════════════════════════════════════════════════════


class TestCutscenes:
    def test_las_acciones_corren_en_orden(self):
        orden: list[str] = []

        class Anotar(WaitAction):
            def __init__(self, etiqueta: str) -> None:
                super().__init__(0.05)
                self._etiqueta = etiqueta

            def start(self) -> None:
                super().start()
                orden.append(self._etiqueta)

        guion = CutsceneScript([Anotar("uno"), Anotar("dos"), Anotar("tres")])
        guion.start()
        for _ in range(60):
            guion.update(FRAME)
        assert orden == ["uno", "dos", "tres"]

    def test_la_siguiente_accion_no_arranca_antes_de_tiempo(self):
        """Si arrancaran a la vez, una cutscene sería un fotograma de caos."""
        guion = CutsceneScript([WaitAction(1.0), WaitAction(1.0)])
        guion.start()
        guion.update(FRAME)
        assert guion._index == 0

    def test_al_terminar_llama_al_callback(self):
        """El callback es lo que devuelve el control al juego.

        Sin él, una cutscene termina y el jugador se queda mirando una escena
        que ya no avanza — que es el mismo fallo que un diálogo activo sin nodo.
        """
        llamadas: list[int] = []
        guion = CutsceneScript([WaitAction(0.05)])
        guion.start(callback=lambda: llamadas.append(1))
        for _ in range(30):
            guion.update(FRAME)
        assert llamadas == [1]
        assert not guion._active

    def test_un_guion_vacio_no_se_queda_colgado(self):
        """Una cutscene sin acciones tiene que terminar, no bloquear la partida."""
        guion = CutsceneScript([])
        guion.start()
        for _ in range(10):
            guion.update(FRAME)
        assert guion._index >= len(guion._actions)

    def test_actualizar_sin_haber_arrancado_no_hace_nada(self):
        guion = CutsceneScript([WaitAction(1.0)])
        guion.update(FRAME)      # sin `start()`
        assert guion._index == 0

    def test_el_fundido_cubre_la_pantalla_y_la_descubre(self):
        """Un fundido que no llega a tapar del todo deja ver el corte."""
        fundido = FadeAction(duration=0.5, fade_in=False)
        fundido.start()
        lienzo = _lienzo()
        lienzo.fill((255, 255, 255))
        # A mitad de camino ya tiene que haber oscurecido algo.
        for _ in range(15):
            fundido.update(FRAME)
        fundido.draw(lienzo)
        medio = pygame.surfarray.array3d(lienzo).mean()
        assert medio < 250.0, f"el fundido apenas oscureció: brillo medio {medio:.0f}"

    def test_un_fundido_a_negro_acaba_en_negro(self):
        """AUD-111 — el destello de un fotograma al final del fundido.

        `draw` salía antes de tiempo al terminar, y con eso la pantalla —que
        llevaba medio segundo oscureciéndose— volvía de golpe a plena luz
        durante un fotograma justo antes del corte. Dieciséis milisegundos que
        son exactamente lo que un fundido existe para evitar.
        """
        fundido = FadeAction(duration=0.2, fade_in=False)
        fundido.start()
        lienzo = _lienzo()
        lienzo.fill((255, 255, 255))
        for _ in range(30):        # se pasa de los 0,2 s a propósito
            fundido.update(FRAME)
        fundido.draw(lienzo)
        medio = pygame.surfarray.array3d(lienzo).mean()
        assert medio < 40.0, (
            f"tras terminar el fundido a negro la pantalla vale {medio:.0f}: "
            f"hay un destello antes del corte"
        )

    def test_una_accion_declara_cuando_ha_terminado(self):
        """`update` devuelve True al acabar: es el contrato del que depende el orden."""
        espera = WaitAction(0.1)
        espera.start()
        assert espera.update(0.05) is False
        assert espera.update(0.10) is True

"""
El sistema de diálogo llega a la pantalla, y su texto cabe en ella.

AUD-127 — el octavo huérfano del mes, y el más caro
====================================================
El sistema estaba **construido, actualizado y dibujado**, y no se abría nunca.
`Stage0._check_dialogue_triggers` buscaba el árbol así::

    tree_id = getattr(mt, "dialogue_tree_id", "")

…y `MessageTrigger` **no tenía ese campo**. El `getattr` devolvía la cadena
vacía en todas las iteraciones, la condición nunca se cumplía, y los dos
árboles que stage 0 construye llevaban meses escritos sin llegar a la pantalla.

Por qué ninguna prueba lo cazó
-------------------------------
Porque el sistema **sí** aparecía en la prueba de humo: se instanciaba, su
`update` corría, su `draw` se llamaba. Un sistema que se actualiza y se dibuja
parece vivo en el perfil y en la cobertura. Lo que no había era una prueba que
preguntara *«¿puede un mapa abrir un diálogo?»*, que es la única pregunta que
importa.

Es el mismo `getattr(objeto, "campo", defecto)` de AUD-039 contra un campo
inexistente: no falla, calla.

AUD-128 — lo que salió al abrirlo
----------------------------------
Cuatro defectos que ninguna prueba podía encontrar mientras nada lo mostraba:
sin salto de línea (medido: el texto de stage 0 ocupa 769 px y el cuadro
tenía 728 útiles, 672 con retrato),
fuentes fuera del tema (la escala de accesibilidad no llegaba a la pantalla con
más texto del juego), sin adelantar, y velocidad fija.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings, user_settings
from src.engine.core.events import Events
from src.engine.core.user_settings import UserSettings
from src.engine.input.action_map import Action
from src.engine.ui.theme import Theme, clear_font_cache, font
from src.framework.stage.stage_loader import MessageTrigger
from src.framework.ui.dialogue_system import (
    DialogueNode,
    DialogueSystem,
    DialogueTree,
    dividir_en_lineas,
)


@pytest.fixture
def preferencias(monkeypatch):
    prefs = UserSettings()
    monkeypatch.setattr(user_settings, "get", lambda: prefs)
    clear_font_cache()
    yield prefs
    clear_font_cache()


class _BusFalso:
    def __init__(self) -> None:
        self.emitidos: list[tuple[str, dict]] = []

    def emit(self, nombre: str, **datos) -> None:
        self.emitidos.append((nombre, datos))


class _EntradaFalsa:
    """Un gestor de entrada que devuelve lo que se le diga."""

    def __init__(self) -> None:
        self.pulsadas: set[Action] = set()

    def is_action_just_pressed(self, accion: Action) -> bool:
        return accion in self.pulsadas

    def is_action_held(self, accion: Action) -> bool:
        return False


class _ContextoFalso:
    def __init__(self) -> None:
        self.event_bus = _BusFalso()
        self.input_manager = _EntradaFalsa()


@pytest.fixture
def sistema(preferencias) -> DialogueSystem:
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    return DialogueSystem(_ContextoFalso())


def _arbol_simple(texto: str = "Hola.") -> DialogueTree:
    return DialogueTree("prueba", "inicio", {
        "inicio": DialogueNode("inicio", "Eco", texto),
    })


class TestUnMapaPuedeAbrirUnDialogo:
    """AUD-127 — la pregunta que faltaba: ¿lo alcanza el jugador?"""

    def test_el_disparador_de_mensaje_tiene_el_campo(self) -> None:
        """Sin el campo, el `getattr` del escenario devuelve "" para siempre."""
        mt = MessageTrigger(rect=pygame.Rect(0, 0, 32, 32), text="")
        assert hasattr(mt, "dialogue_tree_id")

    def test_el_cargador_lee_la_propiedad_del_tmx(self) -> None:
        """El diseñador escribe `dialogue = intro` en Tiled y funciona."""
        from src.framework.stage.stage_loader import StageLoader

        class _Obj:
            x, y, width, height = 10, 20, 48, 48

        class _Datos:
            message_triggers: list = []

        datos = _Datos()
        StageLoader._handle_message_trigger(
            datos, _Obj(), {"text": "hola", "dialogue": "intro"})
        assert datos.message_triggers[0].dialogue_tree_id == "intro"

    def test_sin_la_propiedad_sigue_siendo_un_mensaje_normal(self) -> None:
        """No romper los quince mapas que ya usan `MessageTrigger`."""
        from src.framework.stage.stage_loader import StageLoader

        class _Obj:
            x, y, width, height = 0, 0, 32, 32

        class _Datos:
            message_triggers: list = []

        datos = _Datos()
        StageLoader._handle_message_trigger(datos, _Obj(), {"text": "aviso"})
        assert datos.message_triggers[0].text == "aviso"
        assert datos.message_triggers[0].dialogue_tree_id == ""


class TestElTextoCabeEnLaPantalla:
    """AUD-128 — medido: 769 px de texto en 672 px útiles de cuadro."""

    def test_una_linea_larga_se_parte(self, sistema) -> None:
        fuente = font(Theme.FONT_SMALL)
        # El texto real de la introducción de stage 0, palabra por palabra.
        texto = (
            "The world lies in ruin. You are the last Legacy. "
            "Each zone teaches you the skills you need. "
            "Press F2-F10 anytime for educational panels."
        )
        # Ancho útil con retrato, que es el caso peor y el que usa stage 0.
        ancho = 672
        assert fuente.size(texto)[0] > ancho, (
            f"el texto de ejemplo mide {fuente.size(texto)[0]} px y cabe en "
            f"{ancho}: esta prueba no probaría nada. Es la guarda que cazó que "
            f"mi primera estimación —«unos 1.100 px»— estaba mal por 300."
        )
        lineas = dividir_en_lineas(texto, fuente, ancho)
        assert len(lineas) > 1
        for linea in lineas:
            assert fuente.size(linea)[0] <= ancho, f"«{linea}» se sale"

    def test_no_se_pierde_ni_una_palabra(self, sistema) -> None:
        """Partir no es recortar."""
        fuente = font(Theme.FONT_SMALL)
        texto = "una frase con varias palabras que hay que partir en trozos"
        assert " ".join(dividir_en_lineas(texto, fuente, 100)).split() == texto.split()

    def test_los_saltos_de_linea_escritos_se_respetan(self, sistema) -> None:
        fuente = font(Theme.FONT_SMALL)
        assert dividir_en_lineas("uno\ndos", fuente, 500) == ["uno", "dos"]

    def test_una_palabra_gigante_no_cuelga(self, sistema) -> None:
        """Se desborda en su línea, pero termina. Antes esto era un bucle."""
        fuente = font(Theme.FONT_SMALL)
        lineas = dividir_en_lineas("M" * 300, fuente, 50)
        assert len(lineas) == 1

    def test_texto_vacio_no_produce_lineas(self, sistema) -> None:
        assert dividir_en_lineas("", font(Theme.FONT_SMALL), 500) == []

    def test_con_el_texto_al_doble_tambien_cabe(self, sistema, preferencias) -> None:
        """La ayuda de accesibilidad no debe sacar el texto del cuadro."""
        preferencias.text_scale = 2.0
        clear_font_cache()
        fuente = font(Theme.FONT_SMALL)
        ancho = settings.INTERNAL_WIDTH - 120
        for linea in dividir_en_lineas("palabra " * 40, fuente, ancho):
            assert fuente.size(linea)[0] <= ancho


class TestLaAccesibilidadLlegaAlDialogo:
    """La pantalla con más texto del juego es la que más lo necesita."""

    def test_la_escala_de_texto_agranda_la_fuente_del_dialogo(
        self, sistema, preferencias,
    ) -> None:
        base = sistema._font_text.get_height()
        preferencias.text_scale = 2.0
        clear_font_cache()
        assert sistema._font_text.get_height() > base, (
            "el diálogo construía sus fuentes con pygame.font.Font directo y "
            "se saltaba la escala de accesibilidad"
        )

    @pytest.mark.parametrize(
        ("velocidad", "esperado"),
        [("slow", 15.0), ("normal", 30.0), ("fast", 60.0), ("instant", 0.0)],
    )
    def test_cada_velocidad_ofrecida_se_aplica(
        self, sistema, preferencias, velocidad, esperado,
    ) -> None:
        preferencias.text_speed = velocidad
        assert sistema._velocidad == pytest.approx(esperado)

    def test_instantaneo_muestra_el_texto_entero_de_golpe(
        self, sistema, preferencias,
    ) -> None:
        preferencias.text_speed = "instant"
        sistema.start_dialogue(_arbol_simple("un texto bastante largo"))
        assert sistema._full_text_visible, (
            "con «instant» el jugador sigue viendo la máquina de escribir"
        )

    def test_una_velocidad_desconocida_no_tumba_el_arranque(self) -> None:
        assert UserSettings(text_speed="turbo").text_speed == "normal"


class TestAdelantarYCerrar:
    def test_confirmar_adelanta_la_maquina_de_escribir(
        self, sistema, preferencias,
    ) -> None:
        """AUD-128 — antes había que esperar siempre."""
        preferencias.text_speed = "slow"
        sistema.start_dialogue(_arbol_simple("un texto que tarda en salir"))
        sistema.update(1 / 60)
        assert not sistema._full_text_visible

        sistema._context.input_manager.pulsadas = {Action.CONFIRM}
        sistema.update(1 / 60)
        assert sistema._full_text_visible
        assert sistema.active, "adelantar no debe cerrar el diálogo"

    def test_confirmar_otra_vez_lo_cierra(self, sistema, preferencias) -> None:
        preferencias.text_speed = "instant"
        sistema.start_dialogue(_arbol_simple())
        sistema._context.input_manager.pulsadas = {Action.CONFIRM}
        sistema.update(1 / 60)
        assert not sistema.active

    def test_al_cerrarse_avisa(self, sistema, preferencias) -> None:
        """Sin evento, nada puede reaccionar a una conversación acabada."""
        preferencias.text_speed = "instant"
        sistema.start_dialogue(_arbol_simple())
        sistema._context.input_manager.pulsadas = {Action.CONFIRM}
        sistema.update(1 / 60)
        nombres = [n for n, _ in sistema._context.event_bus.emitidos]
        assert Events.DIALOGUE_FINISHED in nombres

    def test_un_destino_inexistente_cierra_sin_reventar(
        self, sistema, preferencias,
    ) -> None:
        """Una errata en el guion no debe dejar el juego colgado."""
        preferencias.text_speed = "instant"
        arbol = DialogueTree("roto", "inicio", {
            "inicio": DialogueNode("inicio", "Eco", "¿?",
                                   choices=[("ir", "no_existe")]),
        })
        sistema.start_dialogue(arbol)
        sistema._context.input_manager.pulsadas = {Action.CONFIRM}
        sistema.update(1 / 60)
        assert not sistema.active

    def test_end_como_destino_cierra(self, sistema, preferencias) -> None:
        preferencias.text_speed = "instant"
        arbol = DialogueTree("t", "inicio", {
            "inicio": DialogueNode("inicio", "Eco", "adiós",
                                   choices=[("fin", "__end__")]),
        })
        sistema.start_dialogue(arbol)
        sistema._context.input_manager.pulsadas = {Action.CONFIRM}
        sistema.update(1 / 60)
        assert not sistema.active


class TestUnArbolSePuedeEscribirSinProgramar:
    """AUD-127 — la razón por la que un estudiante se hizo el suyo.

    Si la única forma de escribir una conversación es instanciar
    `DialogueNode` en Python, un diseñador que no programa no puede escribir
    ninguna, y uno que sí programa prefiere escribir la suya antes que leer el
    motor. Eso fue literalmente lo que pasó.
    """

    def test_se_construye_desde_un_diccionario(self) -> None:
        arbol = DialogueTree.desde_datos({
            "id": "intro", "start": "saludo",
            "nodes": {
                "saludo": {
                    "speaker": "Eco", "text": "Hola.",
                    "choices": [["Seguir", "__end__"]],
                },
            },
        })
        assert arbol.tree_id == "intro"
        assert arbol.start_node == "saludo"
        assert arbol.nodes["saludo"].speaker == "Eco"
        assert arbol.nodes["saludo"].choices == [("Seguir", "__end__")]

    def test_un_diccionario_incompleto_no_revienta(self) -> None:
        """Un JSON a medio escribir da un árbol vacío, no una excepción."""
        arbol = DialogueTree.desde_datos({})
        assert arbol.nodes == {}

    def test_el_arbol_construido_asi_se_puede_reproducir(
        self, sistema, preferencias,
    ) -> None:
        """Construirlo no basta: tiene que funcionar en el sistema real."""
        preferencias.text_speed = "instant"
        arbol = DialogueTree.desde_datos({
            "id": "t", "start": "a",
            "nodes": {"a": {"speaker": "Eco", "text": "Hola."}},
        })
        sistema.start_dialogue(arbol)
        assert sistema.active
        assert sistema._current_node is not None
        assert sistema._current_node.text == "Hola."


class TestDibujarNoRevienta:
    """El camino real: `draw` sobre una superficie del tamaño del juego."""

    @pytest.mark.parametrize("escala", [1.0, 2.0])
    def test_dibuja_con_retrato_ausente_y_texto_largo(
        self, sistema, preferencias, escala,
    ) -> None:
        preferencias.text_scale = escala
        clear_font_cache()
        arbol = DialogueTree("t", "a", {
            "a": DialogueNode(
                "a", "Eco", "palabra " * 60, portrait="no_existe.png",
                choices=[("una", "__end__"), ("otra", "__end__")]),
        })
        sistema.start_dialogue(arbol)
        sistema.update(10.0)
        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        sistema.draw(lienzo)

    def test_el_cuadro_no_se_sale_de_la_pantalla(
        self, sistema, preferencias,
    ) -> None:
        """Con el texto al doble, el cuadro crece; no debe salirse."""
        preferencias.text_scale = 2.0
        clear_font_cache()
        from src.framework.ui.dialogue_system import ALTO_CUADRO

        alto = int(ALTO_CUADRO * 2.0)
        assert alto + 10 < settings.INTERNAL_HEIGHT, (
            f"el cuadro de diálogo mide {alto} px de alto con la escala al "
            f"doble y la pantalla tiene {settings.INTERNAL_HEIGHT}"
        )

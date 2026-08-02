"""
Module: dialogue_system
System: framework.ui

Diálogo ramificado con retratos, nombre de quien habla y elecciones.

AUD-127 — el octavo huérfano, y el más caro
============================================
El sistema estaba **completo, construido, actualizado y dibujado**, y no se
abría nunca. `Stage0._check_dialogue_triggers` buscaba el árbol así::

    tree_id = getattr(mt, "dialogue_tree_id", "")

…y `MessageTrigger` **no tenía ese campo**. El `getattr` devolvía la cadena
vacía en todas las iteraciones, la condición nunca se cumplía, y los dos
árboles que stage 0 construye —la introducción y el bestiario— llevaban meses
escritos sin llegar jamás a la pantalla.

Es exactamente el patrón de AUD-039: `getattr(objeto, "campo", defecto)` contra
un campo inexistente no falla, **calla**. Y un sistema que se actualiza y se
dibuja parece vivo en cualquier revisión superficial: aparece en el perfil,
aparece en la cobertura, y no hace nada.

Eso explica además por qué un estudiante escribió en su propio código «no se usa
el `DialogueAction` del motor: está pensado para conversación». Cuando la única
forma de ver un diálogo es leer el código y construir un `DialogueTree` a mano,
lo normal es concluir que el sistema no sirve.

AUD-128 — cuatro defectos que sólo se ven cuando el sistema se ve
=================================================================
Al abrirlo por primera vez salieron cuatro problemas que ninguna prueba podía
haber encontrado mientras nada lo mostraba:

1. **Sin salto de línea.** `render(texto)` dibuja **una sola línea**. Medido:
   el texto de introducción de stage 0 son 136 caracteres que a 16 px ocupan
   **769 px**, y el ancho útil del cuadro era **728**. Con retrato, 672. Se
   salía por la derecha y se perdía el final de la frase — y con la escala de
   accesibilidad al doble se pierde la mitad.

   (La primera versión de este comentario decía «unos 1.100 px». Era una
   estimación mía, no una medición, y estaba mal por 300 px. La cazó la propia
   prueba, que empieza comprobando que el texto de ejemplo de verdad no cabe.)
2. **Fuentes fuera del tema.** `pygame.font.Font(None, 16)` directo, así que la
   escala de texto de accesibilidad (AUD-126) **no se aplicaba justo en la
   pantalla con más texto de todo el juego**.
3. **Sin adelantar.** Pulsar confirmar mientras el texto se escribe no hacía
   nada. Hay que esperar a que termine la máquina de escribir, siempre, y eso
   en la segunda vuelta de un nivel es una pequeña tortura.
4. **Velocidad fija.** 30 caracteres por segundo para todo el mundo. La
   velocidad de lectura es una necesidad de accesibilidad, no una preferencia
   estética.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings, user_settings
from src.engine.core.events import Events
from src.engine.input.action_map import Action
from src.engine.ui.theme import Theme, font
from src.engine.utils.asset_loader import AssetLoader

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

#: Alto del cuadro de diálogo, en píxeles, a escala de texto 1,0.
ALTO_CUADRO: int = 110

#: Margen lateral del cuadro respecto a la pantalla.
MARGEN: int = 20

#: Caracteres por segundo de la máquina de escribir, por velocidad elegida.
#:
#: `instant` no es una comodidad: para quien usa lector de pantalla o tiene
#: dificultad de procesamiento, ver el texto entero de golpe es la diferencia
#: entre leer y perseguir letras.
VELOCIDADES_DE_TEXTO: dict[str, float] = {
    "slow": 15.0,
    "normal": 30.0,
    "fast": 60.0,
    "instant": 0.0,          # 0 = sin animación
}


def dividir_en_lineas(
    texto: str, fuente: pygame.font.Font, ancho_max: int,
) -> list[str]:
    """Parte `texto` en líneas que quepan en `ancho_max` píxeles.

    AUD-128 — el defecto que esto corrige.

    Se mide con la fuente **real**, no con un número de caracteres estimado:
    una tipografía proporcional hace que «iiii» y «MMMM» ocupen anchos muy
    distintos, y con la escala de accesibilidad al doble cualquier estimación
    por caracteres se queda corta justo para quien más necesita que no lo haga.

    Una palabra que no cabe entera se deja en su línea y se desborda: partirla
    a mitad la haría ilegible, y una palabra de 80 caracteres en un diálogo es
    un error del guion, no un caso que el motor deba maquillar.
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


class DialogueNode:
    """Un nodo de un árbol de diálogo."""

    def __init__(self, node_id: str, speaker: str, text: str,
                 portrait: str | None = None,
                 choices: list[tuple[str, str]] | None = None,
                 on_enter: str | None = None,
                 on_exit: str | None = None) -> None:
        self.node_id: str = node_id
        self.speaker: str = speaker
        self.text: str = text
        self.portrait: str | None = portrait
        self.choices: list[tuple[str, str]] = choices or []
        self.on_enter: str | None = on_enter
        self.on_exit: str | None = on_exit


class DialogueTree:
    """Un árbol completo, con su nodo de entrada."""

    def __init__(self, tree_id: str, start_node: str,
                 nodes: dict[str, DialogueNode]) -> None:
        self.tree_id: str = tree_id
        self.start_node: str = start_node
        self.nodes: dict[str, DialogueNode] = nodes

    @classmethod
    def desde_datos(cls, datos: dict) -> DialogueTree:
        """Construye un árbol desde un diccionario, típicamente de JSON.

        AUD-127 — por qué existe esto.

        Antes la única forma de escribir un diálogo era instanciar
        `DialogueNode` en Python. Un diseñador de niveles que no programa no
        podía escribir una conversación, y un estudiante que sí programa
        prefería escribir la suya antes que leer el motor. Con esto, un árbol
        es un fichero de datos:

        ```json
        {
          "id": "intro", "start": "saludo",
          "nodes": {
            "saludo": {"speaker": "Eco", "text": "Hola.",
                       "choices": [["Seguir", "__end__"]]}
          }
        }
        ```

        `__end__` como destino cierra el diálogo; es el único nombre reservado.
        """
        nodos: dict[str, DialogueNode] = {}
        for node_id, bruto in (datos.get("nodes") or {}).items():
            nodos[node_id] = DialogueNode(
                node_id=node_id,
                speaker=str(bruto.get("speaker", "")),
                text=str(bruto.get("text", "")),
                portrait=bruto.get("portrait"),
                choices=[
                    (str(t), str(d)) for t, d in (bruto.get("choices") or [])
                ],
                on_enter=bruto.get("on_enter"),
                on_exit=bruto.get("on_exit"),
            )
        return cls(
            tree_id=str(datos.get("id", "")),
            start_node=str(datos.get("start", "")),
            nodes=nodos,
        )


class DialogueSystem:
    """Muestra diálogos con retrato, elecciones y ramificación."""

    def __init__(self, context: GameContext) -> None:
        self._context = context
        self._active: bool = False
        self._current_tree: DialogueTree | None = None
        self._current_node: DialogueNode | None = None
        self._selected_choice: int = 0
        self._text_progress: float = 0.0
        self._full_text_visible: bool = False
        self._portrait_cache: dict[str, pygame.Surface] = {}
        # AUD-128: las fuentes ya no se construyen aquí ni con
        # `pygame.font.Font` directo. `theme.font()` aplica la escala de
        # accesibilidad, cachea, y sobrevive a un `pygame.font.quit()` — los
        # tres motivos por los que existe (AUD-030, AUD-077, AUD-126).

    # ── fuentes, siempre a través del tema ─────────────────────

    @property
    def _font_name(self) -> pygame.font.Font:
        return font(Theme.FONT_BODY)

    @property
    def _font_text(self) -> pygame.font.Font:
        return font(Theme.FONT_SMALL)

    @property
    def _font_choice(self) -> pygame.font.Font:
        return font(Theme.FONT_SMALL)

    @property
    def _velocidad(self) -> float:
        """Caracteres por segundo, según la preferencia del jugador."""
        try:
            nombre = user_settings.get().text_speed
        except Exception:            # el diálogo se muestra igual
            nombre = "normal"
        return VELOCIDADES_DE_TEXTO.get(nombre, 30.0)

    # ── ciclo de vida ──────────────────────────────────────────

    def start_dialogue(self, tree: DialogueTree) -> None:
        self._active = True
        self._current_tree = tree
        self._selected_choice = 0
        # AUD-144 — mientras se habla, la música se aparta.
        #
        # Es el truco más viejo de la radio y el que más se nota: sin él, el
        # jugador sube el volumen para leer el diálogo con la voz de fondo y
        # se lleva un susto con el siguiente golpe. Se pide aquí y no en cada
        # línea porque una conversación es una unidad: agacharse y levantarse
        # entre frase y frase suena a fallo.
        audio = getattr(self._context, "audio", None)
        if audio is not None and hasattr(audio, "agachar_musica"):
            audio.agachar_musica()
        self._go_to_node(tree.start_node)

    def _go_to_node(self, node_id: str) -> None:
        if self._current_tree is None:
            return
        # `__end__` es el único destino reservado: cierra el diálogo.
        if node_id == "__end__":
            self.end_dialogue()
            return
        node = self._current_tree.nodes.get(node_id)
        if node is None:
            if node_id:
                logger.warning(
                    "dialogue_system: el árbol %r no tiene el nodo %r; se "
                    "cierra el diálogo. Revisa los destinos de las opciones.",
                    self._current_tree.tree_id, node_id,
                )
            self.end_dialogue()
            return
        self._current_node = node
        self._text_progress = 0.0
        self._full_text_visible = self._velocidad <= 0.0
        self._selected_choice = 0
        if node.on_enter:
            self._execute_action(node.on_enter)

    def _execute_action(self, action: str) -> None:
        """Ejecuta una acción de guion: `give_item:llave`, `set_flag:x`."""
        parts = action.split(":")
        if len(parts) < 2:
            return
        cmd, arg = parts[0], ":".join(parts[1:])
        if cmd == "give_item":
            self._context.event_bus.emit(Events.ITEM_COLLECTED, item_id=arg)
        elif cmd == "set_flag":
            self._context.event_bus.emit(Events.FLAG_SET, flag=arg)

    def end_dialogue(self) -> None:
        """Cierra el diálogo y **avisa**.

        AUD-127: antes terminaba en silencio, así que nada podía reaccionar a
        que una conversación hubiera acabado — ni abrir una puerta, ni empezar
        una cutscene, ni marcar un objetivo.
        """
        arbol = self._current_tree.tree_id if self._current_tree else ""
        if self._current_node and self._current_node.on_exit:
            self._execute_action(self._current_node.on_exit)
        self._active = False
        self._current_tree = None
        self._current_node = None
        audio = getattr(self._context, "audio", None)
        if audio is not None and hasattr(audio, "soltar_musica"):
            audio.soltar_musica()
        if arbol:
            self._context.event_bus.emit(Events.DIALOGUE_FINISHED, tree_id=arbol)

    # ── fotograma ──────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if not self._active or self._current_node is None:
            return

        velocidad = self._velocidad
        if not self._full_text_visible:
            if velocidad <= 0.0:
                self._full_text_visible = True
            else:
                self._text_progress += velocidad * dt
                if self._text_progress >= len(self._current_node.text):
                    self._text_progress = float(len(self._current_node.text))
                    self._full_text_visible = True

        im = self._context.input_manager
        if im is None:
            return
        confirmar = im.is_action_just_pressed(Action.CONFIRM)

        # AUD-128 — adelantar la máquina de escribir.
        #
        # Antes, confirmar mientras el texto salía no hacía nada: había que
        # esperar siempre. En la segunda vuelta de un nivel eso es una pequeña
        # tortura, y es la razón por la que la gente aprende a saltarse los
        # diálogos en cuanto puede.
        if not self._full_text_visible:
            if confirmar or im.is_action_just_pressed(Action.CANCEL):
                self._text_progress = float(len(self._current_node.text))
                self._full_text_visible = True
            return

        if self._current_node.choices:
            total = len(self._current_node.choices)
            if im.is_action_just_pressed(Action.MOVE_DOWN):
                self._selected_choice = (self._selected_choice + 1) % total
            if im.is_action_just_pressed(Action.MOVE_UP):
                self._selected_choice = (self._selected_choice - 1) % total
            if confirmar:
                _, next_id = self._current_node.choices[self._selected_choice]
                self._go_to_node(next_id)
        elif confirmar or im.is_action_just_pressed(Action.CANCEL):
            self.end_dialogue()

    # ── dibujado ───────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        if not self._active or self._current_node is None:
            return

        w = settings.INTERNAL_WIDTH
        h = settings.INTERNAL_HEIGHT
        # El cuadro crece con la escala de texto: con el texto al doble, un
        # cuadro de alto fijo recortaría justo lo que la ayuda hacía legible.
        alto = int(ALTO_CUADRO * self._escala_actual())
        box = pygame.Rect(MARGEN, h - alto - 10, w - MARGEN * 2, alto)

        velo = pygame.Surface(box.size, pygame.SRCALPHA)
        velo.fill(Theme.OVERLAY)
        surface.blit(velo, box.topleft)
        pygame.draw.rect(surface, Theme.BORDER, box, 2,
                         border_radius=Theme.RADIUS)

        px = box.x + Theme.SPACE_M
        py = box.y + Theme.SPACE_S
        lado_retrato = int(48 * self._escala_actual())
        retrato = self._retrato(self._current_node.portrait, lado_retrato)
        if retrato is not None:
            surface.blit(retrato, (px, py))
            px += lado_retrato + Theme.SPACE_S

        nombre = self._font_name.render(
            self._current_node.speaker, True, Theme.ACCENT)
        surface.blit(nombre, (px, py))
        y = py + nombre.get_height() + Theme.SPACE_XS

        ancho_texto = box.right - px - Theme.SPACE_M
        visible = self._current_node.text[:int(self._text_progress)]
        for linea in dividir_en_lineas(visible, self._font_text, ancho_texto):
            if y + self._font_text.get_height() > box.bottom - Theme.SPACE_S:
                break
            surface.blit(self._font_text.render(linea, True, Theme.TEXT), (px, y))
            y += self._font_text.get_height() + 2

        if not self._full_text_visible:
            return

        if self._current_node.choices:
            for i, (texto, _) in enumerate(self._current_node.choices):
                if y + self._font_choice.get_height() > box.bottom:
                    break
                elegido = i == self._selected_choice
                color = Theme.ACCENT if elegido else Theme.TEXT_MUTED
                prefijo = "> " if elegido else "  "
                surface.blit(
                    self._font_choice.render(f"{prefijo}{texto}", True, color),
                    (px, y),
                )
                y += self._font_choice.get_height() + 2
        else:
            pista = self._font_text.render("[ENTER]", True, Theme.TEXT_DIM)
            surface.blit(pista, (box.right - pista.get_width() - Theme.SPACE_M,
                                 box.bottom - pista.get_height() - Theme.SPACE_XS))

    # ── auxiliares ─────────────────────────────────────────────

    @staticmethod
    def _escala_actual() -> float:
        try:
            return float(user_settings.get().text_scale)
        except Exception:            # el diálogo se dibuja igual
            return 1.0

    def _retrato(self, nombre: str | None, lado: int) -> pygame.Surface | None:
        """El retrato pedido, o un marcador si no se puede cargar.

        Un retrato que falta no debe dejar hueco ni tumbar la escena: se
        sustituye por un rectángulo del color de superficie, que se lee como
        «aquí va una cara» y no como un error.
        """
        if not nombre:
            return None
        clave = f"{nombre}@{lado}"
        cacheado = self._portrait_cache.get(clave)
        if cacheado is not None:
            return cacheado
        try:
            imagen = AssetLoader.load_image(
                settings.ASSETS_DIR / "sprites" / "portraits" / nombre,
                size=(lado, lado),
            )
        except (pygame.error, FileNotFoundError, PermissionError):
            logger.warning("dialogue_system: no se pudo cargar el retrato %s", nombre)
            imagen = pygame.Surface((lado, lado))
            imagen.fill(Theme.SURFACE_RAISED)
        self._portrait_cache[clave] = imagen
        return imagen

    @property
    def active(self) -> bool:
        return self._active

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
2. **Fuentes fuera del tema.** `font(16)` directo, así que la
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
from src.engine.ui.text_panel import (
    FlujoDeTexto,
    dibuja_ficha,
    dibuja_panel,
    dividir_en_lineas,
)
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


#: AUD-291 — la marca que un guion pone donde va el nombre del jugador.
#:
#: Llaves y no `$nombre` ni `%s`: es lo que ya usa cualquiera que haya escrito
#: una plantilla, y no choca con la puntuación normal de una frase en español.
MARCA_DE_APODO: str = "{apodo}"


def personalizar(texto: str) -> str:
    """Cambia `{apodo}` por cómo se llama quien está jugando — AUD-291.

    Se hace aquí, al dibujar, y **no** al cargar el árbol: el apodo se puede
    cambiar a mitad de partida desde la pantalla de identificación, y un texto
    sustituido al cargar seguiría diciendo el nombre viejo hasta reiniciar el
    nivel. Es la misma razón por la que la escala de accesibilidad se lee en
    cada fotograma.

    Un guion que no use la marca no paga nada: la comprobación es un `in` sobre
    una cadena corta, y se hace antes de tocar la sesión académica.
    """
    if MARCA_DE_APODO not in texto:
        return texto
    from src.framework.academic.sesion import SesionAcademica

    return texto.replace(MARCA_DE_APODO, SesionAcademica.instancia().apodo)


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
        #: AUD-269 — página que se está leyendo. Un texto que no cabe en el
        #: cuadro se recortaba en silencio: el jugador veía media frase, pulsaba
        #: ENTER y el resto no se mostraba nunca.
        self._pagina: int = 0
        self._portrait_cache: dict[str, pygame.Surface] = {}
        # AUD-128: las fuentes ya no se construyen aquí ni con
        # `pygame.font.Font` directo. `theme.font()` aplica la escala de
        # accesibilidad, cachea, y sobrevive a un `pygame.font.quit()` — los
        # tres motivos por los que existe (AUD-030, AUD-077, AUD-126).
        #
        # AUD-611 — paginación y bloque de texto calculados UNA vez por
        # (nodo, página, escala), no en cada fotograma. La clave invalida
        # por escala de accesibilidad: subirla a mitad de conversación
        # re-envuelve el texto al fotograma siguiente.
        self._clave_flujo: tuple | None = None
        self._paginas_cache: list[list[str]] = [[]]
        self._flujo = FlujoDeTexto()

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
        nombre = user_settings.preferencia("text_speed", "normal")
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
        self._pagina = 0
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
        elif cmd == "complete_objective":
            # AUD-400 — un guion puede dar un objetivo por cumplido (GAP-047).
            #
            # Es el enganche que el hueco daba por existente —«el diálogo ya
            # ejecuta acciones»— y el que hace posible «habla con el vigía»
            # como objetivo: hablar no emite nada contable hasta que la
            # conversación termina, y a veces sólo cuenta una rama concreta.
            #
            # Se emite por el bus en vez de llamar al sistema de objetivos: el
            # diálogo no tiene por qué saber que ese sistema existe, y así
            # cualquier otra cosa puede reaccionar al mismo aviso.
            self._context.event_bus.emit(Events.OBJECTIVE_REQUESTED,
                                         objective_id=arg)

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
                total = self._caracteres_de_pagina()
                self._text_progress += velocidad * dt
                if self._text_progress >= total:
                    self._text_progress = float(total)
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
                self._text_progress = float(self._caracteres_de_pagina())
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
            self.confirmar()

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

        # AUD-611 — panel del tema: sombra, cuerpo redondeado y borde, en
        # vez de un velo negro plano. El coste son tres primitivas.
        dibuja_panel(surface, box)
        # Filo de acento arriba: marca el cuadro como "voz", no como menú.
        pygame.draw.line(surface, Theme.ACCENT_DIM,
                         (box.x + Theme.RADIUS_L, box.y),
                         (box.right - Theme.RADIUS_L, box.y), 2)

        px = box.x + Theme.SPACE_M
        py = box.y + Theme.SPACE_S + 2
        lado_retrato = int(48 * self._escala_actual())
        retrato = self._retrato(self._current_node.portrait, lado_retrato)
        if retrato is not None:
            surface.blit(retrato, (px, py))
            px += lado_retrato + Theme.SPACE_M

        # AUD-611 — el nombre va en una FICHA redondeada y no suelto: es la
        # jerarquía visual de todo diálogo moderno (quien habla se lee de un
        # vistazo, antes incluso de la primera letra del texto).
        nombre_surf = self._font_name.render(
            self._current_node.speaker, True, (24, 26, 44))
        ficha = pygame.Rect(0, 0,
                            nombre_surf.get_width() + Theme.SPACE_M,
                            nombre_surf.get_height() + 6)
        ficha.topleft = (px, py - 3)
        surface.blit(nombre_surf, dibuja_ficha(surface, ficha, nombre_surf))
        y = ficha.bottom + Theme.SPACE_XS + 2

        # AUD-269/611 — se dibuja la página ya envuelta y renderizada una
        # vez; la máquina de escribir sólo recorta.
        self._asegura_flujo()
        self._flujo.dibujar(
            surface, (px, y), caracteres=int(self._text_progress))
        y += self._flujo.tamano()[1] + Theme.SPACE_XS

        if not self._full_text_visible:
            return

        if self._current_node.choices:
            for i, (texto, _) in enumerate(self._current_node.choices):
                opcion_surf = self._font_choice.render(
                    texto, True,
                    (24, 26, 44) if i == self._selected_choice
                    else Theme.TEXT_MUTED,
                )
                if y + opcion_surf.get_height() + 6 > box.bottom - Theme.SPACE_S:
                    break
                elegido = i == self._selected_choice
                chip = pygame.Rect(
                    0, 0, opcion_surf.get_width() + Theme.SPACE_M + 8,
                    opcion_surf.get_height() + 6,
                )
                chip.topleft = (px, y)
                # AUD-611 — las opciones son chips: la elegida con fondo de
                # acento y flecha, las demás apagadas. Antes eran tres líneas
                # de texto con un "> " delante, indistinguibles del guion.
                pos_texto = dibuja_ficha(
                    surface, chip, opcion_surf,
                    fondo=Theme.ACCENT if elegido else Theme.SURFACE_RAISED,
                )
                if elegido:
                    surface.blit(opcion_surf, pos_texto + pygame.Vector2(10, 0))
                    pygame.draw.polygon(
                        surface, (24, 26, 44),
                        [(chip.x + 8, chip.centery - 4),
                         (chip.x + 8, chip.centery + 4),
                         (chip.x + 14, chip.centery)],
                    )
                else:
                    surface.blit(opcion_surf, pos_texto)
                y += chip.height + 4
        else:
            texto_pista = ("[ENTER]" if self.paginas <= 1
                           else f"[ENTER] {self._pagina + 1}/{self.paginas}")
            pista = self._font_text.render(texto_pista, True, Theme.TEXT_DIM)
            surface.blit(pista, (box.right - pista.get_width() - Theme.SPACE_M,
                                 box.bottom - pista.get_height() - Theme.SPACE_XS))

    # ── paginación (AUD-269) ───────────────────────────────────

    def _lineas_por_pagina(self) -> int:
        """Cuántas líneas caben en el cuadro, con la escala de texto actual.

        Se calcula, no se fija: la escala de accesibilidad llega a 2,0×, y un
        número escrito a mano volvería a recortar texto en cuanto alguien la
        subiera — que es el defecto que esto arregla.
        """
        alto = int(ALTO_CUADRO * self._escala_actual())
        util = alto - Theme.SPACE_S * 2 - self._font_name.get_height()
        paso = self._font_text.get_height() + 2
        return max(1, util // paso)

    def _ancho_util_de_texto(self) -> int:
        w = settings.INTERNAL_WIDTH
        return max(120, w - MARGEN * 2
                   - int(48 * self._escala_actual()) - Theme.SPACE_M * 3)

    def _asegura_flujo(self) -> None:
        """Paginas y bloque de la página actual, si la clave cambió.

        AUD-611 — antes `update()` llamaba `_texto_de_la_pagina()` dos
        veces por fotograma y cada una re-partía el texto midiendo palabra
        a palabra con la fuente; con un guion largo eso era medir miles de
        píxeles sesenta veces por segundo para no cambiar nada.
        """
        nodo = self._current_node
        clave = (
            id(nodo), self._pagina, self._escala_actual(),
            self._ancho_util_de_texto(),
        )
        if self._clave_flujo == clave:
            return
        self._clave_flujo = clave
        if nodo is None:
            self._paginas_cache = [[]]
            self._flujo.preparar("", self._font_text, 10)
            return
        lineas = dividir_en_lineas(
            personalizar(nodo.text), self._font_text,
            self._ancho_util_de_texto(),
        )
        if not lineas:
            lineas = [""]
        por_pagina = self._lineas_por_pagina()
        self._paginas_cache = [
            lineas[i:i + por_pagina]
            for i in range(0, len(lineas), por_pagina)
        ] or [[""]]
        indice = min(self._pagina, len(self._paginas_cache) - 1)
        self._flujo.preparar(
            "\n".join(self._paginas_cache[indice]),
            self._font_text, settings.INTERNAL_WIDTH,
            separacion=2,
        )

    def _paginas_de_texto(self) -> list[list[str]]:
        """El texto del nodo, repartido en páginas de líneas."""
        self._asegura_flujo()
        return self._paginas_cache

    def _caracteres_de_pagina(self) -> int:
        self._asegura_flujo()
        return self._flujo.caracteres_totales()

    @property
    def paginas(self) -> int:
        return len(self._paginas_de_texto())

    @property
    def pagina_actual(self) -> int:
        return self._pagina

    def confirmar(self) -> None:
        """ENTER con el texto ya visible: pasa de página, o cierra.

        Es un método público porque la escena y las pruebas necesitan el mismo
        camino que la tecla: tener dos formas de avanzar un diálogo es cómo se
        acaba con una que pagina y otra que no.
        """
        if self._pagina + 1 < self.paginas:
            self._pagina += 1
            # La máquina de escribir se reinicia: si no, la página siguiente
            # aparecería entera de golpe y el ritmo de lectura cambiaría a
            # mitad de la frase.
            self._text_progress = 0.0
            self._full_text_visible = self._velocidad <= 0.0
            return
        self.end_dialogue()

    # ── auxiliares ─────────────────────────────────────────────

    @staticmethod
    def _escala_actual() -> float:
        return float(user_settings.preferencia("text_scale", 1.0))

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

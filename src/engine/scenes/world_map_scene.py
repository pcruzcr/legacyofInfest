from __future__ import annotations

import logging
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import draw_key_hints, draw_screen

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_data import SaveData


# ── Los nodos, sacados del registro de escenarios ────────────────────
#
# AUD-155. Esta lista estaba escrita a mano con cinco entradas —`stage0`,
# `stage1`, `stage2`, `stage3`, `stage4`— y **cuatro de las cinco apuntaban a
# mapas que no existen**: las carpetas reales son `stage1_1`,
# `stage1_2_la_soda`, `boss_venado`… Entrar en cualquier nodo que no fuera
# Stage 0 hacía esto:
#
#     if tmx_path.exists():        ← falso
#         ...replace(StageScene)   ← no se ejecutaba
#
# Es decir: pulsar Enter no hacía nada y no decía nada. Y los once escenarios
# que entregaron los estudiantes no aparecían en el mapa del mundo en absoluto,
# aunque estaban instalados, validados y en el registro de escenarios.
#
# Ahora los nodos salen de `stage_registry.discover_stages()`, que es la misma
# fuente que usa el juego para encadenar niveles. Si un estudiante entrega un
# escenario y se añade al registro, aparece aquí solo.


#: Nodos por fila del zigzag. Lo leen `_serpiente` —que coloca— y
#: `WorldMapScene._SALTO_VERTICAL` —que navega—: si cada uno tuviera el suyo,
#: bajar una fila dejaría al cursor en un sitio que no está debajo de nada, que
#: es exactamente lo que pasaba (AUD-266).
NODOS_POR_FILA = 3


def _serpiente(indice: int, total: int) -> tuple[float, float]:
    """Coloca el nodo `indice` en zigzag dentro del área normalizada.

    En zigzag y no en rejilla porque un mapa del mundo tiene que leerse como
    un **recorrido**: la línea que une dos nodos es la que dice en qué orden se
    juegan. Con quince escenarios, tres por fila caben sin que las etiquetas se
    pisen a 800 px de ancho.
    """
    por_fila = NODOS_POR_FILA
    fila, columna = divmod(indice, por_fila)
    if fila % 2:                      # las filas impares van al revés
        columna = por_fila - 1 - columna
    filas = max(1, (total + por_fila - 1) // por_fila)
    nx = columna / (por_fila - 1) if por_fila > 1 else 0.5
    ny = fila / (filas - 1) if filas > 1 else 0.5
    return round(nx, 3), round(ny, 3)


#: Cuánto puede apartarse un nodo de su casilla, en coordenadas normalizadas.
#:
#: AUD-448 — 0,055 es lo que rompe la alineación sin que un escenario acabe
#: más cerca del vecino de otra fila que del suyo. Medido sobre los dieciséis
#: escenarios: ninguna pareja baja de 0,04 de separación.
_DISPERSION_MAXIMA = 0.055


def dispersion_de(identificador: str) -> tuple[float, float]:
    """Cuánto se aparta este escenario de su casilla — AUD-448.

    Sale del identificador y no de un generador de azar, y esa es la parte que
    importa: el mapa se dibuja **igual en todos los arranques**. Uno que se
    recoloca cada vez que abres el juego es peor que una rejilla, porque se
    pierde la memoria del sitio — y recordar dónde estaba un nivel es lo que
    hace que un mundo se sienta un mundo.

    `hash()` no vale aquí: Python lo aleatoriza por proceso desde 3.3, así que
    el mapa cambiaría entre ejecuciones. `md5` es estable y aquí no protege
    nada, sólo reparte.
    """
    import hashlib

    digest = hashlib.md5(identificador.encode("utf-8")).digest()
    # Dos bytes independientes, llevados a [-1, 1] y escalados.
    dx = (digest[0] / 127.5 - 1.0) * _DISPERSION_MAXIMA
    dy = (digest[1] / 127.5 - 1.0) * _DISPERSION_MAXIMA
    return round(dx, 4), round(dy, 4)


def construir_nodos() -> list[dict[str, Any]]:
    """Un nodo por escenario descubierto, en el orden en que se juegan."""
    from src.engine.core.stage_registry import discover_stages

    nodos: list[dict[str, Any]] = []
    escenarios = discover_stages()
    for i, cls in enumerate(escenarios):
        stage_id = getattr(cls, "STAGE_ID", "") or cls.__name__
        nombre = getattr(cls, "STAGE_NAME", "") or stage_id
        nx, ny = _serpiente(i, len(escenarios))
        # AUD-448 — la serpentina deja las columnas perfectamente alineadas y
        # el mapa se lee como una lista doblada en zigzag. Se aparta cada nodo
        # de su casilla, siempre lo mismo para el mismo escenario, y se acota
        # al marco para que ninguno se salga de la pantalla.
        # La rejilla base se comprime para dejar sitio a la dispersión, en vez
        # de recortar después: recortando, todos los nodos del borde acababan
        # exactamente en 0,0 y volvían a alinearse —justo el defecto que esto
        # viene a quitar, sólo que ahora en la primera columna.
        margen = _DISPERSION_MAXIMA
        dx, dy = dispersion_de(stage_id)
        nx = round(margen + nx * (1.0 - 2 * margen) + dx, 4)
        ny = round(margen + ny * (1.0 - 2 * margen) + dy, 4)
        nodos.append({
            "id": stage_id,
            "name": nombre,
            "nx": nx,
            "ny": ny,
            # El escenario se abre por su clase, no por su ruta TMX: la clase
            # es la que registra los tipos de entidad propios del estudiante
            # (`CuadernoVolador`, `BossRey`…). Construir un `StageScene`
            # genérico con su TMX cargaría el mapa sin sus enemigos.
            "scene": cls,
            "unlocks": [],
        })
    for anterior, siguiente in pairwise(nodos):
        anterior["unlocks"] = [siguiente["id"]]
    return nodos


STAGE_NODES: list[dict[str, Any]] = construir_nodos()

_node_index = {nd["id"]: i for i, nd in enumerate(STAGE_NODES)}
CONNECTIONS: list[tuple[int, int]] = [
    (i, _node_index[uid])
    for i, nd in enumerate(STAGE_NODES)
    for uid in nd.get("unlocks", [])
    if uid in _node_index
]


class WorldMapScene(BaseScene):
    #: Cuántos nodos salta el cursor con arriba/abajo. Es el ancho de la fila
    #: del zigzag: cualquier otro número mueve el cursor a un nodo que no está
    #: encima ni debajo del actual. Era **2** con una rejilla de **3**, resto
    #: de cuando la lista tenía cinco nodos escritos a mano (AUD-266).
    _SALTO_VERTICAL = NODOS_POR_FILA

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._selected: int = 0
        # AUD-069: fuentes de la escala del tema, a través de su caché.
        self._font_name = font(Theme.FONT_SMALL)
        self._save_data: SaveData | None = None
        self._nodes: list[dict[str, Any]] = []

    def _load_save_data(self) -> None:
        sm = self.context.save_manager
        if sm is not None:
            slot = sm.newest_slot()
            if slot is not None:
                self._save_data = sm.load(slot)

    def _build_nodes(self) -> None:
        completed: list[str] = []
        if self._save_data is not None:
            completed = list(self._save_data.completed_stages)

        # AUD-155 — la regla de desbloqueo tampoco funcionaba. Era:
        #
        #     any(prev_id in completed for prev_id in STAGE_NODES
        #         if node["id"] in nd.get("unlocks", []))
        #
        # `prev_id` iteraba sobre `STAGE_NODES`, que son **diccionarios**, así
        # que `prev_id in completed` comparaba un dict contra una lista de
        # cadenas: siempre falso. Y el `if` miraba `nd`, que es el nodo actual,
        # no el anterior. Lo que quedaba en pie era «desbloqueado si eres
        # stage0 o si ya lo completaste», de modo que **terminar un nivel no
        # abría el siguiente**: el mapa no progresaba.
        #
        # La regla escrita para que se lea: el primero siempre está abierto, y
        # cada uno abre al siguiente.
        self._nodes = []
        anterior_completado = True      # el primero no depende de nadie
        for nd in STAGE_NODES:
            node = dict(nd)
            hecho = node["id"] in completed
            node["completed"] = hecho
            node["unlocked"] = anterior_completado or hecho
            anterior_completado = hecho
            self._nodes.append(node)

    def on_enter(self) -> None:
        self._load_save_data()
        self._build_nodes()
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        prev = self._selected
        if im.is_action_just_pressed(Action.MOVE_RIGHT):
            self._selected = (self._selected + 1) % len(self._nodes)
        if im.is_action_just_pressed(Action.MOVE_LEFT):
            self._selected = (self._selected - 1) % len(self._nodes)
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = (self._selected + self._SALTO_VERTICAL) % len(self._nodes)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = (self._selected - self._SALTO_VERTICAL) % len(self._nodes)
        if self._selected != prev:
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)
        if im.is_action_just_pressed(Action.CONFIRM):
            self._entrar(self._nodes[self._selected])
        if im.is_action_just_pressed(Action.CANCEL):
            # AUD-533 — mismo arreglo que `InventoryScene`/`SkillTreeScene`:
            # `pop()` vuelve a quien haya empujado esta pantalla en vez de
            # mandar siempre al título.
            self.context.scene_manager.pop()

    def _entrar(self, node: dict[str, Any]) -> bool:
        """Abre el escenario del nodo. Devuelve si se pudo.

        Se construye **la clase del escenario**, no un `StageScene` genérico
        con su TMX: es la clase la que registra los tipos de entidad propios de
        cada entrega (`CuadernoVolador`, `BossRey`, `LaSodaWalkerRaton`…). Con
        el genérico el mapa cargaría y sus enemigos no.
        """
        if not node.get("unlocked"):
            return False
        self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)

        cls = node.get("scene")
        if cls is not None:
            # AUD-266 — **declarar la cola antes de entrar**, o el nivel no
            # tiene continuación.
            #
            # Esto faltaba, y era el defecto que hacía que el mapa del mundo
            # «no funcionara»: `SceneManager._on_stage_complete` incrementa el
            # índice y llama a `_enter_next_stage()`, que compara contra la
            # cola. El mapa entraba con `replace()` y sin tocarla, así que al
            # terminar el nivel la cola estaba vacía —o traía la de una partida
            # cargada— y el jugador se encontraba **los créditos finales** en
            # mitad del juego.
            #
            # La cola es la misma lista que el mapa dibuja, y la misma que
            # `story_scene` pone al empezar la campaña: un solo orden de juego.
            self._declarar_cola(node)
            self.context.scene_manager.replace(cls(self.context))
            return True

        # Sin clase, el TMX por convención. Es el camino de respaldo para un
        # mapa suelto que aún no tiene escena propia.
        node_id = node["id"]
        tmx_path = Path(settings.ASSETS_DIR / "maps" / node_id / f"{node_id}.tmx")
        if not tmx_path.exists():
            # Antes esto era un `if` sin `else` y el jugador pulsaba Enter
            # contra un nodo muerto sin ninguna señal. Un aviso en el registro
            # es lo mínimo para que se pueda diagnosticar.
            logger.warning(
                "mapa del mundo: «%s» no tiene ni escena ni mapa en %s",
                node_id, tmx_path,
            )
            return False
        from src.framework.scenes.stage_scene import StageScene
        self.context.scene_manager.replace(StageScene(self.context, tmx_path))
        return True

    def _declarar_cola(self, node: dict[str, Any]) -> None:
        """Deja la cola de escenarios en el nodo elegido (AUD-266)."""
        gestor = self.context.scene_manager
        clases = [nd["scene"] for nd in self._nodes if nd.get("scene") is not None]
        if not clases:
            return
        gestor.set_stage_queue(clases)
        try:
            gestor.set_stage_index(self._nodes.index(node))
        except ValueError:          # un nodo que no salió de esta lista
            pass

    #: Posiciones de los nodos en coordenadas **normalizadas**, de 0 a 1
    #: dentro del área de contenido.
    #:
    #: AUD-093 — antes eran píxeles absolutos: (80, 60), (200, 50), (280, 80)...
    #: Se escribieron para la resolución de referencia de 320x224, y la interna
    #: es 800x600. `draw_screen` devuelve y = 105 como inicio del contenido, así
    #: que **tres de los cinco nodos se dibujaban encima del título** y el mapa
    #: ocupaba el tercio superior izquierdo de la pantalla.
    #:
    #: Normalizadas, el mapa se reparte por el área disponible sea cual sea la
    #: resolución, y nunca invade la cabecera ni la barra de atajos.
    _MARGEN_X = 0.10
    _MARGEN_INFERIOR = 46      # deja sitio a los atajos de teclado

    def _posicion(self, nodo: dict, top: int) -> tuple[int, int]:
        """Traduce la posición normalizada de un nodo a píxeles de pantalla."""
        ancho = settings.INTERNAL_WIDTH
        alto_util = settings.INTERNAL_HEIGHT - top - self._MARGEN_INFERIOR
        x = ancho * (self._MARGEN_X + nodo["nx"] * (1.0 - 2 * self._MARGEN_X))
        y = top + alto_util * nodo["ny"]
        return int(x), int(y)

    def draw(self, surface: pygame.Surface) -> None:
        # AUD-069: la navegación sigue siendo por grafo —los nodos están
        # colocados en un mapa, no en una lista— pero la paleta y los atajos
        # ya son los del resto del juego. Antes esta pantalla tenía siete
        # colores propios y un fondo distinto del de todas las demás.
        top = draw_screen(surface, "MAPA DEL MUNDO", "Elige tu destino")

        posiciones = [self._posicion(n, top) for n in self._nodes]

        # AUD-448 — la línea, en segundo plano. Antes tenía el mismo grosor
        # que el radio del marcador y era lo más llamativo de la pantalla: se
        # veía la línea y los escenarios eran su decoración. Ahora es un
        # px y del color del borde, para que diga «éste lleva a éste» sin
        # competir con lo que se elige.
        for a, b in CONNECTIONS:
            colour = (Theme.ACCENT_DIM if self._nodes[a].get("completed")
                      else Theme.BORDER)
            pygame.draw.line(surface, colour, posiciones[a], posiciones[b], 1)

        for idx, node in enumerate(self._nodes):
            focused = idx == self._selected
            if focused:
                colour = Theme.ACCENT
            elif node.get("completed"):
                colour = Theme.SUCCESS
            elif node.get("unlocked"):
                colour = Theme.TEXT_MUTED
            else:
                colour = Theme.TEXT_DIM
            px, py = posiciones[idx]
            # AUD-448 — el marcador enfocado también crece. El anillo solo se
            # pierde entre dieciséis círculos del mismo tamaño; con el radio
            # cambiando, «dónde estoy» se ve de un vistazo sin leer el color,
            # que es lo que necesita quien juega con el filtro daltónico.
            radio = 13 if focused else 9
            pygame.draw.circle(surface, colour, (px, py), radio)
            # Un aro oscuro separa el marcador del fondo del mapa, que puede
            # ser de cualquier color detrás de un escenario u otro.
            pygame.draw.circle(surface, Theme.BG, (px, py), radio, 1)
            if focused:
                # Anillo alrededor del nodo enfocado: en un mapa, el color solo
                # no basta para distinguir «seleccionado» de «completado».
                pygame.draw.circle(surface, Theme.TEXT, (px, py), radio + 4, 1)
            label = self._font_name.render(
                node["name"], True,
                Theme.TEXT if node.get("unlocked") else Theme.TEXT_DIM,
            )
            # La etiqueta se sitúa a la izquierda si el nodo está pegado al
            # borde derecho, para que no se salga de la pantalla.
            lx = px + 16
            if lx + label.get_width() > settings.INTERNAL_WIDTH - 8:
                lx = px - 16 - label.get_width()
            surface.blit(label, (lx, py - 8))

        draw_key_hints(surface, [
            ("←→↑↓", "Navegar"),
            ("Enter", "Entrar"),
            ("Esc", "Volver"),
        ])


from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.core.save_data import MAX_SLOTS, SaveData
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG,
    COLOR_ERROR,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_SMALL,
    draw_bottom_bar,
    draw_top_bar,
)
from src.engine.ui.theme import font

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


def _stage_display_name(stage_id: str) -> str:
    mapping = {
        "stage0": "Stage 0: Prólogo",
        "boss_venado": "Boss: Venado Sagrado",
    }
    return mapping.get(stage_id, stage_id.replace("_", " ").title())


#: El personaje con el que nace una partida — AUD-443.
#:
#: Hoy sólo hay uno. La elección existe igualmente porque crear el perfil es
#: el momento en que se decide, y añadirla después obligaría a migrar todas
#: las partidas ya guardadas.
PERSONAJE_POR_DEFECTO = "paburu"


def entrar_al_escenario(context: GameContext, data: SaveData) -> bool:
    """Monta la cola de escenarios y entra por donde iba la partida — AUD-445.

    Vive fuera de la pantalla de partidas porque ahora hay dos caminos que
    llegan aquí: elegir una partida y luego CONTINUAR desde el menú. Dejarlo
    dentro de la escena obligaría al menú a instanciar una pantalla que no va
    a mostrar sólo para reutilizar un método.

    Devuelve `False` si no hay escenarios que jugar, para que quien llame
    decida qué decirle al jugador; aquí no se sabe si hay una barra de estado
    donde escribirlo.
    """
    from src.engine.core.stage_registry import discover_stages

    escenarios = discover_stages()
    if not escenarios:
        return False
    indice = max(0, min(int(data.stage_index), len(escenarios) - 1))
    context.pending_load = data
    gestor = context.scene_manager
    gestor.set_stage_queue(escenarios)
    gestor.set_stage_index(indice)
    gestor.replace(escenarios[indice](context))
    return True


class LoadGameScene(BaseScene):
    """Las partidas guardadas: elegir una, o crear una donde no hay.

    AUD-443 — antes sólo dejaba elegir. Confirmar sobre una ranura vacía
    respondía «elige un slot con datos», así que la pantalla que existe para
    escoger partida no permitía crear ninguna: la partida nacía por el menú de
    título, sin nombre, sin personaje y sin decidir en qué ranura vivía.
    """

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._selected: int = 0
        self._slots: list[SaveData | None] = [None] * MAX_SLOTS
        self._error_msg: str = ""
        self._error_timer: float = 0.0
        #: AUD-443 — modo creación: se está escribiendo el nombre de la nueva
        #: partida en la ranura seleccionada.
        self._creando: bool = False
        self._nombre: str = ""
        self._font_small = font(FONT_SMALL)

    # ── lo que la pantalla deja consultar ──────────────────────────

    @property
    def creando(self) -> bool:
        return self._creando

    @property
    def nombre_en_curso(self) -> str:
        return self._nombre

    def seleccionar(self, indice: int) -> None:
        """Mueve la selección a una fila concreta (0 = ranura 1)."""
        self._selected = max(0, min(MAX_SLOTS - 1, int(indice)))

    def on_enter(self) -> None:
        self._selected = 0
        self._refresh_slots()
        self._error_msg = ""
        self._error_timer = 0.0
        self.context.scene_manager.transition.start_fade_in(0.5)

    def _refresh_slots(self) -> None:
        sm = self.context.save_manager
        self._slots = [None] * MAX_SLOTS
        if sm is not None:
            for entry in sm.list_slots():
                slot = entry["slot"] - 1
                if 0 <= slot < MAX_SLOTS:
                    data = sm.load(entry["slot"])
                    self._slots[slot] = data

    def on_exit(self) -> None:
        pass

    def process_events(self, events: list[pygame.event.Event]) -> None:
        """El nombre de la partida nueva, tecla a tecla — AUD-443.

        Se lee de `event.unicode` y no del código de tecla, igual que la
        pantalla de identificación: `pygame.K_*` es la posición física en el
        teclado y `unicode` es la letra que el jugador **cree** estar
        escribiendo, que es la que respeta su distribución.
        """
        if not self._creando:
            return
        for evento in events:
            if evento.type != pygame.KEYDOWN:
                continue
            if evento.key == pygame.K_BACKSPACE:
                self._nombre = self._nombre[:-1]
                continue
            caracter = getattr(evento, "unicode", "") or ""
            # `isprintable()` deja fuera tabuladores, retornos y controles, que
            # `unicode` también entrega y que en un nombre no pintan nada.
            if caracter.isprintable() and len(self._nombre) < SaveData.LARGO_MAXIMO_DEL_NOMBRE:
                self._nombre += caracter

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._error_timer > 0:
            self._error_timer -= dt
            if self._error_timer <= 0:
                self._error_msg = ""

        if self._creando:
            self._actualizar_creacion(im)
            return

        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = (self._selected + 1) % MAX_SLOTS
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = (self._selected - 1) % MAX_SLOTS

        if im.is_action_just_pressed(Action.CONFIRM):
            data = self._slots[self._selected]
            if data is None:
                # AUD-443 — antes esto era un error. Una ranura vacía es una
                # invitación a empezar, no un fallo del jugador.
                self._creando = True
                self._nombre = ""
            else:
                self._cargar_partida(data)

        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))

    def _actualizar_creacion(self, im: object) -> None:
        """El paso de crear: confirmar crea la partida, cancelar vuelve.

        Todo cuelga de flancos (`is_action_just_pressed`) y no de estados, y
        eso es lo que garantiza que la risa de Paburu suene **una vez**: si
        colgara de «¿está confirmado?», mantener la tecla la dispararía sesenta
        veces por segundo, superpuesta consigo misma.
        """
        if im.is_action_just_pressed(Action.CANCEL):  # type: ignore[attr-defined]
            self._creando = False
            self._nombre = ""
            self.context.event_bus.emit(Events.SFX_MENU_CANCEL)
            return
        if im.is_action_just_pressed(Action.CONFIRM):  # type: ignore[attr-defined]
            if not self._nombre.strip():
                # Una partida sin nombre deja la pantalla igual de
                # indistinguible que antes de tener nombres.
                self._error_msg = "Ponle un nombre a la partida"
                self._error_timer = 2.0
                return
            self._crear_partida()

    def _crear_partida(self) -> None:
        """Aquí es donde el perfil existe por primera vez.

        Se escribe en disco antes de ir a ningún sitio: si el juego se cierra
        entre crear y jugar, la partida ya está y la ranura deja de estar
        vacía. Y se declara activa (AUD-441) para que el autoguardado
        siguiente vaya a ésta y no a la de marca más reciente.
        """
        gestor = self.context.save_manager
        if gestor is None:
            self._error_msg = "No se puede guardar en este equipo"
            self._error_timer = 2.0
            return
        ranura = self._selected + 1
        datos = SaveData(
            slot_id=ranura,
            profile_name=self._nombre,
            character=PERSONAJE_POR_DEFECTO,
        )
        gestor.ranura_activa = ranura
        gestor.save(ranura, datos)
        # AUD-443 — la risa, en el flanco de confirmación del personaje.
        self.context.event_bus.emit(Events.SFX_VOZ_PABURU)
        self._creando = False
        self._nombre = ""
        self._refresh_slots()

    def _cargar_partida(self, data: SaveData | None) -> None:
        """Activa el perfil elegido y abre el menú principal — AUD-445.

        Antes esto entraba **directo al escenario**, y por eso el jugador que
        quería mirar su inventario tenía que entrar a jugar y volver atrás. El
        menú principal es lo que se viene a ver después de elegir partida.

        El estado se aplica aquí y no al entrar al escenario: en cuanto se
        vuelve al menú, la tienda y el inventario ya tienen que estar
        enseñando lo de **esta** partida.
        """
        if data is None:
            return
        from src.engine.core.save_manager import aplicar_estado_de
        from src.engine.scenes.title_scene import TitleScene

        # AUD-292 — la partida trae su cartera, su ropa y su marcador.
        aplicar_estado_de(data)
        # AUD-441 — se declara qué partida se juega. Sin esto el autoguardado
        # elige destino por marca de tiempo y, con dos partidas en disco,
        # escribe el progreso de ésta encima de la otra.
        gestor = self.context.save_manager
        if gestor is not None and data.slot_id:
            gestor.ranura_activa = data.slot_id
        self.context.pending_load = data
        self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "NUEVA PARTIDA" if self._creando else "PARTIDAS",
                     "SLOT" if self._creando else "ARCHIVOS")

        cy = 32
        for i in range(MAX_SLOTS):
            data = self._slots[i]
            selected = i == self._selected

            slot_rect = pygame.Rect(20, cy, settings.INTERNAL_WIDTH - 40, 28)
            if selected:
                pygame.draw.rect(surface, (40, 40, 80), slot_rect, border_radius=3)

            pygame.draw.rect(surface, (60, 60, 100), slot_rect, 1, border_radius=3)

            slot_num = self._font_small.render(f"  SLOT {i + 1}", True,
                                               COLOR_HIGHLIGHT if selected else COLOR_TEXT)
            surface.blit(slot_num, (26, cy + 2))

            if self._creando and selected:
                # AUD-443 — la fila que se está creando muestra lo que se
                # escribe, con cursor. Se edita en su sitio y no en un cuadro
                # aparte: así se ve dónde va a vivir la partida.
                cursor = "_" if int(pygame.time.get_ticks() / 400) % 2 == 0 else " "
                escrito = self._font_small.render(
                    f"  Nombre: {self._nombre}{cursor}", True, COLOR_HIGHLIGHT)
                surface.blit(escrito, (26, cy + 14))
            elif data is not None:
                # AUD-442 — el nombre primero: es lo que distingue una partida
                # de otra. Sin él, elegir era elegir por marca de tiempo.
                nombre = data.profile_name or f"Partida {i + 1}"
                stage_str = _stage_display_name(data.stage_id)
                horas = int(data.play_time // 3600)
                minutos = int((data.play_time % 3600) // 60)
                info = (f"  {nombre}  |  {stage_str}  |  {horas:d}h {minutos:02d}m"
                        f"  |  {data.health:.0f}/{data.max_health:.0f}")
                info_surf = self._font_small.render(info, True, (160, 160, 180))
                surface.blit(info_surf, (26, cy + 14))
            else:
                vacia = self._font_small.render(
                    "  (vacía — pulsa Enter para empezar aquí)", True, (100, 100, 100))
                surface.blit(vacia, (26, cy + 14))

            cy += 34

        if self._error_msg:
            err = self._font_small.render(self._error_msg, True, COLOR_ERROR)
            ex = (settings.INTERNAL_WIDTH - err.get_width()) // 2
            surface.blit(err, (ex, 180))

        if self._creando:
            draw_bottom_bar(
                surface,
                f"  Escribe el nombre  |  Personaje: {PERSONAJE_POR_DEFECTO.upper()}"
                f"  |  Enter: crear  |  Esc: volver")
        else:
            draw_bottom_bar(
                surface,
                "  ↑↓: elegir partida  |  Enter: jugar o crear  |  Esc: volver")

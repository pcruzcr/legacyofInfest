from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pygame
import pygame_gui

from src.engine.core import settings, user_settings
from src.engine.core.difficulty import Difficulty, set_difficulty
from src.engine.core.user_settings import ESCALAS_DE_TEXTO
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.theme import clear_font_cache

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class OptionsScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._gui_manager = pygame_gui.UIManager(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )
        self._ui_elements: list[pygame_gui.core.UIElement] = []
        self._dirty = False
        self._btn_subtitles: Any = None
        self._btn_language: Any = None
        self._idioma_actual: str = "es"
        self._subtitles_on: bool = False
        self._dropdown_texto: Any = None
        self._btn_movimiento: Any = None
        self._btn_mantener: Any = None
        self._movimiento_reducido: bool = False
        self._mantener_pulsado: bool = False

    #: Tamaño base de la tipografía de pygame_gui, en píxeles.
    #:
    #: AUD-160 — la escala de texto no llegaba a esta pantalla.
    #:
    #: `text_scale` la aplica `engine.ui.theme.escalar_texto`, que usan el kit
    #: de interfaz y el sistema de diálogo. Esta pantalla no usa ninguno de los
    #: dos: la dibuja `pygame_gui`, con su propia tipografía y su propio tema.
    #: Así que elegir «2.0x» agrandaba el texto de todo el juego **menos el de
    #: la pantalla donde se elige**, que es justo donde alguien que no puede
    #: leer el texto pequeño lo necesita.
    _TAM_FUENTE_BASE = 14

    #: Los tipos de elemento que hay en esta pantalla.
    #:
    #: Hay que nombrarlos uno a uno: un bloque `defaults` **no** llega a los
    #: elementos. Comprobado — con `defaults` el botón seguía midiendo 37×20 px
    #: y con `button` pasó a 72×39. Es el tipo de detalle que hace que un
    #: arreglo parezca aplicado y no lo esté.
    _ELEMENTOS_CON_TEXTO = ("label", "button", "drop_down_menu",
                            "horizontal_slider")

    def _tema_escalado(self) -> dict[str, Any]:
        """El tema de pygame_gui con la tipografía a la escala del jugador."""
        from src.engine.ui.theme import escalar_texto

        fuente = {"name": "noto_sans",
                  "size": str(escalar_texto(self._TAM_FUENTE_BASE))}
        return {elemento: {"font": dict(fuente)}
                for elemento in self._ELEMENTOS_CON_TEXTO}

    def _nuevo_gestor(self) -> pygame_gui.UIManager:
        gestor = pygame_gui.UIManager(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )
        try:
            gestor.get_theme().load_theme(self._tema_escalado())
            gestor.rebuild_all_from_changed_theme_data()
        except Exception:  # una versión de pygame_gui sin temas por diccionario
            logger.warning(
                "opciones: no se pudo aplicar la escala de texto al tema de "
                "pygame_gui; la pantalla se dibuja al tamaño base",
                exc_info=True,
            )
        return gestor

    # ── Disposición ───────────────────────────────────────────
    #
    # AUD-160 — la maqueta se calcula; no está clavada en píxeles.
    #
    # Todas las medidas eran literales: `Rect((200, y), (320, 28))`. Escritas
    # para la escala 1×, de modo que al subir el tamaño del texto pygame_gui
    # avisaba de once etiquetas que no caben en su rectángulo —«MOVIMIENTO
    # REDUCIDO (sacudida, estelas)» se salía por 264 px— y las filas se
    # desbordaban por debajo de la pantalla. La opción de accesibilidad
    # producía justo lo contrario de lo que promete: texto grande y cortado.
    #
    # La pantalla mide 800 × 600 y no se puede estirar, así que **no** se
    # escala todo por igual:
    #
    # * la **tipografía y el alto de fila** sí siguen la escala del jugador;
    # * el **ancho** se reparte sobre el que hay: el control ocupa una fracción
    #   y la etiqueta se lleva el resto, recortada al borde;
    # * el **paso vertical** sale de dividir el alto disponible entre las filas
    #   que hay, así que añadir una opción no vuelve a tirar la última fuera.
    _COL_IZQ = 40
    _MARGEN_SUP = 16
    _MARGEN_INF = 12
    #: Filas: título, dos deslizadores, dos desplegables, dos interruptores,
    #: la cabecera de accesibilidad, tres controles más y la fila de botones.
    _FILAS = 12

    def _tam_fuente(self) -> int:
        from src.engine.ui.theme import escalar_texto

        return escalar_texto(self._TAM_FUENTE_BASE)

    def _paso(self) -> int:
        """Alto de una fila: lo que cabe, nunca menos que el texto."""
        util = settings.INTERNAL_HEIGHT - self._MARGEN_SUP - self._MARGEN_INF
        return max(self._alto_control() + 4, util // self._FILAS)

    def _alto_control(self) -> int:
        return self._tam_fuente() + 12

    def _medir(self, texto: str) -> int:
        """Ancho real del texto con la tipografía del tema, más un margen."""
        try:
            fuente = self._gui_manager.get_theme().get_font(["label"])
            return fuente.size(texto)[0] + 12
        except Exception:      # sin tema utilizable, se estima
            return len(texto) * max(6, self._tam_fuente() // 2)

    def _fila(self, y: int, texto: str, x: int, ancho_max: int) -> None:
        """Dibuja la etiqueta de una fila, recortada para que no se salga."""
        ancho = min(self._medir(texto), max(1, ancho_max))
        pygame_gui.elements.UILabel(
            pygame.Rect((x, y), (ancho, self._alto_control())),
            texto, self._gui_manager,
        )

    def on_enter(self) -> None:
        audio = self.audio
        cfg = self._load_config()
        self._gui_manager = self._nuevo_gestor()
        self._ui_elements.clear()

        izq = self._COL_IZQ
        alto = self._alto_control()
        paso = self._paso()
        ancho_util = settings.INTERNAL_WIDTH - izq * 2
        # El control se lleva un tercio y la etiqueta el resto. Con el texto
        # grande el deslizador encoge en vez de empujar la etiqueta fuera.
        w_ctrl = max(90, int(ancho_util * 0.32))
        x_etq = izq + w_ctrl + 12
        ancho_etq = settings.INTERNAL_WIDTH - x_etq - izq

        y = self._MARGEN_SUP
        titulo = "OPTIONS"
        ancho_t = min(self._medir(titulo), ancho_util)
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                ((settings.INTERNAL_WIDTH - ancho_t) // 2, y), (ancho_t, alto)),
            text=titulo, manager=self._gui_manager,
        )
        y += paso

        self._slider_music = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((izq, y), (w_ctrl, alto)),
            start_value=cfg.get("music_volume",
                                float(audio.music_volume if audio else 0.7)),
            value_range=(0.0, 1.0), manager=self._gui_manager,
        )
        self._fila(y, "MUSIC VOLUME", x_etq, ancho_etq)
        y += paso

        self._slider_sfx = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((izq, y), (w_ctrl, alto)),
            start_value=cfg.get("sfx_volume",
                                float(audio.sfx_volume if audio else 1.0)),
            value_range=(0.0, 1.0), manager=self._gui_manager,
        )
        self._fila(y, "SFX VOLUME", x_etq, ancho_etq)
        y += paso

        self._dropdown_difficulty = pygame_gui.elements.UIDropDownMenu(
            options_list=["easy", "normal", "hard"],
            starting_option=cfg.get("difficulty", "normal"),
            relative_rect=pygame.Rect((izq, y), (w_ctrl, alto)),
            manager=self._gui_manager,
        )
        self._fila(y, "DIFFICULTY", x_etq, ancho_etq)
        y += paso

        self._dropdown_cb = pygame_gui.elements.UIDropDownMenu(
            options_list=["off", "protanopia", "deuteranopia", "tritanopia"],
            starting_option=cfg.get("colorblind_mode", "off"),
            relative_rect=pygame.Rect((izq, y), (w_ctrl, alto)),
            manager=self._gui_manager,
        )
        self._fila(y, "COLORBLIND MODE", x_etq, ancho_etq)
        y += paso

        # AUD-036: subtitles had no UI at all. Captions for non-speech audio are
        # implemented by engine.ui.subtitle_overlay; this is how a player turns
        # them on.
        self._subtitles_on = bool(cfg.get("subtitles_enabled", False))
        self._btn_subtitles = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((izq, y), (w_ctrl, alto)),
            text=self._subtitles_label(), manager=self._gui_manager,
        )
        self._fila(y, "SUBTITLES (audio captions)", x_etq, ancho_etq)
        y += paso

        # F3.1: selector de idioma. Sin esto la traducción existiría y nadie
        # podría cambiarla sin editar config.json a mano.
        self._idioma_actual = cfg.get("language", "es")
        self._btn_language = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((izq, y), (w_ctrl, alto)),
            text=self._language_label(), manager=self._gui_manager,
        )
        self._fila(y, "IDIOMA / LANGUAGE", x_etq, ancho_etq)
        y += paso

        # ── Accesibilidad (AUD-126) ────────────────────────────
        # El modo daltonismo ya estaba; faltaban las tres barreras que más
        # gente encuentran en un plataformas. Van juntas y con etiqueta propia
        # para que se encuentren: una opción de accesibilidad escondida entre
        # los ajustes de volumen no la usa quien la necesita.
        self._fila(y, "ACCESIBILIDAD / ACCESSIBILITY", izq, ancho_util)
        y += paso

        self._dropdown_texto = pygame_gui.elements.UIDropDownMenu(
            options_list=[f"{e:g}x" for e in ESCALAS_DE_TEXTO],
            starting_option=f"{cfg.get('text_scale', 1.0):g}x",
            relative_rect=pygame.Rect((izq, y), (w_ctrl, alto)),
            manager=self._gui_manager,
        )
        self._fila(y, "TAMANO DEL TEXTO", x_etq, ancho_etq)
        y += paso

        self._movimiento_reducido = bool(cfg.get("reduced_motion", False))
        self._btn_movimiento = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((izq, y), (w_ctrl, alto)),
            text=self._movimiento_label(), manager=self._gui_manager,
        )
        self._fila(y, "MOVIMIENTO REDUCIDO", x_etq, ancho_etq)
        y += paso

        self._mantener_pulsado = bool(cfg.get("hold_to_press", False))
        self._btn_mantener = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((izq, y), (w_ctrl, alto)),
            text=self._mantener_label(), manager=self._gui_manager,
        )
        self._fila(y, "PULSAR EN VEZ DE MANTENER", x_etq, ancho_etq)
        y += paso

        # Los dos botones van en la misma fila: apilados, la última se salía
        # de la pantalla en cuanto el texto crecía.
        w_boton = (ancho_util - 12) // 2
        self._btn_keybindings = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((izq, y), (w_boton, alto)),
            text="KEY BINDINGS", manager=self._gui_manager,
        )
        self._btn_back = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((izq + w_boton + 12, y), (w_boton, alto)),
            text="BACK", manager=self._gui_manager,
        )

        self.context.scene_manager.transition.start_fade_in(0.5)

    def _subtitles_label(self) -> str:
        return f"SUBTITLES: {'ON' if self._subtitles_on else 'OFF'}"

    def _movimiento_label(self) -> str:
        return f"MOVIMIENTO: {'REDUCIDO' if self._movimiento_reducido else 'NORMAL'}"

    def _mantener_label(self) -> str:
        return f"ENTRADA: {'PULSAR' if self._mantener_pulsado else 'MANTENER'}"

    #: Nombres que se muestran, en su propio idioma. Un desplegable que dijera
    #: «Español / Inglés» en inglés es exactamente lo que no ayuda a quien no
    #: sabe inglés.
    _NOMBRES_IDIOMA = {"es": "ESPAÑOL", "en": "ENGLISH"}

    def _language_label(self) -> str:
        return self._NOMBRES_IDIOMA.get(self._idioma_actual, self._idioma_actual)

    def _toggle_language(self) -> None:
        """Alterna entre los idiomas disponibles y lo aplica al momento."""
        from src.engine.core.i18n import IDIOMAS, set_idioma

        indice = IDIOMAS.index(self._idioma_actual) if \
            self._idioma_actual in IDIOMAS else 0
        self._idioma_actual = IDIOMAS[(indice + 1) % len(IDIOMAS)]
        set_idioma(self._idioma_actual)
        if self._btn_language is not None:
            self._btn_language.set_text(self._language_label())

    def _load_config(self) -> dict[str, Any]:
        """Current preference values, for populating the widgets."""
        prefs = user_settings.get()
        return {
            "music_volume": prefs.music_volume,
            "sfx_volume": prefs.sfx_volume,
            "difficulty": prefs.difficulty,
            "colorblind_mode": prefs.colorblind_mode,
            "subtitles_enabled": prefs.subtitles_enabled,
            "language": prefs.language,
            "text_scale": prefs.text_scale,
            "reduced_motion": prefs.reduced_motion,
            "hold_to_press": prefs.hold_to_press,
        }

    def _save_config(self) -> None:
        """Apply the widget values to the live preferences and persist them.

        AUD-036: this used to write the values straight to a JSON file that
        nothing ever read back, so the colourblind dropdown persisted a choice
        that never reached the renderer. Writing through ``user_settings`` means
        the change takes effect on the very next frame *and* survives a restart.
        """
        prefs = user_settings.get()
        prefs.music_volume = self._slider_music.get_current_value()
        prefs.sfx_volume = self._slider_sfx.get_current_value()
        prefs.difficulty = self._dropdown_difficulty.selected_option[0]
        prefs.colorblind_mode = self._dropdown_cb.selected_option[0]
        if self._btn_subtitles is not None:
            prefs.subtitles_enabled = self._subtitles_on
        if self._btn_language is not None:
            prefs.language = self._idioma_actual
        if self._dropdown_texto is not None:
            # El desplegable muestra «1.5x»; se guarda el número.
            prefs.text_scale = float(
                self._dropdown_texto.selected_option[0].rstrip("x"))
        if self._btn_movimiento is not None:
            prefs.reduced_motion = self._movimiento_reducido
        if self._btn_mantener is not None:
            prefs.hold_to_press = self._mantener_pulsado
        # Cambiar la escala invalida toda la caché de fuentes: las que hay
        # dentro se crearon con el tamaño anterior y seguirían saliendo
        # pequeñas hasta reiniciar, que es cuando el jugador concluye que la
        # opción no hace nada.
        clear_font_cache()
        prefs.save()

    def on_exit(self) -> None:
        if self._dirty:
            self._save_config()
        audio = self.audio
        if audio is not None:
            audio.music_volume = self._slider_music.get_current_value()
            audio.sfx_volume = self._slider_sfx.get_current_value()
        diff_val = self._dropdown_difficulty.selected_option[0]
        for d in Difficulty:
            if d.value == diff_val:
                set_difficulty(d)
                break

    #: Los eventos de pygame_gui que significan «el jugador tocó algo».
    #:
    #: AUD-154 — esta pantalla comprobaba `event.type == pygame.USEREVENT` y
    #: luego `event.user_type`. Ésa es la API de pygame_gui **0.5**. Desde 0.6
    #: cada evento tiene su propio tipo (`UI_BUTTON_PRESSED` es 32866, y
    #: `USEREVENT` es 32865), así que la condición era falsa para todos ellos y
    #: el cuerpo entero de este método no se ejecutaba nunca.
    #:
    #: Lo que eso significaba, comprobado antes de tocar nada:
    #:
    #: * los botones VOLVER y ATAJOS DE TECLADO no hacían nada —sólo la tecla
    #:   Escape salía de la pantalla, y la de atajos era **inalcanzable**—;
    #:   subtítulos, idioma, movimiento reducido y pulsar/mantener tampoco;
    #: * `_dirty` no se ponía nunca, así que `_save_config()` no corría y
    #:   **nada de lo que el jugador elegía se guardaba**: volumen, dificultad,
    #:   daltonismo, tamaño de texto. Al reiniciar volvía todo al principio.
    #:
    #: La dificultad y los volúmenes se aplicaban igualmente porque `on_exit`
    #: los lee del widget sin mirar `_dirty`, así que duraban la sesión y se
    #: perdían al cerrar. Es la peor forma de fallar: parece que funciona.
    _EVENTOS_DE_CAMBIO = (
        pygame_gui.UI_HORIZONTAL_SLIDER_MOVED,
        pygame_gui.UI_DROP_DOWN_MENU_CHANGED,
    )

    def process_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            self._gui_manager.process_events(event)
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                self._dirty = True
                if self._pulsar_boton(event.ui_element):
                    return
            elif event.type in self._EVENTOS_DE_CAMBIO:
                self._dirty = True

    def _pulsar_boton(self, elemento: object) -> bool:
        """Atiende un botón. Devuelve `True` si hay que dejar de procesar.

        Está extraído porque la lista creció a seis botones y dos de ellos
        —movimiento reducido y pulsar/mantener— se quedaron sin rama cuando se
        añadieron en AUD-126: aunque el evento hubiera llegado, esos dos
        seguirían sin hacer nada. En una cadena de `if` dentro de un bucle
        dentro de un `if` eso no se ve; en un método corto, sí.
        """
        prefs = user_settings.get()

        if self._btn_subtitles is not None and elemento == self._btn_subtitles:
            self._subtitles_on = not self._subtitles_on
            self._btn_subtitles.set_text(self._subtitles_label())
            # Se aplica al momento para que el jugador pueda comprobarlo sin
            # salir del menú.
            prefs.subtitles_enabled = self._subtitles_on
            return True

        if self._btn_language is not None and elemento == self._btn_language:
            self._toggle_language()
            prefs.language = self._idioma_actual
            return True

        if self._btn_movimiento is not None and elemento == self._btn_movimiento:
            self._movimiento_reducido = not self._movimiento_reducido
            self._btn_movimiento.set_text(self._movimiento_label())
            prefs.reduced_motion = self._movimiento_reducido
            return True

        if self._btn_mantener is not None and elemento == self._btn_mantener:
            self._mantener_pulsado = not self._mantener_pulsado
            self._btn_mantener.set_text(self._mantener_label())
            prefs.hold_to_press = self._mantener_pulsado
            return True

        if elemento == self._btn_keybindings:
            from src.engine.scenes.keybinding_scene import KeybindingScene
            self.context.scene_manager.replace(KeybindingScene(self.context))
            return True

        if elemento == self._btn_back:
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))
            return True

        return False

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))
            return

        self._gui_manager.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 30))
        self._gui_manager.draw_ui(surface)

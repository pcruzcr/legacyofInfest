from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame
import pygame_gui

from src.engine.core import settings, user_settings
from src.engine.core.difficulty import Difficulty, set_difficulty
from src.engine.core.user_settings import ESCALAS_DE_TEXTO
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.theme import clear_font_cache

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

    def on_enter(self) -> None:
        audio = self.audio
        cfg = self._load_config()
        self._gui_manager = pygame_gui.UIManager(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )
        self._ui_elements.clear()

        y = 20
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((250, y), (300, 36)),
            text="OPTIONS",
            manager=self._gui_manager,
        )
        y += 44

        self._slider_music = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((40, y), (300, 24)),
            start_value=cfg.get("music_volume", float(audio.music_volume if audio else 0.7)),
            value_range=(0.0, 1.0),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((350, y), (150, 24)),
            "MUSIC VOLUME", self._gui_manager,
        )
        y += 32

        self._slider_sfx = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((40, y), (300, 24)),
            start_value=cfg.get("sfx_volume", float(audio.sfx_volume if audio else 1.0)),
            value_range=(0.0, 1.0),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((350, y), (150, 24)),
            "SFX VOLUME", self._gui_manager,
        )
        y += 32

        self._dropdown_difficulty = pygame_gui.elements.UIDropDownMenu(
            options_list=["easy", "normal", "hard"],
            starting_option=cfg.get("difficulty", "normal"),
            relative_rect=pygame.Rect((40, y), (150, 28)),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((200, y), (150, 28)),
            "DIFFICULTY", self._gui_manager,
        )
        y += 36

        self._dropdown_cb = pygame_gui.elements.UIDropDownMenu(
            options_list=["off", "protanopia", "deuteranopia", "tritanopia"],
            starting_option=cfg.get("colorblind_mode", "off"),
            relative_rect=pygame.Rect((40, y), (150, 28)),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((200, y), (200, 28)),
            "COLORBLIND MODE", self._gui_manager,
        )
        y += 36

        # AUD-036: subtitles had no UI at all. Captions for non-speech audio are
        # implemented by engine.ui.subtitle_overlay; this is how a player turns
        # them on.
        self._subtitles_on = bool(cfg.get("subtitles_enabled", False))
        self._btn_subtitles = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((40, y), (150, 28)),
            text=self._subtitles_label(),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((200, y), (240, 28)),
            "SUBTITLES (audio captions)", self._gui_manager,
        )
        y += 36

        # F3.1: selector de idioma. Sin esto la traducción existiría y nadie
        # podría cambiarla sin editar config.json a mano.
        self._idioma_actual = cfg.get("language", "es")
        self._btn_language = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((40, y), (150, 28)),
            text=self._language_label(),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((200, y), (240, 28)),
            "IDIOMA / LANGUAGE", self._gui_manager,
        )
        y += 36

        # ── Accesibilidad (AUD-126) ────────────────────────────
        # El modo daltonismo ya estaba; faltaban las tres barreras que más
        # gente encuentran en un plataformas. Van juntas y con etiqueta propia
        # para que se encuentren: una opción de accesibilidad escondida entre
        # los ajustes de volumen no la usa quien la necesita.
        pygame_gui.elements.UILabel(
            pygame.Rect((40, y), (400, 24)),
            "ACCESIBILIDAD / ACCESSIBILITY", self._gui_manager,
        )
        y += 28

        self._dropdown_texto = pygame_gui.elements.UIDropDownMenu(
            options_list=[f"{e:g}x" for e in ESCALAS_DE_TEXTO],
            starting_option=f"{cfg.get('text_scale', 1.0):g}x",
            relative_rect=pygame.Rect((40, y), (150, 28)),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((200, y), (280, 28)),
            "TAMANO DEL TEXTO", self._gui_manager,
        )
        y += 36

        self._movimiento_reducido = bool(cfg.get("reduced_motion", False))
        self._btn_movimiento = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((40, y), (150, 28)),
            text=self._movimiento_label(),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((200, y), (320, 28)),
            "MOVIMIENTO REDUCIDO (sacudida, estelas)", self._gui_manager,
        )
        y += 36

        self._mantener_pulsado = bool(cfg.get("hold_to_press", False))
        self._btn_mantener = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((40, y), (150, 28)),
            text=self._mantener_label(),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((200, y), (320, 28)),
            "PULSAR EN VEZ DE MANTENER", self._gui_manager,
        )
        y += 40

        self._btn_keybindings = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((40, y), (200, 32)),
            text="KEY BINDINGS",
            manager=self._gui_manager,
        )
        y += 40

        self._btn_back = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((40, y), (200, 32)),
            text="BACK",
            manager=self._gui_manager,
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

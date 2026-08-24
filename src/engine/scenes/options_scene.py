"""
Module: options_scene
System: engine.scenes
Academic Unit: N/A

Los ajustes del jugador, con el kit de interfaz del propio juego.

Por qué se dejó `pygame_gui` (AUD-452)
--------------------------------------
Todo el juego se maneja con listas de teclado dibujadas por
`engine.ui.widgets`: el título, los archivos de partida, los logros, el
bestiario, la tienda y —lo que más duele en la comparación— **Controles**,
que está justo al lado en este mismo menú. Sólo esta pantalla usaba
`pygame_gui`, con deslizadores y desplegables de ratón, su propia tipografía
y su propio tema.

No era un problema de estilo sino de manejo: en Controles te mueves con las
flechas y confirmas con Enter; aquí había que arrastrar un deslizador y
desplegar una lista. En un juego que se juega con teclado, un desplegable con
foco de ratón es un cuerpo extraño.

La alternativa era escribir deslizador, desplegable e interruptor propios. Se
descartó porque replicaría widgets de ratón dentro de un menú de teclado:
seguirían conviviendo dos formas de manejarse. El patrón que se adopta es el
de consola —una fila por ajuste, ←→ cambia el valor, el valor se lee a la
derecha—, que usa lo que ya existe (`MenuList` y su campo `trailing`) y hereda
gratis dos cosas: el desplazamiento de AUD-446 —que cierra BUG-002, porque
once filas no caben— y la escala de accesibilidad, porque el kit dibuja con
`theme.font()`.

Lo que NO se pierde al migrar
-----------------------------
Los once ajustes siguen estando, y hay una prueba por cada uno. También el
aprendizaje de AUD-154: allí se descubrió que los eventos de `pygame_gui` no
llegaban y **nada de lo que el jugador elegía se guardaba**. Aquí no hay
eventos de terceros que puedan cambiar de API: cada cambio escribe en
`user_settings` en el acto.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import user_settings
from src.engine.core.difficulty import Difficulty, set_difficulty
from src.engine.core.events import Events
from src.engine.core.user_settings import COLORBLIND_MODES, ESCALAS_DE_TEXTO
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.theme import clear_font_cache
from src.engine.ui.widgets import (
    MenuItem,
    MenuList,
    draw_key_hints,
    draw_screen,
    handle_menu_navigation,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


#: Pasos del volumen. Discreto y no continuo a propósito: con el teclado, un
#: deslizador continuo obliga a mantener la flecha y adivinar dónde parar.
#: Once escalones dan un 0-100 % que se recorre en once pulsaciones.
_PASOS_DE_VOLUMEN: tuple[float, ...] = tuple(i / 10 for i in range(11))

_SI_NO: tuple[bool, ...] = (False, True)

#: Nombres que se muestran, cada uno en su propio idioma — viene de antes de
#: esta migración y sigue valiendo: un selector que dijera «Español / Inglés»
#: en inglés es exactamente lo que no ayuda a quien no sabe inglés.
_NOMBRES_IDIOMA = {"es": "ESPAÑOL", "en": "ENGLISH"}

_NOMBRES_DIFICULTAD = {"easy": "FÁCIL", "normal": "NORMAL", "hard": "DIFÍCIL"}

_NOMBRES_DALTONISMO = {
    "off": "NINGUNO",
    "protanopia": "PROTANOPIA",
    "deuteranopia": "DEUTERANOPIA",
    "tritanopia": "TRITANOPIA",
}


@dataclass
class _Ajuste:
    """Una fila de la pantalla: qué se ajusta y entre qué valores.

    Se describen como datos y no como código porque así la lista de ajustes se
    lee de un vistazo y añadir uno es una línea. La versión con `pygame_gui`
    necesitaba doce líneas por ajuste —construir el widget, colocarlo, poner
    la etiqueta, leerlo al guardar— repartidas por tres métodos distintos, y
    ahí es donde se pierde uno.
    """

    clave: str
    etiqueta: str
    valores: tuple[Any, ...]
    #: Cómo se enseña el valor. Por defecto, tal cual en mayúsculas.
    mostrar: Callable[[Any], str] = field(default=lambda v: str(v).upper())

    def indice_de(self, valor: Any) -> int:
        """Dónde cae el valor actual, o 0 si no está entre los posibles.

        Un `config.json` editado a mano puede traer cualquier cosa; caer al
        primero es preferible a reventar la pantalla de ajustes, que es
        justamente adonde iría alguien a arreglar el problema.
        """
        try:
            return self.valores.index(valor)
        except ValueError:
            return 0


def _porcentaje(v: Any) -> str:
    return f"{float(v) * 100:.0f} %"


def _si_no(v: Any) -> str:
    return "SÍ" if v else "NO"


class OptionsScene(BaseScene):
    """Los ajustes, como una lista de teclado igual que el resto del juego."""

    #: Cuántas filas se ven a la vez. Once ajustes más dos acciones no caben en
    #: la pantalla, y recortar ajustes para que quepan sería resolver el
    #: problema equivocado (BUG-002).
    FILAS_VISIBLES = 5

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self.ajustes: list[_Ajuste] = [
            _Ajuste("music_volume", "VOLUMEN DE MÚSICA",
                    _PASOS_DE_VOLUMEN, _porcentaje),
            _Ajuste("sfx_volume", "VOLUMEN DE EFECTOS",
                    _PASOS_DE_VOLUMEN, _porcentaje),
            _Ajuste("difficulty", "DIFICULTAD",
                    ("easy", "normal", "hard"),
                    lambda v: _NOMBRES_DIFICULTAD.get(str(v), str(v).upper())),
            _Ajuste("colorblind_mode", "MODO DALTÓNICO",
                    COLORBLIND_MODES,
                    lambda v: _NOMBRES_DALTONISMO.get(str(v), str(v).upper())),
            _Ajuste("subtitles_enabled", "SUBTÍTULOS DE SONIDO", _SI_NO, _si_no),
            _Ajuste("language", "IDIOMA", ("es", "en"),
                    lambda v: _NOMBRES_IDIOMA.get(str(v), str(v).upper())),
            # AUD-126 — las tres barreras que más gente encuentran en un
            # plataformas van juntas y detrás del daltonismo, para que se
            # encuentren: una opción de accesibilidad escondida entre los
            # ajustes de volumen no la usa quien la necesita.
            _Ajuste("text_scale", "TAMAÑO DEL TEXTO",
                    ESCALAS_DE_TEXTO, lambda v: f"{float(v):g}x"),
            _Ajuste("reduced_motion", "MOVIMIENTO REDUCIDO", _SI_NO, _si_no),
            _Ajuste("hold_to_press", "MANTENER PULSADO", _SI_NO, _si_no),
            _Ajuste("contorno_de_enemigos", "CONTORNO DE ENEMIGOS",
                    _SI_NO, _si_no),
        ]
        self._menu = MenuList()
        self._menu.visible_rows = self.FILAS_VISIBLES
        self._construir_filas()

    # ── construcción de la lista ───────────────────────────────

    def _construir_filas(self) -> None:
        filas = [
            MenuItem(a.etiqueta, value=a.clave,
                     trailing=a.mostrar(self.valor_de(a.clave)))
            for a in self.ajustes
        ]
        filas.append(MenuItem("CONTROLES", value="CONTROLES",
                              hint="Cambiar las teclas"))
        filas.append(MenuItem("VOLVER", value="VOLVER"))
        self._menu.items = filas
        self._menu.ensure_valid()

    def _refrescar_fila(self, clave: str) -> None:
        ajuste = self._ajuste(clave)
        for item in self._menu.items:
            if item.value == clave and ajuste is not None:
                item.trailing = ajuste.mostrar(self.valor_de(clave))
                return

    def _ajuste(self, clave: str) -> _Ajuste | None:
        for a in self.ajustes:
            if a.clave == clave:
                return a
        return None

    # ── leer y escribir preferencias ───────────────────────────

    def valor_de(self, clave: str) -> Any:
        """El valor vigente de un ajuste, leído de las preferencias vivas."""
        return getattr(user_settings.get(), clave)

    def cambiar_valor(self, direccion: int) -> None:
        """Mueve el ajuste enfocado un paso, y lo aplica en el acto.

        Se guarda al momento y no al salir. AUD-154 encontró esta pantalla
        guardando **nada** porque un `if` sobre una API vieja de `pygame_gui`
        nunca se cumplía, y el jugador no tenía forma de saberlo: los cambios
        duraban la sesión y se perdían al cerrar. Escribiendo aquí no hay
        ningún camino en el que el ajuste se quede sin aplicar.
        """
        item = self._menu.current
        if item is None:
            return
        ajuste = self._ajuste(str(item.value))
        if ajuste is None:
            return
        actual = ajuste.indice_de(self.valor_de(ajuste.clave))
        nuevo = ajuste.valores[(actual + direccion) % len(ajuste.valores)]
        self._aplicar(ajuste.clave, nuevo)
        self._refrescar_fila(ajuste.clave)
        self.context.event_bus.emit(Events.SFX_MENU_HOVER)

    def _aplicar(self, clave: str, valor: Any) -> None:
        """Escribe el ajuste, lo persiste y hace lo que tenga efecto inmediato."""
        prefs = user_settings.get()
        setattr(prefs, clave, valor)

        audio = self.audio
        if clave == "music_volume" and audio is not None:
            audio.music_volume = float(valor)
        elif clave == "sfx_volume" and audio is not None:
            audio.sfx_volume = float(valor)
        elif clave == "difficulty":
            for d in Difficulty:
                if d.value == valor:
                    set_difficulty(d)
                    break
        elif clave == "language":
            from src.engine.core.i18n import set_idioma

            set_idioma(str(valor))
        elif clave == "text_scale":
            # Cambiar la escala invalida toda la caché de fuentes: las que hay
            # dentro se crearon con el tamaño anterior y seguirían saliendo
            # pequeñas hasta reiniciar, que es cuando el jugador concluye que
            # la opción no hace nada.
            clear_font_cache()
            self._construir_filas()
        prefs.save()

    # ── ciclo de vida ──────────────────────────────────────────

    def on_enter(self) -> None:
        self._menu.index = 0
        self._construir_filas()
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self._menu.update(dt)
        im = self.input
        if im is None:
            return
        # Arriba/abajo, confirmar y cancelar salen del kit: una sola
        # implementación para todas las pantallas, y así rebindear una tecla en
        # Controles surte efecto en todas a la vez.
        handle_menu_navigation(
            self._menu, im,
            on_confirm=self._activar, on_cancel=lambda: self._volver(),
        )
        # Izquierda/derecha es lo propio de esta pantalla: cambiar el valor de
        # la fila enfocada sin salir de ella.
        if im.is_action_just_pressed(Action.MOVE_RIGHT):
            self.cambiar_valor(+1)
        elif im.is_action_just_pressed(Action.MOVE_LEFT):
            self.cambiar_valor(-1)

    def _activar(self, item: MenuItem | None = None) -> None:
        item = item or self._menu.current
        if item is None:
            return
        if item.value == "CONTROLES":
            from src.engine.scenes.keybinding_scene import KeybindingScene

            self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)
            self.context.scene_manager.replace(KeybindingScene(self.context))
        elif item.value == "VOLVER":
            self._volver()
        else:
            # Confirmar sobre un ajuste avanza, como la flecha derecha: es lo
            # que hace todo el mundo antes de leer que se cambia con ←→.
            self.cambiar_valor(+1)

    def _volver(self) -> None:
        from src.engine.scenes.title_scene import TitleScene

        self.context.event_bus.emit(Events.SFX_MENU_CANCEL)
        self.context.scene_manager.replace(TitleScene(self.context))

    # ── dibujo ─────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        top = draw_screen(surface, "OPCIONES", "Ajustes del jugador")
        fin = self._menu.draw(surface, 40, top + 8,
                              surface.get_width() - 80)
        self._menu.draw_hint(surface, fin + 8)
        draw_key_hints(surface, [
            ("↑↓", "Elegir"),
            ("←→", "Cambiar"),
            ("Enter", "Aceptar"),
            ("Esc", "Volver"),
        ])

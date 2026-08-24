from __future__ import annotations

import logging

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.ui.text_panel import FlujoDeTexto, dibuja_panel
from src.engine.ui.theme import Theme, escalar, font

logger = logging.getLogger(__name__)

#: Máximo de líneas del cuadro. Con el ajuste por píxeles el límite ya no
#: es cuántos «caracteres» caben sino cuántas líneas se quieren leer sin
#: que el aviso tape media pantalla.
_MAX_LINES = 4


class MessageBox:
    """Typewriter message box with auto-dismiss and message queue.

    AUD-611 — el cuadro ahora se **adapta al texto**: ajuste de línea por
    píxeles con la fuente real (no «58 caracteres», que con una tipografía
    proporcional y la escala de accesibilidad no significan nada), alto del
    panel según las líneas resultantes, y el aspecto del tema — panel
    redondeado con sombra en vez de un rectángulo negro plano.

    Y la optimización que lo hace barato: el bloque se renderiza UNA vez
    por mensaje (`FlujoDeTexto`) y la máquina de escribir recorta
    superficies ya hechas. Antes cada carácter re-renderizaba la cadena
    creciente — treinta `font.render` por segundo para pintar cuatro
    líneas fijas.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._text: str = ""
        self._full_text: str = ""
        self._visible: bool = False
        self._char_timer: float = 0.0
        self._display_duration: float = 0.0
        self._elapsed: float = 0.0
        self._chars_per_second: float = 30.0
        self._dismiss_on_confirm: bool = False
        self._queue: list[dict[str, object]] = []
        self._destroyed: bool = False

        # AUD-451 — por `theme.font()`, que aplica la escala de accesibilidad
        # y ya cae a la tipografía de pygame si `game.ttf` falta. Construida a
        # pelo, subir el texto en Opciones no le llegaba: es el cuadro donde se
        # leen los diálogos y los avisos del escenario.
        self._font: pygame.font.Font = font(Theme.FONT_SMALL)

        if hasattr(settings, "ASSETS_DIR"):
            try:
                from src.engine.utils.asset_loader import AssetLoader
                self._arrow = AssetLoader.load_image(
                    settings.ASSETS_DIR / "ui" / "message_arrow.png", size=(5, 7),
                )
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("message_box: failed to load message_arrow.png")
                self._arrow = None
        else:
            self._arrow = None
        self._arrow_timer: float = 0.0

        #: AUD-611 — el bloque envuelto y renderizado una vez por mensaje.
        self._flujo = FlujoDeTexto()

        self._event_bus.subscribe(Events.SHOW_MESSAGE, self._on_show_message)
        self._event_bus.subscribe(Events.HIDE_MESSAGE, self._on_hide_message)

    def destroy(self) -> None:
        if self._destroyed:
            return
        self._destroyed = True
        self._event_bus.unsubscribe(Events.SHOW_MESSAGE, self._on_show_message)
        self._event_bus.unsubscribe(Events.HIDE_MESSAGE, self._on_hide_message)

    def _on_show_message(self, **data: object) -> None:
        if self._destroyed:
            return
        if self._visible:
            self._queue.append(dict(data))
            return
        self._show(data)

    def _show(self, data: dict[str, object]) -> None:
        self._full_text = str(data.get("text", ""))
        duration = data.get("duration", 3.0)
        self._display_duration = float(duration) if isinstance(duration, (int, float)) else 3.0
        self._dismiss_on_confirm = self._display_duration <= 0
        self._text = ""
        self._char_timer = 0.0
        self._elapsed = 0.0
        self._arrow_timer = 0.0
        # AUD-611 — envolver y renderizar UNA vez aquí, no en cada carácter.
        self._flujo.preparar(
            self._full_text, self._font, self._ancho_util(),
            separacion=3, color=(255, 255, 255),
        )
        self._recorta_a_max_lineas()
        self._visible = True

    def _ancho_util(self) -> int:
        """Ancho disponible para el texto dentro del panel."""
        return max(80, settings.INTERNAL_WIDTH
                   - 2 * (_MARGEN + _PAD_X + _FLECHA_HUECO))

    def _recorta_a_max_lineas(self) -> None:
        """Si el texto envuelto pide más de `_MAX_LINES`, trunca el texto."""
        while len(self._flujo.lineas) > _MAX_LINES and self._full_text:
            self._full_text = self._full_text[:-8].rstrip() + "…"
            self._flujo.preparar(
                self._full_text, self._font, self._ancho_util(),
                separacion=3, color=(255, 255, 255),
            )

    def _on_hide_message(self, **data: object) -> None:
        if self._destroyed:
            return
        self._visible = False
        self._text = ""
        self._full_text = ""

    def hide(self) -> None:
        self._visible = False
        self._text = ""
        self._full_text = ""
        self._event_bus.emit(Events.HIDE_MESSAGE)

    def update(self, dt: float) -> None:
        if not self._visible:
            if self._queue:
                self._show(self._queue.pop(0))
            return

        # Typewriter effect — el tope es la longitud del texto completo.
        # Se lee de `_full_text` y no del bloque renderizado porque las
        # pruebas (y quien herede) pueden fijar el texto directamente.
        total = len(self._full_text)
        if len(self._text) < total:
            self._char_timer += dt
            chars_to_add = int(self._char_timer * self._chars_per_second)
            chars_to_add = min(chars_to_add, total)
            self._text = self._full_text[:chars_to_add]
        elif not self._dismiss_on_confirm:
            self._elapsed += dt
            if self._elapsed >= self._display_duration:
                self._visible = False

        if self._dismiss_on_confirm and len(self._text) >= total:
            self._arrow_timer += dt

    def caja_rect(self) -> pygame.Rect:
        """La banda reservada al cuadro, derivada de la maqueta — AUD-453.

        AUD-611 — el alto ahora depende del texto: mínimo el que la maqueta
        siempre reserva (y que el guardián de interfaz exige), máximo el que
        pidan las líneas envueltas. El ancho sigue siendo todo el interior;
        el PANEL visible, centrado dentro, sí se ajusta al contenido.
        """
        alto_contenido = 0
        if self._visible and not self._flujo.vacio:
            _, alto = self._flujo.tamano()
            alto_contenido = alto + 2 * _PAD_Y
            if self._dismiss_on_confirm:
                alto_contenido += _FLECHA_ALTO
        alto_min = max(escalar(56), int(settings.INTERNAL_HEIGHT * 0.085))
        return pygame.Rect(0, escalar(64), settings.INTERNAL_WIDTH,
                           max(alto_min, alto_contenido))

    def rect_del_panel(self) -> pygame.Rect:
        """El panel visible, centrado en la banda y del tamaño del texto.

        Público porque las pruebas fijan aquí el contrato de adaptación:
        ni un píxel más alto que sus líneas, ni más ancho que hace falta
        hasta el mínimo de legibilidad. El mínimo de banda lo respeta
        `caja_rect` (el hueco reservado); el PANEL se ajusta al contenido,
        que es lo que lo hace leerse como burbuja y no como franja.
        """
        banda = self.caja_rect()
        ancho_texto, alto_texto = self._flujo.tamano()
        ancho_min = max(240, banda.width // 3)
        ancho = min(banda.width - 2 * _MARGEN,
                    max(ancho_min, ancho_texto + 2 * _PAD_X))
        alto = alto_texto + 2 * _PAD_Y
        if self._dismiss_on_confirm:
            alto += _FLECHA_ALTO
        return pygame.Rect((banda.width - ancho) // 2, banda.y, ancho, alto)

    def draw(self, surface: pygame.Surface) -> None:
        if not self._visible or not self._text:
            return

        # AUD-611 — preparación perezosa: `_show` ya la hizo, pero quien
        # fije `_full_text` a mano (pruebas, entregas) no se queda sin
        # bloque. Con texto igual, `preparar` es una comparación de clave.
        if self._flujo.caracteres_totales() != len(self._full_text):
            self._flujo.preparar(
                self._full_text, self._font, self._ancho_util(),
                separacion=3, color=(255, 255, 255),
            )
            self._recorta_a_max_lineas()

        panel = self.rect_del_panel()
        dibuja_panel(surface, panel)

        # Texto ya renderizado: sólo blit/recorte por fotograma.
        self._flujo.dibujar(
            surface,
            (panel.x + _PAD_X, panel.y + _PAD_Y),
            caracteres=len(self._text),
        )

        # Arrow indicator when waiting for confirm
        if self._dismiss_on_confirm and len(self._text) >= len(self._full_text):
            arrow_visible = int(self._arrow_timer * 4) % 2 == 0
            if arrow_visible and self._arrow:
                ax = panel.right - _PAD_X - self._arrow.get_width()
                ay = panel.bottom - _PAD_Y - self._arrow.get_height() + 2
                surface.blit(self._arrow, (ax, ay))

    @property
    def is_visible(self) -> bool:
        return self._visible

    @property
    def is_dismiss_on_confirm(self) -> bool:
        return self._dismiss_on_confirm


#: Márgenes y relleno del panel (px a escala 1,0).
_MARGEN = 24
_PAD_X = 14
_PAD_Y = 10
#: Hueco reservado a la flecha de «pulsa para continuar», a la derecha.
_FLECHA_HUECO = 16
_FLECHA_ALTO = 12

"""
Module: hud
System: engine.ui
Description: Heads-Up Display showing hearts (health), timer, and stage info.
Uses sprite-based hearts from assets/ui/ with font fallback.
"""
from __future__ import annotations

import logging
import math
from typing import cast

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.ui.theme import ANCHO_DE_DISENO as theme_ancho_de_diseno
from src.engine.ui.theme import ESCALA_DE_INTERFAZ, escalar, font
from src.engine.utils.asset_loader import AssetLoader

logger = logging.getLogger(__name__)

#: AUD-453 — la escala vive en `theme`, que es el módulo de los tokens de
#: diseño. Estaba aquí desde AUD-451, y eso obligaba al cuadro de mensajes, a
#: la franja del escenario y a los subtítulos a importar del HUD para
#: colocarse: una dependencia que no significa nada. Se reexporta con el
#: nombre de antes porque hay pruebas que lo nombran.
ANCHO_DE_DISENO = theme_ancho_de_diseno
ESCALA_DEL_HUD: float = ESCALA_DE_INTERFAZ

_e = escalar


def _rect_escalado(x: int, y: int, w: int, h: int) -> pygame.Rect:
    """Una región de la maqueta original, a escala."""
    return pygame.Rect(_e(x), _e(y), _e(w), _e(h))


def _heart_slot_state(health: float, slot: int) -> str:
    v = max(0.0, min(1.0, health - slot))
    if v >= 1.0:
        return "full"
    if v >= 0.75:
        return "three_quarter"
    if v >= 0.50:
        return "half"
    if v >= 0.25:
        return "quarter"
    return "empty"


_PORTRAIT_STATES = ("normal", "hurt", "critical", "dead")


class HUD:
    """Heads-up display: hearts, timer, portrait."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._health: float = settings.PLAYER_MAX_HEALTH
        self._max_health: float = settings.PLAYER_MAX_HEALTH
        self._timer: float = 0.0
        self._timer_running: bool = False
        self._time_limit: int = 0
        self._is_countdown: bool = False
        self._timer_paused: bool = False
        self._hurt_portrait_timer: float = 0.0
        self._destroyed: bool = False
        self._save_notify_timer: float = 0.0
        #: AUD-281 — lo que queda del rebote del contador de monedas.
        self._pulso_timer: float = 0.0

        # Portrait frame (34x34 with 1px border, inner sprite at 3,3)
        self._portrait_frame_rect = _rect_escalado(2, 2, 34, 34)
        self._portrait_sprite_rect = _rect_escalado(3, 3, 32, 32)
        self._portrait_fill = None
        self._portrait_edges: dict[str, pygame.Surface] = {}
        self._timer_fill = None
        self._timer_edges: dict[str, pygame.Surface] = {}
        # Load 9-slice frame from hud_frame.png, pre-scale all variants once
        try:
            raw_frame = AssetLoader.load_image(settings.ASSETS_DIR / "ui" / "hud_frame.png")
            fw, fh = raw_frame.get_size()
            if fw >= 6 and fh >= 6:
                c = 2  # corner size, en la maqueta
                esquinas = {
                    "tl": raw_frame.subsurface((0, 0, c, c)),
                    "tr": raw_frame.subsurface((fw - c, 0, c, c)),
                    "bl": raw_frame.subsurface((0, fh - c, c, c)),
                    "br": raw_frame.subsurface((fw - c, fh - c, c, c)),
                }
                src_edges = {
                    "top": raw_frame.subsurface((c, 0, fw - 2 * c, c)),
                    "bottom": raw_frame.subsurface((c, fh - c, fw - 2 * c, c)),
                    "left": raw_frame.subsurface((0, c, c, fh - 2 * c)),
                    "right": raw_frame.subsurface((fw - c, c, c, fh - 2 * c)),
                }
                # AUD-459 — las esquinas y el grosor del borde iban a 2 px
                # dentro de marcos de 80 px: el 9-slice escalaba el relleno y
                # no la orla. Se escalan al mismo factor que la maqueta y los
                # bordes se pre-escalan contra ese grosor (`ce`), no contra 2.
                ce = _e(c)
                self._frame_corners = {
                    k: pygame.transform.scale(v, (ce, ce))
                    for k, v in esquinas.items()
                }
                self._frame_edges = src_edges
                src_fill = raw_frame.subsurface((c, c, fw - 2 * c, fh - 2 * c))
                self._frame_fill = src_fill
                # Pre-scale for portrait frame (34x34)
                pr = self._portrait_frame_rect
                self._portrait_fill = pygame.transform.scale(src_fill, (pr.width, pr.height))
                self._portrait_edges = {
                    "top": pygame.transform.scale(src_edges["top"], (pr.width - 2 * ce, ce)),
                    "bottom": pygame.transform.scale(src_edges["bottom"], (pr.width - 2 * ce, ce)),
                    "left": pygame.transform.scale(src_edges["left"], (ce, pr.height - 2 * ce)),
                    "right": pygame.transform.scale(src_edges["right"], (ce, pr.height - 2 * ce)),
                }
                # Timer background pre-scaling deferred until _timer_bg_rect is set
            else:
                self._frame_corners = {}
                self._frame_edges = {}
                self._frame_fill = None
        except (pygame.error, FileNotFoundError, PermissionError):
            logger.warning("hud: failed to load hud_frame.png")
            self._frame_corners = {}
            self._frame_edges = {}
            self._frame_fill = None

        self._hearts_x: int = _e(38)
        self._hearts_y: int = _e(6)
        self._heart_spacing: int = _e(16)
        # AUD-219 — marcador de puntos y monedas.
        #
        # Va entre los corazones (38..118) y el marco del cronómetro (258..320)
        # porque es el único hueco libre de la franja superior. Se declara como
        # región en `09_HUD_SPEC.md` §2.1: el doc es contrato, y una prueba
        # comprueba que lo que se dibuja cabe en lo que el doc promete.
        self._score_region = _rect_escalado(124, 2, 128, 14)
        self._score: int = 0
        self._coins: int = 0
        # Timer frame (reuse hud_frame.png 9-slice at timer size 90x16)
        self._timer_bg_rect = _rect_escalado(258, 1, 62, 16)
        # Pre-scale timer background once (deferred from frame load block)
        self._timer_fill = (
            pygame.transform.scale(
                self._frame_fill,
                (self._timer_bg_rect.width, self._timer_bg_rect.height),
            )
            if isinstance(self._frame_fill, pygame.Surface)
            else None
        )
        if self._frame_edges:
            tr = self._timer_bg_rect
            # AUD-459 — grosor del borde a escala, igual que en el retrato.
            ce = _e(2)
            self._timer_edges = {
                "top": pygame.transform.scale(self._frame_edges["top"], (tr.width - 2 * ce, ce)),
                "bottom": pygame.transform.scale(self._frame_edges["bottom"], (tr.width - 2 * ce, ce)),
                "left": pygame.transform.scale(self._frame_edges["left"], (ce, tr.height - 2 * ce)),
                "right": pygame.transform.scale(self._frame_edges["right"], (ce, tr.height - 2 * ce)),
            }
        self._timer_rect = _rect_escalado(288, 2, 32, 14)
        self._timer_label_rect = _rect_escalado(260, 2, 26, 12)
        self._timer_flash_timer: float = 0.0
        self._timer_flash_on: bool = False
        # Load timer font (TTF preferred for readability)
        # AUD-455 — iba por fuera de `theme.font()`, así que el 12 nunca se
        # escalaba ni se le aplicaba la preferencia de accesibilidad: a 800×600
        # el reloj se veía a 12 px reales, un tercio del que debía (AUD-451
        # escaló el marcador y el marco del reloj, no la cifra que va dentro).
        self._timer_digit_font: pygame.font.Font = font(_e(12))

        # Heart damage flash state
        self._heart_flash_timer: float = 0.0
        self._heart_flash_old_state: str = ""
        self._heart_flash_slot: int = -1

        # Heart heal animation state (right→left, sequential multi-heart)
        self._heal_anim_timer: float = 0.0
        self._heal_anim_slot_index: int = 0
        self._heal_anim_slots: list[int] = []
        self._heal_anim_active: bool = False
        self._sparkle_frames: list[pygame.Surface] = []
        self._sparkle_frame: int = 0

        # Load heart sprites
        self._heart_sprites: dict[str, pygame.Surface] = {}
        for state in ("full", "three_quarter", "half", "quarter", "empty"):
            path = settings.ASSETS_DIR / "ui" / f"heart_{state}.png"
            try:
                surf = AssetLoader.load_image(path)
                # AUD-459 — los rects estaban a ×escala (AUD-451) y el sprite
                # a pelo: un corazón de 14×8 px dentro de una hilera espaciada
                # a 40 px. El sprite se escala igual que la maqueta.
                self._heart_sprites[state] = pygame.transform.scale(
                    surf, (_e(surf.get_width()), _e(surf.get_height())),
                )
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("hud: failed to load heart sprite %s", path)
                self._heart_sprites[state] = pygame.Surface((_e(14), _e(8)))

        try:
            sparkle_path = settings.ASSETS_DIR / "ui" / "heart_sparkle.png"
            self._sparkle_frames = [
                pygame.transform.scale(f, (_e(8), _e(8)))
                for f in AssetLoader.load_sprite_sheet(sparkle_path, 8, 8)
            ]
        except (pygame.error, FileNotFoundError, PermissionError):
            logger.warning("hud: failed to load heart_sparkle.png")
            self._sparkle_frames = []

        # Load portrait sprites
        self._portraits: dict[str, pygame.Surface] = {}
        for state in _PORTRAIT_STATES:
            path = settings.ASSETS_DIR / "ui" / f"portrait_{state}.png"
            try:
                # AUD-459 — el retrato se subía a 32×32 a pelo; el marco
                # media 80×80. Misma lección que los corazones.
                surf = AssetLoader.load_image(path, size=(_e(32), _e(32)))
                self._portraits[state] = surf
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("hud: failed to load portrait %s", state)
        self._current_portrait_state: str = "normal"

        # Boss HUD state
        self._boss_name: str = ""
        self._boss_health: float = 0.0
        self._boss_max_health: float = 0.0
        self._boss_phase_count: int = 0
        self._boss_active: bool = False

        # Combo state
        self._combo_count: int = 0
        self._special_current: float = 0.0
        #: AUD-141 — estamina. En 0 la barra no se dibuja.
        self._estamina_actual: float = 0.0
        self._estamina_max: float = 0.0
        #: AUD-260 — tiempo bala. Negativo = el escenario no lo pide.
        self._bala_fraccion: float = -1.0
        self._bala_activo: bool = False
        #: AUD-274 — franja del Boss Rush. Progreso vacío = modo apagado, que
        #: es el caso de la partida normal.
        self._rush_progreso: str = ""
        self._rush_jefe: str = ""
        self._rush_puntos: int = 0
        self._rush_golpes: int = 0
        self._special_max: float = 100.0

        # AUD-451 — por `theme.font()` y a la escala de la maqueta.
        #
        # Era `pygame.font.Font(None, 12)`: 6 px de tinta medidos, la
        # tipografía por defecto de pygame en vez de la del juego, y sin pasar
        # por `escalar_texto`, así que subir el texto en Opciones no le
        # llegaba. El 12 se escala como el resto de la maqueta porque es un
        # número de la misma maqueta: dejarlo fijo habría agrandado el marco y
        # no lo que va dentro.
        self._font = font(_e(12))

        self._event_bus.subscribe(Events.PLAYER_DAMAGED, self._on_player_damaged)
        self._event_bus.subscribe(Events.PLAYER_HEALED, self._on_player_healed)
        self._event_bus.subscribe(Events.PLAYER_DIED, self._on_player_died)
        self._event_bus.subscribe(Events.BOSS_PHASE_CHANGED, self._on_boss_phase_changed)
        self._event_bus.subscribe(Events.CHECKPOINT_REACHED, self._on_checkpoint_reached)
        self._event_bus.subscribe(Events.STAGE_COMPLETE, self._on_stage_complete)

    #
    # destroy(): MUST be called before discarding this HUD instance.
    # Removes EventBus subscriptions to prevent orphan callbacks
    # from accumulating across respawns / scene transitions.
    # Idempotent — safe to call multiple times.
    #
    def destroy(self) -> None:
        """Desuscribe todos los eventos del EventBus.
        Obligatorio llamar antes de descartar el HUD.
        Idempotente: llama varias veces sin efecto secundario.
        """
        if self._destroyed:
            return
        self._destroyed = True
        self._event_bus.unsubscribe(Events.PLAYER_DAMAGED, self._on_player_damaged)
        self._event_bus.unsubscribe(Events.PLAYER_HEALED, self._on_player_healed)
        self._event_bus.unsubscribe(Events.PLAYER_DIED, self._on_player_died)
        self._event_bus.unsubscribe(Events.BOSS_PHASE_CHANGED, self._on_boss_phase_changed)
        self._event_bus.unsubscribe(Events.CHECKPOINT_REACHED, self._on_checkpoint_reached)
        self._event_bus.unsubscribe(Events.STAGE_COMPLETE, self._on_stage_complete)

    def _on_player_damaged(self, **data: object) -> None:
        if self._destroyed:
            return
        old_health = self._health
        amount = cast(float, data.get("amount", 1.0))
        self._health = max(0.0, self._health - amount)
        self._hurt_portrait_timer = 0.8
        # Heart flash: track which slot decreased
        for slot in range(int(self._max_health)):
            old_state = _heart_slot_state(old_health, slot)
            new_state = _heart_slot_state(self._health, slot)
            if old_state != new_state:
                self._heart_flash_timer = 0.6
                self._heart_flash_old_state = old_state
                self._heart_flash_slot = slot
                break

    def _on_player_healed(self, **data: object) -> None:
        if self._destroyed:
            return
        old_health = self._health
        amount = cast(float, data.get("amount", 1.0))
        self._health = min(self._max_health, self._health + amount)
        # Heal animation: scan right→left, collect ALL changed slots
        changed_slots: list[int] = []
        for slot in range(int(self._max_health) - 1, -1, -1):
            old_state = _heart_slot_state(old_health, slot)
            new_state = _heart_slot_state(self._health, slot)
            if old_state != new_state:
                changed_slots.append(slot)
        if changed_slots:
            self._heal_anim_timer = 0.0
            self._heal_anim_slot_index = 0
            self._heal_anim_slots = changed_slots
            self._heal_anim_active = True

    def _on_player_died(self, **data: object) -> None:
        if self._destroyed:
            return
        self._health = 0.0
        self._timer_running = False
        self._timer_paused = False

    def timer_rect(self) -> pygame.Rect:
        """El marco del cronómetro. Lo consulta la prueba de maqueta."""
        return pygame.Rect(self._timer_bg_rect)

    def heart_row_rect(self) -> pygame.Rect:
        """Lo que ocupa la fila de corazones, a la escala actual."""
        alto = _e(8)
        ancho = max(1, self.ranuras_de_corazon) * self._heart_spacing
        return pygame.Rect(self._hearts_x, self._hearts_y, ancho, alto)

    def regiones(self) -> dict[str, pygame.Rect]:
        """Las cuatro zonas de la franja superior — AUD-451.

        Existe para que una prueba pueda comprobar de una vez que ninguna se
        sale de la pantalla ni pisa a otra. Escalar una maqueta sin comprobar
        eso sólo cambia un defecto por otro: lo que antes era ilegible por
        pequeño pasaría a ser ilegible por solaparse.
        """
        return {
            "retrato": pygame.Rect(self._portrait_frame_rect),
            "corazones": self.heart_row_rect(),
            "marcador": pygame.Rect(self._score_region),
            "cronometro": self.timer_rect(),
        }

    @property
    def ranuras_de_corazon(self) -> int:
        """Cuántos corazones dibuja el marcador ahora mismo — AUD-439."""
        return max(1, int(self._max_health))

    def set_salud_maxima(self, maxima: float) -> None:
        """La vida máxima **real** del jugador, reliquias y árbol incluidos.

        AUD-439 — `_max_health` se fijaba una vez en `__init__` desde
        `settings.PLAYER_MAX_HEALTH` y no había forma de cambiarlo, así que el
        marcador dibujaba cinco corazones aunque el jugador tuviera diez.
        Comprar el casco de la tienda no producía ningún cambio en pantalla.

        Lo empuja el escenario cada fotograma, igual que la puntuación o la
        estamina, y por lo mismo: es un valor del jugador, no del marcador, y
        el que manda es el jugador. No se hace por eventos porque el máximo no
        cambia con un suceso puntual sino con lo que llevas encima.

        Se acota por abajo a un corazón: `max_health` sale de sumar
        bonificaciones y una partida editada a mano puede traer un cero o un
        negativo. Un marcador sin ranuras no dice nada y además rompería el
        recorrido de dibujo.
        """
        self._max_health = max(1.0, float(maxima))
        # Si el tope baja —se quita una reliquia— la vida no puede quedarse por
        # encima: se verían corazones fuera del marcador.
        self._health = min(self._health, self._max_health)

    def set_boss_hud(self, name: str, health: float, max_health: float, phase: int, phase_count: int) -> None:
        self._boss_name = name
        self._boss_health = health
        self._boss_max_health = max_health
        self._boss_phase_count = phase_count
        self._boss_active = True

    def clear_boss_hud(self) -> None:
        self._boss_active = False
        self._boss_name = ""

    def set_combo_count(self, count: int) -> None:
        self._combo_count = max(0, count)

    def _on_boss_phase_changed(self, **data: object) -> None:
        if self._destroyed:
            return
        self._boss_name = str(data.get("boss_name", ""))
        self._boss_phase_count = cast(int, data.get("phase_count", 1))

    def _on_checkpoint_reached(self, **data: object) -> None:
        if self._destroyed:
            return
        # Timer keeps running through checkpoints — no op

    def _on_stage_complete(self, **data: object) -> None:
        if self._destroyed:
            return
        self.stop_timer()

    def trigger_save_notification(self) -> None:
        if self._destroyed:
            return
        self._save_notify_timer = 2.0

    def start_timer(self, time_limit: int = 0) -> None:
        self._time_limit = time_limit
        self._is_countdown = time_limit > 0
        self._timer = float(time_limit) if self._is_countdown else 0.0
        self._timer_running = True

    def stop_timer(self) -> None:
        self._timer_running = False

    def pause_timer(self) -> None:
        self._timer_running = False
        self._timer_paused = True

    def resume_timer(self) -> None:
        self._timer_running = True
        self._timer_paused = False

    def update(self, dt: float) -> None:
        if self._timer_running:
            if self._is_countdown:
                self._timer -= dt
                if self._timer <= 0.0:
                    self._timer = 0.0
                    self._event_bus.emit(Events.PLAYER_DIED)
                    self._timer_running = False
            else:
                self._timer += dt
        self._hurt_portrait_timer = max(0.0, self._hurt_portrait_timer - dt)
        self._save_notify_timer = max(0.0, self._save_notify_timer - dt)
        self._pulso_timer = max(0.0, self._pulso_timer - dt)
        self._heart_flash_timer = max(0.0, self._heart_flash_timer - dt)
        if self._heart_flash_timer <= 0:
            self._heart_flash_slot = -1
        # Timer flash at 2Hz when countdown ≤30s
        if self._timer_running or self._timer_paused:
            total_seconds = int(self._timer)
            if self._is_countdown and total_seconds <= 30:
                self._timer_flash_timer += dt
                if self._timer_flash_timer >= 0.25:
                    self._timer_flash_on = not self._timer_flash_on
                    self._timer_flash_timer = 0.0
            else:
                self._timer_flash_on = False
                self._timer_flash_timer = 0.0

        if self._heal_anim_active:
            self._sparkle_frame = int(self._heal_anim_timer * 12) % max(len(self._sparkle_frames), 1)
            self._heal_anim_timer += dt
            if self._heal_anim_timer >= 0.1:
                self._heal_anim_timer = 0.0
                self._heal_anim_slot_index += 1
                if self._heal_anim_slot_index >= len(self._heal_anim_slots):
                    self._heal_anim_active = False

    def _get_portrait_state(self) -> str:
        if self._health <= 0:
            return "dead"
        if self._health <= 1.0:
            return "critical"
        if self._hurt_portrait_timer > 0:
            return "hurt"
        return "normal"

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_portrait(surface)
        self._draw_hearts(surface)
        self._draw_special_meter(surface)
        self._draw_estamina(surface)
        self._draw_tiempo_bala(surface)
        self._draw_boss_rush(surface)
        self._draw_score(surface)
        self._draw_timer(surface)
        if self._boss_active:
            self._draw_boss_hud(surface)
        if self._combo_count > 1:
            self._draw_combo_indicator(surface)
        self._draw_save_notification(surface)

    def set_score(self, puntos: int, monedas: int = 0) -> None:
        """Puntos de la partida y saldo de monedas (AUD-219).

        Van juntos porque se leen juntos: los puntos dicen cómo va la partida y
        las monedas, si ya alcanza para comprar algo. Enseñar sólo lo primero
        deja al jugador yendo a la tienda a ver si le llega.
        """
        self._score = max(0, int(puntos))
        self._coins = max(0, int(monedas))

    def _score_text(self) -> str:
        return f"{self._score}  ¤{self._coins}"

    def score_rect(self) -> pygame.Rect:
        """Lo que ocupa de verdad el marcador dibujado, no la región reservada.

        La usa la prueba que comprueba que cabe donde `09_HUD_SPEC.md` dice, y
        que no pisa ni los corazones ni el cronómetro.
        """
        w, h = self._font.size(self._score_text())
        r = self._score_region
        return pygame.Rect(r.right - w, r.y, w, min(h, r.height))

    def set_boss_rush(self, progreso: str, jefe: str,
                      puntos: int, golpes: int) -> None:
        """Los datos del Boss Rush. Con `progreso` vacío la franja no se dibuja.

        AUD-274 — AUD-261 conectó el modo entero y el jugador no veía nada: la
        puntuación se calculaba, los golpes se contaban, la vida se arrastraba,
        y todo ello era invisible. Un marcador que no se ve es, para quien
        juega, un marcador que no existe.
        """
        self._rush_progreso = progreso
        self._rush_jefe = jefe
        self._rush_puntos = puntos
        self._rush_golpes = golpes

    def _draw_boss_rush(self, surface: pygame.Surface) -> None:
        """Una línea arriba: en qué combate va, contra quién y cuántos golpes.

        Una línea y no un panel: el Boss Rush es un modo de concentración, y
        una interfaz que tape la arena trabaja en contra del propio modo.
        """
        if not self._rush_progreso:
            return
        izquierda = self._font.render(
            f"RUSH {self._rush_progreso}  {self._rush_jefe}", True, (255, 210, 120))
        derecha = self._font.render(
            f"{self._rush_puntos} pts   {self._rush_golpes} golpes",
            True, (235, 235, 210))
        y = 20
        surface.blit(izquierda, (settings.INTERNAL_WIDTH // 2
                                 - izquierda.get_width() // 2, y))
        surface.blit(derecha, (settings.INTERNAL_WIDTH
                               - derecha.get_width() - 8, y))

    #: AUD-281 — cuánto dura el rebote del contador al recoger algo.
    #:
    #: 0,18 s. Más corto no se ve; más largo y dos monedas seguidas dejan el
    #: número temblando, que es lo que hace que un jugador acabe mirando la
    #: esquina en vez del escenario.
    _PULSO_DE_RECOGIDA: float = 0.18

    #: Cuánto crece en el pico, en veces. 1,25 se nota de reojo sin empujar el
    #: número contra el marco del cronómetro.
    _PULSO_ESCALA: float = 1.25

    def pulso_de_recogida(self) -> None:
        """Rebota el contador de monedas. Lo llama la escena al recoger algo.

        Respeta «movimiento reducido» dejándolo en nada: es adorno, y la opción
        existe justamente para quitar el adorno que se mueve. Aquí sí se puede
        anular del todo —al contrario que la estela del dash, que era la única
        señal de que el dash ocurrió—, porque el número ya dice lo que pasó.
        """
        from src.engine.core import user_settings

        if user_settings.preferencia("reduced_motion", False):
            return
        self._pulso_timer = self._PULSO_DE_RECOGIDA

    def _draw_score(self, surface: pygame.Surface) -> None:
        """Alineado a la derecha, pegado al cronómetro.

        Alineado a la derecha y no a la izquierda porque el número crece: con
        el origen fijo a la izquierda, pasar de 9999 a 10000 lo empujaría
        contra el marco del cronómetro a mitad de partida.
        """
        r = self.score_rect()
        puntos = self._font.render(str(self._score), True, (235, 235, 210))
        monedas = self._font.render(f"¤{self._coins}", True, (255, 215, 0))
        surface.blit(puntos, (r.x, r.y))

        # AUD-281 — el rebote. Crece y vuelve, anclado a su borde derecho para
        # que el número no se desplace mientras late: escalar desde la esquina
        # superior izquierda lo empujaría contra el cronómetro en cada moneda.
        if self._pulso_timer > 0.0:
            fase = self._pulso_timer / self._PULSO_DE_RECOGIDA
            # Media onda de seno: sube y baja una vez, sin tirón al terminar.
            escala = 1.0 + (self._PULSO_ESCALA - 1.0) * math.sin(fase * math.pi)
            ancho = max(1, int(monedas.get_width() * escala))
            alto = max(1, int(monedas.get_height() * escala))
            monedas = pygame.transform.smoothscale(monedas, (ancho, alto))

        surface.blit(monedas, (r.right - monedas.get_width(), r.y))

    def set_special_meter(self, current: float, max_val: float) -> None:
        self._special_current = current
        self._special_max = max_val

    def set_estamina(self, current: float, max_val: float) -> None:
        """AUD-141. Con `max_val = 0` la barra no se dibuja.

        Un medidor vacío en pantalla en los quince escenarios que no usan
        estamina sería una promesa falsa: el jugador buscaría qué lo llena.
        """
        self._estamina_actual = current
        self._estamina_max = max_val

    def set_tiempo_bala(self, fraccion: float, activo: bool) -> None:
        """AUD-260. Con `fraccion` negativa la barra no se dibuja.

        Mismo trato que la estamina (AUD-141): un medidor en pantalla en los
        dieciséis escenarios que no declaran `tiempo_bala` sería una promesa
        falsa. La escena manda `-1.0` cuando la mecánica está apagada.
        """
        self._bala_fraccion = fraccion
        self._bala_activo = activo

    def _draw_tiempo_bala(self, surface: pygame.Surface) -> None:
        if self._bala_fraccion < 0.0:
            return
        # AUD-455 — estas tres barras eran la última maqueta sin escalar: el
        # medidor especial, la estamina y el tiempo bala se dibujaban a 60×4 px
        # de verdad sobre 800×600, invisibles en la esquina mientras el resto
        # del HUD (retrato, corazones, marcador, reloj) ya estaba a ×2,5.
        bar_x, bar_y, bar_w, bar_h = _e(84), _e(46), _e(60), _e(4)
        pct = max(0.0, min(1.0, self._bala_fraccion))
        pygame.draw.rect(surface, (30, 30, 50), (bar_x, bar_y, bar_w, bar_h))
        if pct > 0:
            # Azul mientras está guardada, blanco mientras se gasta: el
            # jugador tiene que ver **que la está usando** sin apartar la
            # vista del combate, que es cuando la usa.
            color = (255, 255, 255) if self._bala_activo else (110, 160, 255)
            pygame.draw.rect(surface, color,
                             (bar_x, bar_y, int(bar_w * pct), bar_h))
        pygame.draw.rect(surface, (160, 180, 230), (bar_x, bar_y, bar_w, bar_h), 1)

    def _draw_estamina(self, surface: pygame.Surface) -> None:
        if self._estamina_max <= 0.0:
            return
        bar_x, bar_y, bar_w, bar_h = _e(84), _e(40), _e(60), _e(4)
        pct = max(0.0, min(1.0, self._estamina_actual / self._estamina_max))
        pygame.draw.rect(surface, (25, 45, 30), (bar_x, bar_y, bar_w, bar_h))
        if pct > 0:
            # Ámbar cuando queda poco: el jugador tiene que poder decidir
            # **antes** de intentar el dash que no va a salir.
            color = (120, 220, 130) if pct > 0.34 else (230, 180, 70)
            pygame.draw.rect(surface, color,
                             (bar_x, bar_y, int(bar_w * pct), bar_h))
        pygame.draw.rect(surface, (150, 210, 160), (bar_x, bar_y, bar_w, bar_h), 1)

    def _draw_special_meter(self, surface: pygame.Surface) -> None:
        bar_x, bar_y, bar_w, bar_h = _e(84), _e(30), _e(60), _e(6)
        pct = min(1.0, self._special_current / max(self._special_max, 1.0))
        bg_color = (40, 20, 60)
        fill_color = (100, 150, 255) if pct < 1.0 else (255, 220, 50)
        pygame.draw.rect(surface, bg_color, (bar_x, bar_y, bar_w, bar_h))
        if pct > 0:
            pygame.draw.rect(surface, fill_color, (bar_x, bar_y, int(bar_w * pct), bar_h))
        pygame.draw.rect(surface, (200, 200, 255), (bar_x, bar_y, bar_w, bar_h), 1)
        if pct >= 1.0:
            flash = (int(pygame.time.get_ticks() / 200) % 2 == 0)
            if flash:
                label = self._font.render("ULTIMATE READY", True, (255, 220, 50))
                surface.blit(label, (bar_x, bar_y - _e(14)))

    def _draw_save_notification(self, surface: pygame.Surface) -> None:
        if self._save_notify_timer <= 0:
            return
        alpha = int(255 * min(1.0, self._save_notify_timer / 0.5))
        txt = self._font.render("SAVED", True, (100, 255, 100))
        txt.set_alpha(alpha)
        tx = (settings.INTERNAL_WIDTH - txt.get_width()) // 2
        ty = settings.INTERNAL_HEIGHT - 20
        surface.blit(txt, (tx, ty))

    def _draw_combo_indicator(self, surface: pygame.Surface) -> None:
        import src.engine.core.settings as settings
        idx = min(self._combo_count - 1, len(settings.COMBO_DAMAGE_MULT) - 1)
        mult = settings.COMBO_DAMAGE_MULT[idx]
        txt = self._font.render(f"COMBO x{self._combo_count}! {mult}x", True, (255, 220, 100))
        tx = (settings.INTERNAL_WIDTH - txt.get_width()) // 2
        ty = settings.INTERNAL_HEIGHT - 32
        surface.blit(txt, (tx, ty))

    def _draw_portrait(self, surface: pygame.Surface) -> None:
        state = self._get_portrait_state()
        portrait = self._portraits.get(state)

        # Draw fill (pre-scaled in __init__)
        if self._portrait_fill:
            surface.blit(self._portrait_fill, self._portrait_frame_rect)

        # Draw portrait sprite
        if portrait:
            surface.blit(portrait, self._portrait_sprite_rect)
        else:
            color_map = {"normal": (60, 60, 80), "hurt": (180, 60, 60),
                         "critical": (200, 40, 40), "dead": (40, 40, 40)}
            color = color_map.get(state, (60, 60, 80))
            pygame.draw.rect(surface, color, self._portrait_sprite_rect)

        # Draw 9-slice frame with pre-scaled edges
        if self._frame_corners:
            r = self._portrait_frame_rect
            c = _e(2)
            surface.blit(self._frame_corners["tl"], (r.x, r.y))
            surface.blit(self._frame_corners["tr"], (r.right - c, r.y))
            surface.blit(self._frame_corners["bl"], (r.x, r.bottom - c))
            surface.blit(self._frame_corners["br"], (r.right - c, r.bottom - c))
            surface.blit(self._portrait_edges["top"], (r.x + c, r.y))
            surface.blit(self._portrait_edges["bottom"], (r.x + c, r.bottom - c))
            surface.blit(self._portrait_edges["left"], (r.x, r.y + c))
            surface.blit(self._portrait_edges["right"], (r.right - c, r.y + c))
        else:
            pygame.draw.rect(surface, (100, 100, 140), self._portrait_frame_rect, 1)

    def _draw_hearts(self, surface: pygame.Surface) -> None:
        slot_count = int(self._max_health)
        for slot in range(slot_count):
            state = _heart_slot_state(self._health, slot)
            x = self._hearts_x + slot * self._heart_spacing
            y = self._hearts_y

            # Heart damage flash: alternate between old/new state
            if self._heart_flash_timer > 0 and slot == self._heart_flash_slot:
                flash_frame = int(self._heart_flash_timer * 10) % 2 == 0
                if flash_frame and self._heart_flash_old_state:
                    state = self._heart_flash_old_state

            sprite = self._heart_sprites.get(state)
            if sprite and sprite.get_width() > 1:
                surface.blit(sprite, (x, y))
            else:
                color_map = {
                    "empty": (60, 0, 0),
                    "quarter": (120, 40, 40),
                    "half": (160, 80, 40),
                    "three_quarter": (180, 40, 40),
                    "full": (200, 20, 20),
                }
                color = color_map.get(state, (100, 0, 0))
                rect = pygame.Rect(x, y, _e(14), _e(8))
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (255, 50, 50), rect, 1)

            # Heal sparkle effect on current animated slot (right→left, sequential)
            if (self._heal_anim_active and self._sparkle_frames
                    and self._heal_anim_slot_index < len(self._heal_anim_slots)):
                current_slot = self._heal_anim_slots[self._heal_anim_slot_index]
                if slot == current_slot:
                    frame_idx = min(self._sparkle_frame, len(self._sparkle_frames) - 1)
                    surface.blit(self._sparkle_frames[frame_idx], (x, y))

    def _draw_boss_hud(self, surface: pygame.Surface) -> None:
        """Draw boss health bar and name at top of screen."""
        # AUD-459 — la barra era la última maqueta sin escalar: 200×12 a pelo
        # sobre 800×600. Se escala como el resto del HUD.
        bar_width = _e(200)
        bar_height = _e(12)
        bar_x = (settings.INTERNAL_WIDTH - bar_width) // 2
        bar_y = _e(4)
        # Boss name
        phase_text = f"PHASE {self._boss_phase_count}" if self._boss_phase_count > 0 else ""
        label = f"{self._boss_name}  {phase_text}" if phase_text else self._boss_name
        name_surf = self._font.render(label, True, (200, 180, 120))
        nx = bar_x + (bar_width - name_surf.get_width()) // 2
        surface.blit(name_surf, (nx, bar_y - _e(2)))
        # Background bar
        pygame.draw.rect(surface, (40, 30, 20), (bar_x, bar_y + _e(10), bar_width, bar_height))
        pygame.draw.rect(surface, (100, 80, 50), (bar_x, bar_y + _e(10), bar_width, bar_height), 1)
        # Health fill
        if self._boss_max_health > 0:
            ratio = max(0.0, self._boss_health / self._boss_max_health)
            fill_w = int(bar_width * ratio)
            color = (200, 60, 40) if ratio < 0.3 else (200, 180, 60)
            if fill_w > 0:
                pygame.draw.rect(surface, color, (bar_x, bar_y + _e(10), fill_w, bar_height))

    def _draw_timer_background(self, surface: pygame.Surface) -> None:
        r = self._timer_bg_rect
        c = _e(2)
        if self._frame_corners:
            surface.blit(self._frame_corners["tl"], (r.x, r.y))
            surface.blit(self._frame_corners["tr"], (r.right - c, r.y))
            surface.blit(self._frame_corners["bl"], (r.x, r.bottom - c))
            surface.blit(self._frame_corners["br"], (r.right - c, r.bottom - c))
            surface.blit(self._timer_edges["top"], (r.x + c, r.y))
            surface.blit(self._timer_edges["bottom"], (r.x + c, r.bottom - c))
            surface.blit(self._timer_edges["left"], (r.x, r.y + c))
            surface.blit(self._timer_edges["right"], (r.right - c, r.y + c))
            if self._timer_fill:
                surface.blit(self._timer_fill, r, special_flags=pygame.BLEND_ALPHA_SDL2)
        else:
            pygame.draw.rect(surface, (10, 10, 30), r)
            pygame.draw.rect(surface, (100, 100, 140), r, 1)

    def _draw_timer(self, surface: pygame.Surface) -> None:
        if not self._timer_running and not self._timer_paused:
            return
        self._draw_timer_background(surface)
        # Draw "TIME" label at left side of timer background — use same TTF font as digits
        label_font = self._timer_digit_font or self._font
        label_surf = label_font.render("TIME", True, (200, 200, 200))
        surface.blit(label_surf, (self._timer_label_rect.x, self._timer_label_rect.y))
        total_seconds = int(self._timer)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        # 2Hz flash: hide text when flashing
        flash = self._is_countdown and total_seconds <= 30
        if flash and not self._timer_flash_on:
            return
        color = (255, 255, 255)
        if self._timer_digit_font:
            time_surf = self._timer_digit_font.render(time_str, True, color)
            if time_surf.get_width() > 0:
                tx = self._timer_rect.x + max(0, (self._timer_rect.width - time_surf.get_width()) // 2)
                ty = self._timer_rect.y + (self._timer_rect.height - time_surf.get_height()) // 2
                surface.blit(time_surf, (tx, ty))
        else:
            text = self._font.render(time_str, True, color)
            tx = self._timer_rect.x + max(0, (self._timer_rect.width - text.get_width()) // 2)
            ty = self._timer_rect.y + (self._timer_rect.height - text.get_height()) // 2
            surface.blit(text, (tx, ty))

    @property
    def current_time(self) -> float:
        return self._timer

    @current_time.setter
    def current_time(self, value: float) -> None:
        self._timer = value

    @property
    def time_limit(self) -> int:
        return self._time_limit

    @property
    def is_countdown(self) -> bool:
        return self._is_countdown

    @is_countdown.setter
    def is_countdown(self, value: bool) -> None:
        self._is_countdown = value

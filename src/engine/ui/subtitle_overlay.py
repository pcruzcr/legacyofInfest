"""
Module: subtitle_overlay
System: engine.ui
Academic Unit: N/A

Captions for significant audio events, for players who cannot hear them.

AUD-036: ``settings.SUBTITLES_ENABLED`` existed as a module global with no
writer and no reader — a declared accessibility feature with no implementation
behind it. This module is the reader.

Dialogue text is already always drawn on screen, so the gap was *non-speech*
audio: the game communicates a boss entering phase two, a parry landing, a
checkpoint activating and a hazard triggering largely through sound. A deaf or
hard-of-hearing player loses that channel entirely. The overlay subscribes to
the same SFX/music events the audio manager listens to and renders a short
caption for the ones that carry information, ignoring the ones that are purely
texture (footsteps, ambient loops) so the captions stay readable.
"""
from __future__ import annotations

import logging
from collections.abc import Callable

import pygame

from src.engine.core import settings, user_settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.ui.theme import Theme, font

logger = logging.getLogger(__name__)

# How long a caption stays on screen, in seconds.
CAPTION_DURATION: float = 2.2
# Most captions visible at once; older ones scroll off the top.
MAX_VISIBLE: int = 3

# Only events that carry *information* get captioned. Deliberately excludes
# footsteps, jumps, landings and ambient loops: captioning those produces a
# wall of noise that makes the meaningful captions unreadable, which is worse
# for accessibility than showing nothing.
CAPTIONS: dict[str, str] = {
    Events.SFX_BOSS_PHASE_CHANGE: "[Boss changes stance]",
    Events.SFX_BOSS_HIT: "[Boss struck]",
    Events.SFX_PLAYER_PARRY: "[Parry!]",
    Events.SFX_PLAYER_HEAL: "[Health restored]",
    Events.SFX_STAGE_COMPLETE: "[Stage complete]",
    Events.SFX_UI_GAME_OVER: "[Game over]",
    Events.SFX_ENVIRONMENT_SCREEN_SHAKE: "[Rumbling]",
    Events.SFX_ENEMIES_PROJECTILE_HIT_WALL: "[Projectile impact]",
    Events.SFX_BOSSES_VENADO_CHARGE: "[Venado charges]",
    Events.SFX_BOSSES_VENADO_STOMP: "[Venado stomps]",
    Events.SFX_BOSSES_VENADO_VINE: "[Vines erupt]",
    Events.SFX_BOSSES_GAVILAN_DIVE: "[Gavilán dives]",
    Events.SFX_BOSSES_GAVILAN_MASK_BEAM: "[Mask beam charging]",
    Events.SFX_BOSSES_PABURU_EYE_BEAM: "[Eye beam charging]",
    Events.SFX_BOSSES_PABURU_WAVE: "[Shockwave incoming]",
    Events.SFX_BOSSES_REY_SPIT: "[Rey spits]",
    Events.SFX_BOSSES_REY_SPLIT: "[Rey splits]",
    Events.SFX_BOSSES_RELIC_APPEAR: "[A relic appears]",
    Events.MUSIC_STINGER: "[Music swells]",
    Events.CHECKPOINT_REACHED: "[Checkpoint reached]",
    # AUD-064: el docstring de arriba prometía subtitular «a hazard
    # triggering» y esta entrada no existía. Es de las que más falta hacen:
    # una zona de daño puede no tener ninguna señal visual distinguible del
    # decorado, así que sin sonido ni subtítulo el jugador pierde vida sin
    # saber por qué.
    Events.SFX_HAZARD_ZONE: "[Hazard!]",
}


class SubtitleOverlay:
    """Renders captions for audio events while subtitles are enabled.

    Subscribing is unconditional; the *enabled* check happens at draw time, so
    toggling the preference mid-session takes effect immediately without
    re-wiring the bus.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus
        self._font: pygame.font.Font | None = None
        # (text, remaining_seconds)
        # AUD-371 — `list[tuple[str, float]]`, no `list[list[object]]`.
        # El tipo flojo obligaba a `float(...)` y `str(...)` en cada uso y a
        # dos `# type: ignore`, o sea a repetir en cada línea lo que la
        # declaración debía haber dicho una vez. Tuplas y no listas porque
        # el rótulo no se muta: se sustituye, que es lo que ya hacía el
        # filtro de `update`. Indexar `entry[0]` sigue funcionando igual.
        self._active: list[tuple[str, float]] = []
        self._handlers: dict[str, Callable[..., None]] = {}
        self._subscribe()

    # ── lifecycle ──────────────────────────────────────────────

    def _subscribe(self) -> None:
        for event_name, caption in CAPTIONS.items():
            handler = self._make_handler(caption)
            # Handlers must be retained: the bus holds weak references.
            self._handlers[event_name] = handler
            self._bus.subscribe(event_name, handler)

    def _make_handler(self, caption: str) -> Callable[..., None]:
        def handler(**_data: object) -> None:
            self.push(caption)
        return handler

    def rearm(self) -> None:
        """Re-establish subscriptions after a ``destroy()``.

        Scenes are re-entered (``on_exit`` then ``on_enter`` on the same
        instance) in some flows, and a destroyed overlay would otherwise stay
        silent for the rest of the session. Subscription is idempotent, so
        calling this when already armed is harmless.
        """
        if not self._handlers:
            self._subscribe()

    def destroy(self) -> None:
        """Unsubscribe every handler. Call from the owning scene's on_exit."""
        for event_name, handler in self._handlers.items():
            self._bus.unsubscribe(event_name, handler)
        self._handlers.clear()
        self._active.clear()

    # ── content ────────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        return user_settings.get().subtitles_enabled

    def push(self, text: str) -> None:
        """Queue a caption. Repeats of the visible caption refresh it instead
        of stacking, so a rapidly repeating sound does not flood the band."""
        if not self.enabled:
            return
        for i, (rotulo, _) in enumerate(self._active):
            if rotulo == text:
                self._active[i] = (rotulo, CAPTION_DURATION)
                return
        self._active.append((text, CAPTION_DURATION))
        if len(self._active) > MAX_VISIBLE:
            del self._active[0]

    def update(self, dt: float) -> None:
        if not self._active:
            return
        # Se descuenta y se filtra en una sola pasada: el resultado es el
        # mismo que decrementar todos y quedarse con los positivos.
        self._active = [
            (rotulo, restante - dt) for rotulo, restante in self._active
            if restante - dt > 0.0
        ]

    # ── rendering ──────────────────────────────────────────────

    def _ensure_font(self) -> pygame.font.Font:
        if self._font is None:
            if not pygame.font.get_init():
                pygame.font.init()
            # AUD-451 — por el tema, para que la escala de accesibilidad
            # llegue también a los subtítulos. Que precisamente éstos la
            # ignoraran es lo peor del defecto: existen para quien los
            # necesita.
            self._font = font(Theme.FONT_SMALL)
        return self._font

    def draw(self, surface: pygame.Surface) -> None:
        if not self.enabled or not self._active:
            return
        font = self._ensure_font()
        # Anchored above the bottom edge, clear of the HUD and the dialogue box.
        y = settings.INTERNAL_HEIGHT - 150 - (len(self._active) - 1) * 18
        for text, remaining in self._active:
            # Fade the last half-second so captions leave calmly.
            alpha = 255 if remaining > 0.5 else int(255 * remaining / 0.5)
            label = font.render(text, True, (235, 235, 245))
            label.set_alpha(max(0, min(255, alpha)))
            x = (settings.INTERNAL_WIDTH - label.get_width()) // 2
            backdrop = pygame.Surface(
                (label.get_width() + 12, label.get_height() + 4), pygame.SRCALPHA,
            )
            backdrop.fill((0, 0, 0, min(160, alpha)))
            surface.blit(backdrop, (x - 6, y - 2))
            surface.blit(label, (x, y))
            y += 18

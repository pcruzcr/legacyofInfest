"""
Module: security_monitor
System: stages.stage2_1_oficinas
Academic Unit: Unit VI (Animation/Interaction) + Unit VII (Digital Filters)

Monitor de seguridad de la Sala de Control — Evaluación Práctica II
(`docs/eval_practica/eval_practica.md`):

  - **Unidad VI — animación + interacción (20 pts):** el panel no aparece de
    golpe. Se activa por un evento real del juego (`Events.CHECKPOINT_REACHED`
    con `checkpoint_id=SALA_CONTROL_CHECKPOINT_ID`, ya emitido por
    `checkpoint.py`, no un timer inventado aquí) y su entrada/cambio de modo
    se anima con `ease_out_cubic`/`ease_in_out_quad` (`math_utils.py`), no un
    blit directo al 100%.
  - **Unidad VII — histograma (15 pts):** `FilterTools.compute_histogram()`
    no se calcula y se descarta: su luminancia media **decide** cuánto
    brillo/contraste aplica el modo "histograma" (`_auto_levels`). Una toma
    oscura se corrige más que una clara — el histograma dirige la lógica,
    tal como pide la rúbrica.
  - **Unidad VII — convolución/bordes (20 pts):** `FilterTools.gaussian_blur`
    (modo "desenfoque") y `FilterTools.sobel_edge` (modo "bordes") sobre la
    misma captura.

Los cuatro modos se precalculan **una sola vez** por captura (F2.3 del
changelog: no recalcular filtros por fotograma sobre una imagen que no
cambia) y sólo se recorren en pantalla.

No es una entidad de Tiled: no se coloca en el TMX ni pasa por
`entity_factory`, vive en la propia escena (`stage2_1_oficinas.py`), así que
no toca ningún código compartido del framework.
"""
from __future__ import annotations

import pygame

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.utils.math_utils import clamp, ease_in_out_quad, ease_out_cubic
from src.framework.processing.filter_tools import FilterTools

#: Checkpoint de la Sala de Control (ver stage2_1_oficinas.tmx: checkpoint_id
#: 0-6 uno por puerta/sala; el 4 cae dentro del rango x de esa sala).
SALA_CONTROL_CHECKPOINT_ID = 4

#: Recorte del propio mundo renderizado que se usa como "foto" de la cámara.
#: Elegido lejos de las esquinas donde vive el HUD (vida, cronómetro,
#: minimapa) para no capturar esos elementos por accidente.
CAPTURE_RECT = pygame.Rect(280, 260, 200, 140)
SCREEN_SIZE = (176, 128)
SCREEN_POS = (600, 436)

_MODES = ("captura", "histograma", "desenfoque", "bordes")
_MODE_LABELS = {
    "captura": "FEED EN VIVO",
    "histograma": "AUTO-NIVELES (histograma)",
    "desenfoque": "DESENFOQUE GAUSSIANO",
    "bordes": "BORDES (Sobel)",
}
_MODE_HOLD_SECONDS = 3.2
_MODE_TRANSITION_SECONDS = 0.6


class SecurityMonitor:
    """Panel HUD de la Sala de Control. No es un `BaseEntity`: la crea y la
    dibuja directamente `Stage21Oficinas`, igual que hace el motor con su
    propio `HUD`."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._active = False
        self._captured: pygame.Surface | None = None
        self._processed: dict[str, pygame.Surface] = {}
        self._mode_index = 0
        self._mode_timer = 0.0
        self._transition_t = 1.0
        self._font: pygame.font.Font | None = None
        event_bus.subscribe(Events.CHECKPOINT_REACHED, self._on_checkpoint)

    def destroy(self) -> None:
        """Se llama antes de crear el reemplazo (ver AUD-072 en stage_scene.py:
        `on_enter` corre en cada reaparición, y una suscripción sin liberar
        deja al bus podando un handler muerto en cada evento)."""
        self._event_bus.unsubscribe(Events.CHECKPOINT_REACHED, self._on_checkpoint)

    def _on_checkpoint(self, **data: object) -> None:
        if data.get("checkpoint_id") == SALA_CONTROL_CHECKPOINT_ID and not self._active:
            self._active = True
            self._mode_index = 0
            self._mode_timer = 0.0
            self._transition_t = 0.0
            self._event_bus.emit(Events.SFX_MENU_CONFIRM)

    # ── Unidad VII: histograma dirigiendo brillo/contraste ──────────────
    @staticmethod
    def _auto_levels(snap: pygame.Surface) -> pygame.Surface:
        hist = FilterTools.compute_histogram(snap)
        luminance = hist["luminance"]
        total = max(int(hist["total_pixels"]), 1)
        mean_luma = sum(i * int(c) for i, c in enumerate(luminance)) / total / 255.0
        # Cuanto más oscura la captura, más se le sube brillo y contraste;
        # una sala ya clara casi no se toca. Los rangos vienen de probar
        # contra las capturas reales de este escenario (bien iluminado, la
        # luminancia media ronda 0.35-0.45).
        brightness_factor = clamp(1.55 - mean_luma, 1.0, 1.9)
        contrast_factor = clamp(1.7 - mean_luma * 0.6, 1.15, 1.9)
        bright = FilterTools.adjust_brightness(snap, brightness_factor)
        return FilterTools.adjust_contrast(bright, contrast_factor)

    def capture(self, world_surface: pygame.Surface) -> None:
        """Toma la "foto" del mundo ya renderizado y precalcula los 4 modos
        una sola vez — no en cada `draw()`."""
        rect = CAPTURE_RECT.clip(world_surface.get_rect())
        if rect.width < 4 or rect.height < 4:
            return
        snap = world_surface.subsurface(rect).copy()
        snap = pygame.transform.smoothscale(snap, SCREEN_SIZE)
        self._captured = snap
        self._processed = {
            "captura": snap,
            "histograma": self._auto_levels(snap),
            "desenfoque": FilterTools.gaussian_blur(snap, 2.4),
            "bordes": FilterTools.sobel_edge(snap),
        }

    def update(self, dt: float) -> None:
        if not self._active or not self._processed:
            return
        self._transition_t = clamp(self._transition_t + dt / _MODE_TRANSITION_SECONDS, 0.0, 1.0)
        self._mode_timer += dt
        if self._mode_timer >= _MODE_HOLD_SECONDS:
            self._mode_timer = 0.0
            self._mode_index = (self._mode_index + 1) % len(_MODES)
            self._transition_t = 0.0
            # Blip de cambio de modo. Reutiliza SFX_MENU_CONFIRM (ya mapeado
            # a un pitido corto de UI en stage_scene.py) en vez de dar de
            # alta un evento nuevo sólo para este panel.
            self._event_bus.emit(Events.SFX_MENU_CONFIRM)

    def draw(self, surface: pygame.Surface) -> None:
        if not self._active:
            return
        if self._captured is None:
            self.capture(surface)
            if self._captured is None:
                return
        if self._font is None:
            self._font = pygame.font.Font(None, 14)

        mode = _MODES[self._mode_index]
        frame = self._processed[mode]

        # Unidad VI: entrada animada por easing — crece y se desvanece hacia
        # adentro en vez de aparecer al 100% en el primer fotograma.
        grow = ease_out_cubic(self._transition_t)
        fade = ease_in_out_quad(min(1.0, self._transition_t * 2.0))
        w = max(4, int(SCREEN_SIZE[0] * (0.82 + 0.18 * grow)))
        h = max(4, int(SCREEN_SIZE[1] * (0.82 + 0.18 * grow)))
        scaled = pygame.transform.smoothscale(frame, (w, h))

        panel = pygame.Surface((SCREEN_SIZE[0] + 8, SCREEN_SIZE[1] + 24), pygame.SRCALPHA)
        panel.fill((10, 14, 20, int(225 * fade)))
        pygame.draw.rect(panel, (80, 200, 230, int(255 * fade)), panel.get_rect(), 1)
        ox = (panel.get_width() - w) // 2
        panel.blit(scaled, (ox, 4))
        label_surf = self._font.render(_MODE_LABELS[mode], True, (150, 230, 255))
        label_surf.set_alpha(int(255 * fade))
        panel.blit(label_surf, (6, SCREEN_SIZE[1] + 6))

        surface.blit(panel, SCREEN_POS)

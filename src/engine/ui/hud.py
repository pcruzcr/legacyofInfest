"""
Module: hud
System: engine.ui
Description: Heads-Up Display showing hearts (health), timer, and stage info.
Uses sprite-based hearts from assets/ui/ with font fallback.
"""
from __future__ import annotations
import logging
from typing import cast

import pygame
from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader


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

        # Portrait frame (34x34 with 1px border, inner sprite at 3,3)
        self._portrait_frame_rect = pygame.Rect(2, 2, 34, 34)
        self._portrait_sprite_rect = pygame.Rect(3, 3, 32, 32)
        self._portrait_fill = None
        self._portrait_edges: dict[str, pygame.Surface] = {}
        self._timer_fill = None
        self._timer_edges: dict[str, pygame.Surface] = {}
        # Load 9-slice frame from hud_frame.png, pre-scale all variants once
        try:
            raw_frame = AssetLoader.load_image(settings.ASSETS_DIR / "ui" / "hud_frame.png")
            fw, fh = raw_frame.get_size()
            if fw >= 6 and fh >= 6:
                c = 2  # corner size
                self._frame_corners = {
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
                self._frame_edges = src_edges
                src_fill = raw_frame.subsurface((c, c, fw - 2 * c, fh - 2 * c))
                self._frame_fill = src_fill
                # Pre-scale for portrait frame (34x34)
                pr = self._portrait_frame_rect
                self._portrait_fill = pygame.transform.scale(src_fill, (pr.width, pr.height))
                self._portrait_edges = {
                    "top": pygame.transform.scale(src_edges["top"], (pr.width - 4, 2)),
                    "bottom": pygame.transform.scale(src_edges["bottom"], (pr.width - 4, 2)),
                    "left": pygame.transform.scale(src_edges["left"], (2, pr.height - 4)),
                    "right": pygame.transform.scale(src_edges["right"], (2, pr.height - 4)),
                }
                # Timer background pre-scaling deferred until _timer_bg_rect is set
            else:
                self._frame_corners = {}
                self._frame_edges = {}
                self._frame_fill = None
        except (pygame.error, FileNotFoundError, PermissionError):
            logging.warning("hud: failed to load hud_frame.png")
            self._frame_corners = {}
            self._frame_edges = {}
            self._frame_fill = None

        self._hearts_x: int = 38
        self._hearts_y: int = 6
        self._heart_spacing: int = 16
        # Timer frame (reuse hud_frame.png 9-slice at timer size 90x16)
        self._timer_bg_rect = pygame.Rect(258, 1, 62, 16)
        # Pre-scale timer background once (deferred from frame load block)
        self._timer_fill = pygame.transform.scale(self._frame_fill, (self._timer_bg_rect.width, self._timer_bg_rect.height)) if isinstance(self._frame_fill, pygame.Surface) else None
        if self._frame_edges:
            tr = self._timer_bg_rect
            self._timer_edges = {
                "top": pygame.transform.scale(self._frame_edges["top"], (tr.width - 4, 2)),
                "bottom": pygame.transform.scale(self._frame_edges["bottom"], (tr.width - 4, 2)),
                "left": pygame.transform.scale(self._frame_edges["left"], (2, tr.height - 4)),
                "right": pygame.transform.scale(self._frame_edges["right"], (2, tr.height - 4)),
            }
        self._timer_rect = pygame.Rect(288, 2, 32, 14)
        self._timer_label_rect = pygame.Rect(260, 2, 26, 12)
        self._timer_flash_timer: float = 0.0
        self._timer_flash_on: bool = False
        # Load timer font (TTF preferred for readability)
        self._timer_digit_font: pygame.font.Font | None = None
        try:
            self._timer_digit_font = pygame.font.Font(
                settings.ASSETS_DIR / "fonts" / "game.ttf", 12,
            )
        except (pygame.error, FileNotFoundError, PermissionError):
            logging.warning("hud: failed to load game.ttf for timer")
            self._timer_digit_font = None

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
                self._heart_sprites[state] = surf
            except (pygame.error, FileNotFoundError, PermissionError):
                logging.warning("hud: failed to load heart sprite %s", path)
                self._heart_sprites[state] = pygame.Surface((14, 8))

        try:
            sparkle_path = settings.ASSETS_DIR / "ui" / "heart_sparkle.png"
            self._sparkle_frames = AssetLoader.load_sprite_sheet(sparkle_path, 8, 8)
        except (pygame.error, FileNotFoundError, PermissionError):
            logging.warning("hud: failed to load heart_sparkle.png")
            self._sparkle_frames = []

        # Load portrait sprites
        self._portraits: dict[str, pygame.Surface] = {}
        for state in _PORTRAIT_STATES:
            path = settings.ASSETS_DIR / "ui" / f"portrait_{state}.png"
            try:
                surf = AssetLoader.load_image(path, size=(32, 32))
                self._portraits[state] = surf
            except (pygame.error, FileNotFoundError, PermissionError):
                logging.warning("hud: failed to load portrait %s", state)
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
        self._special_max: float = 100.0

        self._font = pygame.font.Font(None, 12)

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
        self._draw_timer(surface)
        if self._boss_active:
            self._draw_boss_hud(surface)
        if self._combo_count > 1:
            self._draw_combo_indicator(surface)
        self._draw_save_notification(surface)

    def set_special_meter(self, current: float, max_val: float) -> None:
        self._special_current = current
        self._special_max = max_val

    def _draw_special_meter(self, surface: pygame.Surface) -> None:
        bar_w = 60
        bar_h = 6
        bar_x = 84
        bar_y = 30
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
                surface.blit(label, (bar_x, bar_y - 14))

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
            c = 2
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
                rect = pygame.Rect(x, y, 14, 8)
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
        bar_width = 200
        bar_height = 12
        bar_x = (settings.INTERNAL_WIDTH - bar_width) // 2
        bar_y = 4
        # Boss name
        phase_text = f"PHASE {self._boss_phase_count}" if self._boss_phase_count > 0 else ""
        label = f"{self._boss_name}  {phase_text}" if phase_text else self._boss_name
        name_surf = self._font.render(label, True, (200, 180, 120))
        nx = bar_x + (bar_width - name_surf.get_width()) // 2
        surface.blit(name_surf, (nx, bar_y - 2))
        # Background bar
        pygame.draw.rect(surface, (40, 30, 20), (bar_x, bar_y + 10, bar_width, bar_height))
        pygame.draw.rect(surface, (100, 80, 50), (bar_x, bar_y + 10, bar_width, bar_height), 1)
        # Health fill
        if self._boss_max_health > 0:
            ratio = max(0.0, self._boss_health / self._boss_max_health)
            fill_w = int(bar_width * ratio)
            color = (200, 60, 40) if ratio < 0.3 else (200, 180, 60)
            if fill_w > 0:
                pygame.draw.rect(surface, color, (bar_x, bar_y + 10, fill_w, bar_height))

    def _draw_timer_background(self, surface: pygame.Surface) -> None:
        r = self._timer_bg_rect
        c = 2
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

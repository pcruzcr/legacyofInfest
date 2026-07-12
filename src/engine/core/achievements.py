from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygame
from src.engine.core import settings

from src.engine.core.event_bus import emit, subscribe, unsubscribe
from src.engine.core.events import Events

ACHIEVEMENTS_PATH = Path(os.environ.get("APPDATA", str(Path("~/.config").expanduser()))) / "legacyofinfest" / "achievements.json"


@dataclass
class AchievementDef:
    id: str
    name: str
    description: str
    icon: str = "trophy"
    hidden: bool = False
    target: int = 1
    event: str = ""


@dataclass
class AchievementProgress:
    current: int = 0
    unlocked: bool = False


class AchievementSystem:
    _instance: AchievementSystem | None = None

    @classmethod
    def get_instance(cls) -> AchievementSystem:
        if cls._instance is None:
            cls._instance = AchievementSystem()
        return cls._instance

    def __init__(self) -> None:
        self._defs: dict[str, AchievementDef] = {}
        self._progress: dict[str, AchievementProgress] = {}
        self._notifications: list[dict[str, Any]] = []
        self._notify_timer: float = 0.0
        self._current_notify: dict[str, Any] | None = None
        self._subscribed: bool = False
        self._stats: dict[str, int] = {}
        self._init_achievements()

    def _init_achievements(self) -> None:
        self.register(AchievementDef(
            id="first_blood", name="First Blood",
            description="Defeat your first enemy",
            target=1, event=Events.ENEMY_DIED,
        ))
        self.register(AchievementDef(
            id="exterminator", name="Exterminator",
            description="Defeat 50 enemies",
            target=50, event=Events.ENEMY_DIED,
        ))
        self.register(AchievementDef(
            id="untouchable", name="Untouchable",
            description="Complete a stage without taking damage",
            target=1,
        ))
        self.register(AchievementDef(
            id="parry_master", name="Parry Master",
            description="Successfully parry 10 attacks",
            target=10, event=Events.VFX_PARRY,
        ))
        self.register(AchievementDef(
            id="air_assault", name="Air Assault",
            description="Perform a 5-hit aerial combo",
            target=5,
        ))
        self.register(AchievementDef(
            id="speed_demon", name="Speed Demon",
            description="Complete a stage in under 60 seconds",
            target=1,
        ))
        self.register(AchievementDef(
            id="collector", name="Collector",
            description="Reach 5 checkpoints in a single run",
            target=5,
        ))
        self.register(AchievementDef(
            id="survivor", name="Survivor",
            description="Survive with 0.5 health or less",
            target=1,
        ))
        self.register(AchievementDef(
            id="combo_king", name="Combo King",
            description="Reach a 10-hit combo",
            target=10,
        ))
        self.register(AchievementDef(
            id="explorer", name="Explorer",
            description="Complete every stage",
            target=15,
        ))

    def register(self, ach: AchievementDef) -> None:
        self._defs[ach.id] = ach
        if ach.id not in self._progress:
            self._progress[ach.id] = AchievementProgress()

    def subscribe_events(self) -> None:
        if self._subscribed:
            return
        self._subscribed = True
        subscribe(Events.ENEMY_DIED, self._on_enemy_died)
        subscribe(Events.VFX_PARRY, self._on_parry)

    def unsubscribe_events(self) -> None:
        if not self._subscribed:
            return
        self._subscribed = False
        unsubscribe(Events.ENEMY_DIED, self._on_enemy_died)
        unsubscribe(Events.VFX_PARRY, self._on_parry)

    def _on_enemy_died(self, **data: object) -> None:
        self._stats["enemies_killed"] = self._stats.get("enemies_killed", 0) + 1
        self.progress("exterminator")
        self.progress("first_blood")

    def _on_parry(self, **data: object) -> None:
        self._stats["parries"] = self._stats.get("parries", 0) + 1
        self.progress("parry_master")

    def progress(self, achievement_id: str, amount: int = 1) -> None:
        ach = self._defs.get(achievement_id)
        prog = self._progress.get(achievement_id)
        if ach is None or prog is None or prog.unlocked:
            return
        prog.current = min(prog.current + amount, ach.target)
        emit(Events.ACHIEVEMENT_PROGRESS,
             achievement_id=achievement_id,
             progress=prog.current,
             target=ach.target)
        if prog.current >= ach.target:
            self._unlock(achievement_id)

    def _unlock(self, achievement_id: str) -> None:
        ach = self._defs.get(achievement_id)
        prog = self._progress.get(achievement_id)
        if ach is None or prog is None:
            return
        prog.unlocked = True
        self._notifications.append({
            "id": ach.id,
            "name": ach.name,
            "description": ach.description,
            "timer": 3.0,
        })
        emit(Events.ACHIEVEMENT_UNLOCKED,
             achievement_id=ach.id,
             name=ach.name)

    def _set_progress(self, achievement_id: str, value: int) -> None:
        prog = self._progress.get(achievement_id)
        if prog is not None:
            prog.current = value

    def is_unlocked(self, achievement_id: str) -> bool:
        prog = self._progress.get(achievement_id)
        return prog is not None and prog.unlocked

    def mark_survived_low_health(self) -> None:
        if not self.is_unlocked("survivor"):
            self._set_progress("survivor", 1)
            self._unlock("survivor")

    def mark_untouchable(self) -> None:
        if not self.is_unlocked("untouchable"):
            self._set_progress("untouchable", 1)
            self._unlock("untouchable")

    def mark_speed_demon(self) -> None:
        if not self.is_unlocked("speed_demon"):
            self._set_progress("speed_demon", 1)
            self._unlock("speed_demon")

    def mark_air_assault(self, combo_count: int) -> None:
        if not self.is_unlocked("air_assault") and combo_count >= 5:
            self._set_progress("air_assault", 1)
            self._unlock("air_assault")

    def mark_combo_king(self, combo_count: int) -> None:
        if not self.is_unlocked("combo_king") and combo_count >= 10:
            self._set_progress("combo_king", 1)
            self._unlock("combo_king")

    def mark_explorer(self, stage_id: str) -> None:
        if not self.is_unlocked("explorer"):
            seen: list[str] = self._stats.get("explored_stages", [])
            if stage_id not in seen:
                seen.append(stage_id)
                self._stats["explored_stages"] = seen
            self._set_progress("explorer", len(seen))
            if len(seen) >= 15:
                self._unlock("explorer")

    @property
    def achievements(self) -> list[tuple[AchievementDef, AchievementProgress]]:
        return [(self._defs[aid], self._progress[aid]) for aid in self._defs]

    def save(self) -> None:
        data = {
            "progress": {
                aid: {"current": p.current, "unlocked": p.unlocked}
                for aid, p in self._progress.items()
            },
            "stats": self._stats,
        }
        ACHIEVEMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ACHIEVEMENTS_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        try:
            with open(ACHIEVEMENTS_PATH) as f:
                data = json.load(f)
            saved_progress = data.get("progress", {})
            for aid, pdata in saved_progress.items():
                if aid in self._progress:
                    self._progress[aid].current = pdata.get("current", 0)
                    self._progress[aid].unlocked = pdata.get("unlocked", False)
            self._stats = data.get("stats", {})
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def get_all_achievements(self) -> list[tuple[AchievementDef, AchievementProgress]]:
        return [(self._defs[aid], self._progress[aid])
                for aid in self._defs
                if aid in self._progress]

    def update_notifications(self, dt: float) -> None:
        if self._current_notify is not None:
            self._current_notify["timer"] -= dt
            if self._current_notify["timer"] <= 0:
                self._current_notify = None
        if self._current_notify is None and self._notifications:
            self._current_notify = self._notifications.pop(0)

    def draw_notifications(self, surface: pygame.Surface) -> None:
        if self._current_notify is None:
            return
        n = self._current_notify
        w = settings.INTERNAL_WIDTH
        bar_w = 240
        bar_h = 32
        bx = (w - bar_w) // 2
        by = 60

        bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 200))
        surface.blit(bg, (bx, by))

        pygame.draw.rect(surface, (255, 215, 0), (bx, by, bar_w, bar_h), 1)

        font = pygame.font.Font(None, 14)
        title = font.render(f"Achievement Unlocked: {n['name']}", True, (255, 215, 0))
        surface.blit(title, (bx + 8, by + 3))
        desc = font.render(n['description'], True, (200, 200, 200))
        surface.blit(desc, (bx + 8, by + 17))

    def get_progress(self, achievement_id: str) -> int:
        prog = self._progress.get(achievement_id)
        return prog.current if prog else 0

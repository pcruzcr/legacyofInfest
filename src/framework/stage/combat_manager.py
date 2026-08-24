"""
Module: combat_manager
System: framework.stage
Description: Orquesta el sistema de combate por escenario — procesa ataques,
gestiona hit-stop en el reloj, y coordina elementos destructibles.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.framework.entities.player import Player
    from src.framework.stage.bloques import BloqueManager
    from src.framework.stage.camera import Camera
    from src.framework.stage.collision_system import CollisionSystem
    from src.framework.stage.stage_loader import StageData


class CombatManager:
    """Capa fina que orquesta el combate del escenario.

    Responsabilidades
    -----------------
    * Llamar a `CollisionSystem.process_attack` con los argumentos correctos.
    * Avanzar el hit-stop y aplicar su factor de tiempo en el reloj.
    * Delegar rotura de bloques destructibles al `BloqueManager`.
    * Resetear estado al cargar un escenario o al hacer respawn.

    Lo que **no** hace
    ----------------
    * No resuelve física de movimiento (eso es `Player.update` / `EnemyBase.update`).
    * No decide qué enemigos se actualizan (eso es `StageScene._update_gameplay`).
    * No conoce `StageScene` ni `StageScene` lo conoce — inyección por constructor.
    """

    def __init__(
        self,
        collision: CollisionSystem,
        bloques: BloqueManager | None = None,
    ) -> None:
        self._collision = collision
        self._bloques = bloques

    # ── ciclo ────────────────────────────────────────────────────

    def reset(self) -> None:
        """Limpia estado por escenario / respawn."""
        self._collision.reset()

    # ── ataque ──────────────────────────────────────────────────

    def process_attack(
        self,
        dt: float,
        player: Player,
        stage: StageData,
        camera: Camera | None = None,
        clock: Any = None,
    ) -> None:
        """Resuelve el hitbox activo del jugador contra enemigos y bloques."""
        self._collision.process_attack(dt, player, stage, camera, clock)
        if self._bloques is not None and player.active_hitbox is not None:
            self._bloques.golpear(player.active_hitbox)

    # ── hit-stop ────────────────────────────────────────────────

    def update_hitstop(self, unscaled_dt: float, clock: Any = None) -> None:
        """Descuenta el hit-stop y registra su factor de tiempo."""
        self._collision.update_hitstop(unscaled_dt, clock)

    def aplicar_factor_hitstop(self, clock: Any = None) -> None:
        """Aplica/retira el factor de hit-stop en el reloj (por paso de simulación)."""
        self._collision.aplicar_escala_de_hitstop(clock)

    @property
    def is_hitstopped(self) -> bool:
        return self._collision.is_hitstopped
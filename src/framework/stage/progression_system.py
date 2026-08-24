from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.entities.boss_base import BossBase

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.engine.ui.hud import HUD
    from src.framework.entities.player import Player
    from src.framework.stage.checkpoint import Checkpoint
    from src.framework.stage.stage_loader import StageData


class ProgressionSystem:
    def __init__(self, context: GameContext) -> None:
        self._context = context
        self._stage_complete: bool = False
        self._complete_timer: float = 0.0
        # AUD-602 — candado de disparo único para el cierre del nivel.
        #
        # Sin él, `update_complete_timer` devolvía True **en todos los
        # fotogramas** una vez agotado el temporizador (el contador seguía
        # bajando sin fondo y `<= 0` seguía siendo cierto), y la escena,
        # que emite STAGE_COMPLETE cada vez que recibe True, re-publicaba
        # el evento cada frame hasta fin de sesión — medido por la campaña
        # de playtesting: 1.255 emisiones en un solo episodio.
        self._complete_fired: bool = False

    def process_checkpoints(
        self, player: Player, stage: StageData,
        checkpoints: list[Checkpoint], hud: HUD | None,
        stage_key: str = "",
    ) -> pygame.Vector2 | None:
        """AUD-156 — `stage_key` es la identidad única del escenario.

        Se pasa desde la escena porque aquí sólo hay `StageData`, y el
        `stage_id` del TMX no siempre coincide con el que el resto del juego
        usa: `lobby_datacenter` guarda `stage_template` en su mapa. Guardar con
        un identificador y buscarlo con otro es lo que dejaba al jugador al
        principio del nivel al cargar. Por defecto cae al del mapa para no
        romper a quien llame a este método con la firma vieja.
        """
        if stage is None or player is None:
            return None
        clave = stage_key or stage.stage_id
        checkpoint_position: pygame.Vector2 | None = None
        for cp in checkpoints:
            if not cp.is_activated and cp.check_collision(player.rect):
                # AUD-502 — el punto de reaparición es la ESQUINA SUPERIOR
                # IZQUIERDA de la caja del jugador, la misma convención que
                # `Player.position`/`set_spawn`. Guardar el centro del
                # checkpoint y que `StageScene.respawn` lo aplicara a la vez
                # como esquina (`position`) y como centro (`rect.center`)
                # dejaba las dos en desacuerdo: `position` gana en el
                # siguiente fotograma, así que el jugador reaparecía con los
                # pies media caja por debajo de donde debía.
                checkpoint_position = pygame.Vector2(
                    cp.rect.centerx - player.ANCHO_DE_PIE / 2.0,
                    cp.rect.bottom - player.ALTO_DE_PIE,
                )
                self._context.event_bus.emit(Events.SFX_CHECKPOINT)
                # AUD-439 — hasta el máximo **del jugador**, no hasta la
                # constante. `Player.max_health` suma reliquias y árbol
                # (AUD-293), así que curar contra `PLAYER_MAX_HEALTH` dejaba a
                # quien se hubiera mejorado permanentemente por debajo de su
                # tope, sin ninguna forma de recuperar esos corazones en un
                # punto de control.
                tope = float(getattr(player, "max_health", settings.PLAYER_MAX_HEALTH))
                if player.current_health < tope:
                    heal_amount = tope - player.current_health
                    player.heal(heal_amount)
                    self._context.event_bus.emit(
                        Events.PLAYER_HEALED, amount=heal_amount
                    )
                self._context.event_bus.emit(
                    Events.SAVE_REQUESTED,
                    stage_id=clave,
                    stage_index=self._context.scene_manager.stage_index,
                    # AUD-502 — misma convención que `checkpoint_position` de
                    # arriba (esquina superior izquierda), no `rect.center`.
                    # `_aplicar_partida_pendiente` ya recoloca con
                    # `set_spawn`, que trata su argumento como esquina; guardar
                    # el centro y cargarlo como esquina desplazaba al jugador
                    # media caja al recuperar una partida.
                    checkpoint_x=checkpoint_position.x,
                    checkpoint_y=checkpoint_position.y,
                    health=player.current_health,
                    # AUD-439 — se guarda el máximo real; anotar la constante
                    # hacía que recargar la partida declarase el tope de
                    # fábrica y perdiera los corazones ganados.
                    max_health=tope,
                )
                if hud is not None:
                    hud.trigger_save_notification()
        return checkpoint_position

    def check_next_trigger(self, player: Player, stage: StageData) -> bool:
        if not self._stage_complete and stage.next_trigger is not None:
            if player.rect.colliderect(stage.next_trigger):
                self._stage_complete = True
                self._complete_timer = 2.9
                return True
        return False

    def check_boss_defeat(self, stage: StageData) -> bool:
        if self._stage_complete:
            return False
        for entity in stage.entity_list:
            if (
                isinstance(entity, BossBase)
                and not entity.is_alive
                and entity.death_timer <= 0
                and not entity.completion_fired
            ):
                entity.completion_fired = True
                self._stage_complete = True
                self._complete_timer = 2.9
                return True
        return False

    def update_complete_timer(self, dt: float) -> bool:
        """True una sola vez, cuando el temporizador de cierre llega a cero.

        AUD-602 — antes devolvía True para siempre a partir del agotamiento:
        el temporizador se decrementaba sin fondo y su condición seguía
        siendo cierta en cada frame posterior, así que quien lo consultara
        emitía el cierre del nivel una y otra vez. El candado hace que la
        segunda llamada y todas las siguientes devuelvan False.
        """
        if not self._stage_complete or self._complete_fired:
            return False
        self._complete_timer -= dt
        if self._complete_timer <= 0:
            self._complete_fired = True
            return True
        return False

    @property
    def stage_complete(self) -> bool:
        return self._stage_complete

    @stage_complete.setter
    def stage_complete(self, value: bool) -> None:
        self._stage_complete = value

    @property
    def complete_timer(self) -> float:
        return self._complete_timer

    def reset(self) -> None:
        self._stage_complete = False
        self._complete_timer = 0.0
        self._complete_fired = False

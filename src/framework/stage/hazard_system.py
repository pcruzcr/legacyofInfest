from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core.events import Events
from src.engine.scenes.game_over_scene import GameOverScene
from src.framework.stage.interactable_system import EVENTO_DISPARADOR

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.framework.entities.player import Player
    from src.framework.stage.stage_loader import StageData


class HazardSystem:
    def __init__(self, context: GameContext) -> None:
        self._context = context
        self._death_timer: float = 0.0
        self._pending_death: bool = False
        # AUD-135 — los eventos que ya se han disparado en este escenario.
        #
        # Se guardan en vez de resolverse al vuelo porque el interruptor puede
        # sonar antes de que el jugador entre en la sala inundable: sin memoria,
        # el agua no arrancaría nunca y el interruptor parecería roto.
        self._eventos_vistos: set[str] = set()
        bus = getattr(context, "event_bus", None)
        if bus is not None:
            bus.subscribe(EVENTO_DISPARADOR, self._al_dispararse)

    # -- inundaciones ----------------------------------------------
    def _al_dispararse(self, nombre: str = "", **_datos: object) -> None:
        if nombre:
            self._eventos_vistos.add(str(nombre))

    def arrancar_por_evento(self, evento: str, stage: StageData | None = None) -> int:
        """Pone en marcha las zonas que esperaban `evento`. Devuelve cuántas."""
        if not evento:
            return 0
        self._eventos_vistos.add(evento)
        if stage is None:
            return 0
        arrancadas = 0
        for hz in stage.hazard_zones:
            if hz.arranca_con == evento and not hz.activa:
                hz.arrancar()
                arrancadas += 1
        return arrancadas

    def update(
        self, dt: float, player: Player, stage: StageData,
    ) -> None:
        # El agua sube aunque el jugador esté muriendo: si se congelara durante
        # los 0,3 s de la muerte, la altura dependería de cuántas veces se ha
        # muerto uno, y el nivel dejaría de ser el mismo para todos.
        self._subir_las_inundaciones(dt, stage)

        if self._pending_death:
            self._death_timer -= dt
            if self._death_timer <= 0:
                self._context.event_bus.emit(Events.PLAYER_DIED)
                self._context.scene_manager.push(
                    GameOverScene(self._context, self._context.scene_manager.current)
                )
                self._pending_death = False
            return

        trigger_rect = player.rect.inflate(0, 2)

        for mt in stage.message_triggers:
            if not mt.triggered and trigger_rect.colliderect(mt.rect):
                mt.triggered = True
                # AUD-244 — un disparador puede pedir una conversación, no sólo
                # un cartel. `StageLoader` lee `dialogue_tree_id` desde AUD-127
                # y aquí se ignoraba, así que declararlo en un mapa no hacía
                # nada y no avisaba de nada.
                arbol = getattr(mt, "dialogue_tree_id", "")
                if arbol:
                    self._context.event_bus.emit(
                        Events.SHOW_DIALOGUE, tree_id=arbol,
                    )
                else:
                    self._context.event_bus.emit(
                        Events.SHOW_MESSAGE, text=mt.text, duration=8.0
                    )

        for hz in stage.hazard_zones:
            hz.timer = max(0.0, hz.timer - dt)
            if hz.timer > 0.0:
                continue
            if trigger_rect.colliderect(hz.rect) and player.rect is not None:
                player.apply_damage(hz.damage, player.rect.center)
                hz.timer = hz.cooldown
                self._context.event_bus.emit(Events.SFX_HAZARD_ZONE)

        for dp in stage.death_pits:
            if trigger_rect.colliderect(dp.rect):
                self._kill_player()

    def _subir_las_inundaciones(self, dt: float, stage: StageData) -> None:
        for hz in stage.hazard_zones:
            if not getattr(hz, "sube_de_verdad", False):
                continue
            if not hz.activa and hz.arranca_con in self._eventos_vistos:
                hz.arrancar()
            hz.avanzar(dt)

    def _kill_player(self) -> None:
        self._pending_death = True
        self._death_timer = 0.3

    def reset(self, stage: StageData | None = None) -> None:
        self._pending_death = False
        self._death_timer = 0.0
        self._eventos_vistos.clear()
        if stage is not None:
            for hz in stage.hazard_zones:
                reiniciar = getattr(hz, "reiniciar", None)
                if callable(reiniciar):
                    reiniciar()

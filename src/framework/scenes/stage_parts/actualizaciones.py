"""Las actualizaciones periféricas de `StageScene` — AUD-351.

Por qué existe este módulo
==========================
`stage_scene.py` volvió a rondar su presupuesto de líneas y el candidato
natural a salir era la familia `_update_*` que alimenta los periféricos:
audio dinámico, HUD, efectos, luz, logros, temporizadores, minimapa y
estelas. Son ocho métodos que `update()` dispara al final de cada fotograma
y que no participan en la simulación: leen el estado de la escena y lo
traducen a la interfaz.

Es un mixin por la misma razón que el resto de `stage_parts/` (AUD-152):
mover el texto sin tocar la orquestación. `self` sigue siendo la misma
escena y los métodos conservan sus nombres, así que las subclases de los
estudiantes —y el MRO que las prueba— no cambian.

Qué NO vive aquí
-----------------
* `_update_gameplay` — la simulación (jugador, físicas, colisiones) se queda
  en `StageScene` junto con `update`, que decide el orden.
* `_update_camera_map`, `_dibujar_bloques`, `_montar_reloj_musical` — mezclan
  montaje y pintado; saldrán con su propio grupo cohesivo si el presupuesto
  vuelve a agotarse.
"""

from __future__ import annotations

import pygame

from src.engine.core.inventory import get_inventory
from src.engine.input.action_map import Action
from src.framework.entities.boss_base import BossBase
from src.framework.entities.enemy_base import EnemyBase


class ActualizacionesDeEscenario:
    """Las 8 actualizaciones periféricas del escenario, movidas de
    `StageScene` en AUD-351 sin cambiar una línea de su texto.

    Espera de la escena: `_dynamic_music`, `_stage_data`, `_hud`, `_player`,
    `_score`, `_subtitles`, `_msg_box`, `_banner`, `_reloj_musical`,
    `_speedrun`, `_fantasma`, `_hazards`, `_tutorial`, `_particle_system`,
    `_damage_numbers`, `_post_processing`, `_ambient_particles`, `_reloj`,
    `_weather`, `_dialogue`, `_niebla`, `_lighting`, `_player_light`,
    `_achievements`, `_minimap`, `_checkpoints`, `_trail_system`,
    `_enemy_trail_system`, `_progression` y `context` — las pone
    `StageScene.__init__`/`on_enter`. No se instancia suelto.
    """

    def _update_audio(self, dt: float) -> None:
        if self._dynamic_music is None:
            return
        stage = self._stage_data
        has_boss = any(isinstance(e, BossBase) and e.is_alive for e in stage.entity_list)
        has_enemies = any(isinstance(e, EnemyBase) and e.is_alive for e in stage.entity_list)
        intensity = self._dynamic_music.detect_intensity_from_state(has_boss, has_enemies)
        self._dynamic_music.set_intensity(intensity)

    def _update_hud_ui(self, dt: float) -> None:
        stage = self._stage_data
        im = self.input
        if self._hud:
            boss_found = False
            for entity in stage.entity_list:
                if isinstance(entity, BossBase) and entity.is_alive:
                    self._hud.set_boss_hud(
                        entity.boss_name, entity.current_health,
                        entity.phase_max_health,
                        getattr(entity, "current_phase", 0) + 1,
                        getattr(entity, "phase_count", 1),
                    )
                    boss_found = True
                    break
            if not boss_found:
                self._hud.clear_boss_hud()
            self._hud.set_combo_count(self._player.combo_count)
            self._hud.set_special_meter(self._player.special_meter, self._player.special_meter_max)
            self._hud.set_estamina(self._player.estamina, self._player.estamina_max)
            # AUD-260: `-1` significa «este escenario no lo pide» y la barra
            # no se dibuja, igual que la estamina con máximo 0.
            # AUD-274 — la franja del Boss Rush. Con el modo apagado se manda
            # progreso vacío y el HUD no dibuja nada, así que la partida normal
            # no puede notarlo.
            modo_rush = self._boss_rush_activo()
            self._hud.set_boss_rush(
                modo_rush.progress if modo_rush else "",
                modo_rush.current_name if modo_rush else "",
                modo_rush.score if modo_rush else 0,
                modo_rush.golpes_totales if modo_rush else 0,
            )
            self._hud.set_tiempo_bala(
                self._tiempo_bala.fraccion
                if self._tiempo_bala.reserva_maxima > 0.0 else -1.0,
                self._tiempo_bala.activo,
            )
            # AUD-219: el saldo se lee del inventario, no se guarda aparte —
            # las monedas *son* el objeto `coin`, y duplicar el número acabaría
            # con los dos desincronizados en cuanto la tienda cobre algo.
            self._hud.set_score(self._score.score, get_inventory().coins)
            # AUD-439 — el tope de vida se empuja como el resto de los valores
            # del jugador. `HUD` lo fijaba una vez desde la constante, así que
            # los corazones ganados con reliquias o con el árbol no se
            # dibujaban nunca.
            if self._player is not None:
                self._hud.set_salud_maxima(self._player.max_health)
            # AUD-575 (GAP-071 resuelto) — el aire del buceo llega al HUD
            # desde el `ControlDeNado` de la escena: ratio real bajo el
            # agua, y -1 (barra oculta) fuera de ella. La alarma visual y
            # sonora del tramo bajo la dispara el propio HUD cuando
            # `avisando` es verdadero.
            if getattr(self, "_nado", None) is not None and self._nado.aire_maximo > 0.0:
                ratio = self._nado.aire / self._nado.aire_maximo if self._nado.en_agua else -1.0
                self._hud.set_oxigeno(ratio, self._nado.avisando)
            self._hud.update(dt)
        self._subtitles.update(dt)
        if self._msg_box:
            self._msg_box.update(dt)
            if self._msg_box.is_dismiss_on_confirm and im.is_action_just_pressed(Action.CONFIRM):
                self._msg_box.hide()
        if self._banner:
            self._banner.update(dt)

    def _update_vfx(self, dt: float) -> None:
        # AUD-137: el reloj musical va con tiempo REAL. El tiempo bala
        # ralentiza el mundo y la música sigue sonando igual; alimentarlo con
        # el `dt` escalado desincronizaría el nivel entero cada vez que algo
        # se ralentiza. Es el mismo error que AUD-118/119 quitó del reloj.
        if self._reloj_musical is not None:
            clock = self.context.clock
            self._reloj_musical.update(
                getattr(clock, "unscaled_dt", dt) if clock is not None else dt,
            )
        self._speedrun.update(dt)
        if self._fantasma is not None and self._player is not None:
            self._fantasma.grabar_si_toca(
                dt, self._player.position.x, self._player.position.y)
        # AUD-249: la cámara viaja al sistema de peligros porque el borde que
        # mata en un `ScrollZone` se mueve con ella.
        self._hazards.update(dt, self._player, self._stage_data, self._camera)
        self._tutorial.update(dt, self.input)
        self._particle_system.update(dt)
        self._damage_numbers.update(dt)
        self._post_processing.update(dt)
        self._ambient_particles.update(dt, self._camera.offset)
        # AUD-362 — se avanza la simulación, no el reloj suelto: el calendario
        # se lleva detectando la vuelta de la hora, así que un reloj movido por
        # fuera dejaría los días sin contar.
        if not self._reloj.congelado:
            self._simulacion.update(dt)
            self._aplicar_hora()
        self._weather.update(dt, self._camera.offset)
        self._dialogue.update(dt)
        # AUD-338 — sin esto el respiro de la niebla de guerra nunca avanzaría:
        # `_niebla` se crea en `_setup_ambiente` y `draw` se llama en el pintado,
        # pero nadie movía su reloj interno. El velo animado se queda congelado
        # en la fase cero, que es exactamente el velo estático de siempre.
        if self._niebla is not None:
            self._niebla.update(dt)

    def _update_lighting(self, dt: float) -> None:
        stage = self._stage_data
        if self._player is None:
            return
        combat = any(isinstance(e, EnemyBase) and e.is_alive for e in stage.entity_list)
        if self._player_light is None:
            self._player_light = self._lighting.get_player_light(self._player.position, combat)
            self._lighting.add_light(self._player_light)
        else:
            self._player_light.position = self._player.position
            self._player_light.intensity = 0.9 if combat else 0.6
            self._player_light.radius = 100 if combat else 60
        self._lighting.update(dt, self._camera.offset)

    def _update_tracking(self, dt: float) -> None:
        self._achievements.update_notifications(dt)
        get_inventory().update_notifications(dt)
        if not self._player_spawned or self._player is None:
            return
        self._stage_start_time += dt
        old_health = self._last_player_health
        if old_health > self._player.current_health:
            self._damage_taken_this_stage += old_health - self._player.current_health
        self._last_player_health = self._player.current_health
        if self._player.current_health <= 0.5 and self._player.current_health > 0:
            self._achievements.mark_survived_low_health()

    def _update_timers(self, dt: float) -> None:
        if self._progression.stage_complete:
            if self._hud:
                self._hud.clear_boss_hud()
            if self._msg_box:
                self._msg_box.update(dt)
            if self._banner:
                self._banner.update(dt)

    def _update_minimap(self) -> None:
        if self._player is None or self._stage_data is None:
            return
        stage = self._stage_data
        enemy_positions = [
            (e.position.x, e.position.y)
            for e in stage.entity_list
            if isinstance(e, EnemyBase) and e.is_alive
        ]
        boss_positions = [
            (e.position.x, e.position.y)
            for e in stage.entity_list
            if isinstance(e, BossBase) and e.is_alive
        ]
        cp_positions = [(cp.rect.centerx, cp.rect.centery) for cp in self._checkpoints]
        activated = {i for i, cp in enumerate(self._checkpoints) if cp.is_activated}
        self._minimap.update(
            player_pos=(self._player.position.x, self._player.position.y),
            player_dir=self._player.facing_direction,
            enemy_positions=enemy_positions,
            boss_positions=boss_positions,
            checkpoint_positions=cp_positions,
            activated_checkpoints=activated,
        )
        explore_rect = pygame.Rect(
            self._player.rect.centerx - 80, self._player.rect.centery - 60, 160, 120,
        )
        self._minimap.explore_rect(explore_rect)

    def _update_trail(self, dt: float) -> None:
        if self._player is not None:
            is_dashing = getattr(self._player, "_dash_timer", 0) > 0
            is_moving = abs(self._player.velocity.x) > 50
            if is_dashing or (is_moving and not self._player.is_grounded):
                self._trail_system.capture(self._player)
        self._trail_system.update(dt)

        self._capture_enemy_trails(dt)
        self._enemy_trail_system.update(dt)

"""
Las señales del escenario: lo que la escena escucha en el bus.

Extraído de `stage_scene.py` en AUD-152 sin cambiar una línea de lógica.

Son dos familias que se montan y se desmontan juntas:

* **efectos visuales** — partículas de golpe y de muerte, números de daño,
  sacudida de cámara, destellos y bloom puntual;
* **sonido** — treinta y ocho eventos mapeados a nombres de muestra, más el
  guardado en checkpoint.

Se guardan las referencias en `_vfx_handlers` y `_sfx_handlers` porque el bus
las mantiene **débilmente**: sin esos diccionarios, el recolector de basura se
lleva los cierres en cuanto termina `_subscribe_event_handlers` y el juego se
queda mudo sin un solo error en consola.
"""
from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.stage.interactable_system import EVENTO_RECOGIDO
from src.framework.vfx.hit_effects import HitEffects


class SenalesDeEscenario:
    """Suscripción, baja y reproducción de sonido de la escena.

    Espera de la escena: `context.event_bus`, `_particle_system`,
    `_damage_numbers`, `_camera`, `_post_processing`, `_player`, audio,
    `_interactables`, `_vfx_handlers` y `_sfx_handlers`.
    """

    #: Lado del recogible de monedas, en píxeles. Del tamaño de una baldosa
    #: para que se vea y se coja al pasar sin tener que buscarlo.
    _BOTIN_TAM: int = 16

    def _soltar_botin(self, entity_id: str, pos: Any, skill: str = "") -> None:
        """Deja el botín donde murió el enemigo: monedas y, si lo declara, su
        habilidad (AUD-218, AUD-238).

        La cantidad de monedas la decide `score_system.coins_for()`, que es
        donde vive la tabla por tipo — la misma lectura de `entity_id` que usa
        la puntuación, para no tener dos formas de decir «esto es un jefe».
        """
        interactables = getattr(self, "_interactables", None)
        if interactables is None:
            return
        from src.engine.core.score_system import coins_for
        from src.framework.stage.interactables import Recogible

        lado = self._BOTIN_TAM
        cx = int(float(pos[0]))
        cy = int(float(pos[1]))
        interactables.soltar_botin(entity_id, Recogible(
            rect=pygame.Rect(cx - lado // 2, cy - lado // 2, lado, lado),
            item_id="coin",
            automatico=True,
            cantidad=coins_for(entity_id),
        ))
        if skill:
            # AUD-238: la reliquia del jefe, **además** de las monedas y no en
            # su lugar. Se deja un poco a la derecha para que no quede
            # exactamente debajo de ellas y se vean las dos.
            #
            # Se descarta lo que no está en el catálogo: un jefe de una entrega
            # con `skill_drop = "skill_volar"` dejaría en el suelo algo que
            # `collect()` rechaza, y el jugador lo cogería sin que pasara nada.
            from src.engine.core.inventory import get_inventory
            if get_inventory().get_def(skill) is not None:
                interactables.recogibles.append(Recogible(
                    rect=pygame.Rect(cx + lado, cy - lado // 2, lado, lado),
                    item_id=skill,
                    automatico=True,
                ))

    def _subscribe_event_handlers(self) -> None:
        # GAP-020 — recogibles que nunca llegaban al inventario.
        #
        # `InteractableSystem._recoger()` guardaba el objeto en el llavero y
        # emitía `EVENTO_RECOGIDO`, pero nadie escuchaba ese evento. Un
        # `Recogible` con `item_id="heart_vessel"` o `"swift_feather"` —objetos
        # que `Recogible` documenta como «si coincide con un objeto de
        # `engine.core.inventory` se aplica su efecto»— se recogía, mostraba el
        # aviso, y la mejora permanente se perdía en silencio: el inventario
        # (que persiste a JSON) nunca recibía la llamada a `collect()`.
        #
        # Aquí se cierra el circuito: quien escuche la recolección decide si el
        # objeto es una mejora permanente o una llave del escenario.
        def _on_item_picked(**data: Any) -> None:
            item_id = str(data.get("item_id", ""))
            if not item_id:
                return
            cantidad = int(data.get("cantidad", 1))
            from src.engine.core.inventory import get_inventory
            if get_inventory().collect(item_id, cantidad):
                # El recogible era una mejora permanente del inventario; el
                # llavero no la necesita como llave.
                self._interactables.llavero.gastar(item_id)

        self.context.event_bus.subscribe(EVENTO_RECOGIDO, _on_item_picked)
        self._vfx_handlers[EVENTO_RECOGIDO] = _on_item_picked

        def _on_enemy_died(**data: Any) -> None:
            pos = data.get("position", (0, 0))
            self._particle_system.get_emitter("death").emit(
                float(pos[0]), float(pos[1]), HitEffects.DEATH,
            )
            # GAP-029 / AUD-218 — el botín que faltaba.
            #
            # La economía tenía catálogo y API (`coin`, `buy`, `sell`) y ningún
            # sitio donde ganar una moneda: este manejador sólo lanzaba
            # partículas. Sin esto, el saldo del jugador no puede subir jugando
            # y la única forma de comprar era editar `data/inventory.json`.
            #
            # Se suelta **un** recogible con la cantidad dentro, no N monedas:
            # veinte objetos en el suelo por un jefe cuestan colisiones cada
            # fotograma y tapan el sitio donde murió.
            self._soltar_botin(
                str(data.get("entity_id", "")), pos,
                str(data.get("skill_drop", "")),
            )

        def _on_hit_connect(**data: Any) -> None:
            pos = data.get("pos", [0, 0])
            dmg = data.get("damage", 1.0)
            self._particle_system.get_emitter("hits").emit(
                pos[0], pos[1], HitEffects.get_for_damage(dmg),
            )
            self._damage_numbers.add(pos[0], pos[1], str(int(dmg)))

        def _on_enemy_hit(**data: Any) -> None:
            pos = data.get("pos", [0, 0])
            dmg = data.get("damage", 1.0)
            self._particle_system.get_emitter("blood").emit(
                pos[0], pos[1], HitEffects.get_blood_for_damage(dmg),
            )
            self._camera.apply_shake(amplitude=1.5, duration=0.06)

        def _on_player_damaged(**data: Any) -> None:
            src = data.get("source", (0, 0))
            self._particle_system.get_emitter("blood").emit(
                float(src[0]), float(src[1]), HitEffects.BLOOD_BIG,
            )
            self._camera.apply_shake(amplitude=2.0, duration=0.1)
            self._post_processing.flash((255, 50, 50), alpha=180, duration=0.15)
            health_pct = self._player.current_health / max(settings.PLAYER_MAX_HEALTH, 1)
            self._post_processing.set_damage_vignette(max(0, 0.5 - health_pct * 0.5))
            # AUD-215 — aberración cromática en el impacto. El golpe es más
            # fuerte cuanta menos vida queda: al 100 % apenas se insinúa y con
            # la barra en rojo la lente se descompone. Es la misma señal que ya
            # dan la viñeta de daño y la sacudida, en un canal que el jugador
            # lee sin mirar la barra.
            #
            # Si no hay GL esto no hace nada: `App` es la única que lo recoge,
            # y sin tarjeta nadie consume el impulso.
            from src.engine.core import gpu_effects
            gpu_effects.request_chromatic_aberration(0.35 + 0.45 * (1.0 - health_pct))

        def _on_vfx_parry(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("parry").emit(
                float(pos[0]), float(pos[1]), HitEffects.PARRY,
            )
            self._camera.apply_shake(amplitude=3.0, duration=0.15)
            self._post_processing.flash((100, 200, 255), alpha=120, duration=0.1)
            self._post_processing.set_bloom(0.3, duration=0.15)

        def _on_vfx_charge(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("charge").emit(
                float(pos[0]), float(pos[1]), HitEffects.CHARGE_GLOW,
            )

        def _on_vfx_slam(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("slam").emit(
                float(pos[0]), float(pos[1]), HitEffects.SPARK_BIG,
            )
            self._camera.apply_shake(amplitude=4.0, duration=0.2)

        def _on_vfx_ultimate(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("parry").emit(
                float(pos[0]), float(pos[1]), HitEffects.SPARK_BIG,
            )
            self._post_processing.set_bloom(0.8, duration=0.6)
            self._post_processing.flash((255, 255, 255), alpha=255, duration=0.15)
            self._camera.apply_shake(amplitude=5.0, duration=0.4)

        self.context.event_bus.subscribe(Events.SFX_HIT_CONNECT, _on_hit_connect)
        self._vfx_handlers[Events.SFX_HIT_CONNECT] = _on_hit_connect
        self.context.event_bus.subscribe(Events.SFX_ENEMY_HIT, _on_enemy_hit)
        self._vfx_handlers[Events.SFX_ENEMY_HIT] = _on_enemy_hit
        self.context.event_bus.subscribe(Events.ENEMY_DIED, _on_enemy_died)
        self._vfx_handlers[Events.ENEMY_DIED] = _on_enemy_died

        def _on_player_died(**data: Any) -> None:
            pos = data.get("pos", [0, 0])
            self._particle_system.get_emitter("death").emit(
                float(pos[0]), float(pos[1]), HitEffects.get_blood_for_damage(10),
            )
            for _ in range(3):
                self._particle_system.get_emitter("death").emit(
                    float(pos[0]) + random.uniform(-8, 8),
                    float(pos[1]) + random.uniform(-8, 8),
                    HitEffects.get_blood_for_damage(5),
                )
            self._camera.apply_shake(amplitude=8.0, duration=0.5)
            self._post_processing.flash((255, 0, 0), alpha=180, duration=0.3)

        self.context.event_bus.subscribe(Events.PLAYER_DAMAGED, _on_player_damaged)
        self._vfx_handlers[Events.PLAYER_DAMAGED] = _on_player_damaged
        self.context.event_bus.subscribe(Events.PLAYER_DIED, _on_player_died)
        self._vfx_handlers[Events.PLAYER_DIED] = _on_player_died
        self.context.event_bus.subscribe(Events.VFX_PARRY, _on_vfx_parry)
        self._vfx_handlers[Events.VFX_PARRY] = _on_vfx_parry
        self.context.event_bus.subscribe(Events.VFX_CHARGE, _on_vfx_charge)
        self._vfx_handlers[Events.VFX_CHARGE] = _on_vfx_charge
        self.context.event_bus.subscribe(Events.VFX_SLAM, _on_vfx_slam)
        self._vfx_handlers[Events.VFX_SLAM] = _on_vfx_slam
        self.context.event_bus.subscribe(Events.VFX_ULTIMATE, _on_vfx_ultimate)
        self._vfx_handlers[Events.VFX_ULTIMATE] = _on_vfx_ultimate

        def _on_vfx_bubble(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("bubble").emit(
                float(pos[0]), float(pos[1]), HitEffects.BUBBLE,
            )
        self.context.event_bus.subscribe(Events.VFX_BUBBLE, _on_vfx_bubble)
        self._vfx_handlers[Events.VFX_BUBBLE] = _on_vfx_bubble

        def _on_music_stinger(**data: Any) -> None:
            name = data.get("name", "stinger_boss_phase")
            vol = data.get("volume", 0.8)
            # BUG-057: Null guard for audio
            if self.audio is not None:
                self.audio.play_stinger(name, volume=vol)
        self.context.event_bus.subscribe(Events.MUSIC_STINGER, _on_music_stinger)
        self._vfx_handlers[Events.MUSIC_STINGER] = _on_music_stinger

        sfx_map = {
            Events.SFX_PLAYER_JUMP: "sfx_player_jump",
            Events.SFX_PLAYER_LAND: "sfx_player_land",
            Events.SFX_PLAYER_SHORT_ATTACK: "sfx_player_short_attack",
            Events.SFX_PLAYER_LONG_ATTACK: "sfx_player_long_attack",
            Events.SFX_PLAYER_HURT: "sfx_player_hurt",
            Events.SFX_PLAYER_DIE: "sfx_player_die",
            Events.SFX_HIT_CONNECT: "sfx_player_hit_connect",
            Events.SFX_ENEMY_HIT: "sfx_enemies_hit",
            Events.SFX_ENEMY_DIE_SMALL: "sfx_enemies_die_small",
            Events.SFX_ENEMY_DIE_LARGE: "sfx_enemies_die_large",
            Events.SFX_PROJECTILE_FIRE: "sfx_enemies_projectile_fire",
            Events.SFX_CHECKPOINT: "sfx_ui_checkpoint",
            Events.SFX_STAGE_BANNER: "sfx_ui_stage_banner",
            Events.SFX_STAGE_COMPLETE: "sfx_ui_stage_complete",
            Events.SFX_HAZARD_ZONE: "sfx_environment_hazard_zone",
            Events.SFX_PLAYER_FOOTSTEP: "sfx_step",
            Events.SFX_MENU_HOVER: "sfx_select",
            Events.SFX_MENU_CONFIRM: "sfx_select",
            Events.SFX_MENU_CANCEL: "sfx_ui_menu_cancel",
            Events.SFX_PLAYER_PARRY: "sfx_parry",
            Events.SFX_PLAYER_CROUCH: "sfx_player_crouch",
            Events.SFX_PLAYER_HEAL: "sfx_ui_heart_restore",
            Events.SFX_BOSS_HIT: "sfx_boss_hit",
            Events.SFX_UI_GAME_OVER: "sfx_ui_game_over",
            Events.SFX_ENVIRONMENT_SCREEN_SHAKE: "sfx_environment_screen_shake",
            Events.SFX_ENVIRONMENT_ONE_WAY_PLATFORM: "sfx_environment_one_way_platform",
            Events.SFX_BOSS_PHASE_CHANGE: "sfx_bosses_phase_change",
            Events.SFX_ENEMIES_PROJECTILE_HIT_WALL: "sfx_enemies_projectile_hit_wall",
            Events.SFX_BOSSES_GAVILAN_DIVE: "sfx_bosses_gavilan_dive",
            Events.SFX_BOSSES_GAVILAN_MASK_BEAM: "sfx_bosses_gavilan_mask_beam",
            Events.SFX_BOSSES_PABURU_EYE_BEAM: "sfx_bosses_paburu_eye_beam",
            Events.SFX_BOSSES_PABURU_WAVE: "sfx_bosses_paburu_wave",
            Events.SFX_BOSSES_RELIC_APPEAR: "sfx_bosses_relic_appear",
            Events.SFX_BOSSES_REY_SPIT: "sfx_bosses_rey_spit",
            Events.SFX_BOSSES_REY_SPLIT: "sfx_bosses_rey_split",
            Events.SFX_BOSSES_VENADO_CHARGE: "sfx_bosses_venado_charge",
            Events.SFX_BOSSES_VENADO_STOMP: "sfx_bosses_venado_stomp",
            Events.SFX_BOSSES_VENADO_VINE: "sfx_bosses_venado_vine",
        }
        for evt, sname in sfx_map.items():
            handler = self._make_sfx_handler(sname)
            self.context.event_bus.subscribe(evt, handler)
            # Retained here so the bus's weak reference stays alive.
            self._sfx_handlers[evt] = handler

        # SAVE_REQUESTED handler — persists game on checkpoint / save & quit
        def _on_save_requested(**data: Any) -> None:
            sm = self.context.save_manager
            if sm is not None:
                sm.auto_save(
                    stage_id=data.get("stage_id", ""),
                    stage_index=data.get("stage_index", 0),
                    checkpoint_x=data.get("checkpoint_x", 0),
                    checkpoint_y=data.get("checkpoint_y", 0),
                    health=data.get("health", 100),
                    max_health=data.get("max_health", 100),
                )
        self.context.event_bus.subscribe(Events.SAVE_REQUESTED, _on_save_requested)
        self._vfx_handlers[Events.SAVE_REQUESTED] = _on_save_requested

    def _make_sfx_handler(self, sound_name: str) -> Callable[..., None]:
        """Build an event handler that plays ``sound_name``.

        AUD-032: this was previously a closure factory defined *inside* the loop
        that used it, with the inner function and the loop variable sharing the
        name ``handler``. It worked, but it tripped B023 and required a careful
        read to see that it did — the exact shape that hides a real late-binding
        bug the next time someone edits it. A named method takes the sound as a
        parameter, so the binding is explicit and unmistakable.
        """
        def handler(**data: Any) -> None:
            volume = 1.0
            if "damage" in data:
                # Slight random variation so repeated hits do not sound robotic.
                volume = 0.8 + random.random() * 0.4
            pos = data.get("pos")
            if pos is not None:
                self._play_sfx_spatial(sound_name, pos[0], volume=volume)
            else:
                self._play_sfx_named(sound_name, volume=volume)
        return handler

    def _unsubscribe_all_handlers(self) -> None:
        for evt, handler in self._sfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._sfx_handlers.clear()
        for evt, handler in self._vfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._vfx_handlers.clear()

    def _play_sfx_named(self, name: str, volume: float = 1.0) -> None:
        audio = self.audio
        if audio is not None:
            audio.play_sfx(name, volume=volume)

    def _play_sfx_spatial(self, name: str, world_x: float, volume: float = 1.0) -> None:
        audio = self.audio
        if audio is not None:
            screen_center_x = self._camera.offset.x + settings.INTERNAL_WIDTH / 2
            audio.play_sfx_at(name, world_x, screen_center_x, volume=volume)


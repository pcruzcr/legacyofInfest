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

import logging
import random
from typing import Any

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.core.experience import ExperienceSystem
from src.framework.stage.interactable_system import EVENTO_RECOGIDO, EVENTO_WARP
from src.framework.vfx.hit_effects import HitEffects


class SenalesDeEscenario:
    """Suscripción, baja y reproducción de sonido de la escena.

    Espera de la escena: `context.event_bus`, `_particle_system`,
    `_damage_numbers`, `_camera`, `_post_processing`, `_player`, audio,
    `_interactables`, `_hud`, `_vfx_handlers` y `_sfx_handlers`.
    """

    def _subscribe_event_handlers(self) -> None:
        # GAP-020 — recogibles que nunca llegaban al inventario.
        #
        # `InteractableSystem._recoger()` guardaba el objeto en el llavero y
        # emitía `EVENTO_RECOGIDO`, pero nadie escuchaba ese evento. Un
        # `Recogible` con `item_id="heart_vessel"` se recogía, mostraba el
        # aviso, y la mejora permanente se perdía en silencio: el inventario
        # (que persiste a JSON) nunca recibía la llamada a `collect()`.
        #
        # AUD-251 — y el mismo hueco tenía la otra puerta: `give_item:` en un
        # diálogo emitía `ITEM_COLLECTED` y **nadie escuchaba**. Un manejador
        # atiende a las dos formas de recibir algo —catálogo al inventario, el
        # resto al llavero— para que no puedan desincronizarse.
        def _on_item_picked(**data: Any) -> None:
            item_id = str(data.get("item_id", ""))
            if not item_id:
                return
            cantidad = int(data.get("cantidad", 1))
            from src.engine.core.inventory import get_inventory
            if get_inventory().collect(item_id, cantidad):
                self._interactables.llavero.gastar(item_id)
            else:
                self._interactables.llavero.coger(item_id)

            # AUD-281 — la recompensa, que hasta hoy era sólo un número que
            # subía en una esquina.
            #
            # Recoger algo era el único acto del juego sin respuesta: el golpe
            # tiene chispas, sacudida y hit-stop; la moneda no tenía nada. Y es
            # la acción que más veces se repite en una partida.
            #
            # Va aquí y no en `InteractableSystem` porque el sistema no conoce
            # ni las partículas ni la cámara, y dárselos para esto invertiría la
            # dirección de dependencia por un efecto visual.
            pos = data.get("pos")
            if pos is not None:
                self._particle_system.get_emitter("pickup").emit(
                    float(pos[0]), float(pos[1]), HitEffects.PICKUP,
                )
                # `sfx_select` y no un nombre inventado: no hay fichero de
                # recogida en `assets/sfx/` y bautizar uno que no existe es lo
                # que AUD-133 tuvo que deshacer. Cuando el sonido exista, se
                # cambia esta línea y ya está.
                self._play_sfx_spatial("sfx_select", float(pos[0]), volume=0.5)
            if self._hud is not None:
                self._hud.pulso_de_recogida()

        for evento in (EVENTO_RECOGIDO, Events.ITEM_COLLECTED):
            self.context.event_bus.subscribe(evento, _on_item_picked)
            self._vfx_handlers[evento] = _on_item_picked

        # AUD-559 — el otro lado de `Inventory.usar()`: `InventoryScene`
        # gasta la unidad y emite, sin saber si hay un jugador vivo a
        # quien curar (es un singleton, también se abre desde el título).
        # Aquí sí lo hay — o no se llegaría a suscribir esto.
        def _on_item_consumed(**data: Any) -> None:
            if self._player is None:
                return
            cantidad = float(data.get("heal_hp", 0.0))
            if cantidad <= 0.0:
                return
            self._player.heal(cantidad)
            self.context.event_bus.emit(Events.PLAYER_HEALED, amount=cantidad)

        self.context.event_bus.subscribe(Events.ITEM_CONSUMED, _on_item_consumed)
        self._vfx_handlers[Events.ITEM_CONSUMED] = _on_item_consumed

        def _on_warp(**data: Any) -> None:
            """AUD-287 — el salto de una punta del mapa a la otra.

            Lo aplica la escena y no `InteractableSystem` porque el jugador y la
            cámara son suyos. Y hay que hacer **tres** cosas, no una:

            1. mover al jugador —a sus pies, que es lo que declara el mapa—;
            2. **cortarle la velocidad**: llegar al destino cayendo a 500 px/s
               lo atraviesa el suelo antes de que la colisión pueda resolverlo;
            3. **saltar la cámara** en vez de dejar que interpole. Con el LERP
               normal, un warp de 3.000 px produce medio segundo de barrido a
               toda velocidad por el nivel, que marea y además enseña partes del
               mapa que el diseño no quería enseñar todavía.
            """
            destino = data.get("destino")
            if destino is None or self._player is None:
                return
            self._player.rect.midbottom = (int(destino[0]), int(destino[1]))
            self._player.position.update(float(self._player.rect.x),
                                         float(self._player.rect.y))
            self._player.velocity.update(0.0, 0.0)
            self._camera.snap_to_target()
            origen = data.get("origen")
            if origen is not None:
                self._particle_system.get_emitter("warp").emit(
                    float(origen[0]), float(origen[1]), HitEffects.PARRY,
                )
            self._particle_system.get_emitter("warp").emit(
                float(destino[0]), float(destino[1]) - 8.0, HitEffects.PARRY,
            )

        self.context.event_bus.subscribe(EVENTO_WARP, _on_warp)
        self._vfx_handlers[EVENTO_WARP] = _on_warp

        def _on_flag_set(**data: Any) -> None:
            flag = str(data.get("flag", ""))
            if flag:
                self.context.banderas[flag] = True

        self.context.event_bus.subscribe(Events.FLAG_SET, _on_flag_set)
        self._vfx_handlers[Events.FLAG_SET] = _on_flag_set

        # AUD-244 — abrir la conversación que pide un disparador del mapa.
        #
        # `StageLoader` lee `dialogue_tree_id` de los `MessageTrigger` desde
        # AUD-127 y hasta ahora sólo `stage0` hacía algo con él, con árboles
        # escritos a mano en Python. Los otros dieciséis mapas podían declarar
        # una conversación y no ocurría nada, sin aviso.
        #
        # Los árboles se cargan de `data/dialogues/<stage_id>.json` con
        # `DialogueTree.desde_datos`, que existe desde AUD-127 para que un
        # diseñador que no programa pueda escribir un diálogo. Hasta hoy no
        # tenía quien la llamara.
        def _on_show_dialogue(**data: Any) -> None:
            tree_id = str(data.get("tree_id", ""))
            arbol = self._arboles_de_dialogo.get(tree_id)
            if arbol is None:
                # Un identificador que no existe es una errata del mapa, y
                # callarse es justamente lo que hizo que esto tardara meses
                # en verse.
                if tree_id:
                    logging.getLogger(__name__).warning(
                        "diálogo: el mapa pide el árbol '%s' y no está en "
                        "data/dialogues/%s.json", tree_id,
                        getattr(self._stage_data, "stage_id", "?"),
                    )
                return
            if not self._dialogue.active:
                self._dialogue.start_dialogue(arbol)

        self._vfx_handlers[Events.SHOW_DIALOGUE] = _on_show_dialogue

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
            # AUD-282 — la pantalla se va **en el sentido del empujón**: del
            # origen del daño hacia el jugador. Con la sacudida isótropa, un
            # golpe por la izquierda y otro por la derecha se sentían iguales, y
            # saber de qué lado viene es la mitad de la información que un
            # jugador necesita para reaccionar.
            direccion = None
            if self._player is not None:
                direccion = (self._player.rect.centerx - float(src[0]),
                             self._player.rect.centery - float(src[1]))
            self._camera.apply_shake(amplitude=2.0, duration=0.1,
                                     direccion=direccion)
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
            # AUD-282 — un pisotón va hacia abajo y no hay ambigüedad posible:
            # es el caso donde la sacudida direccional se nota más.
            self._camera.apply_shake(amplitude=4.0, duration=0.2,
                                     direccion=(0.0, 1.0))

        # AUD-636 — polvo de aterrizaje. La fuerza (0-1) escala la cantidad:
        # una caída corta levanta poco polvo y una larga una nube. El emisor
        # emite dos ráfagas en vez de inventar un `count` dinámico — el
        # `BurstConfig` es inmutable por diseño.
        def _on_vfx_land_dust(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            fuerza = max(0.0, min(1.0, float(data.get("fuerza", 0.5))))
            self._particle_system.get_emitter("dust").emit(
                float(pos[0]), float(pos[1]), HitEffects.DUST_LAND,
            )
            if fuerza > 0.6:
                self._particle_system.get_emitter("dust").emit(
                    float(pos[0]) + 4, float(pos[1]), HitEffects.DUST_LAND,
                )

        def _on_vfx_jump_dust(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("dust").emit(
                float(pos[0]), float(pos[1]), HitEffects.DUST_JUMP,
            )

        def _on_vfx_kill_flash(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("dust").emit(
                float(pos[0]), float(pos[1]), HitEffects.KILL_FLASH,
            )

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

        def _on_vfx_musgo_step(**data: Any) -> None:
            # AUD-522 — el musgo resbala y hasta ahora no se veía.
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("musgo").emit(
                float(pos[0]), float(pos[1]), HitEffects.MUSGO,
            )
        self.context.event_bus.subscribe(Events.VFX_MUSGO_STEP, _on_vfx_musgo_step)
        self._vfx_handlers[Events.VFX_MUSGO_STEP] = _on_vfx_musgo_step

        # AUD-636 — polvo de aterrizaje/salto y destello de muerte.
        self.context.event_bus.subscribe(Events.VFX_LAND_DUST, _on_vfx_land_dust)
        self._vfx_handlers[Events.VFX_LAND_DUST] = _on_vfx_land_dust
        self.context.event_bus.subscribe(Events.VFX_JUMP_DUST, _on_vfx_jump_dust)
        self._vfx_handlers[Events.VFX_JUMP_DUST] = _on_vfx_jump_dust
        self.context.event_bus.subscribe(Events.VFX_KILL_FLASH, _on_vfx_kill_flash)
        self._vfx_handlers[Events.VFX_KILL_FLASH] = _on_vfx_kill_flash

        def _on_music_stinger(**data: Any) -> None:
            name = data.get("name", "stinger_boss_phase")
            vol = data.get("volume", 0.8)
            # BUG-057: Null guard for audio
            if self.audio is not None:
                self.audio.play_stinger(name, volume=vol)
        self.context.event_bus.subscribe(Events.MUSIC_STINGER, _on_music_stinger)
        self._vfx_handlers[Events.MUSIC_STINGER] = _on_music_stinger

        self._subscribe_sfx_handlers()

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
                    # AUD-251: el checkpoint se lleva las banderas de mundo.
                    zone_flags=dict(getattr(self.context, "banderas", {})),
                    # AUD-267: y la experiencia, que sin esto se perdía al
                    # cerrar el juego aunque hubiera subido jugando.
                    exp_total=ExperienceSystem.get_instance().exp,
                )
        self.context.event_bus.subscribe(Events.SAVE_REQUESTED, _on_save_requested)
        self._vfx_handlers[Events.SAVE_REQUESTED] = _on_save_requested

    def _unsubscribe_all_handlers(self) -> None:
        for evt, handler in self._sfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._sfx_handlers.clear()
        for evt, handler in self._vfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._vfx_handlers.clear()


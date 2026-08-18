"""
El sonido del escenario: qué evento suena, con qué muestra y a qué volumen.

Extraído de `senales.py` en AUD-290 sin cambiar una línea de lógica.

Por qué se parte aquí y no por otro sitio
=========================================
`senales.py` llegó a su presupuesto de 400 líneas y AUD-281..287 lo pasaron a
503. El corte no es por tamaño: es por el eje que ya estaba en el docstring del
módulo original —«son **dos** familias: efectos visuales y sonido»— y que hasta
hoy compartían fichero. Aquí queda la segunda entera: la tabla de treinta y ocho
eventos, la fábrica de manejadores y los dos reproductores.

El resto —partículas, sacudida, destellos, inventario, warp— se queda en
`senales.py`, que es lo que la escena *ve* y no lo que *oye*.

Es un mixin, no un colaborador, por la misma razón que los otros cuatro: las
entregas de estudiantes sobreescriben estos métodos, y con un colaborador esas
subclases dejarían de tener efecto en silencio.
"""
from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

from src.engine.core import settings
from src.engine.core.events import Events

#: AUD-284 — los efectos que apartan la música al sonar.
#:
#: Cuatro, y la lista es corta a propósito. El *ducking* funciona porque es raro:
#: si lo disparase cada golpe, la música pasaría la partida entera subiendo y
#: bajando y el bombeo se oiría más que los propios efectos. Entra aquí lo que
#: ocurre **una vez** y cierra algo:
#:
#: * el logro desbloqueado, que además trae un aviso en pantalla que hay que leer;
#: * el escenario completado;
#: * el Game Over;
#: * el cambio de fase de un jefe, que es el momento en que el combate cambia de
#:   reglas y el jugador necesita enterarse.
#:
#: La muerte de un enemigo **no** entra: mueren a docenas.
EVENTOS_CRITICOS: frozenset[str] = frozenset({
    Events.ACHIEVEMENT_UNLOCKED,
    Events.SFX_STAGE_COMPLETE,
    Events.SFX_UI_GAME_OVER,
    Events.SFX_BOSS_PHASE_CHANGE,
})



class SonidoDeEscenario:
    """La mitad sonora de las señales del escenario.

    Espera de la escena: `context.event_bus`, `_camera`, `_sfx_handlers`
    y el gestor de audio.
    """

    def _subscribe_sfx_handlers(self) -> None:
        """Conecta cada evento con su muestra. Lo llama `_subscribe_event_handlers`."""
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
            Events.SFX_PLAYER_FOOTSTEP_MUSGO: "sfx_player_footstep_musgo",
            Events.SFX_MENU_HOVER: "sfx_select",
            Events.SFX_MENU_CONFIRM: "sfx_select",
            Events.SFX_MENU_CANCEL: "sfx_ui_menu_cancel",
            Events.SFX_PLAYER_PARRY: "sfx_parry",
            Events.SFX_PLAYER_CROUCH: "sfx_player_crouch",
            Events.SFX_PLAYER_HEAL: "sfx_ui_heart_restore",
            Events.SFX_BOSS_HIT: "sfx_boss_hit",
            Events.SFX_UI_GAME_OVER: "sfx_ui_game_over",
            # AUD-256 — el logro se veía y no se oía: `ACHIEVEMENT_UNLOCKED`
            # se emitía sin un solo suscriptor y el aviso se perdía en mitad
            # del combate que lo provocaba.
            Events.ACHIEVEMENT_UNLOCKED: "sfx_ui_stage_complete",
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
            handler = self._make_sfx_handler(sname, critico=evt in EVENTOS_CRITICOS)
            self.context.event_bus.subscribe(evt, handler)
            # Retained here so the bus's weak reference stays alive.
            self._sfx_handlers[evt] = handler

    def _make_sfx_handler(self, sound_name: str,
                          critico: bool = False) -> Callable[..., None]:
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
            if critico:
                # AUD-284 — este efecto se lleva por delante a la música.
                audio = self.audio
                if audio is not None:
                    centro = self._camera.offset.x + settings.INTERNAL_WIDTH / 2
                    audio.play_sfx_critico(
                        sound_name, volume=volume,
                        world_x=pos[0] if pos is not None else None,
                        screen_center_x=centro,
                    )
                return
            if pos is not None:
                self._play_sfx_spatial(sound_name, pos[0], volume=volume)
            else:
                self._play_sfx_named(sound_name, volume=volume)
        return handler

    def _play_sfx_named(self, name: str, volume: float = 1.0) -> None:
        audio = self.audio
        if audio is not None:
            audio.play_sfx(name, volume=volume)

    def _play_sfx_spatial(self, name: str, world_x: float, volume: float = 1.0) -> None:
        audio = self.audio
        if audio is not None:
            screen_center_x = self._camera.offset.x + settings.INTERNAL_WIDTH / 2
            audio.play_sfx_at(name, world_x, screen_center_x, volume=volume)


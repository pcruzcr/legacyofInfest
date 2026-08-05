"""Conducir el Boss Rush — AUD-261.

Por qué es una parte y no líneas en `stage_scene.py`
====================================================
El modo necesita cuatro momentos y **los cuatro los conoce sólo la escena**:
cuándo empieza el combate, cuánto dura, cuándo el jugador recibe un golpe y
cuándo cae el jefe. Eso lo convierte en código de escena por definición.

Pero es también un tema entero y cerrado —GAP-030 de principio a fin— que no
tiene nada que decirle al resto del escenario, así que va donde AUD-152 puso el
ambiente, las señales y el fantasma: en una parte que se lee sola.

Lo que hay que saber para leerlo
--------------------------------
`context.boss_rush` sólo existe mientras se juega el modo, así que **todo lo de
aquí es un no-op en la partida normal**. Ésa es la propiedad que importa: los
dieciséis escenarios entregados no pueden notar nada de esto.

Y por qué `0` significa «a vida llena»: es lo que devuelve `salud_arrastrada`
en un modo recién arrancado, así que el primer jefe no se ve afectado sin
necesidad de un caso especial.
"""
from __future__ import annotations

from typing import Any


class ConduccionDelBossRush:
    """Lo que la escena le dice al modo. Espera `context` y `_player`."""

    def _suscribir_boss_rush(self) -> None:
        """Engancha el recuento de golpes. Lo llama `on_enter` de la escena.

        Vive aquí y no en `senales.py` porque el Boss Rush es un tema entero:
        dejar la suscripción allí obligaba a aquel módulo a conocer un modo de
        juego con el que no tiene nada que ver, y a cualquiera que montara sólo
        las señales —una prueba, por ejemplo— a arrastrar este mixin.
        """
        from src.engine.core.events import Events
        self.context.event_bus.subscribe(
            Events.PLAYER_DAMAGED, self._anotar_golpe_de_rush)
        self._vfx_handlers["boss_rush_hit"] = self._anotar_golpe_de_rush

    def _boss_rush_activo(self) -> Any:
        """El modo, si esta escena es uno de sus combates. `None` si no."""
        modo = getattr(self.context, "boss_rush", None)
        return modo if modo is not None and modo.active else None

    def _anotar_golpe_de_rush(self, **_data: Any) -> None:
        """Un golpe recibido.

        Es un método y no un cierre porque el bus retiene a sus suscriptores
        **débilmente**: un método ligado vive mientras viva la escena, que es
        la misma razón por la que `senales.py` guarda sus manejadores en un
        diccionario.
        """
        modo = self._boss_rush_activo()
        if modo is not None:
            modo.record_hit()

    def _acreditar_boss_rush(self) -> None:
        """El jefe cayó: guarda con qué se sigue y pasa al siguiente.

        Se llama **antes** de emitir `STAGE_COMPLETE`, que es lo que hace
        avanzar la cola del `SceneManager`: acreditar después dejaría el
        arrastre de vida escrito cuando el combate siguiente ya ha empezado.
        """
        modo = self._boss_rush_activo()
        if modo is None:
            return
        modo.acreditar_combate(
            salud_restante=self._player.current_health,
            medidor=self._player.special_meter,
            salud_maxima=self._player.max_health,
        )

    def _aplicar_salud_arrastrada(self) -> None:
        """Empieza el combate con lo que quedó del anterior."""
        modo = self._boss_rush_activo()
        if modo is None or modo.salud_arrastrada <= 0.0:
            return
        self._player.set_health(modo.salud_arrastrada)
        self._player.gain_special(modo.medidor_arrastrado)

"""
Module: stage4_1b
System: src.stages.stage4_1b
Academic Unit: N/A

NIVEL 4-1b — LA FOSA ABISAL

Una de las tres variantes que puede tocarle al jugador en el slot de la
Fase 4 (AUD-518, `src/stages/stage4_1/selector.py`): la misma travesía
horizontal del 4-1, sumergida. El jugador nada, no camina —el motor ya
tenía la física (`docs/45_SWIMMING_SPEC.md`), sólo le faltaba un nivel
que la usara de principio a fin—, y un pez abismal
(`EnemyPezAbismal`) aparece de la nada a intervalos, persigue, y
desaparece: no puede tocar al jugador ni ser tocado por él
(`damage_on_contact=0.0`, `apply_hit` es un no-op) — la misma regla de
oro del 4-1 ("cero enemigos, la atmósfera es el desafío"), aplicada a una
amenaza que sí se mueve.

`Stage4_1B` es deliberadamente delgada. `StageScene` ya resuelve TMX,
spawn, checkpoints, salida y la física de natación por sí sola —lo único
que este escenario añade es el ciclo de aparición del pez.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import azar, settings
from src.engine.core.events import Events
from src.framework.entities.enemy_pez_abismal import EnemyPezAbismal
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage4_1B(StageScene):
    """4-1b — La Fosa Abisal."""

    STAGE_ID: str = "stage4_1b"
    STAGE_NAME: str = "4-1b  LA FOSA ABISAL"
    ZONE: int = 4
    BGM_TRACK: str = "bgm_splash"
    TMX_PATH = "assets/maps/stage4_1b/stage4_1b.tmx"

    # ── El ciclo del pez abismal ──────────────────────────────
    #
    # Un rango y no un número fijo, mismo motivo que `ESPERA_ENTRE_GRITOS`
    # del 4-1 (AUD-481): un susto cada N segundos exactos se vuelve
    # previsible a la tercera vez.
    ESPERA_ENTRE_APARICIONES: tuple[float, float] = (12.0, 22.0)
    #: Cuánto dura cada persecución antes de que el pez se retire.
    DURACION_DE_LA_PERSECUCION: tuple[float, float] = (5.0, 9.0)
    #: Antes de la primera aparición, un respiro — que el jugador entienda
    #: dónde está antes de que algo se le acerque.
    ESPERA_ANTES_DE_LA_PRIMERA: float = 8.0
    #: A qué distancia, en píxeles más allá del borde visible de la
    #: cámara, aparece el pez — lo bastante lejos para que "sale de la
    #: nada" sea literal, no un pop-in a medio cuadro.
    MARGEN_DE_APARICION_PX: float = 60.0

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        # `azar.generador()` — el generador aislado del proceso (AUD-374),
        # no el global: mismo criterio que `src/stages/stage4_1/selector.py`.
        self._azar = azar.generador()
        self._proxima_aparicion_pez: float = self.ESPERA_ANTES_DE_LA_PRIMERA
        self._pez: EnemyPezAbismal | None = None
        self._tiempo_restante_del_pez: float = 0.0
        self._fondo_cueva = self._construir_fondo_cueva()

    def _construir_fondo_cueva(self) -> pygame.Surface:
        """AUD-531 — «el negro debe representar únicamente la ausencia de
        luz». Sin un fondo pintado, los faroles (`Light`, AUD-531 más
        abajo) no tienen nada que iluminar: `LightSystem.render` compone
        con `BLEND_RGB_MULT` — multiplicar por un multiplicador de luz
        sobre negro puro sigue dando negro puro (0 × n = 0), así que la
        luz de los faroles era invisible aunque estuviera calculada bien.

        Degradado vertical, roca profunda casi negra abajo y un café algo
        menos oscuro arriba, cerca de donde cuelgan los faroles — la
        misma dirección de luz que pide el guion. Constante en X, así que
        se calcula una sola vez (no en cada fotograma) y se estira al
        ancho real de pantalla.
        """
        alto = settings.INTERNAL_HEIGHT
        tira = pygame.Surface((1, alto))
        oscuro = (9, 7, 5)
        techo = (58, 44, 28)
        for y in range(alto):
            t = y / max(1, alto - 1)
            col = tuple(int(techo[i] + (oscuro[i] - techo[i]) * t) for i in range(3))
            tira.set_at((0, y), col)
        return pygame.transform.scale(tira, (settings.INTERNAL_WIDTH, alto))

    def dibujar_fondo(self, surface: pygame.Surface,
                      offset: pygame.Vector2) -> None:
        """Roca de cueva, no negro puro — ver `_construir_fondo_cueva`."""
        if surface.get_size() == self._fondo_cueva.get_size():
            surface.blit(self._fondo_cueva, (0, 0))
        else:
            surface.blit(pygame.transform.scale(self._fondo_cueva, surface.get_size()), (0, 0))

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._player is None or self._stage_data is None:
            return
        self._actualizar_pez_abismal(dt)

    def _actualizar_pez_abismal(self, dt: float) -> None:
        if self._pez is not None:
            self._tiempo_restante_del_pez -= dt
            if self._tiempo_restante_del_pez <= 0.0 or not self._pez.is_alive:
                self._retirar_pez()
            return
        self._proxima_aparicion_pez -= dt
        if self._proxima_aparicion_pez <= 0.0:
            self._invocar_pez()

    def _invocar_pez(self) -> None:
        """Lo aparece justo más allá del borde de la cámara, en la
        dirección en la que avanza el jugador — nunca dentro del cuadro,
        que se leería como un enemigo que se materializa encima."""
        assert self._player is not None and self._stage_data is not None
        mirando_a_la_derecha = self._player.facing_direction >= 0
        borde_x = (self._camera.offset.x
                   + (settings.INTERNAL_WIDTH if mirando_a_la_derecha else 0.0))
        x = borde_x + (self.MARGEN_DE_APARICION_PX if mirando_a_la_derecha
                       else -self.MARGEN_DE_APARICION_PX)
        # En profundidad, cerca de donde ya está el jugador —no en la
        # superficie ni pegado al lecho— para que la primera silueta que
        # se vea sea la del pez acercándose, no un punto lejano en el
        # extremo de la columna de agua.
        y = self._player.rect.centery + self._azar.uniform(-48.0, 48.0)

        pez = EnemyPezAbismal(pygame.Vector2(x, y), event_bus=self.context.event_bus)
        pez.set_player_ref(self._player.rect)
        self._stage_data.entity_list.append(pez)
        self._pez = pez
        # AUD-529 — «que el jugador lo sienta y lo escuche antes de poder
        # verlo». El pez nace fuera de cámara a propósito (arriba); este
        # sonido es el aviso de un segundo o dos antes de que la silueta
        # entre nadando en cuadro.
        self.context.event_bus.emit(Events.SFX_ENEMIES_PEZ_ABISMAL_ACERCARSE)
        self._tiempo_restante_del_pez = self._azar.uniform(*self.DURACION_DE_LA_PERSECUCION)

    def _retirar_pez(self) -> None:
        if self._pez is not None and self._stage_data is not None:
            try:
                self._stage_data.entity_list.remove(self._pez)
            except ValueError:
                pass  # ya no estaba -- no hay nada que retirar dos veces
        self._pez = None
        self._proxima_aparicion_pez = self._azar.uniform(*self.ESPERA_ENTRE_APARICIONES)

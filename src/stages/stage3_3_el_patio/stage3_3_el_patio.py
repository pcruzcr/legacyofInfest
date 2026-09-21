"""
Module: stage3_3_el_patio
System: stage (student assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

Zone 3 (Sede Heredia), Stage 3-3 — El Patio.
Student: Rebeca.

Test with:
   python main.py --stage stage3_3_el_patio
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.framework.scenes.stage_scene import StageScene
from src.stages.stage3_3_el_patio.fountain import Fountain
from src.stages.stage3_3_el_patio.camara_objetivo import CamaraObjetivo, Objetivo
from src.stages.stage3_3_el_patio.moneda_fx import MonedaFxController
from src.stages.stage3_3_el_patio.onda_fuente import OndaFuenteController
from src.stages.stage3_3_el_patio.vigia import Vigia

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage3_3ElPatio(StageScene):
    """Un patio interior con una fuente central, rodeado de aves en alerta.
    Demuestra: vectores explicitos (Unidad II), curvas (Unidad III),
    representacion de escena via TMX (Unidad IV), color (Unidad V),
    animacion con easing + EventBus (Unidad VI) y filtros (Unidad VII)."""

    STAGE_ID: str = "stage3_3_el_patio"
    STAGE_NAME: str = "3-3  EL PATIO"
    ZONE: int = 3

    TMX_PATH = "assets/maps/stage3_3_el_patio/stage3_3_el_patio.tmx"

    # Debe coincidir con el objeto Platform_Fountain del TMX (x=432, y=832,
    # width=64) -> centro en x = 432 + 64/2 = 464. La fuente se queda en el
    # piso de abajo: es el respiro antes de encarar el muro grande.
    FOUNTAIN_POS = pygame.Vector2(464, 832)

    # Camara de objetivo: (x, y) del punto que se ensena, y el x del jugador
    # que dispara la cinematica. Ahora el nivel tiene dos pisos, asi que la
    # camara ensena la escalera del muro grande, el foso de arriba y la
    # salida — que esta en el piso alto, no donde se empieza.
    OBJETIVOS = [
        (1160, 620, 820, "SUBE EL MURO"),
        (1640, 360, 1450, "EL FOSO"),
        (2352, 300, 2150, "SALIDA"),
    ]

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        self._fountain: Fountain | None = None
        self._moneda_fx: MonedaFxController | None = None
        self._camara_obj: CamaraObjetivo | None = None
        self._onda: OndaFuenteController | None = None
        self._vigia: Vigia | None = None
        self._ultimo_dt: float = 0.0

    # ── Optional lifecycle hooks ────────────────────────────────────
    # Override any of these to add custom behavior:

    def on_stage_start(self) -> None:
        """Called after the stage loads and setup completes."""
        self._fountain = Fountain(self.FOUNTAIN_POS)
        # Unidad VI: interaccion propia con el EventBus — se suscribe al
        # evento del framework que se emite al recoger un Pickup, y anima un
        # destello con easing en el punto exacto donde se recogio.
        self._moneda_fx = MonedaFxController(self.events)
        # Poder propio del escenario: las monedas cargan la fuente y la
        # tecla E suelta una onda expansiva que mata enemigos en area.
        # Unidades VIII y IX: el Vigia mira el fotograma, segmenta lo que se
        # acerca y lo clasifica; la Onda consulta su veredicto.
        self._vigia = Vigia()
        self._onda = OndaFuenteController(self.events, self._vigia)
        # El ancho del mapa sale del propio TMX, no de una constante: si
        # vuelvo a alargar el nivel, el encuadre se ajusta solo.
        ancho, alto = self._stage_data.map_pixel_size
        self._camara_obj = CamaraObjetivo(
            [Objetivo(x, y, disparo, rotulo)
             for x, y, disparo, rotulo in self.OBJETIVOS], ancho, alto)

    def update(self, dt: float) -> None:
        super().update(dt)
        # El Vigia analiza en `draw()`, que es cuando el fotograma existe;
        # aqui solo se guarda el dt para poder temporizarlo alla.
        self._ultimo_dt = dt
        if self._fountain is not None:
            self._fountain.update(dt, self._player)
        if self._moneda_fx is not None:
            self._moneda_fx.update(dt)
        # Va de ultimo a proposito: pisa el offset que acaba de calcular
        # `super().update()`, y asi manda la cinematica mientras dura.
        if self._onda is not None:
            enemigos = getattr(self._stage_data, "entity_list", []) or []
            self._onda.update(dt, self._player, enemigos)
        if self._camara_obj is not None:
            self._camara_obj.update(dt, self._player, self._camera)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        if self._fountain is not None:
            self._fountain.draw(surface, self._camera.offset)
        if self._moneda_fx is not None:
            self._moneda_fx.draw(surface, self._camera.offset)
        if self._onda is not None:
            self._onda.draw(surface, self._camera.offset)
        if self._camara_obj is not None:
            self._camara_obj.draw(surface, self._camera.offset)
        # De ultimo y en `draw`: el Vigia necesita la pantalla YA pintada,
        # porque su entrada son pixeles, no la lista de entidades.
        if self._vigia is not None:
            self._vigia.update(self._ultimo_dt, surface, self._player,
                               self._camera.offset)
            self._vigia.draw_regiones(surface, self._player, self._camera.offset)
            self._vigia.draw(surface)

    def on_player_landed(self) -> None:
        """Called when the player first touches ground after being airborne.
        Not used in this stage."""
        pass

    def on_enemy_died(self, enemy) -> None:
        """Called when an enemy dies. Not used in this stage."""
        pass

    def on_next_trigger_entered(self) -> None:
        """Called when the player touches NextTrigger. Not used in this stage."""
        pass

    def on_debug_toggle(self, enabled: bool) -> None:
        """Called when F1 is pressed to toggle debug overlay.
        Not used in this stage."""
        pass

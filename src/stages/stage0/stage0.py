from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage0(StageScene):
    """Stage 0 — Prologue / Learning Hub.
    6 progressive zones teaching every framework feature through play:
      A: Movement     B: Basic Combat   C: Ranged Combat
      D: Verticality  E: Hazards        F: Culmination
    """

    STAGE_ID: str = "stage0"
    STAGE_NAME: str = "STAGE 0 — PROLOGUE"
    ZONE: int = 0
    TIME_LIMIT: int = 0
    BGM_TRACK: str = "bgm_stage0"
    TILE: int = 16
    TMX_PATH = settings.ASSETS_DIR / "maps/stage0/stage0.tmx"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._cutscene = None
        self._collectibles: list[dict] = []
        self._collected: set[int] = set()
        self._zone_entered: set[int] = set()

    def on_stage_start(self) -> None:
        super().on_stage_start()
        self._start_intro_cutscene()
        self._place_collectibles()
        self._register_dialogue_trees()

    #: El guion de la introducción, en el mismo lenguaje que usan los mapas.
    #:
    #: AUD-040: la versión original empezaba con un fundido **a** negro,
    #: aunque `StageScene.on_enter` acababa de pedir un fundido de entrada. El
    #: jugador veía aparecer el escenario, apagarse de golpe, esperar y volver
    #: a encenderse, con el juego congelado 2,3 s. Primero se establece el
    #: plano y luego se entrega el mando.
    GUION_DE_INTRO = """
    camara 0 0 0.8
    esperar 0.2
    """

    def _start_intro_cutscene(self) -> None:
        """AUD-136 — ahora por el director, no a mano.

        Esto era un `CutsceneScript` propio que este escenario guardaba,
        actualizaba, dibujaba y apagaba tocando `_active` desde fuera. Cada
        escenario que quisiera una escena tenía que repetir esas cuatro cosas,
        y las repetiría igual de mal: apagar el guion a medias no es saltarlo.

        Ahora es un guion de dos líneas que corre por el mismo camino que las
        escenas del mapa.
        """
        if self._cutscenes is None:
            return
        self._cutscene = self._cutscenes.reproducir_texto(self.GUION_DE_INTRO)

    def _place_collectibles(self) -> None:
        items = [
            (48, 27, "swift_feather"),
            (62, 29, "heart_vessel"),
            (82, 28, "ancients_rib"),
            (94, 26, "sunken_crown"),
        ]
        for col, row, item_id in items:
            x = col * self.TILE
            y = row * self.TILE
            self._collectibles.append({
                "rect": pygame.Rect(x - 8, y - 8, self.TILE, self.TILE),
                "item_id": item_id,
            })

    def _register_dialogue_trees(self) -> None:
        from src.framework.ui.dialogue_system import DialogueNode, DialogueTree

        intro = DialogueTree(
            "intro_narrator", "start",
            {
                "start": DialogueNode(
                    "start", "Narrator",
                    "The world lies in ruin. You are the last Legacy. "
                    "Each zone teaches you the skills you need. "
                    "Press F2-F10 anytime for educational panels.",
                    choices=[("Continue...", "zone_a")],
                ),
                "zone_a": DialogueNode(
                    "zone_a", "Narrator",
                    "Zone A — Movement. A/D to walk, W to jump, "
                    "S to crouch. Master your body.",
                    choices=[("I am ready.", "__end__")],
                ),
            },
        )

        bestiary = DialogueTree(
            "bestiary_intro", "start",
            {
                "start": DialogueNode(
                    "start", "Echo",
                    "You defeated your first foe! The Bestiary records "
                    "every enemy. Press TAB to view it.",
                    choices=[("I will study them.", "__end__")],
                ),
            },
        )

        self._dialogue_trees = {"intro": intro, "bestiary": bestiary}

    def update(self, dt: float) -> None:
        # AUD-136: el director corre dentro de `StageScene.update` y ya congela
        # el juego mientras la escena bloquea. Lo que este escenario añade
        # encima sólo tiene sentido cuando se está jugando de verdad.
        super().update(dt)
        if self._cutscenes is not None and self._cutscenes.bloquea:
            return
        self._check_collectibles()
        self._check_dialogue_triggers()
        self._check_zone_progression()

    def _check_collectibles(self) -> None:
        if self._player is None or self._stage_data is None:
            return
        for i, entry in enumerate(self._collectibles):
            if i in self._collected:
                continue
            if self._player.rect.colliderect(entry["rect"]):
                from src.engine.core.inventory import get_inventory
                inventory = get_inventory()
                if inventory.collect(entry["item_id"]):
                    self._collected.add(i)
                    # AUD-022: recompute stat bonuses so a relic takes effect the
                    # moment it is picked up, not on the next stage load.
                    self._player.apply_relic_bonuses(inventory)

    def _check_dialogue_triggers(self) -> None:
        if self._player is None or self._stage_data is None:
            return
        if self._dialogue.active:
            return
        for mt in self._stage_data.message_triggers:
            if self._player.rect.colliderect(mt.rect):
                tree_id = getattr(mt, "dialogue_tree_id", "")
                if tree_id and tree_id in self._dialogue_trees:
                    self._dialogue.start_dialogue(self._dialogue_trees[tree_id])

    def _check_zone_progression(self) -> None:
        if self._player is None:
            return
        px = self._player.position.x
        # Zone B — first enemy encounter
        if px > 16 * self.TILE and 1 not in self._zone_entered:
            self._zone_entered.add(1)
            self._tutorial.show("combat", 5.0)
        # Zone D — verticality
        if px > 52 * self.TILE and 2 not in self._zone_entered:
            self._zone_entered.add(2)
            self._tutorial.show("advanced", 4.0)
        # Zone F — storm finale
        if px > 85 * self.TILE and 3 not in self._zone_entered:
            self._zone_entered.add(3)
            # AUD-374 — se le pide al mundo, no al sistema que dibuja la
            # lluvia. Pedírselo al VFX dejaba la humedad en el clima del TMX,
            # así que la tormenta del clímax se veía y no mojaba el suelo.
            self._cambiar_clima("storm")
            # AUD-066: era `self._context`, que no existe en `BaseScene` —el
            # atributo es `self.context`—. Sólo se ejecuta al pasar del tile 85,
            # así que el juego crasheaba a los tres cuartos del escenario y
            # ninguna prueba llegaba tan lejos.
            self.context.event_bus.emit(
                Events.SHOW_MESSAGE,
                text="¡Tormenta activada! Usa todo lo aprendido.",
                duration=6.0,
            )

    def draw(self, surface: pygame.Surface) -> None:
        # El director dibuja sus escenas dentro de `StageScene.draw`, entre el
        # mundo y la interfaz. Dibujarlas otra vez aquí las pondría por encima
        # del HUD.
        super().draw(surface)

    def on_debug_toggle(self, enabled: bool) -> None:
        if enabled and self._collectibles:
            cam_off = self._camera.offset
            for i, entry in enumerate(self._collectibles):
                r = entry["rect"]
                color = (100, 200, 255) if i not in self._collected else (100, 255, 100)
                pygame.draw.rect(
                    pygame.display.get_surface(), color,
                    (r.x - cam_off.x, r.y - cam_off.y, r.w, r.h),
                )

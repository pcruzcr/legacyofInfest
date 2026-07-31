"""Escena del Stage 4-2 — arena de El Gran Shaman Paburu.

Registra la entidad BossPaburu en el StageLoader (API pública del
framework — sin tocar código del profesor) y carga el TMX de la arena.

Además maneja la iluminación ceremonial: los cuatro cuencos de fuego que
se van encendiendo forma tras forma (GDD §3.2 — "el escenario se ilumina
a medida que Paburu se revela").
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.input.action_map import Action

from src.engine.core.events import Events
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.stage_loader import StageLoader
from src.framework.vfx.lighting import LightSource
from src.stages.boss_paburu.boss_paburu import BossPaburu

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


# Los cuencos, en el orden en que se encienden. Las X coinciden con
# `BRAZIERS` de `tools/gen_paburu_tmx.py`, que es donde se dibuja el tile
# del cuenco; la Y es el pábilo, un tile por encima del suelo.
BRAZIER_POSITIONS = ((128, 548), (672, 548), (240, 548), (560, 548))

# Fuego de ritual: naranja cálido contra el púrpura del cementerio.
BRAZIER_COLOR = (255, 176, 88)

# La arena arranca en penumbra y gana luz con cada forma (GDD §3.2).
# `LightSystem` MULTIPLICA la pantalla por este valor, así que 0.30 deja
# el escenario prácticamente negro.
#
# Estos valores estaban en (0.62, 0.72, 0.82, 0.93). Renderizando la escena
# y mirándola se vio que 0.62 no era "penumbra": el jugador, que arranca
# abajo a la izquierda contra la pared, se perdía dentro del muro. Una
# arena de jefe tiene que dejar leer al jugador y al telegrafiado del
# ataque desde el primer segundo. Se sube el piso y se conserva la
# progresión: cada forma sigue aclarando la sala.
AMBIENT_BY_PHASE = (0.80, 0.87, 0.94, 1.00)



class BossPaburuScene(StageScene):
    STAGE_ID: str = "boss_paburu"
    STAGE_NAME: str = "4-2  EL GRAN SHAMAN PABURU"
    ZONE: int = 4

    def __init__(self, context: GameContext) -> None:
        StageLoader.register_entity("BossPaburu", BossPaburu)
        self._braziers: list[LightSource] = []
        self._teclas_previas: dict[int, bool] = {}
        self._intro: Any | None = None
        self._intro_vista: bool = False
        self._guardianes: list = []
        self._presencia: float = 0.0
        super().__init__(context, Path("assets/maps/boss_paburu/boss_paburu.tmx"))

    # ── Iluminación ceremonial ──────────────────────────────────
    def on_enter(self) -> None:
        """Arma la escena y reemplaza la iluminación por defecto.

        `StageScene.on_enter` decide las luces según la zona, con
        posiciones pensadas para la resolución vieja de 320×224 — en una
        arena de 800×600 quedan amontonadas en la esquina superior
        izquierda. No se puede cambiar ese código porque es del profesor,
        así que se sobrescribe la lista después de que el padre termina.
        Solo se tocan atributos: no se modifica el framework.
        """
        super().on_enter()

        # `StageScene` muestra el tip de "Move / Jump / Crouch" durante los
        # primeros 6 s de cualquier stage. Acá sobra por dos razones: esto es
        # el jefe FINAL —quien llega ya sabe caminar— y el cartel aparece
        # centrado, justo encima de la zona donde el boss telegrafía EL SELLO.
        # Marcarlos como ya vistos lo suprime sin tocar el framework.
        self._tutorial_shown.update({"move", "landed", "enemy_kill"})
        # `super().on_enter()` ya lo disparó unas líneas antes, así que además
        # de marcarlo como visto hay que bajar el que quedó en pantalla.
        self._tutorial._active = False

        self._lighting.clear()
        self._stage_lights = []
        self._player_light = None
        self._braziers = [
            LightSource(
                pygame.Vector2(x, y),
                radius=132.0,
                color=BRAZIER_COLOR,
                intensity=0.0,          # apagados: se encienden por forma
                flicker=True,
                flicker_speed=5.5,
                flicker_amount=0.22,
            )
            for (x, y) in BRAZIER_POSITIONS
        ]
        for light in self._braziers:
            self._lighting.add_light(light)
            self._stage_lights.append(light)

        self._set_phase_light(0)

        # Los tres guardianes salieron del PNG de fondo para poder moverse.
        from src.stages.boss_paburu import guardianes
        self._guardianes = guardianes.cargar()

        def _on_phase(**data: Any) -> None:
            self._set_phase_light(int(data.get("phase", 0)))

        self.context.event_bus.subscribe(Events.BOSS_PHASE_CHANGED, _on_phase)
        # Se guarda en el mismo dict que limpian `on_exit` y `respawn`, así
        # el handler se desuscribe solo y no se duplica al reaparecer.
        self._vfx_handlers[Events.BOSS_PHASE_CHANGED] = _on_phase

    # ── Tecla de debug: forzar forma ────────────────────────────
    # Teclas 1-4. Existe para la demostración: EP1 solo implementa la
    # Forma 1, así que en una partida normal el boss nunca baja de fase y
    # las otras tres —que YA están cargadas, con su hoja de sprites y su
    # iluminación— no se pueden mostrar. El GDD §7 la pide recién para EP3
    # junto a la selección aleatoria de la Forma 3; acá se adelanta solo la
    # parte de depuración, que no afecta al combate.
    _TECLAS_FORMA = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)

    # ── Secuencia de entrada ────────────────────────────────────
    def on_stage_start(self) -> None:
        """Arranca la entrada del jefe, UNA sola vez.

        `respawn()` vuelve a llamar a `on_enter()`, y `on_enter()` llama a
        `on_stage_start()`. Sin la bandera, la entrada de seis segundos se
        repetía entera cada vez que el jugador moría: exactamente el momento
        en que menos ganas hay de mirar una cinemática. Se ve al entrar a la
        sala y no vuelve a aparecer.
        """
        super().on_stage_start()
        if self._intro_vista:
            return
        self._intro_vista = True
        boss = self._boss_ref()
        if boss is None:
            return
        from src.framework.stage.cutscene_system import CutsceneScript
        from src.stages.boss_paburu import intro

        boss.intro_eyes = 0.0
        guion = CutsceneScript(intro.construir(self, boss, AMBIENT_BY_PHASE[0]))
        guion.start(callback=self._fin_intro)
        self._intro = guion

    def _fin_intro(self) -> None:
        """Devuelve el control con la sala exactamente en su estado normal."""
        self._intro = None
        boss = self._boss_ref()
        if boss is not None:
            boss.intro_eyes = 1.0
        self._set_phase_light(0)

    def update(self, dt: float) -> None:
        # Mientras corre la entrada NO se llama a `super().update`: eso
        # congela al jugador, al boss y a los ataques sin necesidad de un
        # flag de "input bloqueado" en el motor. Es el mismo patrón que usa
        # `stages/stage0/stage0.py` para su cinemática.
        # Presencia de los guardianes: 0 en la Forma 1, sube al llegar a la
        # Máscara. La rampa es lenta a propósito —tardan casi dos segundos
        # en terminar de aparecer— para que se lea como una invocación y no
        # como un interruptor.
        boss = self._boss_ref()
        objetivo = 1.0 if (boss is not None and boss.current_phase >= 1) else 0.0
        paso = dt / 1.8
        if self._presencia < objetivo:
            self._presencia = min(objetivo, self._presencia + paso)
        elif self._presencia > objetivo:
            self._presencia = max(objetivo, self._presencia - paso)
        for g in self._guardianes:
            g.update(dt)

        if self._intro is not None and self._intro.active:
            self._intro.update(dt)
            im = self.input
            if im is not None and im.is_action_just_pressed(Action.CANCEL):
                self._saltar_intro()
            return

        super().update(dt)
        pulsadas = pygame.key.get_pressed()
        for fase, tecla in enumerate(self._TECLAS_FORMA):
            # Flanco de subida: sin esto la fase cambiaría 60 veces por
            # segundo mientras la tecla siga apretada.
            antes = self._teclas_previas.get(tecla, False)
            if pulsadas[tecla] and not antes:
                self._forzar_forma(fase)
            self._teclas_previas[tecla] = pulsadas[tecla]

    def _saltar_intro(self) -> None:
        """ESC salta la entrada. Deja la sala como si hubiera terminado."""
        if self._intro is not None:
            self._intro._active = False
        self._fin_intro()

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        # Los guardianes van DESPUÉS del stage y ANTES de la cinemática:
        # están en el cielo, detrás de todo lo jugable, pero la placa del
        # título y la caja de diálogo tienen que quedar encima de ellos.
        off = self._camera.offset if self._camera is not None else pygame.Vector2()
        for g in self._guardianes:
            g.draw(surface, off, self._presencia)
        if self._intro is not None and self._intro.active:
            self._intro.draw(surface)

    def _forzar_forma(self, fase: int) -> None:
        """Salta a una forma sin pasar por el umbral de vida."""
        boss = self._boss_ref()
        if boss is None:
            return
        boss.current_phase = max(0, min(boss.phase_count - 1, fase))
        boss.current_health = boss.phase_max_health
        self._set_phase_light(boss.current_phase)
        self.context.event_bus.emit(
            Events.BOSS_PHASE_CHANGED, phase=boss.current_phase,
        )

    def _boss_ref(self) -> BossPaburu | None:
        if self._stage_data is None:
            return None
        for e in self._stage_data.entity_list:
            if isinstance(e, BossPaburu):
                return e
        return None

    def _set_phase_light(self, phase: int) -> None:
        """Enciende un cuenco más y sube la luz ambiente.

        Forma 1 → un cuenco encendido y la arena casi a oscuras.
        Forma 4 → los cuatro, y el sello del piso ya es legible.
        """
        phase = max(0, min(len(AMBIENT_BY_PHASE) - 1, phase))
        self._lighting.ambient_brightness = AMBIENT_BY_PHASE[phase]
        for i, light in enumerate(self._braziers):
            light.intensity = 0.95 if i <= phase else 0.0

"""
Module: stage2_1_oficinas
System: src.stages.stage2_1_oficinas
Description: Zona 2 (Distrito Central) - Oficinas.
Escenario horizontal de recorrido y combate contra guardias a pie
(Walker / Charger / Brute). Sin jefe.
"""
from __future__ import annotations

from pathlib import Path

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.scenes.stage_scene import StageScene
from src.stages.stage2_1_oficinas.collectible import DataChip
from src.stages.stage2_1_oficinas.security_monitor import SecurityMonitor

#: Zumbido de datacenter en bucle (Unit N/A, ambientación — el asset ya
#: existía en la librería compartida sin que ningún stage lo usara).
_AMBIENT_HUM = settings.ASSETS_DIR / "sfx" / "environment" / "sfx_environment_datacenter_hum.wav"

#: Posiciones de los DataChip, una o dos por cuarto, en zonas alcanzables
#: caminando o con un salto corto (no escondidas). Ver collectible.py.
_CHIP_POSITIONS: tuple[tuple[float, float], ...] = (
    (200, 500),    # Pasillo A
    (650, 460),    # Cubículos
    (1050, 460),   # Cubículos (junto a la plataforma alta)
    (1450, 500),   # Sala de Juntas
    (1950, 500),   # Pasillo B
    (2200, 500),   # Sala de Control
    (2650, 460),   # Sala de Servidores (junto a la plataforma alta)
    (3000, 500),   # Sala de Servidores
)

# DRON-04 (dron04.py, en esta misma carpeta) es la entidad personalizada de
# la Evaluación Práctica I: trayectoria curva vía CurveTools + matemática
# vectorial (vec2_*) + color HSV. Se registra en
# src/framework/entities/entity_factory.py (junto a BossVenado, import
# diferido) porque scripts/grade_stage.py y tools/validate_stage.py cargan
# el TMX directamente con StageLoader, sin pasar por esta clase — un
# registro hecho solo aquí no lo verían y el nivel no calificaría.
#
# BruteOficinas/ChargerOficinas (office_enemies.py) reemplazan a Brute/Charger
# en el TMX: la hoja de sprites compartida de zona 2 no puede satisfacer los
# tamaños de cuadro que esas clases piden (ver ese módulo para el porqué),
# así que Brute caía al rectángulo de color plano — el "cuadro que tapa el
# mapa" — en cualquier stage del juego, no sólo en este.
#
# SecurityMonitor (security_monitor.py, misma carpeta) es el añadido de la
# Evaluación Práctica II: panel de la Sala de Control animado por easing y
# accionado por CHECKPOINT_REACHED, que analiza una captura del propio
# escenario con FilterTools (histograma, desenfoque, bordes). No es una
# entidad de Tiled — vive en esta escena, igual que el HUD del motor.
#
# DataChip (collectible.py): coleccionables de "puntos". Tampoco son
# entidades de Tiled — ver ese módulo para por qué (el bucle genérico de la
# escena sólo actualiza EnemyBase).


class Stage21Oficinas(StageScene):
    TMX_PATH: Path = Path(__file__).parent / "stage2_1_oficinas.tmx"
    ZONE: int = 2

    def on_enter(self) -> None:
        super().on_enter()
        if getattr(self, "_security_monitor", None) is not None:
            self._security_monitor.destroy()
        self._security_monitor = SecurityMonitor(self.context.event_bus)

        # DataChips: se recrean en cada on_enter (incluida la reaparición
        # tras morir) para que un chip ya recogido no reaparezca a mitad de
        # una vida, pero si el checkpoint ya guardó progreso más allá de un
        # chip, éste queda naturalmente detrás del punto de reaparición.
        self._chips = [DataChip(pos, i) for i, pos in enumerate(_CHIP_POSITIONS)]
        self._chips_collected = 0
        self._chip_font: pygame.font.Font | None = None

        # Zumbido ambiental del datacenter, capa aparte de la música
        # (`AudioManager.play_ambient`, ya existe en el motor — nadie lo
        # llamaba). Sin `climate` propio que lo dispare automáticamente
        # (climate="clear" en el TMX), así que se arranca aquí a mano.
        if self.audio is not None:
            self.audio.play_ambient(_AMBIENT_HUM, volume=0.32)

    def update(self, dt: float) -> None:
        super().update(dt)
        self._security_monitor.update(dt)
        if self._player is not None:
            for chip in self._chips:
                chip.update(dt)
                if chip.check_pickup(self._player.rect):
                    self._chips_collected += 1
                    # Reutiliza el "ding" de curación de la UI — ya mapeado
                    # en stage_scene.py — en vez de dar de alta un evento
                    # nuevo sólo para este pickup.
                    self.context.event_bus.emit(Events.SFX_PLAYER_HEAL)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        offset = self._camera.offset
        for chip in self._chips:
            chip.draw(surface, offset)
        self._draw_chip_counter(surface)
        self._security_monitor.draw(surface)

    def _draw_chip_counter(self, surface: pygame.Surface) -> None:
        if self._chip_font is None:
            self._chip_font = pygame.font.Font(None, 16)
        text = f"◆ {self._chips_collected}/{len(_CHIP_POSITIONS)}"
        label = self._chip_font.render(text, True, (140, 230, 255))
        panel = pygame.Surface((label.get_width() + 12, label.get_height() + 8), pygame.SRCALPHA)
        panel.fill((10, 14, 20, 190))
        panel.blit(label, (6, 4))
        # Debajo del minimapa (esquina superior derecha), para no pisar
        # ningún otro elemento del HUD del motor.
        surface.blit(panel, (settings.INTERNAL_WIDTH - panel.get_width() - 4, 64))

    def on_exit(self) -> None:
        # StageScene.on_exit() para música pero no para la capa ambiental
        # (`play_ambient`/`stop_ambient` son independientes de
        # `play_music`/`stop_music`, ver audio_manager.py); sin esto el
        # zumbido de datacenter seguiría sonando de fondo en el siguiente
        # escenario. Se detiene aquí, no en el motor, porque el gap es
        # general y arreglarlo en audio_manager.py afectaría a cualquier
        # stage que empiece a usar `play_ambient` — fuera de lo que me
        # corresponde tocar en esta entrega.
        if self.audio is not None:
            self.audio.stop_ambient()
        super().on_exit()

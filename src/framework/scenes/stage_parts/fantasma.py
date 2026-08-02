"""
El fantasma de tu mejor carrera — AUD-142.

Extraído de `stage_scene.py` en AUD-152 sin cambiar una línea de lógica.

Se guarda **sólo si la carrera fue más corta**: un fantasma que siempre es tu
última partida es peor compañía, porque el jugador quiere perseguir su mejor
marca y no la de hace un rato.
"""
from __future__ import annotations

import logging

import pygame


class FantasmaDeCarrera:
    """Grabar, cargar, guardar y dibujar la silueta de la mejor carrera.

    Espera de la escena: `_stage_data`, `_player`, `_camera`, `_speedrun`,
    `_fantasma` y `_fantasma_previo`.
    """

    # ── AUD-142: el fantasma de tu mejor carrera ──────────────────
    def _ruta_del_fantasma(self):
        from pathlib import Path

        from src.engine.core import settings

        stage_id = getattr(self._stage_data, "stage_id", "") or "sin_id"
        return Path(settings.PROJECT_ROOT) / "saves" / "fantasmas" / f"{stage_id}.json"

    def _preparar_fantasma(self) -> None:
        """Empieza a grabar esta carrera y carga la anterior, si la hay."""
        from src.framework.stage.speedrun_mode import GhostData

        self._fantasma = GhostData()
        previo = GhostData()
        ruta = self._ruta_del_fantasma()
        if ruta.exists():
            previo.load(ruta)
        # Sin fotogramas no hay fantasma que dibujar, y `None` lo dice mejor
        # que un objeto vacío al que hay que preguntarle siempre.
        self._fantasma_previo = previo if previo.frame_count else None

    def _guardar_fantasma_si_es_mejor(self) -> None:
        """Sólo se guarda si esta carrera fue más corta.

        Guardar siempre convertiría el fantasma en «tu última partida», que es
        una compañía peor: el jugador quiere perseguir su mejor marca, no la
        de hace un rato.
        """
        actual = self._fantasma
        if actual is None or not actual.frame_count:
            return
        anterior = self._fantasma_previo
        if anterior is not None and anterior.frame_count <= actual.frame_count:
            return
        try:
            actual.save(self._ruta_del_fantasma())
        except OSError:
            # Un disco lleno o un directorio sin permisos no puede costar la
            # partida a nadie: el fantasma es un adorno, no el guardado.
            logging.getLogger(__name__).warning(
                "no se pudo guardar el fantasma", exc_info=True)

    _COLOR_FANTASMA = (140, 210, 255)

    def _dibujar_fantasma(self, surface: pygame.Surface) -> None:
        """Una silueta translúcida donde estabas en tu mejor carrera.

        Translúcida y sin sprite a propósito: un fantasma opaco con la
        animación del jugador se confunde con el jugador, y en un salto
        difícil eso es peor que no tenerlo.
        """
        previo = self._fantasma_previo
        if previo is None or self._player is None:
            return
        punto = previo.posicion_en(self._speedrun.global_time)
        if punto is None:
            return
        x, y = punto
        offset = self._camera.offset
        alto = self._player.rect.height
        ancho = self._player.rect.width
        silueta = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        silueta.fill((*self._COLOR_FANTASMA, 90))
        surface.blit(silueta, (int(x - offset.x), int(y - offset.y)))


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
        from src.engine.core.user_settings import user_data_dir
        from src.framework.stage.stage_data import slug_de_stage_id

        stage_id = getattr(self._stage_data, "stage_id", "") or "sin_id"
        return (user_data_dir() / "saves" / "fantasmas"
                / f"{slug_de_stage_id(stage_id)}.json")

    def _preparar_fantasma(self) -> None:
        """Empieza a grabar esta carrera y carga la anterior, si la hay.

        AUD-FANTASMA: solo en Boss Rush — en modo historia no hay fantasma.
        Antes se grababa y mostraba siempre que existiera un fichero previo,
        contaminando la partida normal con la mejor marca del speedrun.
        """
        from src.framework.stage.speedrun_mode import GhostData

        # Solo Boss Rush genera y consume fantasmas; en historia no se graba ni
        # se carga para no contaminar el disco ni la pantalla.
        try:
            if getattr(self, "_boss_rush_activo", lambda: None)() is None:
                self._fantasma = GhostData()
                self._fantasma_previo = None
                return
        except Exception:
            pass
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
        de hace un rato. AUD-FANTASMA: solo en Boss Rush.
        """
        try:
            if getattr(self, "_boss_rush_activo", lambda: None)() is None:
                return
        except Exception:
            pass
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
        """Silueta del jugador con transparencia donde estabas en tu mejor Boss Rush.

        AUD-FANTASMA: antes era un rectangulo celeste semi-transparente y se
        dibujaba tambien en modo historia. Ahora es el sprite del player con
        alfa 90 y solo aparece si hay Boss Rush activo. Si el sprite no esta
        disponible se cae al rectangulo fantasma como respaldo.
        """
        try:
            if getattr(self, "_boss_rush_activo", lambda: None)() is None:
                return
        except Exception:
            return
        previo = self._fantasma_previo
        if previo is None or self._player is None:
            return
        punto = previo.posicion_en(self._speedrun.global_time)
        if punto is None:
            return
        x, y = punto
        offset = self._camera.offset
        # Intentar dibujar el sprite actual del player con transparencia
        try:
            player = self._player
            frames = getattr(player, "_sprite_frames", {}).get(
                getattr(player._state_instance.state_enum, "value", ""), None
            )
            if frames:
                idx = min(getattr(player, "_animation_frame", 0), len(frames) - 1)
                frame = frames[idx]
                if getattr(player, "facing_direction", 1) < 0:
                    try:
                        from src.engine.utils.surface_pool import get_pool
                        frame = get_pool().get_flipped_frames(frames)[idx]
                    except Exception:
                        frame = pygame.transform.flip(frame, True, False)
                # Copia con alfa de fantasma (90/255)
                fantasma = frame.copy()
                fantasma.set_alpha(90)
                # Anclaje identico al Player.draw (abajo-centro)
                try:
                    from src.framework.entities.player import SPRITE_H, SPRITE_W
                    ox = (player.rect.width - SPRITE_W) // 2
                    oy = player.rect.height - SPRITE_H
                    sx = int(x - offset.x + ox)
                    sy = int(y - offset.y + oy)
                    # Squash considerado si existe
                    sqx = getattr(player, "_squash_x", 1.0)
                    sqy = getattr(player, "_squash_y", 1.0)
                    if sqx != 1.0 or sqy != 1.0:
                        aw = max(1, int(fantasma.get_width() * sqx))
                        ah = max(1, int(fantasma.get_height() * sqy))
                        fantasma = pygame.transform.scale(fantasma, (aw, ah))
                        dx = (SPRITE_W - aw) // 2
                        dy = SPRITE_H - ah
                        sx += dx
                        sy += dy
                except Exception:
                    sx = int(x - offset.x)
                    sy = int(y - offset.y)
                surface.blit(fantasma, (sx, sy))
                return
        except Exception:
            pass
        # Fallback: rectangulo translucido si no hay sprite
        alto = self._player.rect.height
        ancho = self._player.rect.width
        silueta = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        silueta.fill((*self._COLOR_FANTASMA, 90))
        surface.blit(silueta, (int(x - offset.x), int(y - offset.y)))


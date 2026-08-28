"""Los gizmos de F1 del sistema de dibujo — AUD-352.

Por qué existe este módulo
=========================
`drawing_system.py` es el pintor del mundo y de la interfaz. Los gizmos de
depuración (AUD-285) eran el tercer tema del archivo: las cajas de colisión,
las flechas de velocidad y los conos de visión no pintan el nivel, lo
**explican**. Se dibujan sólo cuando `ctx.debug` está activo y su único
llamante en el sistema es `draw_ui`, que los deja para el final, encima de
todo lo demás.

Es un mixin por la misma razón que `stage_parts/` (AUD-152): mover el texto
sin tocar el cableado. `self` sigue siendo el mismo `DrawingSystem`, los
métodos conservan sus nombres y el MRO de `DrawingSystem(GizmosDeDepuracion)`
los resuelve aquí.

Qué NO vive aquí
----------------
* El dibujo del nivel y su orden — parallax, mapa, entidades, inundación,
  zonas de daño — se queda en `DrawingSystem`, que es quien decide cuándo se
  pinta el gizmo (último, y sólo con `ctx.debug`).
* El menú de pausa — es interfaz de juego, no una herramienta.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings

if TYPE_CHECKING:
    from src.framework.entities.player import Player
    from src.framework.stage.camera import Camera
    from src.framework.stage.stage_loader import StageData

class GizmosDeDepuracion:
    """Los gizmos de F1 (AUD-285), movidos de `DrawingSystem` en AUD-352
    sin cambiar una línea de su texto.

    Espera del sistema: `_debug_font` (la crea `DrawingSystem.__init__`),
    `_GIZMO_SEGUNDOS` y `_dibujar_*` de este mismo mixin. No se instancia
    suelto: dibuja sobre el lienzo del pintor, no es un componente.
    """

    #: AUD-285 — segundos de velocidad que representa el vector dibujado.
    #:
    #: Un cuarto de segundo: la flecha marca **dónde estaría dentro de 250 ms**
    #: si nada la parase. Dibujar la velocidad a escala 1 daría flechas de 500 px
    #: para una caída normal, que taparían el nivel; a escala arbitraria, la
    #: longitud no significaría nada. Así la flecha es una predicción legible.
    _GIZMO_SEGUNDOS: float = 0.25

    # Mixin espera que DrawingSystem lo provea; se declara para mypy.
    _debug_font: pygame.font.Font

    def _draw_debug(
        self, surface: pygame.Surface, stage: StageData | None,
        player: Player | None, camera: Camera, offset: pygame.Vector2,
        mundo: Any | None = None,
    ) -> None:
        if stage is None:
            return
        for entity in stage.entity_list:
            if entity is None:
                continue
            screen_x = int(entity.position.x - offset.x)
            screen_y = int(entity.position.y - offset.y)
            rect = getattr(entity, 'rect', None)
            if rect is not None:
                pygame.draw.rect(surface, (0, 255, 0), (screen_x, screen_y, rect.width, rect.height), 1)
            hurtbox = getattr(entity, 'hurtbox', None)
            if hurtbox is not None:
                hx = int(hurtbox.x - offset.x)
                hy = int(hurtbox.y - offset.y)
                pygame.draw.rect(surface, (255, 0, 0), (hx, hy, hurtbox.width, hurtbox.height), 1)
            hitbox = getattr(entity, 'hitbox', None)
            if hitbox is not None:
                hx2 = int(hitbox.x - offset.x)
                hy2 = int(hitbox.y - offset.y)
                pygame.draw.rect(surface, (0, 0, 255), (hx2, hy2, hitbox.width, hitbox.height), 1)
        if player is not None and hasattr(player, 'rect') and player.rect is not None:
            px = int(player.position.x - offset.x)
            py = int(player.position.y - offset.y)
            pygame.draw.rect(surface, (0, 255, 255), (px, py, player.rect.width, player.rect.height), 2)

        # AUD-285 — los dos gizmos que faltaban.
        #
        # Las cajas dicen dónde está algo; ninguna dice **hacia dónde va** ni
        # **qué está viendo**. Los dos datos existen y no se podían mirar: la
        # velocidad, para diagnosticar un enemigo que se queda pegado a una
        # pared o un knockback que sale al revés; el cono, para entender por
        # qué un guardia detecta a través de media pantalla.
        self._dibujar_velocidades(surface, stage, player, offset)
        self._dibujar_conos(surface, mundo, offset)

        fps = self._debug_font.render(f"Entities: {len(stage.entity_list)}", True, (255, 255, 255))
        surface.blit(fps, (5, settings.INTERNAL_HEIGHT - 60))
        cam_pos = self._debug_font.render(f"Cam: {int(offset.x)},{int(offset.y)}", True, (255, 255, 255))
        surface.blit(cam_pos, (5, settings.INTERNAL_HEIGHT - 40))

    def _dibujar_velocidades(
        self, surface: pygame.Surface, stage: StageData,
        player: Player | None, offset: pygame.Vector2,
    ) -> None:
        """Una flecha por entidad con velocidad, del centro hacia donde va."""
        cuerpos = list(stage.entity_list)
        if player is not None:
            cuerpos.append(player)
        for cuerpo in cuerpos:
            if cuerpo is None:
                continue
            velocidad = getattr(cuerpo, "velocity", None)
            rect = getattr(cuerpo, "rect", None)
            if velocidad is None or rect is None:
                continue
            if abs(velocidad.x) < 1.0 and abs(velocidad.y) < 1.0:
                # Parado. Dibujar un punto por cada entidad quieta llena la
                # pantalla de basura y esconde las que sí se mueven.
                continue
            origen = (int(rect.centerx - offset.x), int(rect.centery - offset.y))
            destino = (int(origen[0] + velocidad.x * self._GIZMO_SEGUNDOS),
                       int(origen[1] + velocidad.y * self._GIZMO_SEGUNDOS))
            pygame.draw.line(surface, (255, 0, 255), origen, destino, 1)
            pygame.draw.circle(surface, (255, 0, 255), destino, 2)

    def _dibujar_conos(
        self, surface: pygame.Surface, mundo: Any | None, offset: pygame.Vector2,
    ) -> None:
        """El cono de visión de cada vigilante, y si te está viendo.

        Rojo cuando ve al jugador y amarillo cuando no: es la única forma de
        contestar «¿por qué me ha detectado?» sin leer el código. El cono se
        dibuja con el **barrido ya aplicado**, o sea mirando adonde mira ahora,
        y no en su orientación de reposo — que es justo la diferencia entre un
        gizmo útil y uno que miente.
        """
        if mundo is None:
            return
        try:
            from src.framework.ecs.components import ConoDeVision, Transform
        except ImportError:  # pragma: no cover - el ECS siempre está
            return
        for entidad, cono in mundo.cada(ConoDeVision):
            t = mundo.obtener(entidad, Transform)
            if t is None:
                continue
            centro = pygame.Vector2(t.rect.center) - offset
            base = math.atan2(cono.mira.y, cono.mira.x)
            oscilacion = math.radians(
                math.sin(math.radians(cono._fase)) * cono.barrido,
            ) if cono.barrido > 0.0 else 0.0
            semi = math.radians(cono.semiangulo)
            color = (255, 60, 60) if cono.ve_al_jugador else (220, 220, 60)
            puntos = [centro]
            # Cinco radios bastan para leer la apertura sin pagar un polígono
            # denso por cada vigilante en una herramienta de depuración.
            for i in range(5):
                ang = base + oscilacion - semi + (2 * semi) * i / 4.0
                puntos.append(centro + pygame.Vector2(
                    math.cos(ang), math.sin(ang)) * cono.alcance)
            pygame.draw.lines(surface, color, True,
                              [(int(p.x), int(p.y)) for p in puntos], 1)

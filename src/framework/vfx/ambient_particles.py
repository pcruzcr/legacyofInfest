from __future__ import annotations

import random

import pygame

from src.engine.core import settings
from src.framework.vfx.particle_system import ParticleEmitter


class AmbientParticleSystem:
    """Partículas de ambiente (polvo, hojas, ascuas, esporas, ceniza).

    F1.3 — este sistema nunca emitió una partícula
    ----------------------------------------------
    `set_effect` no la llamaba nadie, así que `_rate` se quedaba en 0,0 durante
    toda la partida. El sistema estaba instanciado, se actualizaba cada
    fotograma y se dibujaba: simplemente no tenía nada que dibujar. Medido en
    Stage 0 tras tres segundos de juego: **0 partículas**.

    Los tipos y el ritmo se declaran ahora en el TMX, con las propiedades de
    mapa `ambient_fx` y `ambient_fx_rate`, así que un estudiante decide la
    atmósfera de su nivel desde Tiled.
    """

    #: Tipos reconocidos. Se declaran explícitamente en vez de aceptar
    #: cualquier cadena para que una errata en Tiled se pueda diagnosticar:
    #: escribir "leafs" debe avisar, no dejar el nivel sin partículas y callar.
    TIPOS: tuple[str, ...] = ("dust", "leaves", "embers", "spores", "ash")

    def __init__(self) -> None:
        self._emitter = ParticleEmitter()
        self._rate: float = 0.0
        self._timer: float = 0.0
        self._particle_type: str = "dust"

    def set_effect(self, particle_type: str, rate: float = 10.0) -> None:
        self._particle_type = particle_type
        self._rate = max(0.0, rate)

    @property
    def count(self) -> int:
        """Partículas vivas. Para pruebas y para el panel de depuración."""
        return self._emitter.count

    @property
    def rate(self) -> float:
        return self._rate

    def update(self, dt: float, camera_offset: pygame.Vector2) -> None:
        # Un ritmo de cero significa apagado.
        #
        # Antes esto era `1.0 / max(self._rate, 0.1)`, que con ritmo 0 daba un
        # intervalo de 10 s: el sistema "apagado" seguía soltando una partícula
        # cada diez segundos. Una mota que aparece sola cada diez segundos es
        # más desconcertante que ninguna, porque no hay forma de relacionarla
        # con nada.
        if self._rate > 0.0:
            intervalo = 1.0 / self._rate
            self._timer += dt
            # Tope de seguridad: tras una pausa larga o un punto de ruptura,
            # `dt` puede valer segundos y este bucle intentaría crear cientos
            # de partículas de golpe.
            for _ in range(self._MAX_SPAWNS_PER_FRAME):
                if self._timer < intervalo:
                    break
                self._timer -= intervalo
                self._spawn(camera_offset)
            else:
                self._timer = 0.0

        self._emitter.update(dt)

    #: Cuántas partículas puede crear un solo fotograma como máximo.
    _MAX_SPAWNS_PER_FRAME = 32

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        self._emitter.draw(surface, offset)

    def clear(self) -> None:
        self._emitter.clear()

    @property
    def _particles(self) -> list:  # backward compat for tests
        return []

    def _spawn(self, camera_offset: pygame.Vector2) -> None:
        sx = camera_offset.x + random.uniform(0, settings.INTERNAL_WIDTH)
        sy = camera_offset.y + random.uniform(0, settings.INTERNAL_HEIGHT)

        if self._particle_type == "dust":
            self._emitter.emit_directed(
                sx, sy, angle=270, speed=random.uniform(5, 15),
                count=1, lifetime=random.uniform(2, 4),
                size=(1, 2), color=(120, 100, 80), spread=30,
                gravity=0,
            )
        elif self._particle_type == "leaves":
            self._emitter.emit_directed(
                sx, sy, angle=random.uniform(60, 120), speed=random.uniform(10, 30),
                count=1, lifetime=random.uniform(3, 6),
                size=(2, 4), color=(60, 140, 40), spread=20,
                gravity=0,
            )
        elif self._particle_type == "embers":
            self._emitter.emit_directed(
                sx, sy, angle=270, speed=random.uniform(3, 30),
                count=1, lifetime=random.uniform(1, 3),
                size=(2, 3), color=(255, 150, 50), spread=15,
                gravity=0,
            )
        elif self._particle_type == "spores":
            # Esporas del bosque infestado: suben despacio, en todas
            # direcciones, y viven mucho para que la pantalla nunca esté vacía.
            self._emitter.emit_directed(
                sx, sy, angle=random.uniform(240, 300), speed=random.uniform(2, 10),
                count=1, lifetime=random.uniform(4, 8),
                size=(1, 3), color=(150, 255, 130), spread=60,
                gravity=-2,
            )
        elif self._particle_type == "ash":
            # Ceniza: cae, a diferencia de todo lo demás en esta lista.
            self._emitter.emit_directed(
                sx, sy, angle=random.uniform(60, 120), speed=random.uniform(8, 20),
                count=1, lifetime=random.uniform(3, 7),
                size=(1, 2), color=(90, 85, 80), spread=25,
                gravity=6,
            )

from __future__ import annotations

import random

import pygame

from src.engine.core import settings
from src.engine.core.azar import generador
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
    # AUD-532 — "niebla": jirones de bruma que derivan despacio en
    # horizontal, casi sin caer ni subir. 4-1c ("Lo Que Flota en la
    # Niebla") pedía exactamente esto tras jugarlo — partículas de nube
    # para dar identidad al vacío bajo el jugador — y no había ningún tipo
    # existente que sirviera: "dust"/"ash" caen, "embers"/"spores" suben,
    # y todos son puntuales, no jirones anchos y pálidos.
    #
    # AUD-543 — "vida_abisal": la fauna nueva que pedía el reporte de
    # 4.1b ("calamares, peces de colores") y el "coral que cae", sin
    # ampliar `ambient_fx` a varias capas simultáneas (cada mapa sigue
    # declarando un solo tipo — es la misma restricción que ya tenían
    # "niebla" o "dust"). Un mapa sólo puede pedir un efecto de ambiente
    # a la vez, así que en vez de tres tipos que compitan por el único
    # slot del TMX, este es UN tipo que mezcla tres comportamientos: peces
    # de colores (rápidos, erráticos), calamares (grandes, lentos,
    # oscuros, casi silueta) y coral desprendido (cae, no flota). Ver
    # `_spawn` para las proporciones.
    TIPOS: tuple[str, ...] = (
        "dust", "leaves", "embers", "spores", "ash", "niebla", "vida_abisal",
    )

    def __init__(self, rng: random.Random | None = None) -> None:
        #: AUD-398 — azar propio (GAP-042). Sin semilla nace del global,
        #: que ya está sembrado, así que la partida no cambia; lo que
        #: cambia es que estas partículas dejan de desplazar la secuencia
        #: que leen la cámara y el clima.
        self._rng = rng if rng is not None else generador()
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
        sx = camera_offset.x + self._rng.uniform(0, settings.INTERNAL_WIDTH)
        sy = camera_offset.y + self._rng.uniform(0, settings.INTERNAL_HEIGHT)

        if self._particle_type == "dust":
            self._emitter.emit_directed(
                sx, sy, angle=270, speed=self._rng.uniform(5, 15),
                count=1, lifetime=self._rng.uniform(2, 4),
                size=(1, 2), color=(120, 100, 80), spread=30,
                gravity=0,
            )
        elif self._particle_type == "leaves":
            self._emitter.emit_directed(
                sx, sy, angle=self._rng.uniform(60, 120), speed=self._rng.uniform(10, 30),
                count=1, lifetime=self._rng.uniform(3, 6),
                size=(2, 4), color=(60, 140, 40), spread=20,
                gravity=0,
            )
        elif self._particle_type == "embers":
            self._emitter.emit_directed(
                sx, sy, angle=270, speed=self._rng.uniform(3, 30),
                count=1, lifetime=self._rng.uniform(1, 3),
                size=(2, 3), color=(255, 150, 50), spread=15,
                gravity=0,
            )
        elif self._particle_type == "spores":
            # Esporas del bosque infestado: suben despacio, en todas
            # direcciones, y viven mucho para que la pantalla nunca esté vacía.
            self._emitter.emit_directed(
                sx, sy, angle=self._rng.uniform(240, 300), speed=self._rng.uniform(2, 10),
                count=1, lifetime=self._rng.uniform(4, 8),
                size=(1, 3), color=(150, 255, 130), spread=60,
                gravity=-2,
            )
        elif self._particle_type == "ash":
            # Ceniza: cae, a diferencia de todo lo demás en esta lista.
            self._emitter.emit_directed(
                sx, sy, angle=self._rng.uniform(60, 120), speed=self._rng.uniform(8, 20),
                count=1, lifetime=self._rng.uniform(3, 7),
                size=(1, 2), color=(90, 85, 80), spread=25,
                gravity=6,
            )
        elif self._particle_type == "niebla":
            # AUD-532 — jirones anchos y pálidos, casi sin verticalidad:
            # derivan en horizontal (0° o 180°, no un ángulo fijo — la
            # niebla no sopla siempre hacia el mismo lado) y viven mucho,
            # para que nunca se sienta el vacío bajo el jugador como aire
            # vacío de verdad.
            angulo = 0.0 if self._rng.random() < 0.5 else 180.0
            self._emitter.emit_directed(
                sx, sy, angle=angulo, speed=self._rng.uniform(4, 12),
                count=1, lifetime=self._rng.uniform(6, 11),
                size=(4, 7), color=(210, 210, 220), spread=8,
                gravity=0,
            )
        elif self._particle_type == "vida_abisal":
            # AUD-543 — ver la nota de `TIPOS` arriba: un tipo, tres
            # comportamientos, para no pedir un segundo slot de
            # `ambient_fx` que el mapa no tiene.
            dado = self._rng.random()
            if dado < 0.55:
                # Peces de colores: rápidos, erráticos, viven poco — un
                # cardumen se lee por la frecuencia de aparición, no por
                # `count` alto de golpe (eso saturaría la pantalla).
                angulo = self._rng.uniform(0, 360)
                color = self._rng.choice((
                    (255, 150, 60), (255, 210, 90), (120, 190, 255),
                ))
                self._emitter.emit_directed(
                    sx, sy, angle=angulo, speed=self._rng.uniform(20, 45),
                    count=1, lifetime=self._rng.uniform(1.5, 3.0),
                    size=(2, 3), color=color, spread=40,
                    gravity=0,
                )
            elif dado < 0.80:
                # Calamares: grandes, lentos, casi silueta — oscuros contra
                # el fondo café de la cueva (AUD-531), no un color propio
                # que compita con los faroles.
                self._emitter.emit_directed(
                    sx, sy, angle=self._rng.uniform(160, 200),
                    speed=self._rng.uniform(6, 14),
                    count=1, lifetime=self._rng.uniform(5, 9),
                    size=(6, 9), color=(30, 26, 34), spread=10,
                    gravity=0,
                )
            else:
                # Coral desprendido: lo único de los tres que cae en vez
                # de flotar — pedido explícito ("coral que cae").
                self._emitter.emit_directed(
                    sx, sy, angle=self._rng.uniform(75, 105),
                    speed=self._rng.uniform(6, 16),
                    count=1, lifetime=self._rng.uniform(2, 4),
                    size=(2, 4), color=(150, 90, 80), spread=20,
                    gravity=10,
                )
